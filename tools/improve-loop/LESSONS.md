# Lessons — score-reader self-improvement loop

Living document. The loop-pass agent appends here after every experiment
verdict; the fantasy-football analyst pattern applies — lessons are
written back into the working rules, not left in the log.

## Publication note

This is the published lessons file. Per-page numbers are given only
for pages in the published registry (`registry.json`: CC0 and Public
Domain only). Pages the repository does not name are referred to
generically ("a hard SATB page in the local test set"); the full
local lessons file, with their numbers, stays in the workspace.

## How to append

Copy this block to the end of the file, fill it in, keep the numbering
sequential. One lesson per block. A lesson must name its evidence;
a lesson without evidence is a hunch and goes in the experiment entry,
not here.

```
### L-NN — <short title>
- Statement: <one sentence — what to do / not do, and when>
- Evidence: <the numbers or the failure that taught it, with page names>
- Date / source: <YYYY-MM-DD, experiment id or report path>
```

## Seeded lessons (from prior art, 2026-11-10 / 2026-11-15)

### L-01 — Gate first, rescue second
- Statement: A recovery heuristic only ships gated on a measurable
  condition that cannot fire on a clean page; ungated is NO-GO by default.
- Evidence: Median+RL σ=1.8/15it gated on preflight `no-staves` is the
  shipped config (no loss on any mild/moderate page); the same method
  ungated, and plain RL 5it ungated, collapse a moderate SATB page in
  the local test set and break IMSLP hard (193 notes → FAIL).
- Date / source: 2026-11-10, PRIOR-01/02 in `EXPERIMENTS.md`.

### L-02 — Preflight confidence does not predict Audiveris output
- Statement: Never screen or score a recovery method by preflight
  staves/confidence; screen by Audiveris output only. Preflight is a
  gate input, never a score.
- Evidence: Shadow correction lifts preflight staves/confidence on hard
  pages while making Audiveris fail outright on all three GT hard
  pages; median+shadow+unsharp clears the preflight warn on Gute Nacht
  hard (6 staves, conf 0.72) yet Audiveris still fails at SCALE.
- Date / source: 2026-11-10, PRIOR-04 in `EXPERIMENTS.md`.

### L-03 — Audiveris output is cliff-sensitive; small deltas are noise
- Statement: Single-page exact-pitch deltas of a few notes are noise,
  not signal. Judge by the aggregate threshold (≥ +10 summed, ≥ 2 pages
  at ≥ +3) and by FAIL → output rescues, not by one page's wobble.
- Evidence: Lindenbaum hard exact flips 93 ↔ 167–170 across RL iteration
  counts with near-identical pred note counts (170/171); Gute Nacht hard
  rescue numbers are systems-found-or-not cliff effects.
- Date / source: 2026-11-15, PRIOR-05 in `EXPERIMENTS.md`.

### L-04 — A one-page win does not generalise
- Statement: A gain seen on one page must be re-checked on a second page
  of the same class before it is believed; a win that does not reproduce
  is a cliff artifact.
- Evidence: Median pre-step Gute Nacht hard FAIL → 33 did not reproduce:
  Ständchen hard 14 vs plain RL 17, Frühlingssehnsucht hard FAIL vs
  plain RL 18, Lindenbaum hard 93 vs 94. Across four Lieder hard pages
  the median step wins once, ties twice, loses once.
- Date / source: 2026-11-15, PRIOR-07 in `EXPERIMENTS.md`.

### L-05 — Keep the tested config for its safety data, not its origin story
- Statement: When a component's motivating win does not reproduce, keep
  it only if it is the configuration with the full safety data — and
  record the limitation openly.
- Evidence: The median pre-step stays in the shipped config because
  median+RL (15 it) is the only configuration with full 15-page safety
  data (no loss on any mild/moderate page in either round), not because
  the Gute Nacht gain reproduces. Known limitation: on some hard pages
  (Frühlingssehnsucht) it kills a rescue plain RL would give.
