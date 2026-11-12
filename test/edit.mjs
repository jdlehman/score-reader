// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The note editor ("Check the notes", check.js), in Chrome, on a MusicXML file opened as it is (no
// read, so it takes seconds): the bar that's too long is shaded, a note changes, the download has
// the change and is named "(corrected)", the button says Saved, and leaving with a change not
// downloaded asks first.
//   node test/edit.mjs   (with npm run dev running; URL=... tests another copy of the site)
import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { chromium } from 'playwright-core'

const url = process.env.URL ?? 'http://127.0.0.1:8787/'
const out = mkdtempSync(join(tmpdir(), 'score-reader-edit-'))
const browser = await chromium.launch({ channel: 'chrome' })
const tab = await browser.newPage({ acceptDownloads: true })
const errors = []
const dialogs = []
tab.on('pageerror', e => errors.push(String(e)))
tab.on('dialog', d => { dialogs.push(d.type()); d.dismiss() })
let failed = 0
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`); if (!ok) failed++ }

await tab.goto(url)
await tab.setInputFiles('#files', join(import.meta.dirname, 'fixtures', 'edit.musicxml'))
await tab.waitForSelector('#fix-score svg g.note', { timeout: 60000 })
check(await tab.textContent('#done-title') === 'Opened', 'a MusicXML file opens straight to checking its notes')
check(await tab.locator('#fix-score rect.flag-bar').count() > 0, 'the bar that is too long is shaded')

const picked = () => tab.textContent('#fix-picked')
const button = () => tab.$eval('#fix-download', b => (b.hidden ? 'hidden' : b.disabled ? `${b.textContent} (off)` : b.textContent))
const steps = text => [...text.matchAll(/<step>([A-G])<\/step>/g)].map(m => m[1]).join('')
const download = async () => {
  const [d] = await Promise.all([tab.waitForEvent('download'), tab.click('#fix-download')])
  const path = join(out, d.suggestedFilename())
  await d.saveAs(path)
  return { name: d.suggestedFilename(), steps: steps(readFileSync(path, 'utf8')) }
}

check(await button() === 'hidden', 'no download of changes before a change')
// a tap: sent to the note itself (a click at its centre can land on the sticky controls above it)
await tab.locator('#fix-score svg g.note').first().dispatchEvent('click')
check((await picked()).startsWith('C5 · bar 1'), `a tapped note is picked (${await picked()})`)
await tab.click('#fix-pitch [data-step="1"]')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('D5'))
check(await button() === 'Download with your changes', 'a change offers its download')
const first = await download()
check(first.name === 'edit (corrected).musicxml', `the download is named "${first.name}"`)
check(first.steps.startsWith('DDEF'), `it has the change (${first.steps.slice(0, 4)}, was CDEF)`)
check(await button() === 'Saved (off)', 'then it says Saved')
await tab.click('#fix-pitch [data-step="-1"]')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('C5'))
check(await button() === 'Download again with your newest changes', 'another change offers it again')
await tab.click('#again')
await tab.waitForTimeout(1000)
check(dialogs.includes('beforeunload'), 'leaving with a change not downloaded asks first')
await tab.click('#fix-undo')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('D5'))
check(await button() === 'Saved (off)', 'undoing back to what was downloaded is Saved again')
check(!errors.length, `no page errors${errors.length ? ': ' + errors.join('; ') : ''}`)

await browser.close()
process.exit(failed ? 1 : 0)
