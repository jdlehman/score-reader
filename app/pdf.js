// What Audiveris reads: a PDF of grey pages, drawn here from the PDF or photos chosen.
//
// Audiveris can read PDFs and images itself, but in the browser only the simplest ones. Java's
// JPEG decoder is native code that CheerpJ can't finish running (a phone scan's PDF is all
// JPEGs), and so is its colour management. So the page draws everything itself, the PDF with
// PDF.js and photos with the browser, and hands Audiveris raw grey pixels compressed with
// deflate, which Java reads in Java.
//
// Copyright (C) 2026 Jonathan Lehman. GNU AGPL v3 or later: see LICENSE.txt.

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
      const g = canvas.getContext('2d')
      pages.push(await greyPage(canvas.width, canvas.height, g.getImageData(0, 0, canvas.width, canvas.height).data))
      canvas.width = canvas.height = 0
      page.cleanup()
    }
    return writePdf(pages)
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
    pages.push(await greyPage(w, h, g.getImageData(0, 0, w, h).data))
    canvas.width = canvas.height = 0 // let go of the pixels now, not when collected
  }
  return writePdf(pages)
}

/** A page from RGBA pixels: grey (by luminance), one byte a pixel, deflated. */
export async function greyPage(w, h, rgba) {
  const grey = new Uint8Array(w * h)
  for (let i = 0, j = 0; i < grey.length; i++, j += 4) {
    grey[i] = (rgba[j] * 77 + rgba[j + 1] * 150 + rgba[j + 2] * 29 + 128) >> 8
  }
  return { w, h, data: await deflate(grey) }
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
