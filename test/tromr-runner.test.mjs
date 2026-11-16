// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Tests for the TrOMR runner's driver (app/tromr.js): detection, the worker protocol,
// conversion and the gated merge, end to end — with a stub for the TrOMR module, so no
// 32 MB model is needed. The stub answers with the WASM runner's own outputs for the
// synthetic divisi page, so the merged result must match the focr merge exactly.
// The real module's outputs are checked separately by the local validation script
// (score-reader-spikes/tromr-runner/validate.mjs); live-browser timing is still
// unmeasured and is a check for Jonathan's agent, named in PR_DESCRIPTION.md.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
import { parseXml, divisionsOf, readMxl, invalidSlices } from '../app/merge.js'

const STUB_URL = new URL('./fixtures/tromr-stub/crispembed_ocr.js', import.meta.url)
const WORKER_URL = new URL('../app/tromr-worker.js', import.meta.url)

// How many TrOMR workers have started: a clean read must start none at all.
let workersCreated = 0

// The stub's behaviour, set by the tests before a run: failOn makes the nth
// recognition call throw; failFetch makes the worker's downloads fail.
const stubConfig = { failOn: null, failFetch: false }

/** A fake browser Worker: tromr-worker.js runs in a vm context with self, importScripts
 * (which loads the stub module for crispembed_ocr.js), fetch (which answers with dummy
 * bytes, or a 404 when failFetch is set), and console. The worker's own code is the real
 * file — only the module it loads is stubbed. The two message directions are kept
 * separate: postMessage into the worker calls the context's onmessage (the worker's
 * handler); postMessage out of the worker calls this instance's onmessage (the driver's). */
class FakeWorker {
  constructor(url) {
    workersCreated++
    this.onmessage = null
    this.onerror = null
    const instance = this
    const code = readFileSync(new URL(url).pathname, 'utf8')
    const sandbox = {
      console,
      fetch: async (u) => {
        if (stubConfig.failFetch) return { ok: false, status: 404, arrayBuffer: async () => new ArrayBuffer(0) }
        return { ok: true, arrayBuffer: async () => new ArrayBuffer(8) }
      },
      importScripts: (u) => {
        if (!u.endsWith('crispembed_ocr.js')) throw new Error('stub importScripts: unknown ' + u)
        vm.runInContext(readFileSync(STUB_URL.pathname, 'utf8'), ctx)
      },
      postMessage: (data) => { instance.onmessage?.({ data }) },
    }
    const ctx = vm.createContext(sandbox)
    sandbox.self = ctx // in a real worker self is the global; here it is the context
    ctx.__tromrStub = stubConfig
    this._ctx = ctx
    vm.runInContext(code, ctx)
  }

  postMessage(data) {
    queueMicrotask(() => { this._ctx.onmessage?.({ data }) })
  }

  terminate() {}
}

// tromr.js reads Worker at call time, so the fake must be in place before it is imported.
globalThis.Worker = FakeWorker
const { secondOpinion } = await import('../app/tromr.js')

/** A white page with two staves (one pair), as the divisi Audiveris score expects. */
function divisiPage(staffCount = 2) {
  const w = 800, h = 1000
  const grey = new Uint8Array(w * h).fill(255)
  for (let s = 0; s < staffCount; s++) {
    const y0 = 200 + s * 200
    for (let k = 0; k < 5; k++) {
      const y = y0 + k * 12
      for (let x = 40; x < 760; x++) grey[y * w + x] = 0
    }
  }
  return { grey, w, h }
}

const AUD = await readMxl(readFileSync(new URL('./fixtures/divisi-merge/divisi-audiveris.mxl', import.meta.url)))
const GT = JSON.parse(readFileSync(new URL('./fixtures/divisi-merge/divisi-tuplet.json', import.meta.url), 'utf-8'))

/** A clean score (synthetic): one part, one staff, two bars, every voice adding up. */
const CLEAN_XML = `<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
    </measure>
  </part>
</score-partwise>`

/** Exact pitch per bar (multiset, step+octave) and validity per (bar, voice), as in
 * test/merge.test.mjs's scorer, against the Audiveris score's beats. */
