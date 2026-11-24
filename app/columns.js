// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Notes in the same column of a system start at the same time. Audiveris works out each part's
// bar on its own, so a beam, flag or dot it misses, or a triplet the engraving left unmarked, puts
// the rest of that part's bar at the wrong times, while the other parts' bars in the same system
// show where those notes belong.
//
// alignColumns re-times, in the MusicXML of a read, each voice of a part's bar that doesn't add up
// to the bar's length (longer, or shorter inside the piece), by the bars of the other parts in the
// same system that do: a note takes the time of the chords in its column (default-x within COLUMN
// tenths). The notes between two such notes follow the one before, stay, or follow the one after,
// whichever lets every length be written with one value; failing that, a run of equal notes is
// spread evenly (a triplet). Lengths are written again to match, triplets with the marks Verovio
// needs to time them. A voice it can't re-time so stays as read.
//
// A bar's length is its time signature's. Where the read has none (a page from the middle of a
// piece), it is the length most of the page's bars have, if that is the length of a common time
// signature: a page whose bars mostly came out at three and a half beats has no length to trust.
// No DOM: readScore (teavm.js) runs it in the page's worker and in Node alike.

/** Tenths (MusicXML default-x) two note heads may be apart and still stand in one column. */
const COLUMN = 2
/** Bar lengths, in quarter notes, of common time signatures: 3/8, 2/4, 3/4, 4/4, 9/8, 5/4, 6/4, 4/2. */
const STANDARD = [1.5, 2, 3, 4, 4.5, 5, 6, 8]
/** Written values, in quarter notes, longest first. */
const VALUES = [['breve', 8], ['whole', 4], ['half', 2], ['quarter', 1], ['eighth', 0.5], ['16th', 0.25], ['32nd', 0.125], ['64th', 0.0625]]
const EPS = 1e-6
let skip = () => {} // counts why a voice was re-timed or left as read, for alignColumns's caller
let finer = new Map() // part index -> how many times finer its divisions must count for the new lengths
const near = (a, b) => Math.abs(a - b) < EPS
const gcd = (a, b) => (b ? gcd(b, a % b) : a)
const lcm = (a, b) => (a * b) / gcd(a, b)
const tag = (s, name) => s.match(new RegExp(`<${name}\\b[^>]*>([^<]*)</${name}>`))?.[1]

/**
 * Re-times the bars of a MusicXML score that don't add up, by their columns in the other parts.
 * Returns the MusicXML (the same text if nothing changed) and how many part-bars were re-timed.
 * why, if given, counts each voice of a broken bar by what happened to it (for tuning).
 */
export function alignColumns(xml, why = null, scaled = false) {
  const reasons = {}
  skip = reason => (reasons[reason] = (reasons[reason] ?? 0) + 1)
  const parts = parseParts(xml)
  if (parts.length < 2) return { xml, bars: 0 }
  finer = new Map()
  const usual = usualLength(parts)
  for (const p of parts) for (const m of p.measures) m.length = m.timeLength ?? usual
  const replace = [] // [start, end, text] of measures' inner text, in document order
  const count = Math.max(...parts.map(p => p.measures.length))
  for (let i = 0; i < count; i++) {
    const here = parts.map((p, pi) => ({ p, pi, m: p.measures[i], last: i === p.measures.length - 1 })).filter(x => x.m)
    const state = here.map(x => ({ ...x, fits: fits(x.m, i === 0 || x.last) }))
    const trusted = state.filter(s => s.fits === true).flatMap(s => chords(s.m)).filter(c => Number.isFinite(c.x))
    if (!trusted.length) continue
    for (const s of state) {
      if (s.fits !== false) continue
      const text = retime(s.m, trusted)
      if (text != null) replace.push([s.m.innerStart, s.m.innerEnd, text])
    }
  }
  if (finer.size && !scaled) {
    // a part whose new lengths its divisions can't count (thirds of a beat, say): count finer, and again
    let out = ''
    let at = 0
    for (const [pi, f] of [...finer].sort((a, b) => a[0] - b[0])) {
      const p = parts[pi]
      out += xml.slice(at, p.start) + xml.slice(p.start, p.end).replace(/<(duration|divisions|offset)>(-?\d+)<\/\1>/g, (_, t, n) => `<${t}>${Number(n) * f}</${t}>`)
      at = p.end
    }
    return alignColumns(out + xml.slice(at), why, true)
  }
  if (why) for (const [k, v] of Object.entries(reasons)) why[k] = (why[k] ?? 0) + v
  if (!replace.length) return { xml, bars: 0 }
  let out = ''
  let at = 0
  for (const [start, end, text] of replace.sort((a, b) => a[0] - b[0])) {
    out += xml.slice(at, start) + text
    at = end
  }
  return { xml: out + xml.slice(at), bars: replace.length }
}

