# How Audiveris runs in the browser (CheerpJ)

Audiveris 5.11 runs unchanged on CheerpJ 5.0's Java 25 runtime, with these settings and patches.
One clean page (gen-02-open from midi_studio's recognition test) reads in about 100 s, against
19 s natively, and the result is the same (100% of notes).

## Settings (app/reader.js)

- `env`: HOME and XDG folders (Audiveris needs a home).
- `sun.java2d.uiScale=1`: skips a screen-scaling check that loads JNA.
- `sun.font.layout.ffm=false`: Java 25 lays out text with HarfBuzz through the foreign-function
  API, which CheerpJ lacks; this uses the older path. Audiveris lays out its music font to find clefs.
- `TesseractOCR.useOCR=false`: Audiveris's own Tesseract is native code, so it stays off; the page
  reads the text instead (`BrowserOCR`, below).
- `Main.sheetStepTimeOut=3600`: some steps take over the default 120 s in the browser.
- `cheerpjCreateDisplay`: Audiveris asks Swing which thread it is on, even in batch mode.

## Patches (patches/0001-score-reader.patch, on Audiveris 5.11.0)

- Keep sheets in memory (`scorereader.keepSheets`): batch mode saves each sheet and reloads it to
  export, which took 5 minutes in the browser.
- `ScoreReaderHook.finished`: Audiveris's shutdown never ends in CheerpJ, so it tells the page
  when it is done (a JavaScript native) and is parked there.
- No project file saved at the end in the browser (`scorereader.inBrowser`).
- Lighten each sheet once it is done (`Sheet.lightenForExport`, with keepSheets): drop its
  images and its glyph index. CheerpJ never frees objects held only by weak references (a test
  held 5 weakly referenced arrays through 10 rounds of garbage; desktop Java freed them at
  once), and Audiveris holds a page's images and every glyph it tries that way. The export
  needs neither; the MusicXML is the same as the release's on 9 pages (one movement varies in
  its staccatos from run to run, in the release too).
- `FlatMorphology`: the closing filter that finds beam spots, rewritten. The original calls a
  helper per pixel whose erosion branch CheerpJ never compiled (it compiles only branches seen
  taken), so half the calls ran in the interpreter. Same output (checked against the original on
  the page and 300 random images); beams went from 73 s to 6 s.
- `BrowserOCR`: reading text (words, titles, part names) in the browser. `OcrUtil` picks it when
  `scorereader.inBrowser` is set. It hands the page each image Audiveris would give Tesseract, as
  grey bytes (a CheerpJ native), and the page reads it with tesseract.js, the same Tesseract in
  WebAssembly, with its legacy engine as `TesseractOrder` uses and the same English data
  (`app/ocr.js`). Lines, words and characters come back with their boxes and baselines, but no
  font attributes: a word's font size comes from its line's height, and `TextWord` fits the size
  to the word's bounds anyway. On four test pieces (clean pages) it reads 64–77% of the
  syllables, against 76–86% for desktop Audiveris on the same pages, and all the part names; on a
  scan and on photos, 76%. Both use the same engine and data, and on the same image tesseract.js
  reads what desktop Tesseract reads; most of the gap was the page's antialiasing (below), and the
  rest is still to find.
- `MetronomeInter.isParsed`: a line that only looks like a tempo mark (OCR read "J: 88" for
  "J = 88") is exported as plain words. Before, its export failed on a null model.
- `PeakGraph.joinByLeftLines`: staves that no bar line connects but a thin line left of their
  start does are one system. Hymnals and choir books with organ give each choir its own bar lines
  and join the whole system by a thin line outside the brackets, which Audiveris missed, so it
  split every system into its groups (a page of 3 systems of 4 staves read as 5 systems). The line
  must cross the whole gap between the staves, nearly unbroken, and be thin. No change on the test
  pieces (identical MusicXML).
- `Template.evaluate` on plain arrays: matching note-head templates is most of the HEADS step, and
  it read the distance table through a list iterator and two interface calls a point, which
  CheerpJ runs far slower than the arithmetic. For a `Table.Short` it now reads the array
  directly, the template's key points copied into arrays once (`Table.Short.rawData`), and each
  anchor's offset worked out once (`upperLeft` allocated two points and rounded twice a call).
  The same values in the same order: the MusicXML is identical. Note heads on a page went from
  33 s to 18 s, the page from 91 s to 75 s.

## Pages as Audiveris draws them (app/pdf.js)

Audiveris draws a PDF's pages without antialiasing (`ImageLoading`), so drawn music and text come
out crisp. PDF.js antialiases, and Audiveris's binarization reads the grey edges as ink: letters
thicken by a third, and Tesseract reads "e" as "c". On a test page, 79 of its syllables came out
right, against 133 from the PDF itself. So the page makes a page of drawn shapes black and white
at half coverage, as Audiveris would draw it (129 right); a page with images, a scan, keeps its
greys, as Audiveris keeps an image's.

## FastMath (java/org/scorereader)

Java 25's Math.abs, min, max, rint, floor, ceil, sqrt and hypot use raw-bit conversions or
bit-by-bit algorithms, which CheerpJ runs 40 to 300 times slower than native (plain arithmetic is
about 10 times). `Rewrite.java` points every jar's calls at `FastMath`, which gives the same
results (sqrt within one ulp) with comparisons and arithmetic: 2,948 calls. Note heads went from
105 s to 39 s.

## Times on gen-02-open (seconds)

| | start | beams | heads | whole page |
|---|---|---|---|---|
| desktop | | 3.7 | 5.6 | 19 |
| browser, as is | 11 | 75 | 105 | 234 |
| + FastMath | 11 | 73 | 39 | 172 |
| + FlatMorphology, no save | 11 | 6 | 39 | 100 |

Tried and no help: Audiveris's parallelism off (`OmrExecutors.useParallelism=false`); CheerpJ's
`wasmGC` mode crashes ("illegal cast") on any program here, Java 21 or 25.

## Running it

    ./build.sh                          # patched classes, rewritten jars, the site
    npm run serve &                     # static server with ranges, port 8787
    node test/e2e.mjs one score.pdf     # read a score with the page, in Chrome
    node test/profile.mjs HEADS 25      # where a step spends its time, on .work/page.png
    EXTRA='&fast=0' node test/profile.mjs HEADS 25   # the same without FastMath

`.work/` (not committed) holds the Audiveris source (`git clone -b 5.11.0`, patch applied), its jars
in `lib/`, `classpath.txt` and a Temurin 25 JDK in `jdk/`: `./setup.sh` makes it.

CheerpJ's community edition is free for non-commercial open-source projects loaded from its CDN,
with a "Built with CheerpJ" credit.
