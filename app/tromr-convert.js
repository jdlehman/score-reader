// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// TrOMR's token stream for one staff crop, as MusicXML for app/merge.js.
//
// The model writes raw tokens, not MusicXML: `clef-G2+keySignature-CM+
// timeSignature-4/4+note-G3_half|note-C4_quarter|...+barline+...`. This turns
// them into the single-part MusicXML the gated merge consumes (divisions 64,
// one measure per bar, chord notes marked, rests as rests) — the same shape the
// focr reference files have (test/fixtures/divisi-merge/staff*.musicxml), so a
// measure the model reads well merges exactly as the reference does.
//
// The dialect is the one the spike's scorer parses (score-reader-spikes/
// crispembed-wasm/score_wasm.py): note-<STEP>[#b]<OCT>_<DUR>[.], rest-<DUR>[.],
// barline, multirest-N, clef-*, keySignature-*, timeSignature-*. Anything else
// is skipped with a warning, never silently dropped and never interpolated —
// the tokens are model output, and only values the regexes accept reach the XML.
//
// Pure: no DOM, runs in Node and in the browser alike.

/** Ticks at divisions 64 (a quarter note), the focr reference's divisions. */
export const TROMR_DIVISIONS = 64
const TICKS = { whole: 256, half: 128, quarter: 64, eighth: 32, sixteenth: 16, thirtysecond: 8 }
const TYPE_OF = { whole: 'whole', half: 'half', quarter: 'quarter', eighth: 'eighth', sixteenth: '16th', thirtysecond: '32nd' }

/** <fifths> for a TrOMR key-signature token (CM = C major, Dm = D minor, ...). */
const FIFTHS = {
  C: 0, G: 1, D: 2, A: 3, E: 4, B: 5, 'F#': 6, 'C#': 7,
  F: -1, Bb: -2, Eb: -3, Ab: -4, Db: -5, Gb: -6, Cb: -7,
  Am: 0, Em: 1, Bm: 2, 'F#m': 3, 'C#m': 4, 'G#m': 5, 'D#m': 6, 'A#m': 7,
  Dm: -1, Gm: -2, Cm: -3, Fm: -4, Bbm: -5, Ebm: -6, Abm: -7,
}

