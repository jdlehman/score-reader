# Experiment log — score-reader self-improvement loop

Append-only. Never edit an entry after its verdict is recorded; a
correction or follow-up is a new entry that cites the old one. (Modelled
on the fantasy-football analyst pattern: every take through a
deterministic checklist, logged with evidence, graded, lessons written
back.)

## Publication note (read before citing this log)

This is the published log. The full local log — with per-page numbers
for pages the repository does not name — stays in the workspace with
the local test set. In this file:

- Per-page numbers are given only for pages in the published registry
  (`registry.json`: CC0 and Public Domain only).
- Pages the repository does not name are referred to generically
  ("a hard SATB page in the local test set") and without per-page
  numbers. Their verdicts and the reasons for them are recorded; the
  numbers live in the local reports cited as sources.
- Run ids refer to run files retained in the workspace (local working
  files, gitignored, not committed). A run is reproducible from this
  checkout by re-running the loop with the same subset and method.

## Entry schema

Every entry uses this schema. Fields marked * are required for a verdict;
an entry without them is a note, not an experiment.

```
### EXP-YYYY-MM-DD-NN — <short title>
- Date: YYYY-MM-DD
- Hypothesis: <one sentence, falsifiable — what should improve, and where>
- Change: <exact code/parameter change, file + values; link or path>
- Gate: <gate predicate, or "ungated" — see HEURISTIC_POLICY.md §1>
- Method: <pipeline side — harness (single-threaded, authoritative) or
  batch (stock, cpuCount+1 threads); inputs; scorer version>
- Baseline run id: <id/path of the baseline run>
- Experiment run id: <id/path of the experiment run>
- Per-page before/after: <table — page | GT | baseline exact / pred notes /
  measures-valid | experiment exact / pred notes / measures-valid | FAILs>
- Controls: <canonical md5s after the change — hymn / Lindenbaum;
  PASS/FAIL>
- Verdict: KEEP / DISCARD / UNDECIDED — <one line, citing the verdict rule
  that decided it, e.g. "DISCARD per VERDICT_RULES rule 1: clean-page
  regression on X">
- Evidence: <the numbers that support the verdict; FAILs explained with
  the failing Audiveris step from the log>
- Lessons: <what this teaches, in one or two lines; also appended to
  LESSONS.md>
```

Run ids: use the run's output directory or log path (e.g.
`photometric/audiveris-out/median+rl/`), not a bare date — two runs on
one day must be distinguishable.

## Prior art — verdicts already decided before this log existed

These are summaries of work done 2026-11-10 and 2026-11-15, recorded
here so the loop starts from existing knowledge, not zero. No new
experiments are recorded in this section. Sources: the photometric
recovery report, the RL tuning report, and the preflight corpus report
in the local workspace. All numbers below are copied from those
reports, not re-measured here. Desktop Audiveris 5.11, no Tesseract
(no lyrics anywhere — environment gap).

### PRIOR-01 — Median + Richardson–Lucy deblur, gated on preflight warn — CONDITIONAL GO (shipped config)
- Date: 2026-11-10.
- Hypothesis: deblur (3×3 median → RL, Gaussian PSF σ=1.8, 15 iters) rescues
  hard synthetic-photo pages without hurting mild/moderate pages.
