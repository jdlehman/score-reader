// Score reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// node spike/hello.mjs 25 1  -> runs spike/hello.html and prints its console
import { chromium } from 'playwright-core'
const [java = '25', wasm = '0'] = process.argv.slice(2)
const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch())
const tab = await browser.newPage()
tab.on('console', m => { const t = m.text(); if (!/404|CHEERPJ|license|^\s*[|_\\/ ]/.test(t)) console.log(t.trim()) })
tab.on('pageerror', e => console.log('PAGEERROR ' + e.message))
await tab.goto(`http://127.0.0.1:8787/spike/hello.html?java=${java}&wasm=${wasm}`)
await tab.waitForFunction(() => window.spike?.done, null, { timeout: 120000 }).catch(() => console.log('timed out'))
await browser.close()
