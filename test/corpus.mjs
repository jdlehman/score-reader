// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reads the test corpus as the page does (Audiveris in WebAssembly, the page's settings in
// app/settings.js, the words read with tesseract.js), scores each read against its answer
// (test/score.mjs), and compares the scores with the last saved ones (test/corpus/baseline.json).
//
//   node test/corpus.mjs                    read and score everything, compare with the baseline
//   node test/corpus.mjs lieder chorale     only cases whose name contains one of these
//   EXTRA=~/Downloads/choral-test-set node test/corpus.mjs
//                                           also the pieces that can't be in the repo (licences)
//   SAVE=1 node test/corpus.mjs             save these scores as the new baseline
//   JOBS=n reads at once (default 4; desktop 2); REUSE=1 scores the reads of the last run again
//   LIST=1 only lists the cases; SKIP=a,b leaves out cases whose name contains one of these (and
//     EXTRA/skip.txt lists the local test set's own); CASES=<file> reads only the cases it names,
//     one name a line, exactly
//   HOLDOUT=1 also reads the held-out pages (test/holdout, and EXTRA's holdout/), HOLDOUT=only reads only them: to confirm
//     a fix made without looking at them, never to make one
//   RUN=<name> keeps this run's reads apart (.work/corpus/<name>), to compare two builds; a run
//     reads into the same folder again keeps the reads of cases it doesn't read this time
//   WASM=<dir> reads with another WebAssembly build than .work/teavm/out (teavm/build.sh with
//     TEAVM_WORK), to compare it with this one
//   CONSTANTS='a=1,b=2' reads with more Audiveris settings, after the page's (app/settings.js), so
//     one of the same name replaces it
//   PRE=<module>, POST=<module>: a step before the read (on the grey pages) or after it (on the
//     MusicXML), to measure one that isn't in the page yet (teavm/node/read.mjs)
//   OCR=0 leaves the words out (faster; lyrics aren't scored); OCR=deu reads every case's words as
//     German; by default each case's are read in its language (cases.mjs, languageOf), as a reader
//     would pick it on the page
//   ENGINE=desktop reads with desktop Audiveris instead (Java, a few times faster, with Audiveris's
//     logs and .omr files; words left out), against its own baseline (baseline-desktop.json):
//     PATCHED=<jar> reads with other patched classes
//
// test/prove.mjs uses this to read a change and main, and says whether the change is better.
//
// How the page reads, here: an image is made grey as the page makes it (test/grey.py), a PDF is
// drawn by the page's own code in Chrome (test/pdf-grey.mjs), and teavm/node/read.mjs reads them
// with the build the page serves (byte for byte the same output as in Chrome).
// Needs ./setup.sh and ./build.sh first (the Audiveris jars, our patched classes and the
// WebAssembly build in .work/, PDF.js in dist/).
// A case is an image or a PDF. Next to it, <name>.json is its answer (every pitched note, by
// bar); without one only "was it read" and the part count are reported. In EXTRA, photos in
// photo-synthetic/ take their answer from pages/<page>.json.
import { execFile } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { basename, extname, join, resolve } from 'node:path'
import { promisify } from 'node:util'
import { READING, asArgs } from '../app/settings.js'
import { EXTRA, ROOT, allCases, caseKey, isHeldOut, joined, languageOf, reads } from './cases.mjs'
import { parseMusicXml, score } from './score.mjs'

const WORK = join(ROOT, '.work')
const OUT = join(WORK, 'corpus', process.env.RUN ?? 'last')
const ENGINE = process.env.ENGINE ?? 'teavm'
if (!['teavm', 'desktop'].includes(ENGINE)) {
  console.error(`ENGINE is teavm (the default) or desktop, not ${ENGINE}`)
  process.exit(2)
}
const TEAVM = ENGINE === 'teavm'
// each engine against its own: they read a few notes differently (HANDOFF/NOTES: within a point).
// The repository's pages' scores are kept here, the local test set's in its own folder (EXTRA), so
// that the repository names none of its pages.
const BASENAME = TEAVM ? 'baseline.json' : 'baseline-desktop.json'
const BASELINE = join(ROOT, 'test', 'corpus', BASENAME)
const EXTRA_BASELINE = EXTRA && join(EXTRA, BASENAME)
const isExtra = name => name.startsWith('extra/')
const JOBS = Number(process.env.JOBS ?? (TEAVM ? 4 : 2))
/** The words' language for a case, or '' to leave them out. */
const wordsOf = c => (!TEAVM || process.env.OCR === '0' ? '' : process.env.OCR || languageOf(c))
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
 * Reads one case with Audiveris in WebAssembly, as the page would, into OUT/batch-<key>/: its image
 * made grey as the page makes it (test/grey.py), or a PDF's pages drawn by the page's own code
 * (test/pdf-grey.mjs), then teavm/node/read.mjs, with the words read in the case's language.
 */
