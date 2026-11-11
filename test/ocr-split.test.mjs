import { test } from 'node:test'
import assert from 'node:assert/strict'
import { LYRIC_SEPARATORS, splitWordAtSeparators } from '../app/ocr.js'

// Build a tesseract.js-style word from a string: one symbol per character,
// each 10px wide, 20px tall, in reading order.
function word(text, { confidence = 90, y0 = 100 } = {}) {
  const symbols = [...text].map((ch, i) => ({
    text: ch,
    bbox: { x0: i * 10, y0, x1: i * 10 + 10, y1: y0 + 20 },
  }))
  return {
    text,
    confidence,
    bbox: { x0: 0, y0, x1: text.length * 10, y1: y0 + 20 },
    symbols,
  }
}

test('splits an em-dash-joined lyric word into its syllables', () => {
  const pieces = splitWordAtSeparators(word('Hal—le—lu—jah,'))
  assert.deepEqual(pieces.map(p => p.text), ['Hal', 'le', 'lu', 'jah,'])
  // Piece boxes come from their own symbols, not the whole word.
  assert.deepEqual(pieces[0].bbox, { x0: 0, y0: 100, x1: 30, y1: 120 })
  assert.deepEqual(pieces[1].bbox, { x0: 40, y0: 100, x1: 60, y1: 120 })
  assert.deepEqual(pieces[3].bbox, { x0: 100, y0: 100, x1: 140, y1: 120 })
  // Separator symbols are dropped, not emitted as pieces.
  assert.equal(pieces.flatMap(p => p.symbols).some(s => LYRIC_SEPARATORS.has(s.text)), false)
})

test('splits at every Audiveris separator', () => {
  assert.deepEqual(splitWordAtSeparators(word('joy-ful')).map(p => p.text), ['joy', 'ful'])
  assert.deepEqual(splitWordAtSeparators(word('a–b')).map(p => p.text), ['a', 'b'])
  assert.deepEqual(splitWordAtSeparators(word('a_b')).map(p => p.text), ['a', 'b'])
  assert.deepEqual(splitWordAtSeparators(word('a‿b')).map(p => p.text), ['a', 'b'])
  assert.deepEqual([...LYRIC_SEPARATORS].sort(), ['-', '_', '–', '—', '‿'])
})

test('leaves plain words whole', () => {
  assert.equal(splitWordAtSeparators(word('Hallelujah')), null)
  assert.equal(splitWordAtSeparators(word('f')), null)
})

test('leaves a word with only a leading or trailing separator whole', () => {
  // Audiveris already splits these itself; pre-splitting would add nothing.
  assert.equal(splitWordAtSeparators(word('Hal—')), null)
  assert.equal(splitWordAtSeparators(word('—le')), null)
  assert.equal(splitWordAtSeparators(word('—')), null)
  assert.equal(splitWordAtSeparators(word('-')), null)
})

test('leaves a word whole when its symbols do not match its text', () => {
  const w = word('Hal—le')
  w.symbols = w.symbols.slice(0, 3) // symbols no longer concatenate to the text
  assert.equal(splitWordAtSeparators(w), null)
  const noSymbols = { text: 'Hal—le', confidence: 90, bbox: { x0: 0, y0: 0, x1: 60, y1: 20 } }
  assert.equal(splitWordAtSeparators(noSymbols), null)
})

test('splits a hyphenated non-lyric word the same way Audiveris would', () => {
  // The split mirrors Audiveris's own separator split, so it applies to any
  // hyphenated word; Audiveris drops the separator either way.
  const pieces = splitWordAtSeparators(word('BY-NC-SA'))
  assert.deepEqual(pieces.map(p => p.text), ['BY', 'NC', 'SA'])
})
