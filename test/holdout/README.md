# Held-out pages

Twenty pages that no change to the reader has been made against, so a fix can be checked on music
it wasn't fitted to. Every fix so far started from a page in `test/corpus` that showed the bug,
and was then measured on that same corpus. A fix can look good there and only work on those
pages. These pages are the check.

**Rules**
- Don't make or tune a fix while looking at these pages: not their reads, their per-page scores,
  or their images. Make the fix on `test/corpus` (and `EXTRA`), then run these once to confirm it.
- Report their totals, and how many pages got better or worse. If one got worse, look at that page
  to understand why, then either drop the fix or change it on general grounds and run them all
  again. Once a page has been looked at closely it stops being held out; say so in the commit, and
  add fresh pages (below) from time to time.
- Nothing here is picked by hand. `songs.txt` is a seeded random draw from the corpus, and
  `build.mjs` takes the first 20 songs that build, in that order, skipping one only for a reason it
  prints (it can't be drawn, its parts disagree, no notes).

The local test set (`EXTRA`) can hold out pages of its own the same way, in its `holdout/` folder:
they are left out of every run unless `HOLDOUT` is set, and the same rules apply.

**Run**

    HOLDOUT=only RUN=holdout node test/corpus.mjs     # just these
    HOLDOUT=1 node test/corpus.mjs                   # with the rest

**What they are**

Songs from the OpenScore Lieder Corpus (github.com/OpenScore/Lieder, **CC0 1.0**), each one's
first 12 bars (fewer when 12 don't fit on one page), drawn by Verovio as an A4 page at 300 dpi.
The answers come from the same cut MusicXML, with onsets, as in `test/corpus`. Built 2026-11-13
with Verovio 6.3.0 by `node test/holdout/build.mjs` (needs `rsvg-convert` and Python with PIL;
the sources are cached in `.work/holdout-src`). Each answer's `source` names its file.

To add fresh pages, draw more songs the same way (another seed, leaving out every song already
used), build them, and add them here. Don't swap out a page because the reader does badly on it.
