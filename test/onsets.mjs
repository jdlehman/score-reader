// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Gives an answer's notes their onsets (quarter notes from the start of the bar), from the MusicXML
// the page was drawn from, so the corpus scores rhythm too (test/score.mjs).
//   node test/onsets.mjs <answer.json> <source .musicxml or .mxl> [--write]
// The answer's notes are left as they are: each is paired with the source's note of the same part,
// bar and pitch, in order. The page's first bar may be any measure of the source (a page cut from a
// whole song); the tool finds it. Nothing is written unless every bar's notes are the same in both.
import { readFileSync, writeFileSync } from 'node:fs'
import { musicXmlText, parseMusicXml } from './score.mjs'

const [answerPath, sourcePath, ...flags] = process.argv.slice(2)
const answer = JSON.parse(readFileSync(answerPath, 'utf8'))
const source = parseMusicXml(musicXmlText(readFileSync(sourcePath)))
const bars = answer.bars ?? Math.max(...answer.parts.flatMap(p => p.notes.map(n => n.bar)))
const key = ps => [...ps].sort((a, b) => a - b).join(',')

// the answer's parts with the source's: by id, else in order
const partOf = answer.parts.map((p, i) => source.find(s => s.id === p.id) ?? source[i])

/** How many bars of the answer the source has note for note, if the page starts at measure first. */
function fit(first) {
  let same = 0
  for (let b = 1; b <= bars; b++) {
    const ok = answer.parts.every((p, i) => key(p.notes.filter(n => n.bar === b).map(n => n.midi)) === key(partOf[i]?.measures[first + b - 2]?.notes.map(n => n.midi) ?? []))
    if (ok) same++
  }
  return same
}

const longest = Math.max(...source.map(p => p.measures.length))
let first = 1
let best = -1
for (let f = 1; f + bars - 1 <= longest; f++) {
  const n = fit(f)
  if (n > best) (best = n), (first = f)
}
if (best < bars) {
  console.error(`${answerPath}: only ${best} of ${bars} bars match the source (best from its measure ${first}); left as it is`)
  process.exit(1)
}
for (const [i, p] of answer.parts.entries()) {
  for (let b = 1; b <= bars; b++) {
    const pool = [...(partOf[i].measures[first + b - 2]?.notes ?? [])]
    for (const n of p.notes.filter(n => n.bar === b)) {
      const k = pool.findIndex(s => s.midi === n.midi)
      n.onset = Math.round(pool[k].onset * 1e6) / 1e6
      pool.splice(k, 1)
    }
  }
}
const notes = answer.parts.reduce((s, p) => s + p.notes.length, 0)
console.log(`${answerPath}: ${notes} notes given onsets, from measure ${first} of the source`)
if (flags.includes('--write')) {
  const text = readFileSync(answerPath, 'utf8')
  const indent = text.match(/^\{\n( +)"/)?.[1].length ?? 1
  writeFileSync(answerPath, JSON.stringify(answer, null, indent) + '\n')
}
