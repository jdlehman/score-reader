// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
import { chromium } from 'playwright-core'
const b = await chromium.launch({ channel: 'chrome' })
const p = await b.newPage()
p.on('console', m => { if (/bench|exit/.test(m.text())) console.log(m.text().trim()) })
await p.goto('http://127.0.0.1:8787/teavm/cheerpj.html')
await p.waitForFunction(() => window.done, null, { timeout: 600000 })
await b.close()
