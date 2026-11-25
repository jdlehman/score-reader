# Verdict rules — score-reader self-improvement loop

Short, enforceable keep/discard rules for every experiment. A verdict that
cannot point at the evidence below is not a verdict; it is an opinion.

## Definitions

- **Baseline run / experiment run.** Every experiment names both run ids
  (see `EXPERIMENTS.md`). Both runs use the **same** pipeline side: the
  patched single-threaded desktop harness is the authoritative comparator.
  A batch baseline (stock Audiveris, `cpuCount + 1` threads) may never be
  compared against a harness experiment run — the threading gap alone
  moves numbers (see `verifier-health-2026-11-25.md`, blind spot 1).
- **Clean page.** A page in the benchmark registry that satisfies all
  three at baseline: (a) preflight warn is null, (b) the baseline run
  produces an output file (not FAIL), (c) it is a rendered or real-scan
  page, not a synthetic-photo variant. The 75 clean renders in the
  2026-11-17 preflight corpus are the canonical clean set; mild/moderate
  synthetic photos are **not** clean pages (they are degraded inputs and
  are judged by the rescue rules below, not by this rule).
- **Regression on a page.** Any of: exact-pitch drops by ≥ 1 note vs
  baseline; predicted note count drops by > 2% vs baseline; a page that
  produced output at baseline now FAILs (no output); measures-valid
  drops by more than 2. A 1-note exact-pitch drop is a regression even
  if the aggregate went up — see rule 1.
- **FAIL / no-output run.** Counts as **0** exact-pitch, 0 notes, on
  every page it affects. It is never dropped from the table, never
  averaged away, and must be explained (which Audiveris step failed,
  from the log) in the experiment entry.

## The rules

1. **No keep if any clean page regresses.** One clean-page regression
   vetoes KEEP, whatever the aggregate says. (Precedent: plain RL 5
   iterations gained Lindenbaum hard 9 → 186 but collapsed a moderate
   SATB page in the local test set — an ungated win that was correctly
   refused. A regression on a degraded page does not veto by itself; it
   is judged under rule 5.)
2. **Aggregate gain must clear the threshold.** Summed exact-pitch over
   all GT pages in the benchmark set must improve by **≥ +10**, and at
   least **two** pages must each improve by **≥ +3**. Reasoning: Audiveris
   output is cliff-sensitive — Lindenbaum hard exact flips 93 ↔ 167–170
   across RL iteration counts with near-identical note counts — so
   single-page deltas of a few notes are noise. +10 summed with two
   independent +3 contributors is above the observed cliff noise while
   still reachable by a real rescue (median+RL: Lindenbaum hard 9 → 93,
   Gute Nacht hard FAIL → 33). A gain carried by one page alone is a
   cliff artifact until a second page confirms it.
3. **A rescue must be real.** A FAIL → output rescue counts toward rule 2
   only if the rescued page scores ≥ 10 exact-pitch **and** measures-valid
   ≥ 25% — otherwise it is noise output, not a rescue (precedent: IMSLP
   hard σ=1.2 it15 produced 256 notes but measures-valid 4/47 — quoted
   as a failure, not a win).
4. **A heuristic only ships when gated on a measurable condition.**
   The gate condition must be computable before the heuristic runs, on
   the same input the heuristic will see, and must have a measured
   false-positive rate on clean pages. Pattern: PR #7's deblur runs only
   when preflight warn is `no-staves` — 0/75 clean renders flag, so the
   gate cannot hurt a clean page. An ungated heuristic is a NO-GO by
   default; the burden is on the proposer to show the gate.
5. **Tradeoffs shown per page, never hidden in an aggregate.** Every
   verdict carries the full per-page before/after table (exact-pitch,
   pred notes, measures-valid, FAILs). A page that loses while others
   gain must be named, with its numbers, and adjudicated per
   `HEURISTIC_POLICY.md` (narrower gate, per-page condition, or discard).
   An aggregate-only verdict is invalid.
6. **Failed/no-output runs count as 0 and must be explained, not
   dropped.** See Definitions. If a run FAILs on a page the baseline
   passed, that is a regression under rule 1 (clean) or rule 5
   (degraded) and must name the failing Audiveris step from the log
   (e.g. SCALE, "No system found", NPE).
7. **A verdict needs before/after numbers on named pages.** No verdict
   without: baseline run id, experiment run id, the per-page table, and
   the gate condition actually measured. "Looks better" / "feels faster"
   / preflight-only improvement is not a verdict (precedent: shadow
   correction lifted preflight on 4/5 hard pages while making Audiveris
   fail on all three GT hard pages — preflight is never the score).
8. **Licence gate is a veto, not a tradeoff.** Any experiment whose
   fixtures, inputs, or outputs would put non-CC0/public-domain material
   into a PR, or any use of material the published registry excludes
   beyond local scoring, vetoes KEEP regardless of numbers.
9. **Controls must still pass.** The two canonical controls whose pages
   are in the published registry (hymn 44,105 B / `75637092…`,
   Lindenbaum 99,305 B / `dbd546ba…`) must reproduce byte-identically
   after any change that touches the pipeline. If a control moves, the
   experiment is invalid until the movement is explained — it is not a
   "small regression".
10. **Re-run before KEEP.** A KEEP verdict requires the experiment run
    to reproduce on a second run of the same configuration (same inputs,
    same harness). One lucky run is not a keep. If the second run
    disagrees by more than the rule-2 threshold, the verdict is
    UNDECIDED, not KEEP.

## Verdicts

- **KEEP** — all of rules 1–10 satisfied. Ship (gated as specified).
- **DISCARD** — any of rules 1, 4, 8 fails, or rule 2 fails with no
  per-page rescue. Record the numbers and the lesson.
- **UNDECIDED** — rule 2 is marginal (gain between +1 and +9), rule 10
  re-run disagrees, or the gate's false-positive rate is unmeasured.
  Undecided means "do more work", never "ship it and see".
