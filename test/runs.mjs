// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Runs of test/corpus.mjs (.work/corpus/<run>/), and two reads of a page compared bar by bar, for
// test/compare.mjs and test/prove.mjs.
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { ROOT, joined, reads } from './cases.mjs'
import { bars } from './score.mjs'

export const runDir = run => join(ROOT, '.work', 'corpus', run)

/**
 * Where each case's read is in one or more runs ('a,b,c': the first run that read a case gives
 * it): case name -> its batch folder. A run's batches.json says which batch reads each case; a
 * case counts once its batch has finished (its log.txt is written), so a run cut short holds only
 * the cases it got to.
 */
export function locate(spec) {
  const where = new Map()
  for (const run of spec.split(',')) {
    if (run === '-') continue // none
    const manifest = join(runDir(run), 'batches.json')
    if (!existsSync(manifest)) throw new Error(`no run ${run} (${manifest})`)
    for (const [name, batch] of Object.entries(JSON.parse(readFileSync(manifest, 'utf8')))) {
      const dir = join(runDir(run), `batch-${batch}`)
      if (!where.has(name) && existsSync(join(dir, 'log.txt'))) where.set(name, dir)
    }
  }
  return where
}

/** A case's read in a run (locate's map): the MusicXML joined into one, or null if none. */
export function readOf(where, c) {
  const dir = where.get(c.name)
  const files = dir ? reads(dir, c) : []
  return files.length ? joined(files) : null
}

const INSTRUMENT = /piano|organ|harmonium|keyboard|accomp|harp|guitar|lute|flute|piccolo|traverso|recorder|oboe|clarinet|bassoon|saxophone|horn|trumpet|cornet|trombone|tuba|timpani|triangle|cymbal|drum|cowbell|percussion|violin|viola|cello|contrabass|double bass/i
const VOICE = /sopran|alt|tenor|bass|voice|singstimme|gesang|chant|choir|chorus|solo/i
/** A sung part: one with lyrics or a voice's name, unless it is named for an instrument. */
export const sung = part => !INSTRUMENT.test(part.name ?? '') && (part.notes.some(n => n.lyric) || VOICE.test(part.name ?? ''))

/** A bar's errors: notes missing, found but starting at the wrong time, and extra. */
const errors = r => ({ missing: r.want - r.found, time: r.timed === r.want ? r.found - r.onTime : 0, extra: r.extra })
export const KINDS = ['missing', 'time', 'extra']
const wrong = e => e.missing + e.time + e.extra

export const emptyGroup = () => ({ bars: 0, wrongBefore: 0, wrongAfter: 0, fixed: 0, broken: 0, missing: 0, time: 0, extra: 0 })
export const GROUPS = ['sung', 'accompaniment', 'unpaired']

/**
 * Two reads of one page (MusicXML) against its answer, bar by bar. A bar is one answer part's
 * bar, in the read part paired with it (test/score.mjs, bars()); it is right when every note is
 * there, starting on time, with nothing extra. Returns, for sung parts, accompaniment and read
 * parts paired with no answer part: the bars, how many each read got wrong, fixed and broken,
 * and the change in notes missing, at the wrong time and extra (after minus before); and the
 * bars that changed.
 */
export function compareReads(answer, before, after) {
  const rows = [before, after].map(xml => bars(answer, xml))
  // unpaired read parts' extra notes, a row a bar; answer parts', a row a part and bar
  const key = r => (r.part < 0 ? `-1:${r.bar}` : `${r.part}:${r.bar}`)
  const byKey = rows.map(list => {
    const m = new Map()
    for (const r of list) {
      const was = m.get(key(r))
      m.set(key(r), was ? { ...was, extra: was.extra + r.extra } : r)
    }
    return m
  })
  const groups = Object.fromEntries(GROUPS.map(g => [g, emptyGroup()]))
  const changed = []
  for (const k of new Set([...byKey[0].keys(), ...byKey[1].keys()])) {
    const [a, b] = byKey.map(m => m.get(k))
    const r = a ?? b
    const group = r.part < 0 ? 'unpaired' : sung(answer.parts[r.part]) ? 'sung' : 'accompaniment'
    const none = { want: r.want, timed: r.timed, found: 0, onTime: 0, extra: 0 } // an unpaired part only one read has
    const [ea, eb] = [a, b].map(x => errors(x ?? none))
    const t = groups[group]
    t.bars++
    if (wrong(ea)) t.wrongBefore++
    if (wrong(eb)) t.wrongAfter++
    if (wrong(ea) && !wrong(eb)) t.fixed++
    if (!wrong(ea) && wrong(eb)) t.broken++
    for (const e of KINDS) t[e] += eb[e] - ea[e]
    if (KINDS.some(e => ea[e] !== eb[e])) changed.push({ r, group, ea, eb })
  }
  return { groups, changed }
}
