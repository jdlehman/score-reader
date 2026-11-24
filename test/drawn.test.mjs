// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// test/drawn.mjs: a read as Verovio draws it. Verovio times notes as triplets only between
// <tuplet> start and stop marks (app/columns.js writes them for that reason).
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { compareDrawn, drawnBars } from './drawn.mjs'

const tm = '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>'
const triplets = marks => `<?xml version="1.0"?><score-partwise><part-list><score-part id="P1"><part-name>A</part-name></score-part></part-list><part id="P1"><measure number="1"><attributes><divisions>6</divisions><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>${Array.from({ length: 12 }, (_, i) => `<note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><voice>1</voice><type>eighth</type>${tm}${marks && i % 3 !== 1 ? `<notations><tuplet type="${i % 3 ? 'stop' : 'start'}" number="1"/></notations>` : ''}</note>`).join('')}</measure><measure number="2"><note><pitch><step>D</step><octave>4</octave></pitch><duration>24</duration><voice>1</voice><type>whole</type></note></measure></part></score-partwise>`

test('a bar Verovio takes as written: every note, at its time', async () => {
  const bars = await drawnBars(triplets(true))
  assert.deepEqual(bars.map(b => [b.notes, b.drawn, b.moved]), [[12, 12, 0], [1, 1, 0]])
})

test('triplets without their marks: Verovio keeps the notes but times them as plain eighths', async () => {
  const bars = await drawnBars(triplets(false))
  assert.equal(bars[0].drawn, 12)
  assert.ok(bars[0].moved >= 8, `moved ${bars[0].moved}`)
  assert.deepEqual(await compareDrawn(triplets(false), triplets(true)), { full: [2, 2], moved: [bars[0].moved + bars[1].moved, 0] })
})
