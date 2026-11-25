#!/usr/bin/env python3
"""Score a predicted MusicXML against an open-music GT json.

Same multiset metric as score_all.py, but measure validity uses the
page's real time signature (GT json 'beats'), not a hardcoded 4/4.
Usage: python3 open_score.py <pred.mxl> <gt.json>
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_all import load_musicxml, parse_notes, measure_validity  # noqa: E402


def score(pred_path, gt_path):
    gt = json.load(open(gt_path))
    beats = gt.get("beats", 4)
    root = load_musicxml(pred_path)
    pred_parts = parse_notes(root)
    gt_notes = [n for p in gt["parts"] for n in p["notes"]]
    pred_notes = [n for notes in pred_parts.values() for n in notes if not n["rest"]]

    def multiset_score(key):
        hits = 0
        g_by_bar, p_by_bar = {}, {}
        for n in gt_notes:
            g_by_bar.setdefault(n["bar"], []).append(key(n))
        for n in pred_notes:
            p_by_bar.setdefault(n["bar"], []).append(key(n))
        for bar, g in g_by_bar.items():
            hits += sum((Counter(g) & Counter(p_by_bar.get(bar, []))).values())
        return hits

    exact = multiset_score(lambda n: n["pitch"])
    pc = multiset_score(lambda n: n["pitch"][0] if n["pitch"] else None)
    typ = multiset_score(lambda n: n["type"])
    import difflib
    ratios = []
    for p in gt["parts"]:
        g_seq = [n["pitch"] for n in p["notes"]]
        best = 0.0
        for notes in pred_parts.values():
            p_seq = [n["pitch"] for n in notes if not n["rest"]]
            if p_seq:
                best = max(best, difflib.SequenceMatcher(None, g_seq, p_seq).ratio())
        ratios.append(round(best, 3))
    gt_lyr = [n["lyric"] for n in gt_notes if n["lyric"]]
    pred_lyr = [n["lyric"] for n in pred_notes if n["lyric"]]
    lyr_hits = sum((Counter(gt_lyr) & Counter(pred_lyr)).values())
    divs = 4
    for part in root.findall("part"):
        for meas in part.findall("measure"):
            at = meas.find("attributes/divisions")
            if at is not None:
                divs = int(at.text)
                break
        break
    valid, total, bad = 0, 0, []
    for notes in pred_parts.values():
        v, t, b = measure_validity(notes, divisions=divs, beats=beats)
        valid += v
        total += t
        bad += b
    return {
        "file": pred_path.split("/")[-1], "gt_notes": len(gt_notes),
        "pred_notes": len(pred_notes), "exact_pitch": exact,
        "pitch_class": pc, "note_type": typ,
        "seq_ratio_per_part": ratios,
        "lyrics": f"{lyr_hits}/{len(gt_lyr)}",
        "measures_valid": f"{valid}/{total} (beats={beats})",
        "bad_measures": bad[:10],
        "pred_parts": {k: len(v) for k, v in pred_parts.items()},
    }


if __name__ == "__main__":
    print(json.dumps(score(sys.argv[1], sys.argv[2]), indent=1))
