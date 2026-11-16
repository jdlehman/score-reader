// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// TrOMR as a second opinion on an Audiveris read, in the browser.
//
// Audiveris stays the authority (merge.js): TrOMR reads each staff crop the page
// cuts, its tokens become MusicXML (tromr-convert.js), and the gated merge only
// replaces a measure where Audiveris's own slice is broken and TrOMR's is valid
// with exactly the same pitches. A crop TrOMR fails on simply stays Audiveris —
// the merge skips it — so the second opinion can never lose a page.
//
// The reader (the TrOMR module + a 32 MB model) runs in tromr-worker.js. The
// page detects the staves and cuts the crops itself: detection is ~0.1 s a page
// and the crops are what the worker reads. Staff files go to the merge in
// system order, top-to-bottom staff per system — the same order the spike's
// focr runs produced — so the runner only runs when the staves found across
// the read's pages are exactly systems × pairs; anything else (a missed staff,
// a failed page, several movements) stays Audiveris-only. And it only runs at
// all when the Audiveris score has a duration-invalid (or missing) slice: a
// clean read has nothing for it to fix, so the model is never downloaded for
// it. The check screen's "Run second opinion" button forces a run on demand
// (opts.force), which is the "we think Audiveris might be wrong" path.

import { detectStaves, cropStaff } from './staves.js'
import { tokensToMusicXml } from './tromr-convert.js'
import { mergeMusicXml, barsPerSystem, staffPairs, parseXml, invalidSlices } from './merge.js'

/** The TrOMR reader and model, served with the site (see teavm/tromr-fetch.sh). */
const wasmUrl = new URL('tromr/crispembed_ocr.wasm', import.meta.url).href
const modelUrl = new URL('tromr/tromr-q8_0.gguf', import.meta.url).href

/** Start the TrOMR worker (downloads the reader and the model once). */
export async function loadTromr() {
  const worker = new Worker(new URL('tromr-worker.js', import.meta.url))
  const waiting = new Map()
  let nextId = 0
  let failed = null
  const rejectAll = e => {
    for (const [, cb] of waiting) cb(e)
    waiting.clear()
  }
  worker.onmessage = ({ data }) => {
    if (data.ready) {
      waiting.get('init')?.(null)
      waiting.delete('init')
    } else if (data.error !== undefined) {
      if (data.id === undefined) {
        // The reader itself failed to start: the worker is no good for any crop.
        failed = new Error(data.error)
        rejectAll(failed)
      } else {
        waiting.get(data.id)?.(new Error(data.error))
        waiting.delete(data.id)
      }
    } else if (data.id !== undefined) {
      waiting.get(data.id)?.(null, data)
      waiting.delete(data.id)
    }
  }
  worker.onerror = e => {
    failed = new Error(e.message || 'the TrOMR worker stopped')
    rejectAll(failed)
  }
  const ready = new Promise((resolve, reject) => waiting.set('init', e => (e ? reject(e) : resolve())))
  worker.postMessage({ init: { wasmUrl, modelUrl } })
  await ready
  return {
    /** Read one staff crop's tokens. Rejects when the worker reports a failure. */
    recognize(rgba, w, h) {
      if (failed) return Promise.reject(failed)
      const id = nextId++
      return new Promise((resolve, reject) => {
        waiting.set(id, (e, data) => (e ? reject(e) : resolve(data)))
        worker.postMessage({ recognize: { id, rgba, w, h } }, [rgba.buffer])
      })
    },
    terminate() { worker.terminate() },
  }
}

/**
 * Run the second opinion on one Audiveris movement.
 * @param {{ grey: Uint8Array, w: number, h: number }[]} pages - the read's pages (pdf.js shape)
 * @param {string} audiverisXml - one movement's MusicXML, as Audiveris wrote it
 * @param {(p: { done: number, total: number }) => void} [onProgress] - per staff read
 * @param {{ force?: boolean }} [opts] - force runs on a clean read too (the manual run)
 * @returns {Promise<{ status: 'merged'|'clean', xml: string, report: object } | null>}
 *   'merged' with the merged score, 'clean' when the read has no invalid bars
 *   (the Audiveris score unchanged, and no worker started unless forced), or
 *   null when the second opinion doesn't apply to this read (staves don't line
 *   up with the score's systems, or the reader can't start). Never throws for a
 *   single staff's failure — that staff stays Audiveris.
 */
export async function secondOpinion(pages, audiverisXml, onProgress = () => {}, opts = {}) {
  let root
  try {
    root = parseXml(audiverisXml)
  } catch {
    return null
  }
  const systems = barsPerSystem(root)
  const pairs = staffPairs(root)
  if (!systems.length || !pairs.length) return null
  // Staves first (cheap), before the 32 MB model downloads: the run only happens
  // when the staves found are exactly the score's systems × pairs.
  const perPage = pages.map(p => detectStaves(p.grey, p.w, p.h))
  const total = perPage.reduce((a, s) => a + s.length, 0)
  if (total !== systems.length * pairs.length) return null
  // The trigger: only Audiveris's own uncertainty starts the second reader.
  // A duration-invalid (or missing) slice is the one measurable signal in the
  // output that the merge can fix; a clean read has nothing for it to do, so
  // the model is never downloaded for it. `force` is the manual run.
  const audit = invalidSlices(audiverisXml)
  if (!opts.force && !audit.invalid.length) {
    return { status: 'clean', xml: audiverisXml, report: { replaced: [], kept: audit.checked, skipped: [] } }
  }
  let tromr
  try {
    tromr = await loadTromr()
  } catch (e) {
    console.warn('The second reader could not start, so the read stays as Audiveris read it:', e)
    return null
  }
  try {
    const staffXmls = []
    let done = 0
    for (let pi = 0; pi < pages.length; pi++) {
      for (const staff of perPage[pi]) {
        const crop = cropStaff(pages[pi].grey, pages[pi].w, pages[pi].h, staff)
        let xml = null
        try {
          const { text } = await tromr.recognize(crop.rgba, crop.w, crop.h)
          xml = tokensToMusicXml(text).xml
        } catch (e) {
          console.warn('TrOMR could not read a staff, so it stays as Audiveris read it:', e)
        }
        staffXmls.push(xml)
        onProgress({ done: ++done, total })
      }
    }
    const merged = mergeMusicXml(audiverisXml, staffXmls)
    return { status: 'merged', xml: merged.xml, report: merged.report }
  } finally {
    tromr.terminate()
  }
}
