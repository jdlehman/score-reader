// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Tests for the staff detector and cropper (app/staves.js), on pages drawn in code:
// five-line staves are black rows on white, at known positions, so the detector's
// output can be checked to the pixel. No scans are needed, and no real page is
// committed as a fixture.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { detectStaves, cropStaff } from '../app/staves.js'

/**
 * A white page with staves drawn as black rows.
 * @param {number} w page width
 * @param {number} h page height
 * @param {{ y: number, spacing: number, missing?: number | number[], short?: number }[]} staves
 *   y = first line's row, spacing = px between lines; missing = line(s) drawn
 *   at 20% width (below the detector's line threshold); short = one line drawn
 *   at 40% width (a text-like row, not a staff line)
 */
function synthPage(w, h, staves) {
  const grey = new Uint8Array(w * h).fill(255)
  for (const s of staves) {
    const missing = new Set(Array.isArray(s.missing) ? s.missing : s.missing === undefined ? [] : [s.missing])
    for (let k = 0; k < 5; k++) {
      const y = Math.round(s.y + k * s.spacing)
      const frac = missing.has(k) ? 0.2 : s.short === k ? 0.4 : 0.9
      const x1 = Math.trunc(w * 0.05), x2 = Math.trunc(w * (0.05 + frac))
      for (let x = x1; x < x2; x++) grey[y * w + x] = 0
    }
  }
  return { grey, w, h }
}

function close(a, b, tol = 1) {
  assert.ok(Math.abs(a - b) <= tol, `expected ${a} within ${tol} of ${b}`)
}

test('one staff: five lines at the drawn positions, spacing as drawn', () => {
  const { grey, w, h } = synthPage(800, 1000, [{ y: 200, spacing: 12 }])
  const staves = detectStaves(grey, w, h)
  assert.equal(staves.length, 1)
  assert.equal(staves[0].lines.length, 5)
  staves[0].lines.forEach((line, k) => close(line, 200 + k * 12))
  close(staves[0].spacing, 12)
  close(staves[0].y0, 200 - 2.5 * 12)
  close(staves[0].y1, 200 + 4 * 12 + 2.5 * 12)
})

test('two systems of two staves: four staves, top to bottom', () => {
  const { grey, w, h } = synthPage(800, 1200, [
    { y: 100, spacing: 12 }, { y: 200, spacing: 12 },
    { y: 600, spacing: 12 }, { y: 700, spacing: 12 },
  ])
  const staves = detectStaves(grey, w, h)
  assert.equal(staves.length, 4)
  staves.forEach((s, i) => close(s.lines[0], [100, 200, 600, 700][i]))
})

test('a short text-like row between staves is not a staff', () => {
  // A 40%-wide dark row 60 px below the first staff: the classic detector would
  // take it for a line; the pair-candidate one needs a full 5-line group.
  const page = synthPage(800, 1000, [{ y: 200, spacing: 12 }, { y: 400, spacing: 12 }])
  const { grey, w, h } = page
  for (let x = 40; x < 360; x++) grey[260 * w + x] = 0
  const staves = detectStaves(grey, w, h)
  assert.equal(staves.length, 2)
  close(staves[0].lines[0], 200)
  close(staves[1].lines[0], 400)
})

test('one missing line is interpolated and the staff is still found', () => {
  const { grey, w, h } = synthPage(800, 1000, [{ y: 200, spacing: 12, missing: 2 }])
  const staves = detectStaves(grey, w, h)
  assert.equal(staves.length, 1)
  assert.equal(staves[0].lines.length, 5)
  staves[0].lines.forEach((line, k) => close(line, 200 + k * 12, 2))
})

test('two missing lines: the staff is not invented', () => {
  const { grey, w, h } = synthPage(800, 1000, [{ y: 200, spacing: 12, missing: [1, 3] }])
  const staves = detectStaves(grey, w, h)
  assert.equal(staves.length, 0)
})

test('a blank page has no staves', () => {
  const staves = detectStaves(new Uint8Array(800 * 1000).fill(255), 800, 1000)
  assert.deepEqual(staves, [])
})

test('cropStaff: the crop holds the staff, white-padded, pixels copied', () => {
  const { grey, w, h } = synthPage(800, 1000, [{ y: 200, spacing: 12 }])
  const [staff] = detectStaves(grey, w, h)
  const crop = cropStaff(grey, w, h, staff)
  assert.equal(crop.w, 800)
  // The staff's first line (row 200) lands at 200 - y0 in the crop; it is black.
  const lineRow = 200 - crop.y0
  assert.ok(lineRow >= 0 && lineRow < crop.h, `line row ${lineRow} inside crop of height ${crop.h}`)
  const off = (lineRow * crop.w + 100) * 4
  assert.equal(crop.rgba[off], 0)
  assert.equal(crop.rgba[off + 1], 0)
  assert.equal(crop.rgba[off + 2], 0)
  assert.equal(crop.rgba[off + 3], 255)
  // A row above the staff is white.
  const whiteOff = (Math.max(0, lineRow - 20) * crop.w + 100) * 4
  assert.equal(crop.rgba[whiteOff], 255)
  // A narrow page's crop is padded to at most 9:1, never wider.
  assert.ok(crop.w / crop.h <= 9.0 + 1e-9)
})
