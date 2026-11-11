#!/usr/bin/env python3
"""ROUND 49 (Section 43 clean build): strip DIAG14-DIAG48 diagnostic prints.

The DIAG prints were added deliberately through Sections 19-42 for
re-verifiability. The clean build removes them all, keeping every real
fix (the ROUND fixes, shim fixes, classlib patches, MxlWriter,
pre-rendered templates/classifier/metrics, policy entries, and the
indentations=false constant).

How it works
------------
make_patches.py regenerates patched/src from scratch on every build, so
the strip runs as ROUND 49 at the END of make_patches.py, after the
prune step. A future diagnostic ROUND must be inserted BEFORE the
ROUND 49 call, or its prints will be stripped too.

Diagnostic builds (§44.2): set TEAVM_KEEP_DIAG to the DIAG number to
keep (e.g. TEAVM_KEEP_DIAG=50) when running make_patches.py. The strip
then removes every other DIAG print but keeps that number's prints, so
the diagnostic build carries exactly one round's prints. Default
(unset): strip everything, as before. The post-strip verification is
unaffected: kept prints live inside string literals, which the
leftover-code check blanks. To ship clean, remove the diagnostic ROUND
(or just leave it: the default build strips its prints too).

Two tiers:
  1. Generic print removal (all files): every System.out.print/println/
     printf statement whose text contains "DIAG<digit>" is removed, plus
     the StringBuilder-println statements in TupletsBuilder/SlursBuilder
     (println(sb.toString()) / println(d46sb/d47sb/d46ab.toString())),
     which are DIAG44/45/46 dumps whose label lives in the builder, not
     in the println call.
  2. Targeted scaffolding removal (specific files): helper methods,
     fields, counting blocks and accounting statements that exist ONLY
     to feed the DIAG prints. Each removal asserts its expected count —
     if a future ROUND changes the DIAG code, the strip fails loudly
     here instead of silently leaving dead scaffolding (or silently
     removing live code). Update this file when the DIAG code changes.

What is KEPT, deliberately:
  * Operational prints in TeavmMain (IMAGE, GREY BYTES, REACH, MXL len=,
    TEAVM DONE/FAILED, ...) — progress reporting the runner reads.
    (TeavmMain's DIAG blocks are stripped by direct edit in entry/src,
    not here — this script only touches patched/src.)
  * Stock Audiveris prints (Table/Template printf dumps, MetronomeInter
    main() test code, Main/CLI output, WellKnowns error print,
    Sheet.dumpSystemInfos) — never called in the pipeline path.
  * DIAG mentions inside // comments — documentation of why a fix
    exists (e.g. the Section 30 comment in PageCleaner.visit, the
    Section 34 comment in MxlWriter's sort comparator). The final
    verification ignores comments.
  * PreRenderedTemplates' "requested N maps to desktop catalog M" line
    (entry/src, not a DIAG print): one line per catalog pair, same
    character as the other operational progress lines. The Section 41
    tripwire it served is done; the catalog mapping is now verified by
    the Section 36 round-trip.
  * diag45lineY/diag45toLine in SlursBuilder: the DIAG45B print block
    is removed, but the two variables are used by the REAL purge-gate
    test (abs(diag45toLine) > params.maxStaffLineDy) — they stay.

What is NOT in scope here: the desktop harness (teavm-fork/phase23/src)
keeps its own DIAG prints; it is a diagnostic harness, not the build.
TeavmMainDiag.java (entry/src) is deleted outright — a standalone
diagnostic copy of TeavmMain, referenced nowhere.

Usage: python3 strip_diag.py [patched/src] [--dry-run]
Exit code: 0 if the tree is clean after stripping, 1 otherwise.
"""

import os
import pathlib
import re
import sys

# §44.2: diagnostic builds keep one named DIAG number (see docstring).
# TEAVM_KEEP_DIAG is a comma-separated list of numbers, e.g. "50".
_KEEP_NUMS = [n.strip() for n in os.environ.get("TEAVM_KEEP_DIAG", "").split(",")]
KEEP_DIAG = frozenset('"DIAG' + n for n in _KEEP_NUMS if n)

