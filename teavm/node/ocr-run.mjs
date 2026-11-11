// §23: Node-side tesseract.js OCR for the TeaVM TextsStep bridge.
// Mirrors score-reader's app/ocr.js readText() exactly (legacy engine,
// 70 dpi, PSM from Audiveris, L/W/C rows BrowserOCR.parse consumes),
// adapted to Node: the grey image is PNG-encoded here (tesseract.js in
// Node takes a PNG/JPEG buffer; there is no OffscreenCanvas).
// Language data is downloaded by tesseract.js on first use (~6-15 MB
// per language, cached afterwards); a failed pack falls back to English
// and warns, never stopping the read.
import { deflateSync } from 'node:zlib';
import Tesseract from 'tesseract.js';

const DPI = 70;
const LEGACY = 0;

let worker = null;
let workerSpec = null;

function crc32(buf) {
    let table = crc32.table;
    if (!table) {
        table = crc32.table = new Int32Array(256);
        for (let n = 0; n < 256; n++) {
            let c = n;
            for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
            table[n] = c;
        }
    }
    let c = 0xffffffff;
    for (let i = 0; i < buf.length; i++) c = table[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
    const out = Buffer.alloc(8 + data.length + 4);
    out.writeUInt32BE(data.length, 0);
    out.write(type, 4, 'ascii');
    data.copy(out, 8);
    out.writeUInt32BE(crc32(Buffer.concat([Buffer.from(type, 'ascii'), data])), 8 + data.length);
    return out;
}

/** Encode grey bytes (w*h, one byte a pixel) as a PNG Buffer. */
export function greyToPng(grey, w, h) {
    const raw = Buffer.alloc(h * (1 + w));
    for (let y = 0; y < h; y++) {
        raw[y * (1 + w)] = 0; // filter: none
        grey.copy(raw, y * (1 + w) + 1, y * w, (y + 1) * w);
    }
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(w, 0);
    ihdr.writeUInt32BE(h, 4);
    ihdr[8] = 8; // bit depth
    ihdr[9] = 0; // colour type: greyscale
    const png = Buffer.concat([
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
        chunk('IHDR', ihdr),
        chunk('IDAT', deflateSync(raw, { level: 6 })),
        chunk('IEND', Buffer.alloc(0)),
    ]);
    return png;
}

async function startOcr(spec) {
    const want = spec || 'eng';
    if (worker && workerSpec === want) return worker;
    if (worker) { await worker.terminate().catch(() => {}); worker = null; }
    const langs = want.split('+').filter(Boolean);
    try {
        worker = await Tesseract.createWorker(langs.length === 1 ? langs[0] : langs, LEGACY, {
            legacyCore: true,
            legacyLang: true,
        });
    } catch (e) {
        if (want !== 'eng') {
            console.warn(`Tesseract data for '${want}' could not load, falling back to English:`, e.message);
            worker = await Tesseract.createWorker('eng', LEGACY, { legacyCore: true, legacyLang: true });
            workerSpec = 'eng';
            return worker;
        }
        throw e;
    }
    workerSpec = want;
    return worker;
}

export async function stopOcr() {
    if (worker) { await worker.terminate().catch(() => {}); worker = null; workerSpec = null; }
}

/**
 * Run OCR on grey bytes and return the BrowserOCR L/W/C text.
 * pageSegMode: 3 = AUTO (MULTI_BLOCK, as SheetScanner uses), 6 = SINGLE_BLOCK.
 */
export async function readText(grey, width, height, pageSegMode, languages) {
    const w = await startOcr(languages);
    await w.setParameters({ tessedit_pageseg_mode: String(pageSegMode), user_defined_dpi: String(DPI) });
    const png = greyToPng(grey, width, height);
    const { data } = await w.recognize(png, {}, { blocks: true, text: false });
    const out = [];
    const box = (b) => `${b.x0} ${b.y0} ${b.x1} ${b.y1}`;
    for (const block of data.blocks ?? []) {
        for (const paragraph of block.paragraphs ?? []) {
            for (const line of paragraph.lines ?? []) {
                const base = line.baseline ?? { x0: line.bbox.x0, y0: line.bbox.y1, x1: line.bbox.x1, y1: line.bbox.y1 };
                const rowHeight = Math.round(line.rowAttributes?.row_height ?? line.bbox.y1 - line.bbox.y0);
                out.push(`L ${box(line.bbox)} ${Math.round(base.x0)} ${Math.round(base.y0)} ${Math.round(base.x1)} ${Math.round(base.y1)} ${Math.round(rowHeight * 72 / DPI)}`);
                for (const word of line.words ?? []) {
                    const text = (word.text ?? '').replace(/\s+/g, '');
                    if (!text) continue;
                    out.push(`W ${box(word.bbox)} ${Math.round(word.confidence)} ${text}`);
                    for (const symbol of word.symbols ?? []) {
                        const s = (symbol.text ?? '').replace(/\s+/g, '');
                        if (s) out.push(`C ${box(symbol.bbox)} ${s}`);
                    }
                }
            }
        }
    }
    return out.join('\n');
}
