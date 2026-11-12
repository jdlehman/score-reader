// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Audiveris in the browser, built into WebAssembly (teavm-worker.js): the page hands it the pages'
// grey pixels, follows its steps for progress, and offers the MusicXML it writes. With
// ?engine=cheerpj it reads with Audiveris's Java through CheerpJ instead, as it used to.

import { readText, startOcr } from './ocr.js'
import { resolveOcrLanguage } from './language.js'
import { imagesToPdf, pdfToPdf } from './pdf.js'
import { BROWSER, READING, asArgs } from './settings.js'

/** Audiveris's steps for each page, with roughly how long each takes (seconds, first page). */
const STEPS = [
  ['LOAD', 'Opening the page', 1.6],
  ['BINARY', 'Turning it black and white', 2.6],
  ['SCALE', 'Measuring the staff lines', 0.1],
  ['GRID', 'Finding the staves', 7.3],
  ['HEADERS', 'Reading clefs, keys and time signatures', 6.5],
  ['STEM_SEEDS', 'Looking for stems', 0.6],
  ['BEAMS', 'Finding beams', 6.4],
  ['LEDGERS', 'Finding ledger lines', 2.3],
  ['HEADS', 'Finding note heads (the longest part)', 18],
  ['STEMS', 'Joining stems to notes', 3.6],
  ['REDUCTION', 'Sorting out overlaps', 0.5],
  ['CUE_BEAMS', 'Looking for small notes', 0.1],
  ['TEXTS', 'Reading the words', 5],
  ['MEASURES', 'Finding bar lines', 0.1],
  ['CHORDS', 'Grouping notes into chords', 0.1],
  ['CURVES', 'Finding ties and slurs', 6.3],
  ['SYMBOLS', 'Reading other symbols', 8.5],
  ['LINKS', 'Linking symbols to notes', 0.4],
  ['RHYTHMS', 'Working out the rhythm', 0.3],
  ['PAGE', 'Putting the page together', 3],
]
const STEP = new Map(STEPS.map(([id, text, s], i) => [id, { text, i, before: STEPS.slice(0, i).reduce((a, x) => a + x[2], 0) }]))
const PAGE_SECONDS = STEPS.reduce((a, x) => a + x[2], 0)
const START_SECONDS = 12 // starting Java and Audiveris, before the first page
const LATER = 0.6 // later pages take this much of the first one's time (Java has compiled Audiveris by then)

/** Where Audiveris finds the score, and what it names its output after. */
const INPUT = '/str/score.pdf'
const OUTPUT_NAME = 'score'
/** Which Audiveris reads: the WebAssembly build (teavm/README.md), or with ?engine=cheerpj, CheerpJ's Java. */
const ENGINE = new URLSearchParams(location.search).get('engine') === 'cheerpj' ? 'cheerpj' : 'teavm'
/** The WebAssembly build writes plain MusicXML; Audiveris on CheerpJ, compressed MusicXML (.mxl). */
const MUSICXML = 'application/vnd.recordare.musicxml+xml'
/** CheerpJ's loader, from its maker's servers: only when it reads. */
const cheerpjLoaded = ENGINE === 'cheerpj' && new Promise((resolve, reject) => {
  const script = document.createElement('script')
  script.src = 'https://cjrtnc.leaningtech.com/5.0/loader.js'
  script.onload = resolve
  script.onerror = () => reject(new Error('CheerpJ couldn’t be loaded (are you online?)'))
  document.head.append(script)
})
if (cheerpjLoaded) cheerpjLoaded.catch(() => {}) // said when a read needs it
/**
 * Where this read's MusicXML goes: a folder of its own. CheerpJ keeps what Java writes in /files
 * between visits, so a fixed folder still held an earlier read's score, which was offered when a
 * read wrote none of its own (it failed) or wrote movements instead. (Java may not write in
 * /files/uploads, the folder CheerpJ clears.)
 */
