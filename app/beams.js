// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A beamed chord's beams on its first note only. Audiveris writes a chord's <beam> elements on
// every note of the chord; Verovio, which draws the score after a read and in Sectional, then
// loses the notes of the beamed group ("Adding 'beam' to a 'chord'"), most of a bar in a piano
// part. Its other notes follow the first, as most programs write it. No DOM: the same code runs
// in the page and in Node.

/** The MusicXML with no <beam> on a note marked <chord/> (the chord's first note keeps its beams). */
export function beamsOnChordHeads(xml) {
  return xml.replace(/<note\b[^>]*>[\s\S]*?<\/note>/g, note => (/<chord\s*\/>/.test(note) ? note.replace(/\s*<beam\b[^>]*>[^<]*<\/beam>/g, '') : note))
}