function scoreAgainstGT(xmlText, beats) {
  const root = parseXml(xmlText)
  const pred = []
  for (const part of root.children.filter(c => c.tag === 'part')) {
    for (const meas of part.children.filter(c => c.tag === 'measure')) {
      const bar = parseInt(meas.attrs.number ?? '0', 10)
      for (const n of meas.children.filter(c => c.tag === 'note')) {
        const p = n.children.find(c => c.tag === 'pitch')
        if (!p) continue
        pred.push({ bar, pitch: p.children.find(c => c.tag === 'step')?.text + p.children.find(c => c.tag === 'octave')?.text })
      }
    }
  }
  const gtNotes = GT.parts.flatMap(p => p.notes)
  const byBar = new Map(), pByBar = new Map()
  for (const n of gtNotes) byBar.set(n.bar, [...(byBar.get(n.bar) ?? []), n.pitch])
  for (const n of pred) pByBar.set(n.bar, [...(pByBar.get(n.bar) ?? []), n.pitch])
  let exact = 0
  for (const [bar, g] of byBar) {
    const counts = new Map()
    for (const p of pByBar.get(bar) ?? []) counts.set(p, (counts.get(p) ?? 0) + 1)
    for (const p of g) if ((counts.get(p) ?? 0) > 0) { exact++; counts.set(p, counts.get(p) - 1) }
  }
  let valid = 0, total = 0
  for (const part of root.children.filter(c => c.tag === 'part')) {
    const divs = divisionsOf(part)
    const sums = new Map()
    for (const meas of part.children.filter(c => c.tag === 'measure')) {
      const bar = parseInt(meas.attrs.number ?? '0', 10)
      for (const n of meas.children.filter(c => c.tag === 'note')) {
        if (n.children.some(c => c.tag === 'chord')) continue
        const dur = n.children.find(c => c.tag === 'duration')
        if (!dur) continue
        const voice = parseInt(n.children.find(c => c.tag === 'voice')?.text ?? '1', 10)
        const key = `${bar}:${voice}`
        sums.set(key, (sums.get(key) ?? 0) + parseFloat(dur.text) / divs)
      }
    }
    for (const s of sums.values()) { total++; if (Math.abs(s - beats) < 1e-6) valid++ }
  }
  return { exact, gtTotal: gtNotes.length, valid, total }
}

test('invalidSlices finds the broken bars, and none on a clean score', () => {
  const { invalid, checked } = invalidSlices(AUD)
  assert.equal(checked, 8)
  assert.deepEqual(invalid, [
    { part: 0, bar: 3, staff: 1 },
    { part: 0, bar: 4, staff: 1 },
    { part: 1, bar: 3, staff: 1 },
    { part: 1, bar: 4, staff: 1 },
  ])
  assert.deepEqual(invalidSlices(CLEAN_XML), { invalid: [], checked: 2 })
})

test('end to end: the second opinion merges the divisi bars, as the focr merge does', async () => {
  const progress = []
  const result = await secondOpinion([divisiPage()], AUD, p => progress.push({ ...p }))
  assert.ok(result, 'expected a merged score, not null')
  assert.equal(result.status, 'merged')
  assert.equal(result.report.replaced.length, 2)
  assert.deepEqual(result.report.replaced.map(r => r.bar), [3, 4])
  const s = scoreAgainstGT(result.xml, 4)
  assert.equal(s.exact, 72)
  assert.equal(s.gtTotal, 72)
  assert.equal(s.valid, 12)
  assert.equal(s.total, 16)
  assert.deepEqual(progress.at(-1), { done: 2, total: 2 })
})

test('a clean page skips the second opinion entirely', async () => {
  const before = workersCreated
  const result = await secondOpinion([divisiPage(1)], CLEAN_XML)
  assert.ok(result, 'expected a clean-skip result, not null')
  assert.equal(result.status, 'clean')
  assert.equal(result.xml, CLEAN_XML)
  assert.equal(result.report.replaced.length, 0)
  assert.equal(result.report.kept, 2)
  assert.equal(workersCreated, before, 'no worker started, so no model download and no recognition')
})

test('the manual run works on a clean page', async () => {
  const progress = []
  const before = workersCreated
  const result = await secondOpinion([divisiPage(1)], CLEAN_XML, p => progress.push({ ...p }), { force: true })
  assert.ok(result, 'expected a merged score, not null')
  assert.equal(result.status, 'merged')
  assert.equal(result.report.replaced.length, 0)
  assert.equal(workersCreated, before + 1, 'the forced run starts the worker')
  assert.deepEqual(progress.at(-1), { done: 1, total: 1 })
})

test('determinism: two runs produce byte-identical merged scores', async () => {
  const a = await secondOpinion([divisiPage()], AUD)
  const b = await secondOpinion([divisiPage()], AUD)
  assert.ok(a && b)
  assert.equal(a.xml, b.xml)
})

test('staves that do not line up with the score stay Audiveris-only', async () => {
  const result = await secondOpinion([divisiPage(3)], AUD)
  assert.equal(result, null)
})

test('one staff failing to read leaves that staff as Audiveris read it', async () => {
  stubConfig.failOn = 2 // the bass staff's recognition throws
  try {
    const result = await secondOpinion([divisiPage()], AUD)
    assert.ok(result, 'expected a merged score, not null')
    assert.equal(result.report.replaced.length, 0)
    const s = scoreAgainstGT(result.xml, 4)
    assert.equal(s.exact, 72) // no pitch lost
    assert.equal(s.valid, 10) // the Audiveris score, unchanged
    assert.equal(s.total, 24)
  } finally {
    stubConfig.failOn = null
  }
})

test('the reader failing to start leaves the read as Audiveris read it', async () => {
  stubConfig.failFetch = true // the worker's downloads 404
  try {
    const result = await secondOpinion([divisiPage()], AUD)
    assert.equal(result, null)
  } finally {
    stubConfig.failFetch = false
  }
})
