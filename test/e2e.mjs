// Score reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Drive the built page (dist/) in Chrome: choose files, wait, save the download and screenshots.
//   node test/e2e.mjs <out name> <file>...   (with spike/serve.mjs running; results in .work/e2e/)
//   MINUTES=n gives up after n minutes (default 20); the page's console goes to .work/e2e/<name>.log
//   URL=... reads on another copy of the site, such as the published one
import { appendFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { chromium } from 'playwright-core'

const [name, ...files] = process.argv.slice(2)
const out = join(import.meta.dirname, '..', '.work', 'e2e')
mkdirSync(out, { recursive: true })
const browser = await chromium.launch({ channel: 'chrome' }) // the Chrome installed on this computer
const tab = await browser.newPage({ viewport: { width: 900, height: 900 } })
const errors = []
tab.on('pageerror', e => errors.push(e.message))
const logFile = join(out, `${name}.log`)
writeFileSync(logFile, '')
const t00 = Date.now()
const note = text => appendFileSync(logFile, `${String(Math.round((Date.now() - t00) / 1000)).padStart(5)}s ${text}\n`)
tab.on('console', m => note(m.text()))
tab.on('response', r => { if (r.status() >= 400) note(`(${r.status()} ${r.url()})`) })
await tab.goto(process.env.URL ?? 'http://127.0.0.1:8787/dist/') // URL=https://inlehmansterms.net/score-reader/ tests the live site
await tab.screenshot({ path: join(out, `${name}-0-start.png`), fullPage: true })
const t0 = Date.now()
// the page's memory every 15 s (Java's heap lives in it)
setInterval(() => tab.evaluate(() => Math.round(performance.memory.usedJSHeapSize / 1e6)).then(mb => note(`(heap ${mb} MB)`), () => {}), 15000).unref()
await tab.setInputFiles('#files', files.map(f => resolve(f)))
// a look at the progress once the first page is under way
await tab.waitForFunction(() => /^Page \d/.test(document.getElementById('pages')?.textContent ?? '') || !document.getElementById('failed').hidden, null, { timeout: 120000 }).catch(() => {})
await tab.waitForTimeout(20000)
await tab.screenshot({ path: join(out, `${name}-1-working.png`), fullPage: true })
const minutes = Number(process.env.MINUTES ?? 20)
const finished = await tab
  .waitForFunction(() => !document.getElementById('done').hidden || !document.getElementById('failed').hidden, null, { timeout: minutes * 60 * 1000, polling: 2000 })
  .then(() => true, () => false)
const seconds = Math.round((Date.now() - t0) / 1000)
await tab.screenshot({ path: join(out, `${name}-2-end.png`), fullPage: true })
const state = await tab.evaluate(() => ({
  status: document.getElementById('status').textContent,
  heapMB: Math.round((performance.memory?.usedJSHeapSize ?? 0) / 1e6), // Java's heap lives here
  done: !document.getElementById('done').hidden,
  title: document.getElementById('done-title').textContent,
  summary: document.getElementById('done-summary').textContent,
  failed: document.getElementById('failed-why').textContent,
  links: [...document.querySelectorAll('#downloads a')].map(a => a.download),
}))
if (state.done) {
  const [download] = await Promise.all([tab.waitForEvent('download'), tab.click('#downloads a')])
  await download.saveAs(join(out, `${name}.mxl`))
}
console.log(JSON.stringify({ name, seconds, finished, ...state, errors }, null, 1))
await browser.close()
