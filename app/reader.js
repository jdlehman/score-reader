// Score reader: Audiveris (Java) in the browser through CheerpJ. The page hands Audiveris the
// file, follows its log for progress, and offers the MusicXML it writes.
//
// Copyright (C) 2026 Jonathan Lehman. GNU AGPL v3 or later: see LICENSE.txt.

import { imagesToPdf, pdfToPdf } from './pdf.js'

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
  ['HEADS', 'Finding note heads (the longest part)', 38.9],
  ['STEMS', 'Joining stems to notes', 3.6],
  ['REDUCTION', 'Sorting out overlaps', 0.5],
  ['CUE_BEAMS', 'Looking for small notes', 0.1],
  ['TEXTS', 'Looking for text', 0.1],
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
  if (pdfs.length) return { file: 'score.pdf', bytes: await pdfToPdf(new Uint8Array(await pdfs[0].arrayBuffer()), onPage), title: stem(pdfs[0].name) }
  return { file: 'score.pdf', bytes: await imagesToPdf(images, onPage), title: stem(images[0].name) }
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
async function read(files) {
  if (started) return
  started = true
  show('work')
  $('work-name').textContent = stem(files[0]?.name ?? '')
  progress.t0 = performance.now()
  const timer = setInterval(render, 500)
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
  $('status').textContent = 'Starting the reader (it downloads about 45 MB the first time)…'

  try {
    let finished
    const done = new Promise(resolve => { finished = resolve })
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
      ],
      natives: {
        // our patch calls this when Audiveris is done; Java's shutdown never ends in CheerpJ, so park it here
        async Java_org_audiveris_omr_ScoreReaderHook_finished(lib, failure) {
          finished(!!failure)
          return new Promise(() => {})
        },
      },
    })
    // Audiveris asks the window system which thread it is on, even without windows
    cheerpjCreateDisplay(320, 200, $('display'))
    cheerpOSAddStringFile('/str/' + input.file, input.bytes)
    const jars = new URL('jars/', location.href).pathname
    const classpath = (await (await fetch('jars/classpath.txt')).text()).trim().split('\n').map(j => '/app' + jars + j).join(':')
    cheerpjRunMain('Audiveris', classpath,
      '-batch',
      '-constant', 'org.audiveris.omr.text.tesseract.TesseractOCR.useOCR=false', // Tesseract is native: no text yet
      '-constant', 'org.audiveris.omr.Main.sheetStepTimeOut=3600', // steps take longer than the usual 2 minutes here
      '-transcribe', '-export', '-output', '/files/out', '/str/' + input.file,
    ).then(code => finished(code !== 0))
    const failure = await done
    const results = await outputs(stem(input.file))
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
  const one = await blob(`/files/out/${radix}.mxl`)
  if (one) return [one]
  const movements = []
  for (let n = 1; n < 30; n++) {
    const b = await blob(`/files/out/${radix}.mvt${n}.mxl`)
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
    a.className = 'button primary'
    a.href = URL.createObjectURL(new Blob([blob], { type: 'application/vnd.recordare.musicxml' }))
    a.download = results.length === 1 ? `${input.title}.mxl` : `${input.title} (${i + 1}).mxl`
    a.textContent = results.length === 1 ? `Download ${a.download}` : `Download movement ${i + 1}`
    box.append(a)
  })
  show('done')
}

function fail(why) {
  $('failed-why').textContent = why
  show('failed')
}
