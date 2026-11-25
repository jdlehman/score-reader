// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// app/columns.js: a part's bar that doesn't add up is re-timed by the columns of the bars that do.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { alignColumns } from '../app/columns.js'
import { parseMusicXml } from './score.mjs'

const note = ({ x, dur, type, voice = 1, step = 'C', rest = false, dots = 0, chord = false, beam = null }) =>
  `<note default-x="${x}">${chord ? '<chord/>' : ''}${rest ? '<rest/>' : `<pitch><step>${step}</step><octave>4</octave></pitch>`}<duration>${dur}</duration><voice>${voice}</voice><type>${type}</type>${'<dot />'.repeat(dots)}<stem>up</stem>${beam ? `<beam number="1">${beam}</beam>` : ''}</note>`
const time = (beats = 4, divisions = 2) => `<attributes><divisions>${divisions}</divisions><time><beats>${beats}</beats><beat-type>4</beat-type></time></attributes>`
const measure = (n, ...body) => `<measure number="${n}">${body.join('')}</measure>`
const score = (...parts) => `<?xml version="1.0"?><score-partwise><part-list>${parts.map((_, i) => `<score-part id="P${i + 1}"><part-name>V${i + 1}</part-name></score-part>`).join('')}</part-list>${parts.map((ms, i) => `<part id="P${i + 1}">${ms.join('')}</part>`).join('')}</score-partwise>`
const quarters = (n, xs = [10, 50, 90, 130], divisions = 2) => measure(n, ...xs.map(x => note({ x, dur: divisions, type: 'quarter' })))
/** Onsets (quarter notes) of each part's notes in bar i (0-based). */
const onsets = (xml, i) => parseMusicXml(xml).map(p => p.measures[i].notes.map(n => n.onset))

test('a note read too long: the bar takes its times from the other part', () => {
  const xml = score(
    [measure(1, time(), note({ x: 10, dur: 8, type: 'whole' })), quarters(2), quarters(3)],
    // bar 2: the first note read as a half (a missed flag or beam would do the same)
    [measure(1, time(), note({ x: 10, dur: 8, type: 'whole' })), measure(2, note({ x: 10, dur: 4, type: 'half' }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }), note({ x: 130, dur: 2, type: 'quarter' })), quarters(3)],
  )
  assert.deepEqual(onsets(xml, 1)[1], [0, 2, 3, 4])
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 1)[1], [0, 1, 2, 3])
  const bar2 = out.match(/<part id="P2">[\s\S]*?<measure number="2">([\s\S]*?)<\/measure>/)[1]
  assert.equal((bar2.match(/<type>quarter<\/type>/g) ?? []).length, 4)
  assert.equal((bar2.match(/<duration>2<\/duration>/g) ?? []).length, 4)
  assert.deepEqual(onsets(out, 1)[0], [0, 1, 2, 3]) // the other part as it was
})

test('bars that add up are left as they are', () => {
  const xml = score([measure(1, time()), quarters(2), quarters(3)], [measure(1, time()), quarters(2), quarters(3)])
  assert.deepEqual(alignColumns(xml), { xml, bars: 0 })
})

test('a length no single value can write (a quarter and a sixteenth) leaves the voice as read', () => {
  const part1 = [measure(1, time(4, 4), note({ x: 10, dur: 4, type: 'quarter' }), note({ x: 40, dur: 1, type: '16th' }), note({ x: 60, dur: 3, type: 'eighth', dots: 1 }), note({ x: 100, dur: 8, type: 'half' }))]
  const part2 = [measure(1, time(4, 4), note({ x: 10, dur: 8, type: 'half' }), note({ x: 60, dur: 4, type: 'quarter' }), note({ x: 100, dur: 8, type: 'half' }))]
  const xml = score(part1, part2)
  assert.deepEqual(alignColumns(xml), { xml, bars: 0 })
})

test('a second voice in the re-timed bar keeps its times (the backup follows the first voice)', () => {
  const v1 = [note({ x: 10, dur: 4, type: 'half' }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }), note({ x: 130, dur: 2, type: 'quarter' })]
  const v2 = [note({ x: 10, dur: 4, type: 'half', voice: 2, step: 'A' }), note({ x: 90, dur: 4, type: 'half', voice: 2, step: 'A' })]
  const xml = score(
    [measure(1, time(), quarters(1).replace(/^<measure number="1">|<\/measure>$/g, '')), quarters(2), quarters(3)],
    [measure(1, time(), quarters(1).replace(/^<measure number="1">|<\/measure>$/g, '')), measure(2, ...v1, '<backup><duration>10</duration></backup>', ...v2), quarters(3)],
  )
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 1)[1], [0, 1, 2, 3, 0, 2])
  assert.match(out, /<backup><duration>8<\/duration><\/backup>/)
})

