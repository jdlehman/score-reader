// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Read grey pages with the TeaVM build in Node, as the page's worker does (app/teavm.js).
//   node --experimental-wasm-exnref teavm/node/read.mjs <out.musicxml> <page.grey> <page.json> [<page.grey> <page.json>]...
// Each page is its grey pixels (a byte each) and a JSON file with its width and height.
// OCR=deu (or eng, fra, ...) reads the words too, with tesseract.js, as the page does (the corpus
// passes each case's language); without it, words are left out. WASM=<dir> reads with another
// build than .work/teavm/out. CONSTANTS='a=1,b=2' adds Audiveris settings after the page's.
// PRE=<module> and POST=<module> add a step before or after the read, to measure one the page
// doesn't have yet (test/prove.mjs): PRE's default export takes the pages ({ w, h, grey }) and
// returns the pages to read; POST's takes the scores (MusicXML text) and the pages, and returns
// the scores to write.
// A score with several movements is written as <out>.mvt1.musicxml, <out>.mvt2.musicxml, ...
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { readScore } from '../../app/teavm.js'
import { READING } from '../../app/settings.js'

const [out, ...files] = process.argv.slice(2)
if (!out || !files.length || files.length % 2) {
  console.error('usage: read.mjs <out.musicxml> <page.grey> <page.json> [<page.grey> <page.json>]...')
  process.exit(2)
}
const root = fileURLToPath(new URL('../../', import.meta.url))
const dir = resolve(process.env.WASM ?? `${root}.work/teavm/out`)
const { load } = await import(`${dir}/runtime.mjs`)
let pages = []
for (let i = 0; i < files.length; i += 2) {
  const meta = JSON.parse(readFileSync(files[i + 1], 'utf8'))
  pages.push({ w: meta.width, h: meta.height, grey: new Uint8Array(readFileSync(files[i])) })
}
const step = async name => process.env[name] && (await import(pathToFileURL(resolve(process.env[name])).href)).default
const [pre, post] = [await step('PRE'), await step('POST')]

let ocr, stopOcr
if (process.env.OCR) {
  const tesseract = await import('./ocr-run.mjs')
  ocr = image => tesseract.readText(Buffer.from(image.grey), image.width, image.height, image.pageSegMode, image.languages)
  stopOcr = tesseract.stopOcr
}

const t0 = Date.now()
let at = t0
if (pre) pages = await pre(pages)
let { scores, failed } = await readScore({
  teavm: await load(`${dir}/classes.wasm`),
  pages,
  constants: [...READING, ...(process.env.CONSTANTS ? process.env.CONSTANTS.split(',') : [])],
  languages: process.env.OCR ?? '',
  ocr,
  templates: (family, size) => {
    const file = `${dir}/templates/${family}-${size}.bin`
    return existsSync(file) ? readFileSync(file) : null
  },
  onStep: (page, step) => {
    const now = Date.now()
    console.log(`STEP page ${page} ${step} (${((now - at) / 1000).toFixed(1)} s since the last)`)
    at = now
  },
})
if (post && scores.length) scores = await post(scores, pages)
console.log(`read in ${((Date.now() - t0) / 1000).toFixed(1)} s: ${scores.length} score(s)${failed.length ? `, left out page(s) ${failed.join(', ')}` : ''}`)
if (scores.length === 1) writeFileSync(out, scores[0])
else scores.forEach((xml, i) => writeFileSync(out.replace(/(\.musicxml)?$/, `.mvt${i + 1}.musicxml`), xml))
await stopOcr?.() // Tesseract's worker would keep Node running
process.exit(scores.length ? 0 : 1)
