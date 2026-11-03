// Open the spike page in Chrome and wait for Audiveris to finish; save the .mxl and the console.
//   node spike/drive.mjs [page] [java]   (with spike/serve.mjs running)
import { appendFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from '/Users/jdlehman/code/github/jdlehman/midi_studio/node_modules/playwright/index.mjs'

const [page = '/.work/page.png', java = '25', minutes = '30'] = process.argv.slice(2)
const out = join(import.meta.dirname, '..', '.work')
const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch())
const tab = await browser.newPage()
const lines = []
// written as it comes, so a run that never ends still shows how far it got
const live = join(out, 'spike-live.txt')
writeFileSync(live, '')
const t0 = Date.now()
const note = s => { lines.push(s); appendFileSync(live, `${((Date.now() - t0) / 1000).toFixed(1)}s ${s}\n`) }
tab.on('console', m => note(m.text()))
tab.on('pageerror', e => note('PAGEERROR ' + e.message))
await tab.goto(`http://127.0.0.1:8787/spike/index.html?page=${encodeURIComponent(page)}&java=${java}${process.env.EXTRA ?? ''}`)
const started = Date.now()
await tab.waitForFunction(() => window.spike?.done, null, { timeout: Number(minutes) * 60 * 1000, polling: 2000 })
const result = await tab.evaluate(() => ({ ...window.spike, mxl: window.spike.mxl ? window.spike.mxl.length : 0 }))
const mxl = await tab.evaluate(() => window.spike.mxl)
if (mxl) writeFileSync(join(out, 'spike-result.mxl'), Buffer.from(mxl))
const memory = await tab.evaluate(() => performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) + ' MB JS heap' : '')
writeFileSync(join(out, 'spike-console.txt'), lines.join('\n'))
console.log(JSON.stringify({ ...result, wall: Math.round((Date.now() - started) / 1000), memory }, null, 1))
await browser.close()
