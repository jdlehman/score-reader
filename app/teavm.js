// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Reading pages with Audiveris built for WebAssembly by TeaVM (teavm/build.sh), which needs no
// Java in the browser. The same code runs in the page's worker (teavm-worker.js) and in Node
// (teavm/node/read.mjs, which the tests use), so what is tested is what the page runs.
//
// Each page is read in two calls into Audiveris (see teavm/entry/src/teavm/TeavmMain.java): up to
// its words, and the rest. In between, ocr() reads the words: Tesseract is asynchronous, and a call
// into WebAssembly can't wait for it.

/**
 * Read a score.
 * @param {object} o
 * @param {object} o.teavm    the loaded module: `await load(wasm)` from TeaVM's runtime.mjs
 * @param {{w: number, h: number, grey: Uint8Array}[]} o.pages  each page's grey pixels, a byte each
 * @param {string[]} o.constants  Audiveris settings, as 'name=value' (settings.js)
 * @param {string} [o.languages]  the words' language(s), as Tesseract names them ('deu', 'eng+lat')
 * @param {(image: {grey: Uint8Array, width: number, height: number, languages: string, pageSegMode: number}) => Promise<string>} [o.ocr]
 *   reads the words in an image, answering BrowserOCR's lines (ocr.js readText); without it, no words
 * @param {(family: string, size: number) => Uint8Array | null} o.templates  the note-head templates
 *   for a music font and point size (teavm/build.sh writes them, a file each), or null; asked for
 *   in the middle of a page, so it must answer at once (a worker can fetch synchronously)
 * @param {(page: number, step: string) => void} [o.onStep]  as each step of a page starts (page 0: the export)
 * @returns {Promise<{scores: string[], failed: number[]}>} the MusicXML of each score (a movement
 *   each), and the pages that couldn't be read (left out)
 */
export async function readScore({ teavm, pages, constants, languages = '', ocr, templates, onStep }) {
  const java = teavm.exports
  globalThis.__teavmStep = (page, step) => onStep?.(page, step)
  globalThis.__teavmTemplates = (family, size) => {
    const bytes = templates(family, size)
    return bytes ? toBase64(bytes) : null
  }
  java.main([])
  for (const c of constants) {
    const i = c.indexOf('=')
    java.setConstant(c.slice(0, i), c.slice(i + 1))
  }
  java.openBook(pages.length, languages)
  const failed = []
  for (let i = 0; i < pages.length; i++) {
    const n = i + 1
    const page = pages[i]
    globalThis.__greyB64 = toBase64(page.grey)
    globalThis.__greyW = page.w
    globalThis.__greyH = page.h
    let ok = call(() => java.startPage(n))
    globalThis.__greyB64 = null
    if (!ok) {
      failed.push(n)
      continue
    }
    let text = ''
    if (ocr && globalThis.__ocrImageB64) {
      try {
        text = await ocr({
          grey: fromBase64(globalThis.__ocrImageB64),
          width: globalThis.__ocrImageW,
          height: globalThis.__ocrImageH,
          languages: globalThis.__ocrLang || languages || 'eng',
          pageSegMode: globalThis.__ocrPsm,
        })
      } catch (e) {
        console.warn(`The words on page ${n} couldn’t be read, so they are left out:`, e)
      }
    }
    globalThis.__ocrText = text
    ok = call(() => java.finishPage(n))
    if (!ok) failed.push(n)
  }
  const list = JSON.parse(java.scores())
  const utf8 = new TextDecoder()
  return { scores: list.map(b64 => utf8.decode(fromBase64(b64))), failed }
}

/** A call into Audiveris; false if it failed past what Audiveris catches (a WebAssembly trap). */
function call(f) {
  try {
    return f()
  } catch (e) {
    console.warn('WARN Audiveris failed on a page, which is left out:', e)
    return false
  }
}

function toBase64(bytes) {
  if (typeof Buffer !== 'undefined') return Buffer.from(bytes.buffer, bytes.byteOffset, bytes.length).toString('base64')
  let s = ''
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000))
  return btoa(s)
}

function fromBase64(text) {
  if (typeof Buffer !== 'undefined') return new Uint8Array(Buffer.from(text, 'base64'))
  const s = atob(text)
  const bytes = new Uint8Array(s.length)
  for (let i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i)
  return bytes
}
