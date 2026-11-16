# Test corpus

Pages that `test/corpus.mjs` reads as the site does, and scores against their answers
(`test/score.mjs`). As the site does: the WebAssembly build the site serves, run in Node (its
output is byte for byte Chrome's), from the grey pixels the site would hand it (an image made grey
by `test/grey.py`, a PDF drawn by the site's own `app/pdf.js` in Chrome by `test/pdf-grey.mjs`),
with the words read by tesseract.js in the language a reader would pick (`languageOf` in
`test/cases.mjs`). A page with a `.json` next to it has an answer: every pitched note of every
part, by bar, with its syllable and its onset (where in the bar it starts, in quarter notes; the
rhythm column scores these). A page without one is checked only for being read, and for its part
count.

`ENGINE=desktop` reads with desktop Audiveris instead: a few times faster, with Audiveris's logs and
.omr files for finding a fault, but without the words, which also changes what it reads (the
text step can take marks for words, or words for marks). So a change is judged as the site reads.
Each engine has its baseline: `baseline.json` the site's, `baseline-desktop.json` the desktop's.

The onsets come from the MusicXML each page was drawn from: `node test/onsets.mjs <answer.json>
<source.musicxml> --write` pairs each answer note with the source's, and writes nothing unless
every bar has the same notes in both.

    node test/corpus.mjs                       # read, score, compare with baseline.json (~70 min)
    EXTRA=~/Downloads/choral-test-set node test/corpus.mjs   # also the pieces kept out of git
    HOLDOUT=only node test/corpus.mjs          # the held-out pages, to confirm a fix

Fixes are made against these pages, so they can come to fit them. `test/holdout/` has 20 more
pages, drawn at random, that no fix is made against: a fix is confirmed there once, and its
README has the rules.

**Judging a change.** The report above marks a page worse if any score drops by a point, which
catches what broke but can't weigh it: one bar fixed and one broken look the same as nothing. So
read the corpus with and without the change (`RUN=` for each; the change's WebAssembly build made
with `PATCHED=<its jar> TEAVM_WORK=.work/teavm-after teavm/build.sh` and read with `WASM=`) and
compare the two runs bar by bar:

    RUN=before node test/corpus.mjs; RUN=after WASM=.work/teavm-after/out node test/corpus.mjs
    EXTRA=... node test/compare.mjs before after   # VERBOSE=1 lists each bar that changed

It counts the bars (one answer part's bar) each run gets right, separately for sung parts and
accompaniment, and the notes missing, at the wrong time, or extra. Judge the sung parts first:
they are what a singer reads. Audiveris doesn't read every page exactly the same way twice
(between two runs of one build, the anthem p02 had one alto note at another time), so a note or
two on a page the change shouldn't touch is noise: read that page again with and without it.

Collected from 2026-11-08 for the Score Reader spikes (the "open-music" test set); the answers
come from the same MusicXML the pages were drawn from.

## What may be committed

This repository is public, so every file of music in it (a page, scan, photo, PDF, MusicXML, or
an answer made from one) is checked before it is committed, here or anywhere else in the repo.
The same goes for a pull request, whoever opens it: it names each file's source and licence, and
the reviewer checks them.

**Check the file itself**: its footer, title page or MusicXML `<rights>`, not only the site it
came from, which can list it under another licence than the file's own. Then add it to the
tables below (or the folder's README) with its source and licence.

May be committed, and only these: music that needs no permission and comes with no conditions.
- **Public domain**, the music and the edition both. A scan: an edition published before 1931
  (public domain in the US), or one IMSLP tags "Public Domain" (not "Non-PD US").
- **CC0**.
- **Our own**: pieces our tests generate, text we set, pages we draw from the above.

Everything else stays in the local test set (`EXTRA=`, below), and the repository doesn't name it
(README, notes, code, tests, commit messages): any licence with conditions, even an open one (CC BY,
CC BY-SA, CPDL's own licence, NonCommercial, NoDerivatives), "used by permission" or "for testing
only", and anything whose licence can't be found.

A private copy (a choir's own score, a scan someone shared) goes nowhere: not in git, not in the
test set. Read it from where it is.

## Pages with answers (`pages/`, `gute-nacht/`)

Drawn with Verovio from the OpenScore Lieder Corpus (github.com/OpenScore/Lieder), which is
**CC0 1.0**. The first 12 bars of each song unless noted.

| Page | Piece | OpenScore file |
|---|---|---|
| lieder-lindenbaum | Schubert, "Der Lindenbaum", Winterreise D.911 no. 5 | lc5016466 |
| lieder-gute-nacht | Schubert, "Gute Nacht", Winterreise D.911 no. 1 | lc5015378 |
| lieder-staendchen | Schubert, "Ständchen", D.957 no. 4 | lc5004835 |
| lieder-fruehling | Schubert, "Frühlingssehnsucht", D.957 no. 3 (piano introduction) | lc4985999 |
| lieder-schumann-monat-mai | Schumann, "Im wunderschönen Monat Mai", Op. 48 no. 1 | lc4976777 |
| lieder-schumann-widmung | Schumann, "Widmung", Op. 25 no. 1 | lc6885211 |
| lieder-brahms-wiegenlied | Brahms, "Wiegenlied", Op. 49 no. 4 | lc5701612 |
| lieder-faure-apres-un-reve | Fauré, "Après un rêve", Op. 7 no. 1 | lc6810863 |
| lieder-schubert-erlkoenig | Schubert, "Erlkönig", D.328, bars 13–24 | lc29062370 |
| lieder-wolf-verborgenheit | Wolf, "Verborgenheit", Mörike-Lieder no. 12 | lc29477528 |
| gute-nacht-p01 … p04 | Schubert, "Gute Nacht", the whole song on 4 pages (bars per page in each answer's `bars_global`) | lc5015378 |
| grace-staendchen | Schubert, "Ständchen", bars 13–24: grace notes (left out of the answer, as everywhere) | lc5004835 |
| octave-verborgenheit | Wolf, "Verborgenheit", bars 13–24: an 8va line over the piano (the answer has the notes as they sound) | lc29477528 |

And from the OpenScore Orchestra Corpus (github.com/MarkGotham/Hauptstimme, scores **CC0 1.0**):

| Page | Piece |
|---|---|
| orchestral-beethoven9-finale | Beethoven, Symphony No. 9, finale, bars 286–293: 36 parts, chorus and full orchestra, on one page |

## Real pages without answers (`scans/`)

From IMSLP, one page each, drawn at 300 dpi.

| Page | Piece | Source | Licence |
|---|---|---|---|
| beethoven9-p229-229 | Beethoven, Symphony No. 9, finale, p. 229 (22 staves, chorus enters) | IMSLP #516486, Breitkopf & Härtel 1864 | Public domain |
| beethoven9-typeset-p165 | Beethoven, Symphony No. 9, finale | IMSLP #929853, OpenScore typeset 2019 | CC0 |
| faure-sanctus-p50 | Fauré, Requiem Op. 48, Sanctus (choir and organ) | IMSLP #30151, Hamelle 1901 | Public domain |
| faure-agnus-p80 | Fauré, Requiem Op. 48, Agnus Dei | IMSLP #30151 | Public domain |
| mozart-kyrie-p20 | Mozart, Requiem K. 626, Kyrie | IMSLP #26746 | Public domain |
| hallelujah-imslp-p-1 | Handel, "Hallelujah", piano-reduction scan | IMSLP #12244 | Public domain |
| cantique-schoen-p02, -p09 | Fauré, Cantique de Jean Racine Op. 11, first edition (Schoen, 1876): organ introduction; choir and organ | IMSLP #26819 | Public domain |
| hymnal-am1874-p213 | Hymns Ancient and Modern, Appendix (1874), Hymn 289: a tune with 11 verses printed below it | Internet Archive `ancienthym00chur` | Public domain |

## Kept out of git

`EXTRA=<folder>` also reads pages from a local test set that can't be committed. What is in it,
and under what licence, is recorded in that folder, not here: the repository names only what it
may hold. That folder also keeps its pages' baselines (`baseline.json`, `baseline-desktop.json`,
written by `SAVE=1`) and the language of their words (`languages.json`: `[[pattern, language]]`,
read by `test/cases.mjs`). The test set has most of the SATB pages with answers, so a change to
how parts are read should be checked with `EXTRA` too.
