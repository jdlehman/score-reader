// A stand-in for CrispEmbed's UMD build (crispembed_ocr.js), for the runner tests only.
// It has the same shape the worker calls — a factory returning a module with FS.writeFile,
// ccall, _malloc/_free, HEAPU8 and UTF8ToString — but it answers with the WASM runner's
// own outputs for the synthetic divisi page (test/fixtures/divisi-merge/), in call order,
// so the driver's end-to-end behaviour can be tested without the 32 MB model.
// Set globalThis.__tromrStub.failOn to a 1-based call number to make that call throw.
const TOKENS = [
  'clef-G2+keySignature-CM+timeSignature-4/4+note-G3_half|note-C4_quarter|note-E4_quarter+note-C4_quarter|note-E4_quarter+note-F3_half|note-A3_quarter|note-F4_quarter+note-D4_quarter|note-G4_quarter+barline+note-G3_half|note-D4_quarter|note-G4_quarter+note-A3_quarter|note-F4_quarter+note-G3_half|note-C4_quarter|note-E4_quarter+note-B3_quarter|note-D4_quarter+barline+note-C4_eighth|note-C4_quarter+note-D4_eighth+note-E4_eighth+note-C4_quarter+note-F4_eighth+note-G4_eighth+note-A4_eighth+note-D4_quarter+note-E4_quarter+barline+note-C4_eighth|note-E4_quarter+note-D4_eighth+note-E4_eighth+note-D4_quarter+note-F4_eighth+note-G4_eighth+note-A4_eighth+note-D4_quarter+note-C4_quarter+barline',
  'clef-F4+keySignature-CM+timeSignature-4/4+note-C3_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+note-F2_quarter|note-F3_quarter+note-G2_quarter|note-B3_quarter+barline+note-G2_quarter|note-B3_quarter+note-F2_quarter|note-F3_quarter+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+barline+note-C3_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+barline+note-C3_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-G2_quarter|note-G3_quarter+note-C3_quarter|note-G3_quarter+barline',
]
let call = 0

globalThis.CrispEmbedOCR = async function (opts) {
  return {
    FS: { writeFile: (path, bytes) => {} },
    HEAPU8: new Uint8Array(16 * 1024 * 1024),
    _malloc: (n) => 0,
    _free: (ptr) => {},
    UTF8ToString: (ptr) => TOKENS[call - 1] ?? '',
    ccall: (name, ret, argTypes, args) => {
      if (name === 'wasm_ocr_init') return 1 // a non-zero context: the model loaded
      if (name === 'wasm_ocr_recognize_copy') {
        call++
        if (globalThis.__tromrStub?.failOn === call) throw new Error('stub: recognition failed')
        return 1 // a non-zero string pointer; UTF8ToString turns it into the tokens
      }
      return 0
    },
  }
}
