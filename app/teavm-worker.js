// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reads a score with Audiveris in WebAssembly (teavm.js), away from the page: each page is a
// minute or more of work that can't be interrupted, which would freeze the page.
//
// The page sends { pages, constants, languages, deblur } and gets back, as they come:
//   { log }               a line Audiveris printed
//   { step: [page, id] }  a step of a page starts (page 0: the export)
//   { ocr, id }           an image whose words the page should read (ocr.js); it answers { id, text }
//   { done }              { scores, failed }, as readScore returns them
//   { error }             the reading failed
// `deblur` is the pages the quick look warned about (reader.js): they are sharpened first
// (deblur.js), in this worker, before Audiveris reads them.

import { readScore } from './teavm.js'
import { loadDeblur } from './deblur.js'

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
    // Sharpen the warned pages first (deblur.js): a page the quick look flagged as blurred
    // reads far better sharpened, and the sharpening only ever runs on flagged pages. A page
    // that fails to sharpen is read as it was, so a deblur failure can't lose a page; if the
    // module itself can't load (an old dist/), every page is read as it was.
    if (data.deblur?.length) {
      let deblur = null
      try {
        deblur = await loadDeblur(load, new URL('teavm/deblur/classes.wasm', import.meta.url).href)
      } catch (e) {
        console.warn('The sharpening module could not load, reading the pages as they were:', e)
      }
      for (const i of data.deblur) {
        const page = data.pages[i]
        if (!page || !deblur) continue
        postMessage({ log: `Sharpening page ${i + 1} before the read (it looked blurred)…` })
        try {
          page.grey = await deblur(page.grey, page.w, page.h)
        } catch (e) {
          console.warn(`Sharpening page ${i + 1} failed, reading it as it was:`, e)
        }
      }
    }
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