const OUTPUT = `/files/reads/${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`

const $ = id => document.getElementById(id)
const show = id => { for (const s of ['pick', 'work', 'done', 'failed']) $(s).hidden = s !== id }

// ---- choosing files ----

$('files').addEventListener('change', e => read([...e.target.files]))
document.addEventListener('dragover', e => { e.preventDefault(); document.body.classList.add('dragging') })
document.addEventListener('dragleave', e => { if (!e.relatedTarget) document.body.classList.remove('dragging') })
document.addEventListener('drop', e => {
  e.preventDefault()
  document.body.classList.remove('dragging')
  if (!$('pick').hidden) read([...e.dataTransfer.files])
})
// Audiveris can't be started twice in one page, so another score means a fresh page
for (const b of ['again', 'again-failed']) $(b).addEventListener('click', () => location.reload())

const isPdf = f => f.type === 'application/pdf' || /\.pdf$/i.test(f.name)
const isImage = f => f.type.startsWith('image/') || /\.(png|jpe?g|tiff?|bmp)$/i.test(f.name)
const stem = name => name.replace(/\.[^.]+$/, '').trim() || 'score'

/** What Audiveris will read: a PDF of grey pages, drawn from the PDF or images chosen (see pdf.js). */
async function prepare(files, onPage) {
  const pdfs = files.filter(isPdf)
  const images = files.filter(isImage)
  if (!files.length) throw new Error('No file was chosen.')
  if (pdfs.length + images.length < files.length) throw new Error(`${files.find(f => !isPdf(f) && !isImage(f)).name} isn’t a PDF or an image.`)
  if (pdfs.length > 1 || (pdfs.length && images.length)) throw new Error('Choose one PDF at a time, or photos of the pages (not both).')
  if (files.some(f => /\.hei[cf]$/i.test(f.name))) throw new Error('HEIC photos can’t be read here. On an iPhone, share the photos as JPEG, or scan the pages with Notes instead.')
  if (pdfs.length) return { ...await pdfToPdf(new Uint8Array(await pdfs[0].arrayBuffer()), onPage), title: stem(pdfs[0].name) }
  return { ...await imagesToPdf(images, onPage), title: stem(images[0].name) }
}

/**
 * If the quick look (preflight.js) says Audiveris would give up on a page, say so before the read
 * starts, since a read can't be stopped and started again without reloading the page. Resolves true
 * to read anyway, false to choose other files.
 */
function askToRead(checks) {
  const pages = which => checks.flatMap((c, i) => c?.warn === which ? [i + 1] : [])
  const list = ns => checks.length === 1 ? 'this page' : `${ns.length === 1 ? 'page' : 'pages'} ${ns.join(', ')}`
  const none = pages('no-staves'), small = pages('too-small')
  if (!none.length && !small.length) return Promise.resolve(true)
  const why = []
  if (none.length) why.push(`No staves could be found on ${list(none)}: ${none.length > 1 && checks.length > 1 ? 'they' : 'it'} may be blurred, too faint, too small or not music.`)
  if (small.length) why.push(`The music on ${list(small)} is too small to read: take the photo closer, or use a bigger image.`)
  $('check-why').textContent = why.join(' ')
  $('check').hidden = false
  $('status').textContent = 'Check the pages before reading.'
  return new Promise(resolve => {
    const answer = go => { $('check').hidden = true; resolve(go) }
    $('check-read').onclick = () => answer(true)
    $('check-other').onclick = () => answer(false)
  })
}

// ---- progress, from Audiveris's log ----

const progress = {
  t0: 0,
  pages: null, // known once Audiveris has opened the file
  page: 0,
  step: null,
  stepAt: 0,
  failedPages: new Set(),
  phase: 'start', // start, pages, export
}