async function readWasm(batch) {
  const [c] = batch
  const dir = join(OUT, `batch-${batch.index}`)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const radix = join(dir, basename(c.input, extname(c.input)))
  const started = Date.now()
  let log = ''
  let pages = [radix]
  try {
    if (/\.pdf$/i.test(c.input)) {
      const r = await promisify(execFile)(process.execPath, [join(ROOT, 'test', 'pdf-grey.mjs'), c.input, radix], { maxBuffer: 1 << 20 })
      pages = Array.from({ length: Number(r.stdout.trim()) }, (_, i) => `${radix}-p${i + 1}`)
    } else await promisify(execFile)('python3', ['-I', join(ROOT, 'test', 'grey.py'), c.input, radix])
    const r = await promisify(execFile)(process.execPath, ['--experimental-wasm-exnref', join(ROOT, 'teavm', 'node', 'read.mjs'), radix + '.musicxml', ...pages.flatMap(p => [p + '.grey', p + '.json'])],
      { maxBuffer: 1 << 28, timeout: (20 + 10 * pages.length) * 60_000, env: { ...process.env, OCR: wordsOf(c) } }) // minutes: a dense orchestral page can take 25
    log = `words: ${wordsOf(c) || 'left out'}\n` + r.stdout + r.stderr
  } catch (e) {
    log = `words: ${wordsOf(c) || 'left out'}\n` + (e.stdout ?? '') + (e.stderr ?? '') + '\n' + e.message
  }
  for (const p of pages) rmSync(p + '.grey', { force: true })
  writeFileSync(join(dir, 'log.txt'), log)
  return { dir, seconds: Math.round((Date.now() - started) / 1000) }
}

/** The MusicXML files Audiveris wrote for one case (.mxl; .musicxml from WebAssembly): one, or one per movement. */
const named = process.env.CASES && new Set(readFileSync(process.env.CASES, 'utf8').split('\n').filter(Boolean))
const all = allCases(!!process.env.HOLDOUT || !!named).filter(c => !filters.length || filters.some(f => c.name.includes(f)))
  .filter(c => !named || named.has(c.name))
  .filter(c => process.env.HOLDOUT !== 'only' || isHeldOut(c.name))
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
// (WebAssembly: a case a process, a book each, in a folder named after the case)
let batches = TEAVM ? [] : Array.from({ length: Math.max(Math.min(JOBS, all.length), Math.ceil(all.length / 10)) }, (_, index) => Object.assign([], { index }))
const file = c => basename(c.input, extname(c.input))
if (TEAVM) all.forEach(c => batches.push(Object.assign([c], { index: caseKey(c.name) })))
else all.forEach((c, i) => {
  const free = batches.map((_, k) => batches[(i + k) % batches.length]).find(b => !b.some(o => file(o) === file(c)))
  const batch = free ?? Object.assign([], { index: batches.length })
  if (!free) batches.push(batch)
  batch.push(c)
})
const t0 = Date.now()
// which batch read each case, kept with the run: REUSE scores those reads again. A WebAssembly
// run adds to the run's earlier reads (a folder a case); a desktop run's batches replace them.
const manifest = join(OUT, 'batches.json')
const was = existsSync(manifest) ? JSON.parse(readFileSync(manifest, 'utf8')) : {}
let runs
if (process.env.REUSE) {
  // a batch a case, in the folder its read is in (a desktop batch's folder holds several)
  batches = all.filter(c => was[c.name] != null).map(c => Object.assign([c], { index: was[c.name] }))
  runs = batches.map(b => ({ dir: join(OUT, `batch-${b.index}`), seconds: null }))
} else {
  const now = Object.fromEntries(batches.flatMap(b => b.map(c => [c.name, b.index])))
  writeFileSync(manifest, JSON.stringify(TEAVM ? { ...was, ...now } : now, null, 1))
  runs = await pool(batches, JOBS, TEAVM ? readWasm : read)
}
console.error(`read ${all.length} cases in ${Math.round((Date.now() - t0) / 1000)} s`)

for (const [i, batch] of batches.entries()) {
  for (const c of batch) {
    const files = reads(runs[i].dir, c)
    const r = { read: files.length > 0, movements: files.length }
    if (files.length) {
      const xml = joined(files)
      if (c.answer) {
        Object.assign(r, score(JSON.parse(readFileSync(c.answer, 'utf8')), xml))
        if (!wordsOf(c)) r.lyrics = undefined // words left out
      }
      else r.parts = parseMusicXml(xml).length
    }
    results[c.name] = r
  }
}

// report, against the baseline
const load = f => (f && existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : {})
const baseline = { ...load(BASELINE), ...load(EXTRA_BASELINE) }
const pct = x => (x == null ? '   -' : `${Math.round(100 * x)}%`.padStart(4))
const worse = []
const better = []
console.log('case'.padEnd(44), 'notes inPart  prec rhythm lyrics parts extra')
for (const [name, r] of Object.entries(results).sort()) {
  const b = baseline[name]
  let mark = ''
  if (b) {
    // worse: fewer notes found, fewer in their part, more notes that aren't there, fewer on time,
    // or fewer syllables
    const keys = ['notes', 'inPart', 'precision', 'rhythm', 'lyrics']
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
  const merged = { ...baseline, ...results }
  const pick = extra => JSON.stringify(Object.fromEntries(Object.entries(merged).filter(([name]) => isExtra(name) === extra)), null, 1) + '\n'
  writeFileSync(BASELINE, pick(false))
  if (EXTRA_BASELINE) writeFileSync(EXTRA_BASELINE, pick(true))
  console.log('saved as the baseline')
}
process.exit(worse.length ? 1 : 0)
