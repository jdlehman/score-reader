import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import {
  parseXml, serialiseXml, mergeMusicXml, readMxl, writeMxl,
  beatsOf, divisionsOf, barsPerSystem, staffPairs, voiceSums, sliceValid,
  pitchSet,
} from '../app/merge.js'

// --- small MusicXML builders (hand-made scores, no fixtures needed) ---------------

function noteXml(pitch, dur, { voice = 1, staff = 1, type = 'quarter', rest = false, chord = false } = {}) {
  const pitchEl = rest ? '<rest/>' : `<pitch><step>${pitch[0]}</step>${pitch[1] === '#' || pitch[1] === 'b' ? `<alter>${pitch[1] === '#' ? 1 : -1}</alter>` : ''}<octave>${pitch.slice(-1)}</octave></pitch>`
  return `<note>${chord ? '<chord/>' : ''}${pitchEl}<duration>${dur}</duration><voice>${voice}</voice><type>${type}</type><staff>${staff}</staff></note>`
}

function measureXml(n, notes, { newSystem = false, divisions, beats } = {}) {
  const attrs = divisions ? `<attributes><divisions>${divisions}</divisions>${beats ? `<time><beats>${beats}</beats><beat-type>4</beat-type></time>` : ''}</attributes>` : ''
  const print = newSystem ? '<print new-system="yes"/>' : ''
  return `<measure number="${n}">${print}${attrs}${notes.join('')}</measure>`
}

function scoreXml(parts) {
  const list = parts.map(p => `<score-part id="${p.id}"><part-name>${p.name}</part-name></score-part>`).join('')
  const body = parts.map(p => `<part id="${p.id}">${p.measures.join('')}</part>`).join('')
  return `<?xml version="1.0" encoding="UTF-8"?><score-partwise version="4.0"><part-list>${list}</part-list>${body}</score-partwise>`
}

// TrOMR staff file: one part, divisions 64, measures numbered 1..N in the system.
function tromrXml(measures, divs = 64) {
  const body = measures.map((m, i) => measureXml(i + 1, m.notes, { divisions: i === 0 ? divs : undefined })).join('')
  return scoreXml([{ id: 'P1', name: 'Staff 1', measures: [body] }])
}

// --- scorer (same shape as score_all.py: exact pitch multiset per bar, validity) --

function scoreAgainstGT(xmlText, gt) {
  const root = parseXml(xmlText)
  const pred = []
  for (const part of root.children.filter(c => c.tag === 'part')) {
    for (const meas of part.children.filter(c => c.tag === 'measure')) {
      const bar = parseInt(meas.attrs.number ?? '0', 10)
      for (const n of meas.children.filter(c => c.tag === 'note')) {
        const p = n.children.find(c => c.tag === 'pitch')
        if (!p) continue
        const step = p.children.find(c => c.tag === 'step')?.text
        const oct = p.children.find(c => c.tag === 'octave')?.text
        // step+octave only, no alter: that is the GT format (score_all.py), and
        // TrOMR writes no <alter> at all, so alter-aware keys would never match GT
        pred.push({ bar, pitch: step + oct })
      }
    }
  }
  const gtNotes = gt.parts.flatMap(p => p.notes)
  const hits = new Map()
  const byBar = new Map()
  for (const n of gtNotes) byBar.set(n.bar, [...(byBar.get(n.bar) ?? []), n.pitch])
  const pByBar = new Map()
  for (const n of pred) pByBar.set(n.bar, [...(pByBar.get(n.bar) ?? []), n.pitch])
  let exact = 0
  for (const [bar, g] of byBar) {
    const counts = new Map()
    for (const p of pByBar.get(bar) ?? []) counts.set(p, (counts.get(p) ?? 0) + 1)
    for (const p of g) if ((counts.get(p) ?? 0) > 0) { exact++; counts.set(p, counts.get(p) - 1) }
  }
  // measures valid: per (bar, voice) pair, summed durations vs the bar — the same
  // definition score_all.py uses (Hallelujah baseline 41/57, not 41/56)
  let valid = 0, total = 0
  for (const part of root.children.filter(c => c.tag === 'part')) {
    const divs = divisionsOf(part)
    const sums = new Map()
    for (const meas of part.children.filter(c => c.tag === 'measure')) {
      const bar = parseInt(meas.attrs.number ?? '0', 10)
      for (const n of meas.children.filter(c => c.tag === 'note')) {
        if (n.children.some(c => c.tag === 'chord')) continue
        const dur = n.children.find(c => c.tag === 'duration')
        if (!dur) continue
        const voice = parseInt(n.children.find(c => c.tag === 'voice')?.text ?? '1', 10)
        const key = `${bar}:${voice}`
        sums.set(key, (sums.get(key) ?? 0) + parseFloat(dur.text) / divs)
      }
    }
    for (const s of sums.values()) { total++; if (Math.abs(s - gt.beats) < 1e-6) valid++ }
  }
  return { exact, gtTotal: gtNotes.length, valid, total }
}

