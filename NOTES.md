# How Audiveris runs in the browser (CheerpJ)

Audiveris 5.11 runs unchanged on CheerpJ 5.0's Java 25 runtime, with these settings and patches.
One clean page (gen-02-open from midi_studio's recognition test) reads in about 100 s, against
19 s natively, and the result is the same (100% of notes).

## Settings (app/reader.js, app/settings.js)

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
- A page Audiveris can't read is left out, not the whole score (`scorereader.skipFailedPages`,
  `Book.skipFailed`), and stays out: leaving a page out undoes its steps, so every later book
  step read it again (3 times before the export), failing each time. That took seconds on the
  desktop and about 4 minutes a time in the browser, where a 5-page hymnal with 2 bad pages
  never finished.
- `Voices.refineSystem` skips a part that has no measure in a stack. A hymnal page (choirs joined
  by a thin line left of their brackets, partial bar lines) had such a stack, and the whole page
  was lost to a NullPointerException; now it reads, 4 parts. Desktop Audiveris read that page only
  because its own OCR changed the layout a little; with OCR off (as the browser reads, through
  tesseract.js) it failed the same way, with the line number CheerpJ doesn't give. (CheerpJ's
  stack names the wrong frame here: it pointed at `Measure.purgeVoices`, and a guard there was
  no help.)
- The MusicXML export no longer loses a whole measure when a hairpin's chord has no time
  (`PartwiseBuilder.WedgeIterators`). When the rhythm step can't time a chord (a voice "too
  long"), sorting the measure's hairpin starts and stops threw, and the export left the measure
  out of that part: two piano bars of "Der Lindenbaum", 80% of its notes read, now 95%.
- A one-sign key change is a key on every staff of the system (`KeyInter.lookupCandidates`).
  Audiveris takes a lone ♭ or ♯ with a note close after it for that note's accidental. A change
  to one flat drawn without cancelling naturals (Gute Nacht, page 4) was read as a key on the
  voice staff and as accidentals on the piano staves, whose chords follow it closely: the piano
  kept the old key for 7 bars (94%, now 100%). Now such a sign is a key when another staff of the
  system has that key change within a staff space of it.
- A treble clef with a small "8" apart from it, just below, is a tenor's octave clef
  (`ClefBuilder.lookForOctave`). LilyPond draws it so, and the classifier knows the 8 only
  joined to the clef: apart, the clef alone graded better as a plain treble clef, and every
  tenor note was read an octave high (BWV 227, 24 pages: 76% of notes, now 97-100% a page).
  Below only: looking above too took a tempo mark or bar number over a soprano's clef for an
  8 (four pages a soprano read an octave high).
- An 8va or 8vb line is as long as it is drawn (`OctaveShiftInter.create`, `traceLine`).
  Audiveris made every octave line 3 staff spaces long, so only the first chord or two under
  it were moved an octave: the dashed line is now followed on the page, in the rows around
  the 8 (engravers draw it level with the sign's top, middle or bottom). The row with the most
  dashes wins; a run longer than 2 staff spaces is not a dash. Wolf's "Verborgenheit", an 8va
  over three bars of the piano: 92%, now 100%. The export also takes a line with no chord at
  an end to its own end (`PartwiseBuilder.getOctaveShift`), where it skipped the line.
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
  WebAssembly, with its legacy engine as `TesseractOrder` uses and the language data the score
  was picked in (`app/ocr.js`, `app/language.js`). Lines, words and characters come back with their boxes and baselines, but no
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
- `PartCollation`: which part of one system continues which part of another, across a score.
  Audiveris matched them by position and staff count, and by name only as OCR read it: any name,
  however garbled ("r", "sorrumos"), kept a part from joining one named otherwise or not named. A
  hymnal whose layout changes every few systems (solo and organ, chorus on two staves, two
  choirs) came out as 11 parts, one of them treble and bass staves mixed. Now staves that open
  with a treble clef and a bass clef are never the same part (a C clef, rare in choir music and
  the likeliest misreading, agrees with either), and names keep parts apart only when both are
  read and name different voices or instruments, or are both whole words that differ. That
  hymnal: 6 parts, none mixed. On the recognition test's 51 pages, 45 are unchanged and 6 photos
  improve (Audiveris broke their systems into single staves, and the soprano and alto staff no
  longer joins the tenor and bass part).
- `Template.evaluate` on plain arrays: matching note-head templates is most of the HEADS step, and
  it read the distance table through a list iterator and two interface calls a point, which
  CheerpJ runs far slower than the arithmetic. For a `Table.Short` it now reads the array
  directly, the template's key points copied into arrays once (`Table.Short.rawData`), and each
  anchor's offset worked out once (`upperLeft` allocated two points and rounded twice a call).
  The same values in the same order: the MusicXML is identical. Note heads on a page went from
  33 s to 18 s, the page from 91 s to 75 s.

## A quick look before reading (app/preflight.js)

Each photo and scanned page (not drawn PDF pages) gets a look while it is prepared, about 0.3 s a
page. If Audiveris would give up on a page, the page says why and asks before the read starts,
since a read can't be stopped and started again without reloading. Audiveris gives up when it
finds no staves ("No regularly spaced lines found") or when staff lines are under 11 pixels apart
(`ScaleBuilder.minInterline`; "too low interline value").

- Ink is a pixel clearly darker than its neighbourhood, so a dark table or a shadow doesn't count.
- Staves are found in 12 vertical strips, each at its own tilt (a photo's perspective tilts lines
  differently across the page): five evenly spaced rows of ink in at least 3 strips.
- On midi_studio's recognition test: all 20 phone photos (which Audiveris reads at 74–91% of
  notes), every scan and clean page, and the hymnal pass; a blank page and photos shrunk below
  Audiveris's limit warn, and Audiveris rejects those. Staff counts and spacings come out right.
