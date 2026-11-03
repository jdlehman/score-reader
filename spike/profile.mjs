// Score reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Profile one Audiveris step in the browser: start V8's sampling profiler when the step starts
// (from the log) and stop after a while, then list where the time went.
//   node spike/profile.mjs BEAMS 20   (step, seconds to sample)   (with spike/serve.mjs running)
import { appendFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright-core'

const [from = 'BEAMS', seconds = '20', page = '/.work/page.png'] = process.argv.slice(2)
const out = join(import.meta.dirname, '..', '.work')
const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch())
const tab = await browser.newPage()
const cdp = await tab.context().newCDPSession(tab)
const live = join(out, 'profile-live.txt')
writeFileSync(live, '')
const t0 = Date.now()
let started = false
const finished = new Promise(resolve => {
  tab.on('console', async m => {
    const t = m.text().trim()
    appendFileSync(live, `${((Date.now() - t0) / 1000).toFixed(1)}s ${t.slice(0, 160)}\n`)
    if (!started && t.endsWith(`| ${from}`)) {
      started = true
      // switched on only now: on from the start, it slows CheerpJ thirtyfold
      await cdp.send('Profiler.enable')
      await cdp.send('Profiler.setSamplingInterval', { interval: 2000 })
      await cdp.send('Profiler.start')
      appendFileSync(live, 'profiler started\n')
      setTimeout(async () => {
        appendFileSync(live, 'stopping profiler\n')
        const { profile } = await cdp.send('Profiler.stop')
        appendFileSync(live, 'profiler stopped\n')
        resolve(profile)
      }, Number(seconds) * 1000)
    }
  })
})
await tab.goto(`http://127.0.0.1:8787/spike/index.html?page=${encodeURIComponent(page)}&java=25${process.env.EXTRA ?? ''}`)
const profile = await finished
writeFileSync(join(out, `profile-${from}.cpuprofile`), JSON.stringify(profile))

// self time per function
const byId = new Map(profile.nodes.map(n => [n.id, n]))
const self = new Map()
const dt = profile.timeDeltas
for (let i = 0; i < profile.samples.length; i++) {
  const n = byId.get(profile.samples[i])
  const key = `${n.callFrame.functionName || '(anon)'} ${n.callFrame.url.split('/').pop()}:${n.callFrame.lineNumber}`
  self.set(key, (self.get(key) ?? 0) + (dt[i] ?? 0))
}
const total = [...self.values()].reduce((a, b) => a + b, 0)
const top = [...self].sort((a, b) => b[1] - a[1]).slice(0, 40)
console.log(`${from}: ${(total / 1e6).toFixed(1)} s sampled`)
for (const [k, v] of top) console.log(`${((v / total) * 100).toFixed(1).padStart(5)}%  ${k}`)
// the generated code of the hottest compiled functions, to see which Java methods they are
await cdp.send('Debugger.enable').catch(() => {})
const scripts = new Map()
for (const [k] of top.slice(0, 12)) {
  const n = profile.nodes.find(n => `${n.callFrame.functionName || '(anon)'} ${n.callFrame.url.split('/').pop()}:${n.callFrame.lineNumber}` === k)
  if (n && !n.callFrame.url) scripts.set(n.callFrame.scriptId, k)
}
// and their callers'
for (const n of profile.nodes) for (const c of n.children ?? []) {
  const child = profile.nodes.find(x => x.id === c)
  if (child && scripts.has(child.callFrame.scriptId) && !n.callFrame.url && n.callFrame.scriptId !== '0') scripts.set(n.callFrame.scriptId, 'caller of ' + scripts.get(child.callFrame.scriptId))
}
for (const [id, k] of scripts) {
  const src = await cdp.send('Debugger.getScriptSource', { scriptId: id }).then(r => r.scriptSource).catch(e => 'error ' + e.message)
  writeFileSync(join(out, `profile-${from}-script-${id}.js`), `// ${k}\n${src}`)
  console.log('script', id, k, src.length, 'chars')
}
await browser.close()
