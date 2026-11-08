// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// What Audiveris reads: a PDF of grey pages, drawn here from the PDF or photos chosen.
//
// Audiveris can read PDFs and images itself, but in the browser only the simplest ones. Java's
// JPEG decoder is native code that CheerpJ can't finish running (a phone scan's PDF is all
// JPEGs), and so is its colour management. So the page draws everything itself, the PDF with
// PDF.js and photos with the browser, and hands Audiveris raw grey pixels compressed with
// deflate, which Java reads in Java.

import { preflight } from './preflight.js'

/** Audiveris draws a PDF's pages at 300 dpi; pages this size come out at the images' own size. */
const DPI = 300

/** Bigger pages are scaled down to this on their long side: more pixels only slow the reading. */
const MAX_SIDE = 4096

const PDFJS = new URL('pdfjs/', import.meta.url)

/** A PDF's pages, drawn at 300 dpi with PDF.js. onPage(n, of) tells how far it has got. */
export async function pdfToPdf(bytes, onPage) {
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
      // The preflight (see preflight.js) runs on the grey pixels, before they are deflated:
      // if the page looks unreadable, the reader warns to rescan instead of spending a
      // minute a page on it. The deskewed copy is dropped here — only the verdict is kept.
      const grey = toGrey(canvas.width, canvas.height, g.getImageData(0, 0, canvas.width, canvas.height).data, crisp)
      const verdict = preflight(grey, canvas.width, canvas.height)
      delete verdict.deskewedGrey
      pages.push({ w: canvas.width, h: canvas.height, data: await deflate(grey), preflight: verdict })
      canvas.width = canvas.height = 0
      page.cleanup()
    }
    return { bytes: writePdf(pages), preflight: pages.map(p => p.preflight) }
  } finally {
    task.destroy() // and the worker with it
  }
}

/**
 * Each image is drawn (which applies a phone photo's rotation, and puts transparent PNGs on
 * white), made grey and put on a page of its own.
 */
export async function imagesToPdf(files, onPage) {
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
    // Photos are the pages most likely to be unreadable, so they get the same preflight
    // check as PDF pages (see pdfToPdf above).
    const grey = toGrey(w, h, g.getImageData(0, 0, w, h).data)
    const verdict = preflight(grey, w, h)
    delete verdict.deskewedGrey
    pages.push({ w, h, data: await deflate(grey), preflight: verdict })
    canvas.width = canvas.height = 0 // let go of the pixels now, not when collected
  }
  return { bytes: writePdf(pages), preflight: pages.map(p => p.preflight) }
}

/** Grey pixels from RGBA: by luminance, or only black and white if crisp. */
export function toGrey(w, h, rgba, crisp = false) {
  const grey = new Uint8Array(w * h)
  for (let i = 0, j = 0; i < grey.length; i++, j += 4) {
    const v = (rgba[j] * 77 + rgba[j + 1] * 150 + rgba[j + 2] * 29 + 128) >> 8
    grey[i] = crisp ? (v < 128 ? 0 : 255) : v
  }
  return grey
}

/** A page from RGBA pixels: grey (by luminance), or only black and white if crisp; one byte a pixel, deflated. */
export async function greyPage(w, h, rgba, crisp = false) {
  return { w, h, data: await deflate(toGrey(w, h, rgba, crisp)) }
}

/** zlib-wrapped deflate, which is what a PDF's FlateDecode reads. */
async function deflate(bytes) {
  const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

/** The smallest PDF that does: a catalog, the page tree, and per page its page, contents and image. */
export function writePdf(pages) {
  const enc = new TextEncoder()
  const chunks = []
  const offsets = []
  let length = 0
  const put = x => {
    const b = typeof x === 'string' ? enc.encode(x) : x
    chunks.push(b)
    length += b.length
  }
  const obj = (n, body) => {
    offsets[n] = length
    put(`${n} 0 obj\n`)
    body()
    put('\nendobj\n')
  }
  const at = i => ({ page: 3 + 3 * i, contents: 4 + 3 * i, image: 5 + 3 * i })

  put('%PDF-1.4\n%âãÏÓ\n') // the second line marks the file as binary
  obj(1, () => put('<< /Type /Catalog /Pages 2 0 R >>'))
  obj(2, () => put(`<< /Type /Pages /Count ${pages.length} /Kids [${pages.map((_, i) => `${at(i).page} 0 R`).join(' ')}] >>`))
  pages.forEach((p, i) => {
    const w = ((p.w * 72) / DPI).toFixed(2)
    const h = ((p.h * 72) / DPI).toFixed(2)
    const n = at(i)
    obj(n.page, () => put(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${w} ${h}] /Resources << /XObject << /Im ${n.image} 0 R >> >> /Contents ${n.contents} 0 R >>`))
    const draw = `q ${w} 0 0 ${h} 0 0 cm /Im Do Q`
    obj(n.contents, () => put(`<< /Length ${draw.length} >>\nstream\n${draw}\nendstream`))
    obj(n.image, () => {
      put(`<< /Type /XObject /Subtype /Image /Width ${p.w} /Height ${p.h} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length ${p.data.length} >>\nstream\n`)
      put(p.data)
      put('\nendstream')
    })
  })
  const size = 3 + 3 * pages.length
  const xref = length
  put(`xref\n0 ${size}\n0000000000 65535 f \n`)
  for (let n = 1; n < size; n++) put(`${String(offsets[n]).padStart(10, '0')} 00000 n \n`)
  put(`trailer\n<< /Size ${size} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`)

  const out = new Uint8Array(length)
  let o = 0
  for (const c of chunks) {
    out.set(c, o)
    o += c.length
  }
  return out
}
