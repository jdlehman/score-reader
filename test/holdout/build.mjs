// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Builds the held-out pages (test/holdout/README.md): songs from the OpenScore Lieder Corpus (CC0),
// in the order songs.txt lists them (a seeded random draw), the first ones that build until there
// are COUNT. Each page is a song's first 12 bars (fewer if 12 don't fit on one page), drawn by
// Verovio as an A4 page at 300 dpi, and its answer comes from the same cut MusicXML.
//   node test/holdout/build.mjs            (COUNT=20; needs rsvg-convert and Python with PIL)
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import createVerovioModule from 'verovio/wasm'
import { VerovioToolkit } from 'verovio/esm'
import { musicXmlText, parseMusicXml } from '../score.mjs'

const HERE = import.meta.dirname
const CACHE = resolve(HERE, '..', '..', '.work', 'holdout-src')
const COUNT = Number(process.env.COUNT ?? 20)
const BARS = 12
const RAW = 'https://raw.githubusercontent.com/OpenScore/Lieder/main/'
const OPTIONS = { pageWidth: 2100, pageHeight: 2970, scale: 40, footer: 'none', breaks: 'auto', adjustPageHeight: false }
const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

const songs = readFileSync(join(HERE, 'songs.txt'), 'utf8').split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'))
mkdirSync(CACHE, { recursive: true })
const tk = new VerovioToolkit(await createVerovioModule())
tk.setOptions(OPTIONS)

/** A short name for a song: its composer's surname and its title, plain letters. */
const nameOf = path => {
  const [, composer, , song] = path.split('/')
  const plain = s => s.normalize('NFD').replace(/[^\x00-\x7f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  return `${plain(composer.split(',')[0])}-${plain(song.replace(/^\d+_/, '')).slice(0, 32).replace(/-$/, '')}`
}

/** The score with only each part's first n measures. */
const cut = (xml, n) =>
  xml.replace(/(<part\b[^>]*\bid="[^"]+"[^>]*>)([\s\S]*?)(<\/part>)/g, (_, open, body, close) => {
    const measures = [...body.matchAll(/<measure\b[\s\S]*?<\/measure>/g)].slice(0, n).map(m => m[0])
    return `${open}\n${measures.join('\n')}\n${close}`
  })

async function source(path) {
  const file = join(CACHE, path.match(/(lc\d+)\.mxl$/)[1] + '.mxl')
  if (!existsSync(file)) {
    const r = await fetch(RAW + path.split('/').map(encodeURIComponent).join('/'))
    if (!r.ok) throw new Error(`fetch: ${r.status}`)
    writeFileSync(file, Buffer.from(await r.arrayBuffer()))
  }
  return musicXmlText(readFileSync(file))
}

const built = []
for (const path of songs) {
  if (built.length >= COUNT) break
  const name = nameOf(path)
  try {
    const whole = await source(path)
    let n = BARS
    let xml
    for (; n >= 4; n--) {
      xml = cut(whole, n)
      if (!tk.loadData(xml)) throw new Error('Verovio could not load it')
      if (tk.getPageCount() === 1) break
    }
    if (n < 4) throw new Error('4 bars do not fit on a page')
    const parts = parseMusicXml(xml)
    if (parts.some(p => p.measures.length !== n)) throw new Error('parts with different numbers of bars')
    const total = parts.reduce((s, p) => s + p.measures.reduce((t, m) => t + m.notes.length, 0), 0)
    if (!total) throw new Error('no notes')
    const time = xml.match(/<time\b[^>]*>\s*<beats>(\d+)<\/beats>\s*<beat-type>(\d+)<\/beat-type>/)
    const answer = {
      page: name,
      title: `${path.split('/').slice(1, 4).join(', ').replace(/_/g, ' ')}, bars 1-${n}`,
      source: `OpenScore Lieder Corpus (CC0 1.0), ${path}`,
      beats: Number(time?.[1] ?? 4),
      beat_type: Number(time?.[2] ?? 4),
      bars: n,
      parts: parts.map(p => {
        const notes = p.measures.flatMap((m, i) => m.notes.map(x => ({ bar: i + 1, pitch: NAMES[x.midi % 12] + (Math.floor(x.midi / 12) - 1), midi: x.midi, lyric: x.lyric ?? null, onset: Math.round(x.onset * 1e6) / 1e6 })))
        return { id: p.id, name: p.name, note_count: notes.length, notes }
      }),
      total_notes: total,
    }
    answer.total_lyrics = answer.parts.reduce((s, p) => s + p.notes.filter(x => x.lyric).length, 0)
    const svg = join(CACHE, name + '.svg')
    writeFileSync(svg, tk.renderToSVG(1))
    const png = join(HERE, name + '.png')
    execFileSync('rsvg-convert', ['-w', '2480', '-b', 'white', '-o', png, svg])
    execFileSync('python3', ['-I', '-c', 'import sys\nfrom PIL import Image\nImage.open(sys.argv[1]).convert("L").save(sys.argv[1], optimize=True)', png])
    rmSync(svg)
    writeFileSync(join(HERE, name + '.json'), JSON.stringify(answer, null, 1) + '\n')
    built.push(name)
    console.log(`${name}: ${n} bars, ${parts.length} parts, ${total} notes, ${answer.total_lyrics} syllables`)
  } catch (e) {
    console.log(`(skipped ${name}: ${e.message})`)
  }
}
console.log(`${built.length} pages`)
