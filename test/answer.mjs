// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// An answer (test/corpus/README.md) from the MusicXML a page was printed from: every pitched note
// of every part, by bar, with its syllable and onset. For a whole piece, or the bars one page holds.
//   node test/answer.mjs <score.mxl|.musicxml> [options] > <page>.json
//     --bars a-b          only bars a to b (counted in order from 1, whatever the score numbers them)
//     --drop P5,P6        leave out parts the page doesn't print (a hidden rehearsal piano, an empty part)
//     --names Soprano,... the parts' names, in order, where the file's are wrong or blank
//     --title "..."  --source "..."  what the answer says it is, and where the MusicXML came from
import { readFileSync } from 'node:fs'
import { musicXmlText, parseMusicXml } from './score.mjs'

const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

/** The time signature in force at a bar (1-based), from the first part. */
function timeAt(xml, bar) {
  const first = xml.match(/<part\b[\s\S]*?<\/part>/)[0]
  let time = [4, 4]
  for (const [i, m] of [...first.matchAll(/<measure\b[\s\S]*?<\/measure>/g)].entries()) {
    if (i >= bar) break
    const t = m[0].match(/<time\b[^>]*>\s*<beats>(\d+)<\/beats>\s*<beat-type>(\d+)<\/beat-type>/)
    if (t) time = [Number(t[1]), Number(t[2])]
  }
  return time
}

/**
 * The answer for bars from..to (1-based, inclusive; the whole piece by default) of a MusicXML text,
 * with bars_global [from, to] if that's only some of the piece's bars, or if range is set.
 * Throws if the parts have different numbers of bars, or a part to drop isn't there.
 */
export function answerFrom(xml, { from = 1, to, drop = [], names, range = false, ...about } = {}) {
  const all = parseMusicXml(xml)
  const bars = all[0]?.measures.length ?? 0
  if (all.some(p => p.measures.length !== bars)) throw new Error(`parts with different numbers of bars: ${all.map(p => p.measures.length)}`)
  for (const id of drop) if (!all.some(p => p.id === id)) throw new Error(`no part ${id} to drop`)
  to ??= bars
  if (from < 1 || to > bars || from > to) throw new Error(`bars ${from}-${to} of ${bars}`)
  const parts = all.filter(p => !drop.includes(p.id))
  const [beats, beatType] = timeAt(xml, from)
  const answer = {
    page: about.page,
    title: about.title,
    source: about.source,
    ...(about.scan ? { scan: about.scan } : {}),
    ...(range || from !== 1 || to !== bars ? { bars_global: [from, to] } : {}),
    bars: to - from + 1,
    beats,
    beat_type: beatType,
    parts: parts.map((p, i) => {
      const notes = p.measures.slice(from - 1, to).flatMap((m, j) => m.notes.map(x => ({ bar: j + 1, pitch: NAMES[x.midi % 12] + (Math.floor(x.midi / 12) - 1), midi: x.midi, lyric: x.lyric ?? null, onset: Math.round(x.onset * 1e6) / 1e6 })))
      return { id: p.id, name: names?.[i] ?? p.name, note_count: notes.length, notes }
    }),
  }
  answer.total_notes = answer.parts.reduce((s, p) => s + p.note_count, 0)
  answer.total_lyrics = answer.parts.reduce((s, p) => s + p.notes.filter(x => x.lyric).length, 0)
  return answer
}

if (import.meta.main) {
  const [file, ...rest] = process.argv.slice(2)
  if (!file) {
    console.error('usage: node test/answer.mjs <score.mxl|.musicxml> [--bars a-b] [--drop P5,P6] [--names A,B] [--title ..] [--source ..] [--page ..]')
    process.exit(2)
  }
  const options = {}
  for (let i = 0; i < rest.length; i += 2) {
    const [key, value] = [rest[i].replace(/^--/, ''), rest[i + 1]]
    if (key === 'bars') [options.from, options.to] = value.split('-').map(Number)
    else if (key === 'drop' || key === 'names') options[key] = value.split(',')
    else if (['title', 'source', 'page', 'scan'].includes(key)) options[key] = value
    else throw new Error(`unknown option --${key}`)
  }
  process.stdout.write(JSON.stringify(answerFrom(musicXmlText(readFileSync(file)), options), null, 1) + '\n')
}
