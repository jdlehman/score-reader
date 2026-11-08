// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Tests for the lyric-language selector (PR 5).
//
// What is covered here, and what is not:
//   - app/language.js is pure (no DOM, no worker), so its selection logic is tested directly.
//   - The UI, the Java patch, build.sh and package.json are pinned by reading the files
//     the PR changes — a static check, labelled as such, because the real UI needs a
//     browser and the real Java needs Audiveris. The e2e test (not run in this VM) is
//     the place that exercises the selector end to end in Chrome/CheerpJ.
//   - The measured deu-vs-eng numbers are pinned to tools/lang-compare-results.json.
//     They show NO accuracy gain from 'deu' on the clean German lyric strips (see the
//     last test): this PR is selector infrastructure, not an accuracy claim, and the
//     test pins that fact so a future accuracy claim has a failing test to beat.
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import {
  DEFAULT_LANGUAGE, LANGUAGES, LANGUAGE_CODES,
  isSupportedLanguage, normalizeLanguageSpec, workerLanguages, resolveOcrLanguage,
} from '../app/language.js'

const root = new URL('..', import.meta.url).pathname
const read = async p => readFile(root + p, 'utf-8')

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

test('UI (static): the pick panel has a selector with the six languages, English selected', async () => {
  const html = await read('app/index.html')
  assert.ok(html.includes('<select id="ocr-language">'), 'select exists')
  const options = [...html.matchAll(/<option value="([a-z]+)"( selected)?>([^<]+)<\/option>/g)]
    .filter(([, , , name]) => ['English', 'German', 'French', 'Italian', 'Spanish', 'Latin'].includes(name))
  assert.deepEqual(options.map(o => o[1]), ['eng', 'deu', 'fra', 'ita', 'spa', 'lat'])
  assert.ok(options.find(o => o[1] === 'eng')[2], 'English is selected by default')
  assert.ok(/Language of the words/.test(html), 'labelled as the lyric/text language')
  assert.ok(/6–14 MB/.test(html), 'the note says what a pack costs to download')
})

test('Java patch (static): BrowserOCR.LANGUAGES contains all six codes', async () => {
  const patch = await read('patches/0001-score-reader.patch')
  const m = patch.match(/new TreeSet<>\(List\.of\(([^)]+)\)\)/)
  assert.ok(m, 'LANGUAGES list found in the patch')
  for (const code of LANGUAGE_CODES) assert.ok(m[1].includes(`"${code}"`), code)
  assert.ok(!m[1].includes('List.of("eng")'), 'the old eng-only list is gone')
})

test('build + package (static): all six packs are dependencies and copied to dist/tessdata', async () => {
  const pkg = JSON.parse(await read('package.json'))
  for (const code of LANGUAGE_CODES) {
    assert.equal(pkg.dependencies[`@tesseract.js-data/${code}`], '1.0.0', code)
  }
  const build = await read('build.sh')
  assert.ok(build.includes('for lang in deu eng fra ita lat spa; do'), 'build loops over all six')
  assert.ok(build.includes('node_modules/@tesseract.js-data/$lang/4.0.0/$lang.traineddata.gz'), 'packs copied from npm, not vendored')
  assert.ok(build.includes('app/language.js'), 'language.js is copied to dist/')
  assert.ok(build.includes('tessdata_fast is LSTM-only'), 'the fast data is documented as unusable here, not silently copied')
})

test('wiring (static): reader.js resolves the language and ocr.js starts the worker in it', async () => {
  const reader = await read('app/reader.js')
  assert.ok(reader.includes("resolveOcrLanguage(languages, ocrLanguage)"), 'Audiveris spec resolved against the panel choice')
  assert.ok(reader.includes("startOcr(ocrLanguage)"), 'worker preloaded in the picked language')
  assert.ok(reader.includes("$('ocr-language')"), 'panel value read at the start of a read')
  const ocr = await read('app/ocr.js')
  assert.ok(ocr.includes('export async function startOcr(language)'), 'startOcr takes a language')
  assert.ok(ocr.includes('workerLanguages(spec)'), 'worker created with the resolved codes')
  assert.ok(ocr.includes('could not load, so the words will be read in English'), 'pack failure falls back to English')
  assert.ok(ocr.includes('terminate()'), 'a worker for another language is terminated, not kept alongside')
  assert.ok(ocr.includes("export async function readText(grey, width, height, pageSegMode, languages)"), 'readText takes the resolved language')
})

test('measured: German does NOT measurably beat English on the clean German lyric strips', async () => {
  // tools/lang-compare-results.json, PR 4 harness method (legacy OEM 1, dpi 70, PSM 6,
  // grey), language the only change. Lindenbaum 14 syllables, Gute Nacht 18.
  const rows = JSON.parse(await read('tools/lang-compare-results.json'))
  assert.equal(rows.length, 4)
  for (const lang of ['eng', 'deu']) {
    const r = rows.filter(x => x.lang === lang)
    assert.equal(r.reduce((n, x) => n + x.hits, 0), 28, `${lang} hits`)
    assert.equal(r.reduce((n, x) => n + x.ref, 0), 32, `${lang} ref syllables`)
    assert.ok(r.every(x => x.charSim === 1), `${lang} character similarity is 1.0 on both lines`)
  }
  // Identical words in both languages, line for line — the 4 Gute Nacht misses are
  // the same in both. This PR is selector infrastructure, not an accuracy claim.
  const byLine = {}
  for (const r of rows) (byLine[r.page] ??= {})[r.lang] = r.got
  for (const page of Object.keys(byLine)) {
    assert.equal(byLine[page].eng, byLine[page].deu, `${page}: eng and deu read the same words`)
  }
})
