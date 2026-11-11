# TeaVM / WASM Java investigation — Audiveris in the browser

Synthesis of the TeaVM reproduction (`teavm/`) and the alternatives
survey (`alternatives/`), both completed 2026-11-08. Detail lives in
`teavm/TEAVM_SPIKE.md` and `alternatives/ALTERNATIVES.md` (sources in
`alternatives/sources.md`); numbers in `teavm-wasm-results.json`.
Repo untouched (read-only clone at `../repo/`, HEAD `6602144`).

## The question, reframed (clarified 2026-11-08)

Jonathan's main reason for wanting off CheerpJ is **not speed**. It is
**vendor/CDN dependence**: CheerpJ Community licence requires loading
the runtime from Leaning Technologies' CDN
(`cjrtnc.leaningtech.com`); self-hosting is not on the free tier
(£5,000/yr + Small Business at £100/developer/month); Leaning could
narrow the tier, change terms, or shut the CDN path and break the app
on their timetable. He wants **fully self-hosted**: static files he
controls, no vendor server in the loop, no licence server.

So every option below is scored **first on self-hosting / vendor
independence, then on speed**. TeaVM's value is primarily as a
self-hosted exit (Apache-2.0, static Wasm/JS output), with the ~1–3×
speed as secondary. CheerpJ 6.0's WasmGC, even if it works and is
faster, does not solve the problem — it is still Leaning's runtime
from Leaning's CDN. **PRs 1, 3 and 5 are interim CheerpJ
improvements only** — they make the CheerpJ app better, but none
removes the CheerpJ dependency.

"Done" = the site serves its own static files (Audiveris-via-TeaVM
Wasm + JS, tesseract.js, PDF.js, `.traineddata` packs) from its own
hosting, with no request to `leaningtech.com` at runtime.

## Baseline

- App: `jdlehman/score-reader`, AGPL-3.0. Audiveris 5.11 on CheerpJ 5
  / Java 25, batch mode, ~1 min/page after FastMath/FlatMorphology
  patches (down from ~4 min), ~60 MB first download, ~1 GB memory on
  9 pages, Chrome only, cannot start twice in a page.
