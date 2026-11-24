// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Says whether a change to the reader is better, by a fixed rule: reads the corpus with the change
// and with main, as the site reads (test/corpus.mjs), compares the two bar by bar against the
// answers (test/runs.mjs), and gives a verdict: PROVED, TRADE-OFF or NOT PROVED
// (test/corpus/README.md, "Proving a change", has the rule).
//
//   EXTRA=~/Downloads/choral-test-set node test/prove.mjs <name> [options] [filter...]
//
//   --wasm <dir>         the change's WebAssembly build (PATCHED=<jar> TEAVM_WORK=<dir> teavm/build.sh)
//   --constants a=1,b=2  Audiveris settings the change adds, after the page's (app/settings.js)
//   --pre <module>       a step the change adds before the read, on the grey pages (teavm/node/read.mjs)
//   --post <module>      a step it adds after the read, on the MusicXML
//   --main <dir>         main's WebAssembly build (default .work/teavm/out: ./build.sh on main)
//   --base <run,...>     compare with these runs' reads instead of reading main (.work/corpus/<run>)
//   --after <run,...>    take the change's reads from these runs: with a build named, reading only
//                        the cases they lack; without, reading nothing and comparing only those cases
//   --holdout            also the held-out pages, totals only: once per change, to confirm it
//   filter...            only cases whose name contains one of these: a quick look, not a verdict
//   JOBS=n               reads at once (default 4); OCR as in test/corpus.mjs
//
// Reading time only counts against a change (past +20%): main's kept reads are from another day,
// so a faster change is timed on its own, both builds back to back.
//
// With no change named (no --wasm, --constants, --pre, --post, --after), it reads main a second
// time: the noise check. Two reads of one build that differ on a page give that page an allowance
// (.work/corpus/noise.json), which later verdicts use; until it has run, every difference counts.
//
// Main's reads are kept (.work/corpus/main-<build>) and read again only for a case they lack, or
// when main's build or the reading code changes (the build's files, app/ and the reading scripts
// are hashed). The change's reads go to .work/corpus/<name>; a run cut short (the laptop slept)
// picks up where it stopped when run again with the same build. A case read by one side only is
// read again once, alone, before it counts.
//
// Held-out pages (test/holdout/README.md): only their totals are shown, and which pages moved;
// each use is logged (.work/corpus/holdout-log.txt) and a second look at one change is warned of.
import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import { appendFileSync, existsSync, mkdirSync, openSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { EXTRA, ROOT, allCases, isHeldOut, languageOf } from './cases.mjs'
import { GROUPS, compareReads, locate, readOf, runDir } from './runs.mjs'
import { score, syllable } from './score.mjs'

// ---- arguments

const args = process.argv.slice(2)
const options = {}
const filters = []
let name
for (let i = 0; i < args.length; i++) {
  const a = args[i]
  if (a === '--holdout') options.holdout = true
  else if (a.startsWith('--')) {
    if (!['--wasm', '--constants', '--pre', '--post', '--main', '--base', '--after'].includes(a) || args[i + 1] == null) usage(`unknown option or no value: ${a}`)
    options[a.slice(2)] = args[++i]
  } else if (!name) name = a
  else filters.push(a)
}
if (!name || !/^[\w.-]+$/.test(name)) usage('name the change (letters, digits, . - _): its reads go to .work/corpus/<name>')
if (name.startsWith('main-')) usage('main-... is the name of main\'s kept reads')
function usage(why) {
  console.error(`${why}\nusage: node test/prove.mjs <name> [--wasm dir] [--constants a=1,b=2] [--pre module] [--post module] [--main dir] [--base runs] [--after runs] [--holdout] [filter...]`)
  process.exit(2)
}
const JOBS = Number(process.env.JOBS ?? 4)
const abs = p => p && resolve(p)
const MAIN = { wasm: abs(options.main ?? join(ROOT, '.work', 'teavm', 'out')) }
const CHANGE = { wasm: abs(options.wasm) ?? MAIN.wasm, constants: options.constants, pre: abs(options.pre), post: abs(options.post) }
for (const v of [MAIN, CHANGE]) if (!existsSync(join(v.wasm, 'classes.wasm'))) usage(`no WebAssembly build in ${v.wasm}`)
for (const f of [CHANGE.pre, CHANGE.post]) if (f && !existsSync(f)) usage(`no file ${f}`)

// ---- builds

/** The files a read depends on besides the build: the page's code and the reading scripts. */
const READER = ['app/pdf.js', 'app/preflight.js', 'app/teavm.js', 'app/columns.js', 'app/settings.js', 'teavm/node/read.mjs', 'teavm/node/ocr-run.mjs', 'test/pdf-grey.mjs', 'test/grey.py', 'package-lock.json']

/** A variant's fingerprint: its build, steps and settings, the reading code, and OCR. */
function fingerprint(v) {
  const h = createHash('sha256')
  for (const f of ['classes.wasm', 'runtime.mjs']) h.update(readFileSync(join(v.wasm, f)))
  const templates = join(v.wasm, 'templates')
  if (existsSync(templates)) h.update(readdirSync(templates).sort().map(f => `${f}:${statSync(join(templates, f)).size}`).join())
  for (const f of READER) h.update(readFileSync(join(ROOT, f)))
  for (const f of [v.pre, v.post]) h.update(f ? readFileSync(f) : '-')
  h.update(`${v.constants ?? ''}|${process.env.OCR ?? ''}`)
  return h.digest('hex').slice(0, 12)
}
const mainPrint = fingerprint(MAIN)
const changePrint = fingerprint(CHANGE)
const built = !!(options.wasm || options.constants || options.pre || options.post) // a change to read
const repeat = !built && !options.after // main read again: the noise check
// the change's reads: its own run, and with --after those runs' first; reading only what they lack,
// unless --after comes without a build to read the rest with
const readsChange = built || !options.after
const afterSpec = [readsChange && name, options.after].filter(Boolean).join(',')

// ---- cases

const holdoutUse = !!options.holdout
const want = c => !filters.length || filters.some(f => c.name.includes(f))
let cases = allCases(holdoutUse).filter(want)
const baseRuns = options.base && locate(options.base)
const afterRuns = options.after && locate(options.after)
if (baseRuns) cases = cases.filter(c => baseRuns.has(c.name))
if (afterRuns && !readsChange) cases = cases.filter(c => afterRuns.has(c.name))
if (!cases.length) usage('no cases')

// ---- reading

const wordsOf = c => (process.env.OCR === '0' ? '' : process.env.OCR || languageOf(c))
const logOf = (where, c) => {
  const dir = where.get(c.name)
  const f = dir && join(dir, 'log.txt')
  return f && existsSync(f) ? readFileSync(f, 'utf8') : ''
}
/** A case's read in a run is complete: the reader finished it, with the words in its language. */
const done = (where, c) => {
  const log = logOf(where, c)
  return log.startsWith(`words: ${wordsOf(c) || 'left out'}\n`) && /(^|\n)read in [\d.]+ s/.test(log)
}
/** Reading seconds for a case in a run (teavm/node/read.mjs's), or null. */
const secondsOf = (where, c) => {
  const m = logOf(where, c).match(/(?:^|\n)read in ([\d.]+) s/)
  return m ? Number(m[1]) : null
}

/** locate(), leaving out runs not started yet. */
const where = spec => locate(spec.split(',').filter(run => existsSync(join(runDir(run), 'batches.json'))).join(',') || '-')

/** Reads the cases with a variant into .work/corpus/<run>, by test/corpus.mjs. */
async function read(run, v, list, jobs = JOBS) {
  if (!list.length) return
  mkdirSync(runDir(run), { recursive: true })
  const names = join(runDir(run), 'cases.txt')
  writeFileSync(names, list.map(c => c.name).join('\n') + '\n')
  const env = { ...process.env, RUN: run, CASES: names, WASM: v.wasm, JOBS: String(jobs) }
  for (const k of ['CONSTANTS', 'PRE', 'POST', 'HOLDOUT', 'ENGINE', 'SAVE', 'REUSE', 'LIST', 'PATCHED']) delete env[k]
  if (v.constants) env.CONSTANTS = v.constants
  if (v.pre) env.PRE = v.pre
  if (v.post) env.POST = v.post
  console.error(`reading ${list.length} case${list.length === 1 ? '' : 's'} into .work/corpus/${run} (log: .work/corpus/${run}/prove.log)`)
  const log = openSync(join(runDir(run), 'prove.log'), 'a')
  await new Promise(done => spawn(process.execPath, [join(ROOT, 'test', 'corpus.mjs')], { env, stdio: ['ignore', log, log] }).on('close', done))
}

const mainRun = `main-${mainPrint}`
let base = baseRuns
if (!base) {
  const kept = where(mainRun)
  await read(mainRun, MAIN, cases.filter(c => !done(kept, c)))
  base = where(mainRun)
}
let after = afterRuns
if (readsChange) {
  const dir = runDir(name)
  const variantFile = join(dir, 'variant.json')
  if (existsSync(dir) && !existsSync(variantFile)) usage(`.work/corpus/${name} is a run prove didn't make: name the change otherwise, or pass it as --after ${name}`)
  if (existsSync(variantFile) && JSON.parse(readFileSync(variantFile, 'utf8')).fingerprint !== changePrint) {
    console.error(`the change's build or steps differ from its last reads: reading it again`)
    rmSync(dir, { recursive: true, force: true })
  }
  mkdirSync(dir, { recursive: true })
  writeFileSync(variantFile, JSON.stringify({ fingerprint: changePrint, main: mainPrint, ...CHANGE, date: new Date().toISOString() }, null, 1) + '\n')
  const kept = where(afterSpec)
  await read(name, CHANGE, cases.filter(c => !done(kept, c)))
  after = where(afterSpec)
}

// a case one side read and the other didn't: read again, alone, the side that didn't (a read can
// die of a timeout when the machine is busy)
const readBy = (where, c) => readOf(where, c) != null
const once = cases.filter(c => readBy(base, c) !== readBy(after, c))
if (once.length) {
  if (!baseRuns) await read(mainRun, MAIN, once.filter(c => !readBy(base, c)), 1)
  if (readsChange) await read(name, CHANGE, once.filter(c => !readBy(after, c)), 1)
  if (!baseRuns) base = where(mainRun)
  if (readsChange) after = where(afterSpec)
}

// ---- comparing

/** One case's differences, after minus before. */
function compareCase(c) {
  const xml = [readOf(base, c), readOf(after, c)]
  const out = { name: c.name, held: isHeldOut(c.name), read: xml.map(x => x != null), seconds: [secondsOf(base, c), secondsOf(after, c)] }
  if (!c.answer || !xml[0] || !xml[1]) return out
  const answer = JSON.parse(readFileSync(c.answer, 'utf8'))
  const { groups, changed } = compareReads(answer, xml[0], xml[1])
  const syllables = answer.parts.flatMap(p => p.notes.filter(n => Number.isFinite(n.midi) && syllable(n.lyric))).length
  const found = x => Math.round((score(answer, x).lyrics ?? 0) * syllables)
  return { ...out, groups, changedBars: changed.length, syllables: found(xml[1]) - found(xml[0]) }
}
const rows = cases.map(compareCase)

/**
 * The measures, after minus before, over some rows; for each, whether more is better. A note is
 * right when it is there and starts on time. Notes missing and at the wrong time are shown, not
 * judged: a note can only be at the wrong time once it is found, so a change that finds notes
 * puts some there, and a note found at the wrong time is no worse than one missed.
 */
const MEASURES = [
  ['sungBars', 'sung bars right', +1],
  ['accBars', 'accompaniment bars right', +1],
  ['right', 'notes right', +1],
  ['extra', 'extra notes', -1],
  ['syllables', 'syllables found', +1],
  ['read', 'pages read', +1],
]
function measure(r) {
  const g = r.groups
  return {
    sungBars: g ? g.sung.fixed - g.sung.broken : 0,
    accBars: g ? g.accompaniment.fixed - g.accompaniment.broken : 0,
    right: g ? -GROUPS.reduce((s, k) => s + g[k].missing + g[k].time, 0) : 0,
    missing: g ? GROUPS.reduce((s, k) => s + g[k].missing, 0) : 0,
    time: g ? GROUPS.reduce((s, k) => s + g[k].time, 0) : 0,
    extra: g ? GROUPS.reduce((s, k) => s + g[k].extra, 0) : 0,
    syllables: r.syllables ?? 0,
    read: r.read[1] - r.read[0],
  }
}
const sum = list => {
  const t = Object.fromEntries(MEASURES.map(([k]) => [k, 0]))
  for (const r of list) for (const [k, v] of Object.entries(measure(r))) t[k] = (t[k] ?? 0) + v
  return t
}
const timeOf = list => {
  const both = list.filter(r => r.seconds[0] != null && r.seconds[1] != null)
  return [0, 1].map(i => both.reduce((s, r) => s + r.seconds[i], 0))
}

// ---- noise: two reads of main

const NOISE = join(ROOT, '.work', 'corpus', 'noise.json')
const report = []
const say = (s = '') => report.push(s)
const signed = x => `${x > 0 ? '+' : ''}${x}`

if (repeat) {
  const cases = {}
  for (const r of rows) {
    const m = measure(r)
    const moved = Object.fromEntries(Object.entries(m).map(([k, v]) => [k, Math.abs(v)]))
    if (r.groups) {
      moved.sungBars = r.groups.sung.fixed + r.groups.sung.broken
      moved.accBars = r.groups.accompaniment.fixed + r.groups.accompaniment.broken
    }
    moved.notes = moved.missing + moved.time + moved.extra
    if (Object.values(moved).some(v => v) || r.changedBars) cases[r.name] = moved
  }
  const totals = Object.fromEntries(MEASURES.map(([k]) => [k, Object.values(cases).reduce((s, m) => s + m[k], 0)]))
  const [t0, t1] = timeOf(rows)
  const noise = { main: mainPrint, date: new Date().toISOString(), pages: rows.length, cases, totals, seconds: t0 ? Math.abs(t1 / t0 - 1) : 0 }
  if (filters.length) say('(a quick look: filters given, so noise.json is left as it was)')
  else if (baseRuns) say(`(main against ${options.base}, not against itself: noise.json is left as it was)`)
  else writeFileSync(NOISE, JSON.stringify(noise, null, 1) + '\n')
  say(`Noise check: main (build ${mainPrint}) read ${baseRuns ? `and compared with ${options.base}` : 'twice'}, ${rows.length} pages`)
  const moved = Object.keys(cases)
  say(moved.length ? `${moved.length} page(s) read differently the second time:` : 'every page read the same both times: any difference a change makes is the change\'s')
  for (const n of moved) say(`  ${n}: ${MEASURES.filter(([k]) => cases[n][k]).map(([k, label]) => `${label} ${cases[n][k]}`).join(', ') || 'bars moved'}`)
  say(`reading time ${Math.round(t0)} s -> ${Math.round(t1)} s (${t0 ? signed(Math.round(100 * (t1 / t0 - 1))) : 0}%)`)
  finish('NOISE', 0)
}

const noise = existsSync(NOISE) ? JSON.parse(readFileSync(NOISE, 'utf8')) : null
const allow = (caseName, k) => noise?.cases[caseName]?.[k] ?? 0
const allowTotal = k => noise?.totals[k] ?? 0
// Reading time counts against a change when it grows past this. It never counts for one: main's
// reads are kept from another day, when the machine may have been busier or cooler, so a faster
// change has to be timed on its own, both builds back to back.
const TIME = Math.max(0.2, 2 * (noise?.seconds ?? 0))

// ---- the verdict on the tuning pages

const tuning = rows.filter(r => !r.held)
const held = rows.filter(r => r.held)
say(`Proving ${name} against main (build ${mainPrint}${baseRuns ? `, reads from ${options.base}` : `, reads in .work/corpus/${mainRun}`})`)
say(`the change: ${[options.wasm && `build ${options.wasm} (${changePrint})`, options.constants && `settings ${options.constants}`, options.pre && `before the read ${options.pre}`, options.post && `after the read ${options.post}`, options.after && `reads from ${options.after}`].filter(Boolean).join('; ')}`)
const local = tuning.filter(r => r.name.startsWith('extra/')).length
say(`${tuning.length} pages (${tuning.length - local} in the repository, ${local} in the local test set${EXTRA ? '' : ': EXTRA unset, so none'})${filters.length ? `, only those matching ${filters.join(' ')}: a quick look, not a verdict` : ''}`)
say(noise ? `noise: two reads of main (build ${noise.main}, ${noise.date.slice(0, 10)}) differed on ${Object.keys(noise.cases).length} of ${noise.pages} pages; a page's own difference then is allowed it` : 'noise: not measured yet (node test/prove.mjs repeat, once per main build): every difference counts')
say()

const pageLosses = []
const lines = []
for (const r of tuning) {
  const m = measure(r)
  if (r.read[0] && !r.read[1]) pageLosses.push(`${r.name}: not read any more`)
  if (!r.groups) continue
  const losses = []
  if (-m.sungBars > allow(r.name, 'sungBars')) losses.push(`${-m.sungBars} sung bar(s) worse`)
  if (-m.accBars > allow(r.name, 'accBars')) losses.push(`${-m.accBars} accompaniment bar(s) worse`)
  if (-m.syllables > allow(r.name, 'syllables')) losses.push(`${-m.syllables} syllable(s) fewer`)
  const notes = m.missing + m.time + m.extra
  if (notes > allow(r.name, 'notes')) losses.push(`${notes} more note error(s) (missing, at the wrong time or extra)`)
  if (losses.length) pageLosses.push(`${r.name}: ${losses.join(', ')}`)
  if (r.changedBars || m.syllables || notes) {
    const g = r.groups
    lines.push(`  ${r.name.slice(0, 46).padEnd(46)} ${`+${g.sung.fixed}/-${g.sung.broken}`.padStart(8)} ${`+${g.accompaniment.fixed}/-${g.accompaniment.broken}`.padStart(8)} ${[m.missing, m.time, m.extra, m.syllables].map(x => signed(x).padStart(5)).join('')}`)
  }
}
for (const r of tuning) if (!r.read[0] && r.read[1]) lines.push(`  ${r.name}: read now, not before`)
say(lines.length ? 'pages that changed' : 'no page changed')
if (lines.length) {
  say(`  ${'page'.padEnd(46)} ${'sung'.padStart(8)} ${'acc.'.padStart(8)}  miss time xtra  syl`)
  for (const l of lines) say(l)
}
say()

const t = sum(tuning)
const gains = []
const losses = []
const bars = ['sung', 'accompaniment'].map(g => tuning.reduce((s, r) => s + (r.groups?.[g].bars ?? 0), 0))
say(`measures, after minus before (${bars[0]} sung bars, ${bars[1]} accompaniment bars)`)
for (const [k, label, better] of MEASURES) {
  const v = t[k]
  const beyond = Math.abs(v) > allowTotal(k)
  const mark = !v ? '' : !beyond ? 'within noise' : v * better > 0 ? 'better' : 'WORSE'
  if (mark === 'better') gains.push(label)
  if (mark === 'WORSE') losses.push(label)
  const detail = k === 'sungBars' || k === 'accBars'
    ? ` (fixed ${tuning.reduce((s, r) => s + (r.groups?.[k === 'sungBars' ? 'sung' : 'accompaniment'].fixed ?? 0), 0)}, broken ${tuning.reduce((s, r) => s + (r.groups?.[k === 'sungBars' ? 'sung' : 'accompaniment'].broken ?? 0), 0)})`
    : k === 'right' ? ` (missing ${signed(t.missing)}, wrong time ${signed(t.time)})`
    : k === 'read' ? ` (${tuning.filter(r => r.read[0]).length} -> ${tuning.filter(r => r.read[1]).length} of ${tuning.length})` : ''
  say(`  ${label.padEnd(26)} ${signed(v).padStart(6)}${detail.padEnd(34)} ${mark}`)
}
const [s0, s1] = timeOf(tuning)
const ratio = s0 ? s1 / s0 - 1 : 0
const timeMark = ratio > TIME ? 'WORSE' : ''
say(`  ${'reading time'.padEnd(26)} ${s0 && s1 ? `${Math.round(s0)} s -> ${Math.round(s1)} s (${signed(Math.round(100 * ratio))}%; counts only against, past +${Math.round(100 * TIME)}%) ${timeMark}` : 'not timed (a run from before reads were timed)'}`)
if (timeMark === 'WORSE') losses.push('reading time')
say()
say(pageLosses.length ? `pages worse (${pageLosses.length}):` : 'pages worse: none')
for (const l of pageLosses) say(`  ${l}`)
say()

// ---- held-out pages: totals, and which pages moved

let confirmed = null
if (holdoutUse) {
  const logFile = join(ROOT, '.work', 'corpus', 'holdout-log.txt')
  const earlier = existsSync(logFile) ? readFileSync(logFile, 'utf8').split('\n').filter(l => l.split('\t')[1] === changePrint) : []
  if (earlier.length) say(`held-out pages were read for this same change before (${earlier.map(l => l.split('\t')[0]).join(', ')}): a second look tunes against them`)
  if (!filters.length) appendFileSync(logFile, `${new Date().toISOString()}\t${changePrint}\t${name}\n`)
  const h = sum(held)
  const worse = MEASURES.filter(([k, , better]) => h[k] * better < 0 && Math.abs(h[k]) > allowTotal(k)).map(([, label]) => label)
  const movedPages = held.filter(r => r.changedBars || r.syllables || r.read[0] !== r.read[1])
  say(`held-out pages (${held.length}, totals only): ${MEASURES.map(([k, label]) => `${label} ${signed(h[k])}`).join(', ')}`)
  say(`  pages that moved: ${movedPages.length ? movedPages.map(r => r.name).join(', ') : 'none'}`)
  confirmed = !worse.length
  say(confirmed ? '  nothing worse on the held-out pages' : `  WORSE on the held-out pages: ${worse.join(', ')}`)
  say()
}

// ---- verdict

const lost = tuning.some(r => r.read[0] && !r.read[1])
let verdict, why
if (!gains.length) [verdict, why] = ['NOT PROVED', 'nothing measured is better']
else if (t.sungBars < 0 && Math.abs(t.sungBars) > allowTotal('sungBars')) [verdict, why] = ['NOT PROVED', 'fewer sung bars right']
else if (lost) [verdict, why] = ['NOT PROVED', 'a page that was read is not read any more']
else if (losses.length || pageLosses.length) [verdict, why] = ['TRADE-OFF', `better (${gains.join(', ')}) but worse ${[...losses, ...(pageLosses.length ? [`on ${pageLosses.length} page(s)`] : [])].join(', ')}: a person decides, after looking at those bars (node test/compare.mjs, VERBOSE=1)`]
else [verdict, why] = ['PROVED', `better (${gains.join(', ')}), nothing worse`]
if (verdict !== 'NOT PROVED') {
  if (confirmed === false) [verdict, why] = ['NOT PROVED', `${why}; but worse on the held-out pages`]
  else if (confirmed) why += '; confirmed on the held-out pages'
  else why += '; held-out pages not read yet: confirm once with --holdout'
}
if (filters.length) why += ' (a quick look on some pages only)'
say(`VERDICT: ${verdict}: ${why}`)
say(`bar by bar: node test/compare.mjs ${baseRuns ? options.base : mainRun} ${afterSpec}  (VERBOSE=1 lists each bar)`)
finish(verdict, { PROVED: 0, 'TRADE-OFF': 3, 'NOT PROVED': 1 }[verdict])

/** Prints the report and keeps it, with the rows, in .work/corpus/verdicts/<name>.txt and .json. */
function finish(verdict, code) {
  const text = report.join('\n') + '\n'
  process.stdout.write(text)
  const dir = join(ROOT, '.work', 'corpus', 'verdicts')
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, `${name}.txt`), text)
  writeFileSync(join(dir, `${name}.json`), JSON.stringify({ verdict, main: mainPrint, change: changePrint, options, filters, rows }, null, 1) + '\n')
  process.exit(code)
}