const NOTE_RE = /^note-([A-G])(\d)([#b]?)_([a-z_]+)(\.?)$/
const REST_RE = /^rest-([a-z_]+)(\.?)$/
const MULTIREST_RE = /^multirest-(\d+)$/
const CLEF_RE = /^clef-([A-G])(\d)$/
const KEY_RE = /^keySignature-(.+)$/
const TIME_RE = /^timeSignature-(\d+)\/(\d+)$/

function ticksOf(durWord, dotted) {
  // The model writes thirty_second where the scorer's dialect has thirtysecond.
  const base = TICKS[durWord.replace(/_/g, '')]
  if (base === undefined) return null
  return dotted ? Math.round(base * 1.5) : base
}

/** The MusicXML <type> for a duration word (thirty_second is thirtysecond). */
function typeOf(durWord) {
  return TYPE_OF[durWord.replace(/_/g, '')]
}

/** A whole-measure rest's ticks, from the file's own time signature. */
function wholeRestTicks(beats, beatType) {
  return Math.round(beats * TROMR_DIVISIONS * 4 / beatType)
}

function noteXml({ step, octave, alter, duration, type, dotted, chord, rest }) {
  const chordEl = chord ? '<chord/>' : ''
  const pitchEl = rest ? '<rest/>' : `<pitch><step>${step}</step>${alter ? `<alter>${alter}</alter>` : ''}<octave>${octave}</octave></pitch>`
  return `<note>${chordEl}${pitchEl}<duration>${duration}</duration><type>${type}</type>${dotted ? '<dot/>' : ''}</note>`
}

/**
 * Convert a TrOMR token stream to single-part MusicXML for the gated merge.
 * Returns { xml, warnings, stats }: xml is null when the stream yields no
 * measures at all (empty or garbage input — the staff file would be useless).
 * stats counts measures, notes, rests, multirest bars and skipped tokens.
 */
export function tokensToMusicXml(text) {
  const warnings = []
  const stats = { measures: 0, notes: 0, rests: 0, multirestBars: 0, skipped: 0 }
  // Attributes, from the stream's opening tokens (clef/key/time come first).
  let clef = null, fifths = null, beats = null, beatType = null
  let seenContent = false
  const measures = []
  let current = []
  let skipNextBarline = false

  const closeMeasure = () => {
    if (current.length) { measures.push(current); current = [] }
  }
  const wholeRestMeasure = () => {
    const b = beats ?? 4, t = beatType ?? 4
    measures.push([noteXml({ duration: wholeRestTicks(b, t), type: 'whole', dotted: false, chord: false, rest: true })])
    stats.measures++
    stats.rests++
    stats.multirestBars++
  }

  for (const rawTok of String(text ?? '').split('+')) {
    const tok = rawTok.trim()
    if (!tok) continue
    if (tok === 'barline') {
      if (skipNextBarline) skipNextBarline = false
      else closeMeasure()
      continue
    }
    skipNextBarline = false
    if (!seenContent) {
      const cm = CLEF_RE.exec(tok)
      if (cm) { clef = { sign: cm[1], line: cm[2] }; continue }
      const km = KEY_RE.exec(tok)
      if (km) {
        const name = km[1]
        const root = name.endsWith('M') ? name.slice(0, -1) : name.endsWith('m') ? name.slice(0, -1) + 'm' : name
        if (root in FIFTHS) fifths = FIFTHS[root]
        else warnings.push(`unknown key signature ${name}, treated as C major`)
        continue
      }
      const tm = TIME_RE.exec(tok)
      if (tm) { beats = parseInt(tm[1], 10); beatType = parseInt(tm[2], 10); continue }
    }
    const mm = MULTIREST_RE.exec(tok)
    if (mm) {
      seenContent = true
      closeMeasure()
      const n = parseInt(mm[1], 10)
      for (let k = 0; k < n; k++) wholeRestMeasure()
      skipNextBarline = true
      continue
    }
    // A step: one or more chord notes, or a rest, at one time position.
    let stepOk = false
    for (const sub of tok.split('|')) {
      const nm = NOTE_RE.exec(sub)
      if (nm) {
        const [, step, octave, acc, durWord, dot] = nm
        const duration = ticksOf(durWord, dot === '.')
        if (duration === null) { warnings.push(`unknown duration ${durWord} in ${sub}`); stats.skipped++; continue }
        current.push(noteXml({
          step, octave,
          alter: acc === '#' ? 1 : acc === 'b' ? -1 : 0,
          duration, type: typeOf(durWord), dotted: dot === '.',
          chord: stepOk, rest: false,
        }))
        stats.notes++
        stepOk = true
        seenContent = true
        continue
      }
      const rm = REST_RE.exec(sub)
      if (rm) {
        const duration = ticksOf(rm[1], rm[2] === '.')
        if (duration === null) { warnings.push(`unknown duration ${rm[1]} in ${sub}`); stats.skipped++; continue }
        current.push(noteXml({
          duration, type: typeOf(rm[1]), dotted: rm[2] === '.',
          chord: stepOk, rest: true,
        }))
        stats.rests++
        stepOk = true
        seenContent = true
        continue
      }
      warnings.push(`unparsed token ${sub}`)
      stats.skipped++
    }
  }
  closeMeasure()
  stats.measures = measures.length
  if (!measures.length) return { xml: null, warnings, stats }

  const attrs = []
  attrs.push(`<divisions>${TROMR_DIVISIONS}</divisions>`)
  const c = clef ?? { sign: 'G', line: '2' }
  if (!clef) warnings.push('no clef token, assumed treble (G2)')
  attrs.push(`<clef><sign>${c.sign}</sign><line>${c.line}</line></clef>`)
  if (fifths !== null) attrs.push(`<key><fifths>${fifths}</fifths></key>`)
  if (beats !== null) attrs.push(`<time><beats>${beats}</beats><beat-type>${beatType}</beat-type></time>`)
  const body = measures.map((notes, i) =>
    `  <measure number="${i + 1}">\n${i === 0 ? `    <attributes>\n      ${attrs.join('\n      ')}\n    </attributes>\n` : ''}    ${notes.join('\n    ')}\n  </measure>`).join('\n')
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<score-partwise version="4.0">\n  <part-list><score-part id="P1"><part-name>Staff 1</part-name></score-part></part-list>\n  <part id="P1">\n${body}\n  </part>\n</score-partwise>\n`
  return { xml, warnings, stats }
}