/**
 * The parts of a score: their measures, each with its inner text's place in the document, its
 * time signature's length (quarter notes) if one was given by then, its divisions, and its events
 * in order (notes and rests with their times, backups, forwards), times in divisions.
 */
function parseParts(xml) {
  const parts = []
  for (const p of xml.matchAll(/(<part(?:\s[^>]*)?>)([\s\S]*?)<\/part>/g)) {
    const partStart = p.index + p[1].length
    let divisions = 1
    let timeLength = null
    const measures = []
    for (const m of p[2].matchAll(/(<measure(?:\s[^>]*)?>)([\s\S]*?)<\/measure>/g)) {
      const innerStart = partStart + m.index + m[1].length
      const inner = m[2]
      const events = []
      let at = 0
      let last = 0
      for (const e of inner.matchAll(/<(note|backup|forward|attributes)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
        const [whole, kind, attrs, body] = e
        if (kind === 'attributes') {
          const d = Number(tag(body, 'divisions'))
          if (d && events.some(x => x.kind !== 'attributes')) return [] // divisions changed inside a bar: leave the score alone
          if (d) divisions = d
          if (/<time\b/.test(body)) {
            const beats = Number(tag(body, 'beats'))
            const type = Number(tag(body, 'beat-type'))
            timeLength = beats && type ? (beats * 4) / type : null
          }
          events.push({ kind })
          continue
        }
        const duration = Number(tag(body, 'duration') ?? 0) || 0
        const ev = { kind, start: e.index, end: e.index + whole.length, text: whole, duration }
        if (kind === 'backup') at -= duration
        else if (kind === 'forward') {
          ev.time = at
          at += duration
        } else {
          ev.grace = /<grace\b/.test(body)
          ev.chord = /<chord\s*\/>/.test(body)
          ev.rest = /<rest\b/.test(body)
          ev.measureRest = /<rest\b[^>]*measure="yes"/.test(body)
          ev.voice = tag(body, 'voice') ?? '1'
          ev.x = Number(attrs.match(/default-x="(-?[\d.]+)"/)?.[1])
          ev.type = tag(body, 'type')
          ev.stem = tag(body, 'stem')
          ev.dots = (body.match(/<dot\b/g) ?? []).length
          const tm = body.match(/<time-modification>[\s\S]*?<actual-notes>(\d+)<\/actual-notes>[\s\S]*?<normal-notes>(\d+)<\/normal-notes>/)
          ev.tm = tm ? { actual: Number(tm[1]), normal: Number(tm[2]) } : null
          if (ev.grace) ev.time = at
          else {
            ev.time = ev.chord ? last : at
            if (!ev.chord) at += duration
            last = ev.time
          }
          ev.quarters = ev.time / divisions // where it starts, in quarter notes
        }
        events.push(ev)
      }
      measures.push({ innerStart, innerEnd: innerStart + inner.length, inner, events, divisions, timeLength })
    }
    parts.push({ measures, start: partStart, end: partStart + p[2].length })
  }
  parts.forEach((p, pi) => p.measures.forEach(m => (m.part = pi)))
  return parts
}

/**
 * The column of a chord: where its heads on the stem's usual side stand (default-x). A second in a
 * chord puts one head on the other side of the stem, a head's width off the column: to the right
 * of an up stem, to the left of a down one.
 */
function columnOf(notes) {
  const xs = notes.map(e => e.x).filter(Number.isFinite)
  if (!xs.length) return NaN
  return notes[0].stem === 'down' ? Math.max(...xs) : Math.min(...xs)
}

/** A measure's chords (and single notes) that take time: { x: their column, quarters: when they start }. Rests aren't columns. */
function chords(m) {
  const out = []
  for (const e of m.events) {
    if (e.kind !== 'note' || e.grace) continue
    if (e.chord && out.length) out[out.length - 1].notes.push(e)
    else out.push({ notes: [e], quarters: e.quarters })
  }
  return out.filter(c => !c.notes[0].rest).map(c => ({ x: columnOf(c.notes), quarters: c.quarters }))
}

/** Each run of a measure: the events between two backups (a voice, as Audiveris writes them), with where it starts and ends (divisions). */
function runs(m) {
  const out = []
  let run = null
  let at = 0
  for (const e of m.events) {
    if (e.kind === 'attributes') continue
    if (e.kind === 'backup') {
      if (run) {
        run.end = at
        run.backup = e
        out.push(run)
        run = null
      }
      at -= e.duration
      continue
    }
    if (!run) run = { start: at, events: [] }
    run.events.push(e)
    if (e.kind === 'forward') at += e.duration
    else if (e.kind === 'note' && !e.grace && !e.chord) at += e.duration
  }
  if (run) {
    run.end = at
    out.push(run)
  }
  return out
}

/** The length most of the score's inner bars with notes have, if it is a common time signature's (quarter notes), else null. */
function usualLength(parts) {
  const counts = new Map()
  for (const p of parts) {
    p.measures.forEach((m, i) => {
      if (i === 0 || i === p.measures.length - 1 || !m.events.some(e => e.kind === 'note' && !e.rest)) return
      const end = Math.max(...runs(m).map(r => r.end)) / m.divisions
      const k = Math.round(end * 960)
      counts.set(k, (counts.get(k) ?? 0) + 1)
    })
  }
  const top = [...counts].sort((a, b) => b[1] - a[1])[0]
  return top && top[1] >= 3 && STANDARD.some(l => near(l, top[0] / 960)) ? top[0] / 960 : null
}

/** Whether a part's bar adds up to its length: true, false (longer, or shorter inside the piece), or null (no length, or nothing timed). */
function fits(m, edge) {
  if (m.length == null || !m.events.some(e => e.kind === 'note' && !e.grace && !e.measureRest)) return null
  const ends = runs(m).map(r => r.end / m.divisions)
  if (ends.some(e => e > m.length + EPS)) return false
  if (!edge && Math.max(...ends) < m.length - EPS) return false
  return true
}

/** The written value of a length in quarter notes: the note's own if it is that long, else plain, dotted, double-dotted, then triplet; or null. */
function written(q, own) {
  if (own?.type && near(valueOf(own), q)) return own
  for (const tm of [null, { actual: 3, normal: 2 }]) {
    for (const dots of [0, 1, 2]) {
      for (const [type] of VALUES) {
        const w = { type, dots, tm }
        if (near(valueOf(w), q)) return w
      }
    }
  }
  return null
}
const valueOf = w => {
  const v = VALUES.find(([t]) => t === w.type)?.[1]
  return v == null ? NaN : v * (2 - 0.5 ** w.dots) * (w.tm ? w.tm.normal / w.tm.actual : 1)
}
const sameValue = (a, b) => a.type === b.type && a.dots === b.dots && (a.tm?.actual ?? 0) === (b.tm?.actual ?? 0) && (a.tm?.normal ?? 0) === (b.tm?.normal ?? 0)

/**
 * A broken part's bar, re-timed by the trusted columns: its new inner text, or null if no voice
 * could be re-timed. A voice re-timed fits the bar; the others stay as read.
 */
function retime(m, trusted) {
  const edits = [] // [start, end, text] within the measure's inner text
  for (const run of runs(m)) {
    const plan = planRun(run, m, trusted)
    if (plan) edits.push(...plan)
  }
  if (!edits.length) return null
  let text = ''
  let at = 0
  for (const [start, end, t] of edits.sort((a, b) => a[0] - b[0] || a[1] - b[1])) {
    text += m.inner.slice(at, start) + t
    at = end
  }
  text += m.inner.slice(at)
  // the bar as written now: each voice starts where it did, and none got longer past the bar
  const again = parseParts(`<part>${'<measure>'}${text}</measure></part>`)[0]?.measures[0]
  if (!again) return null
  const before = runs(m)
  const after = runs(again)
  if (before.length !== after.length) return null
  for (let k = 0; k < before.length; k++) {
    if (before[k].start !== after[k].start) return null
    if (after[k].end > Math.max(before[k].end, m.length * m.divisions) + EPS) return null
  }
  return text
}

/** The edits that re-time one run (voice) of a broken bar, or null if it can't be re-timed. */
function planRun(run, m, trusted) {
  const notes = run.events.filter(e => e.kind === 'note')
  if (!notes.length || notes.some(e => e.measureRest)) return null
  if (new Set(notes.map(e => e.voice)).size > 1) return skip('voices mixed in one run'), null
  // slots: a note or rest that takes time, with the chord notes that sound with it
  const slots = []
  let lead = null // a forward before the first slot: the voice comes in later
  for (const e of run.events) {
    if (e.kind === 'forward') {
      if (slots.length) return skip('gap inside the voice'), null
      lead = e
    } else if (e.grace) continue
    else if (e.chord && slots.length) slots[slots.length - 1].notes.push(e)
    else slots.push({ notes: [e], time: e.time, duration: e.duration })
  }
  if (!slots.length) return null
  const d = m.divisions
  // each slot's time from its column: the one time all trusted chords in that column have
  for (const s of slots) {
    const x = columnOf(s.notes)
    const times = new Set()
    if (Number.isFinite(x)) for (const t of trusted) if (Math.abs(t.x - x) <= COLUMN) times.add(Math.round(t.quarters * 960))
    s.anchor = times.size === 1 ? [...times][0] / 960 : null
  }
  // anchors must run forward, inside the bar
  let lastAnchor = -Infinity
  for (const s of slots) {
    if (s.anchor == null) continue
    if (s.anchor <= lastAnchor + EPS || s.anchor < run.start / d - EPS || s.anchor >= m.length - EPS) s.anchor = null
    else lastAnchor = s.anchor
  }
  if (!slots.some(s => s.anchor != null && !near(s.anchor, s.time / d))) return null // nothing moves
  const starts = placeBetween(slots, run, m)
  if (!starts) return skip('no order between the anchors'), null
  const fails = []
  const plan = writePlan(slots, starts, run, m, lead, fails)
  if (plan) return skip('retimed'), plan
  skip(fails[0])
  return null
}

/**
 * New times for a run's slots: anchored ones at their column's time, and each stretch of others
 * moved with the anchor before it, left where it was, or moved with the anchor after it: the first
 * of these that keeps the stretch in order between its anchors, with every length in it one value
 * can write. Failing those, a stretch of notes as long as each other and as the anchored note
 * before them is spread evenly up to the next anchor (or the bar's end, if the voice reached it):
 * three eighths read in the time of two are a triplet the engraving left unmarked. Null if a
 * stretch has no place.
 */
function placeBetween(slots, run, m) {
  const d = m.divisions
  const old = slots.map(s => s.time / d)
  const starts = slots.map(s => s.anchor)
  const writable = q => q > EPS && written(q) != null
  for (let i = 0; i < slots.length;) {
    if (starts[i] != null) {
      i++
      continue
    }
    let j = i
    while (j < slots.length && starts[j] == null) j++
    const from = i > 0 ? starts[i - 1] : null
    const to = j < slots.length ? starts[j] : null
    const shifts = [i > 0 ? from - old[i - 1] : null, 0, to != null ? to - old[j] : null].filter(x => x != null)
    let placed = false
    for (const shift of shifts) {
      const t = old.slice(i, j).map(o => o + shift)
      if (from == null && t[0] < run.start / d - EPS) continue
      if (to == null && t[t.length - 1] >= m.length - EPS) continue
      const seq = [...(from != null ? [from] : []), ...t, ...(to != null ? [to] : [])]
      if (seq.every((v, k) => k === 0 || writable(v - seq[k - 1]))) {
        t.forEach((v, n) => (starts[i + n] = v))
        placed = true
        break
      }
    }
    if (!placed) {
      // spread evenly: the anchored note before (if any) and the stretch share the time to the next anchor
      const first = i > 0 ? i - 1 : i
      const a = i > 0 ? from : run.start / d
      const b = to ?? (run.end / d >= m.length - EPS ? m.length : null)
      const even = slots.slice(first, j).every(s => s.duration === slots[first].duration)
      if (even && b != null && (i > 0 || near(old[i], a))) {
        const pieces = j - first
        const step = (b - a) / pieces
        if (writable(step)) {
          for (let k = i; k < j; k++) starts[k] = a + (k - first) * step
          placed = true
        }
      }
    }
    if (!placed) return null
    i = j
  }
  for (let k = 1; k < starts.length; k++) if (starts[k] <= starts[k - 1] + EPS) return null
  return starts
}

/** A run's slots at new times, written as edits, if every new length can be written in the score's divisions. */
function writePlan(slots, starts, run, m, lead, fails) {
  const fail = why => (fails.push(why), null)
  const d = m.divisions
  const runStart = run.start / d
  // lengths: up to the next slot; the last keeps its own if it still fits, and reaches the bar's
  // end if it did before
  const lengths = []
  for (let k = 0; k < slots.length - 1; k++) lengths.push(starts[k + 1] - starts[k])
  const k = slots.length - 1
  const own = slots[k].duration / d
  const room = m.length - starts[k]
  if (room <= EPS) return fail('last note past the bar')
  const reached = run.end / d >= m.length - EPS
  lengths.push(reached ? room : Math.min(own, room))
  const values = []
  for (let i = 0; i < slots.length; i++) {
    const div = lengths[i] * d
    if (Math.abs(div - Math.round(div)) > EPS) {
      const f = [2, 3, 4, 6, 8, 12, 16, 24].find(f => Math.abs(div * f - Math.round(div * f)) < EPS)
      if (f && m.part != null) finer.set(m.part, lcm(finer.get(m.part) ?? 1, f))
      return fail(`not in the divisions (${+lengths[i].toFixed(4)} q, ${d}/q)`)
    }
    if (Math.round(div) <= 0) return fail('no length')
    const first = slots[i].notes[0]
    const w = written(lengths[i], { type: first.type, dots: first.dots, tm: first.tm })
    if (!w) return fail(`no single value (${+lengths[i].toFixed(4)} q)`)
    values.push(w)
  }
  // triplets, each group as long as two of its shortest plain value, marked where it starts and
  // stops: Verovio times notes as triplets only between those marks
  const marks = new Array(slots.length).fill(null)
  let open = null
  let sum = 0
  let shortest = Infinity
  for (let i = 0; i < slots.length; i++) {
    const w = values[i]
    if (w.tm && (w.tm.actual !== 3 || w.tm.normal !== 2)) return fail('a tuplet other than a triplet')
    if (!w.tm) {
      if (open != null) return fail('a triplet left open')
      continue
    }
    if (open == null) [open, sum, shortest] = [i, 0, Infinity]
    sum += lengths[i]
    shortest = Math.min(shortest, VALUES.find(([t]) => t === w.type)[1])
    if (near(sum, 2 * shortest)) {
      if (open === i) return fail('a triplet left open')
      marks[open] = 'start'
      marks[i] = 'stop'
      open = null
    } else if (sum > 2 * shortest + EPS && !near(sum % (2 * shortest), 0)) return fail('a triplet left open')
  }
  if (open != null) return fail('a triplet left open')
  const edits = []
  for (let i = 0; i < slots.length; i++) {
    slots[i].notes.forEach((e, n) => {
      const t = mark(rewrite(e, Math.round(lengths[i] * d), values[i]), n === 0 ? marks[i] : null)
      if (t !== e.text) edits.push([e.start, e.end, t])
    })
  }
  // the voice's entry: a forward before it as long as its first note's time
  const entry = Math.round((starts[0] - runStart) * d)
  if (Math.abs((starts[0] - runStart) * d - entry) > EPS) return fail('entry not in the divisions')
  if (lead) {
    if (entry === 0) edits.push([lead.start, lead.end, ''])
    else if (entry !== lead.duration) edits.push([lead.start, lead.end, lead.text.replace(/<duration>\d+<\/duration>/, `<duration>${entry}</duration>`)])
  } else if (entry > 0) {
    edits.push([slots[0].notes[0].start, slots[0].notes[0].start, `<forward><duration>${entry}</duration></forward>`])
  }
  // the backup after the voice: back to where it went before
  const end = Math.round((starts[k] + lengths[k]) * d)
  if (run.backup) {
    const back = run.backup.duration + (end - run.end)
    if (back < 0) return fail('backup')
    edits.push([run.backup.start, run.backup.end, back === 0 ? '' : run.backup.text.replace(/<duration>\d+<\/duration>/, `<duration>${back}</duration>`)])
  }
  return edits
}

/** A note's tuplet marks taken off, and a triplet's start or stop mark put on if given. */
function mark(t, which) {
  t = t.replace(/\s*<tuplet\b[^>]*\/>/g, '').replace(/\s*<tuplet\b[^>]*>[\s\S]*?<\/tuplet>/g, '').replace(/\s*<notations>\s*<\/notations>/, '')
  if (!which) return t
  const tuplet = `<tuplet type="${which}" number="1"/>`
  if (/<notations>/.test(t)) return t.replace(/<notations>/, `<notations>${tuplet}`)
  const at = t.search(/<(lyric|play|listen)\b|<\/note>/)
  return `${t.slice(0, at)}<notations>${tuplet}</notations>${t.slice(at)}`
}

/** A note or rest written with a new length (divisions) and value: duration, type, dots, triplet; beams off a quarter or longer. */
function rewrite(e, duration, w) {
  let t = e.text.replace(/<duration>\d+<\/duration>/, `<duration>${duration}</duration>`)
  if (sameValue(w, { type: e.type, dots: e.dots, tm: e.tm })) return t
  if (/<type\b[^>]*>[^<]*<\/type>/.test(t)) t = t.replace(/(<type\b[^>]*>)[^<]*(<\/type>)/, `$1${w.type}$2`)
  else t = t.replace(/(<\/voice>|<\/duration>)/, `$1<type>${w.type}</type>`)
  t = t.replace(/\s*<dot\b[^>]*\/>/g, '')
  if (w.dots) t = t.replace(/(<\/type>)/, `$1${'<dot/>'.repeat(w.dots)}`)
  t = t.replace(/\s*<time-modification>[\s\S]*?<\/time-modification>/, '')
  if (w.tm) {
    const tm = `<time-modification><actual-notes>${w.tm.actual}</actual-notes><normal-notes>${w.tm.normal}</normal-notes></time-modification>`
    if (/<\/accidental>/.test(t)) t = t.replace(/(<\/accidental>)/, `$1${tm}`)
    else if (/<dot\/>/.test(t)) t = t.replace(/((?:<dot\/>)+)/, `$1${tm}`)
    else t = t.replace(/(<\/type>)/, `$1${tm}`)
  }
  if (VALUES.findIndex(([n]) => n === w.type) <= VALUES.findIndex(([n]) => n === 'quarter')) t = t.replace(/\s*<beam\b[^>]*>[^<]*<\/beam>/g, '')
  return t.replace(/\s*<notations>\s*<\/notations>/, '')
}
