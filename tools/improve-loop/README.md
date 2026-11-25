# Self-improvement loop

Tooling for improving score-reader's reading with time spent: a
benchmark, a way to verify that a result is an improvement, a way to
check that the verification itself is solid, and a loop — benchmark,
identify issues, hypothesise, verify, keep what improves — with the
tradeoffs written down.

## What it is

- `run.py` — runs desktop Audiveris 5.11 over registry pages (the
  fast path) and scores each output. One results file per run in
  `runs/<run-id>.json`. Resumable, cached, `--force` to re-run.
- `score.py` — scores one `.mxl` against ground truth, prints
  aggregates for a run, and compares two runs page by page (never
  only an aggregate). `score.py --mxl <file> --page <id>` scores a
  single output.
- `score_all.py`, `open_score.py` — the scorers (per-bar multisets of
  pitch/type; measure-duration validity; lyric recall where the GT
  has lyrics). Notes are compared by content, never by id offset.
- `audiveris.py` — runs desktop Audiveris on one image and summarises
  a `.mxl`. Audiveris + JDK come from the repo's own `./setup.sh`
  (`.work/`); overrides `SCORE_READER_JAVA` / `SCORE_READER_CLASSPATH`.
- `recover.py` — photometric recovery of a degraded page image (the
  `median+rl` method is the shipped config; every other method in it
  is a documented NO-GO — see EXPERIMENTS.md).
- `build_registry.py` — regenerates `registry.json` from the corpus.
- `registry.json` — the benchmark: 44 pages, CC0 and Public Domain
  only (see "Licence" below). Paths are relative to the corpus root.
- `verifier_health.py` — checks the checkers: canonical control
  outputs, GT provenance, alignment method, whether a fresh Wasm
  rebuild / re-run is possible. Writes `verifier-health-<date>.md`.
- `VERDICT_RULES.md` — the ten enforceable rules a KEEP verdict has
  to satisfy. `HEURISTIC_POLICY.md` — when a gate or a fallback is
  allowed, and how to adjudicate help-one/hurt-another.
- `EXPERIMENTS.md` — the append-only log: every experiment, its
  verdict, and the numbers. `LESSONS.md` — what the loop has learned.
- `BENCHMARK.md` — the benchmark design (registry, runner, scorer,
  limits) in detail.
- `fixtures/smoke/` — a synthetic page (GT + predicted `.musicxml`)
  and `smoke_test.py`, which scores it and asserts the numbers. Run
  it after any scorer change: `python3 smoke_test.py`.

## How to run a loop pass

Prerequisites:

1. `./setup.sh` at the repo root (Audiveris 5.11.0 + Temurin JDK 25
   into `.work/`). The loop never builds Audiveris itself.
2. The corpus: the local test set (page images + ground truth +
   legacy `.mxl`). It is not in this repo. Pass its root with
   `--corpus` or `SCORE_READER_CORPUS`. The registry's paths are
   relative to it.
3. For the `deblur` method only: `pip install -r requirements.txt`
   (opencv, numpy, Pillow, scipy), or point `SCORE_READER_PHOTO_PY`
   at a Python that has them.

Then:

```
python3 run.py --list-subsets            # what the benchmark holds
python3 run.py --subset default --method baseline --run-id 20261125-baseline
python3 run.py --subset photo-hard --method deblur  --run-id 20261125-deblur
python3 score.py runs/20261125-deblur.json --baseline runs/20261125-baseline.json
```

Write the verdict up in EXPERIMENTS.md (numbers, per-page table,
what regressed, what was not measured) and the lesson in LESSONS.md.
A change is kept only when VERDICT_RULES.md says so.

## What the loop is not

- It does not change how pages are read. It is benchmark tooling
  only — it touches nothing in `app/`, `teavm/`, or `test/`. A change
  to reading itself is proved by `test/prove.mjs` (see
  `test/corpus/README.md`, "Proving a change"); this loop is the
  desktop fast path that finds candidate changes worth proving there.
- It is not a Wasm check. The desktop harness is the fast path; the
  final check for a kept change is a manual in-browser Wasm build
  run. Nothing here claims Wasm parity.
- It has no Tesseract in this environment, so lyric recall reads 0
  everywhere here. That is an environment gap, not a result.

## Licence

The published registry holds only what the repository may hold
(`test/corpus/README.md`, "What may be committed"): **CC0 and Public
Domain, music and edition both**. Pages under any other licence, a
testing-only encoding, or a private score are not in this registry
and are not named here — they stay in the local test set, recorded
there. The generator enforces it: `build_registry.py` skips any page
whose licence is not CC0 or Public Domain, and `verifier_health.py`
fails the audit if any `local_only` entry appears. Run outputs
(`runs/`, `audiveris-out/`, `recovered/`) are gitignored — they are
local working files, never committed.

## Current state

The loop's first repo-native experiment (EXP-2026-11-25-01, in
EXPERIMENTS.md) measured the shipped deblur step on the hard pages
the widened preflight gate (median staves ≤ 3) would newly catch:
summed GT exact 19 → 107 (+88) across the three pages the published
registry holds, no clean page regressed, reproduction run identical.
The same hypothesis measured on the full local registry (which also
holds pages the repo does not name) gained +171. Widening PR #7's
gate to ≤ 3 is a decision for the reader of that PR, not this one.

The next slice is hymnal OCR recall (needs LyricsBuilder
instrumentation + Tesseract, neither available in this environment).
