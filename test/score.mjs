// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Scores a read (MusicXML or .mxl) against a page's answer (test/corpus/**/<page>.json: every
// pitched note of every part, by bar number, with its syllable). No dependencies.
//
// What is counted:
// - notes: the answer's notes found in the read, bar by bar (same bar, same pitch), whatever part
//   they landed in. The read's measures are lined up with the answer's bars in order, all parts
//   together (measure i is the same moment in every part, as a player reads it), the pairing
//   that finds the most notes (dynamic programming): a dropped or extra measure costs only
//   itself, but a part out of step with the others costs its notes.
// - precision: the share of the read's notes that are in the answer; extra: how many are not.
//   Notes padded in, or measures read twice, cost here.
// - inPart: each answer part paired with a read part of its own (the pairing that finds the most
//   notes), as a singer would pick "my part" in Sectional; the share of the answer's notes found
//   there. Low when parts are jumbled across systems, or two parts were read as one.
// - parts: how many parts the read has, against the answer.
// - lyrics: the answer's syllables found in order in the paired part.
// - rhythm: the answer's notes found in the right bar and starting at the right time in it (in
//   quarter notes from the bar's start), whatever part they landed in; for answers whose notes
//   have onsets. A note found at the wrong beat counts in notes but not here. Pitch alone is weak
//   evidence (another chorale's read scores 30-65% of notes against a chorale); this is stronger.
// Not counted: how long notes are held.
import { inflateRawSync } from 'node:zlib'

const STEPS = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }

/** The MusicXML text of an .mxl (a zip) or of plain MusicXML bytes. */
export function musicXmlText(bytes) {
  const buf = Buffer.from(bytes)
  if (buf.readUInt32LE(0) !== 0x04034b50) return buf.toString('utf8')
  // the end of central directory record, then each entry
  let end = buf.length - 22
  while (end >= 0 && buf.readUInt32LE(end) !== 0x06054b50) end--
  if (end < 0) throw new Error('not a zip file')
  const count = buf.readUInt16LE(end + 10)
  let at = buf.readUInt32LE(end + 16)
  const entries = new Map()
  for (let i = 0; i < count; i++) {
    const method = buf.readUInt16LE(at + 10)
    const size = buf.readUInt32LE(at + 20)
    const nameLength = buf.readUInt16LE(at + 28)
    const extraLength = buf.readUInt16LE(at + 30)
    const commentLength = buf.readUInt16LE(at + 32)
    const local = buf.readUInt32LE(at + 42)
    const name = buf.toString('utf8', at + 46, at + 46 + nameLength)
    const start = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28)
    const data = buf.subarray(start, start + size)
    entries.set(name, () => (method === 8 ? inflateRawSync(data) : data).toString('utf8'))
    at += 46 + nameLength + extraLength + commentLength
  }
  const container = entries.get('META-INF/container.xml')?.()
  const root = container?.match(/full-path="([^"]+)"/)?.[1]
  const pick = root ?? [...entries.keys()].find(n => !n.startsWith('META-INF/') && /\.(xml|musicxml)$/.test(n))
  if (!pick || !entries.has(pick)) throw new Error('no MusicXML in the .mxl')
  return entries.get(pick)()
}

const tag = (xml, name) => xml.match(new RegExp(`<${name}\\b[^>]*>([^<]*)</${name}>`))?.[1]

/**
 * Parts of a MusicXML score: { id, name, measures: [{ notes: [{ midi, lyric, onset }] }] }, pitched
 * notes only. onset: where the note starts, in quarter notes from the start of its measure.
 */
