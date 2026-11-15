// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Sharpen a blurred page before Audiveris reads it: a 3x3 median denoise, then Richardson-Lucy
// deconvolution with a Gaussian PSF, in WebAssembly (teavm/deblur/, built by teavm/deblur-build.sh).
//
// Measured on the 15 synthetic phone-photo pages (see teavm/README.md): with the parameters below,
// Audiveris reads Lindenbaum hard 9 -> 199 exact notes and Gute Nacht hard from no output at all
// to 33 exact, with no loss on any mild or moderate page; Hallelujah hard stays unread. The module
// runs about 15-27 seconds a page in Node (about 2.4 s per megapixel), so it only runs on pages the
// quick look already warned about (preflight.js, warn 'no-staves'), never blindly: the same
// sharpening collapses Hallelujah moderate 200 -> 54 exact notes when it runs at 5 iterations.
//
// The module speaks the same globals protocol as the Audiveris module (teavm.js): the caller passes
// the TeaVM runtime's `load` and the deblur wasm URL, and gets back a function that takes a page's
// grey pixels and returns sharpened ones. It runs in the worker (teavm-worker.js), never on the
// page, and a failure leaves the page's grey untouched.

import { fromBase64, toBase64 } from './teavm.js'

/** The parameters the synthetic-photo spike measured (see teavm/README.md). */
export const DEBLUR_SIGMA = 1.8
export const DEBLUR_ITERS = 15

/**
 * Load the deblur module once.
 * @param {(wasm: string) => Promise<{exports: {main: ([]: never[]) => void}}>} load
 *   the TeaVM runtime's loader (teavm/runtime.mjs)
 * @param {string} wasmUrl  the deblur classes.wasm (teavm/deblur/classes.wasm in dist/)
 * @returns {Promise<(grey: Uint8Array, w: number, h: number, opts?: {sigma?: number, iters?: number}) => Promise<Uint8Array>>}
 *   sharpened grey pixels, a byte each, same size as the input
 */
export async function loadDeblur(load, wasmUrl) {
  const teavm = await load(wasmUrl)
  return async (grey, w, h, { sigma = DEBLUR_SIGMA, iters = DEBLUR_ITERS } = {}) => {
    globalThis.__deblurInput = toBase64(grey)
    globalThis.__deblurW = w
    globalThis.__deblurH = h
    globalThis.__deblurSigma = sigma
    globalThis.__deblurIters = iters
    globalThis.__deblurMedian = 1
    teavm.exports.main([])
    const out = fromBase64(globalThis.__deblurOutput)
    globalThis.__deblurInput = null
    globalThis.__deblurOutput = null
    if (out.length !== grey.length) throw new Error('the deblur returned the wrong size')
    return out
  }
}
