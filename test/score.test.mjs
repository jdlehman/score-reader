// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The corpus scorer: a dropped measure costs only itself, and jumbled parts show in inPart.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { score } from './score.mjs'

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
