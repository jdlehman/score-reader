// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Photo preflight: before Audiveris spends a minute a page, check the page looks like music.
//
// Runs on the same grey page pdf.js already makes, in parallel with the CheerpJ start. No model,
// no download: binarise, search for the tilt that levels the staff lines, then find the staves
// by row projection. The verdict is a triage signal only: if no staves are found, or the staff
// lines hold little of the page's ink, warn to rescan before committing to a 60-100 s Audiveris
// run that can't restart without a reload. An odd staff count alone is NOT a warning: 1- and
// 3-staff pages are legitimate (single staff, piano + voice).
//
// Measured (2026-11-08, spike harness, Node on this VM — not the browser):
//   clean Verovio hymn, 4 staves: found 4, angle 0, confidence 0.735, ~0.8 s
//   simulated phone photo of the same page: 0 staves at angle 0, all 4 after the deskew search
//     — the angle search is what makes this work on photos at all
//   clean open pages (Schubert Lieder, Handel Hallelujah): never false-warned, confidence
//     0.62-0.76; staff count undercounts on real pages (7/9 Lindenbaum, 16/22 Beethoven scan),
//     so the count is reported but never used to decide anything here
//   synthetic phone photos of the open pages (mild/moderate/hard): warns on the hard ones
//     (e.g. Lindenbaum hard: 2 staves, confidence 0.186; Hallelujah hard: 0 staves), never on
//     the mild ones — the warn path fires where Audiveris itself falls apart (Lindenbaum hard:
//     Audiveris read 70 of 216 notes, 0/5 measures valid, against 172/216 on mild/moderate)
//   Node timing on full-size pages is ~2-3 s; the browser timing is to be confirmed (see NOTES.md)

export function binarise(grey) {
  let mean = 0
  for (let i = 0; i < grey.length; i++) mean += grey[i]
  mean /= grey.length
  let variance = 0
  for (let i = 0; i < grey.length; i++) variance += (grey[i] - mean) ** 2
  const std = Math.sqrt(variance / grey.length)
  const thr = Math.max(mean - 0.5 * std, 180)
  const out = new Uint8Array(grey.length)
  for (let i = 0; i < grey.length; i++) out[i] = grey[i] < thr ? 1 : 0
  return out
}

// Rotate a greyscale image by `deg` (nearest neighbour, white fill). Small angles only;
// used by the deskew search and, in the deskew PR, to straighten the page before Audiveris.
export function rotate(grey, w, h, deg) {
  const rad = (deg * Math.PI) / 180
  const cos = Math.cos(rad), sin = Math.sin(rad)
  const cx = w / 2, cy = h / 2
  const out = new Uint8Array(w * h).fill(255)
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const dx = x - cx, dy = y - cy
      const sx = Math.round(cx + dx * cos + dy * sin)
      const sy = Math.round(cy - dx * sin + dy * cos)
      if (sx >= 0 && sx < w && sy >= 0 && sy < h) out[y * w + x] = grey[sy * w + sx]
    }
  }
  return out
}

// Share of dark pixels in the darkest 40 rows: staff lines concentrate ink into few rows
// when the page is level, and spread it when tilted.
export function levelScore(binary, w, h) {
  const proj = new Float64Array(h)
  let total = 0
  for (let y = 0; y < h; y++) {
    let row = 0
    for (let x = 0; x < w; x++) row += binary[y * w + x]
    proj[y] = row
    total += row
  }
  if (total === 0) return 0
  const sorted = [...proj].sort((a, b) => b - a)
  let top = 0
  for (let i = 0; i < Math.min(40, sorted.length); i++) top += sorted[i]
  return top / total
}

