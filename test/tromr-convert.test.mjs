// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Tests for the TrOMR token-to-MusicXML converter (app/tromr-convert.js).
// The long token strings are the WASM runner's own outputs for the synthetic divisi page
// (test/fixtures/divisi-merge/) — the same page the merge tests use — so the converter is
// checked against the focr staff files it must match note for note. The Gute Nacht page
// (CC0) is covered the same way by the local validation script, not by a committed fixture.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { tokensToMusicXml } from '../app/tromr-convert.js'
import { parseXml } from '../app/merge.js'

const DIVISI0 = 'clef-G2+keySignature-CM+timeSignature-4/4+note-G3_half|note-C4_quarter|note-E4_quarter+note-C4_quarter|note-E4_quarter+note-F3_half|note-A3_quarter|note-F4_quarter+note-D4_quarter|note-G4_quarter+barline+note-G3_half|note-D4_quarter|note-G4_quarter+note-A3_quarter|note-F4_quarter+note-G3_half|note-C4_quarter|note-E4_quarter+note-B3_quarter|note-D4_quarter+barline+note-C4_eighth|note-C4_quarter+note-D4_eighth+note-E4_eighth+note-C4_quarter+note-F4_eighth+note-G4_eighth+note-A4_eighth+note-D4_quarter+note-E4_quarter+barline+note-C4_eighth|note-E4_quarter+note-D4_eighth+note-E4_eighth+note-D4_quarter+note-F4_eighth+note-G4_eighth+note-A4_eighth+note-D4_quarter+note-C4_quarter+barline'
const DIVISI1 = 'clef-F4+keySignature-CM+timeSignature-4/4+note-C3_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+note-F2_quarter|note-F3_quarter+note-G2_quarter|note-B3_quarter+barline+note-G2_quarter|note-B3_quarter+note-F2_quarter|note-F3_quarter+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+barline+note-C3_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+barline+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+barline'

/** A staff file's notes as plain objects, per measure, for comparison. */
function notesOf(xmlText) {
  const root = parseXml(xmlText)
  const out = []
  for (const part of root.children.filter(c => c.tag === 'part')) {
    for (const meas of part.children.filter(c => c.tag === 'measure')) {
      const notes = []
      for (const n of meas.children.filter(c => c.tag === 'note')) {
        const p = n.children.find(c => c.tag === 'pitch')
        const get = (el, t) => el?.children.find(c => c.tag === t)?.text ?? null
        notes.push({
          chord: !!n.children.find(c => c.tag === 'chord'),
          rest: !!n.children.find(c => c.tag === 'rest'),
          step: p ? get(p, 'step') : null,
          alter: p ? get(p, 'alter') : null,
          octave: p ? get(p, 'octave') : null,
          duration: get(n, 'duration'),
          type: get(n, 'type'),
          dot: !!n.children.find(c => c.tag === 'dot'),
        })
      }
      out.push({ bar: meas.attrs.number, notes })
    }
  }
  return out
}

function attrsOf(xmlText) {
  const root = parseXml(xmlText)
  const part = root.children.find(c => c.tag === 'part')
  const m1 = part.children.find(c => c.tag === 'measure')
  const at = m1.children.find(c => c.tag === 'attributes')
  const get = t => at?.children.find(c => c.tag === t)?.text ?? null
  const key = at?.children.find(c => c.tag === 'key')
  const time = at?.children.find(c => c.tag === 'time')
  const clef = at?.children.find(c => c.tag === 'clef')
  return {
    divisions: get('divisions'),
    clef: clef ? { sign: clef.children.find(c => c.tag === 'sign')?.text, line: clef.children.find(c => c.tag === 'line')?.text } : null,
    keyFifths: key?.children.find(c => c.tag === 'fifths')?.text ?? null,
    beats: time?.children.find(c => c.tag === 'beats')?.text ?? null,
    beatType: time?.children.find(c => c.tag === 'beat-type')?.text ?? null,
  }
}

test('divisi staff0 tokens convert to the focr staff file, note for note', async () => {
  const { xml, warnings, stats } = tokensToMusicXml(DIVISI0)
  assert.deepEqual(warnings, [])
  assert.equal(stats.notes, 40)
  assert.equal(stats.measures, 4)
  const ref = await readFile(new URL('./fixtures/divisi-merge/staff0.musicxml', import.meta.url), 'utf-8')
  assert.deepEqual(notesOf(xml), notesOf(ref))
  assert.deepEqual(attrsOf(xml), attrsOf(ref))
})

test('divisi staff1 tokens convert to the focr staff file, note for note', async () => {
  const { xml, warnings, stats } = tokensToMusicXml(DIVISI1)
  assert.deepEqual(warnings, [])
  assert.equal(stats.notes, 32)
  assert.equal(stats.measures, 4)
  const ref = await readFile(new URL('./fixtures/divisi-merge/staff1.musicxml', import.meta.url), 'utf-8')
  assert.deepEqual(notesOf(xml), notesOf(ref))
  assert.deepEqual(attrsOf(xml), attrsOf(ref))
})

