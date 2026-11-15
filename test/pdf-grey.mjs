// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A PDF's pages as the grey pixels the page hands Audiveris, drawn by the page's own code
// (app/pdf.js, with PDF.js) in Chrome: for the WebAssembly reader in Node (test/corpus.mjs).
//   node test/pdf-grey.mjs <file.pdf> <radix>
// writes <radix>-p1.grey and <radix>-p1.json (width, height), -p2..., and prints the page count.
// Needs Chrome, and PDF.js in dist/pdfjs/ (./build.sh copies it there).
import { createReadStream, readFileSync, statSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, join, normalize } from 'node:path'
import { chromium } from 'playwright-core'

const [pdf, radix] = process.argv.slice(2)
if (!pdf || !radix) {
  console.error('usage: node test/pdf-grey.mjs <file.pdf> <radix>')
  process.exit(2)
}
const ROOT = join(import.meta.dirname, '..')
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json' }

// the page's code as it is in app/ now, and PDF.js as the page gets it (dist/pdfjs/)
const server = createServer((req, res) => {
  const { pathname } = new URL(req.url, 'http://x')
  if (pathname === '/') return res.writeHead(200, { 'Content-Type': 'text/html' }).end('<!DOCTYPE html><title>pdf</title>')
  const base = join(ROOT, pathname.startsWith('/pdfjs/') ? 'dist' : 'app')
  const path = normalize(join(base, decodeURIComponent(pathname)))
  try {
    if (!path.startsWith(base) || !statSync(path).isFile()) throw new Error()
  } catch {
    return res.writeHead(404).end()
  }
  res.writeHead(200, { 'Content-Type': types[extname(path)] ?? 'application/octet-stream' })
  createReadStream(path).pipe(res)
})
await new Promise(done => server.listen(0, '127.0.0.1', done))

const browser = await chromium.launch({ channel: 'chrome' }) // the Chrome installed on this computer
try {
  const tab = await browser.newPage()
  await tab.goto(`http://127.0.0.1:${server.address().port}/`)
  const pages = await tab.evaluate(async b64 => {
    const { pdfPages } = await import('/pdf.js')
    const { pages } = await pdfPages(Uint8Array.from(atob(b64), c => c.charCodeAt(0)))
    const base64 = a => {
      let s = ''
      for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode(...a.subarray(i, i + 0x8000))
      return btoa(s)
    }
    return pages.map(p => ({ w: p.w, h: p.h, grey: base64(p.grey) }))
  }, readFileSync(pdf).toString('base64'))
  pages.forEach((p, i) => {
    writeFileSync(`${radix}-p${i + 1}.grey`, Buffer.from(p.grey, 'base64'))
    writeFileSync(`${radix}-p${i + 1}.json`, JSON.stringify({ width: p.w, height: p.h }))
  })
  console.log(pages.length)
} finally {
  await browser.close()
  server.close()
}
