#!/usr/bin/env python3
"""Unified scorer: compare any MusicXML (.musicxml or .mxl zip) against the
ground-truth JSON for a test page.

Metrics, per part and pooled:
  - multiset exact-pitch / pitch-class / note-type hits per bar
  - ordered pitch-sequence similarity (difflib ratio) per part
  - measure-duration validity: summed durations per measure/voice vs 4/4
  - lyric coverage: % of GT lyric syllables present with same text
"""
import difflib
import glob
import json
import re
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = {"whole": 4.0, "half": 2.0, "quarter": 1.0, "eighth": 0.5,
       "16th": 0.25, "breve": 8.0, "long": 16.0}


def load_musicxml(path):
    if path.endswith(".mxl"):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist()
                     if n.endswith(".xml") and not n.startswith("META-INF")]
            data = z.read(names[0])
        root = ET.fromstring(data)
    else:
        root = ET.parse(path).getroot()
    return root


def parse_notes(root):
    """-> {part_id: [ {bar, pitch, type, voice, lyric, dur} ]} in score order."""
    parts = {}
    for part in root.findall("part"):
        pid = part.get("id")
        notes = []
        for meas in part.findall("measure"):
            bar = int(re.sub(r"[^0-9]", "", meas.get("number", "0")) or 0)  # "7a" split bars -> 7
            for n in meas.findall("note"):
                pitch = n.find("pitch")
                typ = n.find("type")
                dur_el = n.find("duration")
                divs = None
                # divisions from first measure attributes of this part
                notes.append({
                    "bar": bar,
                    "pitch": (pitch.find("step").text + pitch.find("octave").text)
                    if pitch is not None else None,
                    "type": typ.text if typ is not None else None,
                    "voice": int(n.find("voice").text) if n.find("voice") is not None else 1,
                    "lyric": (n.find("lyric/text").text
                              if n.find("lyric/text") is not None else None),
                    "rest": n.find("rest") is not None,
                    "chord": n.find("chord") is not None,
                    "duration": int(dur_el.text) if dur_el is not None else None,
                })
        parts[pid] = notes
    return parts


def measure_validity(notes, divisions=4, beats=4):
    """Per (bar, voice): summed quarter-note durations vs expected.
    Returns (valid_measures, total_measures, bad list)."""
    from collections import defaultdict
    sums = defaultdict(float)
    for n in notes:
        if n["duration"] is None:
            continue
        q = n["duration"] / divisions
        # chord tones don't advance time
        if not n["chord"]:
            sums[(n["bar"], n["voice"])] += q
    bad = [(k, round(v, 2)) for k, v in sorted(sums.items())
           if abs(v - beats) > 0.01]
    return len(sums) - len(bad), len(sums), bad


def score_file(path, gt_path):
    gt = json.load(open(gt_path))
    root = load_musicxml(path)
    pred_parts = parse_notes(root)
    gt_notes = [n for p in gt["parts"] for n in p["notes"]]
    pred_notes = [n for notes in pred_parts.values() for n in notes
                  if not n["rest"]]
    # multiset per bar (pooled)
    from collections import Counter
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
    # ordered sequence similarity per part (pitch sequence, rests excluded)
    ratios = []
    for p in gt["parts"]:
        g_seq = [n["pitch"] for n in p["notes"]]
        # predicted part with the most notes (TrOMR/Audiveris part ids differ)
        best = 0.0
        for notes in pred_parts.values():
            p_seq = [n["pitch"] for n in notes if not n["rest"]]
            if p_seq:
                best = max(best, difflib.SequenceMatcher(None, g_seq, p_seq).ratio())
        ratios.append(round(best, 3))
    # lyrics
    gt_lyr = [n["lyric"] for n in gt_notes if n["lyric"]]
    pred_lyr = [n["lyric"] for n in pred_notes if n["lyric"]]
    lyr_hits = sum((Counter(gt_lyr) & Counter(pred_lyr)).values())
    # measure validity (use divisions from file: find first divisions)
    divs = 4
    for part in root.findall("part"):
        for meas in part.findall("measure"):
            at = meas.find("attributes/divisions")
            if at is not None:
                divs = int(at.text)
                break
        break
    valid, total, bad = (0, 0, [])
    for notes in pred_parts.values():
        v, t, b = measure_validity(notes, divisions=divs)
        valid += v
        total += t
        bad += b
    return {
        "file": os.path.basename(path),
        "gt_notes": len(gt_notes), "pred_notes": len(pred_notes),
        "exact_pitch": exact, "pitch_class": pc, "note_type": typ,
        "seq_ratio_per_part": ratios,
        "lyrics": f"{lyr_hits}/{len(gt_lyr)}",
        "measures_valid": f"{valid}/{total}",
        "bad_measures": bad[:8],
    }


if __name__ == "__main__":
    for path, gt in [(a, b) for a, b in zip(sys.argv[1::2], sys.argv[2::2])]:
        print(json.dumps(score_file(path, gt), indent=1))
