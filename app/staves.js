// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Find the staves on a page and cut them into the crops TrOMR reads.
//
// A JS port of the spike's robust detector (score-reader-spikes/open_detect.py,
// robust_detect): the same row-projection signal, but the 5-line grouping tolerates
// spurious rows (a beam or a line of text crossing the projection threshold) and one
// missing line. The classic consecutive-5 version (run_tromr.detect_staves) misses a
// staff on the Gute Nacht page (5 of 6 — it merges the second system's piano staves);
// this one finds all 6, and the same 6 the focr validation material was cut with.
// Crops follow run_tromr.crop_staff exactly (margins + aspect padding), so a crop cut
// here is the crop the spike measured.
//
// Pure: no DOM, runs in Node and in the browser alike. The page hands it the grey
// pixels Audiveris gets (one byte a pixel).

/** A staff line row is dark across at least this fraction of the page width. */
const MIN_LINE_LEN_FRAC = 0.25
/** A candidate staff's line spacing, in pixels, must lie in this range. */
const MIN_SPACING = 5
const MAX_SPACING = 40
/** A predicted line position counts as hit when a centre is this close (px). */
const HIT_TOLERANCE = 3.0
/** A candidate staff's outer lines must be at least this strong (dark-pixel fraction). */
const MIN_STRENGTH = 0.5

/** Mean and population standard deviation of a list. */
function meanStd(xs) {
  const mean = xs.reduce((a, b) => a + b, 0) / xs.length
  const variance = xs.reduce((a, b) => a + (b - mean) ** 2, 0) / xs.length
  return [mean, Math.sqrt(variance)]
}

function median(xs) {
  const sorted = [...xs].sort((a, b) => a - b)
  return sorted[Math.floor(sorted.length / 2)]
}

/** 1 where a pixel is clearly darker than the page (spike's binarise). */
function binarise(grey) {
  let sum = 0
  for (let i = 0; i < grey.length; i++) sum += grey[i]
  const mean = sum / grey.length
  let sq = 0
  for (let i = 0; i < grey.length; i++) sq += (grey[i] - mean) ** 2
  const thr = mean - 0.5 * Math.sqrt(sq / grey.length)
  const cut = Math.max(thr, 180)
  const out = new Uint8Array(grey.length)
  for (let i = 0; i < grey.length; i++) out[i] = grey[i] < cut ? 1 : 0
  return out
}

/** Line-centre rows: rows dark across a large fraction of the width, grouped. */
function lineCentres(binary, w, h) {
  const proj = new Float64Array(h)
  for (let y = 0; y < h; y++) {
    let row = 0
    const base = y * w
    for (let x = 0; x < w; x++) row += binary[base + x]
    proj[y] = row
  }
  const lineRows = []
  for (let y = 0; y < h; y++) if (proj[y] > w * MIN_LINE_LEN_FRAC) lineRows.push(y)
  if (!lineRows.length) return { centres: [], proj }
  const groups = []
  let start = lineRows[0], prev = lineRows[0]
  for (const r of lineRows.slice(1)) {
    if (r - prev > 3) { groups.push([start, prev]); start = r }
    prev = r
  }
  groups.push([start, prev])
  return { centres: groups.map(([a, b]) => (a + b) / 2), proj }
}

/**
 * The staves on a page: [{ y0, y1, spacing, lines }] in top-to-bottom order,
 * where y0/y1 are the staff's bounds (top line minus 2.5 spacings, bottom line plus
 * 2.5) and lines are the five line centres.
 */
