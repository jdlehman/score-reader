#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build the site into dist/: the page, the licences, Audiveris in WebAssembly (teavm/), and the
# source of the copyleft libraries compiled into it.
#   ./build.sh        (needs .work/ from ./setup.sh, and npm install for PDF.js and tesseract.js)
#   ./build.sh page   rebuilds only the page, keeping Audiveris in dist/
set -e
cd "$(dirname "$0")"

if [ "$1" = page ]; then
  find dist -maxdepth 1 -type f -delete
  rm -rf dist/pdfjs
else
  J=$(ls -d .work/jdk/*/Contents/Home/bin .work/jdk/*/bin 2>/dev/null | head -1) # macOS or Linux
  SRC=.work/audiveris/app/src/main/java/org/audiveris/omr

  # our changed Audiveris classes (patches/), compiled against the Audiveris jars: the browser build
  # starts from them (teavm/build.sh), and the corpus test reads with them (test/corpus.mjs)
  rm -rf .work/classes && mkdir -p .work/classes
  "$J/javac" -nowarn -proc:none -cp ".work/lib/*" -d .work/classes \
    $SRC/sheet/Book.java $SRC/sheet/Sheet.java $SRC/sheet/Picture.java $SRC/CLI.java $SRC/Main.java $SRC/ScoreReaderHook.java \
    $SRC/image/MorphoProcessor.java $SRC/image/FlatMorphology.java $SRC/text/OcrUtil.java $SRC/text/BrowserOCR.java \
    $SRC/sig/inter/MetronomeInter.java $SRC/score/PartwiseBuilder.java $SRC/image/Template.java $SRC/util/Table.java \
    $SRC/sheet/rhythm/MeasureStack.java $SRC/sheet/grid/PeakGraph.java $SRC/score/PartCollation.java $SRC/sheet/rhythm/Voices.java $SRC/sig/inter/KeyInter.java $SRC/sheet/clef/ClefBuilder.java $SRC/sig/inter/OctaveShiftInter.java \
    $SRC/sheet/rhythm/MeasureRhythm.java $SRC/sheet/rhythm/StackRhythm.java $SRC/sheet/note/NoteHeadsBuilder.java 2>&1 | grep -v '^Note:' || true
  "$J/jar" cf .work/patched.jar -C .work/classes .

  # Audiveris in WebAssembly (teavm/README.md), copied into dist/ below
  teavm/build.sh

  rm -rf dist
  mkdir -p dist/source dist/licenses
  # the source of the copyleft libraries (see NOTICE.txt)
  cp .work/sources/*.jar dist/source/
  # the libraries' own licence and notice files, from their jars (their code is compiled into teavm/)
  for j in .work/lib/*.jar; do
    files=$(unzip -Z1 "$j" | grep -iE '^(META-INF/)?(LICEN[CS]E|NOTICE|COPYING)[^/]*$' || true)
    [ -n "$files" ] && unzip -q -o "$j" $files -d "dist/licenses/$(basename "$j" .jar)"
  done
  # TeaVM's (Apache License 2.0, whose text PDF.js's LICENSE is): its jars carry none
  mkdir -p dist/licenses/teavm-0.16.0 && cp node_modules/pdfjs-dist/LICENSE dist/licenses/teavm-0.16.0/LICENSE
fi

cp app/index.html app/reader.js app/pdf.js app/ocr.js app/language.js app/preflight.js app/settings.js app/teavm.js app/teavm-worker.js app/style.css app/*.svg app/*.png dist/
if [ -f .work/teavm/out/classes.wasm ]; then
  rm -rf dist/teavm && mkdir -p dist/teavm
  cp .work/teavm/out/classes.wasm .work/teavm/out/runtime.mjs dist/teavm/
  cp -R .work/teavm/out/templates dist/teavm/
fi
# the score drawn after a read, to correct: @jdlehman/score-view (MIT, built by update-score-view.sh),
# and Verovio (LGPL 3.0), unchanged, as files of its own
cp app/check.js app/engrave-worker.js app/score-view.js dist/
rm -rf dist/verovio && mkdir -p dist/verovio
cp node_modules/verovio/dist/verovio-module.mjs node_modules/verovio/dist/verovio.mjs dist/verovio/
cp licenses/verovio.txt dist/verovio/LICENSE.txt
cp LICENSE dist/LICENSE.txt
cp NOTICE.txt dist/NOTICE.txt
printf '\nThis copy was built from commit %s of the source.\n' "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)" >> dist/NOTICE.txt

# PDF.js draws PDFs' pages: its library, its decoders for scanned images, its fonts and colour profiles
pdfjs=node_modules/pdfjs-dist
mkdir -p dist/pdfjs/wasm
cp $pdfjs/build/pdf.min.mjs $pdfjs/build/pdf.worker.min.mjs $pdfjs/LICENSE dist/pdfjs/
cp -R $pdfjs/cmaps $pdfjs/iccs $pdfjs/standard_fonts dist/pdfjs/
cp $pdfjs/wasm/*.wasm $pdfjs/wasm/*_nowasm_fallback.js $pdfjs/wasm/LICENSE_* dist/pdfjs/wasm/
rm -f dist/pdfjs/wasm/quickjs* dist/pdfjs/wasm/LICENSE_*QUICKJS # that one runs a PDF's scripts, which aren't wanted

# Tesseract (tesseract.js) reads the words: its library and worker, the builds of its engine that
# include the legacy engine Audiveris uses (a browser loads one), and the language data.
# One pack a language (~6-14 MB each, MIT packages of the Apache-2.0 tessdata 4.0.0 data —
# the standard data, which the legacy engine needs; tessdata_fast is LSTM-only and would
# not work here). No traineddata is committed to the repo: build.sh copies it from npm.
rm -rf dist/tesseract dist/tessdata
mkdir -p dist/tesseract dist/tessdata
tjs=node_modules/tesseract.js
cp $tjs/dist/tesseract.esm.min.js $tjs/dist/worker.min.js $tjs/dist/*.LICENSE.txt dist/tesseract/
cp $tjs/LICENSE.md dist/tesseract/LICENSE.md
cp node_modules/tesseract.js-core/tesseract-core.wasm.js node_modules/tesseract.js-core/tesseract-core-simd.wasm.js \
  node_modules/tesseract.js-core/tesseract-core-relaxedsimd.wasm.js dist/tesseract/
cp node_modules/tesseract.js-core/LICENSE dist/tesseract/LICENSE-core
for lang in deu eng fra ita lat spa; do
  cp "node_modules/@tesseract.js-data/$lang/4.0.0/$lang.traineddata.gz" dist/tessdata/
done
echo "dist: $(du -sh dist | cut -f1)"
