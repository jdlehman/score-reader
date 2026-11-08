// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// End-to-end test for the photo preflight: a good page proceeds straight to Audiveris, and a
// bad photo page warns before the CheerpJ run starts.
//   node test/e2e-preflight.mjs   (with npm run serve running; results in .work/e2e/)
// NOT run in the spike VM (no Chrome / CheerpJ there): run locally before merging.
//   The fixtures are test/fixtures/hallelujah-clean.jpg (12 staves, no warning) and
//   test/fixtures/hallelujah-photo-hard.jpg (0 staves, warns).
import { join } from 'node:path'
import { chromium } from 'playwright-core'

const out = join(import.meta.dirname, '..', '.work', 'e2e')

async function read(file) {
  const browser = await chromium.launch({ channel: 'chrome' })
  const tab = await browser.newPage({ viewport: { width: 900, height: 900 } })
  const errors = []
  tab.on('pageerror', e => errors.push(e.message))
  await tab.goto(process.env.URL ?? 'http://127.0.0.1:8787/dist/')
  await tab.setInputFiles('#files', file)
  // the work panel must appear at once
  await tab.waitForFunction(() => !document.getElementById('work').hidden, null, { timeout: 30000 })
  // give the preflight (a second or two) and the CheerpJ start time to show
  await tab.waitForTimeout(15000)
  const state = await tab.evaluate(() => ({
    warned: !document.getElementById('preflight-warn').hidden,
    warnText: document.getElementById('preflight-warn-text').textContent,
    status: document.getElementById('status').textContent,
    reading: /^Page \d/.test(document.getElementById('pages')?.textContent ?? ''),
  }))
  await browser.close()
  return { ...state, errors }
}

const clean = await read(join(import.meta.dirname, 'fixtures', 'hallelujah-clean.jpg'))
console.log('clean page:', JSON.stringify(clean))
const hard = await read(join(import.meta.dirname, 'fixtures', 'hallelujah-photo-hard.jpg'))
console.log('hard photo:', JSON.stringify(hard))

// The good page must NOT warn and must reach Audiveris; the hard photo MUST warn before
// any Audiveris step, and must offer "Read it anyway" / "Choose different files".
const ok = !clean.warned && clean.reading && hard.warned && !hard.reading &&
  /Read it anyway/.test(await readWarnButtons())
async function readWarnButtons() {
  // re-open the hard page and read the button labels (kept separate so the first pass
  // above stays a pure observation of the warning appearing)
  const browser = await chromium.launch({ channel: 'chrome' })
  const tab = await browser.newPage()
  await tab.goto(process.env.URL ?? 'http://127.0.0.1:8787/dist/')
  await tab.setInputFiles('#files', join(import.meta.dirname, 'fixtures', 'hallelujah-photo-hard.jpg'))
  await tab.waitForFunction(() => !document.getElementById('preflight-warn').hidden, null, { timeout: 30000 })
  const labels = await tab.evaluate(() => [...document.querySelectorAll('#preflight-warn button')].map(b => b.textContent).join(' | '))
  // "Read it anyway" must proceed to Audiveris
  await tab.click('#preflight-continue')
  await tab.waitForFunction(() => /^Page \d/.test(document.getElementById('pages')?.textContent ?? ''), null, { timeout: 120000 }).catch(() => {})
  const reading = await tab.evaluate(() => /^Page \d/.test(document.getElementById('pages')?.textContent ?? ''))
  await browser.close()
  return reading ? labels : ''
}
console.log(ok ? 'ok: clean proceeds, hard photo warns first' : 'FAILED: preflight e2e did not behave as expected')
process.exit(ok ? 0 : 1)