- Change: 3×3 median → RL σ=1.8, 15 iters, hard-gated on preflight warn
  (`warn == 'no-staves'`; PR #7 pattern).
- Method: desktop harness, 15 synthetic-photo pages (5 pages × mild /
  moderate / hard), `open_score.score`.
- Per-page before/after (exact pitch; GT in brackets):
  Lindenbaum hard [216]: 9 → **93**; Gute Nacht hard [223]: FAIL → **33**;
  a hard SATB page in the local test set: FAIL → FAIL (unrescued);
  Beethoven hard (pred notes, no GT): 635 → **689**; IMSLP hard (pred
  notes, no GT): 193 → 36. No loss on any mild/moderate page.
- Verdict: **CONDITIONAL GO** — the shipped parameters. The condition is
  the gate: ungated, the same method is NO-GO (see PRIOR-02/03). Real-world
  value still unproven: the corpus has no real blurred photo, and the
  shipped gate fires on only 2 of the 6 hard synthetic pages in the
  published registry.
- Lessons: gate first, rescue second; a rescue that only fires where
  Audiveris would give up cannot hurt a clean page.

### PRIOR-02 — Plain RL, 5 iterations, ungated — NO-GO
- Date: 2026-11-10.
- Change: RL σ=1.8, 5 iters, no median pre-step, ungated.
- Per-page before/after: Lindenbaum hard 9 → **186** (above the clean
  page's 172 — treat as "reaches clean territory", not "beats clean");
  Gute Nacht hard FAIL → 3; a moderate SATB page in the local test set
  collapses; IMSLP hard 193 pred notes → **FAIL** (no output).
- Verdict: **NO-GO per VERDICT_RULES rule 1 (clean/moderate regression)
  and rule 4 (ungated).** The strongest single-page gain in the whole
  tuning history was refused because it broke other pages. This is the
  precedent rule 1 exists for.
- Lessons: a big win on one page never outweighs a collapse elsewhere;
  iteration count is the dominant knob and its cliffs move with σ.

### PRIOR-03 — Plain RL, 15 iterations, ungated — NO-GO
- Date: 2026-11-10.
- Change: RL σ=1.8, 15 iters, no median pre-step, ungated.
- Per-page before/after: Lindenbaum hard 9 → 94; Gute Nacht hard FAIL →
  FAIL ("No system found" after SCALE passed); a hard SATB page in the
  local test set: FAIL → no rescue.
- Verdict: **NO-GO.** Worse than median+RL on the rescue pages and
  ungated. Plain RL at 15 iters has no full-15-page safety data.
- Lessons: the median pre-step is load-bearing for Gute Nacht, not
  cosmetic.

### PRIOR-04 — Shadow correction, unsharp, Wiener, CLAHE, contrast, and compositions — NO-GO
- Date: 2026-11-10.
- Change: shadow-gauss, shadow-close, unsharp, wiener5, CLAHE, contrast,
  and shadow+unsharp / shadow+RL / shadow+wiener / median+shadow+unsharp.
- Per-page before/after (GT hard pages): shadow-gauss FAIL (SCALE) on all
  three GT hard pages — worse than baseline on Lindenbaum (70 notes/9
  exact → no output); unsharp FAIL on all three; wiener5 FAIL on all
  three; CLAHE Lindenbaum hard FAIL at SCALE; shadow+RL FAIL on all
  three (incl. NPE "measure is null"); median+shadow+unsharp FAIL on all
  three. Best of the family: shadow+unsharp, Lindenbaum 1 exact.
- Verdict: **NO-GO, all of them.** Several are worse than doing nothing.
- Lessons: **preflight confidence does not predict Audiveris output.**
  Shadow methods lift preflight staves/confidence on hard pages while
  making Audiveris fail outright. Screen recovery methods by Audiveris
  output, never by preflight alone.

### PRIOR-05 — Adaptive RL iteration count (σ=1.8) — NO-GO
- Date: 2026-11-15 (177 Audiveris jobs).
- Change: stop RL early by a pixel signal instead of fixed 15 iters.
  Signals tested: row_peakiness, rel_update, vert_grad, dark_frac.
- Per-page before/after (GT exact summed over hard + moderate cells):
  fixed 15 = **733**; fixed 20 = 809; fixed 8 = 649. Best rule
  (dark-frac plateau): 780 — beats fixed 15 on GT total but picks it3
  on Gute Nacht hard (33 → **7**), sacrificing the one rescue where
  recovery turns nothing into something. Another rule picks the
  moderate-page collapse; a third degenerates to fixed-15 behaviour.
- Verdict: **NO-GO.** No adaptive rule beats fixed 15 safely. The
  headroom (best-per-page GT total 813 vs fixed-15's 733) is real but
  not reachable from these pixel signals — the cliffs live in
  Audiveris's scale/system detection, not in the pixels.
- Lessons: non-monotonic iteration curves with page-specific cliffs
  defeat early stopping; a rule that wins the aggregate while killing
  the flagship rescue is a failed rule.

### PRIOR-06 — Smaller PSF per severity (σ=1.0 / σ=1.2) — NO-GO
- Date: 2026-11-15.
- Change: median+RL at 5/8/15 iters with PSF σ=1.0 or σ=1.2, as a
  per-severity rule.
- Per-page before/after: σ=1.0 rescues a moderate SATB page in the local
  test set at 5 iters (no collapse) but collapses it again at 8 iters,
  and FAILs every hard GT page at every iter count. σ=1.2 is safe at
  moderate at all tested iters but gains nothing over σ=1.8/15 there
  and is useless at hard (FAIL on both Lieder hard pages and Beethoven
  hard; Lindenbaum hard only 43 at it15 vs 93–170 for σ=1.8).
- Verdict: **NO-GO as a per-severity rule.** A severity switch would need
  a severity estimator and buys ~0, while a misclassified hard page
  lands on a certain FAIL.
- Lessons: the σ≈blur hypothesis holds at one point and fails
  everywhere else; a switch that needs a perfect classifier to be safe
  is not a switch.

### PRIOR-07 — Median pre-step gain (Gute Nacht FAIL → 33) — DOES NOT REPRODUCE; median kept only as the tested config
- Date: 2026-11-15.
- Change: second-page check of the median pre-step on two new Lieder
  hard pages (Ständchen, Frühlingssehnsucht), RL 15 iters, σ=1.8.
- Per-page before/after (hard, exact pitch): Ständchen [192]: raw 10 →
  plain RL 17 → median+RL **14**; Frühlingssehnsucht [123]: raw 0 →
  plain RL 18 → median+RL **FAIL**; Lindenbaum [216]: median 93 vs
  plain 94 (tie); Gute Nacht [223]: median 33 vs plain FAIL (the
  original gain).
- Verdict: **DOES NOT REPRODUCE as a hard-page win.** Across four Lieder
  hard pages the median step wins once, ties twice, loses once. The
  Gute Nacht gain is a page-specific cliff effect, not a robust property
  of the median step. **The median step stays — as the tested
  configuration, with the limitation on record** — because shipped
  median+RL (15 it) is the only configuration with full 15-page safety
  data (no loss on any mild/moderate page in either round), and plain
  RL at 15 iters has no equivalent full-15 safety data.
- Lessons: one-page wins do not generalise; keep the tested config for
  its safety data, not for the story that motivated it. Known
  limitation: on some hard pages (Frühlingssehnsucht) the median step
  kills a rescue plain RL would give. A dual-path is not available
  without Audiveris in the loop to judge.

### PRIOR-08 — RL variants rl3 / rl25 / σ=2.5 — NO-GO as replacements
- Date: 2026-11-10.
- Per-page before/after (GT hard, exact): rl3 — Lindenbaum 60, Gute
  Nacht 22, a hard SATB page in the local test set: FAIL; rl25 —
  Lindenbaum 55, Gute Nacht FAIL, same page 0; rl-s25 (σ=2.5, 15 it) —
  Lindenbaum 168, Gute Nacht FAIL, same page still not a rescue.
- Verdict: **NO-GO.** No variant beats the shipped median+RL config on
  the rescue pages.
- Lessons: iteration count dominates; more iterations amplify sensor
  noise and ringing (Lindenbaum exact 60 → 186 → 94 → 55 across
  3/5/15/25 iters).

## Open questions (not verdicts)

- **Gate widening for PR #7's deblur:** should the gate also fire when
  the median staff count is very low (≤ 3) rather than only on
  `no-staves`? On the published registry the shipped gate fires on 2/6
  hard photos; median staves ≤ 3 takes that to 5/6, newly catching the
  three pages in EXP-2026-11-25-01, with zero new false flags (0/26
  non-photo pages ≤ 3). The one hard photo it still misses is the
  22-stave orchestral page. ≤ 4 gains nothing and falsely flags clean
  pages (per the preflight corpus analysis). **Undecided** — needs a
  decision from Jonathan; EXP-2026-11-25-01 supplies the deblur-effect
  evidence for it.
- **A hard SATB page in the local test set remains unrescued** by every
  method tried. Any future rescue claim for a page like it starts from
  FAIL, not from a partial win.

## New entries go below this line

<!-- Append new EXP- entries below. Do not edit the prior-art section. -->

## New entries

### EXP-2026-11-25-01 — Shipped deblur on the three hard pages the ≤3 gate would newly catch (published registry)
- Date: 2026-11-25
- Hypothesis: The shipped deblur step (3×3 median → RL σ=1.8, 15 iters) improves the three hard pages the widened ≤3 gate would newly catch that the published registry holds — hallelujah-imslp-p1-hard, lindenbaum-hard, staendchen-hard — without regressing anything the gate would leave alone.
- Change: None to the pipeline. Method under test is the shipped `deblur` config (`run.py` method `deblur` = `recover.py` `median+rl`, 3×3 median → RL σ=1.8, 15 iters), applied to the 3 slice pages. Gate under test: median preflight staves ≤ 3 (plus no-staves warn) instead of the shipped `warn == 'no-staves'` only.
- Gate: Median preflight staves ≤ 3 (or preflight warn `no-staves`). Computable before deblur runs, on the same input. Measured on the published registry: fires on all 3 slice pages (staves 2/2/2, warn null on all three — the shipped gate misses all three); fires on none of the controls — clean counterparts staves 12/8/5, mild variants 12/8/5, moderate variants 10/6/4 — and on 0/26 non-photo registry pages (0 false positives; ≤4 is the threshold that falsely flags clean pages, per the preflight corpus analysis).
- Method: Desktop harness (single-threaded, authoritative comparator), `run.py` + `score.py` wrapping `open_score.score`, no Tesseract (lyric 0 everywhere is the environment gap, not a result). Baseline and experiment both through `run.py` from this checkout, same harness.
- Baseline run id: `tools/improve-loop/runs/20261125-baseline-pr.json` (12 pages, 11 ok / 1 no-output; slice pages all ok). The one no-output is the Gute Nacht hard photo, which fails in desktop Audiveris at the SCALE step in this run and in the local baseline runs too — it is not part of the slice. Control baselines: staendchen mild/moderate from the local tuning report 2026-11-15 (175/192, 174/192 — same harness, earlier run); lindenbaum + IMSLP mild/moderate from legacy baseline `.mxl` re-scored fresh with `score.py` in this session (lindenbaum mild 172/216, moderate 172/216; IMSLP mild pred 657 valid 30/86, moderate pred 625 valid 22/101, no GT).
- Experiment run id: `tools/improve-loop/runs/20261125-deblur-slice-pr.json` (0.3 s; 3 ok / 0 no-output; all cached from legacy deblur `.mxl`). Reproduction run id: `tools/improve-loop/runs/20261125-deblur-slice-pr-repro.json` (`--force`, 3 fresh Audiveris runs, 376.7 s; scored metrics identical on all 3 pages — see Evidence).
- Per-page before/after: page | GT | baseline exact / pred notes / measures-valid | deblur exact / pred notes / measures-valid | FAILs
  - photo-hallelujah-imslp-p1-photo-hard | none (structural only) | — / 193 / 5-45 | — / 36 / 11-32 | none (validity 11.1% → 34.4%, valid measures 5 → 11)
  - photo-lieder-lindenbaum-photo-hard | 216 | 9 / 70 / 0-5 | 93 / 170 / 43-75 | none (Δ exact +84)
  - photo-lieder-staendchen-photo-hard | 192 | 10 / 45 / 0-6 | 14 / 32 / 8-12 | none (Δ exact +4)
  - Summed GT exact: baseline 19 → deblur 107 (gain +88). Controls (gate does not fire): staendchen mild 175/192, moderate 174/192; lindenbaum mild 172/216, moderate 172/216; IMSLP mild/moderate structural-only as above; clean counterparts lindenbaum 172/216, staendchen 175/192 (from baseline run; IMSLP clean scan validity 0.260, no GT).
- Controls: No pipeline code was touched, so the canonical controls were not re-run in this experiment. Stored-output check per the verifier run 2026-11-25 (with `--fork`, `--live`): the two controls whose pages are in the published registry — hymn 44,105 B / `75637092…`, Lindenbaum 99,305 B / `dbd546ba…` — PASS (4/4 files), plus a live hymn re-run against full-out113 reproducing the canonical md5 exactly. PASS.
- Verdict: **KEEP** — the deblur *effect* on these three pages under the ≤3 gate. Rule 2 met with margin (+88 summed, two pages ≥ +3: lindenbaum +84, staendchen +4); rule 1 met (no clean page regresses — gate FP 0 on the registry, no clean page in the experiment); rule 10 met (reproduction run identical on all 3 pages). This verdict is about the deblur effect only — the decision whether to widen PR #7's gate to ≤3 belongs to Jonathan; the gate implication is stated separately below.
- Evidence: Baseline run `20261125-baseline-pr` slice numbers (lindenbaum 9/216, staendchen 10/192, IMSLP pred 193 valid 5/45 — all cached legacy re-scored). Deblur run `20261125-deblur-slice-pr`: lindenbaum cached legacy re-scored 93/216 (matches PRIOR-01); staendchen cached legacy re-scored 14/192 (matches PRIOR-07); IMSLP cached legacy re-scored pred 36 valid 11/32 (matches PRIOR-01's "193 → 36"). `score.py --baseline` comparison: 3 improved / 0 regressed / 0 unchanged on the slice. Reproduction run `20261125-deblur-slice-pr-repro` (`--force`, 3 fresh Audiveris runs, 376.7 s): exact/pred/validity identical on all three pages (lindenbaum 93/170/43-75, staendchen 14/32/8-12, IMSLP 36/11-32) — the only differing field is the `mxl` path string (cached legacy filename vs fresh-run filename), not a score. No FAILs in either run on the slice, so rule 3 is N/A (no FAIL → output rescue; all improved pages have validity ≥ 25%: lindenbaum 57%, staendchen 67%, IMSLP 34%). IMSLP pred-note drop 193 → 36 adjudicated per HEURISTIC_POLICY §3: IMSLP-hard is a degraded page, not clean; the baseline's 193 notes are mostly invalid output (5/45 valid, 11.1%) while deblur yields fewer but structurally better notes (11/32 valid, 34.4%; absolute valid measures 5 → 11), and the scorer marks it improved on validity (+0.233). PRIOR-01 already adjudicated this exact tradeoff inside the CONDITIONAL GO. Not a loss; no narrower gate needed — winners and IMSLP are caught by the same ≤3 gate and all improve on validity. Licence: all three slice pages are in the published registry (IMSLP: Public Domain; lindenbaum/staendchen: CC0); no local-only pages in the slice; no derivatives embedded in any file written. The same hypothesis measured on the full local registry (which also holds pages the repo does not name) gains +171 — the extra +83 is a fourth page that stays in the local log. Caveats: desktop harness only — no Wasm parity claim (final check is a manual in-browser run); lyric recall 0 everywhere is the no-Tesseract environment gap.
- Gate implication (separate from the verdict): widening PR #7's gate from `warn == 'no-staves'` to median staves ≤ 3 would newly catch these 3 hard pages and gain +88 summed exact-pitch on the 2 GT pages (+84 lindenbaum, +4 staendchen) plus the IMSLP validity gain (11% → 34%), while firing on no clean, mild, or moderate control in this registry (0/26 non-photo pages ≤ 3). What it would lose: nothing measured — no control page fires, no clean page regresses, and the IMSLP note-count drop is a removal of invalid notes, not a loss of real ones. The gate-widening decision itself is Jonathan's; this entry supplies the deblur-effect evidence for it.
- Lessons: the ≤3 gate's value is concentrated in pages the shipped gate misses entirely (all three slice pages have warn null); a gate validated on the corpus can be widened with measured evidence rather than by analogy.
