#!/usr/bin/env python3
"""Run desktop Audiveris 5.11 over one page image, and summarise a .mxl.

Extracted from the spike harness (`run_photo_spikes.py` in the local
workspace) so the benchmark runner does not depend on the spike tree.
Only the two functions the loop needs live here: `run_audiveris` and
`summarise_mxl`. The TrOMR / OCR / Transcoda parts of that file are
not included — this module is the desktop-Audiveris fast path only.

Audiveris + JDK come from the repo's own `./setup.sh` (`.work/`):
a Temurin JDK 25 and the Audiveris 5.11.0 release jars, whose class
path is `.work/classpath.txt` (entries are `/app/.work/lib/...` and
are rewritten to the repo root at runtime). Overrides, for a machine
whose install lives elsewhere:

  SCORE_READER_JAVA        path to the java binary
  SCORE_READER_CLASSPATH   the Audiveris class path string, or a file
                           containing it

The Audiveris constants are the desktop-harness ones (reconstructed
from `app/reader.js`): no OCR (no Tesseract in this environment, so
lyric recall is 0 by construction — an environment gap, not a result),
a 3600 s sheet timeout, no indentations, maxSlopeDiff 0.05.
"""
import glob
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))

AUD_CONSTANTS = [
    "-constant", "org.audiveris.omr.text.tesseract.TesseractOCR.useOCR=false",
    "-constant", "org.audiveris.omr.Main.sheetStepTimeOut=3600",
    "-constant", "org.audiveris.omr.sheet.ProcessingSwitches.indentations=false",
    "-constant", "org.audiveris.omr.sheet.grid.LinesRetriever.maxSlopeDiff=0.05",
]


def _find_java():
    env = os.environ.get("SCORE_READER_JAVA")
    if env:
        return env
    cands = sorted(glob.glob(os.path.join(REPO_ROOT, ".work", "jdk", "*", "bin", "java")))
    if cands:
        return cands[0]
    return None


def _read_classpath():
    env = os.environ.get("SCORE_READER_CLASSPATH")
    if env:
        if os.path.isfile(env):
            # The file's entries are "/app/.work/lib/...": /app is the
            # install root (the directory that holds .work/).
            install = os.path.dirname(os.path.dirname(env))
            return open(env).read().strip().replace("/app", install)
        return env
    cp_file = os.path.join(REPO_ROOT, ".work", "classpath.txt")
    if not os.path.isfile(cp_file):
        return None
    return open(cp_file).read().strip().replace("/app", REPO_ROOT)


def audiveris_paths():
    """(java, classpath) or raise with the fix (run ./setup.sh)."""
    java = _find_java()
    cp = _read_classpath()
    missing = []
    if not java or not os.path.isfile(java):
        missing.append("java (.work/jdk/*/bin/java)")
    if not cp:
        missing.append("class path (.work/classpath.txt)")
    if missing:
        raise RuntimeError(
            "Audiveris install not found: missing %s. Run ./setup.sh at "
            "the repo root, or set SCORE_READER_JAVA / "
            "SCORE_READER_CLASSPATH." % ", ".join(missing))
    return java, cp


def run_audiveris(png, outdir):
    """Run desktop Audiveris on one PNG. Returns (mxl_path|None, seconds, status).

    A .mxl already in the outdir is returned as cached (no re-run) —
    the runner's resume discipline. A failed run returns None with the
    exit status; the caller records it as no-output, never silently.
    """
    from score_all import load_musicxml, parse_notes, measure_validity  # noqa: F401  (import check)

    mxl = None
    for f in os.listdir(outdir) if os.path.isdir(outdir) else []:
        if f.endswith(".mxl"):
            mxl = os.path.join(outdir, f)
    if mxl:
        return mxl, 0.0, "cached"
    os.makedirs(outdir, exist_ok=True)
    java, cp = audiveris_paths()
    t0 = time.time()
    log = os.path.join(os.path.dirname(outdir), os.path.basename(outdir) + ".log")
    with open(log, "w") as lf:
        r = subprocess.run([java, "-cp", cp, "org.audiveris.omr.Main", "-batch"]
                           + AUD_CONSTANTS
                           + ["-transcribe", "-export", "-output", outdir, png],
                           stdout=lf, stderr=subprocess.STDOUT, timeout=900)
    dt = time.time() - t0
    for f in os.listdir(outdir):
        if f.endswith(".mxl"):
            return os.path.join(outdir, f), round(dt, 1), ("ok" if r.returncode == 0 else f"exit {r.returncode}")
    return None, round(dt, 1), f"no .mxl (exit {r.returncode})"


def summarise_mxl(mxl_path, beats):
    """Structural summary of one .mxl: pred notes/parts + measures-valid."""
    from score_all import load_musicxml, parse_notes, measure_validity

    root = load_musicxml(mxl_path)
    parts = parse_notes(root)
    pred_notes = [n for notes in parts.values() for n in notes if not n["rest"]]
    divs = 4
    for part in root.findall("part"):
        for meas in part.findall("measure"):
            at = meas.find("attributes/divisions")
            if at is not None:
                divs = int(at.text)
                break
        break
    valid, total, _ = 0, 0, []
    for notes in parts.values():
        v, t, b = measure_validity(notes, divisions=divs, beats=beats)
        valid += v
        total += t
    return {"pred_notes": len(pred_notes), "pred_parts": len(parts),
            "measures_valid": f"{valid}/{total}"}
