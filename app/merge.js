// Gated second-opinion merge for MusicXML.
//
// Audiveris is the authority. A light model (Polyphonic-TrOMR, run on staff crops)
// is consulted only where Audiveris's own output is broken, and only under a gate:
// a measure is replaced only when Audiveris's slice for that staff is
// duration-invalid or missing, the model's replacement is itself duration-valid,
// AND the model's distinct pitches cover Audiveris's distinct pitches for that slice.
// Without the pitch check the merge trades pitch for validity — on the Hallelujah
// test page it fixed validity 41/57 -> 56/56 but lost pitch 217 -> 213, because
// Audiveris's "invalid" measures were invalid only in rest durations while their
// pitches were right. See NOTES.md ("Gated TrOMR merge").
//
// The pitch check is a SET of distinct pitches, not a multiset: Audiveris splits one
// sounding pitch across voices in divisi, so counting multiplicity would refuse the
// divisi case the merge exists for. Losing a doubling is a smaller error than losing
// a pitch, and the replacement's job is validity.
//
// Pitches are resolved through the key signature: TrOMR writes no <alter> elements
// (it relies on the key — F# and C# in D major are bare <step>F</step>), while
// Audiveris writes them explicitly. Comparing raw steps would call those different
// pitches and refuse nearly every replacement in a sharp or flat key.
//
// Never a note-list union, never touch a valid Audiveris measure, never touch
// another staff in the same measure. Transcoda is deliberately NOT a source here:
// it scored 0/218 on the same Hallelujah page.
//
// Never a note-list union, never touch a valid Audiveris measure, never touch
// another staff in the same measure. Transcoda is deliberately NOT a source here:
// it scored 0/218 on the same Hallelujah page.
//
// The merge is source-agnostic: it takes Audiveris MusicXML and one MusicXML string
// per TrOMR staff crop, in top-to-bottom order per system (staff file i covers
// system i / pairs, pair i % pairs). How the TrOMR files are produced in the browser
// is a separate step; this module only merges.
//
// No dependencies: the XML parser/serialiser and the .mxl (zip) reader/writer below
// are written for this file, so it runs in the browser and in Node alike.
import { inflateRaw, deflateRaw } from './zip-mxl.js'

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" }

function decodeEntities(s) {
  return s.replace(/&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z]+);/g, (_, e) => {
    if (e[0] === '#') return String.fromCodePoint(e[1] === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
    return ENTITIES[e] ?? `&${e};`
  })
}