// --- parser / helpers -----------------------------------------------------------

test('XML parser round-trips a real TrOMR staff file with identical notes', async () => {
  const xml = await readFile(new URL('./fixtures/hallelujah-merge/staff0.musicxml', import.meta.url), 'utf-8')
  const again = serialiseXml(parseXml(xml))
  const notesOf = t => parseXml(t).children.find(c => c.tag === 'part').children
    .flatMap(m => m.children.filter(c => c.tag === 'note')).length
  assert.equal(notesOf(again), notesOf(xml))
  assert.equal(notesOf(xml), 24) // staff0: 6 measures, 1+1+1+5+7+9 notes
})

test('helpers read beats, divisions, systems and staff pairs from Audiveris Hallelujah', async () => {
  const mxl = await readFile(new URL('./fixtures/hallelujah-merge/hallelujah-audiveris.mxl', import.meta.url))
  const xml = await readMxl(mxl)
  const root = parseXml(xml)
  assert.equal(beatsOf(root), 4)
  assert.equal(divisionsOf(root.children.find(c => c.tag === 'part')), 12)
  assert.deepEqual(barsPerSystem(root).map(s => s.bars), [6, 4, 4]) // systems at bars 1, 7, 11
  assert.deepEqual(staffPairs(root), [[0, 1], [1, 1], [2, 1], [3, 1]])
})

// --- the gate -------------------------------------------------------------------

function twoPartScore(audMeasures) {
  // SATB-shaped: 2 parts, 1 staff each, divisions 12, 4/4, 2 bars, one system.
  const mk = (id, name, measures) => ({ id, name, measures: measures.map((notes, i) =>
    measureXml(i + 1, notes, { divisions: i === 0 ? 12 : undefined, beats: i === 0 ? 4 : undefined })) })
  return scoreXml([mk('P1', 'Soprano', audMeasures[0]), mk('P2', 'Bass', audMeasures[1])])
}

test('valid Audiveris measure is never touched, even when TrOMR differs', () => {
  // 4/4, divisions 12: four quarters = 48 ticks. Soprano valid, bass valid.
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  const tromr = [
    tromrXml([{ notes: [noteXml('A5', 64, { type: 'quarter' }), noteXml('A5', 64), noteXml('A5', 64), noteXml('A5', 64)] },
              { notes: [noteXml('A5', 64), noteXml('A5', 64), noteXml('A5', 64), noteXml('A5', 64)] }]),
    tromrXml([{ notes: [noteXml('A2', 64), noteXml('A2', 64), noteXml('A2', 64), noteXml('A2', 64)] },
              { notes: [noteXml('A2', 64), noteXml('A2', 64), noteXml('A2', 64), noteXml('A2', 64)] }]),
  ]
  const { xml, report } = mergeMusicXml(aud, tromr)
  assert.equal(report.replaced.length, 0)
  assert.equal(report.kept, 4)
  assert.equal(parseXml(xml).children.find(c => c.tag === 'part')
    .children[0].children.filter(c => c.tag === 'note').length, 4)
})

test('duration-invalid Audiveris slice is replaced when TrOMR is valid and pitches agree', () => {
  // Soprano bar 2 sums to 3 beats (missing a quarter); bass is fine.
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12)]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] }]),
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] }]),
  ]
  const { xml, report } = mergeMusicXml(aud, tromr)
  assert.equal(report.replaced.length, 1)
  assert.deepEqual(report.replaced[0], { part: 0, bar: 2, staff: 1, tromrStaff: 0, tromrBar: 2, notes: 4 })
  const out = parseXml(xml)
  const parts = out.children.filter(c => c.tag === 'part')
  const sopranoBar2 = parts[0].children[1]
  assert.equal(sopranoBar2.children.filter(c => c.tag === 'note').length, 4)
  // durations rescaled from TrOMR divisions 64 to Audiveris divisions 12
  assert.deepEqual(sopranoBar2.children.filter(c => c.tag === 'note')
    .map(n => n.children.find(c => c.tag === 'duration').text), ['12', '12', '12', '12'])
  // the bass in the same measure, and the valid soprano bar 1, are untouched
  assert.equal(report.kept, 3)
})

