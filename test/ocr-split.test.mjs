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

test('splits a joined lyric word after each separator, keeping it on the syllable before', () => {
  const pieces = splitWordAtSeparators(word('Hal—le—lu—jah,'))
  assert.deepEqual(pieces.map(p => p.text), ['Hal—', 'le—', 'lu—', 'jah,'])
  // each piece's box is its own symbols' box, not the whole word's
  assert.deepEqual(pieces[0].bbox, { x0: 0, y0: 100, x1: 40, y1: 120 })
  assert.deepEqual(pieces[1].bbox, { x0: 40, y0: 100, x1: 70, y1: 120 })
  assert.deepEqual(pieces[3].bbox, { x0: 100, y0: 100, x1: 140, y1: 120 })
})

test('splits at every Audiveris separator', () => {
  for (const sep of ['-', '–', '—', '_', '‿']) assert.deepEqual(splitWordAtSeparators(word(`a${sep}b`)).map(p => p.text), [`a${sep}`, 'b'])
  assert.deepEqual([...LYRIC_SEPARATORS].sort(), ['-', '_', '–', '—', '‿'])
})

test('leaves plain words, lone separators, and a leading or trailing one whole', () => {
  for (const w of ['Hallelujah', 'f', '—', '-', 'Hal—', '—le', '——']) assert.equal(splitWordAtSeparators(word(w)), null, w)
})

test('keeps a run of separators together, and a leading one with its syllable', () => {
  assert.deepEqual(splitWordAtSeparators(word('a--b')).map(p => p.text), ['a--', 'b'])
  assert.deepEqual(splitWordAtSeparators(word('—le—lu')).map(p => p.text), ['—le—', 'lu'])
})

test('leaves a word whole when its symbols do not spell its text', () => {
  const w = word('Hal—le')
  w.symbols = w.symbols.slice(0, 3)
  assert.equal(splitWordAtSeparators(w), null)
  const noSymbols = { text: 'Hal—le', confidence: 90, bbox: { x0: 0, y0: 0, x1: 60, y1: 20 } }
  assert.equal(splitWordAtSeparators(noSymbols), null)
})

test('leaves a word whole unless every piece has a letter', () => {
  // OCR reads a triplet bracket as text; splitting it cost Lindenbaum a syllable under it
  assert.equal(splitWordAtSeparators(word('|—3—|')), null)
  assert.equal(splitWordAtSeparators(word('(1639-1699)')), null)
  assert.deepEqual(splitWordAtSeparators(word('Jean-Baptiste')).map(p => p.text), ['Jean-', 'Baptiste'])
})
