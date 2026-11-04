// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A read must offer only what it wrote. In one browser profile (CheerpJ keeps /files in it), read
// a score, then a page with no music: the second read must fail, not offer the first score.
//   node test/stale.mjs <score.pdf> <page without music>   (with npm run serve running)
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { chromium } from 'playwright-core'

const [score, blank] = process.argv.slice(2)
const profile = mkdtempSync(join(tmpdir(), 'score-reader-profile-'))
const context = await chromium.launchPersistentContext(profile, { channel: 'chrome' })
const page = await context.newPage()
const url = process.env.URL ?? 'http://127.0.0.1:8787/dist/'

async function read(file) {
  await page.goto(url)
  await page.setInputFiles('#files', resolve(file))
  await page.waitForFunction(() => !document.getElementById('done').hidden || !document.getElementById('failed').hidden, null, { timeout: 10 * 60 * 1000, polling: 2000 })
  return page.evaluate(() => ({
    done: !document.getElementById('done').hidden,
    links: [...document.querySelectorAll('#downloads a')].map(a => a.download),
    why: document.getElementById('failed-why').textContent,
  }))
}

const first = await read(score)
console.log('first read:', JSON.stringify(first))
const second = await read(blank)
console.log('second read:', JSON.stringify(second))
await context.close()
const ok = first.done && !second.done
console.log(ok ? 'ok: the second read offered nothing of the first' : 'FAILED: the second read offered a score')
process.exit(ok ? 0 : 1)
