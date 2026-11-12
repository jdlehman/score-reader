// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Audiveris in the browser, built into WebAssembly (teavm-worker.js, teavm/README.md): the page hands
// it the pages' grey pixels, reads the words it asks for, follows its steps for progress, and offers
// the MusicXML it writes.

import { showScore } from './check.js'
import { readScoreFile } from './score-view.js'
import { readText, startOcr } from './ocr.js'
import { resolveOcrLanguage } from './language.js'
import { imagePages, pdfPages } from './pdf.js'
import { READING } from './settings.js'

/** Audiveris's steps for each page, with roughly how long each takes (seconds, in Chrome on a laptop). */
const STEPS = [
  ['LOAD', 'Opening the page', 0.5],
  ['BINARY', 'Turning it black and white', 3],
  ['SCALE', 'Measuring the staff lines', 0.1],
  ['GRID', 'Finding the staves', 5],
  ['HEADERS', 'Reading clefs, keys and time signatures', 1.7],
  ['STEM_SEEDS', 'Looking for stems', 1.2],
  ['BEAMS', 'Finding beams', 11],
  ['LEDGERS', 'Finding ledger lines', 1.6],
  ['HEADS', 'Finding note heads (the longest part)', 13.5],
  ['STEMS', 'Joining stems to notes', 8.3],
  ['REDUCTION', 'Sorting out overlaps', 0.4],
  ['CUE_BEAMS', 'Looking for small notes', 1.5],
  ['WORDS', 'Reading the words', 4], // ocr.js, between Audiveris's two calls for a page (teavm.js)
  ['TEXTS', 'Placing the words', 1.4],
  ['MEASURES', 'Finding bar lines', 0.1],
  ['CHORDS', 'Grouping notes into chords', 0.1],
  ['CURVES', 'Finding ties and slurs', 3.3],
  ['SYMBOLS', 'Reading other symbols', 2.6],
  ['LINKS', 'Linking symbols to notes', 0.2],
  ['RHYTHMS', 'Working out the rhythm', 0.3],
  ['PAGE', 'Putting the page together', 0.2],
]
const STEP = new Map(STEPS.map(([id, text, s], i) => [id, { text, i, before: STEPS.slice(0, i).reduce((a, x) => a + x[2], 0) }]))
const PAGE_SECONDS = STEPS.reduce((a, x) => a + x[2], 0)
const START_SECONDS = 4 // starting Audiveris (once its 12 MB are downloaded), before the first page

/** What Audiveris writes: plain MusicXML. */
const MUSICXML = 'application/vnd.recordare.musicxml+xml'

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
// another score starts on a fresh page, with nothing left of the last
for (const b of ['again', 'again-failed']) $(b).addEventListener('click', () => location.reload())

const isPdf = f => f.type === 'application/pdf' || /\.pdf$/i.test(f.name)
const isImage = f => f.type.startsWith('image/') || /\.(png|jpe?g|tiff?|bmp)$/i.test(f.name)
const isMusicXml = f => /\.(musicxml|mxl|xml)$/i.test(f.name) || /musicxml/.test(f.type)
const stem = name => name.replace(/\.[^.]+$/, '').trim() || 'score'

