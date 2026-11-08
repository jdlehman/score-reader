// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Unit tests for app/preflight.js. No browser, no fixtures: pages are drawn here, as grey
// pixels, so each case controls exactly what the detector sees.
//   node test/preflight.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { binarise, detectStaves, preflight, rotate } from '../app/preflight.js'

// A deterministic PRNG, so the noise cases are the same every run.
function rng(seed) {
  let s = seed >>> 0
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32
}

/** A white page with `count` five-line staves, spacing `sp` px, first staff top at `y0`. */
function makePage({ w = 1200, h = 1600, count = 4, sp = 20, y0 = 120, gap = 120, line = 2 } = {}) {
  const grey = new Uint8Array(w * h).fill(255)
  const tops = []
  for (let s = 0; s < count; s++) {
    const top = y0 + s * (4 * sp + gap)
    tops.push(top)
    for (let k = 0; k < 5; k++) {
      const y = top + k * sp
      for (let yy = y; yy < y + line; yy++) for (let x = 40; x < w - 40; x++) grey[yy * w + x] = 0
    }
  }
  return { grey, w, h, tops }
}

test('clean page: finds the right staves, no warning', () => {
  const { grey, w, h } = makePage({ count: 4 })
  const v = preflight(grey, w, h)
  assert.equal(v.staves.length, 4)
  assert.equal(v.angleDeg, 0)
  assert.ok(v.confidence > 0.5, `confidence ${v.confidence}`)
  assert.equal(v.warnRescan, false)
})

test('tilted page: staves found only with the deskew search', () => {
  const { grey, w, h } = makePage({ count: 4 })
  const tilted = rotate(grey, w, h, 3)
  // without deskew, a 3-degree tilt spreads each staff line over ~60 rows and the
  // row projection finds nothing
  assert.equal(detectStaves(binarise(tilted), w, h).length, 0)
  const v = preflight(tilted, w, h)
  assert.equal(v.staves.length, 4)
  assert.ok(Math.abs(Math.abs(v.angleDeg) - 3) <= 1, `angle ${v.angleDeg}`)
  assert.equal(v.warnRescan, false)
})

test('blank page: no staves, warns', () => {
  const grey = new Uint8Array(1200 * 1600).fill(255)
  const v = preflight(grey, 1200, 1600)
  assert.equal(v.staves.length, 0)
  assert.equal(v.confidence, 0)
  assert.equal(v.warnRescan, true)
})

test('noise-only page: no staves, warns', () => {
  const r = rng(7)
  const grey = new Uint8Array(1200 * 1600)
  for (let i = 0; i < grey.length; i++) grey[i] = r() < 0.05 ? 0 : 255
  const v = preflight(grey, 1200, 1600)
  assert.equal(v.staves.length, 0)
  assert.equal(v.warnRescan, true)
})

test('one-staff and three-staff pages do not warn on count alone', () => {
  for (const count of [1, 3]) {
    const { grey, w, h } = makePage({ count })
    const v = preflight(grey, w, h)
    assert.equal(v.staves.length, count)
    assert.equal(v.warnRescan, false)
  }
})

test('low confidence warns even when staves are found', () => {
  // staves at the top, and a dense block of ink below them: most of the page's ink is
  // off the staves, so confidence falls below 0.5
  const { grey, w, h } = makePage({ count: 2, y0: 100, gap: 60 })
  const r = rng(11)
  for (let y = 700; y < h; y++) for (let x = 0; x < w; x++) if (r() < 0.5) grey[y * w + x] = 0
  const v = preflight(grey, w, h)
  assert.equal(v.staves.length, 2)
  assert.ok(v.confidence < 0.5, `confidence ${v.confidence}`)
  assert.equal(v.warnRescan, true)
})

test('dense orchestral page: warns never on count, exact count not asserted', () => {
  // 22 staves, as on the Beethoven 9 finale scan: counting is known unreliable on real
  // pages (preflight found 16/22 there), so this asserts only that a dense page of music
  // does not warn — never an exact staff count.
  const { grey, w, h } = makePage({ w: 1600, h: 2600, count: 22, sp: 14, y0: 80, gap: 44, line: 2 })
  const v = preflight(grey, w, h)
  assert.ok(v.staves.length > 0, `found ${v.staves.length} staves`)
  assert.equal(v.warnRescan, false)
})