export function parseMusicXml(xml) {
  const names = new Map()
  for (const m of xml.matchAll(/<score-part\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/score-part>/g)) {
    names.set(m[1], (tag(m[2], 'part-name') ?? '').trim())
  }
  const parts = []
  for (const p of xml.matchAll(/<part\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/part>/g)) {
    const measures = []
    let divisions = 1 // per quarter note; set by <attributes>, kept from measure to measure
    for (const m of p[2].matchAll(/<measure\b[^>]*>([\s\S]*?)<\/measure>/g)) {
      const notes = []
      let at = 0 // where the next note starts, in divisions
      let last = 0 // where the last note started: a <chord/> note starts there too
      for (const e of m[1].matchAll(/<(note|backup|forward|attributes)\b[^>]*>([\s\S]*?)<\/\1>/g)) {
        const [, kind, body] = e
        const duration = Number(tag(body, 'duration') ?? 0) || 0
        if (kind === 'attributes') divisions = Number(tag(body, 'divisions')) || divisions
        else if (kind === 'backup') at -= duration
        else if (kind === 'forward') at += duration
        else if (/<grace\b/.test(body)) continue // takes no time, and isn't counted
        else {
          const chord = /<chord\s*\/>/.test(body)
          const onset = chord ? last : at
          if (!chord) at += duration
          last = onset
          if (/<rest\b/.test(body)) continue
          const pitch = body.match(/<pitch>([\s\S]*?)<\/pitch>/)?.[1]
          if (!pitch) continue
          const step = tag(pitch, 'step')
          const octave = Number(tag(pitch, 'octave'))
          const alter = Number(tag(pitch, 'alter') ?? 0)
          if (!(step in STEPS) || !Number.isFinite(octave)) continue
          // a tied-on note is the same note held: the answer counts it as a note too
          const lyric = body.match(/<lyric\b[^>]*>[\s\S]*?<text>([^<]*)<\/text>/)?.[1]
          notes.push({ midi: 12 * (octave + 1) + STEPS[step] + Math.round(alter), lyric, onset: onset / divisions })
        }
      }
      measures.push({ notes })
    }
    parts.push({ id: p[1], name: names.get(p[1]) ?? '', measures })
  }
  return parts
}

/** How many of a's items b has, each used once. */
function common(a, b) {
  const pool = new Map()
  for (const x of b) pool.set(x, (pool.get(x) ?? 0) + 1)
  let n = 0
  for (const x of a) {
    const left = pool.get(x)
    if (left) {
      n++
      pool.set(x, left - 1)
    }
  }
  return n
}

/** Pitches by bar number of some answer notes. */
const answerBars = notes => {
  const bars = new Map()
  for (const n of notes) bars.set(n.bar, [...(bars.get(n.bar) ?? []), n.midi])
  return bars
}

/** Pitch-and-onset keys by bar number of some answer notes. */
const timedBars = notes => {
  const bars = new Map()
  for (const n of notes) bars.set(n.bar, [...(bars.get(n.bar) ?? []), timed(n)])
  return bars
}

/** A note as pitch and onset, for rhythm: onsets to a 96th of a quarter (triplets, 32nds). */
const timed = n => `${n.midi}@${Math.round(n.onset * 96)}`

/**
 * Lines up the read's measures with the answer's bars, in order, finding the most notes (all
 * parts together: measure i is the same moment in every part, as a player reads it). Returns, for
 * each answer bar, the read measure index that stands for it (or none).
 */
function align(bars, stacks, count) {
  const m = stacks.length
  const n = count
  const gain = (i, j) => common(bars.get(j) ?? [], stacks[i - 1])
  // best[i][j]: most notes found pairing the first i measures with the first j bars
  const best = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) best[i][j] = Math.max(best[i - 1][j - 1] + gain(i, j), best[i - 1][j], best[i][j - 1])
  }
  const measureOf = new Map()
  for (let i = m, j = n; i > 0 && j > 0;) {
    if (best[i][j] === best[i - 1][j - 1] + gain(i, j) && best[i][j] > best[i - 1][j] && best[i][j] > best[i][j - 1]) {
      measureOf.set(j, i - 1)
      i--, j--
    } else if (best[i][j] === best[i - 1][j]) i--
    else j--
  }
  return measureOf
}

/**
 * Pairs answer parts with read parts, each read part with one answer part at most, for the most
 * notes in all: gain[a][r] is how many of answer part a's notes read part r holds. Returns, for
 * each answer part, its read part's index or -1.
 */
function assign(gain) {
  const a = gain.length
  const r = gain[0]?.length ?? 0
  if (a > 12) {
    // too many to try every pairing: greedy, the biggest first
    const pairs = gain.flatMap((row, i) => row.map((g, j) => [g, i, j])).sort((x, y) => y[0] - x[0])
    const of = new Array(a).fill(-1)
    const taken = new Set()
    for (const [, i, j] of pairs) if (of[i] < 0 && !taken.has(j)) (of[i] = j), taken.add(j)
    return of
  }
  // best[mask]: most notes with the answer parts in mask paired, read parts taken in order
  let best = new Map([[0, { total: 0, of: new Array(a).fill(-1) }]])
  for (let j = 0; j < r; j++) {
    const next = new Map(best)
    for (const [mask, s] of best) {
      for (let i = 0; i < a; i++) {
        if (mask & (1 << i)) continue
        const total = s.total + gain[i][j]
        const key = mask | (1 << i)
        if (!next.has(key) || next.get(key).total < total) next.set(key, { total, of: s.of.map((x, k) => (k === i ? j : x)) })
      }
    }
    best = next
  }
  return [...best.values()].reduce((x, y) => (y.total > x.total ? y : x)).of
}

