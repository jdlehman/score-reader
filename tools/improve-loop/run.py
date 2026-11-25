#!/usr/bin/env python3
"""Benchmark runner for the score-reader self-improvement loop.

Runs desktop Audiveris 5.11 over registry pages, scores each output
with score.py, and writes one results file per run to runs/<run-id>.json.

Resumable / cached (same discipline as photometric/tune_aud.py): a job
whose outdir already holds a .mxl is recorded as cached (re-scored from
the .mxl, no re-run); a failed job (no .mxl) is re-attempted on the next
pass. Legacy .mxl outputs recorded in registry.json `legacy_mxl` are
copied into the run outdir on first use and marked cached_from — never
re-run what already exists. --force re-runs everything.

Methods (small registry — add a variant by adding one entry):
  baseline  raw image through Audiveris (no preprocessing).
  deblur    3x3 median -> Richardson-Lucy sigma=1.8, 15 iters
            (photometric/recover.py `median+rl`, the shipped config),
            then Audiveris.
  rl        Richardson-Lucy sigma=1.8, 15 iters only, then Audiveris.

Default subset is `default`: the 6 synthetic hard photos + their 6
clean counterparts (12 pages). Most reuse cached .mxl (see the
registry's `legacy_mxl`); the rest need a fresh Audiveris run
(~35-110 s/page), so the default run takes roughly 5-15 minutes wall
clock. The full `all` subset (44 pages) is hours — do not run it as
one job; shard with --only.

Usage:
  run.py [--subset NAME] [--only PAGE ...] [--clean-only] [--force]
         [--method METHOD] [--run-id ID] [--corpus DIR]
         [--list-subsets] [--list-methods]
  run.py --subset photo-hard --method deblur
  run.py --only onepage-lieder-lindenbaum --force

The corpus (page images + ground truth + legacy .mxl) lives outside
the repo, in the local test set: pass its root with --corpus or the
SCORE_READER_CORPUS environment variable (see README.md). Audiveris
and the JDK come from the repo's own ./setup.sh (.work/); overrides
SCORE_READER_JAVA / SCORE_READER_CLASSPATH. Deblur preprocessing
runs the vendored recover.py with the current Python; if that Python
lacks cv2/scipy, point SCORE_READER_PHOTO_PY at a venv Python that
has them (see requirements.txt).
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from audiveris import run_audiveris  # noqa: E402
from score import score_page  # noqa: E402

REGISTRY = os.path.join(HERE, "registry.json")
OUTDIR_ROOT = os.path.join(HERE, "audiveris-out")
RECOVERED_ROOT = os.path.join(HERE, "recovered")
RUNS_ROOT = os.path.join(HERE, "runs")
RECOVER_PY = os.path.join(HERE, "recover.py")

CORPUS_ROOT = None  # set by main() from --corpus / SCORE_READER_CORPUS


def _corpus():
    root = CORPUS_ROOT or os.environ.get("SCORE_READER_CORPUS")
    if not root:
        raise RuntimeError(
            "no corpus root: pass --corpus or set SCORE_READER_CORPUS "
            "to the local test set (see README.md)")
    return root


def _display_path(p):
    """Store a path relative to the repo root (or corpus root) when possible."""
    if not os.path.isabs(p):
        return p
    for base in (REPO_ROOT, _corpus()):
        try:
            rel = os.path.relpath(p, base)
        except ValueError:
            continue
        if not rel.startswith(".."):
            return rel
    return p


def _resolve_display(p):
    """Resolve a path stored by _display_path back to an absolute path."""
    if os.path.isabs(p):
        return p
    for base in (REPO_ROOT, os.environ.get("SCORE_READER_CORPUS") or ""):
        if not base:
            continue
        cand = os.path.join(base, p)
        if os.path.exists(cand):
            return cand
    return os.path.join(REPO_ROOT, p)

# method -> recover.py method name (None = no preprocessing)
METHODS = {
    "baseline": {"preprocess": None,
                 "desc": "raw image through Audiveris 5.11 desktop"},
    "deblur": {"preprocess": "median+rl",
               "desc": "3x3 median -> Richardson-Lucy sigma=1.8, 15 iters, then Audiveris"},
    "rl": {"preprocess": "rl",
           "desc": "Richardson-Lucy sigma=1.8, 15 iters only, then Audiveris"},
}


def load_registry():
    reg = json.load(open(REGISTRY))
    return reg, {p["id"]: p for p in reg["pages"]}


def find_mxl(outdir):
    if not os.path.isdir(outdir):
        return None
    for f in sorted(os.listdir(outdir)):
        if f.endswith(".mxl"):
            return os.path.join(outdir, f)
    return None


def env_note():
    java_v = "unknown (run ./setup.sh at the repo root)"
    try:
        from audiveris import audiveris_paths
        java, _cp = audiveris_paths()
        r = subprocess.run([java, "-version"], capture_output=True,
                           text=True, timeout=30)
        java_v = (r.stderr or r.stdout).strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        pass
    return {
        "hostname": socket.gethostname(),
        "audiveris": "5.11 desktop (stock, no-OCR constants from "
                     "audiveris.py: TesseractOCR.useOCR=false)",
        "java": java_v,
        "python": sys.version.split()[0],
        "note": "Desktop harness only — this is the fast path. The final "
                "check is a manual in-browser Wasm build run (see "
                "BENCHMARK.md); nothing here claims Wasm parity.",
    }


def preprocess_image(method, entry, page_id):
    """Return the png Audiveris should read for this method.

    For deblur: reuse the legacy recovered image if the registry has
    one, else reuse this run's recovered image, else generate it with
    recover.py under the photo venv (seconds per page).
    """
    spec = METHODS[method]
    src = os.path.join(_corpus(), entry["image"])
    if spec["preprocess"] is None:
        return src, None
    dst = os.path.join(RECOVERED_ROOT, method, page_id + ".png")
    if os.path.exists(dst):
        return dst, {"recovered": "cached",
                     "path": _display_path(dst)}
    legacy_img = entry.get("legacy_mxl", {}).get("deblur_image")
    if method == "deblur" and legacy_img:
        leg = os.path.join(_corpus(), legacy_img)
        if os.path.exists(leg):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(leg, dst)
            return dst, {"recovered": "legacy-copy", "path": legacy_img}
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    t0 = time.time()
    photo_py = os.environ.get("SCORE_READER_PHOTO_PY") or sys.executable
    r = subprocess.run([photo_py, RECOVER_PY, spec["preprocess"], src, dst],
                       capture_output=True, text=True, timeout=600)
    if not os.path.exists(dst):
        raise RuntimeError("recover.py %s failed for %s: %s" % (
            spec["preprocess"], page_id, (r.stderr or r.stdout)[-500:]))
    return dst, {"recovered": "generated",
                 "path": _display_path(dst),
                 "seconds": round(time.time() - t0, 1)}


def run_one(method, entry, force):
    page_id = entry["id"]
    outdir = os.path.join(OUTDIR_ROOT, method, page_id)
    result = {"page": page_id, "group": entry["group"],
              "gt_kind": entry.get("gt_kind"),
              "status": "error", "cached": False, "cached_from": None,
              "seconds": 0.0, "mxl": None, "metrics": None,
              "preprocess": None}
    try:
        png, prep = preprocess_image(method, entry, page_id)
        result["preprocess"] = prep
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = "%s: %s" % (type(e).__name__, e)
        return result
    if force:
        old = find_mxl(outdir)
        if old:
            os.remove(old)
    elif find_mxl(outdir) is None:
        # Legacy cache: copy the recorded .mxl into this run's outdir.
        legacy = entry.get("legacy_mxl", {}).get(method)
        if legacy:
            leg = os.path.join(_corpus(), legacy)
            if os.path.exists(leg):
                os.makedirs(outdir, exist_ok=True)
                shutil.copyfile(leg, os.path.join(outdir, os.path.basename(leg)))
                result["cached_from"] = legacy
    try:
        mxl, secs, status = run_audiveris(png, outdir)
    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Audiveris timed out (900 s)"
        return result
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = "%s: %s" % (type(e).__name__, e)
        return result
    result["seconds"] = secs
    result["cached"] = (status == "cached")
    if mxl:
        result["status"] = "ok"
        result["mxl"] = _display_path(mxl)
    else:
        result["status"] = "no-output"
        result["error"] = status
    result["metrics"] = score_page(mxl, entry, corpus_root=_corpus())
    # score_page's own status is the scoring verdict; keep the run
    # status (ok/no-output) as the outer status.
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--subset", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--clean-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--method", default="baseline", choices=list(METHODS))
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--corpus", default=None,
                    help="corpus root (page images + ground truth); "
                         "or set SCORE_READER_CORPUS")
    ap.add_argument("--list-subsets", action="store_true")
    ap.add_argument("--list-methods", action="store_true")
    a = ap.parse_args(argv)

    global CORPUS_ROOT
    if a.corpus:
        CORPUS_ROOT = a.corpus
    elif os.environ.get("SCORE_READER_CORPUS"):
        CORPUS_ROOT = os.environ["SCORE_READER_CORPUS"]
    if not CORPUS_ROOT or not os.path.isdir(CORPUS_ROOT):
        print("no corpus root: pass --corpus <dir> or set "
              "SCORE_READER_CORPUS to the local test set (see README.md)",
              file=sys.stderr)
        return 2

    reg, by_id = load_registry()
    if a.list_subsets:
        for name, ids in reg["subsets"].items():
            print("%-14s %3d pages" % (name, len(ids)))
        return 0
    if a.list_methods:
        for name, spec in METHODS.items():
            print("%-10s %s" % (name, spec["desc"]))
        return 0
    if a.method not in METHODS:
        print("unknown method: %s" % a.method, file=sys.stderr)
        return 2

    if a.only:
        wanted = []
        for pid in a.only:
            if pid not in by_id:
                print("unknown registry page: %s" % pid, file=sys.stderr)
                return 2
            wanted.append(pid)
        subset_name = "only:" + ",".join(wanted)
    else:
        subset_name = a.subset or "default"
        if subset_name not in reg["subsets"]:
            print("unknown subset: %s (see --list-subsets)" % subset_name,
                  file=sys.stderr)
            return 2
        wanted = list(reg["subsets"][subset_name])
    if a.clean_only:
        wanted = [p for p in wanted if not by_id[p]["local_only"]]
        subset_name += "+clean-only"

    ts = time.strftime("%Y%m%d-%H%M%S")
    run_id = a.run_id or "%s-%s" % (ts, a.method)
    run_path = os.path.join(RUNS_ROOT, run_id + ".json")
    os.makedirs(RUNS_ROOT, exist_ok=True)
    run = {"run_id": run_id, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "method": a.method, "method_desc": METHODS[a.method]["desc"],
           "subset": subset_name, "clean_only": a.clean_only,
           "pages_requested": wanted, "environment": env_note(),
           "results": {}}
    if os.path.exists(run_path) and not a.force:
        prev = json.load(open(run_path))
        if prev.get("method") == a.method:
            run["results"] = prev.get("results", {})
            print("resuming %s (%d pages already recorded)" % (
                run_id, len(run["results"])))

    t0 = time.time()
    n_fresh = n_cached = n_noout = 0
    for pid in wanted:
        entry = by_id[pid]
        # Skip only if this exact run already recorded the page AND its
        # .mxl still exists (resume); --force re-runs regardless.
        prev = run["results"].get(pid)
        if prev and not a.force and prev.get("mxl") and os.path.exists(
                _resolve_display(prev["mxl"])):
            print("[%s] already in run, kept (%s)" % (pid, prev["status"]),
                  flush=True)
            continue
        r = run_one(a.method, entry, a.force)
        run["results"][pid] = r
        json.dump(run, open(run_path, "w"), indent=1)
        if r["cached"]:
            n_cached += 1
        elif r["status"] == "ok":
            n_fresh += 1
        if r["status"] == "no-output":
            n_noout += 1
        m = r["metrics"] or {}
        print("[%s] %s %s %.1fs cached=%s exact=%s/%s valid=%s/%s" % (
            pid, r["status"], r.get("error", "") if r["status"] != "ok" else "",
            r["seconds"], r["cached"],
            m.get("exact_pitch"), m.get("gt_notes"),
            m.get("measures_valid"), m.get("measures_total")), flush=True)
    run["summary"] = {
        "pages": len(run["results"]),
        "ok": sum(1 for r in run["results"].values() if r["status"] == "ok"),
        "no_output": sum(1 for r in run["results"].values()
                         if r["status"] == "no-output"),
        "error": sum(1 for r in run["results"].values()
                     if r["status"] == "error"),
        "cached": sum(1 for r in run["results"].values() if r.get("cached")),
        "fresh_runs_this_invocation": n_fresh,
        "cached_this_invocation": n_cached,
        "wall_seconds": round(time.time() - t0, 1),
    }
    json.dump(run, open(run_path, "w"), indent=1)
    print("DONE %s: %s (%.1fs) -> %s" % (
        run_id, run["summary"], time.time() - t0,
        _display_path(run_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
