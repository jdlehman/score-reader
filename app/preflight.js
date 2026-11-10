// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A quick look at each photo or scanned page before the read: can Audiveris find its staves?
//
// A read takes a minute or more a page and can't restart without reloading the page, so the page
// warns first when Audiveris would give up anyway. It gives up on a page in two ways:
//   - it finds no staves (a blank page, the wrong photo, a blurred or washed-out one): "No
//     regularly spaced lines found";
//   - the staff lines are too close together, under 11 pixels apart (ScaleBuilder.minInterline):
//     "too low interline value", from a small photo or a page taken from too far away.
//
// How: each pixel is ink if it is clearly darker than its neighbourhood, so a dark table around
// the page or a shadow across it doesn't count. The page is cut into narrow vertical strips, and
// each strip gets its own tilt, since a photo's perspective tilts the lines differently across the
// page. In each strip, rows mostly of ink are staff lines, and five evenly spaced lines a staff.
//
// Measured on midi_studio's recognition test (spike/omr): all 20 phone photos and all scans and
// clean pages pass, and so does the hymnal; a blank page warns. Photos shrunk to 1000 pixels wide
// warn that the staves are too small, and Audiveris does reject them. About 0.3 s a page.

/** Audiveris's smallest staff line spacing, in pixels (ScaleBuilder.minInterline). */
export const MIN_SPACING = 11

/** Shrink by a whole factor so the longer side is at most `max`, averaging each block. */
function shrink(grey, w, h, max) {
  const f = Math.max(1, Math.ceil(Math.max(w, h) / max))
  if (f === 1) return { grey, w, h, f }
  const w2 = Math.floor(w / f), h2 = Math.floor(h / f)
  const out = new Uint8Array(w2 * h2)
  for (let y = 0; y < h2; y++) for (let x = 0; x < w2; x++) {
    let sum = 0
    for (let dy = 0; dy < f; dy++) {
      const row = (y * f + dy) * w + x * f
      for (let dx = 0; dx < f; dx++) sum += grey[row + dx]
    }
    out[y * w2 + x] = sum / (f * f)
  }
  return { grey: out, w: w2, h: h2, f }
}

/** 1 where a pixel is clearly darker than the mean of the (2r+1)² around it (Bradley's method). */
function ink(grey, w, h, r, t = 0.15) {
  const W = w + 1
  const sums = new Float64Array(W * (h + 1))
  for (let y = 0; y < h; y++) {
    let row = 0
    for (let x = 0; x < w; x++) {
      row += grey[y * w + x]
      sums[(y + 1) * W + x + 1] = sums[y * W + x + 1] + row
    }
  }
  const out = new Uint8Array(w * h)
  for (let y = 0; y < h; y++) {
    const y0 = Math.max(0, y - r), y1 = Math.min(h, y + r + 1)
    for (let x = 0; x < w; x++) {
      const x0 = Math.max(0, x - r), x1 = Math.min(w, x + r + 1)
      const sum = sums[y1 * W + x1] - sums[y0 * W + x1] - sums[y1 * W + x0] + sums[y0 * W + x0]
      if (grey[y * w + x] * (x1 - x0) * (y1 - y0) < sum * (1 - t)) out[y * w + x] = 1
    }
  }
  return out
}

/** The staves in a strip's line centres: five lines in a row, evenly spaced. Their spacings. */
function staves(centres, maxSpacing) {
  const found = []
  for (let i = 0; i + 4 < centres.length;) {
    const ys = centres.slice(i, i + 5)
    const gaps = ys.slice(1).map((y, k) => y - ys[k])
    const spacing = (ys[4] - ys[0]) / 4
    if (spacing >= 2 && spacing <= maxSpacing && Math.max(...gaps) < 1.35 * Math.min(...gaps)) {
      found.push(spacing)
      i += 5
    } else i++
  }
  return found
}

/** The staves Audiveris would find in one strip of the page, at the strip's best tilt. */
function stripStaves(marks, w, h, x0, width) {
  const xc = x0 + width / 2
  let best = null
  for (let k = -10; k <= 10; k++) { // tilts of up to 0.1 (about 6°)
    const slope = k / 100
    const rows = new Float64Array(h)
    for (let x = x0; x < x0 + width; x++) {
      const dy = Math.round((x - xc) * slope)
      for (let y = Math.max(0, -dy), end = Math.min(h, h - dy); y < end; y++) rows[y] += marks[(y + dy) * w + x]
    }
    let sharpness = 0
    for (let y = 0; y < h; y++) sharpness += rows[y] * rows[y]
    if (!best || sharpness > best.sharpness) best = { sharpness, rows }
  }
  // rows mostly of ink are a line; a few touching rows are one line
  const centres = []
  for (let y = 0, start = -1; y <= h; y++) {
    const on = y < h && best.rows[y] > 0.6 * width
    if (on && start < 0) start = y
    if (!on && start >= 0) {
      if (y - start <= 4) centres.push((start + y - 1) / 2)
      start = -1
    }
  }
  return staves(centres, h / 40)
}

/**
 * Look at a page's grey pixels (one byte a pixel). Returns `{ warn, staves, spacing }`: `warn` is
 * null, 'no-staves' or 'too-small'; `staves` is how many staves a typical strip found; `spacing`
 * is the typical staff line spacing in the page's own pixels (0 if none).
 */
export function preflight(grey, w, h, { strips = 12 } = {}) {
  const page = shrink(grey, w, h, 2400)
  const marks = ink(page.grey, page.w, page.h, Math.max(4, Math.round(Math.max(page.w, page.h) / 80)))
  const width = Math.floor(page.w / strips)
  const counts = [], spacings = []
  for (let s = 0; s < strips; s++) {
    const found = stripStaves(marks, page.w, page.h, s * width, width)
    if (found.length) counts.push(found.length)
    spacings.push(...found)
  }
  const median = list => list.length ? [...list].sort((a, b) => a - b)[Math.floor(list.length / 2)] : 0
  const spacing = Math.round(median(spacings) * page.f * 10) / 10
  // a staff in a few strips only is likely a table edge or a line of text, not music
  const warn = counts.length < 3 ? 'no-staves' : spacing < MIN_SPACING ? 'too-small' : null
  return { warn, staves: median(counts), spacing }
}