DIAG_STR = re.compile(r'"DIAG[0-9]')
BUILDER_PRINT = re.compile(
    r'System\.out\.println\((sb|d46sb|d47sb|d46ab)\.toString\(\)\);')
PRINT_CALL = re.compile(r'System\.out\.(print|println|printf)\s*\(')
IDENT = re.compile(r'diag[0-9]')
DIAG_ANY = re.compile(r'DIAG[0-9]')


# ------------------------------------------------------------------ scanner
def scan_statement(text, start):
    """Return the index just past the ';' terminating the statement whose
    call starts at text[start] (the 'System.out...' call). String, char,
    line-comment and block-comment aware."""
    i = text.index('(', start)
    depth = 0
    j = i
    in_str = in_ch = esc = False
    in_line = in_block = False
    while j < len(text):
        c = text[j]
        n = text[j + 1] if j + 1 < len(text) else ''
        if in_line:
            if c == '\n':
                in_line = False
        elif in_block:
            if c == '*' and n == '/':
                in_block = False
                j += 1
        elif in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        elif in_ch:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == "'":
                in_ch = False
        else:
            if c == '/' and n == '/':
                in_line = True
            elif c == '/' and n == '*':
                in_block = True
            elif c == '"':
                in_str = True
            elif c == "'":
                in_ch = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            # §45: '<=' not '==': a print can be the last expression of an
            # enclosing call (e.g. forEach(e -> System.out.printf(...)); in
            # AbstractPitchedInter), where an extra ')' precedes the ';'.
            # That ';' still terminates the statement. For all previously
            # stripped files depth never went negative at a ';', so this
            # changes nothing there.
            elif c == ';' and depth <= 0:
                return j + 1
        j += 1
    raise ValueError("unterminated statement at offset %d" % start)


def find_code_print_calls(text):
    """Yield the start offsets of System.out.print/println/printf calls
    that occur in CODE (not inside a comment or a string/char literal).
    Single pass, string/char/comment aware."""
    i = 0
    n = len(text)
    in_str = in_ch = esc = False
    in_line = in_block = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_line:
            if c == '\n':
                in_line = False
            i += 1
        elif in_block:
            if c == '*' and nxt == '/':
                in_block = False
                i += 2
            else:
                i += 1
        elif in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            i += 1
        elif in_ch:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == "'":
                in_ch = False
            i += 1
        else:
            if c == '/' and nxt == '/':
                in_line = True
                i += 2
            elif c == '/' and nxt == '*':
                in_block = True
                i += 2
            elif c == '"':
                in_str = True
                i += 1
            elif c == "'":
                in_ch = True
                i += 1
            else:
                m = PRINT_CALL.match(text, i)
                if m:
                    yield m.start()
                    i = m.end()
                else:
                    i += 1


def strip_print_statements(text, basename):
    """Tier 1: remove DIAG System.out print statements. Returns
    (new_text, [labels removed])."""
    out = []
    removed = []
    pos = 0
    for start in find_code_print_calls(text):
        end = scan_statement(text, start)
        stmt = text[start:end]
        is_diag = bool(DIAG_STR.search(stmt))
        # §44.2: a diagnostic build keeps one named DIAG number.
        if is_diag and any(k in stmt for k in KEEP_DIAG):
            continue
        is_builder = (basename in ('TupletsBuilder.java', 'SlursBuilder.java')
                      and bool(BUILDER_PRINT.fullmatch(stmt)))
        if not (is_diag or is_builder):
            continue
        line_start = text.rfind('\n', 0, start) + 1
        if text[line_start:start].strip():
            raise ValueError(
                "%s: DIAG print shares a line with code: %r"
                % (basename, text[line_start:start + 60]))
        removed.append(stmt.split('\n')[0].strip()[:110])
        out.append(text[pos:line_start])
        line_end = text.find('\n', end)
        if line_end == -1:
            pos = end
        elif text[end:line_end].strip() == '':
            pos = line_end + 1
        else:
            pos = end
    out.append(text[pos:])
    return ''.join(out), removed