export function detectStaves(grey, w, h) {
  const binary = binarise(grey)
  const { centres, proj } = lineCentres(binary, w, h)
  if (!centres.length) return []
  // Strength of each centre row: dark-pixel fraction of the page width. Real staff
  // lines are ~0.84-0.96; lyric/beam rows are ~0.25-0.47.
  const strength = centres.map(c => {
    const lo = Math.max(0, Math.trunc(c) - 2), hi = Math.min(h, Math.trunc(c) + 3)
    let m = 0
    for (let y = lo; y < hi; y++) m = Math.max(m, proj[y])
    return m / w
  })
  const used = new Array(centres.length).fill(false)
  // Candidate staves: pairs (i, j) that could be lines 1 and 5, with >= 4 of the 5
  // predicted positions hit by a centre.
  const cands = []
  for (let i = 0; i < centres.length; i++) {
    if (strength[i] < MIN_STRENGTH) continue
    for (let j = i + 1; j < centres.length; j++) {
      if (strength[j] < MIN_STRENGTH) continue
      const sp = (centres[j] - centres[i]) / 4
      if (!(MIN_SPACING < sp && sp < MAX_SPACING)) continue
      const hits = []
      for (let k = 0; k < 5; k++) {
        const p = centres[i] + k * sp
        for (let c = 0; c < centres.length; c++) {
          if (!used[c] && Math.abs(centres[c] - p) <= HIT_TOLERANCE) { hits.push(c); break }
        }
      }
      if (hits.length < 4) continue
      const ys = hits.map(c => centres[c]).sort((a, b) => a - b)
      const diffs = ys.slice(1).map((y, k) => y - ys[k])
      const [, std] = meanStd(diffs)
      cands.push({ hits: hits.length, std, top: centres[i], hitIdx: hits })
    }
  }
  // Greedy: most hits, then tightest spacing, then topmost.
  cands.sort((a, b) => (b.hits - a.hits) || (a.std - b.std) || (a.top - b.top))
  const staves = []
  for (const cand of cands) {
    if (cand.hitIdx.some(c => used[c])) continue
    const ys = cand.hitIdx.map(c => centres[c]).sort((a, b) => a - b)
    // Fill a missing line by interpolation if only 4 are present.
    if (ys.length === 4) {
      const diffs = ys.slice(1).map((y, k) => y - ys[k])
      const sp = median(diffs)
      let filled = false
      for (let k = 0; k < diffs.length; k++) {
        if (diffs[k] > 1.6 * sp) { ys.splice(k + 1, 0, ys[k] + sp); filled = true; break }
      }
      if (!filled) {
        if (ys[0] - sp > 0) ys.unshift(ys[0] - sp)
        else ys.push(ys[ys.length - 1] + sp)
      }
    }
    if (ys.length !== 5) continue
    const diffs = ys.slice(1).map((y, k) => y - ys[k])
    const [sp, std] = meanStd(diffs)
    if (!(MIN_SPACING < sp && sp < MAX_SPACING && std < 3.0)) continue
    for (const c of cand.hitIdx) used[c] = true
    staves.push({
      y0: Math.trunc(ys[0] - 2.5 * sp),
      y1: Math.trunc(ys[ys.length - 1] + 2.5 * sp),
      spacing: sp,
      lines: ys,
    })
  }
  staves.sort((a, b) => a.y0 - b.y0)
  return staves
}

/**
 * Cut one staff out of the page as RGBA pixels (what the TrOMR module reads):
 * the staff with ~1.2 spacings above and ~1.5 below, padded with white to an
 * aspect ratio of at most 9 (TrOMR rejects wider crops). Returns
 * { rgba, w, h, y0, y1 }: h is the padded height, y0/y1 the unpadded crop box.
 */
export function cropStaff(grey, w, h, staff) {
  const y0 = Math.max(0, staff.y0 - Math.trunc(1.2 * staff.spacing))
  const y1 = Math.min(h, staff.y1 + Math.trunc(1.5 * staff.spacing))
  const ch = y1 - y0
  let outH = ch
  let topPad = 0
  if (w / ch > 9.0) {
    const need = Math.trunc(w / 9.0) - ch
    outH = ch + need
    topPad = Math.floor(need / 2)
  }
  const rgba = new Uint8Array(w * outH * 4).fill(255)
  for (let y = 0; y < ch; y++) {
    const srcRow = (y0 + y) * w
    const dstRow = (topPad + y) * w * 4
    for (let x = 0; x < w; x++) {
      const g = grey[srcRow + x]
      const o = dstRow + x * 4
      rgba[o] = g
      rgba[o + 1] = g
      rgba[o + 2] = g
      // alpha stays 255
    }
  }
  return { rgba, w, h: outH, y0, y1 }
}
