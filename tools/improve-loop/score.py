#!/usr/bin/env python3
"""Scorer for the score-reader benchmark (improve-loop/).

Wraps `open_score.score` (imported, not copied) and adds:
  - per-page metrics: exact note hits vs GT, pitch recall, duration-valid
    bar pairs, lyric recall where the GT has lyrics;
  - structural-only metrics for gt:null pages (pred notes/parts,
    duration-valid measures, crash/no-output status);
  - aggregates (mean/median per group) and a per-page baseline-vs-method
    comparison table that shows tradeoffs per page, never only an aggregate.

Failed / no-output runs are recorded as 0 with status, never silently
dropped. Pages that cannot be scored in this VM are recorded as
unscored with the reason.

Comparison rule: inters/notes are compared by content, never by id
offset — inherited from open_score/score_all, which score by per-bar
multisets of pitch/type.

Usage:
  score.py <run.json> [--baseline <baseline-run.json>]
      Print aggregates for <run.json>; with --baseline, also print the
      per-page comparison table and improved/regressed counts.
  score.py --mxl <path.mxl> --page <registry-id> [--corpus DIR]
      Score one .mxl against the registry entry's GT; print JSON.
  score.py --rescore <run.json> [--corpus DIR]
      Re-score a run file from its recorded .mxl (no Audiveris re-run).

The corpus root (page images + ground truth) comes from --corpus or
the SCORE_READER_CORPUS environment variable; it is only needed when
a page has ground truth to score against.
"""
import json
import os
import re
import statistics
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from open_score import score as open_score  # noqa: E402
from audiveris import summarise_mxl  # noqa: E402
from score_all import load_musicxml, parse_notes  # noqa: E402

CORPUS_ROOT = None  # set by a caller (run.py) or --corpus / SCORE_READER_CORPUS


def _corpus(corpus_root=None):
    root = corpus_root or CORPUS_ROOT or os.environ.get("SCORE_READER_CORPUS")
    if not root:
        raise RuntimeError(
            "no corpus root: pass --corpus or set SCORE_READER_CORPUS "
            "to the local test set (see README.md)")
    return root


def _resolve_mxl(p, corpus_root=None):
    """Resolve a .mxl path stored in a run file (absolute, or relative
    to the repo root or the corpus root) to an absolute path."""
    if not p:
        return None
    if os.path.isabs(p):
        return p
    for base in (REPO_ROOT, None):
        if base is None:
            try:
                base = corpus_root or _corpus()
            except RuntimeError:
                break
        cand = os.path.join(base, p)
        if os.path.exists(cand):
            return cand
    return os.path.join(REPO_ROOT, p)


def load_registry(path=None):
    path = path or os.path.join(HERE, "registry.json")
    reg = json.load(open(path))
    return {p["id"]: p for p in reg["pages"]}, reg


def _parse_frac(s):
    """'23/41' or '23/41 (beats=3)' -> (23, 41). None on garbage."""
    if s is None:
        return None, None
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", str(s))
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def _rate(num, den):
    return round(num / den, 4) if den else None


def _structural(mxl_path, beats):
    """Structural metrics only — no GT needed."""
    beats = beats if beats else 4
    s = summarise_mxl(mxl_path, beats)
    valid, total = _parse_frac(s.get("measures_valid"))
    return {
        "pred_notes": s.get("pred_notes"),
        "pred_parts": s.get("pred_parts"),
        "measures_valid": valid,
        "measures_total": total,
        "validity_rate": _rate(valid, total) if valid is not None else None,
        "beats_assumed": beats,
    }


def _lyric_word_recall(mxl_path, gt_path):
    """Hymnal-style lyrics GT: multiset word recall vs stanza words."""
    gt = json.load(open(gt_path))
    words = []
    lyr = gt.get("lyrics", {})
    for key in ("part_1_stanzas", "part_2_stanzas"):
        for stanza in lyr.get(key, []):
            for line in stanza:
                for tok in re.findall(r"[A-Za-z'’\-]+", line.lower()):
                    words.append(tok.strip("-'’"))
    words = [w for w in words if w]
    root = load_musicxml(mxl_path)
    parts = parse_notes(root)
    pred = [n["lyric"].lower() for notes in parts.values() for n in notes
            if n.get("lyric")]
    pred_toks = []
    for t in pred:
        pred_toks.extend(re.findall(r"[a-z'’\-]+", t))
    from collections import Counter
    hits = sum((Counter(words) & Counter(pred_toks)).values())
    return {"lyric_words_gt": len(words), "lyric_word_hits": hits,
            "lyric_word_recall": _rate(hits, len(words))}