# ------------------------------------------------------- brace/text helpers
def strip_comments_strings(text):
    """Return text with // and /* */ comments and string/char literals
    blanked (newlines preserved), for the leftover-code check."""
    res = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if c == '/' and nxt == '/':
            while i < n and text[i] != '\n':
                res.append(' ')
                i += 1
        elif c == '/' and nxt == '*':
            res.append(' ')
            res.append(' ')
            i += 2
            while i < n and not (text[i] == '*' and i + 1 < n
                                 and text[i + 1] == '/'):
                res.append('\n' if text[i] == '\n' else ' ')
                i += 1
            if i < n:
                res.append(' ')
                res.append(' ')
                i += 2
        elif c == '"':
            res.append(' ')
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\' and i + 1 < n:
                    res.append(' ')
                    res.append(' ')
                    i += 2
                else:
                    res.append('\n' if text[i] == '\n' else ' ')
                    i += 1
            if i < n:
                res.append(' ')
                i += 1
        elif c == "'":
            res.append(' ')
            i += 1
            while i < n and text[i] != "'":
                if text[i] == '\\' and i + 1 < n:
                    res.append(' ')
                    res.append(' ')
                    i += 2
                else:
                    res.append(' ')
                    i += 1
            if i < n:
                res.append(' ')
                i += 1
        else:
            res.append(c)
            i += 1
    return ''.join(res)


def find_matching_brace(text, open_idx):
    """open_idx points at '{'. Return the index of the matching '}'.
    String/char/comment aware."""
    depth = 0
    i = open_idx
    n = len(text)
    in_str = in_ch = esc = False
    in_line = in_block = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_line:
            if c == '\n':
                in_line = False
        elif in_block:
            if c == '*' and nxt == '/':
                in_block = False
                i += 1
        elif in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        elif in_ch:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == "'":
                in_ch = False
        else:
            if c == '/' and nxt == '/':
                in_line = True
            elif c == '/' and nxt == '*':
                in_block = True
            elif c == '"':
                in_str = True
            elif c == "'":
                in_ch = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("unbalanced braces from offset %d" % open_idx)


def remove_range(text, start, end, what):
    """Remove text[start:end]; the range must start at a line start and
    end just before a newline (whole lines)."""
    assert start == 0 or text[start - 1] == '\n', what
    assert end == len(text) or text[end] == '\n', what
    return text[:start] + text[end + 1 if end < len(text) else end:]


def line_start_of(text, idx):
    return text.rfind('\n', 0, idx) + 1


def remove_lines_matching(text, pattern, expected, what):
    """Remove every whole line matching pattern (a regex on the line
    content). Fail unless exactly `expected` lines are removed."""
    lines = text.split('\n')
    kept = []
    removed = 0
    for line in lines:
        if pattern.search(line):
            removed += 1
        else:
            kept.append(line)
    if removed != expected:
        raise ValueError("%s: expected %d lines, removed %d"
                         % (what, expected, removed))
    return '\n'.join(kept), removed


def remove_method(text, method_name, what):
    """Remove a private method (with its directly preceding // DIAG
    comment lines) by name. Fail unless exactly one definition exists."""
    sig_re = (r'(?m)^(\s*)(private\s+\w[\w\s<>\[\],]*?\b'
              + re.escape(method_name)
              + r'\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{)')
    defs = re.findall(sig_re, text)
    if len(defs) != 1:
        raise ValueError("%s: method %s defined %d times"
                         % (what, method_name, len(defs)))
    m = re.search(sig_re, text)
    start = m.start()
    # extend back over directly preceding // DIAG comment lines
    while True:
        ls = line_start_of(text, start)
        prev_end = ls - 1
        if prev_end <= 0:
            break
        prev_start = line_start_of(text, prev_end)
        prev = text[prev_start:prev_end]
        if prev.strip().startswith('// DIAG'):
            start = prev_start
        else:
            break
    open_idx = text.index('{', m.start())
    close_idx = find_matching_brace(text, open_idx)
    end = close_idx + 1
    if end < len(text) and text[end] == '\n':
        end += 1
    return text[:start] + text[end:], 1


