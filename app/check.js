// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// After a read: the score as read, drawn with Verovio by @jdlehman/score-view (score-view.js), to
// check and correct before downloading. Tap a note or rest, then change it. Bars that don't add
// up to their time signature are shaded: the reader most often goes wrong there.

import {
  addChordNote, checkFlags, createEngraver, createScoreView, deleteNote, mergeFlags, noteValue, parseMusicXML,
  readerFlags, restToNote, setAlter, setLength, stepNote, writtenRests,
} from './score-view.js'

const engrave = createEngraver(() => new Worker(new URL('engrave-worker.js', import.meta.url), { type: 'module' }))
const $ = id => document.getElementById(id)
const STEP_PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }
const SIGNS = { [-2]: '♭♭', [-1]: '♭', 0: '', 1: '♯', 2: '♯♯' }
const BASE = { whole: 4, half: 2, quarter: 1, eighth: 0.5, '16th': 0.25 }

/** Show the score read, to correct: `results` are the MusicXML files Audiveris wrote (one, or one a movement). */
export async function showScore(results, title) {
  try {
    const scores = await Promise.all(results.map(blob => blob.text()))
    start(scores, title)
  } catch (e) {
    console.warn('The score could not be shown:', e)
  }
}

function start(scores, title) {
  // each movement: the score as read, as it is now, as last downloaded with changes, what is
  // selected, and the scores before each change
  const movements = scores.map(xml => ({ original: xml, xml, saved: xml, selected: null, past: [] }))
  const changed = m => m.xml !== m.original
  /** Changes not downloaded yet (a movement back as read has none to lose). */
  const unsaved = () => movements.some(m => changed(m) && m.xml !== m.saved)
  let downloaded = false
  let at = 0
  let score = null
  let rests = []
  let drawn = false
  const now = () => movements[at]

  $('fix').hidden = false
  const view = createScoreView($('fix-score'), {
    engrave,
    onTap: target => { now().selected = target; view.select(target); controls() },
    onDraw: () => { drawn = true; $('fix-status').textContent = '' },
    onStatus: ({ drawing, error }) => {
      $('fix-status').textContent = error ? `The score couldn’t be drawn: ${error}` : drawing && !drawn ? 'Drawing the score…' : ''
    },
  })

  function redraw() {
    const { xml, selected } = now()
    try {
      score = parseMusicXML(xml)
    } catch (e) {
      $('fix-status').textContent = `The score couldn’t be drawn: ${e.message}`
      return
    }
    rests = writtenRests(xml)
    void view.setXml(xml, score)
    view.highlight(mergeFlags(checkFlags(xml, score), readerFlags(xml)))
    view.select(selected)
    controls()
  }

  /** Make a change with one of score-view.js's edits. */
  function change(edit) {
    const m = now()
    if (!m.selected) return
    try {
      const out = edit(m.xml, m.selected)
      if (out.xml === m.xml) return
      m.past.push({ xml: m.xml, selected: m.selected })
      m.xml = out.xml
      m.selected = out.select
      redraw()
    } catch (e) {
      console.warn('That change couldn’t be made:', e)
      $('fix-status').textContent = `That change couldn’t be made: ${e.message}`
    }
  }

  function undo() {
    const m = now()
    const last = m.past.pop()
    if (!last) return
    m.xml = last.xml
    m.selected = last.selected
    redraw()
  }

  const picked = () => {
    const sel = now().selected
    return {
      note: sel?.kind === 'note' ? score?.notes.find(n => n.id === sel.id) : undefined,
      rest: sel?.kind === 'rest' ? rests.find(r => r.id === sel.id) : undefined,
    }
  }
  const alterOf = n => ((((n.pitch - ((n.octave + 1) * 12 + STEP_PC[n.step])) % 12) + 18) % 12) - 6

  function controls() {
    const { note, rest } = picked()
    const bar = i => score?.measures[i]?.label ?? i + 1
    const part = n => score?.lines.find(l => l.id === n.line)?.name ?? ''
    $('fix-picked').textContent = note ? `${note.step}${SIGNS[alterOf(note)] ?? ''}${note.octave} · bar ${bar(note.measure)} · ${part(note)}`
      : rest ? `Rest · bar ${bar(rest.measure)}`
      : 'Tap a note or rest to change it.'
    $('fix-pitch').hidden = !note
    $('fix-length').hidden = !note && !rest
    $('fix-note').hidden = !note
    $('fix-rest').hidden = !rest
    const value = noteValue(note?.duration ?? rest?.duration ?? 0)
    for (const b of document.querySelectorAll('#fix-length [data-length]')) b.setAttribute('aria-pressed', String(!!value && BASE[value.type] === Number(b.dataset.length)))
    $('fix-dot').setAttribute('aria-pressed', String(!!value?.dots))
    $('fix-dot').disabled = !value || !(value.type in BASE)
    for (const b of document.querySelectorAll('#fix-pitch [data-alter]')) b.setAttribute('aria-pressed', String(!!note && alterOf(note) === Number(b.dataset.alter)))
    $('fix-undo').disabled = !now().past.length
    // once something is changed: download it, and after a download, again when there is more
    $('fix-download').hidden = !movements.some(changed)
    $('fix-download').disabled = !unsaved()
    $('fix-download').textContent = !unsaved() ? 'Saved' : downloaded ? 'Download again with your newest changes' : 'Download with your changes'
  }

  // the controls
  for (const b of document.querySelectorAll('#fix-pitch [data-step]')) b.addEventListener('click', () => change((xml, t) => stepNote(xml, t.id, Number(b.dataset.step))))
  for (const b of document.querySelectorAll('#fix-pitch [data-alter]')) b.addEventListener('click', () => change((xml, t) => setAlter(xml, t.id, Number(b.dataset.alter))))
  for (const b of document.querySelectorAll('#fix-length [data-length]')) {
    b.addEventListener('click', () => {
      const { note, rest } = picked()
      const dotted = !!noteValue(note?.duration ?? rest?.duration ?? 0)?.dots
      change((xml, t) => setLength(xml, t, Number(b.dataset.length) * (dotted ? 1.5 : 1)))
    })
  }
  $('fix-dot').addEventListener('click', () => {
    const { note, rest } = picked()
    const value = noteValue(note?.duration ?? rest?.duration ?? 0)
    if (value && value.type in BASE) change((xml, t) => setLength(xml, t, BASE[value.type] * (value.dots ? 1 : 1.5)))
  })
  $('fix-add').addEventListener('click', () => change((xml, t) => addChordNote(xml, t.id)))
  $('fix-to-rest').addEventListener('click', () => change((xml, t) => deleteNote(xml, t.id)))
  $('fix-to-note').addEventListener('click', () => change((xml, t) => restToNote(xml, t.id)))
  $('fix-undo').addEventListener('click', undo)
  // every change so far, not just the newest: the file is the whole corrected score
  $('fix-download').addEventListener('click', () => {
    movements.forEach((m, i) => {
      if (!changed(m)) return
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([m.xml], { type: 'application/vnd.recordare.musicxml+xml' }))
      a.download = movements.length === 1 ? `${title} (corrected).musicxml` : `${title} (${i + 1}, corrected).musicxml`
      a.click()
      setTimeout(() => URL.revokeObjectURL(a.href), 1000)
      m.saved = m.xml
    })
    downloaded = true
    controls()
  })
  // changes live only in this page: ask before leaving it (or reading another score) with some not downloaded
  window.addEventListener('beforeunload', e => {
    if (unsaved()) e.preventDefault()
  })
  if (movements.length > 1) {
    const select = $('fix-movement')
    select.hidden = false
    select.replaceChildren(...movements.map((_, i) => new Option(`Movement ${i + 1}`, String(i))))
    select.addEventListener('change', () => { at = Number(select.value); drawn = false; redraw() })
  }
  document.addEventListener('keydown', e => {
    if ($('fix').hidden || ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return
    const sel = now().selected
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); return undo() }
    if (e.key === 'Escape') { now().selected = null; view.select(null); return controls() }
    if (sel?.kind !== 'note') return
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); change((xml, t) => stepNote(xml, t.id, e.key === 'ArrowUp' ? 1 : -1)) }
    if (e.key === 'Backspace' || e.key === 'Delete') { e.preventDefault(); change((xml, t) => deleteNote(xml, t.id)) }
  })

  redraw()
}
