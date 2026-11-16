// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// TrOMR in WebAssembly (CrispEmbed's deployed build), away from the page: one staff
// crop is ~10-30 seconds of work that can't be interrupted, which would freeze
// the page. This worker only recognises — the page detects the staves, cuts the
// crops, converts the tokens and merges (tromr.js, tromr-convert.js, merge.js).
//
// The page sends { init: { wasmUrl, modelUrl } } and gets { ready: true } back,
// then { recognize: { id, rgba, w, h } } per crop and gets { id, text, ms }.
// Any failure comes back as { error } (or { id, error } for one crop).
//
// The module is CrispEmbed's Emscripten build (crispembed_ocr.js, a UMD file),
// loaded with importScripts; the .wasm and the model arrive as bytes, so the
// worker never fetches by path and the module never touches the network.

importScripts('tromr/crispembed_ocr.js')

let module = null
let ctx = 0

async function fetchBytes(url, what) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`TrOMR's ${what} could not be downloaded (${res.status})`)
  return res.arrayBuffer()
}

async function init({ wasmUrl, modelUrl }) {
  const [wasmBinary, modelBytes] = await Promise.all([
    fetchBytes(wasmUrl, 'reader'),
    fetchBytes(modelUrl, 'model'),
  ])
  module = await CrispEmbedOCR({
    wasmBinary,
    printErr: s => { /* the engine's own chatter stays out of the page's log */ },
  })
  module.FS.writeFile('/model.gguf', new Uint8Array(modelBytes))
  ctx = module.ccall('wasm_ocr_init', 'number', ['string', 'number'], ['/model.gguf', 1])
  if (!ctx) throw new Error('TrOMR could not start (the model did not load)')
}

function recognize(rgba, w, h) {
  if (!module || !ctx) throw new Error('TrOMR is not started yet')
  const ptr = module._malloc(rgba.length)
  const lenPtr = module._malloc(4)
  try {
    module.HEAPU8.set(rgba, ptr)
    const t0 = Date.now()
    const strPtr = module.ccall('wasm_ocr_recognize_copy', 'number',
      ['number', 'number', 'number', 'number', 'number', 'number'],
      [ctx, ptr, w, h, 4, lenPtr])
    const ms = Date.now() - t0
    const text = strPtr ? module.UTF8ToString(strPtr) : ''
    if (strPtr) module._free(strPtr)
    return { text, ms }
  } finally {
    module._free(ptr)
    module._free(lenPtr)
  }
}

onmessage = async ({ data }) => {
  try {
    if (data.init) {
      await init(data.init)
      postMessage({ ready: true })
    } else if (data.recognize) {
      const { text, ms } = recognize(data.recognize.rgba, data.recognize.w, data.recognize.h)
      postMessage({ id: data.recognize.id, text, ms })
    }
  } catch (e) {
    postMessage({ id: data.recognize?.id, error: e?.message || String(e) })
  }
}