def remove_block_from_comment(text, comment_re, what, expected=1):
    """Remove every diagnostic block whose // comment matches comment_re:
    the comment line(s), then the next block (the first '{' after the
    comment), brace-matched to its close (extended over trailing
    catch/finally). Fail unless exactly `expected` blocks are removed."""
    removed = 0
    while True:
        m = re.search(comment_re, text)
        if not m:
            break
        start = line_start_of(text, m.start())
        # include following comment-continuation lines (// lines directly
        # after the first, that do not start a new DIAG label)
        pos = m.end()
        while True:
            nl = text.find('\n', pos)
            if nl == -1:
                break
            nls = nl + 1
            nle = text.find('\n', nls)
            nxt = text[nls:nle if nle != -1 else len(text)]
            if nxt.strip().startswith('//') and not re.search(r'DIAG[0-9]',
                                                              nxt):
                pos = nle if nle != -1 else len(text)
            else:
                break
        open_idx = text.index('{', pos)
        close_idx = find_matching_brace(text, open_idx)
        # Extend over trailing catch/finally blocks (a try's matching '}'
        # is the one before `catch`, not the end of the whole statement).
        while True:
            j = close_idx + 1
            while j < len(text) and text[j] in ' \t\n':
                j += 1
            if text[j:j + 5] == 'catch' or text[j:j + 7] == 'finally':
                b = text.index('{', j)
                close_idx = find_matching_brace(text, b)
            else:
                break
        end = close_idx + 1
        if end < len(text) and text[end] == '\n':
            end += 1
        text = text[:start] + text[end:]
        removed += 1
    if removed != expected:
        raise ValueError("%s: expected %d block(s), removed %d"
                         % (what, expected, removed))
    return text, removed

# ------------------------------------------------- targeted (tier 2) handlers
def strip_pagecleaner(text):
    """org/audiveris/omr/sheet/PageCleaner.java: DIAG36/37 scaffolding."""
    n = 0
    # Helper region: from the DIAG36 comment to just before @Override
    # of visit(HeadInter). Everything in it exists only for the DIAG36/37
    # counts (diag36Img, setDiag36Img, diag36Count/Pixels/Width/Height/
    # Index/Corner, diag37Snap/HeadsDumped/Index/InGlyphRun/InEllipse).
    m = re.search(r'(?m)^    // DIAG36 \(§31\): the live image', text)
    if not m:
        raise ValueError("PageCleaner: DIAG36 helper region not found")
    start = m.start()
    vm = re.search(r'(?m)^    public void visit \(HeadInter head\)', text)
    if not vm:
        raise ValueError("PageCleaner: visit(HeadInter) not found")
    ov = text.rfind('@Override', 0, vm.start())
    if ov == -1 or text[ov:vm.start()].strip() not in ('@Override',):
        raise ValueError("PageCleaner: @Override above visit not found")
    region = text[start:ov]
    for marker in ('diag37InEllipse', 'setDiag36Img', 'diag36Count'):
        if marker not in region:
            raise ValueError("PageCleaner: helper region lacks %s" % marker)
    text = text[:start] + text[ov:]
    n += 1
    # visit(HeadInter) accounting statements (each exactly once).
    pats = [
        (r'^        // DIAG36 \(§31\): per-head erasure accounting, print-only\.$', 1),
        (r'^        final int foreBefore = diag36Count\(rx0, ry0, rx1, ry1\);$', 1),
        (r'^        // DIAG37 \(§32\): widened snapshot window \(ellipse rect \+ 8 px\);$', 1),
        (r'^        // the paint glyph may extend past the glyph bounds\.$', 1),
        (r'^        final int wx0 = rx0 - 8;$', 1),
        (r'^        final int wy0 = ry0 - 8;$', 1),
        (r'^        final int wx1 = rx1 \+ 8;$', 1),
        (r'^        final int wy1 = ry1 \+ 8;$', 1),
        (r'^        final boolean\[\] diag37S[0-3] = diag37Snap\(wx0, wy0, wx1, wy1\);$', 4),
        (r'^        final int foreAfterPaint = diag36Count\(rx0, ry0, rx1, ry1\);$', 1),
        (r'^        final int foreAfterGlyph = diag36Count\(rx0, ry0, rx1, ry1\);$', 1),
        (r'^        final int cornerFore = diag36Corner\(rx0, ry0, rx1, ry1, cx, cy, w, h\);$', 1),
        (r'^        final int foreAfterEllipse = diag36Count\(rx0, ry0, rx1, ry1\);$', 1),
    ]
    for pat, exp in pats:
        text, c = remove_lines_matching(text, re.compile(pat), exp,
                                        "PageCleaner %s" % pat[:40])
        n += c
    # The DIAG37 classification block (comment + flat statement sequence
    # ending with the DIAG37P if) is removed by
    # strip_pagecleaner_classification, called after this function.
    return text, n


