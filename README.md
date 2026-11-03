# Score Reader

Turn a PDF or photos of sheet music into a MusicXML file, in the browser. Nothing is uploaded:
the music is read on the visitor's own computer.

It runs [Audiveris](https://github.com/Audiveris/audiveris) 5.11, the open-source music reader
(Java), with [CheerpJ](https://cheerpj.com), which runs Java in the browser. It was made for
[Sectional](https://inlehmansterms.net/sectional/), a choir practice app that opens MusicXML, and
works for anything that opens MusicXML (MuseScore, Finale, Sibelius, Dorico).

## How it works

1. The page draws the pages itself: a PDF's with [PDF.js](https://mozilla.github.io/pdf.js/) at
   300 dpi, photos with the browser (which applies a phone's rotation). It makes them grey and
   hands Audiveris one PDF of plain pixel pages (`app/pdf.js`). In the browser Audiveris can't
   read most PDFs and photos itself: Java's JPEG decoder and colour management are native code
   that CheerpJ can't run to the end.
2. Audiveris reads them in batch mode (`-transcribe -export`) and writes a `.mxl` file, which the
   page offers to download (`app/reader.js`). Its log drives the progress bar. When Audiveris
   reads text, the page reads it for it with tesseract.js (`app/ocr.js`).

Audiveris is used as released, with a few changes for the browser (`patches/`) and every jar's
`Math` calls pointed at a faster `FastMath` (`java/`). `NOTES.md` explains them and how the
time came down from 4 minutes a page to about 1.

Words, titles and part names are read with Tesseract, as desktop Audiveris reads them, but with
tesseract.js in the page (`app/ocr.js`), since Tesseract itself is native code.

Limits: a one-page score takes a minute or two, and each page after it under a minute (9 pages:
under 7 minutes). Memory reaches about 1 GB on 9 pages. The first visit downloads about 60 MB
(Java and Audiveris, and Tesseract with its English data). Tested in Chrome.

## Building

Needs Node, git and curl, on macOS or Linux. `./setup.sh` makes `.work/` (not committed): the
Audiveris 5.11.0 source with `patches/0001-score-reader.patch` applied, the jars of its release
(from the installer: there is no plain download of them) and a Temurin JDK 25.

    ./setup.sh           # .work/: about 300 MB to download
    npm install          # PDF.js, and Playwright for the test
    ./build.sh           # the site, in dist/ (./build.sh page rebuilds only the page)
    npm run serve        # http://127.0.0.1:8787/dist/
    node test/e2e.mjs pdf1 some-score.pdf   # read a score in Chrome; results in .work/e2e/

`.github/workflows/pages.yml` does the same on GitHub and publishes `dist/` with GitHub Pages.

## Licence

GNU Affero General Public License v3 or later, like Audiveris: see `LICENSE`. `NOTICE.txt` lists
the licences of Audiveris's libraries and of PDF.js, and where their source is. The site serves the
source of the libraries under copyleft licences next to their jars (`source/`, fetched by
`setup.sh` from Maven Central), and each jar `Rewrite` changes says so inside it. CheerpJ is loaded from Leaning Technologies'
servers under its community licence for non-commercial open-source projects; it is not part of
this repository.
