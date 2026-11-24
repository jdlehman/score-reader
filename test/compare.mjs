// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Compares two runs of test/corpus.mjs bar by bar against the answers: which bars one run got
// right and the other wrong, in sung parts and in accompaniment, and how many more or fewer notes
// each missed, put at the wrong time, or added. A page's percentages can hide what moved (a bar
// fixed and a bar broken cancel out), and "1 better, 1 worse" says nothing of how much.
// test/prove.mjs does this too, and gives a verdict; this shows the bars.
//
//   EXTRA=~/Downloads/choral-test-set node test/compare.mjs perc-all tup2-all
//                                    two runs in .work/corpus/ (RUN=<name>); the second against the first
//   ... a,b,c d,e                    several runs on a side: a case's read from the first that has it
//   ... lieder chorale               only cases whose name contains one of these
//   VERBOSE=1 ...                    also each bar that changed (never a held-out page's: its
//                                    README allows totals and which pages moved, not a close look)
//
// A bar here is one answer part's bar, as its singer or player reads it, in the read part paired
// with it (test/score.mjs, bars()). It is right when every note is there, starting on time, with
// nothing extra. "Sung" is a part with lyrics or a voice's name, unless it is named for an
// instrument. Only cases both runs read are compared; the others are listed.
import { readFileSync } from 'node:fs'
import { allCases, isHeldOut } from './cases.mjs'
import { GROUPS, KINDS, compareReads, emptyGroup, locate, readOf } from './runs.mjs'

const [before, after, ...filters] = process.argv.slice(2)
if (!before || !after) {
  console.error('usage: node test/compare.mjs <run[,run...]> <run[,run...]> [filter...]  (runs in .work/corpus/)')
  process.exit(2)
}
const where = [before, after].map(locate)

const known = allCases(true)
const named = new Set([...where[0].keys()].filter(name => where[1].has(name)))
const cases = known.filter(c => named.has(c.name) && c.answer && (!filters.length || filters.some(f => c.name.includes(f))))
const unknown = [...named].filter(name => !known.some(c => c.name === name))

const totals = Object.fromEntries(GROUPS.map(g => [g, emptyGroup()]))
const pages = { better: 0, worse: 0, even: 0, same: 0 }
const readInOne = []
const readInNone = []
const lines = []
const signed = x => `${x > 0 ? '+' : ''}${x}`

for (const c of cases) {
  const answer = JSON.parse(readFileSync(c.answer, 'utf8'))
  const xml = where.map(w => readOf(w, c))
  if (!xml[0] || !xml[1]) {
    if (xml[0] || xml[1]) readInOne.push(`${c.name} (read only in ${xml[0] ? before : after})`)
    else readInNone.push(c.name)
    continue
  }
  const { groups: page, changed } = compareReads(answer, xml[0], xml[1])
  for (const g of GROUPS) for (const k of Object.keys(totals[g])) totals[g][k] += page[g][k]
  const net = Object.values(page).reduce((s, t) => s + t.missing + t.time + t.extra, 0)
  if (!changed.length) {
    pages.same++
    continue
  }
  pages[net < 0 ? 'better' : net > 0 ? 'worse' : 'even']++
  const show = g => `${String(page[g].fixed).padStart(3)} ${String(page[g].broken).padStart(3)}  ${KINDS.map(e => page[g][e]).map(x => signed(x).padStart(4)).join(' ')}`
  lines.push(`${c.name.slice(0, 44).padEnd(44)} ${show('sung')}   ${show('accompaniment')}  ${signed(page.unpaired.extra).padStart(4)}`)
  if (process.env.VERBOSE && !isHeldOut(c.name)) {
    for (const { r, group, ea, eb } of changed.sort((x, y) => x.r.bar - y.r.bar || x.r.part - y.r.part)) {
      const part = r.part < 0 ? 'unpaired parts' : `${r.name.replace(/\s+/g, ' ')}${group === 'sung' ? '' : ' (acc.)'}`
      const diff = KINDS.filter(e => ea[e] !== eb[e]).map(e => `${e === 'time' ? 'at the wrong time' : e} ${ea[e]}->${eb[e]}`).join(', ')
      lines.push(`    bar ${String(r.bar).padStart(3)} ${part}: ${diff}`)
    }
  }
}

console.log(`${after} against ${before}, ${cases.length} pages with answers in both runs`)
console.log(`${''.padEnd(44)} ${'sung parts: bars, notes'.padEnd(23)}   ${'accompaniment'.padEnd(23)}  unpaired`)
console.log(`${'page'.padEnd(44)} ${'fix brk  miss time xtra'}   ${'fix brk  miss time xtra'}  xtra`)
for (const l of lines) console.log(l)
if (!lines.length) console.log('(no bar changed)')
console.log()
for (const g of ['sung', 'accompaniment']) {
  const t = totals[g]
  console.log(`${g}: ${t.bars} bars, wrong ${t.wrongBefore} -> ${t.wrongAfter} (${t.fixed} fixed, ${t.broken} broken); notes missing ${signed(t.missing)}, at the wrong time ${signed(t.time)}, extra ${signed(t.extra)}`)
}
if (totals.unpaired.extra) console.log(`notes in read parts paired with no answer part: ${signed(totals.unpaired.extra)}`)
console.log(`pages: ${pages.better} with fewer notes wrong, ${pages.worse} with more, ${pages.even} changed but even, ${pages.same} unchanged`)
if (readInOne.length) console.log(`not compared, read in one run only: ${readInOne.join(', ')}`)
if (readInNone.length) console.log(`not compared, read in neither run: ${readInNone.join(', ')}`)
if (unknown.length) console.log(`not compared, not found (EXTRA unset?): ${unknown.length} cases`)
