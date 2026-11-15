#!/usr/bin/env node
// CLI for the gated TrOMR merge (app/merge.js).
// Usage:
//   node tools/merge.mjs <audiveris.mxl|.musicxml> <tromr-staff-dir> <out.musicxml> [--beats N]
//
// The TrOMR dir holds one MusicXML file per staff crop, named staff0.musicxml,
// staff1.musicxml, ... in system order, top-to-bottom staff per system (the same
// layout run_tromr.py produces in the spikes). Output is plain MusicXML; the
// caller re-zips it to .mxl if needed. Prints the merge report as JSON.
import { readFile, readdir, writeFile } from 'node:fs/promises'
import { mergeMusicXml, readMxl } from '../app/merge.js'

const args = process.argv.slice(2)
const beatsIdx = args.indexOf('--beats')
const beats = beatsIdx === -1 ? undefined : parseInt(args[beatsIdx + 1], 10)
const [audPath, tromrDir, outPath] = args.filter(a => a !== '--beats' && a !== String(beats))

if (!audPath || !tromrDir || !outPath) {
  console.error('usage: node tools/merge.mjs <audiveris.mxl|.musicxml> <tromr-staff-dir> <out.musicxml> [--beats N]')
  process.exit(2)
}

const audBuf = await readFile(audPath)
const audXml = audPath.endsWith('.mxl') ? await readMxl(audBuf) : audBuf.toString('utf-8')
const files = (await readdir(tromrDir))
  .filter(f => /^staff\d+\.musicxml$/.test(f))
  .sort((a, b) => parseInt(a.match(/\d+/)[0], 10) - parseInt(b.match(/\d+/)[0], 10))
if (!files.length) {
  console.error(`no staffN.musicxml files in ${tromrDir}`)
  process.exit(2)
}
const tromrXmls = []
for (const f of files) tromrXmls.push((await readFile(`${tromrDir}/${f}`)).toString('utf-8'))

const { xml, report } = mergeMusicXml(audXml, tromrXmls, { beats })
await writeFile(outPath, xml)
console.log(JSON.stringify({ out: outPath, staffFiles: files.length, ...report }, null, 1))
