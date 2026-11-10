// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The quick look before a read (app/preflight.js), on pages drawn here as grey pixels.
//   node --test test/preflight.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MIN_SPACING, preflight } from '../app/preflight.js'

/** A deterministic random number generator, so the noisy pages are the same every run. */
function random(seed) {
  let s = seed >>> 0
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32
}

/**
 * A page of `count` five-line staves `spacing` apart. `bend(x, y)` moves each line's pixels down
 * (a tilt or a perspective); the paper spans `paper` (x0, x1) on a `table` grey background.
 */
function page({ w = 1200, h = 1600, count = 4, spacing = 20, bend = () => 0, paper = [0, 1200], table = 255, ink = 30 } = {}) {
  const grey = new Uint8Array(w * h).fill(table)
  for (let y = 0; y < h; y++) for (let x = paper[0]; x < paper[1]; x++) grey[y * w + x] = 235
  const top = 150, gap = 6 * spacing
  for (let s = 0; s < count; s++) for (let k = 0; k < 5; k++) {
    const y0 = top + s * (4 * spacing + gap) + k * spacing
    for (let x = paper[0] + 60; x < paper[1] - 60; x++) {
      const y = Math.round(y0 + bend(x, y0))
      for (const yy of [y, y + 1]) if (yy >= 0 && yy < h) grey[yy * w + x] = ink
    }
  }
  return [grey, w, h]
}

test('a clean page: its staves and their spacing, no warning', () => {
  const v = preflight(...page())
  assert.equal(v.warn, null)
  assert.equal(v.staves, 4)
  assert.ok(Math.abs(v.spacing - 20) <= 1, `spacing ${v.spacing}`)
})

test('a page tilted by 3°', () => {
  const v = preflight(...page({ bend: x => (x - 600) * Math.tan(3 * Math.PI / 180) }))
  assert.equal(v.warn, null)
  assert.equal(v.staves, 4)
})

test('a photo’s perspective: lines tilt one way on the left and the other on the right', () => {
  const v = preflight(...page({ bend: x => ((x - 600) ** 2) / 12000 }))
  assert.equal(v.warn, null)
})

test('a page on a dark table, with a shadow across it', () => {
  const [grey, w, h] = page({ paper: [200, 1000], table: 70 })
  for (let y = 0; y < h; y++) for (let x = 200; x < 1000; x++) if (y > 900) grey[y * w + x] = Math.round(grey[y * w + x] * 0.55)
  const v = preflight(grey, w, h)
  assert.equal(v.warn, null)
  assert.equal(v.staves, 4)
})

test('one staff is enough', () => {
  assert.equal(preflight(...page({ count: 1 })).warn, null)
})

test('a blank page: no staves', () => {
  const v = preflight(...page({ count: 0 }))
  assert.equal(v.warn, 'no-staves')
  assert.equal(v.spacing, 0)
})

test('noise: no staves', () => {
  const r = random(7)
  const grey = new Uint8Array(1200 * 1600).map(() => (r() < 0.2 ? 0 : 255))
  assert.equal(preflight(grey, 1200, 1600).warn, 'no-staves')
})

test(`staff lines under ${MIN_SPACING} pixels apart: too small for Audiveris`, () => {
  const v = preflight(...page({ spacing: 7, count: 8 }))
  assert.equal(v.warn, 'too-small')
  assert.ok(v.spacing < MIN_SPACING)
})

test('a big page is looked at shrunk, but its spacing is in its own pixels', () => {
  const v = preflight(...page({ w: 3000, h: 4000, spacing: 40 }))
  assert.equal(v.warn, null)
  assert.ok(Math.abs(v.spacing - 40) <= 2, `spacing ${v.spacing}`)
})
