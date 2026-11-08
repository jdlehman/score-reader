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

## Settings for scans of books (app/reader.js)

- `LinesRetriever.maxSlopeDiff=0.05` (Audiveris: 0.025): a staff line may tilt this much more than
  the page. A scanned book page is warped: on one, the top staves tilted −0.032 and the bottom
  ones about 0, against −0.008 for the page, and Audiveris dropped 1 or 2 staves a page (10 of
  12). With 0.05 it found them all. No change on the recognition test's pages, scan or photos.
- `ProcessingSwitches.indentations=false`: no new movement at each indented system. Hymnals
  indent many, and a 5-page hymn came back as 11 movements.

## Photo preflight (app/preflight.js)

Before Audiveris spends a minute a page, the page checks the grey pixels it already made:
binarise, search the tilt from −5° to +5° that levels the staff lines, find the staves by row
projection. If no staves are found, or the staff lines hold under half the page's ink, the
reader warns to rescan before starting Java — a read can't restart without a reload, so a
rescan now is cheaper than gaps later. Reading anyway is allowed. An odd staff count alone
never warns (1- and 3-staff pages are legitimate).

Measured (2026-11-08, spike harness, Node): clean Verovio hymn 4/4 staves, ~0.8 s; the
simulated phone photo of the same page found 0 staves at angle 0 and all 4 after the deskew
search. On clean open pages (Schubert Lieder, Handel Hallelujah) it never false-warned
(confidence 0.62–0.76), but the staff *count* undercounts on real pages (7/9 Lindenbaum,
16/22 Beethoven scan), so the count is reported and never used to decide anything. On
synthetic phone photos of the open pages it warns on the hard ones (Lindenbaum hard: 2
staves, confidence 0.186; Hallelujah hard: 0 staves) and never on the mild ones — and the
warn path fires where Audiveris itself falls apart (Lindenbaum hard: 70 of 216 notes, 0/5
measures valid, against 172/216 on mild/moderate). Node timing on full-size pages is
~2–3 s; browser timing is to be confirmed by running `test/e2e-preflight.mjs` locally.

One bug the tests caught: the angle search first tried −5° upwards and kept the first angle
that tied for best, so a level one-staff page was "corrected" by −0.5°, which spread its
2 px staff lines below the detection threshold. Angles are now tried in order of increasing
|angle|, so 0 wins ties.

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
    node tools/merge.mjs audiveris.mxl tromr-dir/ out.musicxml  # gated TrOMR merge, below

`.work/` (not committed) holds the Audiveris source (`git clone -b 5.11.0`, patch applied), its jars
in `lib/`, `classpath.txt` and a Temurin 25 JDK in `jdk/`: `./setup.sh` makes it.

CheerpJ's community edition is free for non-commercial open-source projects loaded from its CDN,
with a "Built with CheerpJ" credit.

## Gated TrOMR merge (app/merge.js, tools/merge.mjs)

Audiveris is the authority. Polyphonic-TrOMR, run on staff crops, is consulted only where
Audiveris's own output is broken, and only under a gate: a staff slice of a measure is replaced
only when Audiveris's slice is duration-invalid or missing, the TrOMR replacement is itself
duration-valid, AND TrOMR's distinct pitches cover Audiveris's distinct pitches for that slice.
Never a note-list union; a valid Audiveris measure is never touched; only one staff in a
measure is ever replaced. System bar ranges come from Audiveris's own `<print new-system="yes">`
markers, so no Verovio SVG is needed; staff order is top-to-bottom per system.

Why the pitch check: the ungated spike merge fixed Hallelujah validity 41/57 -> 56/56 but lost
pitch 217 -> 213, because Audiveris's "invalid" measures were invalid only in rest durations
while their pitches were right. With the gate, Hallelujah stays at 217 exact pitch and validity
improves (measured in test/merge.test.mjs, which scores the merge against ground truth). The
check is a set of distinct pitches, not a multiset: Audiveris splits one sounding pitch across
voices in divisi, so multiplicity would refuse the divisi case the merge exists for.

Pitches are resolved through the key signature: TrOMR writes no `<alter>` elements (it relies on
the key — F# and C# in D major are bare `<step>F</step>`), while Audiveris writes them explicitly,
so raw steps would call those different pitches and refuse nearly every replacement in a sharp
or flat key.

What it is not: the merge is not wired into the read flow yet. TrOMR has no in-browser runner in
the repo (the spikes used its native `focr` CLI), so `tools/merge.mjs` runs it offline for now,
and no model weights are vendored (TrOMR is ~61 MB). Transcoda is deliberately not a source: it
scored 0/218 on the Hallelujah page.
