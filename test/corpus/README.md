# Test corpus

Pages that `test/corpus.mjs` reads with desktop Audiveris (patched and set up as the page reads)
and scores against their answers (`test/score.mjs`). A page with a `.json` next to it has an
answer: every pitched note of every part, by bar, with its syllable and its onset (where in the
bar it starts, in quarter notes; the rhythm column scores these). A page without one is checked
only for being read, and for its part count.

The onsets come from the MusicXML each page was drawn from: `node test/onsets.mjs <answer.json>
<source.musicxml> --write` pairs each answer note with the source's, and writes nothing unless
every bar has the same notes in both.

    node test/corpus.mjs                       # read, score, compare with baseline.json
    EXTRA=~/Downloads/choral-test-set node test/corpus.mjs   # also the pieces kept out of git

Only music that anyone may copy is here. Collected on 2026-11-08 and 2026-11-10 for the
Score Reader spikes (the "open-music" test set); the answers come from the same MusicXML the
pages were drawn from.

## Pages with answers (`pages/`, `gute-nacht/`)

Drawn with Verovio from the OpenScore Lieder Corpus (github.com/OpenScore/Lieder), which is
**CC0 1.0**. The first 12 bars of each song unless noted.

| Page | Piece | OpenScore file |
|---|---|---|
| lieder-lindenbaum | Schubert, "Der Lindenbaum", Winterreise D.911 no. 5 | lc5016466 |
| lieder-gute-nacht | Schubert, "Gute Nacht", Winterreise D.911 no. 1 | lc5015378 |
| lieder-staendchen | Schubert, "Ständchen", D.957 no. 4 | |
| lieder-fruehling | Schubert, "Frühlingssehnsucht", D.957 no. 3 (piano introduction) | |
| lieder-schumann-monat-mai | Schumann, "Im wunderschönen Monat Mai", Op. 48 no. 1 | lc4976777 |
| lieder-schumann-widmung | Schumann, "Widmung", Op. 25 no. 1 | lc6885211 |
| lieder-brahms-wiegenlied | Brahms, "Wiegenlied", Op. 49 no. 4 | lc5701612 |
| lieder-faure-apres-un-reve | Fauré, "Après un rêve", Op. 7 no. 1 | lc6810863 |
| lieder-schubert-erlkoenig | Schubert, "Erlkönig", D.328, bars 13–24 | lc29062370 |
| lieder-wolf-verborgenheit | Wolf, "Verborgenheit", Mörike-Lieder no. 12 | lc29477528 |
| gute-nacht-p01 … p04 | Schubert, "Gute Nacht", the whole song on 4 pages (bars per page in each answer's `bars_global`) | lc5015378 |
| grace-staendchen | Schubert, "Ständchen", bars 13–24: grace notes (left out of the answer, as everywhere) | |
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

The test set has more, which can't be copied freely; `EXTRA=<folder>` reads them from a local
copy. Bach chorales and BWV 227 pages (music in the public domain, but the encodings are
"PDF © 2004 Margaret Greentree, used by permission", for testing only); Handel's "Hallelujah"
from cafe-puccini.dk (CC BY-NC-SA 4.0); BWV 227 from CPDL #42494 (CC BY-NC); Mendelssohn, "Hör
mein Bitten" (CC BY-NC-SA 4.0); Fauré's Cantique de Jean Racine, the whole piece on 13 pages
with answers (Skinner 2022, Choral Public Domain Library License); Foster's "Jeanie" with chord
names and a drum page (music21's corpus, for testing). These are the SATB pages with answers, so a change to how parts
are read should be checked with `EXTRA` too. The test set's synthetic phone photos are left out
for size (about 4 MB each).
