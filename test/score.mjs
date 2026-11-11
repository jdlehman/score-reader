// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Scores a read (MusicXML or .mxl) against a page's answer (test/corpus/**/<page>.json: every
// pitched note of every part, by bar number, with its syllable). No dependencies.
//
// What is counted:
// - notes: the answer's notes found in the read, bar by bar (same bar, same pitch), whatever part
//   they landed in. Each read part's measures are lined up with the answer's bars in order, the
//   pairing that finds the most notes (dynamic programming), so a dropped or extra measure costs
//   only itself.
// - extra: notes in the read that the answer doesn't have.
// - inPart: each answer part paired with the read part that holds most of its notes, as a singer
//   would pick "my part" in Sectional; the share of the answer's notes found there. Low when
//   parts are jumbled across systems even if every note was read.
// - parts: how many parts the read has, against the answer.
// - lyrics: the answer's syllables found in order in the paired part.
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

/** Parts of a MusicXML score: { id, name, measures: [{ notes: [{ midi, lyric }] }] } (pitched notes only). */
export function parseMusicXml(xml) {
  const names = new Map()
  for (const m of xml.matchAll(/<score-part\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/score-part>/g)) {
    names.set(m[1], (tag(m[2], 'part-name') ?? '').trim())
  }
  const parts = []
  for (const p of xml.matchAll(/<part\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/part>/g)) {
    const measures = []
    for (const m of p[2].matchAll(/<measure\b[^>]*>([\s\S]*?)<\/measure>/g)) {
      const notes = []
      for (const n of m[1].matchAll(/<note\b[^>]*>([\s\S]*?)<\/note>/g)) {
        const body = n[1]
        if (/<rest\b/.test(body) || /<grace\b/.test(body)) continue
        const pitch = body.match(/<pitch>([\s\S]*?)<\/pitch>/)?.[1]
        if (!pitch) continue
        const step = tag(pitch, 'step')
        const octave = Number(tag(pitch, 'octave'))
        const alter = Number(tag(pitch, 'alter') ?? 0)
        if (!(step in STEPS) || !Number.isFinite(octave)) continue
        // a tied-on note is the same note held: the answer counts it as a note too
        const lyric = body.match(/<lyric\b[^>]*>[\s\S]*?<text>([^<]*)<\/text>/)?.[1]
        notes.push({ midi: 12 * (octave + 1) + STEPS[step] + Math.round(alter), lyric })
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

/**
 * Lines up a read part's measures with the answer's bars, in order, finding the most notes:
 * returns, for each read measure, the answer bar it stands for (or none), and the notes found.
 */
function align(bars, part, count) {
  const numbers = Array.from({ length: count }, (_, i) => i + 1)
  const m = part.measures.length
  const n = numbers.length
  // best[i][j]: most notes found pairing the first i measures with the first j bars
  const best = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    const pitches = part.measures[i - 1].notes.map(x => x.midi)
    for (let j = 1; j <= n; j++) {
      const pair = best[i - 1][j - 1] + common(bars.get(numbers[j - 1]) ?? [], pitches)
      best[i][j] = Math.max(pair, best[i - 1][j], best[i][j - 1])
    }
  }
  const barOf = new Array(m).fill(null)
  for (let i = m, j = n; i > 0 && j > 0;) {
    const pitches = part.measures[i - 1].notes.map(x => x.midi)
    if (best[i][j] === best[i - 1][j - 1] + common(bars.get(numbers[j - 1]) ?? [], pitches) && best[i][j] > best[i - 1][j] && best[i][j] > best[i][j - 1]) {
      barOf[i - 1] = numbers[j - 1]
      i--, j--
    } else if (best[i][j] === best[i - 1][j]) i--
    else j--
  }
  return { barOf, found: best[m][n] }
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
  const total = answer.parts.reduce((s, p) => s + p.notes.length, 0)
  const readTotal = parts.reduce((s, p) => s + p.measures.reduce((t, m) => t + m.notes.length, 0), 0)
  const count = answer.bars ?? Math.max(...answer.parts.flatMap(p => p.notes.map(n => n.bar)))
  // all parts together: each read part lined up with all the answer's notes, then every read
  // note pooled under the bar its measure stands for
  const allBars = answerBars(answer.parts.flatMap(p => p.notes))
  const pooled = new Map()
  for (const rp of parts) {
    const { barOf } = align(allBars, rp, count)
    rp.measures.forEach((m, i) => {
      if (barOf[i] != null) pooled.set(barOf[i], [...(pooled.get(barOf[i]) ?? []), ...m.notes.map(x => x.midi)])
    })
  }
  let notes = 0
  for (const [bar, pitches] of allBars) notes += common(pitches, pooled.get(bar) ?? [])
  // each answer part with the read part that holds most of its notes
  let inPart = 0
  let lyricsTotal = 0
  let lyricsFound = 0
  for (const ap of answer.parts) {
    const bars = answerBars(ap.notes)
    let pick = null
    let pickN = -1
    for (const rp of parts) {
      const { found } = align(bars, rp, count)
      if (found > pickN) [pick, pickN] = [rp, found]
    }
    inPart += Math.max(0, pickN)
    const want = ap.notes.map(n => syllable(n.lyric)).filter(Boolean)
    lyricsTotal += want.length
    if (pick && want.length) {
      const got = pick.measures.flatMap(m => m.notes.map(n => syllable(n.lyric))).filter(Boolean)
      lyricsFound += lcs(want, got)
    }
  }
  // a note found in its own part is found: the two line-ups are worked out apart, and can differ
  notes = Math.max(notes, inPart)
  return {
    notes: total ? notes / total : 1,
    extra: readTotal - notes,
    inPart: total ? inPart / total : 1,
    parts: parts.length,
    answerParts: answer.parts.length,
    lyrics: lyricsTotal ? lyricsFound / lyricsTotal : null,
    measures: parts[0]?.measures.length ?? 0,
    answerBars: count,
  }
}