test('rests, dots and accidentals: durations, types and alters', () => {
  const { xml, warnings } = tokensToMusicXml(
    // The model writes the accidental after the octave (C4#, E3b), not before it.
    'clef-F4+keySignature-FM+timeSignature-3/4+note-C3_half.+rest-quarter+note-D3#_eighth+note-E3b_quarter+barline')
  assert.deepEqual(warnings, [])
  const notes = notesOf(xml)[0].notes
  assert.equal(notes.length, 4)
  assert.deepEqual(notes[0], { chord: false, rest: false, step: 'C', alter: null, octave: '3', duration: '192', type: 'half', dot: true })
  assert.deepEqual(notes[1], { chord: false, rest: true, step: null, alter: null, octave: null, duration: '64', type: 'quarter', dot: false })
  assert.deepEqual(notes[2], { chord: false, rest: false, step: 'D', alter: '1', octave: '3', duration: '32', type: 'eighth', dot: false })
  assert.deepEqual(notes[3], { chord: false, rest: false, step: 'E', alter: '-1', octave: '3', duration: '64', type: 'quarter', dot: false })
  assert.deepEqual(attrsOf(xml), { divisions: '64', clef: { sign: 'F', line: '4' }, keyFifths: '-1', beats: '3', beatType: '4' })
})

test('multirest-N becomes N whole-measure rests, at the file’s own time signature', () => {
  const { xml, warnings, stats } = tokensToMusicXml(
    'clef-G2+keySignature-CM+timeSignature-2/4+multirest-2+note-C4_quarter+barline')
  assert.deepEqual(warnings, [])
  assert.equal(stats.measures, 3)
  assert.equal(stats.multirestBars, 2)
  const measures = notesOf(xml)
  assert.equal(measures.length, 3)
  assert.deepEqual(measures[0].notes, [{ chord: false, rest: true, step: null, alter: null, octave: null, duration: '128', type: 'whole', dot: false }])
  assert.deepEqual(measures[1].notes, measures[0].notes)
  assert.equal(measures[2].notes[0].duration, '64')
})

test('multirest without a time signature rests a whole 4/4 measure', () => {
  const { xml } = tokensToMusicXml('clef-G2+keySignature-CM+multirest-1+barline')
  assert.equal(notesOf(xml)[0].notes[0].duration, '256')
})

test('thirty_second is the thirtysecond the model sometimes writes', () => {
  const { xml, warnings } = tokensToMusicXml(
    'clef-G2+keySignature-FM+timeSignature-2/4+note-F4_sixteenth.+note-E4_thirty_second+barline')
  assert.deepEqual(warnings, [])
  const notes = notesOf(xml)[0].notes
  assert.equal(notes.length, 2)
  assert.equal(notes[0].duration, '24') // dotted 16th
  assert.equal(notes[0].type, '16th')
  assert.equal(notes[1].duration, '8') // 32nd
  assert.equal(notes[1].type, '32nd')
})

test('a chord group marks the 2nd and 3rd notes as chord notes', () => {
  const { xml } = tokensToMusicXml('clef-G2+keySignature-CM+timeSignature-4/4+note-C4_quarter|note-E4_quarter|note-G4_quarter+barline')
  const notes = notesOf(xml)[0].notes
  assert.equal(notes.length, 3)
  assert.equal(notes[0].chord, false)
  assert.equal(notes[1].chord, true)
  assert.equal(notes[2].chord, true)
})

test('a rest inside a chord group is transcribed as a chord rest, not dropped', () => {
  // The WASM model writes these on two-voice staves (Gute Nacht staff1, bar 1); the
  // merge ignores chord notes in its voice sums, so they are merge-neutral.
  const { xml, warnings } = tokensToMusicXml('clef-G2+keySignature-FM+timeSignature-2/4+note-F4_eighth|rest-quarter+barline')
  assert.deepEqual(warnings, [])
  const notes = notesOf(xml)[0].notes
  assert.equal(notes.length, 2)
  assert.equal(notes[1].chord, true)
  assert.equal(notes[1].rest, true)
  assert.equal(notes[1].duration, '64')
})

test('minor keys: fifths from the key name, mode omitted', () => {
  const { xml } = tokensToMusicXml('clef-G2+keySignature-Dm+timeSignature-4/4+note-A4_quarter+barline')
  assert.equal(attrsOf(xml).keyFifths, '-1')
  const { xml: xml2 } = tokensToMusicXml('clef-G2+keySignature-BbM+timeSignature-4/4+note-A4_quarter+barline')
  assert.equal(attrsOf(xml2).keyFifths, '-2')
})

test('unknown tokens are warned about and skipped, never thrown', () => {
  const { xml, warnings, stats } = tokensToMusicXml(
    'clef-G2+keySignature-CM+timeSignature-4/4+note-C4_quarter+garbage-token+note-D4_quarter+barline+note-E4_whole+barline')
  assert.equal(warnings.length, 1)
  assert.match(warnings[0], /garbage-token/)
  assert.equal(stats.notes, 3)
  assert.equal(notesOf(xml).length, 2)
})

test('empty input and a bare barline do not throw', () => {
  const a = tokensToMusicXml('')
  assert.equal(a.stats.notes, 0)
  assert.equal(a.stats.measures, 0)
  assert.equal(a.xml, null) // no measures at all: no staff file to merge
  assert.deepEqual(a.warnings, [])
  const b = tokensToMusicXml('barline')
  assert.equal(b.stats.measures, 0)
  assert.equal(b.xml, null)
})
