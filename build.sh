#!/bin/sh
# Build the site into dist/: the page, the licences, and Audiveris's jars (patched and rewritten).
#   ./build.sh   (needs .work/: see spike/README.md; and npm install, for PDF.js)
#   ./build.sh page   rebuilds only the page, keeping the jars in dist/
set -e
cd "$(dirname "$0")"
if [ "$1" = page ]; then
  find dist -maxdepth 1 -type f -delete
  rm -rf dist/pdfjs
else
  spike/build.sh
  rm -rf dist
fi
mkdir -p dist/jars dist/pdfjs
cp app/index.html app/reader.js app/pdf.js app/style.css dist/
cp LICENSE dist/LICENSE.txt
cp NOTICE.txt dist/NOTICE.txt
# PDF.js draws PDFs' pages: its library, its decoders for scanned images, its fonts and colour profiles
pdfjs=node_modules/pdfjs-dist
cp $pdfjs/build/pdf.min.mjs $pdfjs/build/pdf.worker.min.mjs $pdfjs/LICENSE dist/pdfjs/
cp -R $pdfjs/cmaps $pdfjs/iccs $pdfjs/standard_fonts dist/pdfjs/
mkdir dist/pdfjs/wasm
cp $pdfjs/wasm/*.wasm $pdfjs/wasm/*_nowasm_fallback.js $pdfjs/wasm/LICENSE_* dist/pdfjs/wasm/
rm -f dist/pdfjs/wasm/quickjs* dist/pdfjs/wasm/LICENSE_*QUICKJS # that one runs a PDF's scripts, which aren't wanted
# the jars in classpath order, patched classes first; the page adds where they are served from
[ "$1" = page ] || sed 's|/app/.work/fast/||g' .work/classpath-fast.txt | tr ':' '\n' > dist/jars/classpath.txt
[ "$1" = page ] || for j in $(cat dist/jars/classpath.txt); do cp ".work/fast/$j" dist/jars/; done
echo "dist: $(du -sh dist | cut -f1)"
