// §37: save one MusicXML file per score, mirroring desktop Audiveris
// Book.export: a single-score book exports as BOOK.ext; a multi-score
// book exports as several BOOK.mvt#.ext files (one per movement).
// `b64List` is the parsed __mxlB64List JSON array (base64 strings, one
// per score, in score order). Returns the list of files written, each
// { path, bytes, lyrics }.
// Usage: import { saveMxl } from "./save-mxl.mjs";
import { writeFile } from "node:fs/promises";

export async function saveMxl(out, b64List) {
    const files = [];
    if (!b64List || b64List.length === 0) {
        return files;
    }
    for (let i = 0; i < b64List.length; i++) {
        const xml = Buffer.from(b64List[i], "base64").toString("utf8");
        let path = out;
        if (b64List.length > 1) {
            const dot = out.lastIndexOf(".");
            path = (dot === -1 ? out : out.slice(0, dot))
                + `.mvt${i + 1}` + (dot === -1 ? "" : out.slice(dot));
        }
        await writeFile(path, xml, "utf8");
        files.push({
            path,
            bytes: xml.length,
            lyrics: (xml.match(/<lyric[ >]/g) || []).length,
        });
    }
    return files;
}

// Read the list TeavmMain set, with the legacy single __mxlB64 as fallback
// (builds before full-out84 set only __mxlB64, to the LAST score).
export function readMxlList() {
    let list = null;
    try {
        list = JSON.parse(globalThis.__mxlB64List ?? "null");
    } catch {
        list = null;
    }
    if (!list && globalThis.__mxlB64 != null) {
        list = [globalThis.__mxlB64];
    }
    return list;
}