- Date / source: 2026-11-15, PRIOR-07 in `EXPERIMENTS.md`.

### L-06 — Iteration count is the dominant RL knob, and its cliffs move with σ
- Statement: Do not tune RL iterations and PSF σ independently; a cliff
  that moves when σ changes has not been fixed, only relocated.
- Evidence: Lindenbaum hard exact 60 → 186 → 94 → 55 across RL 3/5/15/25
  iters; σ=1.0 rescues a moderate SATB page in the local test set at 5
  iters then collapses it at 8 iters.
- Date / source: 2026-11-10 / 2026-11-15, PRIOR-02/06/08 in
  `EXPERIMENTS.md`.

### L-07 — Compare inters/notes by content, never by id offset
- Statement: Alignment for scoring is per-bar multiset by pitch (and
  type); position/id-offset pairing is meaningless when part order or
  splits differ.
- Evidence: Spot-check 2026-11-25 (verifier health): desktop Lindenbaum
  vs GT scores 172/216 content-based but 25/172 by naive index-offset
  pairing (GT voice 15 + piano 201 vs pred P1 28 + P2 162).
- Date / source: 2026-11-25, verifier health §1c.

### L-08 — Report the preflight warn, never the staff count
- Statement: The preflight staff count is a per-strip median that
  undercounts on dense pages; the warn decision does not use it. Cite
  the warn outcome, not the count, as a gate outcome.
- Evidence: Beethoven p229: 22 staves found for a 36-part page;
  Lindenbaum clean render: 8 staves. Preflight corpus: 119 pages, 7
  flagged, 112 clean.
- Date / source: 2026-11-17, preflight corpus report.

### L-09 — The harness is the comparator; batch and harness are different pipelines
- Statement: Never compare a batch baseline against a harness experiment
  run (or vice versa). Stock Audiveris batches pool `cpuCount + 1`
  threads; the patched harness is single-threaded, and their outputs
  differ.
- Evidence: Batch-vs-harness output gaps measured in the fork work;
  verifier health blind spot 1.
- Date / source: 2026-11-10; `verifier-health-2026-11-25.md` blind spot 1.

### L-10 — A heuristic failure must never lose a page
- Statement: Any heuristic must fall back to the original input on any
  failure (per-page try/catch + module-load fallback, PR #7 pattern).
  A heuristic whose failure mode is a lost page is not shippable.
- Evidence: PR #7 deblur design; no page in the corpus has been lost to
  a deblur failure because the fallback exists.
- Date / source: 2026-11-17, `HEURISTIC_POLICY.md` §2; PR #7.

### L-11 — A hard SATB page in the local test set is unrescued; do not over-read small numbers there
- Statement: No method tried rescues that page. Claims about a page like
  it start from FAIL.
- Evidence: Every RL variant, shadow, unsharp, Wiener, and CLAHE FAILs
  or scores ~0 exact on that page across both tuning rounds.
- Date / source: 2026-11-10 / 2026-11-15, PRIOR-01–04/08 in
  `EXPERIMENTS.md`.

### L-12 — A widened gate is earned by re-measuring the newly caught pages, not by analogy
- Statement: When a gate widening is proposed, measure the deblur effect on exactly the pages the new gate would newly catch, with fresh controls for the pages it must leave alone — and reproduce the experiment run before claiming the gain.
- Evidence: The ≤3 widening newly catches hallelujah-imslp-p1-hard, lindenbaum-hard, staendchen-hard (all warn null, staves 2). Deblur on those three: summed GT exact 19 → 107 (+88; lindenbaum +84, staendchen +4), IMSLP validity 11% → 34%; gate fires on no clean/mild/moderate control (0/26 non-photo registry pages ≤ 3); a `--force` second run reproduced all three pages' scored metrics exactly (only the `mxl` path strings differ). The local log records a further +83 on a fourth page the published registry does not hold.
- Date / source: 2026-11-25, EXP-2026-11-25-01 in `EXPERIMENTS.md`.
