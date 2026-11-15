// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The deblur pre-step (app/deblur.js) on a page drawn here as grey pixels, blurred in the test.
//   node --test test/deblur.test.mjs
// Needs the built module (.work/teavm/deblur-out/classes.wasm from ./build.sh); skips without it.
// Node 24 runs the TeaVM WasmGC module without extra flags.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { loadDeblur } from '../app/deblur.js'

// the TeaVM runtime's load takes a filesystem path, not a file:// URL (see teavm/node/read.mjs)
const wasmPath = fileURLToPath(new URL('../.work/teavm/deblur-out/classes.wasm', import.meta.url))
const runtimeUrl = new URL('../teavm/runtime.mjs', import.meta.url).href

/** A 96x96 page: white paper, three black vertical bars (staff lines seen side-on). */
function bars() {
  const w = 96, h = 96, grey = new Uint8Array(w * h).fill(235)
  for (const x0 of [20, 48, 76]) for (let y = 10; y < 86; y++) for (let x = x0; x < x0 + 2; x++) grey[y * w + x] = 30
  return [grey, w, h]
}

/** Blur with a separable [1,4,6,4,1]/16 kernel, twice (about a Gaussian sigma 1.8 blur). */
function blur(grey, w, h) {
  const k = [1 / 16, 4 / 16, 6 / 16, 4 / 16, 1 / 16]
  let src = Float32Array.from(grey), dst = new Float32Array(w * h)
  for (let pass = 0; pass < 2; pass++) {
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let s = 0
      for (let j = -2; j <= 2; j++) s += k[j + 2] * src[y * w + Math.min(w - 1, Math.max(0, x + j))]
      dst[y * w + x] = s
    }
    ;[src, dst] = [dst, src]
  }
  return Uint8Array.from(src, v => Math.max(0, Math.min(255, Math.round(v))))
}

/** Steepest horizontal step across the first bar's left edge, mid-page. */
function edge(grey, w) {
  const y = 48
  let m = 0
  for (let x = 14; x < 28; x++) m = Math.max(m, Math.abs(grey[y * w + x + 1] - grey[y * w + x]))
  return m
}

test('deblur sharpens a blurred page', async t => {
  if (!existsSync(wasmPath)) t.skip('build the reader first (./build.sh): no .work/teavm/deblur-out/classes.wasm')
  const { load } = await import(runtimeUrl)
  const deblur = await loadDeblur(load, wasmPath)
  const [grey, w, h] = bars()
  const blurred = blur(grey, w, h)
  assert.ok(edge(blurred, w) < edge(grey, w), 'the fixture is blurred first')
  const out = await deblur(blurred, w, h, { sigma: 1.8, iters: 5 })
  assert.equal(out.length, blurred.length)
  assert.ok(out.every(v => v >= 0 && v <= 255))
  assert.ok(edge(out, w) > edge(blurred, w), `edge steepens after deblur (${edge(blurred, w)} -> ${edge(out, w)})`)
  assert.notDeepEqual(out, blurred)
})

test('deblur is deterministic', async t => {
  if (!existsSync(wasmPath)) t.skip('build the reader first (./build.sh): no .work/teavm/deblur-out/classes.wasm')
  const { load } = await import(runtimeUrl)
  const deblur = await loadDeblur(load, wasmPath)
  const [grey, w, h] = bars()
  const blurred = blur(grey, w, h)
  const a = await deblur(blurred, w, h, { sigma: 1.8, iters: 2 })
  const b = await deblur(blurred, w, h, { sigma: 1.8, iters: 2 })
  assert.deepEqual(a, b)
})
