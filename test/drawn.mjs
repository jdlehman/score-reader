// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A read as Verovio takes it. Verovio draws the score after a read (app/check.js) and in
// Sectional, and Sectional plays by its timings, so a read it imports wrongly is wrong for the
// person using it however well the MusicXML scores. Per bar (all parts together): whether
// Verovio keeps every note, and how many of the MusicXML's note times it puts elsewhere.
import createModule from 'verovio/wasm'
import { LOG_OFF, VerovioToolkit, enableLog } from 'verovio/esm'
import { MEASURE } from './score.mjs'

let toolkit = null

/**
 * The bars of a MusicXML read as Verovio draws them: [{ notes, drawn, times, moved }], notes
 * being the MusicXML's (rests left out, grace notes in) and drawn Verovio's; times, how many
 * distinct note times the MusicXML gives the bar, and moved, how many of those Verovio's timemap
 * doesn't have. Null if Verovio can't load it, or makes another number of bars of it.
 */
export async function drawnBars(xml) {
  if (!toolkit) {
    const module = await createModule()
    enableLog(LOG_OFF, module)
    toolkit = new VerovioToolkit(module)
  }
  if (!toolkit.loadData(xml)) return null
  const mei = toolkit.getMEI()
  const drawn = [...mei.matchAll(MEASURE)].map(m => (m[0].match(/<note\b/g) ?? []).length)
  const timemap = toolkit.renderToTimemap({ includeMeasures: true, includeRests: false })
  const starts = timemap.filter(e => e.measureOn).map(e => e.qstamp)
  const heard = new Set(timemap.filter(e => e.on?.length).map(e => Math.round(e.qstamp * 96)))
  const bars = musicXmlBars(xml)
  if (bars.length !== drawn.length || bars.length !== starts.length) return null
  return bars.map((b, i) => {
    const times = [...new Set(b.onsets.map(o => Math.round((starts[i] + o) * 96)))]
    return { notes: b.notes, drawn: drawn[i], times: times.length, moved: times.filter(t => !heard.has(t)).length }
  })
}

/**
 * Two reads of a page as Verovio draws them: bars it draws in full in each, and, in the bars it
 * draws in full in both, the note times it puts elsewhere in each. Null if either won't compare.
 */
export async function compareDrawn(before, after) {
  const [a, b] = [await drawnBars(before), await drawnBars(after)]
  if (!a || !b || a.length !== b.length) return null
  const full = x => x.notes === x.drawn
  const both = a.map((x, i) => full(x) && full(b[i]))
  return {
    full: [a.filter(full).length, b.filter(full).length],
    moved: [a.reduce((s, x, i) => s + (both[i] ? x.moved : 0), 0), b.reduce((s, x, i) => s + (both[i] ? x.moved : 0), 0)],
  }
}

/** Each bar of a MusicXML read, all parts together: its notes (no rests; grace notes too) and their onsets in quarter notes. */
function musicXmlBars(xml) {
  const tag = (s, name) => s.match(new RegExp(`<${name}\\b[^>]*>([^<]*)</${name}>`))?.[1]
  const bars = []
  for (const p of xml.matchAll(/<part(?:\s[^>]*)?>([\s\S]*?)<\/part>/g)) {
    let divisions = 1
    let i = 0
    for (const m of p[1].matchAll(MEASURE)) {
      const bar = (bars[i++] ??= { notes: 0, onsets: [] })
      let at = 0
      let last = 0
      for (const e of (m[1] ?? '').matchAll(/<(note|backup|forward|attributes)\b[^>]*>([\s\S]*?)<\/\1>/g)) {
        const [, kind, body] = e
        const duration = Number(tag(body, 'duration') ?? 0) || 0
        if (kind === 'attributes') divisions = Number(tag(body, 'divisions')) || divisions
        else if (kind === 'backup') at -= duration
        else if (kind === 'forward') at += duration
        else {
          const grace = /<grace\b/.test(body)
          const chord = /<chord\s*\/>/.test(body)
          const onset = grace ? at : chord ? last : at
          if (!grace && !chord) at += duration
          if (!grace) last = onset
          if (/<rest\b/.test(body)) continue
          bar.notes++
          if (!grace) bar.onsets.push(onset / divisions)
        }
      }
    }
  }
  return bars
}
