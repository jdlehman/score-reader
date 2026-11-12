// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// The Audiveris settings Score Reader reads with. The page (reader.js, Audiveris in WebAssembly) and
// the corpus test (test/corpus.mjs, desktop Audiveris) both use these, so the test reads as the page does.

/** Settings for how Audiveris reads music, the same in the browser and on the desktop. */
export const READING = [
  // one piece, one score: Audiveris starts a new movement at each indented system, and hymnals indent many
  'org.audiveris.omr.sheet.ProcessingSwitches.indentations=false',
  // staff lines may tilt more against the page, and bend more: scans of a book and photos warp
  // it, and Audiveris dropped such lines, or kept only their straight part (see NOTES.md)
  'org.audiveris.omr.sheet.grid.LinesRetriever.maxSlopeDiff=0.1',
  'org.audiveris.omr.sheet.grid.LinesRetriever.maxFilamentRotation=0.2',
  // a staff may be 15 staff spaces long, not 30: a last system of one short bar is shorter than
  // 30, and Audiveris dropped it whole (Erlkönig, Ständchen)
  'org.audiveris.omr.sheet.grid.LinesRetriever.minStaffLength=15',
]

/** As desktop Audiveris's command line wants them (the corpus test): -constant name=value, each. */
export const asArgs = constants => constants.flatMap(c => ['-constant', c])