def _feature_counts(mxl_path):
    """Writer-path feature check: unpitched notes, percussion clef,
    measure-repeat presence in the output MusicXML."""
    if mxl_path.endswith(".mxl"):
        with zipfile.ZipFile(mxl_path) as z:
            names = [n for n in z.namelist()
                     if n.endswith(".xml") and not n.startswith("META-INF")]
            data = z.read(names[0])
        root = ET.fromstring(data)
    else:
        root = ET.parse(mxl_path).getroot()
    unpitched = len(root.findall(".//note/unpitched"))
    clefs = [c.findtext("sign") for c in root.findall(".//clef")]
    repeats = len(root.findall(".//measure-style/measure-repeat"))
    return {"pred_unpitched": unpitched,
            "pred_percussion_clef": "percussion" in clefs,
            "pred_measure_repeat": repeats}


def score_page(mxl_path, entry, corpus_root=None):
    """Score one Audiveris output against one registry entry.

    Returns a metrics dict. Always returns a dict — never raises for a
    bad/missing .mxl; those become status no-output / unscored.
    `corpus_root` is the corpus root (page images + ground truth); it
    defaults to --corpus / SCORE_READER_CORPUS via _corpus().
    """
    out = {"page": entry["id"], "group": entry["group"],
           "gt_kind": entry.get("gt_kind"), "gt_notes": entry.get("gt_notes"),
           "scored": False, "status": "unscored", "reason": None,
           "pred_notes": 0, "pred_parts": 0,
           "exact_pitch": 0, "exact_recall": None,
           "pitch_class": 0, "pitch_recall": None,
           "note_type": None, "seq_ratio_mean": None,
           "lyric_hits": None, "lyric_total": None, "lyric_recall": None,
           "measures_valid": 0, "measures_total": 0, "validity_rate": None}
    if not mxl_path or not os.path.exists(mxl_path):
        out["status"] = "no-output"
        out["reason"] = "no .mxl produced by Audiveris"
        # Recorded as 0 with status (never silently dropped): a page
        # that produced nothing recalls 0 of its GT and validates 0
        # measures. gt:null pages keep exact_recall None (no GT to
        # recall against); the status field distinguishes "0 hits"
        # from "no output".
        if entry.get("gt_notes"):
            out["exact_recall"] = 0.0
            out["pitch_recall"] = 0.0
        if entry.get("gt_lyrics"):
            out["lyric_recall"] = 0.0
        out["validity_rate"] = 0.0
        return out
    out["mxl"] = mxl_path
    gt_kind = entry.get("gt_kind")
    try:
        gt_path = os.path.join(_corpus(corpus_root), entry["gt"]) if entry.get("gt") else None
    except Exception as e:  # noqa: BLE001 — no corpus root: unscored, not a crash
        out["status"] = "unscored"
        out["reason"] = "%s: %s" % (type(e).__name__, e)
        return out
    try:
        if gt_kind == "notes":
            s = open_score(mxl_path, gt_path)
            out.update(_structural(mxl_path, entry.get("beats")))
            out["exact_pitch"] = s.get("exact_pitch", 0)
            out["pitch_class"] = s.get("pitch_class", 0)
            out["note_type"] = s.get("note_type")
            out["pred_notes"] = s.get("pred_notes", out["pred_notes"])
            gt_n = s.get("gt_notes") or entry.get("gt_notes") or 0
            out["gt_notes"] = gt_n
            out["exact_recall"] = _rate(s.get("exact_pitch", 0), gt_n)
            out["pitch_recall"] = _rate(s.get("pitch_class", 0), gt_n)
            ratios = s.get("seq_ratio_per_part") or []
            out["seq_ratio_mean"] = (round(sum(ratios) / len(ratios), 3)
                                     if ratios else None)
            lh, lt = _parse_frac(s.get("lyrics"))
            out["lyric_hits"], out["lyric_total"] = lh, lt
            out["lyric_recall"] = _rate(lh, lt) if lt else None
            out["scored"] = True
            out["status"] = "ok"
        elif gt_kind == "lyrics":
            # Hymnal: stanza-word recall + structural metrics.
            out.update(_structural(mxl_path, entry.get("beats")))
            out.update(_lyric_word_recall(mxl_path, gt_path))
            out["lyric_total"] = out.pop("lyric_words_gt")
            out["lyric_hits"] = out.pop("lyric_word_hits")
            out["lyric_recall"] = out.pop("lyric_word_recall")
            out["scored"] = True
            out["status"] = "ok"
        elif gt_kind == "unpitched":
            # Drums: pitch scoring does not apply; structural + features.
            out.update(_structural(mxl_path, entry.get("beats")))
            out.update(_feature_counts(mxl_path))
            out["gt_unpitched"] = entry.get("gt_unpitched")
            out["scored"] = True
            out["status"] = "ok"
        else:  # gt null — structural metrics only
            out.update(_structural(mxl_path, entry.get("beats")))
            out["scored"] = True
            out["status"] = "ok"
    except Exception as e:  # noqa: BLE001 — record, never crash the run
        out["status"] = "unscored"
        out["reason"] = "%s: %s" % (type(e).__name__, e)
    return out


