// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// app/beams.js: a beamed chord's beams on its first note only, so Verovio keeps its notes.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import createModule from 'verovio/wasm'
import { LOG_OFF, VerovioToolkit, enableLog } from 'verovio/esm'
import { beamsOnChordHeads } from '../app/beams.js'

const note = (step, beam, chord = false) => `<note>${chord ? '<chord/>' : ''}<pitch><step>${step}</step><octave>4</octave></pitch><duration>1</duration><voice>1</voice><type>eighth</type><beam number="1">${beam}</beam></note>`
const chord = beam => note('C', beam) + note('E', beam, true) + note('G', beam, true)
const score = body => `<?xml version="1.0"?><score-partwise version="4.0"><part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list><part id="P1"><measure number="1"><attributes><divisions>2</divisions><time><beats>2</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>${body}</measure></part></score-partwise>`
const xml = score(chord('begin') + chord('continue') + chord('continue') + chord('end'))

test('only a chord\'s first note keeps its beams', () => {
  const out = beamsOnChordHeads(xml)
  assert.equal((out.match(/<beam\b/g) ?? []).length, 4)
  assert.equal((out.match(/<note\b/g) ?? []).length, 12)
  assert.equal(beamsOnChordHeads(out), out)
  const plain = score(note('C', 'begin') + note('D', 'end'))
  assert.equal(beamsOnChordHeads(plain), plain)
})

test('Verovio keeps every note of the beamed chords then', async () => {
  const module = await createModule()
  enableLog(LOG_OFF, module)
  const tk = new VerovioToolkit(module)
  const drawn = x => (tk.loadData(x), (tk.getMEI().match(/<note\b/g) ?? []).length)
  assert.ok(drawn(xml) < 12) // as Audiveris writes it
  assert.equal(drawn(beamsOnChordHeads(xml)), 12)
})
