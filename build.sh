#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build the site into dist/: the page, the licences, Audiveris's jars (patched, and rewritten to
# call FastMath), and the source of the copyleft libraries.
#   ./build.sh        (needs .work/ from ./setup.sh, and npm install for PDF.js)
#   ./build.sh page   rebuilds only the page, keeping the jars in dist/
set -e
cd "$(dirname "$0")"

if [ "$1" = page ]; then
  find dist -maxdepth 1 -type f -delete
  rm -rf dist/pdfjs
else
  J=$(ls -d .work/jdk/*/Contents/Home/bin .work/jdk/*/bin 2>/dev/null | head -1) # macOS or Linux
  SRC=.work/audiveris/app/src/main/java/org/audiveris/omr

  # our changed Audiveris classes (patches/), compiled against the Audiveris jars
  rm -rf .work/classes && mkdir -p .work/classes
  "$J/javac" -nowarn -proc:none -cp ".work/lib/*" -d .work/classes \
    $SRC/sheet/Book.java $SRC/sheet/Sheet.java $SRC/sheet/Picture.java $SRC/CLI.java $SRC/Main.java $SRC/ScoreReaderHook.java \
    $SRC/image/MorphoProcessor.java $SRC/image/FlatMorphology.java $SRC/text/OcrUtil.java $SRC/text/BrowserOCR.java \
    $SRC/sig/inter/MetronomeInter.java $SRC/score/PartwiseBuilder.java $SRC/image/Template.java $SRC/util/Table.java \
    $SRC/sheet/rhythm/MeasureStack.java $SRC/sheet/grid/PeakGraph.java 2>&1 | grep -v '^Note:' || true
  "$J/jar" cf .work/patched.jar -C .work/classes .

  # FastMath, and every jar rewritten to call it (patched classes first, so they win)
  rm -rf .work/fastclasses .work/fast && mkdir -p .work/fastclasses
  "$J/javac" -d .work/fastclasses java/org/scorereader/FastMath.java java/org/scorereader/Rewrite.java
  (echo .work/patched.jar; tr ':' '\n' < .work/classpath.txt | sed 's|^/app/||') \
    | xargs "$J/java" -cp .work/fastclasses org.scorereader.Rewrite .work/fast
  "$J/jar" cf .work/fast/scorereader.jar -C .work/fastclasses org/scorereader/FastMath.class
  (printf '/app/.work/fast/patched.jar:/app/.work/fast/scorereader.jar:'; sed 's|/app/.work/lib/|/app/.work/fast/|g' .work/classpath.txt) > .work/classpath-fast.txt

  rm -rf dist
  mkdir -p dist/jars dist/source
  # the jars in class path order; the page adds where they are served from
  sed 's|/app/.work/fast/||g' .work/classpath-fast.txt | tr ':' '\n' > dist/jars/classpath.txt
  for j in $(cat dist/jars/classpath.txt); do cp ".work/fast/$j" dist/jars/; done
  # the source of the copyleft libraries (see NOTICE.txt)
  cp .work/sources/*.jar dist/source/
fi

cp app/index.html app/reader.js app/pdf.js app/ocr.js app/language.js app/style.css app/*.svg app/*.png dist/
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
