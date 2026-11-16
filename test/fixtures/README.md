# Test fixtures

Small files the tests open. All our own; checked against the rules in
`../corpus/README.md` ("What may be committed") on 2026-11-15.

| File | What | Licence |
|---|---|---|
| `photo.jpg`, `photo-small.jpg` | "Test piece 1005", a random SATB piece made by midi_studio's recognition test (`spike/omr/generate.ts`), drawn, then made to look like a phone photo by its `distort.py` (`test/e2e-check.mjs`) | our own |
| `lyrics-deu.png` | a lyric line set in a plain font: words from Wilhelm Müller's "Die schöne Müllerin" (1820) (`test/language.test.mjs`) | our own; the words public domain |
| `lyrics-fra.png` | a French lyric line we wrote, set the same way (`test/language.test.mjs`) | our own |
| `edit.musicxml` | a short score written by hand for the editor's test (`test/edit.mjs`) | our own |
