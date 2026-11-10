// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Tests for the lyric language: which language a read uses (app/language.js), and that the
// language data does what it is for, reading accented words that English data gets wrong.
//   node --test test/language.test.mjs
import test from 'node:test'
import assert from 'node:assert/strict'
import { createWorker } from 'tesseract.js'
import {
  DEFAULT_LANGUAGE, LANGUAGES, LANGUAGE_CODES,
  isSupportedLanguage, normalizeLanguageSpec, workerLanguages, resolveOcrLanguage,
} from '../app/language.js'

const root = new URL('..', import.meta.url).pathname

test('the six languages, English first and default', () => {
  assert.equal(DEFAULT_LANGUAGE, 'eng')
  assert.deepEqual(LANGUAGE_CODES, ['eng', 'deu', 'fra', 'ita', 'spa', 'lat'])
  assert.deepEqual(LANGUAGES.map(l => l.name),
    ['English', 'German', 'French', 'Italian', 'Spanish', 'Latin'])
})

test('isSupportedLanguage: the six codes, case-insensitive; nothing else', () => {
  for (const code of LANGUAGE_CODES) assert.ok(isSupportedLanguage(code), code)
  assert.ok(isSupportedLanguage('DEU'))
  assert.ok(isSupportedLanguage(' deu '))
  for (const bad of ['xx', 'en', 'ger', 'de', '', 'eng+xx', null, undefined, 42]) {
    assert.ok(!isSupportedLanguage(bad), String(bad))
  }
})

test('normalizeLanguageSpec: single codes, case/space, and Audiveris "+" specs', () => {
  assert.equal(normalizeLanguageSpec('deu'), 'deu')
  assert.equal(normalizeLanguageSpec('DEU'), 'deu')
  assert.equal(normalizeLanguageSpec(' deu '), 'deu')
  assert.equal(normalizeLanguageSpec('deu+eng'), 'deu+eng')
  assert.equal(normalizeLanguageSpec('eng+deu'), 'eng+deu')
  assert.equal(normalizeLanguageSpec('deu+deu'), 'deu')
  for (const bad of ['xx', 'deu+xx', 'eng+', '+', '', ' ', null, undefined, 42]) {
    assert.equal(normalizeLanguageSpec(bad), null, String(bad))
  }
})

test('workerLanguages: an array for tesseract.js, English when the spec is bad', () => {
  assert.deepEqual(workerLanguages('deu'), ['deu'])
  assert.deepEqual(workerLanguages('deu+eng'), ['deu', 'eng'])
  assert.deepEqual(workerLanguages('xx'), ['eng'])
  assert.deepEqual(workerLanguages(null), ['eng'])
})

test('resolveOcrLanguage: a non-default panel choice wins over Audiveris\'s default', () => {
  // Audiveris's default is always 'eng' (Language.ocrDefaultLanguages), so honouring
  // its spec first would make the selector dead — every read would come back 'eng'.
  assert.equal(resolveOcrLanguage('eng', 'deu'), 'deu')
  assert.equal(resolveOcrLanguage('eng', 'fra'), 'fra')
  assert.equal(resolveOcrLanguage(null, 'lat'), 'lat')
})

test('resolveOcrLanguage: an explicitly-set Audiveris language wins when the panel is on English', () => {
  assert.equal(resolveOcrLanguage('deu', 'eng'), 'deu')
  assert.equal(resolveOcrLanguage('fra', 'eng'), 'fra')
  assert.equal(resolveOcrLanguage('deu+eng', 'eng'), 'deu+eng')
})

test('resolveOcrLanguage: defaults and refusals fall through to English, never to no text', () => {
  assert.equal(resolveOcrLanguage('eng', 'eng'), 'eng')
  assert.equal(resolveOcrLanguage(null, null), 'eng')
  assert.equal(resolveOcrLanguage('', ''), 'eng')
  assert.equal(resolveOcrLanguage('xx', 'eng'), 'eng')
  assert.equal(resolveOcrLanguage('eng', 'xx'), 'eng')
  assert.equal(resolveOcrLanguage('deu+xx', 'eng'), 'eng')
})

// The page's settings for Tesseract (ocr.js): the legacy engine, and the 4.0.0 data build.sh serves.
async function ocr(lang, image) {
  const w = await createWorker(lang, 0, {
    legacyCore: true, legacyLang: true, cacheMethod: 'none',
    langPath: `${root}node_modules/@tesseract.js-data/${lang}/4.0.0`,
  })
  try {
    return (await w.recognize(`${root}test/fixtures/${image}`)).data.text.trim()
  } finally {
    await w.terminate()
  }
}

test('German data reads umlauts and ß that English data gets wrong', async () => {
  const words = ['Grü-', 'ße,', 'schö-', 'Mül-']
  const got = await ocr('deu', 'lyrics-deu.png')
  for (const word of words) assert.ok(got.includes(word), `${word} in ${got}`)
  const english = await ocr('eng', 'lyrics-deu.png')
  assert.ok(words.some(word => !english.includes(word)), english)
})

test('French data reads accents that English data gets wrong', async () => {
  const words = ['ël,', 'fê-', 'où', 'ê-']
  const got = await ocr('fra', 'lyrics-fra.png')
  for (const word of words) assert.ok(got.includes(word), `${word} in ${got}`)
  const english = await ocr('eng', 'lyrics-fra.png')
  assert.ok(words.some(word => !english.includes(word)), english)
})
