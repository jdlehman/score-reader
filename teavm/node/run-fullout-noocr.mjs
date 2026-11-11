// No-OCR control run of a compiled TeavmMain wasm dir (§23).
// Same build as the OCR runs, TextsStep restored, but zero OCR lines:
// __ocrText is a single blank space, so TeavmMain takes the full-pipeline
// path (hasOcr = non-empty) while BrowserOCR.parse returns 0 lines.
// Use: node run-fullout-noocr.mjs <wasm-dir> <grey> <meta.json> <out.musicxml>
//   e.g. node run-fullout-noocr.mjs full-out49 ../teavm/hymn-satb.gray ../teavm/hymn-satb.json wasm-hymn-noocr49.musicxml
import { readFile } from "node:fs/promises";
import { saveMxl, readMxlList } from "./save-mxl.mjs"; // §37: one file per score

const dir = process.argv[2];
const greyPath = process.argv[3];
const metaPath = process.argv[4];
const out = process.argv[5];
const grey = await readFile(greyPath);
const meta = JSON.parse(await readFile(metaPath, "utf8"));
globalThis.__greyB64 = grey.toString("base64");
globalThis.__greyW = meta.width;
globalThis.__greyH = meta.height;
globalThis.__ocrText = " "; // non-empty => full pipeline; parses to 0 lines
console.log(`grey bytes=${grey.length} w=${meta.width} h=${meta.height} (no-OCR control)`);

const t0 = Date.now();
const { load } = await import("../teavm/out-teavm/runtime.mjs");
const teavm = await load(new URL(`./${dir}/classes.wasm`, import.meta.url).pathname);
console.log(`wasm loaded in ${Date.now() - t0} ms`);
const t1 = Date.now();
teavm.exports.main([]);
console.log(`main() returned in ${Date.now() - t1} ms`);

const list = readMxlList();
if (!list) {
    console.log("NO MXL: globalThis.__mxlB64 was never set");
    process.exit(2);
}
const files = await saveMxl(out, list);
for (const f of files) {
    console.log(`MXL saved ${f.path} bytes=${f.bytes} lyricElements=${f.lyrics}`);
}
