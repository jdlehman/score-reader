// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Builds the real scans with answers (test/corpus/README.md, "Real scans with answers"): songs from
// public-domain IMSLP scans, each the edition an OpenScore Lieder Corpus song (CC0) was copied
// from, so the song's MusicXML is the answer. Each case is the whole song, its scan pages cut out
// as one PDF, as someone would upload it. The bars on each scan page were read off the scan; they
// check that the pages cut cover the song.
//   node test/corpus/real/build.mjs                       answers only, for the PDFs already here
//   IMSLP=<folder with the IMSLP files> node test/corpus/real/build.mjs   also cuts the PDFs (macOS)
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { answerFrom } from '../../answer.mjs'
import { musicXmlText, parseMusicXml } from '../../score.mjs' // parts, to check the pages cover the song

const HERE = import.meta.dirname
const CACHE = resolve(HERE, '..', '..', '..', '.work', 'real-src')
const RAW = 'https://raw.githubusercontent.com/OpenScore/Lieder/main/scores/'

/** Each song: its OpenScore file, the IMSLP file it was copied from, and per scan page [PDF page, first bar, last bar]. */
const SONGS = [
  {
    name: 'lieder-schubert-gute-nacht', title: 'Schubert, "Gute Nacht", Winterreise D.911 no. 1',
    openscore: 'Schubert,_Franz/Winterreise,_D.911/01_Gute_Nacht/lc5015378.mxl',
    imslp: 60822, file: 'IMSLP60822-PMLP02203-Schubert_Werke_Breitkopf_Serie_XX_Band_9_F.S.878-904.pdf',
    edition: "Schubert's Werke, Serie XX, Band 9 (Breitkopf & Härtel, 1895)",
    pages: [[6, 1, 18], [7, 19, 50], [8, 51, 77], [9, 78, 105]],
  },
  {
    name: 'lieder-schubert-lindenbaum', title: 'Schubert, "Der Lindenbaum", Winterreise D.911 no. 5',
    openscore: 'Schubert,_Franz/Winterreise,_D.911/05_Der_Lindenbaum/lc5016466.mxl',
    imslp: 60822, file: 'IMSLP60822-PMLP02203-Schubert_Werke_Breitkopf_Serie_XX_Band_9_F.S.878-904.pdf',
    edition: "Schubert's Werke, Serie XX, Band 9 (Breitkopf & Härtel, 1895)",
    pages: [[20, 1, 24], [21, 25, 45], [22, 46, 62], [23, 63, 82]],
  },
  {
    name: 'lieder-schumann-widmung', title: 'Schumann, "Widmung", Myrthen Op. 25 no. 1',
    openscore: 'Schumann,_Robert/Myrthen,_Op.25/01_Widmung/lc6885211.mxl',
    imslp: 270905, file: 'IMSLP270905-PMLP12732-Schumann,_Robert_Werke_Breitkopf_Gregg_Serie_13_Band_1_RS_120_Op_25_scan.pdf',
    edition: "Robert Schumann's Werke, Serie XIII (Breitkopf & Härtel, issued 1887)",
    pages: [[1, 1, 18], [2, 19, 44]],
  },
  {
    name: 'lieder-brahms-wiegenlied', title: 'Brahms, "Wiegenlied", Op. 49 no. 4',
    openscore: 'Brahms,_Johannes/5_Lieder,_Op.49/4_Wiegenlied/lc5701612.mxl',
    imslp: 81909, file: 'IMSLP81909-PMLP22223-Brahms_Werke_Band_24_Breitkopf_JB_148_Op_49_scan.pdf',
    edition: 'Johannes Brahms, Sämtliche Werke, Band 24 (Breitkopf & Härtel, 1926-27)',
    pages: [[10, 1, 19]],
  },
  {
    name: 'lieder-faure-apres-un-reve', title: 'Fauré, "Après un rêve", Op. 7 no. 1',
    openscore: 'Fauré,_Gabriel/3_Songs,_Op.7/1_Après_un_rêve/lc6810863.mxl',
    imslp: 24047, file: 'IMSLP24047-PMLP54610-Fauré_-_Aprè_une_rêve,_Op._7,_No._1_(c).pdf',
    edition: 'J. Hamelle, Paris, ca. 1878 (first edition)',
    pages: [[1, 1, 11], [2, 12, 23], [3, 24, 35], [4, 36, 48]],
  },
  {
    name: 'lieder-schubert-erlkoenig', title: 'Schubert, "Erlkönig", D.328 (4th version)',
    openscore: 'Schubert,_Franz/_/Der_Erlkönig,_D.328/lc29062370.mxl',
    imslp: 15041, file: 'IMSLP15041-SchubertD328_Erlkönig_4th_version.pdf',
    edition: "Schubert's Werke, Serie XX, Band 3 (Breitkopf & Härtel, 1895; a Kalmus reprint)",
    pages: [[1, 1, 23], [2, 24, 53], [3, 54, 75], [4, 76, 96], [5, 97, 122], [6, 123, 148]],
    partNames: ['Singstimme', 'Pianoforte'], // OpenScore names the voice "Clarinet in C"
  },
]

