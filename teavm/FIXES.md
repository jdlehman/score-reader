# What the TeaVM build changes

Audiveris runs here under TeaVM 0.16 (WebAssembly GC). TeaVM's class library lacks much of the
JDK and has a few bugs Audiveris runs into, and Audiveris expects files, fonts, threads and
reflection that a browser doesn't give it. This is what the build changes for that. Code comments
cite these entries by § number; the numbers have gaps.

## TeaVM's own bugs (fork/, compiled over its release jars by build.sh)

- **§9** `teavm-core-21244.patch`, `teavm-core-21244b.patch`: WebAssembly type inference marked a
  block's result non-nullable where one path yields null (a `Map.Entry` loop variable in a method
  that can suspend), so the module failed to load. Block results are nullable when any path into
  them is, in the coroutine transformation too.
- `teavm-classlib-fix.patch`: `TPoint` extends `Point2D` and `TDimension` extends `Dimension2D`,
  as in the JDK.
- **§19** `teavm-classlib-color.patch`: the JDK's standard colour constants and
  `Color(int, boolean)`.
- **§27** `teavm-classlib-hypot.patch`: `Math.hypot` is +∞ when either argument is infinite, even
  if the other is NaN, as in the JDK. TeaVM's gave NaN, which let a NaN-radius circle through the
  slur fit for three points in a line and crashed the CURVES step.
- **§33** `teavm-classlib-retainall.patch`: `ArrayList.retainAll` and `removeAll` scan the array
  by index, as the JDK's do. TeaVM's used an iterator, so `list.retainAll(list.subList(0, i))`,
  which Audiveris uses in nine places, threw `ConcurrentModificationException`.
- **§35** `teavm-classlib-formatter.patch`: `String.format` writes "null" for a null argument to a
  numeric conversion, as the JDK does, instead of throwing.
- **§40** `teavm-classlib-rint.patch`: `Math.rint` rounds halves to even and keeps NaN and
  infinities, and `Math.round(float)` is `(int) floor(a + 0.5f)`, as in the JDK. TeaVM rounded
  halves away from zero, which put some staff-line positions a pixel off.

## JDK classes TeaVM lacks (shims/)

AWT geometry and images, fonts, Swing and XML, as stubs or as copies of OpenJDK's code where
Audiveris depends on the behaviour.
- **§12** `QuadCurve2D` and `CubicCurve2D` return real path iterators (slurs are splines).
- **§13** `BufferedImage.getRGB`/`setRGB` go by the raster's actual data buffer, not the declared
  image type; `Raster` puts a null location at (0, 0), as the JDK does.
- **§14** `Color` has the constants the symbol painters use; `CubicCurve2D.setCurve(Point2D[], int)`.
- **§19** There are no fonts, so `BravuraMetrics` holds each Bravura symbol's bounds, advance and
  centroid, dumped by desktop Java (`generate/phase-font/`), and `TextLayout` and
  `SimpleGlyphVector` take their sizes from it. **§45**: the table includes U+E010, the staff line
  that pitch positions are measured from; without it no flat key was ever found.
- **§23** `Font.createGlyphVector` returns a `SimpleGlyphVector` (text sizes need it).
- **§24** `Rectangle.contains` and `Rectangle2D.contains` treat edges as the JDK does.
- **§26** `Area`'s add, subtract, intersect and exclusive-or clip real polygons, and `Path2D`'s
  contains and intersects test the real shape (both went by bounding boxes, which lost beams).
  `BufferedImageGraphics` fills shapes by scanline.
- **§31** `Ellipse2D` geometry and `RectangularShape.getBounds` are copied from OpenJDK 25.

## Changes to Audiveris's source (patched/make_patches.py, each marked TEAVM in the code)

- **No files or user folders** (§11, §13): `WellKnowns`, `ConstantManager`, `BookManager`,
  `AliasPatterns` and `OmrFont` work without a resources folder, user properties or a home.
- **No command line** (§12): `SheetStub` and `Book.getStubsToUpgrade` don't ask for one.
- **Reflection** (§10, §11, §12, §42): `ConstantSet` names its constants from its own class, and
  `policy/` keeps the constructors Audiveris calls by reflection (filaments, support relations).
- **One thread** (§10): `OmrExecutors` runs tasks in the calling thread.
- `LogUtil` and `StepMonitoring` do nothing; `LoadStep` takes the page the worker was given
  (`TeavmImageHolder`).
- **§16** `FloodFiller.fill` uses its own stack: the recursive one overflowed WebAssembly's stack
  while building note-head templates. Same pixels.
- **§17** Note-head templates are read from files that desktop Audiveris drew
  (`PreRenderedTemplates`; `teavm/README.md`), since drawing them needs the fonts.
- **§18** The glyph classifier's network is saved as data (`entry/PreRenderedClassifier.java`, the
  same results as the desktop's), and `ClefBuilder` takes a clef's bounds from its glyph, not from
  the font.
- **§30–§32** `PageCleaner` erases a note head from its glyph's runs plus an ellipse 1.32 times
  the glyph's bounds, where the desktop paints the glyph white, which needs the font.
- **§23** Text goes to the page's tesseract.js through `BrowserOCR`: each page is read in two
  calls, up to the TEXTS step and the rest, and the words are read in between (`node/ocr-run.mjs`
  for Node).

## The MusicXML writer (entry/MxlWriter.java)

- **§22** JAXB can't run here, so `MxlWriter` writes MusicXML 4.0 itself, walking the score as
  Audiveris's `PartwiseBuilder` does.
- **§34** A chord the rhythm step couldn't time is skipped where the writer sorts by time, so its
  measure is still written.
- **§44** A key cancellation with no fifths writes no `<key>`.

## Tools that made the data (generate/)

- `TemplateDump.java`: the note-head templates (§17), run by `build.sh`.
- `phase-font/gen_symbol_metrics.py` with `SymbolMetricsDump.java`: the Bravura metrics table
  (§19); `phase55/LineCodeDump.java` its U+E010 entry (§45). The other programs in `phase-font/`
  check the shims' text measurements against the real font on the desktop.
- `phasec/gen_classifier.py`: the classifier's network as Java data (§18).