test('with no time signature, the length most bars have, if a common one', () => {
  const broken = measure(3, note({ x: 10, dur: 4, type: 'half' }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }), note({ x: 130, dur: 2, type: 'quarter' }))
  const top = ['<attributes><divisions>2</divisions></attributes>']
  const bars = (part2bar3, extra = []) => score(
    [measure(1, ...top, note({ x: 10, dur: 8, type: 'whole' })), quarters(2), quarters(3), quarters(4), quarters(5), ...extra.map((b, i) => quarters(6 + i))],
    [measure(1, ...top, note({ x: 10, dur: 8, type: 'whole' })), quarters(2), part2bar3, quarters(4), quarters(5), ...extra.map((b, i) => quarters(6 + i))],
  )
  // most bars at four quarters: a length to trust
  assert.equal(alignColumns(bars(broken)).bars, 1)
  // bars mostly at three and a half quarters: none
  const short = n => measure(n, note({ x: 10, dur: 3, type: 'quarter', dots: 1 }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }))
  const xml = score(
    [measure(1, ...top, note({ x: 10, dur: 8, type: 'whole' })), short(2), short(3), short(4), short(5), quarters(6)],
    [measure(1, ...top, note({ x: 10, dur: 8, type: 'whole' })), short(2), short(3), short(4), short(5), quarters(6)],
  )
  assert.equal(alignColumns(xml).bars, 0)
})

test('a short first bar (a pickup) is no reason to re-time', () => {
  const pickup = measure(1, time(), note({ x: 10, dur: 2, type: 'quarter' }))
  const xml = score([pickup, quarters(2), quarters(3)], [pickup.replace('default-x="10"', 'default-x="12"'), quarters(2), quarters(3)])
  assert.equal(alignColumns(xml).bars, 0)
})

test('one part: nothing to line up with', () => {
  const xml = score([measure(1, time(), note({ x: 10, dur: 4, type: 'half' }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }), note({ x: 130, dur: 2, type: 'quarter' }))])
  assert.equal(alignColumns(xml).bars, 0)
})

test('eighths read plain where the other part puts every third on the beat: an unmarked triplet', () => {
  const xs = [10, 23, 36, 50, 63, 76, 90, 103, 116, 130, 143, 156]
  const xml = score(
    [measure(1, time(4, 6), note({ x: 10, dur: 24, type: 'whole' })), quarters(2, undefined, 6), quarters(3, undefined, 6)],
    [measure(1, time(4, 6), note({ x: 10, dur: 24, type: 'whole' })), measure(2, ...xs.map(x => note({ x, dur: 3, type: 'eighth' }))), quarters(3, undefined, 6)],
  )
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 1)[1].map(t => Math.round(t * 3)), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
  const bar2 = out.match(/<part id="P2">[\s\S]*?<measure number="2">([\s\S]*?)<\/measure>/)[1]
  assert.equal((bar2.match(/<actual-notes>3<\/actual-notes>/g) ?? []).length, 12)
  assert.equal((bar2.match(/<type>eighth<\/type>/g) ?? []).length, 12)
  // four triplets, each marked where it starts and stops (Verovio times them only so)
  assert.equal((bar2.match(/<tuplet type="start" number="1"\/>/g) ?? []).length, 4)
  assert.equal((bar2.match(/<tuplet type="stop" number="1"\/>/g) ?? []).length, 4)
})

test('a triplet the divisions can\'t count: the part counts three times finer, its other notes as long as before', () => {
  const xs = [10, 23, 36, 50, 63, 76, 90, 103, 116, 130, 143, 156]
  const xml = score(
    [measure(1, time(4, 2), note({ x: 10, dur: 8, type: 'whole' })), quarters(2), quarters(3)],
    [measure(1, time(4, 2), note({ x: 10, dur: 8, type: 'whole' })), measure(2, ...xs.map(x => note({ x, dur: 1, type: 'eighth' }))), quarters(3)],
  )
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 1)[1].map(t => Math.round(t * 3)), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
  assert.deepEqual(onsets(out, 2), onsets(xml, 2))
  assert.match(out.match(/<part id="P2">[\s\S]*<\/part>/)[0], /<divisions>6<\/divisions>/)
  assert.match(out.match(/<part id="P1">[\s\S]*?<\/part>/)[0], /<divisions>2<\/divisions>/)
})