# ---------------------------------------------------------------- aggregates
def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 4) if xs else None


def aggregate(results):
    """results: {page_id: per-page dict incl. metrics}. -> per-group table."""
    groups = {}
    for pid, r in results.items():
        m = r.get("metrics") or {}
        g = groups.setdefault(r.get("group", "?"), {
            "n": 0, "ok": 0, "no_output": 0, "unscored": 0,
            "exact_recall": [], "pitch_recall": [], "validity_rate": [],
            "lyric_recall": []})
        g["n"] += 1
        st = r.get("status", m.get("status", "?"))
        if st == "ok":
            g["ok"] += 1
        elif st == "no-output":
            g["no_output"] += 1
        else:
            g["unscored"] += 1
        # Collect every non-None metric value. No-output pages carry
        # explicit 0.0 recalls (see score_page), so failures count as
        # zeros in the mean; genuinely unscored pages carry None and
        # are excluded by the _mean/_median filters.
        for key in ("exact_recall", "pitch_recall", "validity_rate",
                    "lyric_recall"):
            if m.get(key) is not None:
                g[key].append(m[key])
    rows = []
    for gname in sorted(groups):
        g = groups[gname]
        rows.append({
            "group": gname, "n": g["n"], "ok": g["ok"],
            "no_output": g["no_output"], "unscored": g["unscored"],
            "exact_recall_mean": _mean(g["exact_recall"]),
            "exact_recall_median": _median(g["exact_recall"]),
            "pitch_recall_mean": _mean(g["pitch_recall"]),
            "validity_rate_mean": _mean(g["validity_rate"]),
            "validity_rate_median": _median(g["validity_rate"]),
            "lyric_recall_mean": _mean(g["lyric_recall"]),
            "gt_pages_scored": len(g["exact_recall"]),
        })
    return rows


def compare(baseline, method, exact_delta=0.01, validity_delta=0.02):
    """Per-page baseline-vs-method table + improved/regressed counts.

    Verdict is per page, on exact recall where GT exists, else on
    validity rate. A page is 'improved' / 'regressed' only past the
    thresholds; anything inside is 'unchanged'. Pages where either side
    is no-output / unscored are listed as such, never dropped.
    """
    rows, improved, regressed, unchanged, incomparable = [], 0, 0, 0, 0
    ids = sorted(set(baseline) | set(method))
    for pid in ids:
        b = (baseline.get(pid) or {}).get("metrics") or {}
        m = (method.get(pid) or {}).get("metrics") or {}
        b_st = (baseline.get(pid) or {}).get("status")
        m_st = (method.get(pid) or {}).get("status")
        row = {"page": pid,
               "group": (method.get(pid) or baseline.get(pid) or {}).get("group"),
               "baseline_status": b_st, "method_status": m_st,
               "baseline_exact_recall": b.get("exact_recall"),
               "method_exact_recall": m.get("exact_recall"),
               "exact_recall_delta": None,
               "baseline_validity": b.get("validity_rate"),
               "method_validity": m.get("validity_rate"),
               "validity_delta": None, "verdict": "incomparable"}
        if b.get("exact_recall") is not None and m.get("exact_recall") is not None:
            d = round(m["exact_recall"] - b["exact_recall"], 4)
            row["exact_recall_delta"] = d
            row["verdict"] = ("improved" if d > exact_delta else
                              "regressed" if d < -exact_delta else "unchanged")
        elif b.get("validity_rate") is not None and m.get("validity_rate") is not None:
            d = round(m["validity_rate"] - b["validity_rate"], 4)
            row["validity_delta"] = d
            row["verdict"] = ("improved" if d > validity_delta else
                              "regressed" if d < -validity_delta else "unchanged")
        else:
            incomparable += 1
        if row["verdict"] == "improved":
            improved += 1
        elif row["verdict"] == "regressed":
            regressed += 1
        elif row["verdict"] == "unchanged":
            unchanged += 1
        rows.append(row)
    return rows, {"improved": improved, "regressed": regressed,
                  "unchanged": unchanged, "incomparable": incomparable,
                  "pages": len(rows)}


