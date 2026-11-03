# Spike: Audiveris in the browser (CheerpJ)

Audiveris 5.11 runs unchanged on CheerpJ 5.0's Java 25 runtime, with these settings and patches.
One clean page (gen-02-open from midi_studio's recognition test) reads in about 100 s, against
19 s natively, and the result is the same (100% of notes).

## Settings (spike/index.html)

- `env`: HOME and XDG folders (Audiveris needs a home).
- `sun.java2d.uiScale=1`: skips a screen-scaling check that loads JNA.
- `sun.font.layout.ffm=false`: Java 25 lays out text with HarfBuzz through the foreign-function
  API, which CheerpJ lacks; this uses the older path. Audiveris lays out its music font to find clefs.
- `TesseractOCR.useOCR=false`: Tesseract is native; no words for now.
- `Main.sheetStepTimeOut=3600`: some steps take over the default 120 s in the browser.
- `cheerpjCreateDisplay`: Audiveris asks Swing which thread it is on, even in batch mode.

## Patches (patches/0001-score-reader.patch, on Audiveris 5.11.0)

- Keep sheets in memory (`scorereader.keepSheets`): batch mode saves each sheet and reloads it to
  export, which took 5 minutes in the browser.
- `ScoreReaderHook.finished`: Audiveris's shutdown never ends in CheerpJ, so it tells the page
  when it is done (a JavaScript native) and is parked there.
- No project file saved at the end in the browser (`scorereader.inBrowser`).
- `FlatMorphology`: the closing filter that finds beam spots, rewritten. The original calls a
  helper per pixel whose erosion branch CheerpJ never compiled (it compiles only branches seen
  taken), so half the calls ran in the interpreter. Same output (checked against the original on
  the page and 300 random images); beams went from 73 s to 6 s.

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

    spike/build.sh                         # patched classes, rewritten jars, classpath
    node spike/serve.mjs &                 # static server with ranges, port 8787
    EXTRA='&fast=1' node spike/drive.mjs   # one page; result in .work/spike-result.mxl
    EXTRA='&fast=1' node spike/profile.mjs HEADS 25   # where a step spends its time

`.work/` (not committed) holds the Audiveris source (`git clone -b 5.11.0`, patch applied), its jars
in `lib/`, `classpath.txt` and a Temurin 25 JDK in `jdk/`.

CheerpJ's community edition is free for non-commercial open-source projects loaded from its CDN,
with a "Built with CheerpJ" credit.
