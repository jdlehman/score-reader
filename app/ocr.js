// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reading text for Audiveris: the words, titles and part names. Audiveris reads text with
// Tesseract, which is native code that CheerpJ can't run, so the page reads it with tesseract.js
// (the same Tesseract, in WebAssembly) and hands Java the lines, words and characters (see
// BrowserOCR.java in patches/).

import { DEFAULT_LANGUAGE, normalizeLanguageSpec, workerLanguages } from './language.js'

const BASE = new URL('./', import.meta.url)
/** Tesseract's legacy engine, as Audiveris uses (the newer one doesn't report its words' fonts). */
const LEGACY = 0
/** Audiveris tells Tesseract its images are 70 dpi (TesseractOrder's typicalImageResolution). */
const DPI = 70

let worker = null
/** The canonical spec ('deu', or 'deu+eng') the current worker was created for, if any. */
let workerLanguage = null
/** The worker being created, if any: concurrent startOcr calls share one creation. */
let starting = null

/**
 * Start Tesseract, and its language data, downloading: ~6-14 MB a language, kept by the
 * browser afterwards. Loaded only now, so that a failure here leaves the words out but
 * never stops the reading.
 *
 * One worker serves one language (tesseract.js v7 has no safe public way to re-language
 * an already-booted worker, so a different language terminates this worker and starts a
 * new one). A read picks its language once, before CheerpJ starts, so that never happens
 * mid-read; it only matters if Audiveris asks for a different language than the page
 * preloaded. If the pack fails to load, fall back to English and warn — never stop the
 * read for a missing language pack.
 */
export async function startOcr(language) {
  const spec = normalizeLanguageSpec(language) ?? DEFAULT_LANGUAGE
  if (worker && workerLanguage === spec) return worker
  if (starting) {
    // A worker for some language is already being created: wait for it, then switch
    // to this one if it is not the one wanted. Two creations must never run at once.
    const started = await starting
    if (workerLanguage === spec) return started
  }
  starting = startOcrFor(spec)
  try {
    return await starting
  } finally {
    starting = null
  }
}

async function startOcrFor(spec) {
  const previous = worker
  let next
  try {
    next = await createWorkerFor(spec)
  } catch (e) {
    if (spec !== DEFAULT_LANGUAGE) {
      console.warn(`Tesseract data for '${spec}' could not load, so the words will be read in English:`, e)
      next = await createWorkerFor(DEFAULT_LANGUAGE)
      worker = next
      workerLanguage = DEFAULT_LANGUAGE
      if (previous) previous.terminate().catch(() => {})
      return worker
    }
    throw e
  }
  worker = next
  workerLanguage = spec
  // The old worker, if any, is done with: terminate it after the new one is up, so a
  // read in flight keeps a worker until its replacement exists.
  if (previous) previous.terminate().catch(() => {})
  return worker
}

async function createWorkerFor(spec) {
  const { default: Tesseract } = await import('./tesseract/tesseract.esm.min.js')
  const langs = workerLanguages(spec)
  return Tesseract.createWorker(langs.length === 1 ? langs[0] : langs, LEGACY, {
    legacyCore: true,
    legacyLang: true,
    workerPath: new URL('tesseract/worker.min.js', BASE).href,
    workerBlobURL: false,
    corePath: new URL('tesseract/', BASE).href,
    langPath: new URL('tessdata', BASE).href,
  })
}

/** The language the current worker reads, or null if none has started. */
export function ocrLanguage() {
  return workerLanguage
}

/**
 * Read the text in a grey image (Java's byte[], one byte a pixel): the answer BrowserOCR.read
 * parses, a line per text line, word and character.
 * `languages` is the canonical spec resolved by reader.js (Audiveris's spec, the pick
 * panel's choice, or 'eng'); an unsupported one falls back to English inside startOcr.
 */
export async function readText(grey, width, height, pageSegMode, languages) {
  const w = await startOcr(languages)
  await w.setParameters({ tessedit_pageseg_mode: String(pageSegMode), user_defined_dpi: String(DPI) })
  const pixels = new Uint8Array(grey.buffer, grey.byteOffset, width * height)
  const rgba = new Uint8ClampedArray(width * height * 4)
  for (let i = 0, j = 0; i < pixels.length; i++, j += 4) {
    rgba[j] = rgba[j + 1] = rgba[j + 2] = pixels[i]
    rgba[j + 3] = 255
  }
  const canvas = new OffscreenCanvas(width, height)
  canvas.getContext('2d').putImageData(new ImageData(rgba, width, height), 0, 0)
  const { data } = await w.recognize(await canvas.convertToBlob({ type: 'image/png' }), {}, { blocks: true, text: false })

  const out = []
  const box = b => `${b.x0} ${b.y0} ${b.x1} ${b.y1}`
  for (const block of data.blocks ?? []) {
    for (const paragraph of block.paragraphs) {
      for (const line of paragraph.lines) {
        const base = line.baseline ?? { x0: line.bbox.x0, y0: line.bbox.y1, x1: line.bbox.x1, y1: line.bbox.y1 }
        const rowHeight = Math.round(line.rowAttributes?.row_height ?? line.bbox.y1 - line.bbox.y0)
        out.push(`L ${box(line.bbox)} ${Math.round(base.x0)} ${Math.round(base.y0)} ${Math.round(base.x1)} ${Math.round(base.y1)} ${Math.round(rowHeight * 72 / DPI)}`)
        for (const word of line.words) {
          const text = word.text.replace(/\s+/g, '')
          if (!text) continue
          out.push(`W ${box(word.bbox)} ${Math.round(word.confidence)} ${text}`)
          for (const symbol of word.symbols ?? []) {
            const s = symbol.text.replace(/\s+/g, '')
            if (s) out.push(`C ${box(symbol.bbox)} ${s}`)
          }
        }
      }
    }
  }
  return out.join('\n')
}