/** What Audiveris will read: the grey pages, drawn from the PDF or images chosen (see pdf.js). */
async function prepare(files, onPage) {
  const pdfs = files.filter(isPdf)
  const images = files.filter(isImage)
  if (!files.length) throw new Error('No file was chosen.')
  if (pdfs.length + images.length < files.length) throw new Error(`${files.find(f => !isPdf(f) && !isImage(f)).name} isn’t a PDF or an image.`)
  if (pdfs.length > 1 || (pdfs.length && images.length)) throw new Error('Choose one PDF at a time, or photos of the pages (not both).')
  if (files.some(f => /\.hei[cf]$/i.test(f.name))) throw new Error('HEIC photos can’t be read here. On an iPhone, share the photos as JPEG, or scan the pages with Notes instead.')
  if (pdfs.length) return { ...await pdfPages(new Uint8Array(await pdfs[0].arrayBuffer()), onPage), title: stem(pdfs[0].name) }
  return { ...await imagePages(images, onPage), title: stem(images[0].name) }
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

// ---- progress, from the steps Audiveris reports ----

const progress = {
  t0: 0,
  pages: null,
  page: 0,
  step: null,
  stepAt: 0,
  failedPages: new Set(),
  phase: 'start', // start, pages, export
}

function fraction() {
  const p = progress
  const pages = p.pages ?? 1
  const total = START_SECONDS + PAGE_SECONDS * pages + 1
  if (p.phase === 'start') return Math.min(0.95, (performance.now() - p.t0) / 1000 / total) * (START_SECONDS / (START_SECONDS + 1)) // creeps
  let done = START_SECONDS + PAGE_SECONDS * (p.page - 1)
  const s = STEP.get(p.step)
  if (s) done += s.before + Math.min(STEPS[s.i][2], (performance.now() - p.stepAt) / 1000)
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

/** A step of a page starts, as Audiveris says (page 0: writing the MusicXML). */
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

/** What Audiveris prints, shown under "Details". */
const log = []
function onLine(text) {
  for (const line of String(text).split('\n')) {
    if (!line.trim() || /^\s+at /.test(line)) continue
    log.push(line)
    if (log.length > 400) log.shift()
  }
  $('log').textContent = log.slice(-200).join('\n')
}

// ---- reading ----

let started = false
/** The pick panel's lyric-language choice for this read (a single code, 'eng' by default). */
let ocrLanguage = 'eng'
async function read(files) {
  if (started) return
  if (files.some(isMusicXml)) return open(files)
  started = true
  ocrLanguage = $('ocr-language')?.value ?? 'eng'
  show('work')
  $('work-name').textContent = stem(files[0]?.name ?? '')
  progress.t0 = performance.now()
  const timer = setInterval(render, 500)
  // Tesseract and its data download while the pages are prepared and Audiveris starts, in the
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
  $('status').textContent = 'Starting the reader (it downloads about 12 MB the first time)…'
  progress.pages = input.pages.length
  // in a worker: each page is a minute or more of work that can't be interrupted
  const worker = new Worker(new URL('teavm-worker.js', import.meta.url), { type: 'module' })
  try {
    const { scores, failed } = await new Promise((resolve, reject) => {
      worker.onmessage = ({ data }) => {
        if (data.log !== undefined) onLine(data.log)
        else if (data.step) stepStarts(...data.step)
        else if (data.ocr) {
          // Audiveris passes the language it was told to use; the page resolves it against the
          // pick panel's choice (language.js)
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

/** A MusicXML file chosen instead of pages: nothing to read, straight to checking its notes. */
async function open(files) {
  started = true
  if (files.length > 1) return fail('Open one MusicXML file at a time, or choose a PDF or photos of the pages.')
  const [file] = files
  let xml
  try {
    xml = await readScoreFile(file)
  } catch {
    return fail(`${file.name} couldn’t be opened as MusicXML.`)
  }
  if (!/<score-partwise\b/.test(xml)) return fail(`${file.name} isn’t a MusicXML score that opens here (a partwise one, as notation programs write).`)
  $('done-title').textContent = 'Opened'
  $('done-summary').textContent = `${file.name}: check the notes below, change any that are wrong, and download it with your changes.`
  document.querySelector('#done .next').hidden = true
  show('done')
  // "X (corrected).musicxml" opened again is downloaded as itself, not "X (corrected) (corrected)"
  showScore([new Blob([xml], { type: MUSICXML })], stem(file.name).replace(/ \(corrected\)$/, ''))
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
    a.href = URL.createObjectURL(blob)
    a.download = results.length === 1 ? `${input.title}.musicxml` : `${input.title} (${i + 1}).musicxml`
    a.textContent = results.length === 1 ? `Download ${a.download}` : `Download movement ${i + 1}`
    box.append(a)
  })
  show('done')
  showScore(results, input.title) // the score drawn, to check and correct (check.js)
}

function fail(why) {
  $('failed-why').textContent = why
  show('failed')
}
