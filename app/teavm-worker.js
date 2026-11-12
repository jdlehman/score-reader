// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reads a score with Audiveris in WebAssembly (teavm.js), away from the page: each page is a
// minute or more of work that can't be interrupted, which would freeze the page.
//
// The page sends { pages, constants, languages } and gets back, as they come:
//   { log }               a line Audiveris printed
//   { step: [page, id] }  a step of a page starts (page 0: the export)
//   { ocr, id }           an image whose words the page should read (ocr.js); it answers { id, text }
//   { done }              { scores, failed }, as readScore returns them
//   { error }             the reading failed

import { readScore } from './teavm.js'

// Audiveris prints to the console: the page shows it, and learns from it which pages failed
for (const level of ['log', 'info', 'warn', 'error']) {
  const original = console[level].bind(console)
  console[level] = (...args) => {
    postMessage({ log: args.map(a => (a instanceof Error ? a.stack || a.message : String(a))).join(' ') })
    original(...args)
  }
}

const waiting = new Map() // OCR requests the page hasn't answered yet, by id
let nextId = 0

onmessage = async ({ data }) => {
  if ('text' in data) {
    waiting.get(data.id)?.(data.text)
    waiting.delete(data.id)
    return
  }
  try {
    const { load } = await import(new URL('teavm/runtime.mjs', import.meta.url).href)
    const teavm = await load(new URL('teavm/classes.wasm', import.meta.url).href)
    const done = await readScore({
      teavm,
      pages: data.pages,
      constants: data.constants,
      languages: data.languages,
      ocr: image => new Promise(resolve => {
        const id = nextId++
        waiting.set(id, resolve)
        postMessage({ ocr: image, id }, [image.grey.buffer])
      }),
      // asked for in the middle of a page, which can't wait: fetched synchronously (a worker may)
      templates: (family, size) => {
        const xhr = new XMLHttpRequest()
        xhr.open('GET', new URL(`teavm/templates/${family}-${size}.bin`, import.meta.url).href, false)
        xhr.responseType = 'arraybuffer'
        xhr.send()
        return xhr.status === 200 ? new Uint8Array(xhr.response) : null
      },
      onStep: (page, step) => postMessage({ step: [page, step] }),
    })
    postMessage({ done })
  } catch (e) {
    postMessage({ error: String(e?.stack || e) })
  }
}