# ---------------------------------------------------------------- CLI
def _print_aggregates(run):
    print("run %s  method=%s  subset=%s  clean_only=%s  pages=%d" % (
        run.get("run_id"), run.get("method"), run.get("subset"),
        run.get("clean_only"), len(run.get("results", {}))))
    rows = aggregate(run["results"])
    print("%-18s %3s %3s %4s %4s | %6s %6s %6s | %6s %6s | %6s %3s" % (
        "group", "n", "ok", "noout", "unsc", "exMean", "exMed",
        "pitchM", "valMean", "valMed", "lyrMean", "gtN"))
    for r in rows:
        f = lambda v: ("%.3f" % v) if v is not None else "  -   "
        print("%-18s %3d %3d %4d %4d | %6s %6s %6s | %6s %6s | %6s %3d" % (
            r["group"], r["n"], r["ok"], r["no_output"], r["unscored"],
            f(r["exact_recall_mean"]), f(r["exact_recall_median"]),
            f(r["pitch_recall_mean"]), f(r["validity_rate_mean"]),
            f(r["validity_rate_median"]), f(r["lyric_recall_mean"]),
            r["gt_pages_scored"]))


def _print_comparison(base_run, run):
    rows, counts = compare(base_run["results"], run["results"])
    print("\nbaseline %s (%s) vs %s (%s): %s" % (
        base_run.get("run_id"), base_run.get("method"),
        run.get("run_id"), run.get("method"), counts))
    print("%-38s %-6s %-6s %7s | %-6s %-6s %7s | %s" % (
        "page", "bExRec", "mExRec", "delta", "bValid", "mValid", "delta",
        "verdict"))
    for r in rows:
        f = lambda v: ("%.3f" % v) if v is not None else "  -   "
        d = r["exact_recall_delta"] if r["exact_recall_delta"] is not None \
            else r["validity_delta"]
        print("%-38s %-6s %-6s %7s | %-6s %-6s %7s | %s%s" % (
            r["page"], f(r["baseline_exact_recall"]), f(r["method_exact_recall"]),
            ("%.3f" % d) if d is not None else "  -    ",
            f(r["baseline_validity"]), f(r["method_validity"]),
            ("%.3f" % r["validity_delta"]) if r["validity_delta"] is not None else "  -    ",
            r["verdict"],
            "" if r["method_status"] == "ok" else "  [%s]" % r["method_status"]))


def main(argv):
    corpus = None
    if "--corpus" in argv:
        corpus = argv[argv.index("--corpus") + 1]
        argv = [a for a in argv if a != "--corpus" and a != corpus]
    if len(argv) >= 2 and argv[0] == "--rescore":
        # Re-score every page of an existing run file from its recorded
        # .mxl (no Audiveris re-run). Use after scorer changes.
        path = argv[1]
        run = json.load(open(path))
        by_id, _ = load_registry()
        n = 0
        for pid, r in run["results"].items():
            mxl = _resolve_mxl(r["mxl"], corpus) if r.get("mxl") else None
            r["metrics"] = score_page(mxl, by_id[pid], corpus_root=corpus)
            n += 1
        json.dump(run, open(path, "w"), indent=1)
        print("rescored %d pages in %s" % (n, path))
        return 0
    if len(argv) >= 2 and argv[0] == "--mxl":
        mxl = argv[1]
        page = argv[argv.index("--page") + 1]
        by_id, _ = load_registry()
        if page not in by_id:
            print("unknown registry page: %s" % page, file=sys.stderr)
            return 2
        print(json.dumps(score_page(mxl, by_id[page], corpus_root=corpus), indent=1))
        return 0
    if len(argv) < 1:
        print(__doc__)
        return 2
    run = json.load(open(argv[0]))
    _print_aggregates(run)
    if "--baseline" in argv:
        base = json.load(open(argv[argv.index("--baseline") + 1]))
        _print_comparison(base, run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
