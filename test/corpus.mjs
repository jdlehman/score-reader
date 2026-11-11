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
//   PATCHED=<jar> reads with other patched classes; CONSTANTS='a=1,b=2' with other settings;
//   RUN=<name> keeps this run's reads apart (.work/corpus/<name>), to compare two builds
//
// Needs ./setup.sh and ./build.sh first (the Audiveris jars and our patched classes in .work/).
// A case is an image or a PDF. Next to it, <name>.json is its answer (every pitched note, by
// bar); without one only "was it read" and the part count are reported. In EXTRA, photos in
// photo-synthetic/ take their answer from pages/<page>.json.
import { execFile } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { basename, dirname, extname, join, relative, resolve } from 'node:path'
import { promisify } from 'node:util'
import { READING, asArgs } from '../app/settings.js'
import { musicXmlText, parseMusicXml, score } from './score.mjs'

const ROOT = resolve(import.meta.dirname, '..')
const WORK = join(ROOT, '.work')
const OUT = join(WORK, 'corpus', process.env.RUN ?? 'last')
const BASELINE = join(ROOT, 'test', 'corpus', 'baseline.json')
const JOBS = Number(process.env.JOBS ?? 2)
const filters = process.argv.slice(2)

const INPUT = /\.(png|jpe?g|tiff?|pdf)$/i

/** An answer file: <name>.gt.json, or <name>.json if it lists parts (not just an image's size). */
function answerFor(input) {
  for (const f of [input.replace(INPUT, '.gt.json'), input.replace(INPUT, '.json')]) {
    try {
      if (Array.isArray(JSON.parse(readFileSync(f, 'utf8')).parts)) return f
    } catch {}
  }
  return null
}

/** Cases in a corpus folder: { name, input, answer? }, named by their path in it. */
function cases(dir, prefix = '') {
  const out = []
  const walk = d => {
    for (const f of readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const path = join(d, f.name)
      if (f.isDirectory()) walk(path)
      else if (INPUT.test(f.name)) {
        const name = prefix + relative(dir, path).replace(INPUT, '')
        let answer = answerFor(path)
        if (!answer && basename(d) === 'photo-synthetic') answer = answerFor(join(dirname(d), 'pages', basename(f.name).replace(/-photo-\w+\.\w+$/, '.png')))
        out.push({ name, input: path, answer })
      }
    }
  }
  walk(dir)
  return out
}