- `test/e2e-check.mjs` checks the warning in Chrome with two photos of a recognition-test piece:
  desktop Audiveris reads `photo.jpg` and rejects `photo-small.jpg` (spacing 9 pixels).

## Lyric language (app/language.js, app/ocr.js)

The pick panel asks for the language of the words: English (the default), German, French,
Italian, Spanish or Latin, one a score.

- `reader.js` reads the choice when a read starts and `startOcr` downloads that language's data
  while the pages are prepared. For each image Audiveris hands over, `resolveOcrLanguage` picks
  the panel's choice over Audiveris's own, because Audiveris always asks for English.
- `BrowserOCR.LANGUAGES` (in the patch) lists all six, so Audiveris doesn't refuse them.
- `build.sh` serves `@tesseract.js-data/<code>/4.0.0` for all six: the standard data, which the
  legacy engine needs (`tessdata_fast` works only with the newer engine). From 5.7 MB (Latin) to
  13.9 MB (English); a browser downloads only the one picked, and keeps it.
- One worker reads one language; a new language ends the old worker. If a language's data fails
  to load, the words are read in English from then on.
- What it buys: accents. On a line of German lyrics, English data reads "Grü- ße, schö- ne Mül-"
  as "Grii- Be, sché- ne Mﬁl-"; German data reads it right, and French data reads French the
  same way (`test/language.test.mjs`). Without accents the words come out alike.

## Settings for scans of books (app/settings.js)

- `LinesRetriever.maxSlopeDiff=0.1` (Audiveris: 0.025) and `maxFilamentRotation=0.2` (0.1): a
  staff line may tilt this much more than the page, and bend this much along its length. A
  scanned book page is warped: on one, the top staves tilted −0.032 and the bottom ones about 0,
  against −0.008 for the page, and Audiveris dropped 1 or 2 staves a page (10 of 12); 0.05 found
  them all. Near the binding the lines also bend, and Audiveris kept only their straight part:
  a hymnal's staves started 400–900 pixels late, so a system lost its join (page 3) and staves
  lost their clefs and keys (page 5). Both settings together found every staff's true start.
  On the recognition test's 71 inputs (pages, scans, photos, PDFs) the staves and systems are
  unchanged (one staff end moves a pixel).
- `ProcessingSwitches.indentations=false`: no new movement at each indented system. Hymnals
  indent many, and a 5-page hymn came back as 11 movements.
- `LinesRetriever.minStaffLength=15` (Audiveris: 30 staff spaces): a song's last system can
  be one short bar, under 30 staff spaces long, and Audiveris dropped its staves before
  looking at them ("Erlkönig" 75% of notes, now 85%; "Ständchen" 91%, now 100%).

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
    npm run corpus                      # read test/corpus/ with desktop Audiveris, score it (see its README)
    EXTRA='&fast=0' node test/profile.mjs HEADS 25   # the same without FastMath

`.work/` (not committed) holds the Audiveris source (`git clone -b 5.11.0`, patch applied), its jars
in `lib/`, `classpath.txt` and a Temurin 25 JDK in `jdk/`: `./setup.sh` makes it.

CheerpJ's community edition is free for non-commercial open-source projects loaded from its CDN,
with a "Built with CheerpJ" credit.