test('a chord\'s second head, printed beside the stem, is not its column', () => {
  // part 2's last chord C-D (a second, stem up): D printed right of the stem at x 204, by part 1's
  // next note (x 206), while the chord's column is C's, x 193, where part 1 has no note
  const p1 = measure(2, note({ x: 20, dur: 2, type: 'quarter' }), note({ x: 79, dur: 2, type: 'quarter' }), note({ x: 157, dur: 1, type: 'eighth' }), note({ x: 206, dur: 1, type: 'eighth' }))
  const chord = (x2, t) => [note({ x: 193, dur: t, type: 'eighth' }), note({ x: x2, dur: t, type: 'eighth', step: 'D', chord: true })]
  const p2 = measure(2, note({ x: 20, dur: 2, type: 'quarter' }), note({ x: 79, dur: 2, type: 'quarter' }), note({ x: 157, dur: 1, type: 'eighth' }), ...chord(204, 1), '<backup><duration>6</duration></backup>', note({ x: 20, dur: 7, type: 'half', voice: 2, dots: 2 }))
  const xml = score([measure(1, time(3)), p1, quarters(3, [20, 79, 157])], [measure(1, time(3)), p2, quarters(3, [20, 79, 157])])
  assert.deepEqual(alignColumns(xml).xml.match(/<part id="P2">[\s\S]*?<measure number="2">[\s\S]*?<\/measure>/)[0], xml.match(/<part id="P2">[\s\S]*?<measure number="2">[\s\S]*?<\/measure>/)[0])
})

test('a rest and two beamed eighths, twice, running past a 2/4 bar: unmarked triplets, even in one part', () => {
  const group = x => [note({ x, dur: 3, type: 'eighth', rest: true }), note({ x: x + 10, dur: 3, type: 'eighth', step: 'D', beam: 'begin' }), note({ x: x + 20, dur: 3, type: 'eighth', step: 'B', beam: 'end' })]
  const xml = score([measure(1, time(2, 6), ...group(10), ...group(60))])
  assert.deepEqual(onsets(xml, 0)[0], [0.5, 1, 2, 2.5]) // as read: 3 quarters in a 2/4 bar
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 0)[0].map(o => +o.toFixed(4)), [0.3333, 0.6667, 1.3333, 1.6667])
  assert.equal((out.match(/<time-modification>/g) ?? []).length, 6)
  assert.equal((out.match(/<tuplet type="start"/g) ?? []).length, 2)
})

test('four beamed eighths with the last read as a quarter: not a triplet, left as read', () => {
  const xml = score([measure(1, time(2, 6), note({ x: 10, dur: 3, type: 'eighth', beam: 'begin' }), note({ x: 30, dur: 3, type: 'eighth', beam: 'continue' }), note({ x: 50, dur: 3, type: 'eighth', beam: 'continue' }), note({ x: 70, dur: 6, type: 'quarter', beam: 'end' }))])
  assert.equal(alignColumns(xml).bars, 0)
})

test('an empty bar written <measure/> keeps the part\'s later bars against the right bars of the others', () => {
  // part 2 rests in bar 2 (written <measure/>) and reads bar 3 too long; part 1's bar 3 (not its bar 2,
  // a whole note) shows where its notes go
  const xml = score(
    [measure(1, time(), quarters(1).replace(/^<measure number="1">|<\/measure>$/g, '')), measure(2, note({ x: 10, dur: 8, type: 'whole' })), quarters(3)],
    [measure(1, time(), quarters(1).replace(/^<measure number="1">|<\/measure>$/g, '')), '<measure number="2" width="300"/>', measure(3, note({ x: 10, dur: 4, type: 'half' }), note({ x: 50, dur: 2, type: 'quarter' }), note({ x: 90, dur: 2, type: 'quarter' }), note({ x: 130, dur: 2, type: 'quarter' }))],
  )
  const { xml: out, bars } = alignColumns(xml)
  assert.equal(bars, 1)
  assert.deepEqual(onsets(out, 2)[1], [0, 1, 2, 3])
  assert.match(out, /<measure number="2" width="300"\/>/)
})
