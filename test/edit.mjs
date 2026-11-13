// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The note editor ("Check the notes", check.js), in Chrome, on a MusicXML file opened as it is (no
// read, so it takes seconds): the bar that's too long is shaded, a note changes, the download has
// the change and is named "(corrected)", the button says Saved, leaving with a change not
// downloaded asks first, and the edits for a reader's mistakes (octave, stepping through a voice,
// a note put in and taken out, a triplet made and taken away) work.
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
// the new edits, on the first note of bar 3 (five quarters: a beat too long)
const note = i => tab.locator('#fix-score svg g.note').nth(i).dispatchEvent('click')
await note(5)
check((await picked()).startsWith('A4 · bar 3'), `bar 3's first note is picked (${await picked()})`)
await tab.click('#fix-pitch [data-octave="1"]')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('A5'))
await tab.keyboard.press('Shift+ArrowDown')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('A4'))
check(true, 'an octave up, and back down with shift ↓')
await tab.keyboard.press('ArrowRight')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('B4'))
await tab.keyboard.press('ArrowLeft')
await tab.waitForFunction(() => document.getElementById('fix-picked').textContent.startsWith('A4'))
check(true, '→ steps to the next note in the voice, ← back')
const count = () => tab.locator('#fix-score svg g.note').count()
const notesBefore = await count()
await tab.click('#fix-insert')
await tab.waitForFunction(n => document.querySelectorAll('#fix-score svg g.note').length === n + 1, notesBefore)
await tab.keyboard.press('Delete')
await tab.waitForFunction(n => document.querySelectorAll('#fix-score svg g.note').length === n, notesBefore)
check(true, 'a note put in after it, and taken out with Delete')
await tab.click('#fix-triplet')
await tab.waitForFunction(() => !document.getElementById('fix-not-triplet').hidden)
await tab.waitForFunction(() => document.querySelectorAll('#fix-score rect.flag-bar').length === 0)
check(await tab.isDisabled('#fix-length [data-length="1"]'), 'made a triplet: bar 3 fits, no bar is shaded, and its lengths wait for "Not a triplet"')
await tab.click('#fix-not-triplet')
await tab.waitForFunction(() => document.querySelectorAll('#fix-score rect.flag-bar').length > 0)
check(true, '"Not a triplet" puts it back: bar 3 is shaded again')

check(!errors.length, `no page errors${errors.length ? ': ' + errors.join('; ') : ''}`)

await browser.close()
process.exit(failed ? 1 : 0)