const java = join(WORK, 'jdk', readdirSync(join(WORK, 'jdk')).find(d => d.startsWith('jdk')), 'Contents', 'Home', 'bin', 'java')
const classpath = [resolve(process.env.PATCHED ?? join(WORK, 'patched.jar')), ...readFileSync(join(WORK, 'classpath.txt'), 'utf8').trim().split(':').map(j => join(ROOT, j.replace(/^\/app\//, '')))].join(':')

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
    ...asArgs(process.env.CONSTANTS ? process.env.CONSTANTS.split(',') : READING), '-transcribe', '-export', '-output', dir,
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

/** The .mxl files Audiveris wrote for one case: one, or one per movement. */
function reads(dir, c) {
  const radix = basename(c.input, extname(c.input))
  const where = [join(dir, radix), dir]
  for (const d of where) {
    if (!existsSync(d)) continue
    const files = readdirSync(d).filter(f => f.endsWith('.mxl') && (f === radix + '.mxl' || f.startsWith(radix + '.mvt'))).sort()
    if (files.length) return files.map(f => join(d, f))
  }
  return []
}

/** Joins movements into one list of parts, measure lists end to end, for scoring. */
function joined(files) {
  const xmls = files.map(f => musicXmlText(readFileSync(f)))
  if (xmls.length === 1) return xmls[0]
  // score each movement's parts as continuing the first's, by position (good enough for a check)
  const parts = xmls.map(parseMusicXml)
  const widest = parts.reduce((a, b) => (b.length > a.length ? b : a))
  const out = widest.map((p, i) => ({ ...p, measures: parts.flatMap(ps => ps[i]?.measures ?? []) }))
  return toXml(out)
}

/** Minimal MusicXML from parsed parts (only what score.mjs reads back). */
function toXml(parts) {
  const steps = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
  const alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
  const note = n => `<note><pitch><step>${steps[n.midi % 12]}</step>${alters[n.midi % 12] ? '<alter>1</alter>' : ''}<octave>${Math.floor(n.midi / 12) - 1}</octave></pitch>${n.lyric ? `<lyric><text>${n.lyric}</text></lyric>` : ''}</note>`
  return `<score-partwise><part-list>${parts.map(p => `<score-part id="${p.id}"><part-name>${p.name}</part-name></score-part>`).join('')}</part-list>${parts.map(p => `<part id="${p.id}">${p.measures.map(m => `<measure>${m.notes.map(note).join('')}</measure>`).join('')}</part>`).join('')}</score-partwise>`
}

const all = [
  ...cases(join(ROOT, 'test', 'corpus')),
  // the extra folder's copies of pieces the repo has are left out
  ...(process.env.EXTRA ? cases(resolve(process.env.EXTRA.replace(/^~/, process.env.HOME)), 'extra/') : []),
].filter((c, i, list) => !c.name.startsWith('extra/') || !list.some(o => !o.name.startsWith('extra/') && basename(o.input) === basename(c.input))).filter(c => !filters.length || filters.some(f => c.name.includes(f)))
  .filter(c => !process.env.SKIP || !process.env.SKIP.split(',').some(f => c.name.includes(f)))
if (process.env.LIST) {
  for (const c of all) console.log(c.answer ? 'answer ' : '       ', c.name)
  process.exit(0)
}
if (!all.length) {
  console.error('No cases.')
  process.exit(1)
}

// read: JOBS Java processes, each working through its share of the cases
mkdirSync(OUT, { recursive: true })
const results = {}
const batches = Array.from({ length: Math.min(JOBS, all.length) }, (_, index) => Object.assign([], { index }))
all.forEach((c, i) => batches[i % batches.length].push(c))
const t0 = Date.now()
const runs = process.env.REUSE
  ? batches.map(b => ({ dir: join(OUT, `batch-${b.index}`), seconds: null }))
  : await Promise.all(batches.map(read))
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
console.log('case'.padEnd(44), 'notes inPart lyrics parts extra')
for (const [name, r] of Object.entries(results).sort()) {
  const b = baseline[name]
  let mark = ''
  if (b) {
    const drop = (b.notes ?? 0) - (r.notes ?? 0) > 0.01 || (b.inPart ?? 0) - (r.inPart ?? 0) > 0.01 || (b.read && !r.read)
    const gain = (r.notes ?? 0) - (b.notes ?? 0) > 0.01 || (r.inPart ?? 0) - (b.inPart ?? 0) > 0.01 || (!b.read && r.read)
    if (drop) worse.push(name), (mark = '  WORSE')
    else if (gain) better.push(name), (mark = '  better')
  }
  const parts = r.read ? `${r.parts}${r.answerParts ? '/' + r.answerParts : ''}` : 'not read'
  console.log(name.padEnd(44), pct(r.notes), ' ', pct(r.inPart), ' ', pct(r.lyrics), ' ', parts.padEnd(5), String(r.extra ?? '').padStart(4), mark)
}
const scored = Object.values(results).filter(r => r.notes != null)
const mean = k => scored.reduce((s, r) => s + (r[k] ?? 0), 0) / (scored.length || 1)
console.log(`\n${Object.values(results).filter(r => r.read).length}/${all.length} read; with answers: notes ${pct(mean('notes'))}, in part ${pct(mean('inPart'))} (mean of ${scored.length})`)
if (Object.keys(baseline).length) console.log(`against the baseline: ${better.length} better, ${worse.length} worse${worse.length ? ': ' + worse.join(', ') : ''}`)
writeFileSync(join(OUT, 'results.json'), JSON.stringify(results, null, 1))
if (process.env.SAVE) {
  writeFileSync(BASELINE, JSON.stringify({ ...baseline, ...results }, null, 1) + '\n')
  console.log('saved as the baseline')
}
process.exit(worse.length ? 1 : 0)