def strip_pagecleaner_classification(text):
    """The DIAG37 classification block is a flat statement sequence, not
    a single braced block: remove from its comment line through the
    closing brace of the trailing `if (diag37Px.length() > 0)`."""
    m = re.search(r'(?m)^        // DIAG37 \(§32\): paint-footprint classification, print-only\.',
                  text)
    if not m:
        raise ValueError("PageCleaner: DIAG37 classification comment not found")
    start = m.start()
    im = re.search(r'if \(diag37Px\.length\(\) > 0\) \{', text[start:])
    if not im:
        raise ValueError("PageCleaner: DIAG37P if not found")
    open_idx = text.index('{', start + im.start())
    close_idx = find_matching_brace(text, open_idx)
    end = close_idx + 1
    if end < len(text) and text[end] == '\n':
        end += 1
    return text[:start] + text[end:], 1


def strip_skeleton(text):
    """org/audiveris/omr/sheet/curve/Skeleton.java: DIAG34/35 helpers,
    call sites, and the DIAG35-REGION try/catch."""
    n = 0
    for method in ('diag34Dump', 'diag35DumpImg', 'diag35Band',
                   'diag35Erased'):
        text, c = remove_method(text, method, "Skeleton %s" % method)
        n += c
    # Call sites (each exactly once) + their attached DIAG34 comments.
    calls = [
        (r'^        // DIAG34 \(§29\): raw skeleton, before any erasing$', 1),
        (r'^        diag34Dump\("DIAG34A", buffer\);$', 1),
        (r'^        cleaner\.setDiag36Img\(img\);$', 1),
        (r'^        diag35Erased\("DIAG35-NONCROSS", nonCrossables\);$', 1),
        (r'^        diag35DumpImg\("DIAG35A", img\);$', 1),
        (r'^        diag35Erased\("DIAG35-CROSS", crossables\);$', 1),
        (r'^        diag35DumpImg\("DIAG35B", img\);$', 1),
        (r'^        diag35DumpImg\("DIAG35C", img\);$', 1),
        (r'^        diag35Band\("DIAG35C-BAND", new ByteProcessor\(img\), 179, 257\);$', 1),
        (r'^        // DIAG34 \(§29\): final skeleton buffer ArcRetriever walks$', 1),
        (r'^        diag34Dump\("DIAG34B", buf\);$', 1),
        (r'^        diag35Band\("DIAG35D-BAND", buf, 179, 257\);$', 1),
    ]
    for pat, exp in calls:
        text, c = remove_lines_matching(text, re.compile(pat), exp,
                                        "Skeleton %s" % pat[:40])
        n += c
    # DIAG35-REGION try/catch: computes segCount only for the print.
    text, c = remove_block_from_comment(
        text,
        r'// DIAG35 \(§30\): segment count of the distant-region area before fill',
        "Skeleton DIAG35-REGION try/catch")
    n += c
    return text, n


def strip_phase_vars(text, name, expected_assigns):
    """HeaderBuilder/KeyColumn: remove `String diagNNPhase = "entry";`
    and every `diagNNPhase = ...;` assignment (the prints that read the
    variable go through the generic pass)."""
    text, c1 = remove_lines_matching(
        text, re.compile(r'^\s*String %s = "entry";$' % name), 1,
        "%s decl" % name)
    text, c2 = remove_lines_matching(
        text, re.compile(r'^\s*%s = .*;$' % name), expected_assigns,
        "%s assigns" % name)
    return text, c1 + c2


