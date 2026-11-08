# Test fixtures — open music

Small, downscaled copies of the open-music test pages used by the spike harness, so the
tests run without the full-size pages. Ground truth is unchanged: the same `.json` scores
every variant of a page. Full-size pages, sources and the complete manifest live in the
spike workspace (`score-reader-spikes/open-music/`); these are only the small forms the
tests need.

## Pages

- `hallelujah-clean.jpg` — Handel, "Hallelujah" from Messiah HWV 56, p. 1, SATB, bars
  1–14. Downscaled to 1000 px wide from `open-music/pages/hallelujah-satb.png`.
  Licence: **CC BY-NC-SA 4.0** (printed in the PDF footer; CPDL #36487, ed. Jes Wagner).
  Preflight on this file: 12 staves, confidence 0.774, no warning.
- `hallelujah-photo-hard.jpg` — the same page with synthetic phone-photo defects applied
  (perspective warp 6% of page size, tilt 2.21 deg, shadow depth 0.45, blur 1.8 px, noise
  sigma 10, contrast 0.85; generator `make_photo_pages.py`, seed 20261310). Downscaled to
  1000 px wide from `open-music/photo-synthetic/hallelujah-satb-photo-hard.png`.
  Same licence as the source page. Preflight on this file: 0 staves, warns.
- `hallelujah-satb.json`, `lieder-lindenbaum.json`, `lieder-gute-nacht.json` — ground truth
  (notes and lyrics) for the three rendered open pages, copied from `open-music/pages/`.
  Lindenbaum and Gute Nacht are Schubert, Winterreise D.911, OpenScore Lieder Corpus,
  **CC0**.

## What is NOT here, and why

- No full-size pages (several MB each) and no Beethoven / IMSLP scans: the unit tests draw
  their own pages, and the e2e tests use only the two Hallelujah files above. The Beethoven
  orchestral scan is qualitative-only (no aligned MusicXML) and is not a fixture.
- No DeepScores data: it is symbol-detection data (135 classes, no lyrics, no MusicXML),
  not page-level ground truth for this app.
