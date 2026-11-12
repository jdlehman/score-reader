# Score Reader

Turn a PDF or photos of sheet music into a MusicXML file, in the browser. Nothing is uploaded:
the music is read on the visitor's own computer.

It runs [Audiveris](https://github.com/Audiveris/audiveris) 5.11, the open-source music reader
(Java), compiled to WebAssembly with [TeaVM](https://teavm.org) (`teavm/`). It was made for
[Sectional](https://inlehmansterms.net/sectional/), a choir practice app that opens MusicXML, and
works for anything that opens MusicXML (MuseScore, Finale, Sibelius, Dorico).

## How it works

1. The page draws the pages itself: a PDF's with [PDF.js](https://mozilla.github.io/pdf.js/) at
   300 dpi, photos with the browser (which applies a phone's rotation), and makes them grey
   (`app/pdf.js`). Audiveris in WebAssembly has no image decoders or PDF reader of its own.
2. A worker runs Audiveris on them, page by page (`app/teavm-worker.js`, `app/teavm.js`), and it
   writes MusicXML, which the page offers to download (`app/reader.js`). Its steps drive the
   progress bar. When Audiveris reads text, the page reads it for it with tesseract.js
   (`app/ocr.js`).

Audiveris is used as released, with our changes (`patches/`, the same on the desktop) and the ones
WebAssembly needs (`teavm/`). `NOTES.md` explains them; `teavm/README.md` explains the build.

Words, titles and part names are read with Tesseract, as desktop Audiveris reads them, but with
tesseract.js in the page (`app/ocr.js`), since Tesseract itself is native code.

Limits: a page takes about a minute (a crowded orchestral page much longer), and memory reaches
about 1 GB. The first visit downloads about 30 MB (Audiveris, and Tesseract with its English
data). Tested in Chrome.

Until November 2026 the page ran Audiveris's Java with [CheerpJ](https://cheerpj.com), loaded from
Leaning Technologies' servers; WebAssembly reads the test corpus as well (`NOTES.md`), a little
faster, and from this site alone.

## Building

Needs Node, git and curl, on macOS or Linux. `./setup.sh` makes `.work/` (not committed): the
Audiveris 5.11.0 source with `patches/0001-score-reader.patch` applied, the jars of its release
(from the installer: there is no plain download of them), a Temurin JDK 25 and TeaVM's jars.

    ./setup.sh           # .work/: about 340 MB to download
    npm install          # PDF.js, tesseract.js, and Playwright for the test
    ./build.sh           # the site, in dist/, in about a minute (./build.sh page rebuilds only the page)
    npm run dev          # http://127.0.0.1:8787/
    node test/e2e.mjs pdf1 some-score.pdf   # read a score in Chrome; results in .work/e2e/
    npm run corpus       # read the test corpus, with desktop Audiveris or (ENGINE=teavm) the browser's

`.github/workflows/pages.yml` does the same on GitHub and publishes `dist/` with GitHub Pages.

## Licence

GNU Affero General Public License v3 or later, like Audiveris: see `LICENSE`. `NOTICE.txt` lists
the licences of Audiveris's libraries, TeaVM, PDF.js and tesseract.js, and where their source is.
The site serves the source of the libraries under copyleft licences (`source/`, fetched by
`setup.sh` from Maven Central), and the licence files in the libraries' jars (`licenses/`).