def strip_tupletsbuilder(text):
    """org/audiveris/omr/sheet/rhythm/TupletsBuilder.java: DIAG44B,
    DIAG45A, DIAG46 blocks."""
    n = 0
    # DIAG44B braced block ("linked chords"): the other DIAG44B labels
    # in this file are single printlns, handled by the generic pass.
    text, c = remove_block_from_comment(
        text,
        r'// DIAG44B \(§38\): linked chords for this tuplet sign, print-only\.',
        "TupletsBuilder DIAG44B block", expected=1)
    n += c
    # DIAG45A braced block ("per-candidate staff/duration/members"): the
    # other DIAG45A labels here are single printlns, generic pass.
    text, c = remove_block_from_comment(
        text,
        r'// DIAG45A \(§39\): per-candidate staff/duration/members, print-only\.',
        "TupletsBuilder DIAG45A block", expected=1)
    n += c
    # DIAG46/47: `boolean diag46 = ...` gates TWO `if (diag46)` blocks
    # (the filterList/member dump at line ~256 and the pair comparison
    # at line ~322). Remove both blocks, then the declaration.
    n_if = 0
    while True:
        im = re.search(r'(?m)^(\s*)if \(diag46\) \{', text)
        if not im:
            break
        start = im.start()
        open_idx = text.index('{', im.start())
        close_idx = find_matching_brace(text, open_idx)
        end = close_idx + 1
        if end < len(text) and text[end] == '\n':
            end += 1
        text = text[:start] + text[end:]
        n_if += 1
    if n_if != 2:
        raise ValueError("TupletsBuilder: expected 2 if (diag46) blocks, "
                         "removed %d" % n_if)
    n += n_if
    text, c = remove_lines_matching(
        text,
        re.compile(r'^        boolean diag46 = .*$'),
        1, "TupletsBuilder diag46 decl")
    n += c
    return text, n


def strip_slursbuilder(text):
    """org/audiveris/omr/sheet/curve/SlursBuilder.java: DIAG45B and
    DIAG46A blocks. diag45lineY/diag45toLine STAY — the purge gate reads
    them (abs(diag45toLine) > params.maxStaffLineDy)."""
    n = 0
    text, c = remove_block_from_comment(
        text,
        r'// DIAG45B \(§39\): purge gate inputs for every candidate that',
        "SlursBuilder DIAG45B")
    n += c
    text, c = remove_block_from_comment(
        text,
        r'// DIAG46A \(§40\): staff-line fit \+ arc points for the P2 m9',
        "SlursBuilder DIAG46A")
    n += c
    return text, n


def strip_stemscaler(text):
    """org/audiveris/omr/sheet/stem/StemScaler.java: diag31Segs method
    and the diag31t0 timer."""
    text, c = remove_method(text, 'diag31Segs', "StemScaler diag31Segs")
    n = c
    text, c = remove_lines_matching(
        text,
        re.compile(r'^        // DIAG31 \(§26 GH follow-up\): bracket the StemScaler stall$'),
        1, "StemScaler DIAG31 bracket comment")
    n += c
    text, c = remove_lines_matching(
        text,
        re.compile(r'^        final long diag31t0 = System\.currentTimeMillis\(\);$'),
        1, "StemScaler diag31t0")
    n += c
    return text, n


def strip_ledgerspostanalysis(text):
    """org/audiveris/omr/sheet/ledger/LedgersPostAnalysis.java: the
    DIAG41 census block (comment + counters + for loop)."""
    return remove_block_from_comment(
        text,
        r'// DIAG41 \(§35\): per-staff ledger census, print-only\.',
        "LedgersPostAnalysis DIAG41 census")


