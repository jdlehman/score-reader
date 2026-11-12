// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// What Audiveris reads: grey pages, drawn here from the PDF or photos chosen.
//
// Audiveris in WebAssembly has no image decoders, PDF reader or colour management (they are
// native code, or need fonts), so the page draws everything itself, the PDF with PDF.js and photos
// with the browser, and hands Audiveris raw grey pixels, a byte each (teavm.js).
//
// Each photo and scanned page also gets a quick look (preflight.js), so the page can warn before a
// read that Audiveris would give up on.

import { preflight } from './preflight.js'

/** Desktop Audiveris draws a PDF's pages at 300 dpi: so does the page. */
const DPI = 300

/** Bigger pages are scaled down to this on their long side: more pixels only slow the reading. */
const MAX_SIDE = 4096

const PDFJS = new URL('pdfjs/', import.meta.url)

/**
 * A PDF's pages, drawn at 300 dpi with PDF.js. onPage(n, of) tells how far it has got. Returns each
 * page's grey pixels, and what the quick look found (null for a drawn page).
 */
export async function pdfPages(bytes, onPage) {
  const pdfjs = await import(new URL('pdf.min.mjs', PDFJS).href)
  pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdf.worker.min.mjs', PDFJS).href
  const task = pdfjs.getDocument({
    data: bytes,
    wasmUrl: new URL('wasm/', PDFJS).href, // decoders for the images in scans (JPEG 2000, JBIG2)
    iccUrl: new URL('iccs/', PDFJS).href,
    standardFontDataUrl: new URL('standard_fonts/', PDFJS).href,
    cMapUrl: new URL('cmaps/', PDFJS).href,
    cMapPacked: true,
  })
  let doc
  try {
    doc = await task.promise
  } catch (e) {
    if (e?.name === 'PasswordException') throw new Error('This PDF is locked with a password. Open it, save or print a copy without one, and try that.')
    throw new Error('This file couldn’t be opened as a PDF.')
  }
  // what paints an image (a scan), as opposed to drawn shapes and text
  const IMAGE = new Set([pdfjs.OPS.paintImageXObject, pdfjs.OPS.paintInlineImageXObject, pdfjs.OPS.paintImageXObjectRepeat,
    pdfjs.OPS.paintInlineImageXObjectGroup, pdfjs.OPS.paintImageMaskXObject, pdfjs.OPS.paintImageMaskXObjectGroup, pdfjs.OPS.paintImageMaskXObjectRepeat])
  try {
    const pages = []
    for (let n = 1; n <= doc.numPages; n++) {
      onPage?.(n, doc.numPages)
      const page = await doc.getPage(n)
      const size = page.getViewport({ scale: 1 })
      const scale = Math.min(DPI / 72, MAX_SIDE / Math.max(size.width, size.height))
      const viewport = page.getViewport({ scale })
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(viewport.width)
      canvas.height = Math.round(viewport.height)
      await page.render({ canvas, viewport, background: '#fff' }).promise
      // Audiveris draws a PDF's pages without antialiasing: drawn music and text come out crisp, a
      // pixel black when its centre is inside a shape. PDF.js antialiases, and Audiveris reads the
      // grey edges as ink, so letters thicken and Tesseract reads "e" as "c" (60% of a test piece's
      // words, against 92%). So a page of drawn shapes is made black and white at half coverage,
      // as Audiveris would draw it; a page with images (a scan) keeps its greys, as Audiveris does.
      const crisp = !(await page.getOperatorList()).fnArray.some(f => IMAGE.has(f))
      const g = canvas.getContext('2d')
      pages.push(greyPage(canvas.width, canvas.height, g.getImageData(0, 0, canvas.width, canvas.height).data, crisp))
      canvas.width = canvas.height = 0
      page.cleanup()
    }
    return { pages: pages.map(({ w, h, grey }) => ({ w, h, grey })), checks: pages.map(p => p.check) }
  } finally {
    task.destroy() // and the worker with it
  }
}

/**
 * Each image is drawn (which applies a phone photo's rotation, and puts transparent PNGs on
 * white), made grey and put on a page of its own.
 */
export async function imagePages(files, onPage) {
  const pages = []
  for (const f of files) {
    onPage?.(pages.length + 1, files.length)
    let bitmap
    try {
      bitmap = await createImageBitmap(f, { imageOrientation: 'from-image' })
    } catch {
      throw new Error(`${f.name} couldn’t be opened as an image in this browser. Try a JPEG or PNG.`)
    }
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
    const w = Math.round(bitmap.width * scale)
    const h = Math.round(bitmap.height * scale)
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const g = canvas.getContext('2d', { willReadFrequently: true })
    g.fillStyle = '#fff'
    g.fillRect(0, 0, w, h)
    g.imageSmoothingQuality = 'high'
    g.drawImage(bitmap, 0, 0, w, h)
    bitmap.close()
    pages.push(greyPage(w, h, g.getImageData(0, 0, w, h).data))
    canvas.width = canvas.height = 0 // let go of the pixels now, not when collected
  }
  return { pages: pages.map(({ w, h, grey }) => ({ w, h, grey })), checks: pages.map(p => p.check) }
}

/**
 * A page from RGBA pixels: grey (by luminance), or only black and white if crisp; one byte a pixel.
 * A page that isn't crisp (a photo or a scan) also gets a quick look (preflight.js); drawn pages,
 * from notation software, don't need one.
 */
export function greyPage(w, h, rgba, crisp = false) {
  const grey = new Uint8Array(w * h)
  for (let i = 0, j = 0; i < grey.length; i++, j += 4) {
    const v = (rgba[j] * 77 + rgba[j + 1] * 150 + rgba[j + 2] * 29 + 128) >> 8
    grey[i] = crisp ? (v < 128 ? 0 : 255) : v
  }
  return { w, h, grey, check: crisp ? null : preflight(grey, w, h) }
}
