# How Score Reader reads music

Score Reader runs Audiveris 5.11 with the changes and settings below. The Java changes are in
`patches/0001-score-reader.patch` and are the same on the desktop (the corpus test's
`ENGINE=desktop`) and in the browser. The browser build adds what TeaVM needs (`teavm/README.md`,
`teavm/FIXES.md`). `test/corpus/README.md` explains how a change is proved better (`test/prove.mjs`).

## Changes to Audiveris (patches/0001-score-reader.patch)

**Reading a whole book.** The browser build reads page by page itself
(`teavm/entry/src/teavm/TeavmMain.java`): it keeps each sheet in memory, lightens it when done and
leaves out a page that fails. These switches make desktop batch mode (the corpus test's
`ENGINE=desktop`) do the same.
- `scorereader.keepSheets`: sheets stay in memory for the export, where batch mode saves each one
  to disk and loads it again.
- `Sheet.lightenForExport`: a finished sheet drops its images and glyph index, which the export
  doesn't need and which hold most of its memory.
- `scorereader.skipFailedPages`, `Book.skipFailed`: a page Audiveris can't read is left out, not
  the whole score, and stays out. Otherwise every later book step reads it again and fails again.

**Layout: systems, staves, parts**
- `PeakGraph.joinByLeftLines`: staves joined by a thin line left of their start, with no barline
  across them, are one system. Hymnals and choir books with organ join their choirs that way. The
  line must cross the whole gap between the staves, nearly unbroken, and be thin.
- `PartCollation`: which part of one system continues which part of another. Staves that open
  with a treble clef and with a bass clef are never the same part (a C clef agrees with either).
  Names keep parts apart only when both are read and name different voices or instruments, or are
  different whole words, so a garbled OCR'd name doesn't split a part.
- `BarsRetriever.freezeFullColumns`: barlines found in every staff of a system are kept, as
  barlines that join staves already are. A choir's barlines stop at each staff to leave room for
  the words, and without this one could later be read as a stem, merging two bars. Each must run
  from its staff's first line to its last, within half a staff space (`maxFrozenBarShortfall`).
- `BarsRetriever.pageBraces`: a system found with no brace takes the braces that more than half of
  the sheet's other systems with the same staves (count, line counts, sizes) share. A piano brace
  missed on one system made its two staves new parts, cut off from the parts around them.
- `Voices.refineSystem` skips a part with no measure in a stack, where Audiveris threw and lost the
  page.
- `ClefBuilder.HEADER_CLEF_SHAPES`: no percussion clef at the start of a 5-line staff (a 1-line
  staff still takes one). On a staff whose start is cut off, stems and a rest were read as one.