export function detectStaves(binary, w, h, minLineLenFrac = 0.25) {
  const proj = new Float64Array(h)
  for (let y = 0; y < h; y++) {
    let row = 0
    for (let x = 0; x < w; x++) row += binary[y * w + x]
    proj[y] = row
  }
  const lineRows = []
  for (let y = 0; y < h; y++) if (proj[y] > w * minLineLenFrac) lineRows.push(y)
  if (lineRows.length === 0) return []
  // group consecutive rows into line centres
  const groups = []
  let start = lineRows[0], prev = lineRows[0]
  for (const r of lineRows.slice(1)) {
    if (r - prev > 3) { groups.push([start, prev]); start = r }
    prev = r
  }
  groups.push([start, prev])
  const centres = groups.map(([a, b]) => (a + b) / 2)
  // cluster into 5-line staves with near-equal spacing
  const staves = []
  let i = 0
  while (i + 4 < centres.length) {
    const ys = centres.slice(i, i + 5)
    const diffs = ys.slice(1).map((v, k) => v - ys[k])
    const mean = diffs.reduce((a, b) => a + b, 0) / diffs.length
    const std = Math.sqrt(diffs.reduce((a, b) => a + (b - mean) ** 2, 0) / diffs.length)
    if (std < 2.5 && mean > 5 && mean < 40 && Math.max(...diffs) < 1.8 * Math.min(...diffs)) {
      staves.push({ y0: Math.round(ys[0] - 2.5 * mean), y1: Math.round(ys[4] + 2.5 * mean), spacing: +mean.toFixed(1) })
      i += 5
    } else {
      i += 1
    }
  }
  return staves
}

// Halve the image (nearest 2x2 mean) for the angle search: the search is 21 rotations and
// dominates the cost; angles found at half scale transfer to full scale.
export function downscaleHalf(grey, w, h) {
  const w2 = Math.floor(w / 2), h2 = Math.floor(h / 2)
  const out = new Uint8Array(w2 * h2)
  for (let y = 0; y < h2; y++) for (let x = 0; x < w2; x++) {
    const i = (2 * y) * w + 2 * x
    out[y * w2 + x] = Math.round((grey[i] + grey[i + 1] + grey[i + w] + grey[i + w + 1]) / 4)
  }
  return { grey: out, w: w2, h: h2 }
}

export function preflight(grey, w, h) {
  // 1. angle search on a half-scale copy (-5..+5 deg, 0.5 steps), tried in order of
  // increasing |angle| so that angle 0 wins ties: a page whose ink is already level must
  // not be rotated at all. (A tie once picked -0.5 deg on a one-staff page, and rotating
  // by half a degree spread its 2 px staff lines below the detection threshold.)
  const small = downscaleHalf(grey, w, h)
  let best = { angle: 0, score: -1 }
  for (const a of [0, -0.5, 0.5, -1, 1, -1.5, 1.5, -2, 2, -2.5, 2.5, -3, 3, -3.5, 3.5, -4, 4, -4.5, 4.5, -5, 5]) {
    const rot = a === 0 ? small.grey : rotate(small.grey, small.w, small.h, a)
    const s = levelScore(binarise(rot), small.w, small.h)
    if (s > best.score) best = { angle: +a.toFixed(1), score: s }
  }
  // 2. deskew the full-res page once at the best angle, then detect
  const deskewedGrey = best.angle === 0 ? grey : rotate(grey, w, h, best.angle)
  const binary = binarise(deskewedGrey)
  const staves = detectStaves(binary, w, h)
  // 3. confidence: fraction of the page's dark pixels that sit on detected staff lines
  // (a page of music scores high; blank/noise low)
  const lineRows = new Set()
  for (const s of staves) for (let y = s.y0; y <= s.y1; y++) lineRows.add(y)
  let onStaff = 0, total = 0
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (binary[y * w + x]) { total++; if (lineRows.has(y)) onStaff++ }
  }
  const confidence = total ? onStaff / total : 0
  return {
    staves,
    angleDeg: best.angle,
    levelScore: +best.score.toFixed(3),
    confidence: +confidence.toFixed(3),
    // warn when nothing was found, or the staff lines hold little of the page's ink
    // (blank page, wrong side of the paper, heavy blur). An odd staff count alone is NOT
    // a warning: 1- and 3-staff pages are legitimate.
    warnRescan: staves.length === 0 || confidence < 0.5,
    // the deskewed pixels, for the deskew PR to straighten the page with; callers that
    // only need the verdict should drop this (a full-res copy per page).
    deskewedGrey,
  }
}
