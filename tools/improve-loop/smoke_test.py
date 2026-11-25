#!/usr/bin/env python3
"""Smoke test for the loop's scorer: score a synthetic page and assert
the numbers. No Audiveris, no corpus, no network — stdlib only.

The fixture is synthetic (written for this test, no real music): a
two-part, two-bar page whose prediction has one wrong pitch and one
wrong lyric, so the expected scores are below the GT totals:

  GT 7 notes / 3 lyrics; pred 12 notes.
  exact_pitch 6/7 (bar 1 voice D4 read as E4), pitch_class 6,
  note_type 7, lyrics 2/3 (bar 2 voice "lo" not "la"),
  measures_valid 4/4 (every bar/voice sums to 4 beats).

Also covers the two failure paths: a missing .mxl is recorded as
no-output with 0.0 recalls (never silently dropped), and a gt:null
page scores structural metrics only.

Run: python3 smoke_test.py   (exit 0 = pass, prints the numbers)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from score import score_page  # noqa: E402


def check(name, got, want):
    if got != want:
        print("FAIL %s: got %r, want %r" % (name, got, want))
        return False
    print("ok   %s = %r" % (name, got))
    return True


def main():
    mxl = os.path.join(HERE, "fixtures", "smoke", "pred.musicxml")
    entry = {"id": "smoke-synthetic", "group": "smoke",
             "gt": "fixtures/smoke/gt.json", "gt_kind": "notes",
             "beats": 4, "gt_notes": 7, "gt_lyrics": 3}
    m = score_page(mxl, entry, corpus_root=HERE)
    ok = True
    ok &= check("status", m["status"], "ok")
    ok &= check("scored", m["scored"], True)
    ok &= check("exact_pitch", m["exact_pitch"], 6)
    ok &= check("gt_notes", m["gt_notes"], 7)
    ok &= check("pred_notes", m["pred_notes"], 12)
    ok &= check("exact_recall", m["exact_recall"], round(6 / 7, 4))
    ok &= check("pitch_class", m["pitch_class"], 6)
    ok &= check("note_type", m["note_type"], 7)
    ok &= check("lyric_hits", m["lyric_hits"], 2)
    ok &= check("lyric_total", m["lyric_total"], 3)
    ok &= check("measures_valid", m["measures_valid"], 4)
    ok &= check("measures_total", m["measures_total"], 4)
    ratio = m["seq_ratio_mean"]
    if ratio is None or not (0 < ratio < 1):
        print("FAIL seq_ratio_mean: got %r, want a float in (0, 1)" % ratio)
        ok = False
    else:
        print("ok   seq_ratio_mean = %r (in (0, 1))" % ratio)

    # Missing .mxl: recorded as no-output with 0.0 recalls.
    m2 = score_page(os.path.join(HERE, "fixtures", "smoke", "nope.mxl"),
                    entry, corpus_root=HERE)
    ok &= check("no-output status", m2["status"], "no-output")
    ok &= check("no-output exact_recall", m2["exact_recall"], 0.0)
    ok &= check("no-output validity_rate", m2["validity_rate"], 0.0)

    # gt:null page: structural metrics only.
    entry_null = {"id": "smoke-structural", "group": "smoke",
                  "gt": None, "gt_kind": None, "beats": 4}
    m3 = score_page(mxl, entry_null, corpus_root=HERE)
    ok &= check("structural status", m3["status"], "ok")
    ok &= check("structural measures_valid", m3["measures_valid"], 4)
    ok &= check("structural exact_recall", m3["exact_recall"], None)

    print("SMOKE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
