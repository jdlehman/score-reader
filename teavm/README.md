# Spike: Audiveris with TeaVM instead of CheerpJ (2026-11-03)

CheerpJ runs Audiveris in the browser, but its free licence holds only while the page loads it from
Leaning Technologies' servers, and it is proprietary. [TeaVM](https://teavm.org) (Apache 2.0)
compiles Java ahead of time to WebAssembly (with the browser's garbage collector, WasmGC) or
JavaScript, which the site would host itself. This spike asks: how fast would it be, and what would
it take?

## Speed

`Bench.java` does what dominates Audiveris's slowest step, on plain arrays: a chamfer distance
transform of a page-sized image, then template matching along every staff line and space. Best of
five runs, same machine, same result (the check value):

| Runs on | Time | Against desktop Java |
|---|---|---|
| Desktop Java (Temurin 25) | 707 ms | 1× |
| TeaVM, WebAssembly (Node 24) | 1,072 ms | 1.5× |
| CheerpJ 5.0 (Chrome) | 1,913 ms | 2.7× |

On a whole page, CheerpJ runs Audiveris about 4× slower than desktop Java (75 s against 19 s): its
object-heavy code (interface calls, small allocations) suffers more than this loop, and that is
what ahead-of-time compilation does best with. So TeaVM could plausibly read a page 2–3× faster
than now. Not measured on Audiveris itself.

## What Audiveris needs that TeaVM lacks

`Spike.java` runs TeaVM 0.14.1 on Audiveris 5.11's `Main` (WasmGC). Its analysis reports 361
problems, then crashes before writing anything. The list undercounts: TeaVM stops following a
chain at its first missing class. Grouped by the code that needs them:

- **The reading path itself**, not just the desktop UI: `BufferedImage` and `DataBuffer`, Java2D
  geometry (`Point2D`, `Line2D`, `Rectangle2D`, `Path2D`), thread pools and locks
  (`ExecutorService`, `Future`, `ReentrantLock`, `ConcurrentSkipListMap`), JAXB, and Swing
  dialogs reached from step code.
- **Music and text fonts** (`ui.symbol`): `MusicFont` and `TextFont` extend `java.awt.Font`, and
  note-head templates are made by drawing the music font's glyphs with `Graphics2D` and
  `TextLayout`. TeaVM has no `java.awt` at all.
- **Libraries**: Logback, SLF4J and Commons Logging look themselves up through class loaders;
  JavaCPP loads native code (Tesseract, not needed: the page reads text); PDFBox needs AWT
  rasters and `java.util.zip.Inflater`; BSAF and JGoodies are desktop UI.
- **Files and environment**: `File.toPath`, file channels, `System.getenv`, resources.

## What a port would take

A fork of Audiveris's batch path for TeaVM, built from the same release plus patches, as now:

1. Its own entry point: the image comes from the page (already drawn by PDF.js or the browser, so
   no PDFBox or ImageIO), constants from their defaults, a console logger in place of Logback,
   the MusicXML handed back to the page; text through tesseract.js via TeaVM's JavaScript interop.
2. Cut the desktop UI out of the reading path (patches where step code reaches Swing or BSAF).
3. Supply what TeaVM lacks: geometry (OpenJDK's `java.awt.geom` is plain Java, GPL 2 with the
   classpath exception), a small `BufferedImage` for grey bytes, ImageJ's `ByteProcessor`
   without AWT, and single-threaded stand-ins for the executors and locks.
4. Fonts: draw the note-head templates ahead of time, for the sizes Audiveris uses, and ship them
   as data; text font metrics as a table.
5. A direct MusicXML writer in place of JAXB marshalling.
6. Check the output against desktop Audiveris on the recognition test, page for page.

Roughly two to three weeks of work to a first page read correctly, then upkeep with each Audiveris
release. Steps 3 and 4 are the uncertain ones.

## Running it

As it was run (in `.work/`, not committed):

1. TeaVM and its dependencies: a Gradle project with `tools.gradle` as its build file and the task
   `lib` (Gradle 8.9, which runs on Java 17, not 25).
2. TeaVM reads every class, its own Java library included, from the class path it is given. So
   the list passed to `Spike` has TeaVM's `teavm-classlib`, `-core`, `-interop`, `-jso`,
   `-jso-apis`, `-jso-impl`, `-platform` and `-metaprogramming-*` jars, then the program's;
   `@file` reads a list, one entry a line:

       java -cp "lib/*:." Spike wasm-gc <out dir> <main class> @teavm-jars.txt @program-jars.txt

3. Bench: compile `Bench.java` into `.work/teavm-bench/classes`, run `Spike` on it into
   `out-wasm-gc`, and put TeaVM's loader next to it (`org/teavm/backend/wasm/wasm-gc-module-runtime.js`
   from `teavm-core`, as `runtime.mjs`); then `node teavm/run-wasm.mjs`. For CheerpJ, make
   `.work/teavm-bench/bench.jar` from the classes, `npm run serve`, and `node teavm/run-cheerpj.mjs`.
