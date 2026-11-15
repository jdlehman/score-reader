// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The corpus scorer: a dropped measure costs only itself, and jumbled parts show in inPart.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { bars, score } from './score.mjs'

const STEP = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
const note = midi => `<note><pitch><step>${STEP[midi % 12]}</step>${[1, 3, 6, 8, 10].includes(midi % 12) ? '<alter>1</alter>' : ''}<octave>${Math.floor(midi / 12) - 1}</octave></pitch></note>`
const xml = parts => `<score-partwise><part-list>${parts.map((_, i) => `<score-part id="P${i}"><part-name>p</part-name></score-part>`).join('')}</part-list>${parts.map((measures, i) => `<part id="P${i}">${measures.map(m => `<measure>${m.map(note).join('')}</measure>`).join('')}</part>`).join('')}</score-partwise>`

// two parts, four bars, a different pitch in every bar
const upper = [[72, 74], [76, 77], [79, 81], [83, 84]]
const lower = [[48], [50], [52], [53]]
const answer = {
  bars: 4,
  parts: [upper, lower].map(bars => ({ notes: bars.flatMap((ps, i) => ps.map(midi => ({ bar: i + 1, midi }))) })),
}

test('a perfect read scores 100%', () => {
  const r = score(answer, xml([upper, lower]))
  assert.equal(r.notes, 1)
  assert.equal(r.inPart, 1)
  assert.equal(r.extra, 0)
})

test('a dropped measure costs only its own notes', () => {
  const r = score(answer, xml([[upper[0], upper[2], upper[3]], [lower[0], lower[2], lower[3]]]))
  assert.equal(r.notes, 9 / 12)
})

test('parts swapped halfway find every note but not in one part', () => {
  const r = score(answer, xml([[upper[0], upper[1], lower[2], lower[3]], [lower[0], lower[1], upper[2], upper[3]]]))
  assert.equal(r.notes, 1)
  assert.ok(r.inPart < 0.7, `inPart ${r.inPart}`)
})

// reads that look complete by pitch but aren't (an adversarial review of this scorer)
test('padding every bar with wrong notes costs precision', () => {
  const r = score(answer, xml([upper.map(m => [...m, 60, 61, 62]), lower.map(m => [...m, 36])]))
  assert.equal(r.notes, 1)
  assert.equal(r.precision, 12 / 28)
})

test('a measure read twice costs precision', () => {
  const r = score(answer, xml([upper.flatMap(m => [m, m]), lower.flatMap(m => [m, m])]))
  assert.equal(r.notes, 1)
  assert.equal(r.precision, 0.5)
})

test('two parts read as one are not both in their part', () => {
  const r = score(answer, xml([upper.map((m, i) => [...m, ...lower[i]])]))
  assert.equal(r.notes, 1)
  assert.equal(r.inPart, 8 / 12)
})

test('a part out of step with the others loses its notes', () => {
  const r = score(answer, xml([upper, [[], ...lower.slice(0, 3)]]))
  assert.ok(r.notes <= 9 / 12, `notes ${r.notes}`)
})

test('unpitched (drum) notes are not scored', () => {
  const drums = { bars: 1, parts: [{ notes: [{ bar: 1, unpitched: true, display_step: 'E' }] }] }
  assert.equal(score(drums, xml([[[60]]])).notes, null)
  const mixed = { bars: 1, parts: [{ notes: [{ bar: 1, midi: 60 }, { bar: 1, unpitched: true }] }] }
  assert.equal(score(mixed, xml([[[60]]])).notes, 1)
})

// rhythm: notes with durations (divisions 2 to the quarter), as Audiveris writes them
const timedNote = (midi, duration, extra = '') => `<note>${extra}<pitch><step>${STEP[midi % 12]}</step>${[1, 3, 6, 8, 10].includes(midi % 12) ? '<alter>1</alter>' : ''}<octave>${Math.floor(midi / 12) - 1}</octave></pitch><duration>${duration}</duration></note>`
const timedXml = measures => `<score-partwise><part-list><score-part id="P0"><part-name>p</part-name></score-part></part-list><part id="P0">${measures.map((m, i) => `<measure>${i ? '' : '<attributes><divisions>2</divisions></attributes>'}${m}</measure>`).join('')}</part></score-partwise>`
// bar 1: C5 and E5 together for a half, then G5 a half; under them, from the start, C3 a whole
const timedAnswer = { bars: 1, parts: [{ notes: [[72, 0], [76, 0], [79, 2], [48, 0]].map(([midi, onset]) => ({ bar: 1, midi, onset })) }] }

test('onsets follow chords, backups and forwards', () => {
  const r = score(timedAnswer, timedXml([timedNote(72, 4) + timedNote(76, 4, '<chord/>') + timedNote(79, 4) + '<backup><duration>8</duration></backup>' + timedNote(48, 8)]))
  assert.equal(r.notes, 1)
  assert.equal(r.rhythm, 1)
})

test('a note at the wrong beat counts in notes, not in rhythm', () => {
  // C5 and E5 read as quarters, so G5 starts a quarter early
  const r = score(timedAnswer, timedXml([timedNote(72, 2) + timedNote(76, 2, '<chord/>') + timedNote(79, 4) + '<backup><duration>6</duration></backup>' + timedNote(48, 8)]))
  assert.equal(r.notes, 1)
  assert.equal(r.rhythm, 3 / 4)
})

test('a forward moves the next note on; grace notes take no time', () => {
  const r = score(timedAnswer, timedXml(['<note><grace/><pitch><step>B</step><octave>4</octave></pitch></note>' + timedNote(72, 4) + timedNote(76, 4, '<chord/>') + '<forward><duration>4</duration></forward><backup><duration>4</duration></backup>' + timedNote(79, 4) + '<backup><duration>8</duration></backup>' + timedNote(48, 8)]))
  assert.equal(r.rhythm, 1)
})

test('rhythm is not scored without answer onsets', () => {
  assert.equal(score(answer, xml([upper, lower])).rhythm, null)
})

// bars(): what test/compare.mjs counts, a row an answer part and bar
const row = (rows, part, bar) => rows.find(r => r.part === part && r.bar === bar)

test('bars: a perfect read has nothing missing or extra', () => {
  const rows = bars(answer, xml([upper, lower]))
  assert.equal(rows.length, 8)
  assert.ok(rows.every(r => r.found === r.want && r.extra === 0))
})

test('bars: a missed note and a false one show in their part and bar', () => {
  const rows = bars(answer, xml([[upper[0], [76], upper[2], [...upper[3], 60]], lower]))
  assert.deepEqual([row(rows, 0, 2).want, row(rows, 0, 2).found, row(rows, 0, 2).extra], [2, 1, 0])
  assert.deepEqual([row(rows, 0, 4).found, row(rows, 0, 4).extra], [2, 1])
  assert.equal(row(rows, 1, 2).found, 1)
})

test('bars: a note at the wrong beat is found but not on time', () => {
  const r = row(bars(timedAnswer, timedXml([timedNote(72, 2) + timedNote(76, 2, '<chord/>') + timedNote(79, 4) + '<backup><duration>6</duration></backup>' + timedNote(48, 8)])), 0, 1)
  assert.deepEqual([r.want, r.timed, r.found, r.onTime], [4, 4, 4, 3])
})

test('bars: a read part paired with no answer part is all extra', () => {
  const rows = bars(answer, xml([upper, lower, [[60], [], [], []]]))
  assert.deepEqual(rows.filter(r => r.part === -1).map(r => [r.bar, r.extra]), [[1, 1]])
})
