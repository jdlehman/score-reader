// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The warning before a read (preflight.js), in Chrome: a photo too small for Audiveris warns, and
// either answer works; a good photo goes straight to reading. Stops before Audiveris runs.
//   node test/e2e-check.mjs   (with npm run serve running; URL=... tests another copy of the site)
// The photos are of a test piece from midi_studio's recognition test; desktop Audiveris reads
// photo.jpg and rejects photo-small.jpg ("too low interline value of 9 pixels").
import { join } from 'node:path'
import { chromium } from 'playwright-core'

const url = process.env.URL ?? 'http://127.0.0.1:8787/'
const fixture = name => join(import.meta.dirname, 'fixtures', name)
const browser = await chromium.launch({ channel: 'chrome' })
const visible = (tab, id) => tab.waitForFunction(id => !document.getElementById(id).hidden, id, { timeout: 60000 })
const reading = tab => tab.waitForFunction(() => /^Starting the reader/.test(document.getElementById('status').textContent), null, { timeout: 60000 })
let failed = false
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`); failed ||= !ok }

try {
  // too small: warns; "Choose other files" goes back, and a good photo then reads with no warning
  let tab = await browser.newPage()
  await tab.goto(url)
  await tab.setInputFiles('#files', fixture('photo-small.jpg'))
  await visible(tab, 'check')
  check(/too small/.test(await tab.textContent('#check-why')), 'a photo too small for Audiveris warns that it is too small')
  await tab.click('#check-other')
  await visible(tab, 'pick')
  check(true, '"Choose other files" goes back to choosing')
  await tab.setInputFiles('#files', fixture('photo.jpg'))
  await reading(tab)
  check(await tab.$eval('#check', e => e.hidden), 'a good photo then reads with no warning')
  await tab.close()

  // "Read it anyway" reads
  tab = await browser.newPage()
  await tab.goto(url)
  await tab.setInputFiles('#files', fixture('photo-small.jpg'))
  await visible(tab, 'check')
  await tab.click('#check-read')
  await reading(tab)
  check(true, '"Read it anyway" starts the read')
} catch (e) {
  check(false, e.message)
}
await browser.close()
process.exit(failed ? 1 : 0)
