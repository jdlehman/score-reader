// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The language of the words under the notes (lyrics, titles, part names).
//
// Audiveris reads text with Tesseract, which is native code CheerpJ can't run, so the page reads
// it with tesseract.js instead (see ocr.js). That worker was English-only: createWorker('eng').
// The page now offers six languages; each is a tesseract.js language pack
// (@tesseract.js-data/<code> 1.0.0, MIT, the 4.0.0 data Audiveris's legacy engine needs —
// NOT tessdata_fast, whose integer models only work with the LSTM engine).
// A pack is ~6-14 MB, downloaded once and kept by the browser afterwards.
//
// This module is pure (no DOM, no worker, no imports) so node --test can cover it directly.
// The only place a language is chosen is here: ocr.js and reader.js both go through it.

/** The language used when nothing else says otherwise. Audiveris's own default, too. */
export const DEFAULT_LANGUAGE = 'eng'

/** The languages the pick panel offers, in the order it offers them. */
export const LANGUAGES = [
  { code: 'eng', name: 'English' },
  { code: 'deu', name: 'German' },
  { code: 'fra', name: 'French' },
  { code: 'ita', name: 'Italian' },
  { code: 'spa', name: 'Spanish' },
  { code: 'lat', name: 'Latin' },
]

export const LANGUAGE_CODES = LANGUAGES.map(l => l.code)

export function isSupportedLanguage(code) {
  return typeof code === 'string' && LANGUAGE_CODES.includes(code.trim().toLowerCase())
}

/**
 * Canonical form of a language specification, or null if it names nothing supported.
 *
 * A spec is one code, or several joined with '+', as Audiveris writes them
 * (Language.codesOf splits on '+': "deu+eng"). Case and surrounding space are ignored.
 * Every code in a '+' spec must be supported, or the whole spec is refused — a half-supported
 * spec would silently read in the wrong language.
 * Multi-language specs are supported here (tesseract.js takes an array of codes), but the
 * pick panel offers one language at a time; a '+' spec can only arrive from Audiveris.
 */
export function normalizeLanguageSpec(spec) {
  if (typeof spec !== 'string') return null
  const codes = spec.split('+').map(c => c.trim().toLowerCase())
  if (!codes.length) return null
  // Every part must be a supported code: a malformed spec ('eng+', 'deu+xx') is
  // refused whole, not silently repaired to the part that happened to work.
  if (!codes.every(c => c && LANGUAGE_CODES.includes(c))) return null
  return [...new Set(codes)].join('+')
}

/** The codes of a canonical spec, as tesseract.js wants them (an array). */
export function workerLanguages(spec) {
  const canonical = normalizeLanguageSpec(spec)
  return canonical ? canonical.split('+') : [DEFAULT_LANGUAGE]
}

/**
 * Which language a read actually uses, from the two places that can name one.
 *
 * @param javaSpec the `languages` string Audiveris passes to BrowserOCR_read
 * @param uiLanguage the value of the pick panel's selector (a single code)
 * @returns a canonical spec string
 *
 * The order is deliberate, and the opposite of what it looks like it should be:
 * Audiveris's default language is always 'eng' (Language.ocrDefaultLanguages), so
 * honouring the Java spec first would make the selector dead — every read would come
 * back 'eng' no matter what the user picked. So:
 *   1. a non-default UI choice wins — the user just picked it for this score;
 *   2. otherwise a Java spec wins, if it names a supported language (or languages) —
 *      that is how an explicitly-set Audiveris language reaches the page;
 *   3. otherwise the UI choice (which is 'eng' by default);
 *   4. otherwise 'eng'.
 * An unsupported or empty spec anywhere falls through to the next step, never to a
 * refusal: Audiveris would otherwise return no text at all for that image
 * (OcrUtil.scan returns empty when ocr.supports(languages) is false).
 */
export function resolveOcrLanguage(javaSpec, uiLanguage) {
  const ui = normalizeLanguageSpec(uiLanguage)
  if (ui && ui !== DEFAULT_LANGUAGE) return ui
  const java = normalizeLanguageSpec(javaSpec)
  if (java) return java
  if (ui) return ui
  return DEFAULT_LANGUAGE
}
