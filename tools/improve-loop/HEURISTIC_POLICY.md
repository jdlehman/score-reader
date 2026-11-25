# Heuristic policy — when heuristics apply in the score-reader loop

A heuristic is a conditional transformation or decision applied before or
inside the pipeline (e.g. deblur, denoise, a PSF/iteration choice, a
staff-count rule). This policy governs when one may run, what happens
when its inputs are missing or it fails, and how a heuristic that helps
one page and hurts another is adjudicated.

## 1. Gates

- **Every heuristic ships gated.** The gate is a condition computable
  from the input page *before* the heuristic runs, using only signals
  already available at that point in the pipeline (preflight warn,
  image statistics, page metadata). The gate must be stated as a
  predicate, e.g. `preflight warn == 'no-staves'`, not as a vibe
  ("blurry-looking pages").
- **The gate must be measured, not assumed.** Before a gated heuristic
  ships, report: (a) how many corpus pages the gate fires on, broken
  down by clean / mild / moderate / hard / real-scan; (b) the
  false-positive rate on clean pages (must be 0 — see VERDICT_RULES
  rule 1; a gate that fires on any clean page is not shippable until
  narrowed); (c) which pages the gate *misses* that the heuristic
  would have helped (precedent: the shipped `no-staves` gate fires on
  6/11 hard synthetic pages; Lindenbaum hard — the page deblur helps
  most — does not flag, because 2 staves are found in a typical strip).
  A gate with known misses ships with the misses on record, not hidden.
- **The gate's input is itself untrusted where documented.**
  Preflight staff *counts* undercount on dense pages (Beethoven p229:
  22 found for a 36-part page) and the warn decision does not use the
  count. Never gate on the raw staff count. Gate on the warn value, or
  on a count threshold that has itself been validated against the
  corpus (the median-staves ≤ 3 widening proposal is exactly this kind
  of validation, and it is still undecided — it does not ship by
  analogy).
- **No gate may depend on a signal that does not predict the outcome.**
  Preflight confidence does not predict Audiveris output (shadow
  correction lifts preflight while killing Audiveris). A gate built on
  a non-predictive signal is not a gate.

## 2. Conditions and fallbacks

- **Missing gate input → heuristic does not run.** If the preflight (or
  whatever the gate reads) cannot be computed — missing image, corrupt
  grey, preflight crash — the page takes the unmodified path. A missing
  gate input must never default to "run the heuristic".
- **Heuristic failure must never lose a page.** If the heuristic throws,
  returns an empty/corrupt image, or times out, the pipeline falls back
  to the original input and continues. Precedent: PR #7's deblur has a
  per-page try/catch plus a module-load fallback — a deblur failure
  degrades to "no deblur", never to "no page". Any new heuristic must
  have the same shape: try heuristic → on any failure, original input →
  log the fallback. A heuristic whose failure mode is a lost page is
  not shippable.
- **Timeouts are failures.** A heuristic that does not return within its
  stated budget (record the budget in the experiment entry) is treated
  as a failure and falls back, not retried silently.
- **The fallback path must itself be tested.** At least one experiment
  run must exercise the fallback (e.g. force the heuristic to throw on
  one page) and show the page still produces its baseline output.

## 3. Adjudicating help-one-page / hurt-another

When a heuristic helps page A and hurts page B, in this order:

1. **Show the per-page table.** No adjudication without exact-pitch,
   pred notes, and measures-valid before/after for both pages (and all
   other pages in the set). Aggregates do not adjudicate.
2. **Apply the no-clean-regression rule.** If B is a clean page
   (VERDICT_RULES definition), the heuristic as-gated is DISCARD. No
   amount of gain on A overrides a clean-page regression. The only
   way forward is a narrower gate that excludes B.
3. **If B is a degraded page**, ask whether a narrower gate or a
   per-page condition separates A from B:
   - **Narrower gate:** tighten the predicate so it fires on A and not
     B (e.g. `no-staves` → `no-staves` plus a blur/contrast condition),
     then re-measure the gate's fire/miss rates on the whole corpus.
     The narrowed gate is a new experiment, with its own entry.
   - **Per-page condition:** if A and B differ on a measurable input
     property (severity, staff spacing, page class), condition the
     heuristic on that property. The condition must be stated, measured,
     and itself gated — it is a second gate, subject to §1.
   - **Discard:** if no measurable condition separates A from B, or the
     separation only works on the two pages in front of you (overfit to
     n=2), DISCARD. A heuristic that cannot tell its winners from its
     losers in advance is not a heuristic; it is a coin flip with extra
     steps.
4. **What happens to the losing pages.** They are recorded by name in
   the experiment entry with their before/after numbers, and in
   `LESSONS.md` if the loss teaches something general. They are not
   dropped from the table, not averaged away, and not re-run until they
   pass. If a narrowed gate later rescues them, that is a new
   experiment entry, not an edit to the old one.
5. **Rescue-path heuristics get a stricter bar, not a looser one.**
   A heuristic that only runs where Audiveris would otherwise give up
   (the deblur pattern) may accept losses on pages that were already
   FAILing at baseline — there is nothing to lose there — but it may
   not turn a producing page into a FAIL. "It was already broken" is
   only a defence for pages that were FAIL at baseline.

## 4. What does not count as a heuristic

- A parameter change with no condition (e.g. "always run RL 5
  iterations") is not a gated heuristic; it is a pipeline change and
  is judged by VERDICT_RULES directly. Precedent: ungated RL 5 was
  NO-GO precisely because it had no gate.
- A dual-path ("run both, keep the better") is not available without
  Audiveris in the loop to judge, and Audiveris output is the thing
  being optimised — there is no cheap judge. Do not propose dual-path
  without naming the judge and its cost.
