// §23: two-phase OCR run of a compiled TeavmMain wasm dir.
//   Phase 1: main() with no __ocrText — runs LOAD..TEXTS; TextsStep's
//     BrowserOCR exports the clean OCR image (grey bytes + w/h/lang/psm)
//     to JS globals and returns no lines. main() returns after TEXTS.
//   OCR: tesseract.js (phase23/ocr-run.mjs) on the exported image.
//   Phase 2: fresh module load with __ocrText set — full run LOAD..PAGE
//     + export; BrowserOCR parses the prefed L/W/C text, TextBuilder
//     attaches lyrics, MxlWriter emits them.
// Usage: node run-fullout-ocr.mjs <wasm-dir> <grey> <meta.json> <out.musicxml> [lang] [tag]
//   e.g. node run-fullout-ocr.mjs full-out49 ../teavm/hymn-satb.gray ../teavm/hymn-satb.json wasm-hymn-ocr.musicxml eng hymn
// Intermediate files (clean image + OCR text) land in phase23/<tag>-*.
import { readFile, writeFile } from "node:fs/promises";
import { readText, stopOcr } from "./phase23/ocr-run.mjs";
import { saveMxl, readMxlList } from "./save-mxl.mjs"; // §37: one file per score

const dir = process.argv[2] ?? "full-out49";
const greyPath = process.argv[3] ?? "../teavm/hymn-satb.gray";
const metaPath = process.argv[4] ?? "../teavm/hymn-satb.json";
const out = process.argv[5] ?? "wasm-ocr.musicxml";
const lang = process.argv[6]; // e.g. "deu"; undefined = stub default (eng)
const tag = process.argv[7] ?? "page";

const grey = await readFile(new URL(greyPath, import.meta.url));
const meta = JSON.parse(await readFile(new URL(metaPath, import.meta.url), "utf8"));
const { load } = await import("../teavm/out-teavm/runtime.mjs");

async function runMain() {
    globalThis.__greyB64 = grey.toString("base64");
    globalThis.__greyW = meta.width;
    globalThis.__greyH = meta.height;
    const t0 = Date.now();
    const teavm = await load(new URL(`./${dir}/classes.wasm`, import.meta.url).pathname);
    console.log(`wasm loaded in ${Date.now() - t0} ms`);
    const t1 = Date.now();
    teavm.exports.main([]);
    console.log(`main() returned in ${Date.now() - t1} ms`);
}

// --- Phase 1 ---
console.log(`== PHASE 1 ${tag} ==`);
delete globalThis.__ocrText;
if (lang) globalThis.__ocrLang = lang;
await runMain();
const imgB64 = globalThis.__ocrImageB64;
if (imgB64 == null) {
    console.log("NO OCR IMAGE: globalThis.__ocrImageB64 was never set — TextsStep did not reach OCR");
    process.exit(2);
}
const iw = globalThis.__ocrImageW, ih = globalThis.__ocrImageH;
const ilang = globalThis.__ocrLang, ipsm = globalThis.__ocrPsm;
console.log(`clean image w=${iw} h=${ih} lang=${ilang} psm=${ipsm} bytes=${Buffer.from(imgB64, "base64").length}`);
const cleanGrey = Buffer.from(imgB64, "base64");
await writeFile(`./phase23/${tag}-clean.gray`, cleanGrey);
await writeFile(`./phase23/${tag}-clean.json`, JSON.stringify({ width: iw, height: ih, bytes: cleanGrey.length, lang: ilang, psm: ipsm }));

// --- OCR (Node-side tesseract.js) ---
console.log(`== OCR ${tag} lang=${ilang ?? lang ?? "eng"} psm=${ipsm ?? 3} ==`);
const t0 = Date.now();
const ocrText = await readText(cleanGrey, iw, ih, ipsm ?? 3, ilang ?? lang ?? "eng");
console.log(`ocr ms=${Date.now() - t0} rows=${ocrText.split("\n").length} L=${ocrText.split("\n").filter((r) => r.startsWith("L ")).length} W=${ocrText.split("\n").filter((r) => r.startsWith("W ")).length} C=${ocrText.split("\n").filter((r) => r.startsWith("C ")).length}`);
await writeFile(`./phase23/${tag}-ocr.txt`, ocrText);
await stopOcr();

// --- Phase 2 ---
console.log(`== PHASE 2 ${tag} ==`);
globalThis.__ocrText = ocrText;
if (lang) globalThis.__ocrLang = lang;
await runMain();
const list = readMxlList();
if (!list) {
    console.log("NO MXL: globalThis.__mxlB64 was never set");
    process.exit(2);
}
const files = await saveMxl(out, list);
for (const f of files) {
    console.log(`MXL saved ${f.path} bytes=${f.bytes} lyricElements=${f.lyrics}`);
}
