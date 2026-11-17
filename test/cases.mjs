// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The corpus's cases and their reads, for test/corpus.mjs (reads and scores them) and
// test/compare.mjs (compares two runs bar by bar).
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { basename, dirname, extname, join, relative, resolve } from 'node:path'
import { musicXmlText, parseMusicXml } from './score.mjs'

export const ROOT = resolve(import.meta.dirname, '..')
/** The local test set (EXTRA), if any: pages the repository can't hold, and doesn't name. */
export const EXTRA = process.env.EXTRA ? resolve(process.env.EXTRA.replace(/^~/, process.env.HOME)) : null

const INPUT = /\.(png|jpe?g|tiff?|pdf)$/i

/** An answer file: <name>.gt.json, or <name>.json if it lists parts (not just an image's size). */
function answerFor(input) {
  for (const f of [input.replace(INPUT, '.gt.json'), input.replace(INPUT, '.json')]) {
    try {
      if (Array.isArray(JSON.parse(readFileSync(f, 'utf8')).parts)) return f
    } catch {}
  }
  return null
}

/** Cases in a corpus folder: { name, input, answer? }, named by their path in it. */
function cases(dir, prefix = '') {
  const out = []
  const walk = d => {
    for (const f of readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const path = join(d, f.name)
      if (f.isDirectory()) walk(path)
      else if (INPUT.test(f.name)) {
        const name = prefix + relative(dir, path).replace(INPUT, '')
        let answer = answerFor(path)
        if (!answer && basename(d) === 'photo-synthetic') answer = answerFor(join(dirname(d), 'pages', basename(f.name).replace(/-photo-\w+\.\w+$/, '.png')))
        out.push({ name, input: path, answer })
      }
    }
  }
  walk(dir)
  return out
}

/**
 * A held-out case (test/holdout/README.md): test/holdout's, or one in the local test set's own
 * holdout/ folder (EXTRA/holdout), which keeps the same rules.
 */
export const isHeldOut = name => name.startsWith('holdout/') || name.startsWith('extra/holdout/')

/**
 * Every case: test/corpus, then EXTRA's (leaving out its copies of pieces the repo has), then the
 * held-out pages if asked for (HOLDOUT; test/holdout/README.md), the repository's and EXTRA's.
 */
export function allCases(holdout = !!process.env.HOLDOUT) {
  const all = [
    ...cases(join(ROOT, 'test', 'corpus')),
    ...(EXTRA ? cases(EXTRA, 'extra/') : []),
    ...(holdout ? cases(join(ROOT, 'test', 'holdout'), 'holdout/') : []),
  ].filter(c => holdout || !isHeldOut(c.name))
  return all.filter(c => !c.name.startsWith('extra/') || !all.some(o => !o.name.startsWith('extra/') && basename(o.input) === basename(c.input)))
}

/** Short words common in each language the page offers (app/language.js), lower case. */
const WORDS = {
  eng: 'the and of to my thy thee is in with a his he i you all that be for o our we me',
  deu: 'der die das und ich du nicht mein dein im ist zu mit den dem ein sie wie so auf mir dich mich es',
  fra: 'le la les et de des je tu mon ton que qui un une dans est pour pas au du en ma ta',
  ita: 'il lo la le e di che non mi ti per un una con del al nel sei',
  spa: 'el la los las y de que no mi tu por un una con del al en es',
  lat: 'et in dominus domine deus qui tu est nobis dei gloria sanctus agnus pacem eleison kyrie te cum ad',
}
/**
 * The repository's pieces by the language of their words, first match first. A guess from an
 * answer can't tell a word from a syllable (answers keep no hyphens): "Hal-le-lu-jah" counted as
 * French. The local test set has its own, in EXTRA/languages.json ([[pattern, language], ...],
 * matched against a case's path there), so that its pieces aren't named here.
 */
const NAMED = [
  [/faure-apres|cantique/i, 'fra'],
  [/faure-sanctus|faure-agnus|mozart-kyrie|requiem/i, 'lat'],
  [/hallelujah-imslp|hymnal/i, 'eng'],
  [/lieder-|gute-nacht|staendchen|verborgenheit|beethoven/i, 'deu'],
]
const EXTRA_NAMED = EXTRA && existsSync(join(EXTRA, 'languages.json'))
  ? JSON.parse(readFileSync(join(EXTRA, 'languages.json'), 'utf8')).map(([pattern, language]) => [new RegExp(pattern, 'i'), language])
  : []

/**
 * The language a reader would pick on the page for a case's words: by its name, for the corpus's
 * pieces (the test set's hints first, for its own); else the one whose short words its answer's
 * lyrics use most (the held-out songs); else the page's default, English.
 */
export function languageOf(c) {
  const local = c.name.startsWith('extra/') && EXTRA_NAMED.find(([re]) => re.test(c.name.slice('extra/'.length)))
  const named = local || NAMED.find(([re]) => re.test(c.name))
  if (named) return named[1]
  if (!c.answer) return 'eng'
  const words = JSON.parse(readFileSync(c.answer, 'utf8')).parts
    .flatMap(p => (p.notes ?? []).map(n => n.lyric?.toLowerCase().replace(/[^\p{L}]/gu, '')).filter(Boolean))
  const count = code => { const set = new Set(WORDS[code].split(' ')); return words.filter(w => set.has(w)).length }
  const [best] = Object.keys(WORDS).map(code => [code, count(code)]).sort((a, b) => b[1] - a[1])
  return best[1] ? best[0] : 'eng'
}

/** A case's read in a batch folder: its MusicXML files, one a movement. */
export function reads(dir, c) {
  const radix = basename(c.input, extname(c.input))
  const where = [join(dir, radix), dir]
  for (const d of where) {
    if (!existsSync(d)) continue
    const files = readdirSync(d).filter(f => /\.(mxl|musicxml)$/.test(f) && (f === radix + '.mxl' || f === radix + '.musicxml' || f.startsWith(radix + '.mvt'))).sort()
    if (files.length) return files.map(f => join(d, f))
  }
  return []
}

/** Joins movements into one list of parts, measure lists end to end, for scoring. */
export function joined(files) {
  const xmls = files.map(f => musicXmlText(readFileSync(f)))
  if (xmls.length === 1) return xmls[0]
  // score each movement's parts as continuing the first's, by position (good enough for a check)
  const parts = xmls.map(parseMusicXml)
  const widest = parts.reduce((a, b) => (b.length > a.length ? b : a))
  const out = widest.map((p, i) => ({ ...p, measures: parts.flatMap(ps => ps[i]?.measures ?? []) }))
  return toXml(out)
}

/** Minimal MusicXML from parsed parts (only what score.mjs reads back). */
function toXml(parts) {
  const steps = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
  const alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
  const note = n => `<note><pitch><step>${steps[n.midi % 12]}</step>${alters[n.midi % 12] ? '<alter>1</alter>' : ''}<octave>${Math.floor(n.midi / 12) - 1}</octave></pitch>${n.lyric ? `<lyric><text>${n.lyric}</text></lyric>` : ''}</note>`
  return `<score-partwise><part-list>${parts.map(p => `<score-part id="${p.id}"><part-name>${p.name}</part-name></score-part>`).join('')}</part-list>${parts.map(p => `<part id="${p.id}">${p.measures.map(m => `<measure>${m.notes.map(note).join('')}</measure>`).join('')}</part>`).join('')}</score-partwise>`
}
