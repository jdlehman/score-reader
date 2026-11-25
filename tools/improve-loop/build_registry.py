#!/usr/bin/env python3
"""Build registry.json for the score-reader benchmark.

Regenerates `registry.json` from:
  - photometric/preflight-corpus-results.json (the 119-page corpus:
    preflight staves + warn per page),
  - the GT jsons under open-music/ (beats, note/lyric counts),
  - the hand-curated LICENCE / GT tables below (licence + GT mapping
    follow open-music/MANIFEST.md; nothing here embeds music data).

Writer-path pages (2) are NOT in the 119-page preflight corpus; they
are appended with preflight=None.

Licence rule — this is the published registry, so it holds only what
the repository may hold (see test/corpus/README.md, "What may be
committed"): CC0 and Public Domain, music and edition both. Any page
whose licence is anything else (a conditional licence, a testing-only
encoding, a private score) is NOT in this registry and is NOT named
here — it stays in the local test set, recorded there, not here. The
builder enforces it: an entry whose licence is not CC0 or Public
Domain is skipped, never written. The local registry (123 pages)
lives in the workspace; this file is its committable subset (44).

All paths in registry.json are relative to the corpus root — the
local test set directory that contains open-music/ and photometric/
(e.g. image "open-music/pages/lieder-lindenbaum.png").

Usage: python3 build_registry.py [--corpus DIR]
       (or set SCORE_READER_CORPUS; run from improve-loop/)
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "registry.json")

CORPUS_ROOT = None


def _corpus():
    root = CORPUS_ROOT or os.environ.get("SCORE_READER_CORPUS")
    if not root:
        raise RuntimeError(
            "no corpus root: pass --corpus or set SCORE_READER_CORPUS "
            "to the local test set (see README.md)")
    return root


def _preflight_path():
    return os.path.join(_corpus(), "photometric", "preflight-corpus-results.json")


def gt_stats(rel_gt):
    """(gt_notes, gt_lyrics, beats, gt_unpitched) from a GT json, or Nones."""
    if not rel_gt:
        return None, None, None, None
    p = os.path.join(_corpus(), rel_gt)
    if not os.path.exists(p):
        return None, None, None, None
    d = json.load(open(p))
    notes = d.get("total_notes")
    if notes is None:
        notes = sum(len(pt.get("notes", [])) for pt in d.get("parts", []))
    lyrics = d.get("total_lyrics")
    if lyrics is None:
        lyrics = sum(1 for pt in d.get("parts", [])
                     for n in pt.get("notes", []) if n.get("lyric"))
    return notes, lyrics, d.get("beats"), d.get("total_unpitched_notes")


def gt_kind_for(rel_gt, override=None):
    if override:
        return override
    if not rel_gt:
        return None
    if rel_gt.endswith("-lyrics.json"):
        return "lyrics"
    return "notes"


# ---------------------------------------------------------------- tables
# Per preflight "page" value: (id, gt rel-path or None, licence,
# local_only, tests, staves_true or None, clean_counterpart id or None
# for photo pages, base page id or None). Only CC0 / Public Domain
# pages are listed here at all — the repository does not name the
# rest, so a page that is not in these tables is skipped by the
# builder, not recorded with a different licence.

# Photo base pages: base stem -> (clean counterpart id, gt, licence, local_only, tests)
PHOTO_BASES = {
    "lieder-lindenbaum": ("onepage-lieder-lindenbaum", "open-music/pages/lieder-lindenbaum.json",
                          "CC0", False, "hard photo, tuplet-heavy voice+piano, lyrics"),
    "lieder-gute-nacht": ("onepage-lieder-gute-nacht", "open-music/pages/lieder-gute-nacht.json",
                          "CC0", False, "hard photo, clean-control voice+piano, lyrics"),
    "lieder-fruehling": ("onepage-lieder-fruehling", "open-music/pages/lieder-fruehling.json",
                         "CC0", False, "hard photo, voice+piano, piano intro (0 lyrics in bars)"),
    "lieder-staendchen": ("onepage-lieder-staendchen", "open-music/pages/lieder-staendchen.json",
                          "CC0", False, "hard photo, voice+piano, lyrics"),
    "beethoven-p229": ("scan-beethoven-p229", None,
                       "Public Domain", False, "hard photo, 22-stave orchestral scan, no GT"),
    "hallelujah-imslp-p1": ("scan-hallelujah-imslp-p1", None,
                            "Public Domain", False, "hard photo, dense old scan, no GT"),
}

# One-page rendered pages (pages/<stem>.png): stem -> (licence, local_only, tests)
ONEPAGE = {
    "lieder-brahms-wiegenlied": ("CC0", False, "voice+piano, lyrics"),
    "lieder-faure-apres-un-reve": ("CC0", False, "voice+piano, lyrics"),
    "lieder-fruehling": ("CC0", False, "voice+piano, piano intro (0 lyrics in bars)"),
    "lieder-gute-nacht": ("CC0", False, "voice+piano, lyrics, clean control"),
    "lieder-lindenbaum": ("CC0", False, "voice+piano, tuplet-heavy, lyrics"),
    "lieder-schubert-erlkoenig": ("CC0", False, "voice+piano, lyrics"),
    "lieder-schumann-monat-mai": ("CC0", False, "voice+piano, lyrics"),
    "lieder-schumann-widmung": ("CC0", False, "voice+piano, pedal marks, lyrics"),
    "lieder-staendchen": ("CC0", False, "voice+piano, lyrics"),
    "lieder-wolf-verborgenheit": ("CC0", False, "voice+piano, lyrics"),
    "orchestral-beethoven9-finale": ("CC0", False, "36-part orchestral + chorus, 735 notes"),
}

# Writer-path extras (not in the 119-page preflight corpus).
WRITER_PATHS = [
    ("writer-grace-staendchen", "writer-path", "open-music/writer-paths/grace-staendchen/grace-staendchen.png",
     "open-music/writer-paths/grace-staendchen/grace-staendchen.json", "notes", 3,
     "CC0", False, "voice+piano, 6 grace notes (writer-path feature)"),
    ("writer-octave-verborgenheit", "writer-path", "open-music/writer-paths/octave-verborgenheit/octave-verborgenheit.png",
     "open-music/writer-paths/octave-verborgenheit/octave-verborgenheit.json", "notes", 4,
     "CC0", False, "voice+piano, 8vb octave shift (writer-path feature)"),
]


def id_for_preflight(page, group):
    """Registry id from a preflight 'page' value like 'multi-page/gute-nacht/p01.png'."""
    stem = page[:-4]  # strip .png
    if group == "render-gute-nacht":
        return "gute-nacht-full-" + stem.split("/")[-1]
    if group == "render-onepage":
        return "onepage-" + stem.split("/")[-1]
    if group == "scan-hymnal":
        return "hymnal-am1874-p213"
    if group == "scan-organ":
        return "schoen-" + stem.split("-")[-1]
    if group == "scan":
        base = stem.split("/")[-1]
        return "scan-" + base.replace("beethoven9-p229-229", "beethoven-p229") \
                             .replace("beethoven9-typeset-p165", "beethoven-p165") \
                             .replace("hallelujah-imslp-p-1", "hallelujah-imslp-p1")
    if group == "photo-synthetic":
        base = stem.split("/")[-1]  # <base>-photo-<sev>
        return "photo-" + base
    return stem.replace("/", "-")


def entry_for_preflight(e):
    """One registry entry from a preflight row, or None to skip it.

    A row is skipped (never written) when it is not in the committable
    tables above — the repository does not name it. The skip is printed
    so gaps are visible in the build log, not silent.
    """
    page, group = e["page"], e["group"]
    rid = id_for_preflight(page, group)
    image = "open-music/" + page
    gt, licence, local_only, tests = None, None, False, ""
    staves_true, clean_counterpart, base_page = None, None, None
    gt_kind_override = None
    beats_override = None
    if group == "render-gute-nacht":
        gt = "open-music/multi-page/gute-nacht/%s.gt.json" % page.split("/")[-1][:-4]
        licence, tests = "CC0", "Gute Nacht full piece, voice+piano"
    elif group == "render-onepage":
        stem = page.split("/")[-1][:-4]
        if stem not in ONEPAGE:
            print("SKIP (not in published registry): %s (%s)" % (rid, page))
            return None
        gt = "open-music/pages/%s.json" % stem
        licence, local_only, tests = ONEPAGE[stem]
        if stem == "orchestral-beethoven9-finale":
            staves_true = 36
    elif group == "scan-hymnal":
        gt = "open-music/hymnal/hymnal-am1874-p213-lyrics.json"
        licence, tests = "Public Domain", "hymnal tune + 11 stanzas / 373 words (lyrics GT)"
        gt_kind_override, beats_override = "lyrics", None
        staves_true = 6
    elif group == "scan-organ":
        licence, tests = "Public Domain", "Cantique Schoen 1876 scan, SATB + organ, no aligned GT"
    elif group == "scan":
        stem = page.split("/")[-1][:-4]
        if stem == "beethoven9-p229-229":
            licence, tests, staves_true = "Public Domain", "22-stave orchestral scan, no GT", 22
        elif stem == "beethoven9-typeset-p165":
            licence, tests, staves_true = "CC0", "clean typeset orchestral + chorus, no GT", 22
        elif stem == "faure-agnus-p80":
            licence, tests = "Public Domain", "Faure Requiem Agnus, chorus + organ + orchestra, no GT"
        elif stem == "faure-sanctus-p50":
            licence, tests = "Public Domain", "Faure Requiem Sanctus, chorus + organ + orchestra, no GT"
        elif stem == "hallelujah-imslp-p-1":
            licence, tests, staves_true = "Public Domain", "dense old scan, piano reduction, no GT", 12
        elif stem == "mozart-kyrie-p20":
            licence, tests = "Public Domain", "Mozart Requiem Kyrie, chorus + orchestra, no GT"
    elif group == "photo-synthetic":
        stem = page.split("/")[-1][:-4]  # <base>-photo-<sev>
        base, sev = stem.rsplit("-photo-", 1)
        if base not in PHOTO_BASES:
            print("SKIP (not in published registry): %s (%s)" % (rid, page))
            return None
        clean_counterpart, gt, licence, local_only, tests = PHOTO_BASES[base]
        base_page = clean_counterpart
        if base == "beethoven-p229":
            staves_true = 22
        elif base == "hallelujah-imslp-p1":
            staves_true = 12
    else:
        print("SKIP (unhandled preflight group): %s (%s)" % (rid, page))
        return None
    # Licence gate (hard): only CC0 and Public Domain may be published.
    # Anything else — or an unlisted page with no licence — is skipped.
    if licence not in ("CC0", "Public Domain"):
        print("SKIP (licence not publishable): %s (%s) licence=%r" % (rid, page, licence))
        return None
    if gt is not None and not os.path.exists(os.path.join(_corpus(), gt)):
        print("WARNING: GT file missing for %s: %s" % (rid, gt))
        gt = None
    if not os.path.exists(os.path.join(_corpus(), image)):
        print("WARNING: image missing for %s: %s" % (rid, image))
    gt_notes, gt_lyrics, beats, gt_unpitched = gt_stats(gt)
    if gt_kind_override == "lyrics":
        # Hymnal lyrics GT: stanza words, counted with the SAME
        # tokenisation score.py uses (re [A-Za-z'’-]+ per line), so the
        # registry number and the scorer's denominator agree.
        import re as _re
        words = []
        d = json.load(open(os.path.join(_corpus(), gt)))
        for key in ("part_1_stanzas", "part_2_stanzas"):
            for stanza in d.get("lyrics", {}).get(key, []):
                for line in stanza:
                    words.extend(t.strip("-'’") for t in
                                 _re.findall(r"[A-Za-z'’\-]+", line.lower()))
        gt_notes, gt_lyrics = 0, len([w for w in words if w])
        beats = None
    return {
        "id": rid,
        "group": group,
        "image": image,
        "gt": gt,
        "gt_kind": gt_kind_for(gt, gt_kind_override),
        "beats": beats_override if gt_kind_override else beats,
        "licence": licence,
        "local_only": local_only,
        "tests": tests,
        "staves_preflight": e.get("staves"),
        "staves_true": staves_true,
        "preflight_warn": e.get("warn"),
        "preflight_spacing": e.get("spacing"),
        "gt_notes": gt_notes,
        "gt_lyrics": gt_lyrics,
        "gt_unpitched": gt_unpitched,
        "clean_counterpart": clean_counterpart,
        "base_page": base_page,
        "legacy_mxl": {},
    }


def legacy_mxl_for(entry):
    """Existing desktop .mxl outputs for this page (verified on disk).

    Keys are method names; values are paths relative to the spikes root.
    These are the cache the runner reuses instead of re-running Audiveris.
    """
    rid, group = entry["id"], entry["group"]
    cands = {}
    # Baseline (raw image) legacy outputs, by source.
    if group == "photo-synthetic":
        key = entry["image"].split("/")[-1][:-4]  # <base>-photo-<sev>
        p = "open-music/photo-synthetic/audiveris-out/%s/%s.mxl" % (key, key)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands["baseline"] = p
        if "baseline" not in cands:
            # tuning round (tune_aud.py --only baseline) outputs
            p0 = "photometric/audiveris-out/baseline/%s/%s.mxl" % (key, key)
            if os.path.exists(os.path.join(_corpus(), p0)):
                cands["baseline"] = p0
        p2 = "photometric/audiveris-out/median+rl/%s/%s.mxl" % (key, key)
        if os.path.exists(os.path.join(_corpus(), p2)):
            cands["deblur"] = p2
        p3 = "photometric/recovered/median+rl/%s.png" % key
        if os.path.exists(os.path.join(_corpus(), p3)):
            cands["deblur_image"] = p3
    elif rid.startswith("onepage-"):
        stem = rid[len("onepage-"):]
        # Nov-8 clean baselines (open-music/audiveris-out/<stem>/)
        d = os.path.join(_corpus(), "open-music/audiveris-out", stem)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".mxl"):
                    cands["baseline"] = "open-music/audiveris-out/%s/%s" % (stem, f)
        # full-out92 desktop
        p = "open-music/wasm92/%s/desktop/%s.mxl" % (stem, stem)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands.setdefault("baseline", p)
        # photometric clean baselines (staendchen / fruehling)
        p = "photometric/audiveris-out/baseline-clean/%s-clean/%s.mxl" % (stem, stem)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands.setdefault("baseline", p)
        # full-out110 desktop (orchestral finale)
        p = "open-music/wasm110/%s/desktop/%s.mxl" % (stem, stem)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands.setdefault("baseline", p)
    elif rid.startswith("scan-"):
        stem = {"scan-beethoven-p229": "beethoven-p229",
                "scan-hallelujah-imslp-p1": "hallelujah-imslp-p1"}.get(rid)
        if stem:
            d = os.path.join(_corpus(), "open-music/audiveris-out", stem)
            if os.path.isdir(d):
                for f in sorted(os.listdir(d)):
                    if f.endswith(".mxl"):
                        cands["baseline"] = "open-music/audiveris-out/%s/%s" % (stem, f)
    elif rid.startswith("gute-nacht-full-"):
        pnn = rid[len("gute-nacht-full-"):]
        p = "open-music/multi-page/gute-nacht/desktop/%s/%s.mxl" % (pnn, pnn)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands["baseline"] = p
    elif rid == "hymnal-am1874-p213":
        p = "open-music/wasm110/hymnal-am1874-p213/desktop/hymnal-am1874-p213.mxl"
        if os.path.exists(os.path.join(_corpus(), p)):
            cands["baseline"] = p
    elif rid.startswith("schoen-"):
        p = "open-music/wasm110/cantique-%s/desktop/cantique-%s.mxl" % (rid, rid)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands["baseline"] = p
    elif rid.startswith("writer-"):
        stem = rid[len("writer-"):]
        p = "open-music/wasm110/%s/desktop/%s.mxl" % (stem, stem)
        if os.path.exists(os.path.join(_corpus(), p)):
            cands["baseline"] = p
    return cands


def main():
    global CORPUS_ROOT
    ap = argparse.ArgumentParser(description="Build registry.json "
                                 "(CC0 / Public Domain pages only)")
    ap.add_argument("--corpus", default=None,
                    help="corpus root (page images + ground truth); "
                         "or set SCORE_READER_CORPUS")
    a = ap.parse_args()
    if a.corpus:
        CORPUS_ROOT = a.corpus
    elif os.environ.get("SCORE_READER_CORPUS"):
        CORPUS_ROOT = os.environ["SCORE_READER_CORPUS"]
    if not CORPUS_ROOT or not os.path.isdir(CORPUS_ROOT):
        print("no corpus root: pass --corpus <dir> or set "
              "SCORE_READER_CORPUS to the local test set", file=sys.stderr)
        return 2
    pre = json.load(open(_preflight_path()))
    pages = []
    n_skipped = 0
    for e in pre:
        entry = entry_for_preflight(e)
        if entry is None:
            n_skipped += 1
            continue
        entry["legacy_mxl"] = legacy_mxl_for(entry)
        pages.append(entry)
    # Writer-path extras (not in the preflight corpus).
    for (rid, group, image, gt, gt_kind, beats, licence, local_only, tests) in WRITER_PATHS:
        gt_notes, gt_lyrics, _b, gt_unpitched = gt_stats(gt)
        entry = {
            "id": rid, "group": group, "image": image, "gt": gt,
            "gt_kind": gt_kind, "beats": beats, "licence": licence,
            "local_only": local_only, "tests": tests,
            "staves_preflight": None, "staves_true": None,
            "preflight_warn": None, "preflight_spacing": None,
            "gt_notes": gt_notes, "gt_lyrics": gt_lyrics,
            "gt_unpitched": gt_unpitched,
            "clean_counterpart": None, "base_page": None,
            "legacy_mxl": {},
        }
        entry["legacy_mxl"] = legacy_mxl_for(entry)
        pages.append(entry)

    by_id = {p["id"]: p for p in pages}
    assert len(by_id) == len(pages), "duplicate registry ids"

    def ids(pred):
        return [p["id"] for p in pages if pred(p)]

    photo_hard = ids(lambda p: p["group"] == "photo-synthetic" and p["id"].endswith("-hard"))
    clean_of_hard = [by_id[p["clean_counterpart"]]["id"] for p in pages
                     if p["id"] in photo_hard]
    subsets = {
        "default": photo_hard + clean_of_hard,
        "photo-hard": photo_hard,
        "photo-mild": ids(lambda p: p["group"] == "photo-synthetic" and p["id"].endswith("-mild")),
        "photo-moderate": ids(lambda p: p["group"] == "photo-synthetic" and p["id"].endswith("-moderate")),
        "photo-all": ids(lambda p: p["group"] == "photo-synthetic"),
        "onepage": ids(lambda p: p["group"] == "render-onepage"),
        "gute-nacht": ids(lambda p: p["group"] == "render-gute-nacht"),
        "scans": ids(lambda p: p["group"] in ("scan", "scan-hymnal", "scan-organ")),
        "writer": ids(lambda p: p["group"] == "writer-path"),
        "clean": ids(lambda p: not p["local_only"]),
        "all": [p["id"] for p in pages],
    }
    subsets = {k: v for k, v in subsets.items() if v}
    reg = {
        "version": 1,
        "generated": "2026-11-25",
        "corpus_root": "open-music/",
        "path_base": "All paths are relative to the corpus root — the "
                     "local test set directory that contains open-music/ "
                     "and photometric/. Registry holds paths + metadata "
                     "only — no embedded music data.",
        "licence_rule": "Published registry: CC0 and Public Domain only "
                        "(music and edition both). Pages under any other "
                        "licence, a testing-only encoding, or a private "
                        "score are not in this registry and are not named "
                        "here; they stay in the local test set. "
                        "--clean-only is therefore a no-op on this "
                        "registry (kept as a safety net).",
        "preflight_source": "photometric/preflight-corpus-results.json (119 pages; "
                            "44 kept, %d skipped as not publishable)" % n_skipped,
        "counts": {
            "pages": len(pages),
            "preflight_corpus": len(pre),
            "writer_path_extras": len(WRITER_PATHS),
            "local_only": sum(1 for p in pages if p["local_only"]),
            "licence_clean": sum(1 for p in pages if not p["local_only"]),
            "with_gt_notes": sum(1 for p in pages if p["gt_kind"] == "notes"),
            "with_gt_lyrics": sum(1 for p in pages if p["gt_kind"] == "lyrics"),
            "with_gt_unpitched": sum(1 for p in pages if p["gt_kind"] == "unpitched"),
            "gt_null_structural_only": sum(1 for p in pages if p["gt"] is None),
            "with_legacy_baseline_mxl": sum(1 for p in pages if "baseline" in p["legacy_mxl"]),
            "with_legacy_deblur_mxl": sum(1 for p in pages if "deblur" in p["legacy_mxl"]),
        },
        "subsets": subsets,
        "pages": pages,
    }
    json.dump(reg, open(OUT, "w"), indent=1)
    print("wrote %s: %d pages (%d preflight kept, %d skipped, +%d writer-path), "
          "%d local-only, %d licence-clean" % (
              OUT, len(pages), len(pre) - n_skipped, n_skipped,
              len(WRITER_PATHS),
              reg["counts"]["local_only"], reg["counts"]["licence_clean"]))
    for name, s in subsets.items():
        print("  subset %-14s %d pages" % (name, len(s)))


if __name__ == "__main__":
    main()
