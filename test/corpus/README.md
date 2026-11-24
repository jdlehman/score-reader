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

    node test/corpus.mjs                       # read, score, compare with baseline.json (over an hour)
    EXTRA=~/Downloads/choral-test-set node test/corpus.mjs   # also the pieces kept out of git
    HOLDOUT=only node test/corpus.mjs          # the held-out pages, to confirm a fix

Fixes are made against these pages, so they can come to fit them. `test/holdout/` has 20 more
pages, drawn at random, that no fix is made against: a fix is confirmed there once, and its
README has the rules.

## Proving a change

A change goes in when `test/prove.mjs` says it is better: ours, or one in a pull request. The
report above marks a page worse if any score drops by a point, which catches what broke but can't
weigh it (one bar fixed and one broken look the same as nothing). `prove.mjs` reads the corpus
with the change and with main, compares them bar by bar, and gives a verdict by the rule below.

    PATCHED=<its jar> TEAVM_WORK=.work/teavm-x teavm/build.sh          # the change's build
    EXTRA=... node test/prove.mjs x --wasm .work/teavm-x/out           # read, compare, verdict
    EXTRA=... node test/prove.mjs x --wasm .work/teavm-x/out --holdout # then once, to confirm

A change that isn't in the build says so instead: `--constants a=1,b=2` (Audiveris settings),
`--pre <module>` (a step on the grey pages before the read), `--post <module>` (a step on the
MusicXML after it); `teavm/node/read.mjs` describes the modules. Main's reads are kept and read
again only when main's build or the reading code changes, so a verdict costs one read of the
corpus (about two hours with `EXTRA`). `--main <dir>` names main's build if it isn't
`.work/teavm/out`. The verdict is kept in `.work/corpus/verdicts/<name>.txt`, and
`node test/compare.mjs` lists the bars that changed (`VERBOSE=1`).

**What it counts.** A bar is one answer part's bar, as its singer or player reads it, in the read
part paired with it; it is right when every note is there, starting on time, with nothing extra.
Sung parts (lyrics or a voice's name) and accompaniment are counted apart. The measures, after
minus before: sung bars right, accompaniment bars right, notes right (there and starting on time),
extra notes, syllables found, pages read, and reading time. Notes missing and at the wrong time
are shown but not judged apart: a note can only be at the wrong time once it is found, so a change
that finds notes puts some there, and a note found at the wrong time is no worse than one missed.

**Noise.** `node test/prove.mjs repeat` (no change named) reads main a second time. If two reads
of one build differ on a page, that page is allowed that much difference in later verdicts (kept
in `.work/corpus/noise.json`); until the check has run, every difference counts. Run it again when
main's build changes. A page read by one side only is read again, alone, before it counts (a busy
machine can time a read out).

**The rule**, on the pages fixes are made against:
- **PROVED**: at least one measure better, and nothing worse: no measure worse in total, and no
  page with fewer sung or accompaniment bars right, fewer syllables, more note errors, or not read
  any more (each beyond its noise).
- **TRADE-OFF**: better in some measure, worse in another or on some page. A person decides,
  after looking at those bars, and says why in the commit.
- **NOT PROVED**: nothing better; or fewer sung bars right in total; or a page that was read no
  longer is.

Then the held-out pages, once (`--holdout`): only their totals are shown, and which pages moved.
Anything worse there in total makes the verdict NOT PROVED. Each use is logged, and a second look
at the same change is warned of (`test/holdout/README.md` has the rules).

Reading time only counts against a change, past +20%: main's reads are kept from another day,
when the machine may have been busier, so a faster change is timed on its own, both builds back to
back. A step outside the read that the corpus can't run (one needing the page's interface) isn't
proved here: measure what it costs and gains some other way, and say how in its pull request.

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

## Real scans with answers (`real/`)

Pages of IMSLP scans of old printed editions, each cut out as a one-page PDF (so the page reads
it as it would an uploaded PDF), with an answer from the OpenScore Lieder Corpus (**CC0 1.0**): each
of these songs was copied into OpenScore from this very scan (OpenScore's `data/scores.yaml` names
the IMSLP file), so its MusicXML, cut at the scan's page breaks, is the page's answer. The bars on
each page were read off the scan; OpenScore's MusicXML breaks its pages where MuseScore laid them
out, which isn't where the edition did. `real/build.mjs` writes the answers with `test/answer.mjs`
(and, given the IMSLP files, cuts the pages; `real/cut.swift` says how exactly a cut page matches
the original).

Next to the drawn pages of the same songs (`pages/`, `gute-nacht/`), these show what a real scan
costs: the same music, printed by engravers in the 1870s-1920s and scanned.
`real/drawn-vs-scan.mjs <run> <run>` compares the two over the bars the drawn pages hold.
Measured 2026-11-16 with the site's build: over those bars, notes 100% drawn and 92% scanned,
rhythm 98% and 78%. The 21 scan pages on their own: notes 87%, rhythm 60%, words about half. The
Fauré (a 2400-pixel-wide scan of an 1878 print) reads worst, 57-74% of notes; Erlkönig and
Lindenbaum keep their notes but lose rhythm in their piano triplets.

| Pages | Piece | Bars on each page | Scan (IMSLP file, PDF pages) | Edition | Licence |
|---|---|---|---|---|---|
| lieder-schubert-gute-nacht-p1 … p4 | Schubert, "Gute Nacht", Winterreise D.911 no. 1 (OpenScore lc5015378) | 1-18, 19-50, 51-77, 78-105 | #60822, pp. 6-9 | Schubert's Werke XX/9, Breitkopf & Härtel 1895 | Public domain |
| lieder-schubert-lindenbaum-p1 … p4 | Schubert, "Der Lindenbaum", D.911 no. 5 (lc5016466) | 1-24, 25-45, 46-62, 63-82 | #60822, pp. 20-23 | as above | Public domain |
| lieder-schumann-widmung-p1, p2 | Schumann, "Widmung", Myrthen Op. 25 no. 1 (lc6885211) | 1-18, 19-44 | #270905, pp. 1-2 | Robert Schumann's Werke XIII, Breitkopf & Härtel, issued 1887 | Public domain |
| lieder-brahms-wiegenlied-p1 | Brahms, "Wiegenlied", Op. 49 no. 4 (lc5701612) | 1-19 | #81909, p. 10 | Brahms, Sämtliche Werke 24, Breitkopf & Härtel 1926-27 | Public domain |
| lieder-faure-apres-un-reve-p1 … p4 | Fauré, "Après un rêve", Op. 7 no. 1 (lc6810863) | 1-11, 12-23, 24-35, 36-48 | #24047, pp. 1-4 | J. Hamelle, Paris, ca. 1878 (first edition) | Public domain |
| lieder-schubert-erlkoenig-p1 … p6 | Schubert, "Erlkönig", D.328, 4th version (lc29062370) | 1-23, 24-53, 54-75, 76-96, 97-122, 123-148 | #15041, pp. 1-6 | Schubert's Werke XX/3, Breitkopf & Härtel 1895 (scanned from a Kalmus reprint) | Public domain |

Each scan's IMSLP entry is tagged "Public Domain", and each edition is dated on the scan or by
IMSLP before 1931. The songs' words are by poets who died in the 19th century (Müller, Rückert,
Scherer, Bussine, Goethe).

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
how parts are read should be checked with `EXTRA` too. Its `holdout/` folder is held out like
`test/holdout`.