function fraction() {
  const p = progress
  const pages = p.pages ?? 1
  // the first page is slower than the rest (Java compiles Audiveris as it goes)
  const total = START_SECONDS + PAGE_SECONDS * (1 + (pages - 1) * LATER) + 3
  if (p.phase === 'start') return Math.min(0.95, (performance.now() - p.t0) / 1000 / total) * (START_SECONDS / (START_SECONDS + 1)) // creeps
  const pageWeight = n => (n === 1 ? 1 : LATER) * PAGE_SECONDS
  let done = START_SECONDS
  for (let n = 1; n < p.page; n++) done += pageWeight(n)
  const s = STEP.get(p.step)
  if (s) done += (pageWeight(p.page) * (s.before + Math.min(STEPS[s.i][2], (performance.now() - p.stepAt) / 1000 * (p.page === 1 ? 1 : 1 / LATER)))) / PAGE_SECONDS
  if (p.phase === 'export') done = total - 1
  return Math.min(0.99, done / total)
}

function render() {
  const p = progress
  const secs = Math.round((performance.now() - p.t0) / 1000)
  $('elapsed').textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`
  $('bar-fill').style.width = `${Math.round(fraction() * 1000) / 10}%`
  if (p.phase === 'pages' && p.step) {
    $('status').textContent = STEP.get(p.step).text + '…'
    $('pages').textContent = p.pages ? `Page ${p.page} of ${p.pages}` : `Page ${p.page}`
  }
}

const log = []
function onLine(text) {
  for (const line of String(text).split('\n')) {
    if (!line.trim() || /^\s+at /.test(line)) continue
    log.push(line)
    if (log.length > 400) log.shift()
    // INFO  [score#2]        null 0    | HEADS
    const m = /^(INFO|WARN|ERROR)\s+\[([^\]]*)\][^|]*\|\s?(.*)$/.exec(line)
    if (!m) continue
    const [, level, tag, message] = m
    const sheet = Number(/#(\d+)/.exec(tag)?.[1] ?? 1)
    const count = /^(\d+) sheets? in /.exec(message)
    if (count) progress.pages = Number(count[1])
    if (STEP.has(message)) {
      progress.phase = 'pages'
      progress.page = sheet
      progress.step = message
      progress.stepAt = performance.now()
    } else if (/^Exporting/.test(message)) {
      progress.phase = 'export'
      $('status').textContent = 'Writing the MusicXML file…'
    } else if (level === 'WARN' && /Error processing stub|Sheet ignored|invalid/i.test(message) && tag.includes('#')) {
      progress.failedPages.add(sheet)
    }
  }
  $('log').textContent = log.slice(-200).join('\n')
}

// CheerpJ writes Java's output to the console
for (const level of ['log', 'info', 'warn', 'error']) {
  const original = console[level].bind(console)
  console[level] = (...args) => { onLine(args.join(' ')); original(...args) }
}

// ---- reading ----

let started = false
/** The pick panel's lyric-language choice for this read (a single code, 'eng' by default). */
let ocrLanguage = 'eng'
async function read(files) {
  if (started) return
  started = true
  ocrLanguage = $('ocr-language')?.value ?? 'eng'
  show('work')
  $('work-name').textContent = stem(files[0]?.name ?? '')
  progress.t0 = performance.now()
  const timer = setInterval(render, 500)
  // Tesseract and its data download while the pages are prepared and Java starts, in the
  // language picked for this score (a pack is ~6-14 MB, cached by the browser afterwards)
  startOcr(ocrLanguage).catch(e => console.warn('Tesseract could not start, so the words will be left out:', e))
  let input
  try {
    input = await prepare(files, (n, of) => {
      progress.pages = of
      $('status').textContent = `Preparing page ${n} of ${of}…`
    })
  } catch (e) {
    clearInterval(timer)
    return fail(e.message)
  }
  if (!await askToRead(input.checks)) {
    clearInterval(timer)
    started = false
    $('files').value = ''
    show('pick')
    return
  }
  if (ENGINE === 'teavm') return readInWasm(input, timer)
  $('status').textContent = 'Starting the reader (it downloads about 45 MB the first time)…'

  try {
    let finished
    const done = new Promise(resolve => { finished = resolve })
    await cheerpjLoaded
    await cheerpjInit({
      version: 25,
      status: 'none',
      // Audiveris wants a home folder
      env: ['HOME=/files/home', 'XDG_CONFIG_HOME=/files/home/config', 'XDG_DATA_HOME=/files/home/data', 'XDG_CACHE_HOME=/files/home/cache'],
      javaProperties: [
        'file.encoding=UTF-8',
        'java.awt.headless=true',
        'sun.java2d.uiScale=1', // skips a screen-scaling check that needs native code
        'com.sun.media.jai.disableMediaLib=true',
        'sun.font.layout.ffm=false', // Java 25's HarfBuzz text layout needs native code; use the older one
        'scorereader.keepSheets=true', // our patch: keep pages in memory (reloading them is slow here)
        'scorereader.inBrowser=true', // our patch: tell the page when done; don't save the project file
        'scorereader.skipFailedPages=true', // our patch: a page Audiveris can't read is left out, not the whole score
      ],
      natives: {
        // our patch calls this when Audiveris is done; Java's shutdown never ends in CheerpJ, so park it here
        async Java_org_audiveris_omr_ScoreReaderHook_finished(lib, failure) {
          finished(!!failure)
          return new Promise(() => {})
        },
        // our patch's OCR: Audiveris asks the page to read the text in an image (see ocr.js).
        // Audiveris passes the language it was told to use; the page resolves it against
        // the pick panel's choice (see language.js — Audiveris's default is always 'eng',
        // so a non-default panel choice wins, or the selector would do nothing).
        async Java_org_audiveris_omr_text_BrowserOCR_read(lib, grey, width, height, languages, pageSegMode) {
          try {
            return await readText(grey, width, height, pageSegMode, resolveOcrLanguage(languages, ocrLanguage))
          } catch (e) {
            console.warn('Tesseract failed, so this text is left out:', e)
            return ''
          }
        },
      },
    })
    // Audiveris asks the window system which thread it is on, even without windows
    cheerpjCreateDisplay(320, 200, $('display'))
    cheerpOSAddStringFile(INPUT, input.bytes)
    const jars = new URL('jars/', location.href).pathname
    const classpath = (await (await fetch('jars/classpath.txt')).text()).trim().split('\n').map(j => '/app' + jars + j).join(':')
    cheerpjRunMain('Audiveris', classpath,
      '-batch',
      ...asArgs([...BROWSER, ...READING]), // see settings.js
      '-transcribe', '-export', '-output', OUTPUT, INPUT,
    ).then(code => finished(code !== 0))
    const failure = await done
    const results = await outputs(OUTPUT_NAME)
    clearInterval(timer)
    render()
    if (!results.length) {
      return fail(progress.pages === 0 || failure
        ? 'Audiveris couldn’t find music it could read. Check the file is sheet music with five-line staves, and try a clearer scan or the original PDF.'
        : 'Audiveris finished without writing a score.')
    }
    finish(input, results)
  } catch (e) {
    clearInterval(timer)
    console.error(e)
    fail('Something went wrong in the reader: ' + (e.message || e) + '. Reload the page to try again.')
  }
}

/**
 * Read with Audiveris in WebAssembly, in a worker (teavm-worker.js): the pages' grey pixels go to
 * it, the words it asks for are read here (ocr.js, as for CheerpJ), and MusicXML comes back.
 */
async function readInWasm(input, timer) {
  $('status').textContent = 'Starting the reader (it downloads about 12 MB the first time)…'
  progress.pages = input.pages.length
  const worker = new Worker(new URL('teavm-worker.js', import.meta.url), { type: 'module' })
  try {
    const { scores, failed } = await new Promise((resolve, reject) => {
      worker.onmessage = ({ data }) => {
        if (data.log !== undefined) onLine(data.log)
        else if (data.step) stepStarts(...data.step)
        else if (data.ocr) {
          const { grey, width, height, pageSegMode, languages } = data.ocr
          readText(grey, width, height, pageSegMode, resolveOcrLanguage(languages, ocrLanguage))
            .catch(e => {
              console.warn('Tesseract failed, so this text is left out:', e)
              return ''
            })
            .then(text => worker.postMessage({ id: data.id, text }))
        } else if (data.done) resolve(data.done)
        else if (data.error) reject(new Error(data.error))
      }
      worker.onerror = e => reject(new Error(e.message || 'the reader stopped'))
      worker.postMessage({ pages: input.pages, constants: READING, languages: ocrLanguage }, input.pages.map(p => p.grey.buffer))
    })
    for (const n of failed) progress.failedPages.add(n)
    clearInterval(timer)
    render()
    if (!scores.length) return fail('Audiveris couldn’t find music it could read. Check the file is sheet music with five-line staves, and try a clearer scan or the original PDF.')
    finish(input, scores.map(xml => new Blob([xml], { type: MUSICXML })))
  } catch (e) {
    clearInterval(timer)
    console.error(e)
    fail('Something went wrong in the reader: ' + (e.message || e) + '. Reload the page to try again.')
  } finally {
    worker.terminate()
  }
}

/** A step of a page starts, as the WebAssembly reader says (page 0: writing the MusicXML). */
function stepStarts(page, id) {
  if (page === 0) {
    progress.phase = 'export'
    $('status').textContent = 'Writing the MusicXML file…'
  } else if (STEP.has(id)) {
    progress.phase = 'pages'
    progress.page = page
    progress.step = id
    progress.stepAt = performance.now()
  }
}

/** The MusicXML files Audiveris wrote: one, or one per movement. */
async function outputs(radix) {
  const blob = async path => {
    try {
      const b = await cjFileBlob(path)
      return b && b.size ? b : null
    } catch {
      return null
    }
  }
  const one = await blob(`${OUTPUT}/${radix}.mxl`)
  if (one) return [one]
  const movements = []
  for (let n = 1; n < 30; n++) {
    const b = await blob(`${OUTPUT}/${radix}.mvt${n}.mxl`)
    if (!b) break
    movements.push(b)
  }
  return movements
}

function finish(input, results) {
  const secs = Math.round((performance.now() - progress.t0) / 1000)
  const time = secs >= 90 ? `${Math.round(secs / 6) / 10} minutes` : `${secs} seconds`
  const pages = progress.pages ?? 1
  const failed = [...progress.failedPages].sort((a, b) => a - b)
  $('done-title').textContent = failed.length ? 'Done, with gaps' : 'Done'
  $('done-summary').textContent = `Read ${pages} page${pages === 1 ? '' : 's'} in ${time}.` +
    (failed.length ? ` Page${failed.length === 1 ? '' : 's'} ${failed.join(', ')} couldn’t be read and ${failed.length === 1 ? 'is' : 'are'} missing.` : '') +
    (results.length > 1 ? ` The music is in ${results.length} movements, a file each: Audiveris starts a new movement where the music starts afresh, as at a new title.` : '')
  const box = $('downloads')
  results.forEach((blob, i) => {
    const a = document.createElement('a')
    const ext = blob.type === MUSICXML ? 'musicxml' : 'mxl'
    a.className = 'button primary'
    a.href = URL.createObjectURL(blob.type === MUSICXML ? blob : new Blob([blob], { type: 'application/vnd.recordare.musicxml' }))
    a.download = results.length === 1 ? `${input.title}.${ext}` : `${input.title} (${i + 1}).${ext}`
    a.textContent = results.length === 1 ? `Download ${a.download}` : `Download movement ${i + 1}`
    box.append(a)
  })
  show('done')
}

function fail(why) {
  $('failed-why').textContent = why
  show('failed')
}