**Symbols**
- `ScaleBuilder`: beam height is a peak in the lengths of black vertical runs, between 0.45 and 1
  staff space. A peak at the very bottom of that range now counts when it has at least twice the
  runs of the best peak inside it. Thin beams (LilyPond's) sit there, and `getLocalMaxima` never
  finds a peak at an end of its range; missed, their sixteenths are read as quarters.
- `NoteHeadsBuilder`, `wholeCatalog`: whole notes are matched with Leland's template as well as
  Bravura's, the better kept. Bravura's whole note is wider than MuseScore's or LilyPond's.
- `ClefBuilder.lookForOctave`: a treble clef with a small "8" just below it is the tenors' octave
  clef, as LilyPond draws it. The 8 may stand apart, a small glyph centred under the clef, or touch
  the clef's curl (LilyPond 2.24), and so be part of the clef's own glyph: a treble clef ends 1.5
  to 2.1 staff spaces below the staff, so a glyph reaching 2.2 to 3.2 below, with a hole in its ink
  there, ends in the 8. Only below: above it, a tempo mark or bar number can pass for the 8.
- `KeyInter.lookupCandidates`: a lone ♭ or ♯ is a key change when another staff of the system has
  the same change within a staff space of it. Otherwise Audiveris takes it for the accidental of
  the note just after it, and a part keeps the old key.
- `OctaveShiftInter.create`, `traceLine`: an 8va or 8vb line covers every note under its drawn
  length. The dashes are followed in the rows around the 8 (the row with most dashes wins; a run
  longer than 2 staff spaces is not a dash). `PartwiseBuilder.getOctaveShift` takes a line with no
  chord at an end to its own end.
- `MetronomeInter.isParsed`: a line that only looks like a tempo mark (OCR's "J: 88") is exported
  as words, not as a tempo with no value.

**Rhythm and export**
- `StackRhythm.doProcess`, `MeasureRhythm(measure, implicitTuplets)`: a measure whose voices
  don't fit is read again with unmarked tuplets allowed. Engravers mark the first triplets and
  then leave the 3 out. Only failing measures are read again: Audiveris's own switch
  (`ProcessingSwitches.implicitTuplets`) applies to every measure and upsets ones that fit. A
  measure too long for another reason (a false note) can come out with its eighths as triplets.
- `PartwiseBuilder.WedgeIterators`: a hairpin on a chord the rhythm step couldn't time no longer
  makes the export drop that measure from the part.

**Text**
- `BrowserOCR`: words, titles and part names are read by tesseract.js on the page (`app/ocr.js`),
  through the browser build's `OcrUtil` (`teavm/patched/make_patches.py`). It hands over each
  image Audiveris would give Tesseract, as grey bytes; tesseract.js runs the same legacy engine
  (`TesseractOrder`) with the language picked on the page. Lines, words and characters come back
  with their boxes and baselines but no font attributes, so a word's size comes from its line's
  height. `BrowserOCR.LANGUAGES` lists the page's six languages.

**Speed** (same output as the original code)
- `FlatMorphology`: the closing filter that finds beam spots, without a helper call per pixel.
- `Template.evaluate`: for a `Table.Short` it reads the array directly (`Table.Short.rawData`),
  with each template's key points in arrays and each anchor's offset worked out once.

## Settings (app/settings.js)

The page and the corpus test both read with these.
- `LinesRetriever.maxSlopeDiff=0.1` (Audiveris: 0.025) and `maxFilamentRotation=0.2` (0.1): a
  staff line may tilt more against the page and bend more along its length. Scanned books and
  photos warp: with Audiveris's values whole staves are dropped, or start late near the binding.
- `LinesRetriever.minStaffLength=15` (30 staff spaces): a song's last system can be one short bar.
- `ProcessingSwitches.indentations=false`: an indented system doesn't start a new movement.
  Hymnals indent many.

## What the page does around Audiveris

**Drawing pages (app/pdf.js).** The page draws a PDF's pages with PDF.js at 300 dpi and photos
with the browser, and makes them grey. Audiveris draws PDFs without antialiasing, and reads
antialiased grey edges as ink (letters thicken and Tesseract reads "e" as "c"), so a page of drawn
shapes is made black and white at half coverage. A page with images, such as a scan, keeps its
greys.

**A look before reading (app/preflight.js).** Each photo and scanned page gets a check of about
0.3 s while it is prepared. If Audiveris would give up on it, because it finds no staves or the
staff lines are under 11 pixels apart (`ScaleBuilder.minInterline`), the page says why and asks
before the read starts, since a read can't be stopped. Ink is a pixel clearly darker than its
neighbourhood, so shadows don't count; staves are five evenly spaced rows of ink in at least 3 of
12 vertical strips, each strip at its own tilt. `test/e2e-check.mjs` checks the warning in Chrome
(`photo.jpg` reads, `photo-small.jpg` is warned about).

**Language of the words (app/language.js, app/ocr.js).** The pick panel offers English (the
default), German, French, Italian, Spanish and Latin. The page downloads that language's data
while it prepares the pages (`startOcr`) and uses it for every image Audiveris hands over
(`resolveOcrLanguage`; Audiveris itself always asks for English). `build.sh` serves the standard
data for all six (`@tesseract.js-data/<code>/4.0.0`, 6 to 14 MB each, which the legacy engine
needs); a browser downloads only the one picked. If it fails to load, words are read in English.
What a language buys is accented letters (`test/language.test.mjs`).

**A beamed chord's beams on its first note only (app/beams.js).** Audiveris writes a chord's
beams on every note of the chord. Verovio, which draws the score after a read and in Sectional,
then drops the notes of the beamed group ("Adding 'beam' to a 'chord'"): on the test pages with
beamed chords it kept 14,063 of 24,218 notes, losing most of a piano bar at a time. After the
read, the chord's other notes lose their `<beam>` elements and follow its first note, as most
programs write a chord; Verovio then keeps 24,214.

**Notes in one column start together (app/columns.js).** Audiveris times each part's bar on its
own, so a beam, flag or dot it misses, or a triplet the engraving left unmarked, puts the rest of
that part's bar at the wrong times, though the other parts show where its notes belong. After
the read, a part's bar longer than its time signature (or shorter, inside the piece) is re-timed
by the other parts' bars in the same system that add up: a note takes the time of the chords in
its column (default-x within 2 tenths; a chord's column is where its heads on the stem's usual
side stand), and the notes between two such notes follow the one before, stay, or follow the one
after, whichever can be written; failing that, a run of equal notes is spread evenly, as a
triplet, with the triplet marks Verovio needs to time it. Lengths are written again to match; a
voice that plain, dotted or triplet values can't write stays as read. A page with no time
signature (one from the middle of a piece) takes the bar length most of its bars have, if a
common time signature has it. Measured 2026-11-24 with `test/prove.mjs` from the corpus's reads:
75 sung and 33 accompaniment bars more right, 1,414 more notes at the right time, none worse;
held-out pages 65 more notes, none worse.

A voice the columns can't place (in a part alone, or with no part that adds up) and that runs
past its bar is tried as unmarked triplets: every three eighths (or shorter) of one length that
are beamed as a group of their own (one beam over the three, or a rest or flagged note and a beam
over the other two) and start on a beat of the triplet become a triplet, and this is kept only if
the voice then ends on the bar's end. A beam running on past the three (four eighths, the last
misread as a quarter) is not a triplet. Measured 2026-11-25: 295 more notes at the right time
(Erlkönig, Lindenbaum, Widmung and the canticle most), 3 accompaniment bars more right, 74 fewer
bars that don't add up, none worse; held-out pages 6 more notes, none worse.

**Reading in a worker (teavm/).** The worker reads each page in two calls into Audiveris, up to
the TEXTS step and the rest, and the page reads the words with tesseract.js in between.
