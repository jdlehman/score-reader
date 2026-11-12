// @jdlehman/score-view 0.1.0, built from midi_studio commit 98675ad (packages/score-view) by
// Score Reader's update-score-view.sh. Change it there, not here. Its licence:
//
// The MIT License (MIT)
//
// Copyright (c) 2026 Jonathan Lehman
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

//#region ../midi_studio/packages/score-view/src/musicxml.ts
const STEP_PC = {
	C: 0,
	D: 2,
	E: 4,
	F: 5,
	G: 7,
	A: 9,
	B: 11
};
const DYNAMICS = {
	pppp: 25,
	ppp: 32,
	pp: 42,
	p: 55,
	mp: 68,
	mf: 82,
	f: 96,
	ff: 108,
	fff: 118,
	ffff: 124,
	sf: 100,
	sfz: 100,
	fp: 96
};
const DEFAULT_VELOCITY = 80;
const kids$2 = (el, name) => Array.from(el.children).filter((c) => c.tagName === name);
const kid$2 = (el, name) => el ? Array.from(el.children).find((c) => c.tagName === name) ?? null : null;
const text = (el, name) => kid$2(el, name)?.textContent?.trim() ?? null;
const num$2 = (s, fallback) => {
	const n = s == null ? NaN : Number(s);
	return Number.isFinite(n) ? n : fallback;
};
const KEYBOARD = /piano|pno|organ|org\.|keyboard|kbd|harp|accomp|guitar|rehearsal|reduction|celest|harpsichord/i;
const VOCAL = /sop|alto|tenor|bass|bari|choir|chorus|voice|vox|satb|women|men\b|treble|mezzo|contralto|cantus|vocal|solo|^[SATB]{1,4}\.?$/i;
const VOICE_NAMES = {
	S: "Soprano",
	A: "Alto",
	T: "Tenor",
	B: "Bass"
};
/** General MIDI programs (1-based, as MusicXML writes them) for the instruments a choir score has. */
const PROGRAMS = {
	1: "acoustic_grand_piano",
	2: "bright_acoustic_piano",
	5: "electric_piano_1",
	7: "harpsichord",
	20: "church_organ",
	17: "drawbar_organ",
	25: "acoustic_guitar_nylon",
	26: "acoustic_guitar_steel",
	41: "violin",
	42: "viola",
	43: "cello",
	44: "contrabass",
	47: "orchestral_harp",
	57: "trumpet",
	61: "french_horn",
	58: "trombone",
	74: "flute",
	69: "oboe",
	72: "clarinet",
	71: "bassoon"
};
const VOCAL_PROGRAMS = /* @__PURE__ */ new Set([
	53,
	54,
	55
]);
/** The written pitch of a `<pitch>` element, as MIDI. */
function pitchOf(p) {
	const step = (text(p, "step") ?? "C").toUpperCase();
	const octave = num$2(text(p, "octave"), 4);
	return {
		midi: (octave + 1) * 12 + (STEP_PC[step] ?? 0) + Math.round(num$2(text(p, "alter"), 0)),
		step,
		octave
	};
}
/** The numbers of a volta: "1", "1, 2" or "1 2". */
const endingNumbers = (s) => (s ?? "1").split(/[\s,.]+/).map(Number).filter((n) => Number.isFinite(n) && n > 0);
/**
* Name each line of a part split by voice: from the part's name if it names them ("Soprano Alto",
* "S/A", "TB", or "SopranoAlto" as a score reader can run them together).
*/
function voiceNames(partName, count, vocal) {
	const split = (name) => name.split(/\s*(?:,|&|\/|\+|\band\b|\s)\s*/i).map((t) => t.replace(/\.$/, "")).filter(Boolean);
	const expand = (t) => VOICE_NAMES[t.toUpperCase()] ?? t;
	for (const tokens of [split(partName), split(partName.replace(/([a-z])([A-Z])/g, "$1 $2"))]) if (tokens.length === count) return tokens.map(expand);
	const letters = partName.replace(/[\s.]/g, "");
	if (new RegExp(`^[SATB]{${count}}$`, "i").test(letters)) return [...letters].map(expand);
	if (vocal && count === 4 && /choir|chorus|satb|mixed/i.test(partName)) return [
		"Soprano",
		"Alto",
		"Tenor",
		"Bass"
	];
	if (vocal && count === 2 && /women|ladies|female/i.test(partName)) return ["Soprano", "Alto"];
	if (vocal && count === 2 && /\bmen\b|male/i.test(partName)) return ["Tenor", "Bass"];
	return Array.from({ length: count }, (_, i) => `${partName} ${i + 1}`);
}
/**
* A `<note>` that is a written note of the score: pitched, and not a grace or cue note. The score's
* notes are these, in document order (part by part, measure by measure), and note `n<k>` is the
* k-th of them: edits find a note's element the same way.
*/
const isWrittenNote = (el) => el.tagName === "note" && !kid$2(el, "grace") && !kid$2(el, "cue") && !!kid$2(el, "pitch");
/**
* Read a MusicXML score (score-partwise, as nearly every program writes). Each part becomes one
* line, or one line per voice when voices share a staff the way soprano and alto do; a piano
* part stays whole.
*/
function parseMusicXML(xml) {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	if (doc.getElementsByTagName("parsererror").length) throw new Error("This file is not valid MusicXML.");
	const root = doc.documentElement;
	if (root.tagName === "score-timewise") throw new Error("Timewise MusicXML is not supported yet; save it as partwise.");
	if (root.tagName !== "score-partwise") throw new Error("This file is not a MusicXML score.");
	const title = text(kid$2(root, "work"), "work-title") ?? text(root, "movement-title") ?? root.querySelector("credit credit-words")?.textContent?.trim() ?? "Untitled";
	const info = /* @__PURE__ */ new Map();
	for (const sp of kid$2(root, "part-list")?.getElementsByTagName("score-part") ?? []) {
		const program = sp.getElementsByTagName("midi-program")[0]?.textContent;
		info.set(sp.getAttribute("id") ?? "", {
			name: (text(sp, "part-name") ?? "").replace(/\s+/g, " "),
			program: program ? Number(program) : void 0
		});
	}
	const partEls = kids$2(root, "part");
	const measures = [];
	const parts = [];
	const lines = [];
	const notes = [];
	let staffBase = 0;
	let noteId = 0;
	partEls.forEach((partEl, pi) => {
		const meta = info.get(partEl.getAttribute("id") ?? "") ?? { name: "" };
		const partName = readVoiceName(meta.name) ?? (meta.name || `Part ${pi + 1}`);
		let divisions = 1;
		let staves = 1;
		let transpose = 0;
		let beats = 4;
		let beatType = 4;
		let velocity = DEFAULT_VELOCITY;
		let ending = null;
		const partNotes = [];
		kids$2(partEl, "measure").forEach((mEl, mi) => {
			let cursor = 0;
			let longest = 0;
			let lastStart = 0;
			const m = measures[mi] ??= {
				index: mi,
				label: mEl.getAttribute("number") ?? String(mi + 1),
				length: 0,
				beats,
				beatType,
				tempos: [],
				repeatStart: false
			};
			const q = (d) => d / divisions;
			if (ending) m.ending ??= ending;
			let endingDone = false;
			const sound = (s) => {
				const tempo = s.getAttribute("tempo");
				if (tempo && Number(tempo) > 0 && !m.tempos.some((t) => Math.abs(t.offset - q(cursor)) < 1e-6)) m.tempos.push({
					offset: q(cursor),
					bpm: Number(tempo)
				});
				if (s.hasAttribute("segno")) m.segno = true;
				if (s.hasAttribute("coda")) m.coda = true;
				if (s.hasAttribute("tocoda")) m.toCoda = true;
				if (s.getAttribute("fine") != null) m.fine = true;
				if (s.getAttribute("dacapo") === "yes") m.daCapo = true;
				if (s.hasAttribute("dalsegno")) m.dalSegno = true;
				const dyn = s.getAttribute("dynamics");
				if (dyn && Number(dyn) > 0) velocity = Math.min(127, Math.round(Number(dyn) / 100 * 90));
			};
			for (const el of Array.from(mEl.children)) switch (el.tagName) {
				case "attributes": {
					divisions = num$2(text(el, "divisions"), divisions);
					staves = num$2(text(el, "staves"), staves);
					const time = kid$2(el, "time");
					if (time && text(time, "beats")) {
						beats = String(text(time, "beats")).split("+").reduce((a, b) => a + num$2(b, 0), 0) || 4;
						beatType = num$2(text(time, "beat-type"), 4);
						if (cursor === 0) {
							m.beats = beats;
							m.beatType = beatType;
						}
					}
					const tr = kid$2(el, "transpose");
					if (tr) transpose = num$2(text(tr, "chromatic"), 0) + 12 * num$2(text(tr, "octave-change"), 0);
					break;
				}
				case "backup":
					cursor = Math.max(0, cursor - num$2(text(el, "duration"), 0));
					break;
				case "forward":
					cursor += num$2(text(el, "duration"), 0);
					longest = Math.max(longest, cursor);
					break;
				case "direction": {
					for (const d of el.getElementsByTagName("dynamics")) {
						const mark = d.firstElementChild?.tagName;
						if (mark && DYNAMICS[mark]) velocity = DYNAMICS[mark];
					}
					const s = kid$2(el, "sound");
					if (s) sound(s);
					else {
						const metro = el.getElementsByTagName("metronome")[0];
						const per = num$2(text(metro, "per-minute"), NaN);
						if (metro && per > 0) {
							const bpm = per * ({
								whole: 4,
								half: 2,
								quarter: 1,
								eighth: .5,
								"16th": .25
							}[text(metro, "beat-unit") ?? "quarter"] ?? 1) * (kid$2(metro, "beat-unit-dot") ? 1.5 : 1);
							if (!m.tempos.some((t) => Math.abs(t.offset - q(cursor)) < 1e-6)) m.tempos.push({
								offset: q(cursor),
								bpm
							});
						}
					}
					break;
				}
				case "sound":
					sound(el);
					break;
				case "barline": {
					const rep = kid$2(el, "repeat");
					if (rep?.getAttribute("direction") === "forward") m.repeatStart = true;
					if (rep?.getAttribute("direction") === "backward") m.repeatEnd = Math.max(m.repeatEnd ?? 0, num$2(rep.getAttribute("times"), 2));
					const end = kid$2(el, "ending");
					if (end) {
						const type = end.getAttribute("type");
						const nums = endingNumbers(end.getAttribute("number"));
						if (type === "start") {
							ending = nums;
							m.ending = nums;
						} else {
							m.ending ??= ending ?? nums;
							endingDone = true;
						}
					}
					if (el.getElementsByTagName("segno").length) m.segno = true;
					if (el.getElementsByTagName("coda").length) m.coda = true;
					const s = kid$2(el, "sound");
					if (s) sound(s);
					break;
				}
				case "note": {
					if (kid$2(el, "grace")) break;
					const chord = !!kid$2(el, "chord");
					const d = num$2(text(el, "duration"), 0);
					const start = chord ? lastStart : cursor;
					const pitch = kid$2(el, "pitch");
					if (pitch && isWrittenNote(el)) {
						const p = pitchOf(pitch);
						const ties = kids$2(el, "tie").map((t) => t.getAttribute("type"));
						const tiedNotation = Array.from(el.getElementsByTagName("tied")).map((t) => t.getAttribute("type"));
						const lyricEl = kids$2(el, "lyric").find((l) => (l.getAttribute("number") ?? "1") === "1") ?? kid$2(el, "lyric");
						const syl = text(lyricEl, "syllabic");
						const words = lyricEl ? kids$2(lyricEl, "text").map((t) => t.textContent ?? "").join("") : "";
						partNotes.push({
							id: `n${noteId++}`,
							line: "",
							part: pi,
							staff: staffBase + num$2(text(el, "staff"), 1),
							voice: num$2(text(el, "voice"), 1),
							measure: mi,
							offset: q(start),
							duration: q(d),
							pitch: p.midi + transpose,
							step: p.step,
							octave: p.octave,
							tieNext: ties.includes("start") || tiedNotation.includes("start"),
							tiedFrom: ties.includes("stop") || tiedNotation.includes("stop"),
							velocity,
							lyric: words ? words + (syl === "begin" || syl === "middle" ? "-" : "") : void 0
						});
					}
					if (!chord) {
						lastStart = cursor;
						cursor += d;
					}
					longest = Math.max(longest, cursor);
					break;
				}
			}
			if (endingDone) ending = null;
			const length = longest > 0 ? q(longest) : m.beats * 4 / m.beatType;
			m.length = Math.max(m.length, length);
		});
		const keyboard = KEYBOARD.test(partName);
		const hasLyrics = partNotes.some((n) => n.lyric);
		const vocal = !keyboard && (hasLyrics || VOCAL.test(partName) || meta.program !== void 0 && VOCAL_PROGRAMS.has(meta.program));
		const voiceMeasures = /* @__PURE__ */ new Map();
		const voiceStaff = /* @__PURE__ */ new Map();
		for (const n of partNotes) {
			if (!voiceMeasures.has(n.voice)) voiceMeasures.set(n.voice, /* @__PURE__ */ new Set());
			voiceMeasures.get(n.voice).add(n.measure);
			if (!voiceStaff.has(n.voice)) voiceStaff.set(n.voice, n.staff);
		}
		const most = Math.max(0, ...[...voiceMeasures.values()].map((s) => s.size));
		const byStaffThenVoice = (a, b) => voiceStaff.get(a) - voiceStaff.get(b) || a - b;
		const main = keyboard ? [] : [...voiceMeasures.keys()].filter((v) => voiceMeasures.get(v).size >= Math.max(1, most * .4)).sort(byStaffThenVoice);
		const instrumentName = keyboard ? /organ|org\./i.test(partName) ? "church_organ" : /harp/i.test(partName) ? "orchestral_harp" : /guitar/i.test(partName) ? "acoustic_guitar_nylon" : "acoustic_grand_piano" : meta.program !== void 0 && PROGRAMS[meta.program] || "acoustic_grand_piano";
		const partLines = [];
		if (main.length <= 1) partLines.push({
			id: `p${pi}`,
			name: partName,
			part: pi,
			voices: [...voiceMeasures.keys()].sort((a, b) => a - b),
			vocal,
			instrument: instrumentName
		});
		else {
			const names = voiceNames(partName, main.length, vocal);
			main.forEach((v, i) => partLines.push({
				id: `p${pi}v${v}`,
				name: names[i],
				part: pi,
				voices: [v],
				vocal,
				instrument: instrumentName
			}));
			for (const v of voiceMeasures.keys()) {
				if (main.includes(v)) continue;
				const home = main.find((x) => voiceStaff.get(x) === voiceStaff.get(v)) ?? main[0];
				partLines.find((l) => l.voices.includes(home)).voices.push(v);
			}
		}
		for (const n of partNotes) n.line = (partLines.find((l) => l.voices.includes(n.voice)) ?? partLines[0]).id;
		if (partNotes.length) lines.push(...partLines);
		notes.push(...partNotes);
		parts.push({
			name: partName,
			staves
		});
		staffBase += staves;
	});
	if (!measures.length) throw new Error("This score has no measures.");
	for (const m of measures) m.tempos.sort((a, b) => a.offset - b.offset);
	return {
		title,
		parts,
		lines,
		notes,
		measures,
		...nameUnnamedVoices(lines, notes) ? { guessedNames: true } : {}
	};
}
/** What a score reader calls a part it couldn't read the name of (Audiveris: "Voice"). */
const GENERIC = /^(voice|vocals?|part|staff|instrument|p)?\s*\d*$/i;
const SATB = [
	"Soprano",
	"Alto",
	"Tenor",
	"Bass"
];
/** Digits a score reader's OCR reads for letters: "Ten01" is Tenor. */
const OCR_DIGITS = {
	0: "o",
	1: "l",
	5: "s",
	8: "b"
};
function editDistance(a, b) {
	let row = Array.from({ length: b.length + 1 }, (_, j) => j);
	for (let i = 1; i <= a.length; i++) {
		const next = [i];
		for (let j = 1; j <= b.length; j++) next.push(Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
		row = next;
	}
	return row[b.length];
}
/**
* The choir voice a misread one-word part name stands for ("Ten01", "Sopran0", "8ass"), or null.
* Names of more than one word ("Bass 1", "Soprano Alto") are left as they are.
*/
function readVoiceName(name) {
	if (/\s/.test(name.trim()) || SATB.includes(name)) return null;
	const s = name.toLowerCase().replace(/[0158]/g, (d) => OCR_DIGITS[d]).replace(/[^a-z]/g, "");
	if (s.length < 3) return null;
	const [best, distance] = SATB.map((v) => [v, editDistance(s, v.toLowerCase())]).sort((x, y) => x[1] - y[1])[0];
	return distance <= (best.length >= 5 ? 2 : 1) ? best : null;
}
/**
* Name sung lines whose part names say nothing ("Voice", as Audiveris writes when it can't read
* them), from their order and range: four are soprano, alto, tenor and bass; two are the upper
* or lower voices, or a closed score's two staves of chords. Otherwise they are numbered, so they
* can at least be told apart. Says whether it guessed.
*/
function nameUnnamedVoices(lines, notes) {
	const sung = lines.filter((l) => l.vocal);
	const generic = (l) => GENERIC.test(l.name.replace(/\s+\d+$/, "").trim());
	if (sung.length === 4 && sung.some(generic) && sung.every((l, i) => generic(l) || l.name === SATB[i])) {
		sung.forEach((l, i) => {
			l.name = SATB[i];
		});
		return true;
	}
	if (!sung.length || !sung.every(generic)) return false;
	const own = (l) => notes.filter((n) => n.line === l.id);
	const median = (l) => {
		const p = own(l).map((n) => n.pitch).sort((a, b) => a - b);
		return p.length ? p[p.length >> 1] : 60;
	};
	const chords = (l) => {
		const starts = /* @__PURE__ */ new Map();
		for (const n of own(l)) starts.set(`${n.measure}|${n.offset}`, (starts.get(`${n.measure}|${n.offset}`) ?? 0) + 1);
		const together = [...starts.values()].filter((c) => c > 1).length;
		return starts.size > 0 && together / starts.size > .3;
	};
	let names = null;
	if (sung.length === 4) names = SATB;
	else if (sung.length === 2) {
		const [a, b] = sung.map(median);
		if (a >= 60 && b >= 60 && !chords(sung[0]) && !chords(sung[1])) names = ["Soprano", "Alto"];
		else if (a < 60 && b < 60 && !chords(sung[0]) && !chords(sung[1])) names = ["Tenor", "Bass"];
		else if (a >= 60 && b < 60 && chords(sung[0]) && chords(sung[1])) names = ["Soprano Alto", "Tenor Bass"];
	}
	if (names) sung.forEach((l, i) => {
		l.name = names[i];
	});
	else if (sung.length > 1) sung.forEach((l, i) => {
		l.name = `Voice ${i + 1}`;
	});
	return !!names;
}
//#endregion
//#region ../midi_studio/packages/score-view/src/mxl.ts
function entries(view) {
	let eocd = -1;
	for (let i = view.byteLength - 22; i >= Math.max(0, view.byteLength - 65557); i--) if (view.getUint32(i, true) === 101010256) {
		eocd = i;
		break;
	}
	if (eocd < 0) throw new Error("This .mxl file is not a zip archive.");
	const count = view.getUint16(eocd + 10, true);
	let at = view.getUint32(eocd + 16, true);
	const out = [];
	const decoder = new TextDecoder();
	for (let i = 0; i < count; i++) {
		if (view.getUint32(at, true) !== 33639248) throw new Error("This .mxl file is damaged.");
		const method = view.getUint16(at + 10, true);
		const compressedSize = view.getUint32(at + 20, true);
		const nameLength = view.getUint16(at + 28, true);
		const extraLength = view.getUint16(at + 30, true);
		const commentLength = view.getUint16(at + 32, true);
		const offset = view.getUint32(at + 42, true);
		const name = decoder.decode(new Uint8Array(view.buffer, view.byteOffset + at + 46, nameLength));
		out.push({
			name,
			method,
			compressedSize,
			offset
		});
		at += 46 + nameLength + extraLength + commentLength;
	}
	return out;
}
async function read(view, e) {
	const local = e.offset;
	if (view.getUint32(local, true) !== 67324752) throw new Error("This .mxl file is damaged.");
	const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
	const data = new Uint8Array(view.buffer, view.byteOffset + start, e.compressedSize);
	if (e.method === 0) return new TextDecoder().decode(data);
	if (e.method !== 8) throw new Error("This .mxl file uses a compression this browser cannot read.");
	const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
	return new TextDecoder().decode(await new Response(stream).arrayBuffer());
}
/** The MusicXML inside an .mxl file. */
async function unzipMxl(buffer) {
	const view = new DataView(buffer);
	const all = entries(view);
	const container = all.find((e) => e.name === "META-INF/container.xml");
	let path = null;
	if (container) {
		const xml = await read(view, container);
		path = /full-path\s*=\s*"([^"]+)"/.exec(xml)?.[1] ?? null;
	}
	const score = all.find((e) => e.name === path) ?? all.find((e) => !e.name.startsWith("META-INF/") && /\.(musicxml|xml)$/i.test(e.name));
	if (!score) throw new Error("No score was found inside this .mxl file.");
	return read(view, score);
}
/** A score file's MusicXML: .mxl unzipped, .musicxml and .xml as they are. */
async function readScoreFile(file) {
	const buffer = await file.arrayBuffer();
	const head = new Uint8Array(buffer, 0, Math.min(4, buffer.byteLength));
	return head[0] === 80 && head[1] === 75 ? unzipMxl(buffer) : new TextDecoder().decode(buffer);
}
//#endregion
//#region ../midi_studio/packages/score-view/src/values.ts
/** Written note values: how a length in quarter notes is drawn. */
const EPS$1 = 1e-6;
/** Note values, longest first, in quarters. */
const TYPES = [
	["whole", 4],
	["half", 2],
	["quarter", 1],
	["eighth", .5],
	["16th", .25],
	["32nd", .125],
	["64th", .0625]
];
/** Quarters a note value with dots lasts. */
const valueLength = (type, dots = 0) => (TYPES.find((t) => t[0] === type)?.[1] ?? 0) * (2 - 1 / 2 ** dots);
/** The value (and dots) a length in quarters is written as, or null if no single value is that long. */
function noteValue(quarters) {
	for (const [type, q] of TYPES) for (const dots of [
		0,
		1,
		2
	]) if (Math.abs(q * (2 - 1 / 2 ** dots) - quarters) < EPS$1) return {
		type,
		dots
	};
	return null;
}
/**
* A length in quarters as values that add up to it, longest first (a rest of five eighths is a
* half and an eighth). Null if it can't be written exactly (a tuplet's remainder).
*/
function splitValues(quarters) {
	const out = [];
	let left = quarters;
	while (left > EPS$1) {
		const one = noteValue(left);
		if (one) {
			out.push({
				...one,
				quarters: left
			});
			break;
		}
		let best = null;
		for (const [type, q] of TYPES) for (const dots of [1, 0]) {
			const len = q * (2 - 1 / 2 ** dots);
			if (len <= left + EPS$1 && (!best || len > best.quarters)) best = {
				type,
				dots,
				quarters: len
			};
		}
		if (!best) return null;
		out.push(best);
		left -= best.quarters;
	}
	return out;
}
//#endregion
//#region ../midi_studio/packages/score-view/src/repair.ts
/**
* Checks and fixes for scores that came from a score reader (optical music recognition), such
* as Audiveris. Tested against Audiveris on generated pages (spike/omr): two mistakes it makes
* that change what you practise are a short last line of music it never sees, and a barline it
* misses, which runs two bars into one and puts every later bar number one off.
*/
const EPS = 1e-6;
const FINAL_STYLES = /* @__PURE__ */ new Set([
	"light-heavy",
	"heavy",
	"light-light",
	"heavy-light",
	"heavy-heavy"
]);
const kids$1 = (el, tag) => Array.from(el.children).filter((c) => c.tagName === tag);
const kid$1 = (el, tag) => kids$1(el, tag)[0];
const num$1 = (el, tag) => Number(el && kid$1(el, tag)?.textContent);
/** The length of a bar in quarters, by its time signature. */
const barLength = (m) => m.beats * 4 / m.beatType;
function checkScore(xml, score) {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	const longBars = doc.getElementsByTagName("beats").length > 0 ? score.measures.filter((m) => m.length > barLength(m) + EPS).map((m) => m.index) : [];
	const part = doc.getElementsByTagName("part")[0];
	const measures = part ? kids$1(part, "measure") : [];
	const last = measures[measures.length - 1];
	const ends = !!last && kids$1(last, "barline").some((b) => {
		if (b.getAttribute("location") === "left") return false;
		const style = kid$1(b, "bar-style")?.textContent?.trim() ?? "";
		return FINAL_STYLES.has(style) || kid$1(b, "repeat")?.getAttribute("direction") === "backward";
	});
	return {
		longBars,
		missingEnd: !!last && !ends
	};
}
/**
* Split every bar longer than its time signature into bars of the right length, in every part,
* and number the bars again. A note that crosses a new barline is split into two tied notes.
* Returns the new MusicXML.
*/
function splitLongBars(xml, score, which = checkScore(xml, score).longBars) {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	const long = new Set(which);
	for (const part of Array.from(doc.getElementsByTagName("part"))) {
		let divisions = 1;
		let firstSplit = Infinity;
		kids$1(part, "measure").forEach((mEl, mi) => {
			for (const a of kids$1(mEl, "attributes")) if (num$1(a, "divisions") > 0) divisions = num$1(a, "divisions");
			const m = score.measures[mi];
			if (!m || !long.has(mi)) return;
			const bar = Math.round(barLength(m) * divisions);
			const total = Math.round(m.length * divisions);
			if (bar <= 0 || total <= bar) return;
			const pieces = splitMeasure(doc, mEl, bar, total, divisions);
			mEl.replaceWith(...pieces);
			firstSplit = Math.min(firstSplit, mi);
		});
		const all = kids$1(part, "measure");
		for (let i = Math.max(1, firstSplit); i < all.length; i++) {
			const prev = parseInt(all[i - 1].getAttribute("number") ?? "", 10);
			if (Number.isFinite(prev)) all[i].setAttribute("number", String(prev + 1));
		}
	}
	return new XMLSerializer().serializeToString(doc);
}
function splitMeasure(doc, mEl, bar, total, divisions) {
	const items = [];
	let cursor = 0;
	let head = null;
	for (const el of Array.from(mEl.children)) {
		if (el.tagName === "backup") {
			cursor = Math.max(0, cursor - num$1(el, "duration"));
			continue;
		}
		if (el.tagName === "forward") {
			cursor += num$1(el, "duration");
			continue;
		}
		const grace = el.tagName === "note" && !!kid$1(el, "grace");
		if (el.tagName === "note" && !grace && kid$1(el, "chord") && head) {
			head.els.push(el);
			continue;
		}
		if (el.tagName === "note" && !grace) {
			head = {
				els: [el],
				start: cursor,
				duration: num$1(el, "duration") || 0,
				note: true
			};
			items.push(head);
			cursor += head.duration;
			continue;
		}
		const start = el.tagName === "barline" ? el.getAttribute("location") === "left" ? 0 : total : cursor;
		items.push({
			els: [el],
			start,
			duration: 0,
			note: false
		});
	}
	const count = Math.ceil(total / bar);
	const piece = (start) => Math.min(count - 1, Math.floor((start + EPS) / bar));
	const out = Array.from({ length: count }, () => []);
	for (const item of items) {
		let it = item;
		while (it.note && piece(it.start) < count - 1 && it.start + it.duration > (piece(it.start) + 1) * bar) {
			const cut = (piece(it.start) + 1) * bar;
			const first = {
				...it,
				duration: cut - it.start,
				els: it.els.map((e) => e.cloneNode(true))
			};
			const rest = {
				...it,
				start: cut,
				duration: it.start + it.duration - cut,
				els: it.els.map((e) => e.cloneNode(true))
			};
			for (const e of first.els) retime(doc, e, first.duration, divisions, "start");
			for (const e of rest.els) {
				retime(doc, e, rest.duration, divisions, "stop");
				kids$1(e, "lyric").forEach((l) => l.remove());
			}
			out[piece(first.start)].push(first);
			it = rest;
		}
		out[piece(it.start)].push(it);
	}
	return out.map((list, k) => {
		const m = mEl.cloneNode(false);
		m.removeAttribute("width");
		m.removeAttribute("implicit");
		const base = k * bar;
		const length = Math.min(bar, total - base);
		let at = 0;
		const move = (to) => {
			if (to === at) return;
			const el = doc.createElement(to < at ? "backup" : "forward");
			const d = doc.createElement("duration");
			d.textContent = String(Math.abs(to - at));
			el.appendChild(d);
			m.appendChild(el);
			at = to;
		};
		for (const it of list) {
			if (it.els[0].tagName === "barline") {
				m.append(...it.els);
				continue;
			}
			move(Math.min(it.start - base, length));
			m.append(...it.els);
			at += it.duration;
		}
		if (!list.some((it) => it.note)) {
			const rest = doc.createElement("note");
			const r = doc.createElement("rest");
			r.setAttribute("measure", "yes");
			const d = doc.createElement("duration");
			d.textContent = String(length);
			const v = doc.createElement("voice");
			v.textContent = "1";
			rest.append(r, d, v);
			m.insertBefore(rest, m.firstChild);
		}
		return m;
	});
}
/** Give a note a new length (in divisions), its written value, and a tie on one side. */
function retime(doc, note, duration, divisions, tie) {
	const d = kid$1(note, "duration");
	if (d) d.textContent = String(duration);
	kids$1(note, "dot").forEach((e) => e.remove());
	const value = noteValue(duration / divisions);
	const type = kid$1(note, "type");
	if (value && type) {
		type.textContent = value.type;
		for (let i = 0; i < value.dots; i++) type.after(doc.createElement("dot"));
	} else type?.remove();
	if (kid$1(note, "rest")) return;
	const other = tie === "start" ? "stop" : "start";
	const keep = kids$1(note, "tie").some((t) => t.getAttribute("type") === other);
	kids$1(note, "tie").forEach((t) => t.remove());
	let notations = kid$1(note, "notations");
	notations?.querySelectorAll("tied").forEach((t) => t.remove());
	const types = keep ? ["stop", "start"] : [tie];
	let after = d ?? note.firstElementChild;
	for (const t of types) {
		const el = doc.createElement("tie");
		el.setAttribute("type", t);
		after.after(el);
		after = el;
	}
	if (!notations) {
		notations = doc.createElement("notations");
		note.appendChild(notations);
	}
	for (const t of types) {
		const el = doc.createElement("tied");
		el.setAttribute("type", t);
		notations.appendChild(el);
	}
}
/** The first clef of each staff, numbered across the score as the parser numbers them. */
function staffClefs(doc) {
	const out = /* @__PURE__ */ new Map();
	let base = 0;
	for (const part of Array.from(doc.getElementsByTagName("part"))) {
		let staves = 1;
		for (const a of Array.from(part.getElementsByTagName("attributes"))) {
			if (num$1(a, "staves") > 0) staves = Math.max(staves, num$1(a, "staves"));
			for (const c of kids$1(a, "clef")) {
				const staff = base + (Number(c.getAttribute("number")) || 1);
				if (!out.has(staff)) out.set(staff, {
					sign: kid$1(c, "sign")?.textContent?.trim() ?? "",
					octave: num$1(c, "clef-octave-change") || 0
				});
			}
		}
		base += staves;
	}
	return out;
}
const TENOR = /\bten(or|ore|ori)?\b|^T\.?\s*\d?$/i;
/**
* Tenor parts written in the treble clef are sung an octave lower than written. The clef says so
* with a small 8 below it, which score readers miss (Audiveris did on MuseScore's pages), and
* which older hymnals leave out. A sung part named tenor on a plain treble clef, sitting an
* octave too high for a tenor, is the case: returns the lines to play an octave lower.
*/
function tenorsInTreble(xml, score) {
	const clefs = staffClefs(new DOMParser().parseFromString(xml, "application/xml"));
	return score.lines.filter((line) => {
		if (!line.vocal || !TENOR.test(line.name)) return false;
		const own = score.notes.filter((n) => n.line === line.id);
		if (!own.length) return false;
		const plainTreble = [...new Set(own.map((n) => n.staff))].every((s) => clefs.get(s)?.sign === "G" && clefs.get(s)?.octave === 0);
		const pitches = own.map((n) => n.pitch).sort((a, b) => a - b);
		return plainTreble && pitches[Math.floor(pitches.length / 2)] >= 66;
	}).map((l) => l.id);
}
/** The score with these lines an octave lower (as heard; the drawn notes stay as written). */
function octaveDown(score, lines) {
	if (!lines.length) return score;
	const set = new Set(lines);
	return {
		...score,
		notes: score.notes.map((n) => set.has(n.line) ? {
			...n,
			pitch: n.pitch - 12
		} : n)
	};
}
//#endregion
//#region ../midi_studio/packages/score-view/src/render.ts
/** Smaller on a phone, so a system of four staves and lyrics still fits a few measures. */
const scaleFor = (width) => width < 520 ? 30 : width < 900 ? 36 : 42;
/** Draw a MusicXML score to fit the width, and say when each drawn note is played. */
function engraveScore(tk, req) {
	const scale = scaleFor(req.width);
	tk.setOptions({
		scale,
		pageWidth: Math.round(Math.max(req.width, 300) * 100 / scale),
		pageHeight: 6e4,
		adjustPageHeight: true,
		breaks: "auto",
		header: "auto",
		footer: "none",
		pageMarginTop: 40,
		pageMarginBottom: 40,
		pageMarginLeft: 40,
		pageMarginRight: 40,
		svgViewBox: true,
		svgAdditionalAttribute: [
			"staff@n",
			"layer@n",
			"note@pname",
			"note@oct"
		]
	});
	if (!tk.loadData(req.xml)) throw new Error(`The score could not be read for drawing: ${tk.getLog()}`);
	const pages = [];
	for (let p = 1; p <= tk.getPageCount(); p++) pages.push(tk.renderToSVG(p));
	const noteQ = /* @__PURE__ */ new Map();
	const restQ = /* @__PURE__ */ new Map();
	const measureQ = /* @__PURE__ */ new Map();
	for (const e of tk.renderToTimemap({
		includeMeasures: true,
		includeRests: true
	})) {
		for (const id of e.on ?? []) if (!id.includes("-rend") && !noteQ.has(id)) noteQ.set(id, e.qstamp);
		for (const id of e.restsOn ?? []) if (!id.includes("-rend") && !restQ.has(id)) restQ.set(id, e.qstamp);
		if (e.measureOn && !e.measureOn.includes("-rend") && !measureQ.has(e.measureOn)) measureQ.set(e.measureOn, e.qstamp);
	}
	return {
		pages,
		noteQ: [...noteQ],
		restQ: [...restQ],
		measureQ: [...measureQ]
	};
}
//#endregion
//#region ../midi_studio/packages/score-view/src/engrave.ts
/**
* Draw scores in a worker. `makeWorker` starts the worker (a module that calls `serveEngraving`),
* the first time a score is drawn. How it is started is up to the app's bundler: with Vite,
* `() => new Worker(new URL('./engrave.worker.ts', import.meta.url), { type: 'module' })`.
*/
function createEngraver(makeWorker) {
	let worker = null;
	let seq = 0;
	const pending = /* @__PURE__ */ new Map();
	return (request) => {
		if (typeof Worker === "undefined") return Promise.reject(/* @__PURE__ */ new Error("This browser cannot draw scores."));
		if (!worker) {
			worker = makeWorker();
			worker.onmessage = (e) => {
				const { id, result, error } = e.data;
				const p = pending.get(id);
				pending.delete(id);
				if (result) p?.resolve(result);
				else p?.reject(new Error(error ?? "The score could not be drawn."));
			};
			worker.onerror = (e) => {
				for (const p of pending.values()) p.reject(new Error(e.message || "The notation engine failed to load."));
				pending.clear();
			};
		}
		const id = ++seq;
		return new Promise((resolve, reject) => {
			pending.set(id, {
				resolve,
				reject
			});
			worker.postMessage({
				id,
				request
			});
		});
	};
}
/**
* The worker's side: answer drawing requests with Verovio. `load` makes the toolkit (Verovio is
* LGPL, so the app loads it as a file of its own, which can be replaced), once.
*/
function serveEngraving(scope, load) {
	let toolkit = null;
	scope.onmessage = async (e) => {
		const { id, request } = e.data;
		try {
			toolkit ??= load();
			scope.postMessage({
				id,
				result: engraveScore(await toolkit, request)
			});
		} catch (err) {
			scope.postMessage({
				id,
				error: err instanceof Error ? err.message : String(err)
			});
		}
	};
}
//#endregion
//#region ../midi_studio/packages/score-view/src/link.ts
/** What a note is known by on both sides: where it is written, on which staff and voice, and its written pitch. */
const keyOf = (measure, offset, staff, voice, step, octave) => `${measure}|${Math.round(offset * 1e3)}|${staff}|${voice}|${step.toUpperCase()}|${octave}`;
const noteKey = (n) => keyOf(n.measure, n.offset, n.staff, n.voice, n.step, n.octave);
/** The notes drawn in an SVG score, with the measure each is in (counted in the order drawn). */
function drawnNotes(root) {
	const out = [];
	root.querySelectorAll("g.measure").forEach((m, measure) => {
		m.querySelectorAll("g.note").forEach((el) => {
			const staff = Number(el.closest("g.staff")?.getAttribute("data-n"));
			const voice = Number(el.closest("g.layer")?.getAttribute("data-n"));
			const step = el.getAttribute("data-pname") ?? "";
			const octave = Number(el.getAttribute("data-oct"));
			if (el.id && step && Number.isFinite(staff)) out.push({
				id: el.id,
				measure,
				staff,
				voice,
				step,
				octave
			});
		});
	});
	return out;
}
/**
* Match drawn notes to the score's notes. Verovio's timemap says when each drawn note starts
* and each measure starts, so a note's place in its measure is the difference.
*/
function linkNotes(score, drawn, noteQ, measureQ, measureIds) {
	const byKey = /* @__PURE__ */ new Map();
	for (const n of score.notes) byKey.set(noteKey(n), [...byKey.get(noteKey(n)) ?? [], n.id]);
	const out = /* @__PURE__ */ new Map();
	for (const d of drawn) {
		const q = noteQ.get(d.id);
		const mq = measureQ.get(measureIds[d.measure]);
		if (q === void 0 || mq === void 0) continue;
		for (const id of byKey.get(keyOf(d.measure, q - mq, d.staff, d.voice, d.step, d.octave)) ?? []) if (!out.has(id)) out.set(id, d.id);
	}
	return out;
}
/** The rests drawn in an SVG score. */
function drawnRests(root) {
	const out = [];
	root.querySelectorAll("g.measure").forEach((m, measure) => {
		m.querySelectorAll("g.rest, g.mRest").forEach((el) => {
			const staff = Number(el.closest("g.staff")?.getAttribute("data-n"));
			const voice = Number(el.closest("g.layer")?.getAttribute("data-n"));
			if (el.id && Number.isFinite(staff)) out.push({
				id: el.id,
				measure,
				staff,
				voice
			});
		});
	});
	return out;
}
/** Match drawn rests to the score's rests, by bar, staff, voice and start. */
function linkRests(rests, drawn, restQ, measureQ, measureIds) {
	const key = (measure, offset, staff, voice) => `${measure}|${Math.round(offset * 1e3)}|${staff}|${voice}`;
	const byKey = /* @__PURE__ */ new Map();
	for (const r of rests) byKey.set(key(r.measure, r.offset, r.staff, r.voice), r.id);
	const out = /* @__PURE__ */ new Map();
	for (const d of drawn) {
		const q = restQ.get(d.id);
		const mq = measureQ.get(measureIds[d.measure]);
		if (q === void 0 || mq === void 0) continue;
		const id = byKey.get(key(d.measure, q - mq, d.staff, d.voice));
		if (id && !out.has(id)) out.set(id, d.id);
	}
	return out;
}
//#endregion
//#region ../midi_studio/packages/score-view/src/layout.ts
/**
* Where everything in a MusicXML measure sits in time, for edits and for finding rests. MusicXML
* writes a measure as runs of notes, one voice after another, each run going back to the start
* with a <backup>; a note's start is where the runs before it left the cursor.
*/
const kids = (el, tag) => Array.from(el.children).filter((c) => c.tagName === tag);
const kid = (el, tag) => el ? Array.from(el.children).find((c) => c.tagName === tag) : void 0;
const textOf = (el, tag) => kid(el, tag)?.textContent?.trim() ?? null;
const num = (el, tag) => Number(textOf(el, tag));
/** Everything in a measure, in order, with its time. */
function scanMeasure(measure) {
	const out = [];
	let cursor = 0;
	let run = 0;
	let head = null;
	for (const el of Array.from(measure.children)) {
		const base = {
			el,
			chord: [],
			start: cursor,
			duration: 0,
			voice: textOf(el, "voice") ?? "1",
			staff: textOf(el, "staff") ?? "1",
			run
		};
		if (el.tagName === "backup") {
			const d = num(el, "duration") || 0;
			out.push({
				...base,
				kind: "backup",
				duration: d
			});
			cursor = Math.max(0, cursor - d);
			run++;
			continue;
		}
		if (el.tagName === "forward") {
			const d = num(el, "duration") || 0;
			out.push({
				...base,
				kind: "forward",
				duration: d
			});
			cursor += d;
			continue;
		}
		if (el.tagName === "note" && !kid(el, "grace")) {
			if (kid(el, "chord") && head) {
				head.chord.push(el);
				continue;
			}
			const d = num(el, "duration") || 0;
			head = {
				...base,
				kind: kid(el, "rest") ? "rest" : "note",
				chord: [el],
				duration: d
			};
			out.push(head);
			cursor += d;
			continue;
		}
		out.push({
			...base,
			kind: "other"
		});
	}
	return out;
}
/** Where a run's cursor ends: after its last note, rest or forward. */
function runEnd(slots, run) {
	let end = 0;
	for (const s of slots) if (s.run === run && s.kind !== "backup" && s.kind !== "other") end = Math.max(end, s.start + s.duration);
	return end;
}
/** Apply an <attributes> element to the state. */
function applyAttributes(state, a) {
	if (num(a, "divisions") > 0) state.divisions = num(a, "divisions");
	const time = kid(a, "time");
	if (time && textOf(time, "beats")) {
		state.beats = String(textOf(time, "beats")).split("+").reduce((x, y) => x + (Number(y) || 0), 0) || 4;
		state.beatType = num(time, "beat-type") || 4;
	}
	const key = kid(a, "key");
	if (key && textOf(key, "fifths") != null) state.fifths = num(key, "fifths") || 0;
	for (const c of kids(a, "clef")) state.clefs.set(Number(c.getAttribute("number")) || 1, {
		sign: textOf(c, "sign") ?? "G",
		line: num(c, "line") || 2,
		octave: num(c, "clef-octave-change") || 0
	});
}
/** The state of a part just before `stop` (an element in one of its measures). */
function stateAt(part, stop) {
	const state = {
		divisions: 1,
		beats: 4,
		beatType: 4,
		fifths: 0,
		clefs: /* @__PURE__ */ new Map()
	};
	for (const m of kids(part, "measure")) {
		for (const el of Array.from(m.children)) {
			if (el === stop) return state;
			if (el.tagName === "attributes") applyAttributes(state, el);
		}
		if (m === stop) return state;
	}
	return state;
}
/** A bar's length by its time signature, in divisions. */
const barDivisions = (s) => Math.round(s.beats * 4 * s.divisions / s.beatType);
const parts = (doc) => kids(doc.documentElement, "part");
/** Every `<note>` element that `test` picks, in document order, with its place. */
function collect(doc, test) {
	const out = [];
	let staffBase = 0;
	parts(doc).forEach((part, partIndex) => {
		let staves = 1;
		kids(part, "measure").forEach((measure, measureIndex) => {
			for (const el of Array.from(measure.children)) {
				if (el.tagName === "attributes" && num(el, "staves") > 0) staves = num(el, "staves");
				if (test(el)) out.push({
					el,
					part,
					partIndex,
					measure,
					measureIndex,
					staff: staffBase + (num(el, "staff") || 1)
				});
			}
		});
		staffBase += staves;
	});
	return out;
}
/** The score's written notes, in the order the parser numbers them: note `n<k>` is the k-th. */
const writtenNotes = (doc) => collect(doc, isWrittenNote);
/** A rest that can be tapped and turned into a note (rests in chords and grace rests aside). */
const isWrittenRest = (el) => el.tagName === "note" && !!kid(el, "rest") && !kid(el, "grace") && !kid(el, "cue") && !kid(el, "chord");
/** The score's rests: rest `r<k>` is the k-th. */
const writtenRestEls = (doc) => collect(doc, isWrittenRest);
/** The rests of a score, where they start. */
function writtenRests(xml) {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	const starts = /* @__PURE__ */ new Map();
	const lengths = /* @__PURE__ */ new Map();
	const divs = /* @__PURE__ */ new Map();
	for (const part of parts(doc)) {
		const state = {
			divisions: 1,
			beats: 4,
			beatType: 4,
			fifths: 0,
			clefs: /* @__PURE__ */ new Map()
		};
		for (const m of kids(part, "measure")) {
			for (const a of kids(m, "attributes")) applyAttributes(state, a);
			for (const s of scanMeasure(m)) if (s.kind === "rest") {
				starts.set(s.el, s.start);
				lengths.set(s.el, s.duration);
				divs.set(s.el, state.divisions);
			}
		}
	}
	return writtenRestEls(doc).map((r, k) => ({
		id: `r${k}`,
		part: r.partIndex,
		staff: r.staff,
		voice: Number(textOf(r.el, "voice") ?? 1) || 1,
		measure: r.measureIndex,
		offset: (starts.get(r.el) ?? 0) / (divs.get(r.el) ?? 1),
		duration: (lengths.get(r.el) ?? 0) / (divs.get(r.el) ?? 1)
	}));
}
//#endregion
//#region ../midi_studio/packages/score-view/src/edit.ts
/**
* Corrections to a MusicXML score, note by note, for what a score reader got wrong. Each edit
* takes the score's text and gives back new text (and what to select next): the rest of the
* file is left as it was.
*
* Notes are named as the parser names them (`n<k>`, the k-th written note) and rests as
* `r<k>` (the k-th rest), so a tap on the drawing, which is linked to those names, says what
* to change.
*
* Bars keep adding up: a note made longer takes the time of the rests after it first, and
* moves the notes after it later only if there are none; a note made shorter leaves a rest after
* it, or, in a bar that was too long (as when an eighth was read as a quarter), moves the notes
* after it earlier. Nothing moves in the other voices.
*/
const STEPS = [
	"C",
	"D",
	"E",
	"F",
	"G",
	"A",
	"B"
];
const SHARPS = [
	"F",
	"C",
	"G",
	"D",
	"A",
	"E",
	"B"
];
const ACCIDENTALS = {
	[-2]: "flat-flat",
	[-1]: "flat",
	0: "natural",
	1: "sharp",
	2: "double-sharp"
};
const BEAM_LEVEL = {
	eighth: 1,
	"16th": 2,
	"32nd": 3,
	"64th": 4
};
/** The order of a <note>'s children in MusicXML. */
const NOTE_ORDER = [
	"grace",
	"cue",
	"chord",
	"pitch",
	"unpitched",
	"rest",
	"duration",
	"tie",
	"instrument",
	"footnote",
	"level",
	"voice",
	"type",
	"dot",
	"accidental",
	"time-modification",
	"stem",
	"notehead",
	"notehead-text",
	"staff",
	"beam",
	"notations",
	"lyric",
	"play",
	"listen"
];
/** A step's alteration in a key: F is sharp in G major. */
function keyAlter(fifths, step) {
	if (fifths > 0) return SHARPS.slice(0, fifths).includes(step) ? 1 : 0;
	if (fifths < 0) return [...SHARPS].reverse().slice(0, -fifths).includes(step) ? -1 : 0;
	return 0;
}
const load = (xml) => {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	if (doc.getElementsByTagName("parsererror").length) throw new Error("This file is not valid MusicXML.");
	return doc;
};
const save = (doc) => new XMLSerializer().serializeToString(doc);
function make(doc, tag, text, attrs = {}) {
	const el = doc.createElement(tag);
	if (text !== void 0) el.textContent = text;
	for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
	return el;
}
/** Put a child in its place among a note's children. */
function place(note, child) {
	const rank = NOTE_ORDER.indexOf(child.tagName);
	const before = Array.from(note.children).find((c) => NOTE_ORDER.indexOf(c.tagName) > rank) ?? null;
	note.insertBefore(child, before);
}
function setChild(note, tag, text) {
	const el = kid(note, tag);
	if (el) el.textContent = text;
	else place(note, make(note.ownerDocument, tag, text));
}
const removeAll = (el, tag) => kids(el, tag).forEach((c) => c.remove());
function find(doc, target) {
	const list = target.kind === "note" ? writtenNotes(doc) : writtenRestEls(doc);
	const k = Number(target.id.slice(1));
	const found = Number.isInteger(k) ? list[k] : void 0;
	if (!found || target.id[0] !== (target.kind === "note" ? "n" : "r")) throw new Error(`There is no ${target.kind} ${target.id} in this score.`);
	return found;
}
/** The name a note or rest element has now. */
function nameOf(doc, el) {
	const n = writtenNotes(doc).findIndex((x) => x.el === el);
	if (n >= 0) return {
		kind: "note",
		id: `n${n}`
	};
	const r = writtenRestEls(doc).findIndex((x) => x.el === el);
	return r >= 0 ? {
		kind: "rest",
		id: `r${r}`
	} : null;
}
/** The slot (a note with its chord, or a rest) an element is in. */
function slotOf(measure, el) {
	const slot = scanMeasure(measure).find((s) => s.el === el || s.chord.includes(el));
	if (!slot) throw new Error("That note is not in its measure.");
	return slot;
}
function readPitch(note) {
	const p = kid(note, "pitch");
	return {
		step: (textOf(p, "step") ?? "C").toUpperCase(),
		octave: Number(textOf(p, "octave") ?? 4),
		alter: Math.round(Number(textOf(p, "alter") ?? 0)) || 0
	};
}
function writePitch(note, { step, octave, alter }) {
	const doc = note.ownerDocument;
	let p = kid(note, "pitch");
	if (!p) {
		p = make(doc, "pitch");
		place(note, p);
	}
	p.replaceChildren(make(doc, "step", step), ...alter ? [make(doc, "alter", String(alter))] : [], make(doc, "octave", String(octave)));
}
const tied = (note, type) => kids(note, "tie").some((t) => t.getAttribute("type") === type);
/** The notes of one staff of a measure, every note of every chord, in the order they sound. */
function staffNotes(measure, staff) {
	const out = [];
	for (const s of scanMeasure(measure)) if (s.kind === "note") {
		for (const el of s.chord) if ((textOf(el, "staff") ?? "1") === staff && kid(el, "pitch")) out.push({
			el,
			start: s.start
		});
	}
	return out.sort((a, b) => a.start - b.start);
}
/** The alteration a step and octave has at a point in a bar: the key's, or an accidental's before it. */
function impliedAlter(measure, staff, fifths, at, self, step, octave) {
	let alter = keyAlter(fifths, step);
	for (const n of staffNotes(measure, staff)) {
		if (n.start > at || n.el === self) break;
		const p = readPitch(n.el);
		if (p.step === step && p.octave === octave && !tied(n.el, "stop")) alter = p.alter;
	}
	return alter;
}
/**
* Draw the accidentals these steps (step and octave, "F4") need in a bar on one staff: a sign
* where a note's alteration differs from the key's or the last one in the bar, none where it
* doesn't. Other notes keep theirs.
*/
function respell(measure, staff, fifths, pairs) {
	const state = /* @__PURE__ */ new Map();
	for (const { el } of staffNotes(measure, staff)) {
		const p = readPitch(el);
		const k = `${p.step}${p.octave}`;
		const current = state.get(k) ?? keyAlter(fifths, p.step);
		if (pairs.has(k)) {
			removeAll(el, "accidental");
			if (p.alter !== current && !tied(el, "stop")) place(el, make(el.ownerDocument, "accidental", ACCIDENTALS[p.alter] ?? "natural"));
		}
		if (!tied(el, "stop")) state.set(k, p.alter);
	}
}
/** Write a note's or rest's length: its duration, value and dots; out of any tuplet. */
function setLengthOf(note, duration, divisions) {
	setChild(note, "duration", String(duration));
	removeAll(note, "dot");
	removeAll(note, "time-modification");
	kid(note, "notations")?.querySelectorAll("tuplet").forEach((t) => t.remove());
	const rest = kid(note, "rest");
	if (rest?.getAttribute("measure") === "yes") rest.removeAttribute("measure");
	const value = noteValue(duration / divisions);
	if (!value) {
		removeAll(note, "type");
		return;
	}
	setChild(note, "type", value.type);
	const type = kid(note, "type");
	for (let i = 0; i < value.dots; i++) type.after(make(note.ownerDocument, "dot"));
}
/** Rests that fill `duration` divisions in a voice: values that add up, or a gap if none can. */
function makeRests(doc, duration, divisions, voice, staff) {
	const values = splitValues(duration / divisions);
	if (!values || values.some((v) => Math.abs(v.quarters * divisions - Math.round(v.quarters * divisions)) > 1e-6)) {
		const f = make(doc, "forward");
		f.append(make(doc, "duration", String(duration)), make(doc, "voice", voice), ...staff ? [make(doc, "staff", staff)] : []);
		return [f];
	}
	return values.map((v) => {
		const r = make(doc, "note");
		r.append(make(doc, "rest"), make(doc, "duration", String(Math.round(v.quarters * divisions))), make(doc, "voice", voice), make(doc, "type", v.type));
		for (let i = 0; i < v.dots; i++) r.append(make(doc, "dot"));
		if (staff) r.append(make(doc, "staff", staff));
		return r;
	});
}
/** Make a rest or gap shorter, keeping its start; a rest is written again as values that fit. */
function shorten(slot, by, divisions) {
	const left = slot.duration - by;
	if (slot.kind === "forward") {
		setChild(slot.el, "duration", String(left));
		return;
	}
	const staff = textOf(slot.el, "staff");
	const rests = makeRests(slot.el.ownerDocument, left, divisions, slot.voice, staff);
	slot.el.replaceWith(...rests);
}
/**
* Multiply a part's divisions (and every duration in it) so a length in quarters is a whole number
* of them: an eighth in a part counted in quarters. Returns the part's state again.
*/
function ensureDivisions(part, at, quarters) {
	const state = stateAt(part, at);
	let k = 1;
	while (Math.abs(quarters * state.divisions * k - Math.round(quarters * state.divisions * k)) > 1e-6 && k < 64) k *= 2;
	if (k === 1) return state;
	for (const m of kids(part, "measure")) {
		for (const el of Array.from(m.getElementsByTagName("duration")).concat(Array.from(m.getElementsByTagName("offset")))) el.textContent = String(Math.round(Number(el.textContent) * k));
		for (const a of kids(m, "attributes")) {
			const d = kid(a, "divisions");
			if (d) d.textContent = String(Number(d.textContent) * k);
		}
	}
	return stateAt(part, at);
}
/**
* After a run's notes changed length, the <backup> that ends it goes back by as much more or less,
* so the next voice still starts where it did.
*/
function keepNextRunInPlace(measure, run, afterBoundary, boundary) {
	if (!boundary || afterBoundary === null) return;
	const slots = scanMeasure(measure);
	const back = (slots.find((s) => s.el === boundary)?.start ?? runEnd(slots, run)) - afterBoundary;
	if (back > 0) setChild(boundary, "duration", String(back));
	else if (back === 0) boundary.remove();
	else {
		const f = make(boundary.ownerDocument, "forward");
		f.append(make(boundary.ownerDocument, "duration", String(-back)));
		boundary.replaceWith(f);
	}
}
/** Remove trailing rests (and gaps) from a run, up to `excess` divisions. */
function trimEnd(measure, run, excess, divisions) {
	const slots = scanMeasure(measure).filter((s) => s.run === run && (s.kind === "note" || s.kind === "rest" || s.kind === "forward"));
	for (let i = slots.length - 1; i >= 0 && excess > 0; i--) {
		const s = slots[i];
		if (s.kind === "note") break;
		if (s.duration <= excess) {
			s.el.remove();
			excess -= s.duration;
		} else {
			shorten(s, excess, divisions);
			excess = 0;
		}
	}
}
/** Where to add to the end of a run: after its last note, rest or gap (before a final barline). */
function runTail(measure, run) {
	const slots = scanMeasure(measure);
	const timed = slots.filter((s) => s.run === run && (s.kind === "note" || s.kind === "rest" || s.kind === "forward"));
	const last = timed[timed.length - 1];
	if (last) return (last.chord[last.chord.length - 1] ?? last.el).nextElementSibling;
	return slots.find((s) => s.kind === "backup" && s.run === run)?.el ?? null;
}
function insertBeforeOrAppend(measure, before, els) {
	for (const e of els) measure.insertBefore(e, before);
}
/**
* Beam a run's eighths and shorter again, a beat at a time (a dotted quarter in 6/8): after an
* edit the old beams may join notes that no longer belong together.
*/
function rebeam(measure, run, state) {
	const beat = state.beatType === 8 && state.beats % 3 === 0 ? 1.5 * state.divisions : state.divisions;
	const slots = scanMeasure(measure).filter((s) => s.run === run && (s.kind === "note" || s.kind === "rest"));
	for (const s of slots) for (const el of s.chord) removeAll(el, "beam");
	const level = (s) => s.kind === "note" ? BEAM_LEVEL[textOf(s.el, "type") ?? ""] ?? 0 : 0;
	const groups = [];
	let group = [];
	for (const s of slots) {
		const prev = group[group.length - 1];
		if (prev && level(s) > 0 && Math.floor((s.start + 1e-6) / beat) === Math.floor((prev.start + 1e-6) / beat) && Math.abs(prev.start + prev.duration - s.start) < 1e-6) group.push(s);
		else {
			if (group.length) groups.push(group);
			group = level(s) > 0 ? [s] : [];
		}
	}
	if (group.length) groups.push(group);
	for (const g of groups) {
		if (g.length < 2) continue;
		const top = Math.max(...g.map(level));
		for (let L = 1; L <= top; L++) {
			let i = 0;
			while (i < g.length) {
				if (level(g[i]) < L) {
					i++;
					continue;
				}
				let j = i;
				while (j + 1 < g.length && level(g[j + 1]) >= L) j++;
				for (let k = i; k <= j; k++) {
					const value = i === j ? i === 0 ? "forward hook" : "backward hook" : k === i ? "begin" : k === j ? "end" : "continue";
					const head = g[k].el;
					const beams = kids(head, "beam");
					const b = make(head.ownerDocument, "beam", value, { number: String(L) });
					if (beams.length) beams[beams.length - 1].after(b);
					else place(head, b);
				}
				i = j + 1;
			}
		}
	}
}
/** Remove the other half of a tie to or from a note that is going. */
function untie(doc, found) {
	const p = readPitch(found.el);
	const voice = textOf(found.el, "voice") ?? "1";
	const same = writtenNotes(doc).filter((n) => n.part === found.part && (textOf(n.el, "voice") ?? "1") === voice && (() => {
		const q = readPitch(n.el);
		return q.step === p.step && q.octave === p.octave && q.alter === p.alter;
	})());
	const i = same.findIndex((n) => n.el === found.el);
	const drop = (el, type) => {
		kids(el, "tie").filter((t) => t.getAttribute("type") === type).forEach((t) => t.remove());
		kid(el, "notations")?.querySelectorAll(`tied[type="${type}"]`).forEach((t) => t.remove());
	};
	if (tied(found.el, "start") && same[i + 1]) drop(same[i + 1].el, "stop");
	if (tied(found.el, "stop") && same[i - 1]) drop(same[i - 1].el, "start");
}
/** Move a note up or down a step (a line or space), to the pitch the key and bar give that step. */
function stepNote(xml, id, direction) {
	const doc = load(xml);
	const found = find(doc, {
		kind: "note",
		id
	});
	const state = stateAt(found.part, found.el);
	const before = readPitch(found.el);
	let i = STEPS.indexOf(before.step) + direction;
	let octave = before.octave;
	if (i > 6) {
		i = 0;
		octave++;
	}
	if (i < 0) {
		i = 6;
		octave--;
	}
	const step = STEPS[i];
	const staff = textOf(found.el, "staff") ?? "1";
	const at = slotOf(found.measure, found.el).start;
	writePitch(found.el, {
		step,
		octave,
		alter: impliedAlter(found.measure, staff, state.fifths, at, found.el, step, octave)
	});
	respell(found.measure, staff, state.fifths, /* @__PURE__ */ new Set([`${before.step}${before.octave}`, `${step}${octave}`]));
	return {
		xml: save(doc),
		select: {
			kind: "note",
			id
		}
	};
}
/** Make a note flat (-1), natural (0) or sharp (1); the bar's other notes keep their pitches. */
function setAlter(xml, id, alter) {
	const doc = load(xml);
	const found = find(doc, {
		kind: "note",
		id
	});
	const state = stateAt(found.part, found.el);
	const p = readPitch(found.el);
	writePitch(found.el, {
		...p,
		alter
	});
	respell(found.measure, textOf(found.el, "staff") ?? "1", state.fifths, /* @__PURE__ */ new Set([`${p.step}${p.octave}`]));
	return {
		xml: save(doc),
		select: {
			kind: "note",
			id
		}
	};
}
/**
* Give a note (with its chord) or a rest a new length, in quarters: 1 a quarter, 1.5 a dotted
* quarter. The bar keeps adding up (see the top of this file).
*/
function setLength(xml, target, quarters) {
	if (!noteValue(quarters)) throw new Error(`A note can't be ${quarters} quarters long.`);
	const doc = load(xml);
	const found = find(doc, target);
	const state = ensureDivisions(found.part, found.el, quarters);
	const { measure } = found;
	const slot = slotOf(measure, found.el);
	const newDuration = Math.round(quarters * state.divisions);
	const delta = newDuration - slot.duration;
	if (delta === 0) return {
		xml,
		select: target
	};
	const slots = scanMeasure(measure);
	const run = slot.run;
	const bar = barDivisions(state);
	const oldEnd = runEnd(slots, run);
	const goal = oldEnd < bar ? oldEnd : bar;
	const boundarySlot = slots.find((s) => s.kind === "backup" && s.run === run) ?? null;
	const boundary = boundarySlot?.el ?? null;
	const afterBoundary = boundarySlot ? Math.max(0, boundarySlot.start - boundarySlot.duration) : null;
	for (const el of slot.chord) setLengthOf(el, newDuration, state.divisions);
	if (delta > 0) {
		let need = delta;
		const after = slots.filter((s) => s.run === run && s.start >= slot.start + slot.duration - 1e-6 && s !== slot && (s.kind === "note" || s.kind === "rest" || s.kind === "forward"));
		for (const s of after) {
			if (need <= 0 || s.kind === "note") break;
			if (s.duration <= need) {
				s.el.remove();
				need -= s.duration;
			} else {
				shorten(s, need, state.divisions);
				need = 0;
			}
		}
		const end = oldEnd + need;
		if (end > goal) trimEnd(measure, run, end - goal, state.divisions);
	} else if (oldEnd > goal) {
		const end = oldEnd + delta;
		if (end < goal) insertBeforeOrAppend(measure, runTail(measure, run), makeRests(doc, goal - end, state.divisions, slot.voice, textOf(slot.el, "staff")));
	} else {
		const last = slot.chord[slot.chord.length - 1];
		insertBeforeOrAppend(measure, last.nextElementSibling, makeRests(doc, -delta, state.divisions, slot.voice, textOf(slot.el, "staff")));
	}
	keepNextRunInPlace(measure, run, afterBoundary, boundary);
	rebeam(measure, run, state);
	return {
		xml: save(doc),
		select: nameOf(doc, found.el)
	};
}
/** Take a note out: one of a chord just goes; a note on its own becomes a rest as long. */
function deleteNote(xml, id) {
	const doc = load(xml);
	const found = find(doc, {
		kind: "note",
		id
	});
	const { el, measure } = found;
	const state = stateAt(found.part, el);
	const slot = slotOf(measure, el);
	const staff = textOf(el, "staff") ?? "1";
	const p = readPitch(el);
	untie(doc, found);
	if (slot.chord.length > 1) {
		const i = slot.chord.indexOf(el);
		if (i === 0) {
			const next = slot.chord[1];
			removeAll(next, "chord");
			for (const tag of ["beam", "lyric"]) if (!kids(next, tag).length) for (const c of kids(el, tag)) place(next, c);
		}
		el.remove();
		respell(measure, staff, state.fifths, /* @__PURE__ */ new Set([`${p.step}${p.octave}`]));
		const stays = slot.chord[i === 0 ? 1 : i - 1];
		return {
			xml: save(doc),
			select: nameOf(doc, stays)
		};
	}
	kid(el, "pitch")?.replaceWith(make(doc, "rest"));
	for (const tag of [
		"tie",
		"accidental",
		"stem",
		"notehead",
		"notehead-text",
		"beam",
		"lyric",
		"instrument",
		"play",
		"listen"
	]) removeAll(el, tag);
	for (const n of kids(el, "notations")) {
		for (const c of Array.from(n.children)) if (c.tagName !== "tuplet") c.remove();
		if (!n.children.length) n.remove();
	}
	respell(measure, staff, state.fifths, /* @__PURE__ */ new Set([`${p.step}${p.octave}`]));
	rebeam(measure, slot.run, state);
	return {
		xml: save(doc),
		select: nameOf(doc, el)
	};
}
/** The pitch a new note in a voice starts at: the note before it in its voice, or the middle of the staff. */
function startingPitch(found, state, slot) {
	const staff = textOf(found.el, "staff") ?? "1";
	const near = scanMeasure(found.measure).filter((s) => s.kind === "note" && s.voice === slot.voice && (textOf(s.el, "staff") ?? "1") === staff);
	const before = near.filter((s) => s.start < slot.start).pop() ?? near.find((s) => s.start > slot.start);
	if (before) return readPitch(before.el);
	const clef = state.clefs.get(Number(staff)) ?? {
		sign: "G",
		line: 2,
		octave: 0
	};
	const middle = clef.sign === "F" ? {
		step: "D",
		octave: 3,
		alter: 0
	} : clef.sign === "C" ? {
		step: "C",
		octave: 4,
		alter: 0
	} : {
		step: "B",
		octave: 4,
		alter: 0
	};
	return {
		...middle,
		octave: middle.octave + clef.octave
	};
}
/** Turn a rest into a note as long, at the pitch of the note before it in its voice. */
function restToNote(xml, id) {
	const doc = load(xml);
	const found = find(doc, {
		kind: "rest",
		id
	});
	const { el, measure } = found;
	const state = stateAt(found.part, el);
	const slot = slotOf(measure, el);
	const p = startingPitch(found, state, slot);
	const staff = textOf(el, "staff") ?? "1";
	kid(el, "rest")?.replaceWith(make(doc, "pitch"));
	writePitch(el, {
		...p,
		alter: impliedAlter(measure, staff, state.fifths, slot.start, el, p.step, p.octave)
	});
	if (!kid(el, "type") || !noteValue(slot.duration / state.divisions)) {
		const first = splitValues(slot.duration / state.divisions)?.[0];
		if (first) {
			const d = Math.round(first.quarters * state.divisions);
			setLengthOf(el, d, state.divisions);
			if (d < slot.duration) insertBeforeOrAppend(measure, el.nextElementSibling, makeRests(doc, slot.duration - d, state.divisions, slot.voice, textOf(el, "staff")));
		}
	}
	respell(measure, staff, state.fifths, /* @__PURE__ */ new Set([`${p.step}${p.octave}`]));
	rebeam(measure, slot.run, state);
	return {
		xml: save(doc),
		select: nameOf(doc, el)
	};
}
/** Add a note to a note's chord: a third above it (or the next free step up). */
function addChordNote(xml, id) {
	const doc = load(xml);
	const found = find(doc, {
		kind: "note",
		id
	});
	const { el, measure } = found;
	const state = stateAt(found.part, el);
	const slot = slotOf(measure, el);
	const staff = textOf(el, "staff") ?? "1";
	const taken = new Set(slot.chord.map((n) => {
		const q = readPitch(n);
		return `${q.step}${q.octave}`;
	}));
	const p = readPitch(el);
	let i = STEPS.indexOf(p.step);
	let octave = p.octave;
	let step = p.step;
	do {
		i += 2;
		if (i > 6) {
			i -= 7;
			octave++;
		}
		step = STEPS[i];
	} while (taken.has(`${step}${octave}`));
	const added = el.cloneNode(true);
	for (const tag of [
		"chord",
		"tie",
		"accidental",
		"notehead",
		"notehead-text",
		"beam",
		"notations",
		"lyric"
	]) removeAll(added, tag);
	place(added, make(doc, "chord"));
	writePitch(added, {
		step,
		octave,
		alter: impliedAlter(measure, staff, state.fifths, slot.start, el, step, octave)
	});
	slot.chord[slot.chord.length - 1].after(added);
	respell(measure, staff, state.fifths, /* @__PURE__ */ new Set([`${step}${octave}`]));
	return {
		xml: save(doc),
		select: nameOf(doc, added)
	};
}
/** What each voice of each bar adds up to, in quarters, against its time signature: for tests and checks. */
function voiceLengths(xml) {
	const doc = load(xml);
	const out = [];
	kids(doc.documentElement, "part").forEach((part, pi) => {
		const state = {
			divisions: 1,
			beats: 4,
			beatType: 4,
			fifths: 0,
			clefs: /* @__PURE__ */ new Map()
		};
		kids(part, "measure").forEach((m, mi) => {
			for (const a of kids(m, "attributes")) applyAttributes(state, a);
			const ends = /* @__PURE__ */ new Map();
			for (const s of scanMeasure(m)) if (s.kind === "note" || s.kind === "rest" || s.kind === "forward") ends.set(s.voice, Math.max(ends.get(s.voice) ?? 0, s.start + s.duration));
			for (const [voice, end] of ends) out.push({
				part: pi,
				measure: mi,
				voice,
				length: end / state.divisions,
				bar: barDivisions(state) / state.divisions
			});
		});
	});
	return out;
}
/** Undo for a run of edits: the texts before each. */
var EditHistory = class {
	past = [];
	current;
	constructor(current) {
		this.current = current;
	}
	get canUndo() {
		return this.past.length > 0;
	}
	/** How many edits there are to undo. */
	get count() {
		return this.past.length;
	}
	push(xml) {
		if (xml === this.current) return;
		this.past.push(this.current);
		this.current = xml;
	}
	undo() {
		const prev = this.past.pop();
		if (prev === void 0) return null;
		this.current = prev;
		return prev;
	}
};
//#endregion
//#region ../midi_studio/packages/score-view/src/flags.ts
/** What the checks find: bars longer than their time signature allows. */
function checkFlags(xml, score = parseMusicXML(xml)) {
	return { bars: checkScore(xml, score).longBars };
}
/**
* Bars the score reader was unsure of, if it wrote them into the file. Provisional, until Score
* Reader writes them: `<identification><miscellaneous><miscellaneous-field name="doubtful-measures">`
* holding bar positions from 1, separated by spaces ("3 7 12"). Standard MusicXML, which other
* programs ignore.
*/
function readerFlags(xml) {
	const doc = new DOMParser().parseFromString(xml, "application/xml");
	const bars = (Array.from(doc.getElementsByTagName("miscellaneous-field")).find((f) => f.getAttribute("name") === "doubtful-measures")?.textContent ?? "").split(/\s+/).map(Number).filter((n) => Number.isInteger(n) && n > 0).map((n) => n - 1);
	return bars.length ? { bars } : {};
}
/** Several sets of flags as one. */
function mergeFlags(...all) {
	const bars = /* @__PURE__ */ new Set();
	const notes = /* @__PURE__ */ new Set();
	for (const f of all) {
		for (const b of f?.bars ?? []) bars.add(b);
		for (const n of f?.notes ?? []) notes.add(n);
	}
	return {
		bars: [...bars].sort((a, b) => a - b),
		notes: [...notes]
	};
}
//#endregion
//#region ../midi_studio/packages/score-view/src/style.ts
/**
* The view's own look: selected and flagged notes and bars. Colours are CSS variables, so a page
* can set its own: --score-select, --score-flag, --score-flag-bar.
*/
const SCORE_VIEW_CSS = `
.score-view .score-page g.note.selected, .score-view .score-page g.rest.selected, .score-view .score-page g.mRest.selected { color: var(--score-select, #1565c0); fill: var(--score-select, #1565c0); stroke: var(--score-select, #1565c0) }
.score-view .score-page g.note.selected .notehead, .score-view .score-page g.rest.selected, .score-view .score-page g.mRest.selected { filter: drop-shadow(0 0 2px var(--score-select, #1565c0)) }
.score-view g.note.flagged { color: var(--score-flag, #c2410c); fill: var(--score-flag, #c2410c); stroke: var(--score-flag, #c2410c) }
.score-view rect.flag-bar { fill: var(--score-flag-bar, rgba(234, 179, 8, 0.22)); stroke: none }
`;
const STYLE_ID = "score-view-style";
/** Add the view's look to the page, once. */
function addScoreViewStyle(doc = document) {
	if (doc.getElementById(STYLE_ID)) return;
	const style = doc.createElement("style");
	style.id = STYLE_ID;
	style.textContent = SCORE_VIEW_CSS;
	doc.head.prepend(style);
}
//#endregion
//#region ../midi_studio/packages/score-view/src/view.ts
/** Redraw when the width changes by more than this: less doesn't change the layout much. */
const REDRAW_PX = 40;
function createScoreView(container, options) {
	const doc = container.ownerDocument;
	container.classList.add("score-view");
	addScoreViewStyle(doc);
	let xml = "";
	let score = null;
	let width = 0;
	let seq = 0;
	let flags = null;
	let selected = null;
	let notes = /* @__PURE__ */ new Map();
	let rests = /* @__PURE__ */ new Map();
	let targets = /* @__PURE__ */ new Map();
	let measures = [];
	const status = (drawing, error = null) => options.onStatus?.({
		drawing,
		error
	});
	async function draw() {
		if (!xml || !width || !score) return;
		const mine = ++seq;
		status(true);
		try {
			const result = await options.engrave({
				xml,
				width
			});
			if (mine !== seq) return;
			container.replaceChildren(...result.pages.map((svg) => {
				const page = doc.createElement("div");
				page.className = "score-page";
				page.innerHTML = svg;
				return page;
			}));
			measures = Array.from(container.querySelectorAll("g.measure"));
			const measureIds = measures.map((m) => m.id);
			const measureQ = new Map(result.measureQ);
			const byId = (id) => container.querySelector(`[id="${id}"]`);
			notes = /* @__PURE__ */ new Map();
			rests = /* @__PURE__ */ new Map();
			targets = /* @__PURE__ */ new Map();
			for (const [note, drawn] of linkNotes(score, drawnNotes(container), new Map(result.noteQ), measureQ, measureIds)) {
				const el = byId(drawn);
				if (!el) continue;
				notes.set(note, el);
				if (!targets.has(el)) targets.set(el, {
					kind: "note",
					id: note
				});
			}
			for (const [rest, drawn] of linkRests(writtenRests(xml), drawnRests(container), new Map(result.restQ ?? []), measureQ, measureIds)) {
				const el = byId(drawn);
				if (el) {
					rests.set(rest, el);
					targets.set(el, {
						kind: "rest",
						id: rest
					});
				}
			}
			paintFlags();
			paintSelection();
			status(false);
			options.onDraw?.();
		} catch (e) {
			if (mine === seq) status(false, e instanceof Error ? e.message : String(e));
		}
	}
	function measureWidth() {
		const w = Math.round(container.clientWidth);
		if (Math.abs(w - width) > REDRAW_PX || !width && w) {
			width = w;
			draw();
		}
	}
	const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(measureWidth) : null;
	observer?.observe(container);
	function paintFlags() {
		container.querySelectorAll(".flagged").forEach((el) => el.classList.remove("flagged"));
		container.querySelectorAll("rect.flag-bar").forEach((el) => el.remove());
		for (const i of flags?.bars ?? []) {
			const m = measures[i];
			if (!m) continue;
			m.classList.add("flagged");
			try {
				const boxes = Array.from(m.querySelectorAll(":scope > g.staff")).map((s) => s.getBBox());
				if (!boxes.length) continue;
				const x = Math.min(...boxes.map((b) => b.x));
				const y = Math.min(...boxes.map((b) => b.y));
				const right = Math.max(...boxes.map((b) => b.x + b.width));
				const bottom = Math.max(...boxes.map((b) => b.y + b.height));
				const pad = (bottom - y) * .06;
				const rect = doc.createElementNS("http://www.w3.org/2000/svg", "rect");
				rect.setAttribute("class", "flag-bar");
				rect.setAttribute("x", String(x - pad));
				rect.setAttribute("y", String(y - pad));
				rect.setAttribute("width", String(right - x + 2 * pad));
				rect.setAttribute("height", String(bottom - y + 2 * pad));
				m.insertBefore(rect, m.firstChild);
			} catch {}
		}
		for (const id of flags?.notes ?? []) notes.get(id)?.classList.add("flagged");
	}
	function drawnOf(target) {
		if (!target) return null;
		return (target.kind === "note" ? notes : rests).get(target.id) ?? null;
	}
	function paintSelection() {
		container.querySelectorAll(".selected").forEach((el) => el.classList.remove("selected"));
		drawnOf(selected)?.classList.add("selected");
	}
	const onClick = (e) => {
		const target = e.target;
		let hit = target.closest?.("g.note, g.rest, g.mRest") ?? null;
		if (hit && !targets.has(hit)) hit = null;
		if (!hit) {
			const candidates = Array.from(target.closest?.("g.measure")?.querySelectorAll("g.note, g.rest, g.mRest") ?? []).filter((n) => targets.has(n));
			let best = Infinity;
			for (const n of candidates) {
				const r = n.getBoundingClientRect();
				const d = Math.abs(r.left + r.width / 2 - e.clientX);
				if (d < best) {
					best = d;
					hit = n;
				}
			}
		}
		options.onTap?.(hit ? targets.get(hit) ?? null : null, e);
	};
	container.addEventListener("click", onClick);
	return {
		async setXml(next, nextScore) {
			xml = next;
			try {
				score = nextScore ?? parseMusicXML(next);
			} catch (e) {
				score = null;
				status(false, e instanceof Error ? e.message : String(e));
				return;
			}
			if (!width) width = Math.round(container.clientWidth) || (observer ? 0 : 800);
			await draw();
		},
		drawn: drawnOf,
		get notes() {
			return notes;
		},
		highlight(next) {
			flags = next;
			paintFlags();
		},
		select(target) {
			selected = target;
			paintSelection();
		},
		get selected() {
			return selected;
		},
		destroy() {
			seq++;
			observer?.disconnect();
			container.removeEventListener("click", onClick);
			container.replaceChildren();
			container.classList.remove("score-view");
		}
	};
}
//#endregion
export { EditHistory, SCORE_VIEW_CSS, addChordNote, addScoreViewStyle, barLength, checkFlags, checkScore, createEngraver, createScoreView, deleteNote, drawnNotes, drawnRests, engraveScore, isWrittenNote, keyAlter, linkNotes, linkRests, mergeFlags, noteKey, noteValue, octaveDown, parseMusicXML, readScoreFile, readVoiceName, readerFlags, restToNote, scaleFor, serveEngraving, setAlter, setLength, splitLongBars, splitValues, stepNote, tenorsInTreble, unzipMxl, valueLength, voiceLengths, writtenRests };