const syllable = s => (s ?? '').toLowerCase().normalize('NFC').replace(/[^\p{L}\p{N}]/gu, '')

/** Longest common subsequence length of two lists. */
function lcs(a, b) {
  let prev = new Array(b.length + 1).fill(0)
  for (const x of a) {
    const row = [0]
    for (let j = 0; j < b.length; j++) row.push(x === b[j] ? prev[j] + 1 : Math.max(prev[j + 1], row[j]))
    prev = row
  }
  return prev[b.length]
}

/** Scores one read against one answer. */
export function score(answer, readXml) {
  const parts = parseMusicXml(readXml)
  // pitched notes only: an unpitched (drum) note has no pitch to find
  answer = { ...answer, parts: answer.parts.map(p => ({ ...p, notes: p.notes.filter(n => Number.isFinite(n.midi)) })) }
  const total = answer.parts.reduce((s, p) => s + p.notes.length, 0)
  const readTotal = parts.reduce((s, p) => s + p.measures.reduce((t, m) => t + m.notes.length, 0), 0)
  if (!total) {
    // nothing pitched to score (a drum page): only whether it was read, and its parts
    return { notes: null, precision: null, extra: readTotal, inPart: null, rhythm: null, parts: parts.length, answerParts: answer.parts.length, lyrics: null }
  }
  const count = answer.bars ?? Math.max(...answer.parts.flatMap(p => p.notes.map(n => n.bar)))
  // one line-up for the whole read: measure i of every part stands for the same answer bar
  const pitches = (rp, i) => (i == null ? [] : (rp.measures[i]?.notes ?? []).map(x => x.midi))
  const stacks = Array.from({ length: Math.max(0, ...parts.map(p => p.measures.length)) }, (_, i) => parts.flatMap(rp => pitches(rp, i)))
  const allBars = answerBars(answer.parts.flatMap(p => p.notes))
  const measureOf = align(allBars, stacks, count)
  let notes = 0
  for (const [bar, want] of allBars) notes += common(want, stacks[measureOf.get(bar)] ?? [])
  // rhythm: the same, but each note must start where the answer's does (answers with onsets only)
  const onTime = answer.parts.flatMap(p => p.notes.filter(n => Number.isFinite(n.onset)))
  let rhythm = 0
  for (const [bar, want] of timedBars(onTime)) {
    const i = measureOf.get(bar)
    if (i != null) rhythm += common(want, parts.flatMap(rp => (rp.measures[i]?.notes ?? []).map(timed)))
  }
  // each answer part with a read part of its own: the pairing that finds the most notes
  const gain = answer.parts.map(ap => {
    const bars = answerBars(ap.notes)
    return parts.map(rp => [...bars].reduce((s, [bar, want]) => s + common(want, pitches(rp, measureOf.get(bar))), 0))
  })
  const of = assign(gain)
  let inPart = 0
  let lyricsTotal = 0
  let lyricsFound = 0
  answer.parts.forEach((ap, a) => {
    const pick = parts[of[a]]
    if (pick) inPart += gain[a][of[a]]
    const want = ap.notes.map(n => syllable(n.lyric)).filter(Boolean)
    lyricsTotal += want.length
    if (pick && want.length) {
      const got = pick.measures.flatMap(m => m.notes.map(n => syllable(n.lyric))).filter(Boolean)
      lyricsFound += lcs(want, got)
    }
  })
  return {
    notes: total ? notes / total : 1,
    precision: readTotal ? notes / readTotal : total ? 0 : 1,
    extra: readTotal - notes,
    inPart: total ? inPart / total : 1,
    rhythm: onTime.length ? rhythm / onTime.length : null,
    parts: parts.length,
    answerParts: answer.parts.length,
    lyrics: lyricsTotal ? lyricsFound / lyricsTotal : null,
    measures: stacks.length,
    answerBars: count,
  }
}
