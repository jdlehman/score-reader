// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reads the test corpus with desktop Audiveris, patched and set up as the page reads (see
// app/settings.js), scores each read against its answer (test/score.mjs), and compares the
// scores with the last saved ones (test/corpus/baseline.json).
//
//   node test/corpus.mjs                    read and score everything, compare with the baseline
//   node test/corpus.mjs lieder chorale     only cases whose name contains one of these
//   EXTRA=~/Downloads/choral-test-set node test/corpus.mjs
//                                           also the pieces that can't be in the repo (licences)
//   SAVE=1 node test/corpus.mjs             save these scores as the new baseline
//   JOBS=3 (default 2) Java processes at once; REUSE=1 scores the reads of the last run again
//   LIST=1 only lists the cases; SKIP=a,b leaves out cases whose name contains one of these
//   HOLDOUT=1 also reads the held-out pages (test/holdout), HOLDOUT=only reads only them: to confirm
//     a fix made without looking at them, never to make one
//   PATCHED=<jar> reads with other patched classes; CONSTANTS='a=1,b=2' with more settings, after
//     the page's (app/settings.js), so one of the same name replaces it (desktop only);
//   RUN=<name> keeps this run's reads apart (.work/corpus/<name>), to compare two builds
//   ENGINE=teavm reads with Audiveris in WebAssembly (teavm/node/read.mjs), from the grey pixels the
//     page would hand it (test/grey.py), against the desktop's baseline; PDFs are left out (the page
//     draws them with PDF.js). Needs teavm/build.sh first; never saved as the baseline.
//
// Needs ./setup.sh and ./build.sh first (the Audiveris jars and our patched classes in .work/).
// A case is an image or a PDF. Next to it, <name>.json is its answer (every pitched note, by
// bar); without one only "was it read" and the part count are reported. In EXTRA, photos in
// photo-synthetic/ take their answer from pages/<page>.json.
import { execFile } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { basename, extname, join, resolve } from 'node:path'
import { promisify } from 'node:util'
import { READING, asArgs } from '../app/settings.js'
import { ROOT, allCases, joined, reads } from './cases.mjs'
import { parseMusicXml, score } from './score.mjs'

const WORK = join(ROOT, '.work')
const OUT = join(WORK, 'corpus', process.env.RUN ?? 'last')
const BASELINE = join(ROOT, 'test', 'corpus', 'baseline.json')
const JOBS = Number(process.env.JOBS ?? 2)
const TEAVM = process.env.ENGINE === 'teavm'
if (TEAVM && process.env.SAVE) {
  console.error('The baseline is the desktop\'s: ENGINE=teavm compares with it, and is never saved.')
  process.exit(2)
}
const filters = process.argv.slice(2)

