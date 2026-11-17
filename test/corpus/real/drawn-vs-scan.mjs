// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// What a real scan costs: the same bars of a song read from the page Verovio drew (pages/,
// gute-nacht/) and from the scan (real/), notes and rhythm found in each, summed over the bars the
// drawn page holds. Two corpus runs (RUN=<name>), which may be one run that read both.
//   node test/corpus/real/drawn-vs-scan.mjs <drawn run> <scan run>
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { ROOT, allCases, joined, reads } from '../../cases.mjs'
import { bars } from '../../score.mjs'

const [drawnRun, scanRun] = process.argv.slice(2)
const cases = Object.fromEntries(allCases(false).map(c => [c.name, c]))
const rowsOf = (run, name, offset) => {
  const dir = join(ROOT, '.work', 'corpus', run)
  const batch = JSON.parse(readFileSync(join(dir, 'batches.json'), 'utf8'))[name]
  if (batch == null) throw new Error(`${name} not in ${run}`)
  const files = reads(join(dir, `batch-${batch}`), cases[name])
  const answer = JSON.parse(readFileSync(cases[name].answer, 'utf8'))
  const off = offset ?? (answer.bars_global ? answer.bars_global[0] - 1 : 0)
  if (!files.length) return { unread: true, rows: answer.parts.flatMap((p, a) => p.notes.map(n => ({ part: a, bar: n.bar + off, want: 1, timed: 1, found: 0, onTime: 0, extra: 0 }))) }
  return { rows: bars(answer, joined(files)).map(r => ({ ...r, bar: r.bar + off })) }
}
const SONGS = [
  ['Gute Nacht (first 12 bars)', [['pages/lieder-gute-nacht', 0]], 'real/lieder-schubert-gute-nacht-p', 4],
  ['Gute Nacht (whole song)', [1, 2, 3, 4].map(k => [`gute-nacht/gute-nacht-p0${k}`]), 'real/lieder-schubert-gute-nacht-p', 4],
  ['Der Lindenbaum', [['pages/lieder-lindenbaum', 0]], 'real/lieder-schubert-lindenbaum-p', 4],
  ['Widmung', [['pages/lieder-schumann-widmung', 0]], 'real/lieder-schumann-widmung-p', 2],
  ['Wiegenlied', [['pages/lieder-brahms-wiegenlied', 0]], 'real/lieder-brahms-wiegenlied-p', 1],
  ['Après un rêve', [['pages/lieder-faure-apres-un-reve', 0]], 'real/lieder-faure-apres-un-reve-p', 4],
  ['Erlkönig', [['pages/lieder-schubert-erlkoenig', 12]], 'real/lieder-schubert-erlkoenig-p', 6],
]
const pct = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : '-').padStart(5)
console.log('song'.padEnd(28), 'bars'.padStart(5), '  drawn notes rhythm', '   scan notes rhythm')
const tot = { d: [0, 0, 0, 0], s: [0, 0, 0, 0] }
for (const [title, drawn, scanPrefix, n] of SONGS) {
  const d = drawn.flatMap(([name, off]) => rowsOf(drawnRun, name, off).rows)
  const s = Array.from({ length: n }, (_, k) => rowsOf(scanRun, scanPrefix + (k + 1)).rows).flat()
  const barsD = new Set(d.map(r => r.bar))
  const sum = rows => rows.filter(r => r.part >= 0 && barsD.has(r.bar)).reduce((t, r) => [t[0] + r.found, t[1] + r.want, t[2] + r.onTime, t[3] + r.timed], [0, 0, 0, 0])
  const [a, b] = [sum(d), sum(s)]
  a.forEach((x, i) => (tot.d[i] += x)); b.forEach((x, i) => (tot.s[i] += x))
  console.log(title.padEnd(28), String(barsD.size).padStart(5), '   ', pct(a[0], a[1]), pct(a[2], a[3]), '    ', pct(b[0], b[1]), pct(b[2], b[3]))
}
console.log('all (notes summed)'.padEnd(28), ''.padStart(5), '   ', pct(tot.d[0], tot.d[1]), pct(tot.d[2], tot.d[3]), '    ', pct(tot.s[0], tot.s[1]), pct(tot.s[2], tot.s[3]))