def strip_beamsbuilder(text):
    """org/audiveris/omr/sheet/beam/BeamsBuilder.java: diag29/diag29small
    tally maps and their merge statements."""
    n = 0
    text, c = remove_lines_matching(
        text,
        re.compile(r'^        // DIAG29 \(§26 grid gap\): tally checkBeamGlyph failure reasons$'),
        1, "BeamsBuilder DIAG29 tally comment")
    n += c
    text, c = remove_lines_matching(
        text,
        re.compile(r'^        final java\.util\.Map<String, Integer> diag29(small)? = new java\.util\.LinkedHashMap<>\(\);$'),
        2, "BeamsBuilder diag29 maps")
    n += c
    # The merge statements sit inside `if (failure != null) { ... }`
    # blocks that exist only for the tally: remove each enclosing if.
    for var in ('diag29', 'diag29small'):
        m = re.search(re.escape(var) + r'\.merge\(', text)
        if not m:
            raise ValueError("BeamsBuilder: %s.merge not found" % var)
        im = text.rfind('if (failure != null) {', 0, m.start())
        if im == -1:
            raise ValueError("BeamsBuilder: enclosing if not found for %s" % var)
        open_idx = text.index('{', im)
        close_idx = find_matching_brace(text, open_idx)
        start = line_start_of(text, im)
        end = close_idx + 1
        if end < len(text) and text[end] == '\n':
            end += 1
        text = text[:start] + text[end:]
        n += 1
    return text, n


TARGETED = {
    'Skeleton.java': strip_skeleton,
    'HeaderBuilder.java': lambda t: strip_phase_vars(t, 'diag38Phase', 7),
    'KeyColumn.java': lambda t: strip_phase_vars(t, 'diag39Phase', 5),
    'TupletsBuilder.java': strip_tupletsbuilder,
    'SlursBuilder.java': strip_slursbuilder,
    'StemScaler.java': strip_stemscaler,
    'LedgersPostAnalysis.java': strip_ledgerspostanalysis,
    'BeamsBuilder.java': strip_beamsbuilder,
}


# Identifiers that legitimately survive the strip because REAL code
# reads them (not just the DIAG prints):
#   diag45lineY / diag45toLine (SlursBuilder): the purge-gate test
#   `abs(diag45toLine) > params.maxStaffLineDy` reads them; only the
#   DIAG45B print block that also read them is removed.
KEPT_IDENTS = {'diag45lineY', 'diag45toLine'}


def strip_file(path, dry_run=False):
    """Strip one file. Returns (changed, n_prints_removed, n_targeted)."""
    text = path.read_text()
    orig = text
    basename = path.name
    # Tier 2 first (blocks that contain prints), then tier 1 (stragglers).
    n_targeted = 0
    if basename == 'PageCleaner.java':
        text, _ = strip_pagecleaner(text)
        text, c = strip_pagecleaner_classification(text)
        n_targeted += c
    elif basename in TARGETED:
        text, n_targeted = TARGETED[basename](text)
    text, removed = strip_print_statements(text, basename)
    # Verification: no DIAG print and no diagNN identifier left in code.
    cleaned = strip_comments_strings(text)
    if DIAG_STR.search(cleaned):
        raise ValueError("%s: DIAG string remains in code" % basename)
    for m in IDENT.finditer(cleaned):
        ident = re.match(r'diag[0-9]\w*', cleaned[m.start():]).group(0)
        if ident not in KEPT_IDENTS:
            raise ValueError("%s: diagNN identifier remains in code: %r"
                             % (basename, cleaned[max(0, m.start() - 40):m.start() + 40]))
    changed = text != orig
    if changed and not dry_run:
        path.write_text(text)
    return changed, len(removed), n_targeted, removed


def strip_tree(out_dir, dry_run=False):
    """Strip every .java under out_dir. Prints a per-file report.
    Returns the number of files changed."""
    out_dir = pathlib.Path(out_dir)
    files = sorted(out_dir.rglob('*.java'))
    changed_files = 0
    total_prints = 0
    total_targeted = 0
    for path in files:
        changed, n_prints, n_targeted, removed = strip_file(path, dry_run)
        if changed:
            changed_files += 1
            total_prints += n_prints
            total_targeted += n_targeted
            print("  %s: %d print(s) removed, %d targeted removal(s)"
                  % (path.relative_to(out_dir), n_prints, n_targeted))
            for label in removed:
                print("      - %s" % label)
    print("STRIP %s: %d file(s) changed, %d print statement(s) removed, "
          "%d targeted removal(s)"
          % ("DRY-RUN" if dry_run else "DONE", changed_files, total_prints,
             total_targeted))
    return changed_files


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    target = pathlib.Path(args[0]) if args else pathlib.Path(__file__).resolve().parent / 'src'
    strip_tree(target, dry_run=dry)