test('replacement is refused when TrOMR is itself duration-invalid (triplet bars)', () => {
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12)]], // 3 beats, invalid
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  // TrOMR flattens triplet eighths to plain eighths: 7 eighths = 3.5 beats, invalid.
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: Array.from({ length: 7 }, () => noteXml('C5', 32, { type: 'eighth' })) }]),
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] }]),
  ]
  const { xml, report } = mergeMusicXml(aud, tromr)
  assert.equal(report.replaced.length, 0)
  assert.deepEqual(report.skipped, [{ part: 0, bar: 2, staff: 1, reason: 'tromr-invalid' }])
  assert.equal(scoreAgainstGT(xml, { parts: [], beats: 4 }).exact, 0) // scorer needs GT; output equals input here
  assert.equal(xml, serialiseXml(parseXml(aud)))
})

test('replacement is refused when TrOMR pitches disagree — the Hallelujah regression', () => {
  // Audiveris bar 2 is invalid only in rest durations: its pitches are right.
  // TrOMR is valid but drops one pitch (E5). The old merge (no pitch check) replaced
  // this and lost pitch; the gate must refuse.
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12, { rest: true })]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  // make bar 2 invalid: the rest is 6 ticks (half a beat) instead of 12
  const audBroken = aud.replace(
    noteXml('G5', 12, { rest: true }), noteXml('G5', 6, { rest: true }))
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('G5', 64), noteXml('A5', 64)] }]), // no E5
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] }]),
  ]
  const { xml, report } = mergeMusicXml(audBroken, tromr)
  assert.equal(report.replaced.length, 0)
  assert.deepEqual(report.skipped, [{ part: 0, bar: 2, staff: 1, reason: 'pitch-disagrees' }])
  assert.equal(xml, serialiseXml(parseXml(audBroken)))
})

test('no note-list union: a replacement holds exactly TrOMR notes, other staff untouched', () => {
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12)]], // soprano bar 2 invalid (2 beats)
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] }]),
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] }]),
  ]
  const { xml } = mergeMusicXml(aud, tromr)
  const out = parseXml(xml)
  const parts = out.children.filter(c => c.tag === 'part')
  const sopranoBar2 = parts[0].children[1]
  const pitches = sopranoBar2.children.filter(c => c.tag === 'note')
    .map(n => n.children.find(c => c.tag === 'pitch').children.find(c => c.tag === 'step').text)
  assert.deepEqual(pitches, ['C', 'D', 'E', 'G']) // exactly TrOMR's, no Audiveris leftovers
  const bassBar2 = parts[1].children[1]
  assert.deepEqual(bassBar2.children.filter(c => c.tag === 'note')
    .map(n => n.children.find(c => c.tag === 'pitch').children.find(c => c.tag === 'step').text),
    ['C', 'D', 'E', 'G'])
})

test('missing Audiveris notes: an empty staff slice is filled when TrOMR is valid', () => {
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12, { rest: true }), noteXml('C5', 12, { rest: true }), noteXml('C5', 12, { rest: true }), noteXml('C5', 12, { rest: true })]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] }]),
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] }]),
  ]
  const { report } = mergeMusicXml(aud, tromr)
  // the all-rest bar is duration-valid (4 beats of rest) so it is kept, not replaced:
  // a rest-only slice is not "missing notes" to the gate — it is a valid measure.
  assert.equal(report.replaced.length, 0)
  assert.equal(report.kept, 4)
})

test('divisi: Audiveris bass split across 5 voices is replaced by TrOMR single-voice bar', () => {
  // Bass bar 2: five voices of one quarter each — every voice sums to 1 beat, invalid.
  const bassBar2 = [1, 2, 3, 4, 5].map(v => noteXml('C3', 12, { voice: v }))
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     bassBar2],
  ])
  const tromr = [
    tromrXml([{ notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] },
              { notes: [noteXml('C5', 64), noteXml('D5', 64), noteXml('E5', 64), noteXml('G5', 64)] }]),
    tromrXml([{ notes: [noteXml('C3', 64), noteXml('D3', 64), noteXml('E3', 64), noteXml('G3', 64)] },
              { notes: [noteXml('C3', 64), noteXml('C3', 64), noteXml('C3', 64), noteXml('C3', 64)] }]),
  ]
  const { xml, report } = mergeMusicXml(aud, tromr)
  assert.equal(report.replaced.length, 1)
  assert.equal(report.replaced[0].part, 1)
  const out = parseXml(xml)
  const parts = out.children.filter(c => c.tag === 'part')
  const bassBar2Out = parts[1].children[1]
  assert.equal(bassBar2Out.children.filter(c => c.tag === 'note').length, 4)
  assert.ok(bassBar2Out.children.filter(c => c.tag === 'note')
    .every(n => n.children.find(c => c.tag === 'voice').text === '1'))
})

