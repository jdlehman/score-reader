// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reading text for Audiveris: the words, titles and part names. Audiveris reads text with
// Tesseract, which is native code, so the page reads it with tesseract.js (the same Tesseract, in
// WebAssembly) and hands Audiveris the lines, words and characters (see BrowserOCR.java in patches/,
// and how teavm.js passes them).

import { DEFAULT_LANGUAGE, normalizeLanguageSpec, workerLanguages } from './language.js'

const BASE = new URL('./', import.meta.url)
/** Tesseract's legacy engine, as Audiveris uses (the newer one doesn't report its words' fonts). */
const LEGACY = 0
/** Audiveris tells Tesseract its images are 70 dpi (TesseractOrder's typicalImageResolution). */
const DPI = 70

/**
 * The characters Audiveris splits lyric words at (LyricItemInter.isSeparator: '-', U+203F, '_',
 * U+2013, U+2014). Tesseract joins hyphenated syllables into one word ("Hal—le—lu—jah,"), and
 * Audiveris splits such a word only in a line it already takes for lyrics (TextLine.splitWords);
 * elsewhere the word stays whole and attaches to one note, and the other syllables are lost (52 of
 * 208 on Hallelujah p.1).
 */
export const LYRIC_SEPARATORS = new Set(['-', '‿', '_', '–', '—'])

/**
 * Split one tesseract.js word after each separator that a syllable follows, keeping the separator
 * on the syllable before it: "Hal—le—lu—jah," becomes "Hal—", "le—", "lu—", "jah,". Each syllable
 * then reaches a note of its own, and its separator still says it goes on: in a line Audiveris
 * takes for lyrics it splits that off as a hyphen, which makes the syllables begin, middle and end
 * ones (LyricItemInter.defineSyllabicType), so the score keeps "Hal-le-lu-jah" one word. (Dropping
 * the separators made every syllable a word of its own; giving them words of their own lost most
 * of Hallelujah p.1's syllables in the browser, 45% against 75% unsplit.) Returns the pieces
 * ({ text, bbox, symbols }), or null to leave the word as it is: no separator with a syllable
 * after it, a piece with no letter in it (not lyrics), or symbols that don't spell the word (so
 * their boxes can't be trusted).
 */
export function splitWordAtSeparators(word) {
  const text = word.text.replace(/\s+/g, '')
  if (!text || ![...text].some(ch => LYRIC_SEPARATORS.has(ch))) return null
  const symbols = (word.symbols ?? [])
    .map(s => ({ text: s.text.replace(/\s+/g, ''), bbox: s.bbox }))
    .filter(s => s.text)
  if (symbols.map(s => s.text).join('') !== text) return null
  const pieces = []
  let piece = []
  for (const symbol of symbols) {
    const separator = LYRIC_SEPARATORS.has(symbol.text)
    const last = piece[piece.length - 1]
    // a new syllable starts after a separator that follows a syllable
    if (!separator && last && LYRIC_SEPARATORS.has(last.text) && piece.some(s => !LYRIC_SEPARATORS.has(s.text))) {
      pieces.push(piece)
      piece = []
    }
    piece.push(symbol)
  }
  pieces.push(piece)
  // syllables have letters: OCR also reads a triplet bracket as "|—3—|", and a date as "1639-1699"
  if (pieces.length < 2 || !pieces.every(p => p.some(s => /\p{L}/u.test(s.text)))) return null
  return pieces.map(symbols => ({
    text: symbols.map(s => s.text).join(''),
    bbox: {
      x0: Math.min(...symbols.map(s => s.bbox.x0)),
      y0: Math.min(...symbols.map(s => s.bbox.y0)),
      x1: Math.max(...symbols.map(s => s.bbox.x1)),
      y1: Math.max(...symbols.map(s => s.bbox.y1)),
    },
    symbols,
  }))
}

let worker = null
/** The canonical spec ('deu', or 'deu+eng') the current worker was created for, if any. */
let workerLanguage = null
/** The worker being created, if any: concurrent startOcr calls share one creation. */
let starting = null
/** Languages whose data failed to load: read in English from then on, rather than retry for every image. */
const failed = new Set()

/**
 * Start Tesseract, and its language data, downloading: ~6-14 MB a language, kept by the
 * browser afterwards. Loaded only now, so that a failure here leaves the words out but
 * never stops the reading.
 *
 * One worker serves one language (tesseract.js v7 has no safe public way to re-language
 * an already-booted worker, so a different language terminates this worker and starts a
 * new one). A read picks its language once, before Audiveris starts, so that never happens
 * mid-read; it only matters if Audiveris asks for a different language than the page
 * preloaded. If the pack fails to load, fall back to English and warn — never stop the
 * read for a missing language pack.
 */
export async function startOcr(language) {
  let spec = normalizeLanguageSpec(language) ?? DEFAULT_LANGUAGE
  if (failed.has(spec)) spec = DEFAULT_LANGUAGE
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
      failed.add(spec)
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
          const pieces = splitWordAtSeparators(word)
          const emit = pieces ?? [{ text, bbox: word.bbox, symbols: word.symbols ?? [] }]
          for (const piece of emit) {
            out.push(`W ${box(piece.bbox)} ${Math.round(word.confidence)} ${piece.text}`)
            for (const symbol of piece.symbols) {
              const s = symbol.text.replace(/\s+/g, '')
              if (s) out.push(`C ${box(symbol.bbox)} ${s}`)
            }
          }
        }
      }
    }
  }
  return out.join('\n')
}