const java = join(WORK, 'jdk', readdirSync(join(WORK, 'jdk')).find(d => d.startsWith('jdk')), 'Contents', 'Home', 'bin', 'java')
const classpath = [resolve(process.env.PATCHED ?? join(WORK, 'patched.jar')), ...readFileSync(join(WORK, 'classpath.txt'), 'utf8').trim().split(':').map(j => join(ROOT, j.replace(/^\/app\//, '')))].join(':')

/** Runs work(item) for every item, at most `jobs` at once; the results in the items' order. */
async function pool(items, jobs, work) {
  const out = []
  let next = 0
  const worker = async () => { while (next < items.length) { const i = next++; out[i] = await work(items[i]) } }
  await Promise.all(Array.from({ length: Math.min(jobs, items.length) }, worker))
  return out
}

/** Reads some cases in one Java process (one book each), each into OUT/<name>/. */
async function read(batch) {
  const dir = join(OUT, `batch-${batch.index}`)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const args = [
    '-Xmx3g', '-Dscorereader.skipFailedPages=true', '-Dscorereader.keepSheets=true',
    '-cp', classpath, 'org.audiveris.omr.Main',
    '-batch',
    // the page reads words with tesseract.js; here Tesseract stays off (its native libraries
    // aren't in the page's jar list), so lyrics aren't scored on the desktop
    ...asArgs(['org.audiveris.omr.text.tesseract.TesseractOCR.useOCR=false']),
    ...asArgs([...READING, ...(process.env.CONSTANTS ? process.env.CONSTANTS.split(',') : [])]), '-transcribe', '-export', '-output', dir,
    ...batch.map(c => c.input),
  ]
  const started = Date.now()
  let log = ''
  try {
    const r = await promisify(execFile)(java, args, { maxBuffer: 1 << 28, timeout: (10 + 5 * batch.length) * 60_000 }) // minutes: a hard photo can take 4
    log = r.stdout + r.stderr
  } catch (e) {
    log = (e.stdout ?? '') + (e.stderr ?? '') + '\n' + e.message
  }
  writeFileSync(join(dir, 'log.txt'), log)
  return { dir, seconds: Math.round((Date.now() - started) / 1000) }
}

/**
 * Reads one case with Audiveris in WebAssembly, as the page would: its image made grey as the
 * page makes it (test/grey.py), then teavm/node/read.mjs, into OUT/batch-<n>/.
 */
async function readWasm(batch) {
  const [c] = batch
  const dir = join(OUT, `batch-${batch.index}`)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const radix = join(dir, basename(c.input, extname(c.input)))
  const started = Date.now()
  let log = ''
  try {
    await promisify(execFile)('python3', ['-I', join(ROOT, 'test', 'grey.py'), c.input, radix])
    const r = await promisify(execFile)(process.execPath, ['--experimental-wasm-exnref', join(ROOT, 'teavm', 'node', 'read.mjs'), radix + '.musicxml', radix + '.grey', radix + '.json'],
      { maxBuffer: 1 << 28, timeout: 30 * 60_000, env: { ...process.env, OCR: '' } })
    log = r.stdout + r.stderr
  } catch (e) {
    log = (e.stdout ?? '') + (e.stderr ?? '') + '\n' + e.message
  }
  rmSync(radix + '.grey', { force: true })
  writeFileSync(join(dir, 'log.txt'), log)
  return { dir, seconds: Math.round((Date.now() - started) / 1000) }
}

/** The MusicXML files Audiveris wrote for one case (.mxl; .musicxml from WebAssembly): one, or one per movement. */
const all = allCases().filter(c => !filters.length || filters.some(f => c.name.includes(f)))
  .filter(c => !process.env.SKIP || !process.env.SKIP.split(',').some(f => c.name.includes(f)))
  .filter(c => !TEAVM || !/\.pdf$/i.test(c.input))
  .filter(c => process.env.HOLDOUT !== 'only' || c.name.startsWith('holdout/'))
if (process.env.LIST) {
  for (const c of all) console.log(c.answer ? 'answer ' : '       ', c.name)
  process.exit(0)
}
if (!all.length) {
  console.error('No cases.')
  process.exit(1)
}

// read: JOBS Java processes at once, each working through a batch of at most about 10 cases
// (Audiveris's memory grows from one book to the next: a batch of 37 with the hard photos ran out
// of its 3 GB). Audiveris names a read after its image, so two cases with one file name
// (multi-page/*/p01.png) go in different batches: in one they overwrote each other's read.
mkdirSync(OUT, { recursive: true })
const results = {}
// (WebAssembly: a case a process, a book each)
const batches = TEAVM ? [] : Array.from({ length: Math.max(Math.min(JOBS, all.length), Math.ceil(all.length / 10)) }, (_, index) => Object.assign([], { index }))
const file = c => basename(c.input, extname(c.input))
if (TEAVM) all.forEach((c, index) => batches.push(Object.assign([c], { index })))
else all.forEach((c, i) => {
  const free = batches.map((_, k) => batches[(i + k) % batches.length]).find(b => !b.some(o => file(o) === file(c)))
  const batch = free ?? Object.assign([], { index: batches.length })
  if (!free) batches.push(batch)
  batch.push(c)
})
const t0 = Date.now()
// which batch read each case, kept with the run: REUSE scores those reads again
const manifest = join(OUT, 'batches.json')
let runs
if (process.env.REUSE) {
  const was = JSON.parse(readFileSync(manifest, 'utf8'))
  for (const b of batches) b.length = 0
  for (const c of all) if (was[c.name] != null) (batches[was[c.name]] ??= Object.assign([], { index: was[c.name] })).push(c)
  for (let i = 0; i < batches.length; i++) batches[i] ??= Object.assign([], { index: i })
  runs = batches.map(b => ({ dir: join(OUT, `batch-${b.index}`), seconds: null }))
} else {
  writeFileSync(manifest, JSON.stringify(Object.fromEntries(batches.flatMap(b => b.map(c => [c.name, b.index]))), null, 1))
  runs = await pool(batches, JOBS, TEAVM ? readWasm : read)
}
console.error(`read ${all.length} cases in ${Math.round((Date.now() - t0) / 1000)} s`)

for (const [i, batch] of batches.entries()) {
  for (const c of batch) {
    const files = reads(runs[i].dir, c)
    const r = { read: files.length > 0, movements: files.length }
    if (files.length) {
      const xml = joined(files)
      if (c.answer) Object.assign(r, score(JSON.parse(readFileSync(c.answer, 'utf8')), xml), { lyrics: undefined }) // no OCR here
      else r.parts = parseMusicXml(xml).length
    }
    results[c.name] = r
  }
}

// report, against the baseline
const baseline = existsSync(BASELINE) ? JSON.parse(readFileSync(BASELINE, 'utf8')) : {}
const pct = x => (x == null ? '   -' : `${Math.round(100 * x)}%`.padStart(4))
const worse = []
const better = []
console.log('case'.padEnd(44), 'notes inPart  prec rhythm lyrics parts extra')
for (const [name, r] of Object.entries(results).sort()) {
  const b = baseline[name]
  let mark = ''
  if (b) {
    // worse: fewer notes found, fewer in their part, more notes that aren't there, or fewer on time
    const keys = ['notes', 'inPart', 'precision', 'rhythm']
    const both = keys.filter(k => b[k] != null) // a baseline from before a score was counted
    const drop = both.some(k => b[k] - (r[k] ?? 0) > 0.01) || (b.read && !r.read)
    const gain = !drop && (both.some(k => (r[k] ?? 0) - b[k] > 0.01) || (!b.read && r.read))
    if (drop) worse.push(name), (mark = '  WORSE')
    else if (gain) better.push(name), (mark = '  better')
  }
  const parts = r.read ? `${r.parts}${r.answerParts ? '/' + r.answerParts : ''}` : 'not read'
  console.log(name.padEnd(44), pct(r.notes), ' ', pct(r.inPart), ' ', pct(r.precision), '  ', pct(r.rhythm), ' ', pct(r.lyrics), ' ', parts.padEnd(5), String(r.extra ?? '').padStart(4), mark)
}
const scored = Object.values(results).filter(r => r.notes != null)
const mean = k => scored.reduce((s, r) => s + (r[k] ?? 0), 0) / (scored.length || 1)
const timed = scored.filter(r => r.rhythm != null)
const rhythm = timed.length ? `, rhythm ${pct(timed.reduce((s, r) => s + r.rhythm, 0) / timed.length)} (mean of ${timed.length})` : ''
console.log(`\n${Object.values(results).filter(r => r.read).length}/${all.length} read; with answers: notes ${pct(mean('notes'))}, in part ${pct(mean('inPart'))}, precision ${pct(mean('precision'))} (mean of ${scored.length})${rhythm}`)
if (Object.keys(baseline).length) console.log(`against the baseline: ${better.length} better, ${worse.length} worse${worse.length ? ': ' + worse.join(', ') : ''}`)
writeFileSync(join(OUT, 'results.json'), JSON.stringify(results, null, 1))
if (process.env.SAVE) {
  writeFileSync(BASELINE, JSON.stringify({ ...baseline, ...results }, null, 1) + '\n')
  console.log('saved as the baseline')
}
process.exit(worse.length ? 1 : 0)