test('no TrOMR files at all: everything is kept, output equals input', () => {
  const aud = twoPartScore([
    [[noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12)],
     [noteXml('C5', 12), noteXml('D5', 12), noteXml('E5', 12), noteXml('G5', 12)]],
    [[noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)],
     [noteXml('C3', 12), noteXml('D3', 12), noteXml('E3', 12), noteXml('G3', 12)]],
  ])
  const { xml, report } = mergeMusicXml(aud, [])
  assert.equal(report.replaced.length, 0)
  assert.equal(report.skipped.length, 1)
  assert.equal(report.skipped[0].reason, 'no-tromr-staff')
  assert.equal(xml, serialiseXml(parseXml(aud)))
})

// --- real files -----------------------------------------------------------------

async function loadHallelujah() {
  const mxl = await readFile(new URL('./fixtures/hallelujah-merge/hallelujah-audiveris.mxl', import.meta.url))
  const audXml = await readMxl(mxl)
  const tromr = []
  for (let i = 0; i < 12; i++) {
    tromr.push(await readFile(new URL(`./fixtures/hallelujah-merge/staff${i}.musicxml`, import.meta.url), 'utf-8'))
  }
  const gt = JSON.parse(await readFile(new URL('./fixtures/hallelujah-merge/hallelujah-satb.json', import.meta.url), 'utf-8'))
  return { audXml, tromr, gt }
}

test('Hallelujah: gated merge improves validity without losing pitch (217 stays 217)', async () => {
  const { audXml, tromr, gt } = await loadHallelujah()
  const before = scoreAgainstGT(audXml, gt)
  assert.equal(before.exact, 217, 'baseline Audiveris exact pitch')
  assert.equal(before.valid, 41, 'baseline Audiveris valid measures')
  assert.equal(before.total, 57)
  const { xml, report } = mergeMusicXml(audXml, tromr)
  const after = scoreAgainstGT(xml, gt)
  assert.equal(after.exact, 217, 'no pitch lost — the old ungated merge dropped this to 213')
  assert.ok(after.valid > before.valid, `validity ${before.valid} -> ${after.valid}`)
  assert.ok(report.skipped.some(s => s.reason === 'pitch-disagrees'),
    'the gate refused at least one pitch-disagreeing replacement')
})

test('divisi-tuplet: gated merge keeps all 72 pitches and improves validity', async () => {
  const mxl = await readFile(new URL('./fixtures/divisi-merge/divisi-audiveris.mxl', import.meta.url))
  const audXml = await readMxl(mxl)
  const tromr = [
    await readFile(new URL('./fixtures/divisi-merge/staff0.musicxml', import.meta.url), 'utf-8'),
    await readFile(new URL('./fixtures/divisi-merge/staff1.musicxml', import.meta.url), 'utf-8'),
  ]
  const gt = JSON.parse(await readFile(new URL('./fixtures/divisi-merge/divisi-tuplet.json', import.meta.url), 'utf-8'))
  const before = scoreAgainstGT(audXml, gt)
  assert.equal(before.exact, 72, 'baseline Audiveris exact pitch')
  const { xml } = mergeMusicXml(audXml, tromr)
  const after = scoreAgainstGT(xml, gt)
  assert.equal(after.exact, 72, 'no pitch lost')
  assert.ok(after.valid >= before.valid, `validity ${before.valid} -> ${after.valid}`)
})

// --- .mxl round-trip --------------------------------------------------------------

test('.mxl round-trip: read, write, read again keeps the same notes', async () => {
  const mxl = await readFile(new URL('./fixtures/hallelujah-merge/hallelujah-audiveris.mxl', import.meta.url))
  const xml = await readMxl(mxl)
  const out = await writeMxl(xml, 'hallelujah-p-1.xml')
  const back = await readMxl(out)
  const count = t => parseXml(t).children.filter(c => c.tag === 'part')
    .flatMap(p => p.children.filter(c => c.tag === 'measure'))
    .flatMap(m => m.children.filter(c => c.tag === 'note')).length
  assert.equal(count(back), count(xml))
  // 275 note elements including rests and chord notes (221 sounding notes)
})
