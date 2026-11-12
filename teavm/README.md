# Audiveris in WebAssembly (TeaVM)

The page reads music with Audiveris, a Java program, built into WebAssembly with
[TeaVM](https://teavm.org) 0.16 (WebAssembly GC, Apache-2.0), so the site serves everything itself.
(Until November 2026 it ran the Java with CheerpJ, whose runtime loads from its maker's servers
under a licence they can change.)

The port is robbie-muse's [score-reader-teavm](https://github.com/robbie-muse/score-reader-teavm)
(imported at 9b7e935); `FORK_FIX.md` is its log of every defect found and fixed, which the code's
§ numbers refer to.

## Build

```sh
./setup.sh && ./build.sh   # .work/: Audiveris, our patch, the JDK, TeaVM's jars; .work/patched.jar
teavm/build.sh             # .work/teavm/out/: classes.wasm (~15 MB) and runtime.mjs, in about a minute
```

What it builds from:

- **Audiveris's source with our patch** (`.work/audiveris`), changed further for TeaVM by
  `patched/make_patches.py` (each change marked TEAVM). Our own patched classes
  (`.work/patched.jar`) come next on the class path, so a change in `patches/` reaches this build
  without being copied here. `make_patches.py` fails loudly when a change of ours moves code it
  edits.
- **TeaVM's release jars** from Maven Central (`setup.sh`, checked by SHA-256), and its bugs that
  Audiveris hits, fixed in `fork/*.patch` and compiled over them.
- **`shims/`**: the JDK classes TeaVM's class library lacks (AWT, Swing, XML), as stubs.
- **`entry/`**: what the page calls (`TeavmMain`), a MusicXML writer (`MxlWriter`: JAXB can't run
  here), and Audiveris's classifier and font metrics, saved as data (there are no fonts here).
- **Note-head templates**: desktop Audiveris draws them from its fonts at every point size from 32
  to 200 (`generate/TemplateDump.java`, run by `build.sh`), a file a font and size; the page
  fetches the one a page needs (`PreRenderedTemplates`). The port's five sizes made most pages use
  a neighbouring size, up to 12% off, and lose heads (Hallelujah p05 88% of notes, now 100%).
- **`policy/`**: the reflection TeaVM must keep. **`tools/RewriteJars.java`**: bytecode fixes to
  five of the release's jars.

## Run

`app/teavm.js` reads a score: grey pages in, MusicXML out. The page runs it in a worker
(`app/teavm-worker.js`); `node/read.mjs` runs it in Node:

```sh
node --experimental-wasm-exnref teavm/node/read.mjs out.musicxml page1.grey page1.json [page2.grey page2.json ...]
OCR=deu node --experimental-wasm-exnref teavm/node/read.mjs ...   # with the words, by tesseract.js
```

Each page is read in two calls, up to its words and the rest, so the words can be read in between
(Tesseract is asynchronous JavaScript; WebAssembly can't wait for it). Node 24.7 needs
`--experimental-wasm-exnref`; Chrome doesn't.

## Known gaps

- A boxed rehearsal letter's own OCR gets no text (the page's words are read once, before the
  TEXTS step).
- `MxlWriter` hasn't met pedal marks, chord names, measure repeats or drum parts on a test page.