- Native desktop baseline measured in this investigation
  (hymn-satb.png, 2480×3507, 128 notes): LOAD→HEADS 30.8 s, whole
  page 68–71 s wall (this loaded host; repo's clean figure is 19 s).
- Repo's 2026-11-03 TeaVM spike: bench 707 ms desktop / 1,072 ms
  TeaVM Wasm / 1,913 ms CheerpJ; Audiveris Main under TeaVM 0.14.1
  reported 361 problems then crashed; estimated 2–3 weeks to a first
  page.

## TeaVM — verdict: investigate further (not a drop-in win yet)

**TeaVM 0.16.0** (3 Oct 2026) is the current stable; 0.14.1 is
superseded. `teavm-cli` is discontinued after 0.14.1; `teavm-tooling`
0.16.0 is the programmatic driver.

What the reproduction actually achieved:

- **Bench reproduced in spirit, not absolutes.** Same-band
  conclusion only: best-of-best Wasm/desktop ≈ 1.00× on this loaded
  host (desktop best 1,860 ms, Wasm best 1,863 ms); the 1.5× figure
  from 2026-11-03 is consistent only with the upper end of the Wasm
  range vs the lower end of desktop. Check value identical.
- **Audiveris 5.11 `Main` under TeaVM 0.16.0: 635 problems** (vs 361
  with 0.14.1) — mostly because 0.16.0 reports more, not because
  Audiveris got worse.
- **Headless/batch TeavmMain: 0 problems after 7 rounds of shimming.**
  2,863 classes, 27,661 methods, 10,190,425-byte `classes.wasm`.
  The class-library gap that blocked the 2026-11-03 spike is closed
  for the headless path — shims for AWT geometry/`BufferedImage`,
  Swing stand-ins, single-threaded executors/locks, patched Audiveris
  sources (240 classes), ASM jar rewrites.
- **But no Audiveris step completed under TeaVM in either backend:**
  - **WasmGC:** Node 24 refuses to load the module —
    `Compiling function #272 failed: call_ref[1] expected type
    (ref null 48), found block of type (ref null 467)`. A TeaVM
    WasmGC codegen bug. ADVANCED optimisation fails the same way
    (fn #273); FULL crashes the TeaVM compiler itself
    (`AssertionError: Variable used before definition`).
  - **JavaScript backend:** compiled (0 problems, 8.8 MB JS),
    main() genuinely executed at 85–99% CPU — and **never
    completed**: ~47 min wall, terminated (SIGTERM) with zero
    output, never reached HEADS. Native LOAD→HEADS is 30.8 s, so
    JS is >90× slower here or stuck in a pathological path.
    Leading hypothesis (unverified): stub-font blank templates make
    HEADS match everywhere. Testable on a smaller page or with
    per-step progress prints.
- **Effort to first page (rough, from TEAVM_SPIKE.md §7):** ~0.5–1
  day to identify function #272 and file/minimise a TeaVM issue
  (critical path); if WasmGC is fixed/worked around, ~1–2 days to
  run TeavmMain and compare LOAD→HEADS (expect 0 heads in Phase A
  — stub classifier); Phase B pre-rendered note-head templates
  ~2–4 days; after that the JAXB/MusicXML export path, OCR
  (tesseract.js, same as CheerpJ app), and the download/memory
  comparison. The 2–3 week estimate from the repo spike is not
  confirmed or refuted — it is blocked behind the codegen bug.

## Alternatives — verdicts (self-hosting scored first)

| Option | Verdict | Self-hosted? | Decisive reason |
|---|---|---|---|
| CheerpJ 5 (stay) | **GO — safest short term, interim only** | No — CDN + Community licence, self-hosting £5,000/yr | Only option running Audiveris unmodified today; Community £0 fits this non-commercial OSS project. Holding position, not the destination. CheerpJ 5.0 launched 2 Nov 2026 (Java 21/25, full JDK); WasmGC experimental, production in 6.0 early 2027 — and the repo's own test says wasmGC mode crashes ("illegal cast") on this app, so it is a retest candidate, not a switch. |
| TeaVM 0.16.0 | **Investigate further** | **Yes — Apache-2.0, static output** | Only credible open-source AOT path; class-library gap closed, but WasmGC codegen bug (#272) and JS backend never completing a page are the blockers. |
| GraalVM Native Image → Web Image | **Investigate further (watch, don't start)** | Yes, in principle | Real WASM target since GraalVM 25.1, but experimental, single-threaded ("threading, networking, graphics still missing"), no AWT in stock Native Image, no JAXB/Web Image evidence. Same gaps as TeaVM on a younger backend. Revisit in 6–12 months. |
| J2CL / GWT | **No-go** | Yes, but irrelevant | No AWT, no threads, no JAXB, source-only (not bytecode). J2CL still "alpha developer preview, not an official Google product"; GWT 2.13.1 (19 Jun 2026) alive but architecturally incapable. |
| Bytecoder | **No-go** | Yes, but irrelevant | Last release 2024-05-10, no release in ~2½ years, no AWT/JAXB/thread evidence. |
| JWebAssembly | **No-go** | Yes, but irrelevant | Milestone 1 only; threads, exceptions, GC, reflection explicitly Milestone 3.0 (undone); README says file/socket "will never work" in-browser. |
| JSweet / Rise JVM | **No-go** | — | Dormant (JSweet ~2022) / no verifiable release or capability (Rise JVM). |
| Bytecode Alliance Endive | **No-go for the browser question** | n/a — wrong direction | JVM-native Wasm runtime (runs Wasm *inside* a JVM, fork of Chicory, Apache-2.0, 1.2.0 on 31 Oct 2026, WasmGC spec tests pass). Opposite direction from TeaVM/CheerpJ; needs a JVM, which a browser tab has no — that is exactly CheerpJ's job. Niche only: a server-side JVM hosting a Wasm-packaged model without JNI, if that architecture is ever chosen. |
| Server-side / native Audiveris service | **Investigate further — viable fallback & hybrid, not the default** | Yes (your server) — but a different dependence | Deletes the porting problem, desktop speed (~19 s/page vs ~100 s in-browser), ~$7–25/month rough (Fly.io 1 GB ~$6.70/mo). But breaks "nothing uploaded" and offline use, and the AGPL question (pristine vs patched Audiveris on the server) must be settled first. Best shape: in-browser default + opt-in server read for hard pages. |
| Anything else credible | **None found** | — | Searches turned up only the above, plus the JavaBox/QEMU curiosity (227 MB blob, ~20 s boot — no-go) and Leaning's CheerpX/BrowserPod (Java "through CheerpJ" still coming). |

## Non-English OCR — added 2026-11-08

**TeaVM does NOT restore native Audiveris Tesseract — no mechanism.**
`TesseractOCR` reaches libtesseract via a JavaCPP/JNI bridge
(`org.bytedeco.tesseract.TessBaseAPI`, per-OS native jars); TeaVM
restricts JNI and compiles bytecode only. The only loophole (linking
an Emscripten C library) would just re-implement tesseract.js.
CheerpJ has the identical constraint — the repo already sets
`TesseractOCR.useOCR=false`.

**Non-English OCR in the browser is a GO via tesseract.js packs.**
Audiveris already has the language plumbing (`Language` specs like
`"DEU+ENG+ITA"`, `Book`/`Params` `ocr-languages`, default `"eng"`).
The actual gap is small and concrete: `BrowserOCR` receives a
`langSpec` but `app/reader.js:200-202` drops it at the JS bridge,
`app/ocr.js:22` hard-codes `createWorker('eng')` on a singleton
worker, `BrowserOCR.LANGUAGES` is `{"eng"}`, and `build.sh` vendors
only `eng.traineddata.gz`. Fix: parameterise the worker by spec,
pass `languages` through the bridge, widen `LANGUAGES`, vendor the
needed `.traineddata.gz` files (~6–10 MB each standard 4.0.0 model:
deu 6.77, fra 5.99, spa 7.98 MB), add a per-score language picker.
Effort well under a day for the plumbing; real work is measuring
accuracy per language on real pages. **Open question: which
languages?** German/French/Italian/Spanish/Latin cover the choral
repertoire. Full evidence in `teavm/TEAVM_SPIKE.md` §10.

## Recommended path (reframed: independence first)

1. **Stay on CheerpJ 5 now — as an interim, not the destination.**
   Pin the `5.0` loader, re-benchmark on 5.0, calendar-check CheerpJ
   6.0 (early 2027) to retest `wasmGC: true`. PRs 1/3/5 extend the
   stay; they do not end it.
2. **Continue the TeaVM spike as the self-hosted exit — the primary
   goal, not a performance project.** Next step is the function #272
   diagnosis (~0.5–1 day): bisect the entry point until the
   validation failure disappears, or get a debug-name mapping, and
   file/minimise a TeaVM issue. If WasmGC cannot be worked around,
   the JS backend is **not** a proven fallback (47 min, zero output)
   and needs the same diagnosis.
3. **Do not start work on GraalVM Web Image, J2CL/GWT, Bytecoder,
   JWebAssembly, JSweet or Rise JVM.** GraalVM only, in 6–12 months,
   if its threading/graphics story changes.
4. **Keep server-side as the fallback, in hybrid form** (opt-in
   server read for hard pages), after settling the AGPL question
   and the retention/consent design.
5. **Watch the commercialisation tripwire.** The moment Sectional
   charges for anything built on this, CheerpJ Community stops
   applying. Under the reframed priority this is less a price
   question than a deadline: the date by which the self-hosted
   exit must exist.

## Files

- `TEAVM_WASM.md` — this synthesis. `teavm-wasm-results.json` —
  machine-readable numbers.
- `teavm/TEAVM_SPIKE.md` — TeaVM reproduction, shims, timings,
  blockers (§5 WasmGC fn #272, §6 JS 47-min run, §7 verdict,
  §10 non-English OCR), `timings.json`, `problems*.txt`,
  `build.sh`, `shims/`, `patched/`, `entry/`, `out-teavm/`,
  `out-js/`.
- `alternatives/ALTERNATIVES.md` — per-option verdicts with
  evidence, recommended path; `alternatives/sources.md` — every
  primary source URL + date checked (2026-11-08).