async function source(path) {
  mkdirSync(CACHE, { recursive: true })
  const file = join(CACHE, path.match(/(lc\d+)\.mxl$/)[1] + '.mxl')
  if (!existsSync(file)) {
    const r = await fetch(RAW + path.split('/').map(encodeURIComponent).join('/'))
    if (!r.ok) throw new Error(`fetch ${path}: ${r.status}`)
    writeFileSync(file, Buffer.from(await r.arrayBuffer()))
  }
  return musicXmlText(readFileSync(file))
}

const IMSLP = process.env.IMSLP ? resolve(process.env.IMSLP.replace(/^~/, process.env.HOME)) : null
const CUT = join(CACHE, 'cut')
if (IMSLP) {
  mkdirSync(CACHE, { recursive: true })
  execFileSync('swiftc', ['-O', join(HERE, 'cut.swift'), '-o', CUT]) // `swift cut.swift` can't load PDFKit
}
for (const song of SONGS) {
  const xml = await source(song.openscore)
  const parts = parseMusicXml(xml)
  const bars = parts[0].measures.length
  if (parts.some(p => p.measures.length !== bars)) throw new Error(`${song.name}: parts with different numbers of bars`)
  if (song.pages.at(-1)[2] !== bars) throw new Error(`${song.name}: the pages end at bar ${song.pages.at(-1)[2]}, the song at ${bars}`)
  song.pages.forEach(([pdfPage, a], k) => {
    if (a !== (k ? song.pages[k - 1][2] + 1 : 1)) throw new Error(`${song.name}: page ${k + 1} doesn't follow on`)
    if (k && pdfPage !== song.pages[k - 1][0] + 1) throw new Error(`${song.name}: its scan pages aren't one run`)
  })
  // the whole song as one PDF, as it is uploaded: a page without a time signature then takes the
  // one before it, as Audiveris does in a book
  const name = `${song.name}-song`
  const [first, last] = [song.pages[0][0], song.pages.at(-1)[0]]
  if (IMSLP) execFileSync(CUT, [join(IMSLP, song.file), `${first}-${last}`, join(HERE, name + '.pdf')])
  const answer = answerFrom(xml, {
    names: song.partNames,
    page: name,
    title: `${song.title}, the whole song (${song.pages.length === 1 ? 'one scan page' : `${song.pages.length} scan pages`})`,
    source: `OpenScore Lieder Corpus (CC0 1.0), ${song.openscore}`,
    scan: `IMSLP #${song.imslp}, PDF ${first === last ? `page ${first}` : `pages ${first}-${last}`}: ${song.edition}. Public domain.`,
  })
  writeFileSync(join(HERE, name + '.json'), JSON.stringify(answer, null, 1) + '\n')
  console.log(`${name}: ${answer.bars} bars, ${answer.total_notes} notes, ${answer.total_lyrics} syllables${IMSLP ? ', pages cut' : ''}`)
}