function encodeEntities(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function encodeAttr(s) {
  return encodeEntities(s).replace(/"/g, '&quot;')
}

/** Parse an XML document into { tag, attrs, children, text }. Whitespace-only text is dropped. */
export function parseXml(src) {
  let i = 0
  const n = src.length
  function skipWs() { while (i < n && /\s/.test(src[i])) i++ }
  function parseElement() {
    // src[i] === '<'
    i++
    if (src.startsWith('!--', i)) { i = src.indexOf('-->', i + 3) + 3; return null }
    if (src.startsWith('![CDATA[', i)) { i = src.indexOf(']]>', i + 8) + 3; return null }
    if (src[i] === '?') { i = src.indexOf('?>', i + 1) + 2; return null }
    if (src.startsWith('!DOCTYPE', i)) {
      // skip to '>', honouring an internal subset in [ ... ]
      i += 8
      let depth = 0
      while (i < n) {
        if (src[i] === '[') depth++
        else if (src[i] === ']') depth--
        else if (src[i] === '>' && depth === 0) { i++; break }
        i++
      }
      return null
    }
    const m = /^[A-Za-z_][\w:.-]*/.exec(src.slice(i))
    if (!m) throw new Error(`merge: bad tag at offset ${i}: ${src.slice(i, i + 40)}`)
    const tag = m[0]
    i += tag.length
    const attrs = {}
    for (;;) {
      skipWs()
      if (src[i] === '/') { i += 2; return { tag, attrs, children: [], text: '' } } // />
      if (src[i] === '>') { i++; break }
      const am = /^([A-Za-z_][\w:.-]*)\s*=\s*("[^"]*"|'[^']*')/.exec(src.slice(i))
      if (!am) throw new Error(`merge: bad attribute at offset ${i}: ${src.slice(i, i + 40)}`)
      attrs[am[1]] = decodeEntities(am[2].slice(1, -1))
      i += am[0].length
    }
    const el = { tag, attrs, children: [], text: '' }
    for (;;) {
      if (i >= n) throw new Error(`merge: unclosed <${tag}>`)
      if (src[i] === '<') {
        if (src.startsWith('</', i)) {
          i = src.indexOf('>', i) + 1
          return el
        }
        const child = parseElement()
        if (child) el.children.push(child)
      } else {
        const j = src.indexOf('<', i)
        const text = decodeEntities(src.slice(i, j === -1 ? n : j))
        if (text.trim()) el.text += text
        i = j === -1 ? n : j
      }
    }
  }
  skipWs()
  if (src.startsWith('<?xml', i)) i = src.indexOf('?>', i) + 2
  for (;;) {
    skipWs()
    if (i >= n) throw new Error('merge: no root element')
    const el = parseElement()
    if (el) return el
  }
}

/** Serialise a parsed element back to XML text. */
export function serialiseXml(el, indent = '') {
  const attrs = Object.entries(el.attrs).map(([k, v]) => ` ${k}="${encodeAttr(v)}"`).join('')
  const kids = el.children.map(c => serialiseXml(c, indent + '  ')).join('')
  const text = el.text ? encodeEntities(el.text) : ''
  if (!kids && !text) return `${indent}<${el.tag}${attrs}/>`
  if (!kids) return `${indent}<${el.tag}${attrs}>${text}</${el.tag}>`
  return `${indent}<${el.tag}${attrs}>${text}${kids ? '\n' + kids + indent : ''}</${el.tag}>`
}

// ---------------------------------------------------------------------------
// MusicXML helpers (all pure, all exported for the tests)
// ---------------------------------------------------------------------------

export const children = (el, tag) => el.children.filter(c => c.tag === tag)
export const child = (el, tag) => el.children.find(c => c.tag === tag)
export const textOf = (el, tag) => { const c = child(el, tag); return c ? c.text.trim() : null }

export function measureNumber(el, fallback) {
  const raw = (el.attrs.number ?? '').replace(/[^0-9]/g, '')
  const n = parseInt(raw, 10)
  return Number.isFinite(n) ? n : fallback
}

/** Beats per bar, from the first <attributes><time><beats> in the score (fallback 4). */
export function beatsOf(root) {
  for (const part of children(root, 'part')) {
    for (const meas of children(part, 'measure')) {
      const at = child(meas, 'attributes')
      if (!at) continue
      for (const time of children(at, 'time')) {
        const b = parseInt(textOf(time, 'beats') ?? '', 10)
        if (Number.isFinite(b) && b > 0) return b
      }
    }
  }
  return 4
}

/** Divisions (ticks per quarter) of a part, from its first <attributes><divisions>. */
export function divisionsOf(partEl) {
  for (const meas of children(partEl, 'measure')) {
    const at = child(meas, 'attributes')
    if (at && textOf(at, 'divisions')) return parseInt(textOf(at, 'divisions'), 10)
  }
  return null
}

const SHARPS = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
const FLATS = ['B', 'E', 'A', 'D', 'G', 'C', 'F']

/** <key><fifths> of a part (0 = C major / A minor), from its first <key>. */
export function keyFifthsOf(partEl) {
  for (const meas of children(partEl, 'measure')) {
    const at = child(meas, 'attributes')
    if (!at) continue
    for (const key of children(at, 'key')) {
      const f = parseInt(textOf(key, 'fifths') ?? '', 10)
      if (Number.isFinite(f)) return f
    }
  }
  return 0
}

/** Alter implied by the key signature for a step (-1, 0, 1). */
function keyAlter(step, fifths) {
  if (fifths > 0) return SHARPS.slice(0, fifths).includes(step) ? 1 : 0
  if (fifths < 0) return FLATS.slice(0, -fifths).includes(step) ? -1 : 0
  return 0
}

/** Pitch key of a note, resolved through the key signature (see header). */
function pitchKey(noteEl, fifths = 0) {
  const p = child(noteEl, 'pitch')
  if (!p) return null
  const step = textOf(p, 'step')
  const octave = textOf(p, 'octave')
  if (!step || octave === null) return null
  const alterText = textOf(p, 'alter')
  const alter = alterText === null ? keyAlter(step, fifths) : parseFloat(alterText)
  const acc = alter === 1 ? '#' : alter === -1 ? 'b' : alter === 2 ? '##' : alter === -2 ? 'bb' : ''
  return `${step}${acc}${octave}`
}

const isChord = n => !!child(n, 'chord')
const isGrace = n => !!child(n, 'grace')
const noteStaff = n => parseInt(textOf(n, 'staff') ?? '1', 10)
const noteVoice = n => parseInt(textOf(n, 'voice') ?? '1', 10)
const noteDuration = (n, divs) => {
  const d = parseFloat(textOf(n, 'duration') ?? '')
  return Number.isFinite(d) && divs ? d / divs : 0 // in quarter notes
}

/**
 * Voice sums for one measure, in quarter notes, keyed `${staff}:${voice}`.
 * Chord notes and grace notes are excluded (a chord note is the same sounding event).
 * Rests count: a rest occupies time.
 */
export function voiceSums(measureEl, divs) {
  const sums = new Map()
  for (const n of children(measureEl, 'note')) {
    if (isChord(n) || isGrace(n)) continue
    const key = `${noteStaff(n)}:${noteVoice(n)}`
    sums.set(key, (sums.get(key) ?? 0) + noteDuration(n, divs))
  }
  return sums
}

/** A (staff, voice) slice is duration-valid when its sum is exactly one bar. */
export function sliceValid(measureEl, divs, beats, staff) {
  let any = false
  for (const [key, sum] of voiceSums(measureEl, divs)) {
    if (parseInt(key, 10) !== staff) continue
    any = true
    if (Math.abs(sum - beats) > 1e-6) return false
  }
  return any
}

/** Distinct pitches of one staff's notes in a measure (rests excluded). */
export function pitchSet(measureEl, staff, fifths = 0) {
  const pitches = new Set()
  for (const n of children(measureEl, 'note')) {
    if (noteStaff(n) !== staff) continue
    const p = pitchKey(n, fifths)
    if (p) pitches.add(p)
  }
  return pitches
}

export function setCovers(have, need) {
  for (const p of need) if (!have.has(p)) return false
  return true
}

/** System bar ranges from the first part's <print new-system="yes"> markers. */
export function barsPerSystem(root) {
  const part = children(root, 'part')[0]
  if (!part) return []
  const measures = children(part, 'measure')
  const starts = [measureNumber(measures[0], 1)]
  for (const m of measures.slice(1)) {
    const pr = child(m, 'print')
    if (pr && pr.attrs['new-system'] === 'yes') starts.push(measureNumber(m, starts[starts.length - 1] + 1))
  }
  const out = []
  for (let s = 0; s < starts.length; s++) {
    const next = s + 1 < starts.length ? starts[s + 1] : measureNumber(measures[measures.length - 1], starts[s]) + 1
    out.push({ start: starts[s], bars: next - starts[s] })
  }
  return out
}

/** Staff pairs in TrOMR file order: [[partIndex, staff], ...] across all parts. */
export function staffPairs(root) {
  const pairs = []
  children(root, 'part').forEach((part, pi) => {
    let staves = 1
    for (const meas of children(part, 'measure')) {
      const at = child(meas, 'attributes')
      if (at && textOf(at, 'staves')) { staves = parseInt(textOf(at, 'staves'), 10); break }
    }
    for (let s = 1; s <= staves; s++) pairs.push([pi, s])
  })
  return pairs
}

// ---------------------------------------------------------------------------
// The merge
// ---------------------------------------------------------------------------

/**
 * Merge Audiveris MusicXML with TrOMR staff-crop MusicXML.
 *
 * @param {string} audiverisXml - Audiveris output, plain MusicXML text
 * @param {string[]} tromrStaffXmls - one MusicXML string per TrOMR staff crop,
 *   in system order, top-to-bottom staff per system (staff file i covers system
 *   floor(i / pairs), pair i % pairs)
 * @param {{ beats?: number }} [opts]
 * @returns {{ xml: string, report: { replaced: object[], kept: number, skipped: object[] } }}
 */
export function mergeMusicXml(audiverisXml, tromrStaffXmls, opts = {}) {
  const root = parseXml(audiverisXml)
  const beats = opts.beats ?? beatsOf(root)
  const systems = barsPerSystem(root)
  const pairs = staffPairs(root)
  const parts = children(root, 'part')
  const tromr = tromrStaffXmls.map(x => parseXml(x))

  const report = { replaced: [], kept: 0, skipped: [] }

  function tromrStaff(systemIdx, pairIdx) {
    const i = systemIdx * pairs.length + pairIdx
    return tromr[i] ?? null
  }

  function tromrMeasure(tRoot, barInSystem) {
    const part = children(tRoot, 'part')[0]
    if (!part) return null
    for (const m of children(part, 'measure')) {
      if (measureNumber(m, -1) === barInSystem) return m
    }
    return null
  }

  systems.forEach((sys, sysIdx) => {
    parts.forEach((partEl, pi) => {
      const divs = divisionsOf(partEl)
      if (!divs) { report.kept += children(partEl, 'measure').length; return }
      const stavesHere = pairs.filter(([p]) => p === pi).map(([, s]) => s)
      for (const meas of children(partEl, 'measure')) {
        const bar = measureNumber(meas, -1)
        if (bar < sys.start || bar >= sys.start + sys.bars) continue
        for (const staff of stavesHere) {
          if (sliceValid(meas, divs, beats, staff)) { report.kept++; continue }
          // Audiveris's slice for this staff is broken (or empty): consult TrOMR.
          const pairIdx = pairs.findIndex(([p, s]) => p === pi && s === staff)
          const tRoot = tromrStaff(sysIdx, pairIdx)
          if (!tRoot) { report.skipped.push({ part: pi, bar, staff, reason: 'no-tromr-staff' }); continue }
          const tMeas = tromrMeasure(tRoot, bar - sys.start + 1)
          if (!tMeas) { report.skipped.push({ part: pi, bar, staff, reason: 'no-tromr-measure' }); continue }
          const tDivs = divisionsOf(children(tRoot, 'part')[0]) ?? divs
          const tStaff = 1 // a staff file holds one staff; its notes carry staff 1
          if (!sliceValid(tMeas, tDivs, beats, tStaff)) {
            report.skipped.push({ part: pi, bar, staff, reason: 'tromr-invalid' })
            continue
          }
          const audPitches = pitchSet(meas, staff, keyFifthsOf(partEl))
          const tromrPitches = pitchSet(tMeas, tStaff, keyFifthsOf(children(tRoot, 'part')[0]))
          if (audPitches.size && !setCovers(tromrPitches, audPitches)) {
            report.skipped.push({ part: pi, bar, staff, reason: 'pitch-disagrees' })
            continue
          }
          // Gate passed: replace only this staff's notes in this measure.
          const scale = divs / tDivs
          const replacement = children(tMeas, 'note').map(n => cloneNoteFor(n, staff, scale))
          const idx = meas.children.findIndex(c => c.tag === 'note' && noteStaff(c) === staff)
          meas.children = meas.children.filter(c => !(c.tag === 'note' && noteStaff(c) === staff))
          meas.children.splice(idx === -1 ? meas.children.length : idx, 0, ...replacement)
          report.replaced.push({ part: pi, bar, staff, tromrStaff: sysIdx * pairs.length + pairIdx, tromrBar: bar - sys.start + 1, notes: replacement.length })
        }
      }
    })
  })

  return { xml: serialiseXml(root), report }
}

/**
 * Clone a TrOMR note, rescaling its duration to the target divisions, staff and voice.
 * Voice goes after <duration> (and <tie>), staff after <type>/<dot>/<stem> — the
 * MusicXML element order, so the output still validates. TrOMR notes carry neither.
 */
function cloneNoteFor(noteEl, staff, scale) {
  const clone = JSON.parse(JSON.stringify(noteEl))
  const dur = child(clone, 'duration')
  if (dur && scale !== 1) dur.text = String(Math.round(parseFloat(dur.text) * scale))
  const voiceEl = { tag: 'voice', attrs: {}, children: [], text: '1' }
  const staffEl = { tag: 'staff', attrs: {}, children: [], text: String(staff) }
  const out = []
  let voiceDone = false, staffDone = false
  for (const c of clone.children) {
    if (c.tag === 'voice') { c.text = '1'; voiceDone = true }
    if (c.tag === 'staff') { c.text = String(staff); staffDone = true }
    out.push(c)
    if (!voiceDone && (c.tag === 'duration' || c.tag === 'tie')) { out.push(voiceEl); voiceDone = true }
  }
  if (!voiceDone) out.push(voiceEl)
  if (!staffDone) {
    // insert after the last type/dot/stem/notehead element, else at the end
    const group = ['type', 'dot', 'accidental', 'time-modification', 'stem', 'notehead']
    let at = -1
    out.forEach((c, i) => { if (group.includes(c.tag)) at = i })
    out.splice(at + 1, 0, staffEl)
  }
  clone.children = out
  return clone
}

// ---------------------------------------------------------------------------
// .mxl (zipped MusicXML) — read the .xml entry out, write one back
// ---------------------------------------------------------------------------

/** Read a .mxl (zip) and return the MusicXML text of its first .xml/.musicxml entry. */
export async function readMxl(bytes) {
  const data = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)
  const entries = zipEntries(data)
  const entry = entries.find(e => /\.(xml|musicxml)$/i.test(e.name))
  if (!entry) throw new Error('merge: no MusicXML entry in .mxl')
  const raw = data.subarray(entry.dataStart, entry.dataStart + entry.compressedSize)
  if (entry.method === 0) return new TextDecoder().decode(raw) // stored, not deflated
  if (entry.method !== 8) throw new Error(`merge: unsupported zip method ${entry.method}`)
  return new TextDecoder().decode(await inflateRaw(raw))
}

/** Write MusicXML text into a .mxl (zip) with one entry. Returns the zip bytes. */
export async function writeMxl(xmlText, filename = 'score.musicxml') {
  const payload = new TextEncoder().encode(xmlText)
  const deflated = await deflateRaw(payload)
  const name = new TextEncoder().encode(filename)
  const crc = crc32(payload)
  const local = new Uint8Array(30 + name.length)
  const lv = new DataView(local.buffer)
  lv.setUint32(0, 0x04034b50, true)
  lv.setUint16(4, 20, true) // version needed: deflate
  lv.setUint16(6, 0x0800, true) // UTF-8 flag
  lv.setUint16(8, 8, true) // method deflate
  lv.setUint32(10, 0, true) // mod time/date
  lv.setUint32(14, crc, true)
  lv.setUint32(18, deflated.length, true)
  lv.setUint32(22, payload.length, true)
  lv.setUint16(26, name.length, true)
  local.set(name, 30)
  const central = new Uint8Array(46 + name.length)
  const cv = new DataView(central.buffer)
  cv.setUint32(0, 0x02014b50, true)
  cv.setUint16(4, 20, true)
  cv.setUint16(6, 20, true)
  cv.setUint16(8, 0x0800, true)
  cv.setUint16(10, 8, true)
  cv.setUint32(12, 0, true)
  cv.setUint32(16, crc, true)
  cv.setUint32(20, deflated.length, true)
  cv.setUint32(24, payload.length, true)
  cv.setUint16(28, name.length, true)
  cv.setUint32(42, 0, true) // local header offset
  central.set(name, 46)
  const eocd = new Uint8Array(22)
  const ev = new DataView(eocd.buffer)
  ev.setUint32(0, 0x06054b50, true)
  ev.setUint16(8, 1, true)
  ev.setUint16(10, 1, true)
  ev.setUint32(12, central.length, true)
  ev.setUint32(16, local.length + deflated.length, true)
  const out = new Uint8Array(local.length + deflated.length + central.length + eocd.length)
  out.set(local, 0)
  out.set(deflated, local.length)
  out.set(central, local.length + deflated.length)
  out.set(eocd, local.length + deflated.length + central.length)
  return out
}

/** Central-directory entries of a zip: { name, method, compressedSize, dataStart }. */
export function zipEntries(data) {
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength)
  // find the end-of-central-directory record, scanning back from the end
  let eocd = -1
  for (let i = data.length - 22; i >= Math.max(0, data.length - 65557); i--) {
    if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break }
  }
  if (eocd === -1) throw new Error('merge: not a zip file (no end-of-central-directory)')
  const count = view.getUint16(eocd + 10, true)
  let off = view.getUint32(eocd + 16, true)
  const entries = []
  for (let k = 0; k < count; k++) {
    if (view.getUint32(off, true) !== 0x02014b50) throw new Error('merge: bad central directory')
    const method = view.getUint16(off + 10, true)
    const compressedSize = view.getUint32(off + 20, true)
    const nameLen = view.getUint16(off + 28, true)
    const extraLen = view.getUint16(off + 30, true)
    const commentLen = view.getUint16(off + 32, true)
    const localOff = view.getUint32(off + 42, true)
    const name = new TextDecoder().decode(data.subarray(off + 46, off + 46 + nameLen))
    const lv = new DataView(data.buffer, data.byteOffset + localOff, 30)
    if (lv.getUint32(0, true) !== 0x04034b50) throw new Error('merge: bad local header')
    const lNameLen = lv.getUint16(26, true)
    const lExtraLen = lv.getUint16(28, true)
    entries.push({ name, method, compressedSize, dataStart: localOff + 30 + lNameLen + lExtraLen })
    off += 46 + nameLen + extraLen + commentLen
  }
  return entries
}

/** CRC-32 (IEEE) of a byte array. */
export function crc32(bytes) {
  let table = crc32.table
  if (!table) {
    table = crc32.table = new Uint32Array(256)
    for (let n = 0; n < 256; n++) {
      let c = n
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
      table[n] = c
    }
  }
  let crc = 0xffffffff
  for (const b of bytes) crc = table[(crc ^ b) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}
