#!/usr/bin/env python3
"""Copy Audiveris 5.11 sources and apply TeaVM-0.16.0 patches.

Reads Audiveris's source with score-reader's patch applied (.work/audiveris, from ./setup.sh;
AUDIVERIS_SRC to read another) and writes the patched copies to .work/teavm/patched-src
(TEAVM_PATCHED_SRC to write elsewhere). teavm/build.sh runs it.

Patches (each marked TEAVM in the source):
  WellKnowns:      hard-code OS (no System.getenv/getProperty), dummy class container,
                   RES_URI null, getFolder -> null (no user folders in WASM).
  ConstantManager: UserHolder path -> null (no user.properties file).
  Constant:        Color.decodeColor -> manual hex parse (Color.decode missing in TeaVM).
  LogUtil:         minimal rewrite: all Logback/MDC methods are no-ops.
  StepMonitoring:  minimal rewrite: all Swing-monitor notifies are no-ops.
  LoadStep:        doit takes the image from teavm.TeavmImageHolder (JS-supplied bytes).
  OmrExecutors:    pools use no-arg Executors factories (no ThreadFactory/ThreadGroup),
                   cpuCount -> 1 (single-threaded inline executor).
  SheetStub:       doOneStep guards Main.getCli() == null (no CLI under TeaVM).
  ConstantSet:     unit name derived from own class name when the declaring
                   class has no getName() metadata under TeaVM (§11).
  BookManager:     Constants folder defaults null-safe (WellKnowns folders are
                   null in WASM, §11).
  AliasPatterns:   loadAliasPatterns skips null CONFIG_FOLDER / RES_URI (§11).
  UriUtil:         toURI(URI, String) names the child file when it throws
                   on a null parent (RES_URI is null here, §13).
  OmrFont:         createFont catches IllegalArgumentException from the res
                   lookup too, falling through to the platform font (§13).
  Book:            getStubsToUpgrade returns an empty set for a fresh book
                   (no book path, so no saved .omr project can exist; the
                   original logic would return empty anyway, but
                   getStubsWithTableFiles traps first on Main.getCli() (§12).
                   Books loaded from a project keep the original logic, so
                   the method behaves exactly as before on the desktop.
  FloodFiller:     fill rewritten as an iterative explicit-stack flood
                   fill (§16): same pixels as the recursive version, no
                   recursion, so it cannot overflow the Wasm call stack
                   in HEADS template building. Desktop-neutral (verified
                   pixel-identical on desktop, §16).
Later rounds (ROUND n below) add the rest: see teavm/FIXES.md for what each § is.
"""
import os, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]  # the score-reader checkout
REPO = pathlib.Path(os.environ.get("AUDIVERIS_SRC", ROOT / ".work/audiveris/app/src/main/java"))
OUT = pathlib.Path(os.environ.get("TEAVM_PATCHED_SRC", ROOT / ".work/teavm/patched-src"))

FILES = [
    "org/audiveris/omr/WellKnowns.java",
    "org/audiveris/omr/constant/ConstantManager.java",
    "org/audiveris/omr/constant/Constant.java",
    "org/audiveris/omr/log/LogUtil.java",
    "org/audiveris/omr/step/ui/StepMonitoring.java",
    "org/audiveris/omr/step/LoadStep.java",
    "org/audiveris/omr/util/OmrExecutors.java",
    "org/audiveris/omr/sheet/SheetStub.java",
    "org/audiveris/omr/constant/ConstantSet.java",
    "org/audiveris/omr/sheet/BookManager.java",
    "org/audiveris/omr/sheet/AliasPatterns.java",
    "org/audiveris/omr/util/UriUtil.java",
    "org/audiveris/omr/ui/symbol/OmrFont.java",
]

def replace_method(text, sig_pat, new_body, count=0):
    """Replace the body of the method matching sig_pat (regex) with new_body.

    new_body must be the full method text including signature and braces.
    count=0 replaces all occurrences."""
    pat = re.compile(sig_pat, re.S)
    out = []
    pos = 0
    n = 0
    while True:
        m = pat.search(text, pos)
        if not m:
            break
        # find opening brace after the signature start (signature itself has no braces)
        brace = text.index("{", m.start())
        depth = 0
        i = brace
        while True:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.append(text[pos:m.start()])
        out.append(new_body)
        pos = i + 1
        n += 1
        if count and n >= count:
            break
    out.append(text[pos:])
    if n == 0:
        raise SystemExit(f"PATCH FAILED: no match for {sig_pat}")
    print(f"  replaced {n}x: {sig_pat[:70]}")
    return "".join(out)

def sub(text, old, new, must=True):
    if old not in text:
        if must:
            raise SystemExit(f"PATCH FAILED: not found: {old[:90]}")
        print(f"  (skip, not found) {old[:70]}")
        return text
    print(f"  sub: {old[:70]}")
    return text.replace(old, new, 1)

# Files written by this run. §19: make_patches.py never cleaned OUT, so a
# removed round left a stale patched file behind (the §18 ClefBuilder
# glyph-bounds patch survived the §19 revert and was still compiled).
# The prune at the end of this script deletes any other .java under OUT.
WRITTEN = set()


def write(rel, text):
    WRITTEN.add(rel)
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    print(f"wrote {dst.relative_to(OUT.parent.parent)}")

# ---------------------------------------------------------------- WellKnowns
text = (REPO / FILES[0]).read_text()
text = sub(text, 'public static final String FLATPAK_ID = System.getenv("FLATPAK_ID");',
           'public static final String FLATPAK_ID = null; // TEAVM: no System.getenv')
text = sub(text, 'private static final String OS_NAME = System.getProperty("os.name").toLowerCase(Locale.ENGLISH);',
           'private static final String OS_NAME = "linux"; // TEAVM: no System.getProperty')
text = sub(text, 'public static final String OS_ARCH = System.getProperty("os.arch");',
           'public static final String OS_ARCH = "amd64"; // TEAVM')
text = sub(text, '''    public static final boolean WINDOWS_64 = WINDOWS && (System.getenv(
            "ProgramFiles(x86)") != null);''',
           '    public static final boolean WINDOWS_64 = false; // TEAVM: no System.getenv')
text = sub(text, 'public static final String FILE_ENCODING = getFileEncoding();',
           'public static final String FILE_ENCODING = "UTF-8"; // TEAVM')
text = sub(text, 'public static final boolean RUNNING_FROM_JAR = runningFromJar();',
           'public static final boolean RUNNING_FROM_JAR = false; // TEAVM')
text = sub(text, '''    public static final URI RES_URI = RUNNING_FROM_JAR ? toURI(
            WellKnowns.class.getClassLoader().getResource("res")) : Paths.get("res").toUri();''',
           '    public static final URI RES_URI = null; // TEAVM: no resources')
text = replace_method(text, r'private static URI getClassContainer \(\)',
    '''    private static URI getClassContainer ()
    {
        return URI.create("file:///teavm/"); // TEAVM: dummy container
    }''')
# getFolder: find its signature then replace body with "return null;"
m = re.search(r'(    private static Path getFolder \(FolderKind kind\)\s*\n    \{)', text)
if not m:
    raise SystemExit("PATCH FAILED: getFolder signature")
brace = text.index("{", m.start())
depth = 0; i = brace
while True:
    c = text[i]
    if c == "{": depth += 1
    elif c == "}":
        depth -= 1
        if depth == 0: break
    i += 1
text = text[:m.start()] + '''    private static Path getFolder (FolderKind kind)
    {
        return null; // TEAVM: no user folders in WASM
    }''' + text[i+1:]
print("  replaced getFolder body")
# TEAVM: getFolder returns null, but the derived folders dereference it
# (DATA_FOLDER.resolve("www") etc.) -- under TeaVM WasmGC a null receiver traps with
# RuntimeError: unreachable instead of throwing NPE. Make the derived folders null-safe,
# and make createFolder tolerate a null folder (LOG_FOLDER/TEMP_FOLDER are null too).
text = sub(text, 'public static final Path DOC_FOLDER = DATA_FOLDER.resolve("www");',
           'public static final Path DOC_FOLDER = (DATA_FOLDER == null) ? null : DATA_FOLDER.resolve("www"); // TEAVM: getFolder null')
text = sub(text, 'public static final Path EXAMPLES_FOLDER = DATA_FOLDER.resolve("examples");',
           'public static final Path EXAMPLES_FOLDER = (DATA_FOLDER == null) ? null : DATA_FOLDER.resolve("examples"); // TEAVM: getFolder null')
text = sub(text, 'public static final Path TRAIN_FOLDER = CONFIG_FOLDER.resolve("train");',
           'public static final Path TRAIN_FOLDER = (CONFIG_FOLDER == null) ? null : CONFIG_FOLDER.resolve("train"); // TEAVM: getFolder null')
text = sub(text, 'public static final Path TEMP_FOLDER = LOG_FOLDER.resolve("temp");',
           'public static final Path TEMP_FOLDER = (LOG_FOLDER == null) ? null : LOG_FOLDER.resolve("temp"); // TEAVM: getFolder null')
text = sub(text, '''    private static void createFolder (Path folder)
    {
        if (!Files.exists(folder)) {''',
           '''    private static void createFolder (Path folder)
    {
        if (folder == null) {
            return; // TEAVM: no user folders in WASM
        }

        if (!Files.exists(folder)) {''')
write(FILES[0], text)

# ------------------------------------------------------------ ConstantManager
text = (REPO / FILES[1]).read_text()
text = sub(text, 'new UserHolder(\n            WellKnowns.CONFIG_FOLDER.resolve(USER_FILE_NAME));',
           'new UserHolder(null); // TEAVM: no user.properties file')
# score-reader settings (app/settings.js READING): the page passes them as -constant name=value,
# which reach addConstant through Main.getCli(); TeaVM has no CLI, so TeavmMain fills this map
# before reading and addConstant consults it the same way.
text = sub(text, '''    protected final ConcurrentHashMap<String, Constant> constants = new ConcurrentHashMap<>();''',
           '''    protected final ConcurrentHashMap<String, Constant> constants = new ConcurrentHashMap<>();

    /** TEAVM: constant values set by TeavmMain, as -constant would set them (no CLI here). */
    public static final java.util.Map<String, String> TEAVM_CONSTANTS = new java.util.HashMap<>();''')
text = sub(text, '''        // Value set at CLI level?
        CLI cli = Main.getCli();''', '''        // TEAVM: value set by TeavmMain (in place of the CLI)?
        String teavmValue = TEAVM_CONSTANTS.get(qName);

        if (teavmValue != null) {
            return teavmValue;
        }

        // Value set at CLI level?
        CLI cli = Main.getCli();''')
write(FILES[1], text)

# ------------------------------------------------------------------- Constant
text = (REPO / FILES[2]).read_text()
text = replace_method(text, r'public static java\.awt\.Color decodeColor \(java\.lang\.String str\)',
    '''    public static java.awt.Color decodeColor (java.lang.String str)
    {
        // TEAVM: Color.decode is missing in TeaVM classlib; parse hex manually.
        java.lang.String s = str.trim();

        if (s.startsWith("#")) {
            s = s.substring(1);
        } else if (s.startsWith("0x") || s.startsWith("0X")) {
            s = s.substring(2);
        }

        return new java.awt.Color(java.lang.Integer.parseInt(s, 16));
    }''')
write(FILES[2], text)

# -------------------------------------------------------------------- LogUtil
# Minimal rewrite: same public surface used by the reading path, all no-ops.
write(FILES[3], '''package org.audiveris.omr.log;

import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.SheetStub;

import java.net.URI;
import java.nio.file.Path;

/**
 * TEAVM minimal LogUtil: Logback / MDC / Swing appenders are unavailable in WASM.
 * All methods are no-ops; logging goes through SLF4J (console) instead.
 */
public class LogUtil
{
    public static final String BOOK = "BOOK";
    public static final String SHEET = "SHEET";

    public static void addAppender (String name,
                                    Path logFolder)
    {
    }

    public static void addFileAppender ()
    {
    }

    public static void addGuiAppender ()
    {
    }

    public static String allInitialMessages ()
    {
        return "";
    }

    public static void initialize (Path CONFIG_FOLDER,
                                   URI RES_URI)
    {
    }

    public static void removeAppender (String name)
    {
    }

    public static void start (Book book)
    {
    }

    public static void start (SheetStub stub)
    {
    }

    public static void stopBook ()
    {
    }

    public static void stopStub ()
    {
    }
}
''')

# -------------------------------------------------------------- StepMonitoring
write(FILES[4], '''package org.audiveris.omr.step.ui;

import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.step.OmrStep;

/**
 * TEAVM minimal StepMonitoring: the Swing StepMonitor UI is unavailable in WASM.
 * All notifications are no-ops.
 */
public class StepMonitoring
{
    public static void animate ()
    {
    }

    public static StepMonitor createMonitor ()
    {
        return null;
    }

    public static void notifyMsg (String msg)
    {
    }

    public static void notifyStart ()
    {
    }

    public static void notifyStep (final SheetStub stub,
                                   final OmrStep step)
    {
    }

    public static void notifyStop ()
    {
    }
}
''')

# -------------------------------------------------------------------- LoadStep
text = (REPO / FILES[5]).read_text()
text = replace_method(text, r'public void doit \(Sheet sheet\)\s*\n\s*throws StepException',
    '''    public void doit (Sheet sheet)
        throws StepException
    {
        // TEAVM: the image comes from JS (grey bytes), not from a file via ImageIO.
        final java.awt.image.BufferedImage image = teavm.TeavmImageHolder.getImage();

        if (image == null) {
            throw new StepException("No image supplied from JS");
        }

        sheet.setImage(image, true);
    }''')
write(FILES[5], text)

# --------------------------------------------------------------- OmrExecutors
text = (REPO / FILES[6]).read_text()
text = sub(text, 'private static final int cpuCount = Runtime.getRuntime().availableProcessors();',
           'private static final int cpuCount = 1; // TEAVM: single-threaded')
# CachedLows pool
text = replace_method(text, r'protected ExecutorService createPool \(\)\s*\n\s*\{[^}]*newCachedThreadPool',
    '''        protected ExecutorService createPool ()
        {
            return Executors.newCachedThreadPool(); // TEAVM: no ThreadFactory
        }''')
# Highs + Lows pools (same shape, replace all remaining newFixedThreadPool factories)
text = replace_method(text, r'protected ExecutorService createPool \(\)\s*\n\s*\{[^}]*newFixedThreadPool\(',
    '''        protected ExecutorService createPool ()
        {
            return Executors.newFixedThreadPool(1); // TEAVM: no ThreadFactory
        }''')
write(FILES[6], text)

# ------------------------------------------------------------------ SheetStub
text = (REPO / FILES[7]).read_text()
text = sub(text, 'if ((OMR.gui == null) && Main.getCli().isSave()) {',
           'if ((OMR.gui == null) && (Main.getCli() != null) && Main.getCli().isSave()) { // TEAVM: cli may be null')
write(FILES[7], text)

# --------------------------------------------------------------- ConstantSet
# TEAVM §11: TeaVM generates class-name metadata only for types
# that flow into a Class.getName() call site; a declaring class reached only
# via getDeclaringClass() (e.g. Profiles) gets no name metadata, so
# getName() returns null and UnitManager.addSet() traps on the null unit.
# getClass().getName() DOES have metadata for the nested class itself, so
# derive the declaring name from it ("a.b.C$Constants" -> "a.b.C").
# On the desktop dc.getName() is never null, so behaviour is unchanged there.
text = (REPO / FILES[8]).read_text()
text = replace_method(text, r'public ConstantSet \(\)',
    '''    public ConstantSet ()
    {
        // TEAVM §11: declaring-class name metadata may be absent under TeaVM
        // (ClassMetadataRequirements only generates names for types flowing
        // into a getName() call site); derive it from our own class name.
        Class<?> dc = getClass().getDeclaringClass();
        String name = (dc != null) ? dc.getName() : null;

        if (name == null) {
            String cn = getClass().getName();
            int dollar = cn.indexOf('$');
            name = (dollar >= 0) ? cn.substring(0, dollar) : cn;
        }

        unit = name;

        //        System.out.println(
        //            "\\n" + Thread.currentThread().getName() +
        //            ": Creating ConstantSet " + unit);
        // Register this instance
        UnitManager.getInstance().addSet(this);
    }''')
write(FILES[8], text)

# --------------------------------------------------------------- BookManager
# TEAVM §11: BookManager$Constants initialises folder defaults from
# WellKnowns.DEFAULT_BASE_FOLDER / EXAMPLES_FOLDER, which are null in WASM
# (getFolder returns null). A null .toString() traps under TeaVM WasmGC.
text = (REPO / FILES[9]).read_text()
# DEFAULT_BASE_FOLDER appears twice (baseFolder, defaultBookFolder); plain
# replace() handles both at once (sub() would re-match inside its own
# replacement). Block comments: a // comment would eat the rest of the
# argument line.
_old = 'WellKnowns.DEFAULT_BASE_FOLDER.toString()'
_new = '(WellKnowns.DEFAULT_BASE_FOLDER == null) ? "" : WellKnowns.DEFAULT_BASE_FOLDER.toString() /* TEAVM §11: folder is null in WASM */'
assert text.count(_old) == 2, f"BookManager: expected 2 DEFAULT_BASE_FOLDER, got {text.count(_old)}"
text = text.replace(_old, _new)
text = sub(text, 'WellKnowns.EXAMPLES_FOLDER.toString()',
           '(WellKnowns.EXAMPLES_FOLDER == null) ? "" : WellKnowns.EXAMPLES_FOLDER.toString() /* TEAVM §11: folder is null in WASM */')
write(FILES[9], text)

# ------------------------------------------------------------- AliasPatterns
# TEAVM §11: loadAliasPatterns() builds its URI array by
# dereferencing WellKnowns.CONFIG_FOLDER and RES_URI, both null in WASM;
# the dereference happens outside the IOException catch and traps under
# TeaVM WasmGC. Build the list from whichever source is non-null.
text = (REPO / FILES[10]).read_text()
text = sub(text, '''            URI[] uris = new URI[] { WellKnowns.CONFIG_FOLDER.resolve(ALIAS_PATTERNS_FILENAME)
                    .toUri().normalize(), UriUtil.toURI(
                            WellKnowns.RES_URI,
                            ALIAS_PATTERNS_FILENAME) };''',
           '''            // TEAVM §11: CONFIG_FOLDER and RES_URI are null in WASM (no user
            // folders, no resources); build the URI list from whichever is
            // non-null instead of dereferencing them (a null receiver traps
            // under TeaVM WasmGC instead of throwing NPE).
            java.util.List<URI> uriList = new java.util.ArrayList<>();

            if (WellKnowns.CONFIG_FOLDER != null) {
                uriList.add(WellKnowns.CONFIG_FOLDER.resolve(ALIAS_PATTERNS_FILENAME)
                        .toUri().normalize());
            }

            if (WellKnowns.RES_URI != null) {
                uriList.add(UriUtil.toURI(WellKnowns.RES_URI, ALIAS_PATTERNS_FILENAME));
            }

            URI[] uris = uriList.toArray(new URI[0]);''')
write(FILES[10], text)

# ------------------------------------------------------------------ UriUtil
# Compiled from source here, as it is (in FILES for the copy).
text = (REPO / FILES[11]).read_text()
write(FILES[11], text)

# ------------------------------------------------------------------ OmrFont
# TEAVM §13: OmrFont.createFont looks the music font up in the "res"
# folder via UriUtil.toURI(WellKnowns.RES_URI, fileName) — but RES_URI is
# null in WASM (no resources), so toURI throws IllegalArgumentException
# ("Parent is null"), which the existing catch (MalformedURLException
# only) does not catch (MusicFont and the BEAMS step both ask for
# Bravura.otf). Catch the
# IllegalArgumentException too, so the res lookup fails the same way a
# missing res file fails and execution falls through to the platform
# font below — the code's existing fallback. Desktop-neutral: on the
# desktop RES_URI is never null and the res file exists, so this branch
# never triggers there.
text = (REPO / FILES[12]).read_text()
text = sub(text, '''            } catch (MalformedURLException ex) {
                logger.warn("MalformedURLException", ex);
            }''',
           '''            } catch (MalformedURLException | IllegalArgumentException ex) {
                // TEAVM §13: RES_URI is null in WASM, so toURI throws
                // IllegalArgumentException, not MalformedURLException.
                // Fall through to the platform font below.
                logger.warn("Could not load res font", ex);
            }''')
write(FILES[12], text)

print("All patches applied.")

# ============================================================ ROUND 2 =======
# UI pruning (delete OMR.gui branches so the Swing tree is never analyzed),
# Color/Point call-site fixes (TeaVM classlib lacks them), classifier stub,
# OCR neutering (post-HEADS step), PDFBox cut (loadGrayImage).
# ---------------------------------------------------------------------------

def delete_gui_block(text, needle):
    """Delete the `if (...OMR.gui...) { ... }` block containing needle
    (needle may be in the condition or in the block body)."""
    pat = re.compile(r'if\s*\([^\n]*OMR\.gui[^\n]*\)\s*\{')
    cands = list(pat.finditer(text))
    for m in cands:
        brace = text.index("{", m.start())
        depth = 0
        i = brace
        while True:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block_end = i + 1
        if m.start() <= text.index(needle) < block_end or needle in text[m.start():block_end]:
            # also swallow one trailing newline
            if block_end < len(text) and text[block_end] == "\n":
                block_end += 1
            print(f"  deleted OMR.gui block containing: {needle[:60]}")
            return text[:m.start()] + text[block_end:]
    raise SystemExit(f"PATCH FAILED: no OMR.gui block containing {needle[:80]}")

def sub_all(text, old, new, must=True):
    n = text.count(old)
    if n == 0 and must:
        raise SystemExit(f"PATCH FAILED: not found (all): {old[:90]}")
    print(f"  sub_all {n}x: {old[:70]}")
    return text.replace(old, new)

def copy_src(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit(f"PATCH FAILED: source missing {rel}")
    return p.read_text()

R2 = [
    "org/audiveris/omr/sheet/Sheet.java",
    "org/audiveris/omr/sheet/Book.java",
    "org/audiveris/omr/step/AbstractStep.java",
    "org/audiveris/omr/sheet/grid/GridBuilder.java",
    "org/audiveris/omr/sheet/stem/VerticalsBuilder.java",
    "org/audiveris/omr/sheet/ledger/LedgersFilter.java",
    "org/audiveris/omr/sheet/note/DistancesBuilder.java",
    "org/audiveris/omr/sheet/stem/StemChecker.java",
    "org/audiveris/omr/sheet/ledger/LedgersBuilder.java",
    "org/audiveris/omr/sheet/beam/SpotsBuilder.java",
    "org/audiveris/omr/sheet/curve/Curves.java",
    "org/audiveris/omr/sheet/SheetDiff.java",
    "org/audiveris/omr/sheet/grid/GridStep.java",
    "org/audiveris/omr/sheet/ledger/LedgersStep.java",
    "org/audiveris/omr/sheet/stem/StemSeedsStep.java",
    "org/audiveris/omr/sheet/symbol/SymbolsStep.java",
    "org/audiveris/omr/step/BinaryStep.java",
    "org/audiveris/omr/image/TemplateFactory.java",
    "org/audiveris/omr/image/DistanceTable.java",
    "org/audiveris/omr/ui/Colors.java",
    "org/audiveris/omr/sheet/key/KeyRoi.java",
    "org/audiveris/omr/sheet/curve/Skeleton.java",
    "org/audiveris/omr/sheet/curve/SegmentsBuilder.java",
    "org/audiveris/omr/sheet/stem/StemBuilder.java",
    "org/audiveris/omr/sig/inter/AbstractFlagInter.java",
    "org/audiveris/omr/sheet/curve/Curve.java",
    "org/audiveris/omr/text/OcrUtil.java",
    "org/audiveris/omr/sig/inter/NumberInter.java",
    "org/audiveris/omr/sig/inter/AbstractInter.java",
    "org/audiveris/omr/sig/inter/AbstractChordInter.java",
    "org/audiveris/omr/sheet/stem/HeadLinker.java",
    "org/audiveris/omr/sheet/stem/BeamLinker.java",
    "org/audiveris/omr/sheet/rhythm/TupletsBuilder.java",
    "org/audiveris/omr/sheet/curve/WedgesBuilder.java",
    "org/audiveris/omr/sheet/curve/SlurLinker.java",
    "org/audiveris/omr/classifier/ShapeClassifier.java",
    "org/audiveris/omr/classifier/BasicClassifier.java",
    "org/audiveris/omr/text/TextsStep.java",
    "org/audiveris/omr/sheet/PageCleaner.java",
]

# --- SheetStub: more pruning + loadGrayImage from holder (round 1 file) ---
text = (OUT / FILES[7]).read_text()
text = delete_gui_block(text, "assembly = new SheetAssembly(this);")
text = delete_gui_block(text, 'logger.debug("calling storeSheet");')
text = replace_method(text, r'public synchronized BufferedImage loadGrayImage \(\)',
    '''    public synchronized BufferedImage loadGrayImage ()
    {
        // TEAVM: the image comes from JS (grey bytes), not from a file via ImageIO.
        // (Also cuts the ImageLoading/PDFBox chain out of the reading path.)
        return teavm.TeavmImageHolder.getImage();
    }''')
write(FILES[7], text)

# --- Sheet: delete OMR.gui blocks ---
text = copy_src(R2[0])
text = delete_gui_block(text, 'locationService = new SelectionService("locationService", eventsAllowed);')
text = delete_gui_block(text, "getErrorsEditor().clearStep(step);")
write(R2[0], text)

# --- Book: setModified OMR.gui branch ---
text = copy_src(R2[1])
text = delete_gui_block(text, "StubsController.getInstance();")
write(R2[1], text)

# --- AbstractStep: clearErrors no-op ---
text = copy_src(R2[2])
text = replace_method(text, r'public void clearErrors \(OmrStep step,\s*\n\s*Sheet sheet\)',
    '''    public void clearErrors (OmrStep step,
                             Sheet sheet)
    {
        // TEAVM: no UI errors window.
    }''')
write(R2[2], text)

# --- GridBuilder / VerticalsBuilder: delete OMR.gui display blocks ---
text = copy_src(R2[3])
text = delete_gui_block(text, "sheet.getSheetEditor().refresh();")
write(R2[3], text)

text = copy_src(R2[4])
text = delete_gui_block(text, "sheet.getSheetEditor().refresh();")
write(R2[4], text)

# --- LedgersFilter / DistancesBuilder: delete OMR.gui display blocks ---
text = copy_src(R2[5])
text = delete_gui_block(text, "new LagController(sheet, lag, SheetTab.LEDGER_TAB).refresh();")
write(R2[5], text)

text = copy_src(R2[6])
text = delete_gui_block(text, "TemplateBoard templateBoard = new TemplateBoard")
write(R2[6], text)

# --- StemChecker / LedgersBuilder: addCheckBoard no-op ---
for rel in (R2[7], R2[8]):
    text = copy_src(rel)
    text = replace_method(text, r'public void addCheckBoard \(\)',
        '''    public void addCheckBoard ()
    {
        // TEAVM: no UI check board.
    }''')
    write(rel, text)

# --- SpotsBuilder: delete both OMR.gui blocks ---
text = copy_src(R2[9])
text = delete_gui_block(text, "new SpotsController(sheet, spots, spotLag)")
text = delete_gui_block(text, "displayGraySpots")
write(R2[9], text)

# --- Curves / SheetDiff: delete OMR.gui blocks ---
text = copy_src(R2[10])
text = delete_gui_block(text, "displayCurves")
write(R2[10], text)

text = copy_src(R2[11])
text = delete_gui_block(text, "SheetTab.DIFF_TAB")
write(R2[11], text)

# --- PageCleaner: copied verbatim; ROUND 33 (§30) patches visit(HeadInter) ---
text = copy_src(R2[38])
write(R2[38], text)

# --- displayUI overrides -> no-op (5 step classes) ---
for rel in (R2[12], R2[13], R2[14], R2[15], R2[16]):
    text = copy_src(rel)
    text = replace_method(text, r'public void displayUI \(OmrStep step,\s*\n\s*Sheet sheet\)',
        '''    public void displayUI (OmrStep step,
                           Sheet sheet)
    {
        // TEAVM: no UI.
    }''')
    write(rel, text)

# --- TemplateFactory: Color literals + binarize rewrite ---
text = copy_src(R2[17])
text = sub(text, "private static final int FORE = Color.YELLOW.getRGB();",
           "private static final int FORE = 0xFFFFFF00; // TEAVM: Color.YELLOW.getRGB()")
text = sub(text, "private static final int BACK = Color.WHITE.getRGB();",
           "private static final int BACK = 0xFFFFFFFF; // TEAVM: Color.WHITE.getRGB()")
text = sub(text, "private static final int HOLE = Color.PINK.getRGB();",
           "private static final int HOLE = 0xFFFFAFAF; // TEAVM: Color.PINK.getRGB()")
text = sub_all(text, "g.setColor(Color.GRAY);", "g.setColor(new Color(128, 128, 128)); // TEAVM")
text = sub_all(text, "g.setColor(Color.YELLOW);", "g.setColor(new Color(255, 255, 0)); // TEAVM")
text = sub_all(text, "g.setColor(Color.GREEN);", "g.setColor(new Color(0, 255, 0)); // TEAVM")
text = replace_method(text, r'private void binarize \(BufferedImage img,\s*\n\s*int threshold\)',
    '''        private void binarize (BufferedImage img,
                               int threshold)
        {
            // TEAVM: no Color(int, boolean) ctor / getRGB(); work on the ARGB int directly.
            for (int y = 0, h = img.getHeight(); y < h; y++) {
                for (int x = 0, w = img.getWidth(); x < w; x++) {
                    final int argb = img.getRGB(x, y);

                    if (((argb >> 24) & 0xFF) >= threshold) {
                        if (((argb >> 16) & 0xFF) >= threshold) {
                            img.setRGB(x, y, BACK);
                        } else {
                            img.setRGB(x, y, FORE);
                        }
                    } else {
                        img.setRGB(x, y, BACK);
                    }
                }
            }
        }''')
write(R2[17], text)

# --- DistanceTable: literals + rgb() helper (no Color.getRGB) ---
text = copy_src(R2[18])
text = sub(text, "Arrays.fill(data, Color.WHITE.getRGB()); // All white by default",
           "Arrays.fill(data, 0xFFFFFFFF); // All white by default // TEAVM")
text = sub(text, "lut[1 + VALUE_UNKNOWN] = Colors.DISTANCE_UNKNOWN.getRGB();",
           "lut[1 + VALUE_UNKNOWN] = rgb(Colors.DISTANCE_UNKNOWN); // TEAVM")
text = sub(text, "lut[1 + VALUE_TARGET] = Colors.DISTANCE_TARGET.getRGB();",
           "lut[1 + VALUE_TARGET] = rgb(Colors.DISTANCE_TARGET); // TEAVM")
text = sub(text, "lut[1 + i] = Color.WHITE.getRGB();",
           "lut[1 + i] = 0xFFFFFFFF; // TEAVM")
anchor = "        private int[] getLut (int rawDistMax)"
helper = """        // TEAVM: Color.getRGB() is missing in TeaVM classlib; compose from components.
        private static int rgb (Color c)
        {
            return (c.getAlpha() << 24) | (c.getRed() << 16) | (c.getGreen() << 8) | c.getBlue();
        }

"""
if anchor not in text:
    raise SystemExit("PATCH FAILED: DistanceTable getLut anchor")
text = text.replace(anchor, helper + anchor, 1)
write(R2[18], text)

# --- Colors: all Color.XXX constants -> new Color(r,g,b) ---
text = copy_src(R2[19])
RGB = {
    "LIGHT_GRAY": (192, 192, 192), "MAGENTA": (255, 0, 255), "PINK": (255, 175, 175),
    "RED": (255, 0, 0), "GREEN": (0, 255, 0), "CYAN": (0, 255, 255),
    "YELLOW": (255, 255, 0), "BLUE": (0, 0, 255), "GRAY": (128, 128, 128),
    "ORANGE": (255, 200, 0),
}
def _color_repl(m):
    r, g, b = RGB[m.group(1)]
    return f"new Color({r}, {g}, {b})"
text2, n = re.subn(r'Color\.(LIGHT_GRAY|MAGENTA|PINK|RED|GREEN|CYAN|YELLOW|BLUE|GRAY|ORANGE)', _color_repl, text)
print(f"  Colors: replaced {n} Color constants")
text = text2
write(R2[19], text)

# --- KeyRoi / Skeleton / SegmentsBuilder: Color constants ---
text = copy_src(R2[20])
text = sub(text, "g.setColor(Color.white);", "g.setColor(Color.WHITE); // TEAVM")
write(R2[20], text)

text = copy_src(R2[21])
text = sub(text, "private static final Color ARC_SLUR = Color.RED;",
           "private static final Color ARC_SLUR = new Color(255, 0, 0); // TEAVM")
text = sub(text, "private static final Color ARC_LINE = Color.BLUE;",
           "private static final Color ARC_LINE = new Color(0, 0, 255); // TEAVM")
text = sub(text, "private static final Color ARC_LAMBDA = Color.LIGHT_GRAY;",
           "private static final Color ARC_LAMBDA = new Color(192, 192, 192); // TEAVM")
write(R2[21], text)

text = copy_src(R2[22])
text = sub(text, "private static final Color SEGMENT = Color.CYAN;",
           "private static final Color SEGMENT = new Color(0, 255, 255); // TEAVM")
write(R2[22], text)

# --- StemBuilder: Color constants + center.getY() (only the Point one) ---
text = copy_src(R2[23])
text = sub_all(text, "g.setColor(Color.RED);", "g.setColor(new Color(255, 0, 0)); // TEAVM")
text = sub_all(text, "g.setColor(Color.PINK);", "g.setColor(new Color(255, 175, 175)); // TEAVM")
text = sub(text, "final Point center = GeoUtil.center(seed.getBounds());\n                if (yDir * Double.compare(center.getY(), lastHeadY) >= 0) {",
           "final Point center = GeoUtil.center(seed.getBounds());\n                if (yDir * Double.compare(center.y, lastHeadY) >= 0) { // TEAVM")
write(R2[23], text)

# --- AbstractFlagInter: refPt.getX/getY ---
text = copy_src(R2[24])
text = sub_all(text, "refPt.getX()", "refPt.x")
text = sub_all(text, "refPt.getY()", "refPt.y")
write(R2[24], text)

# --- Curve: distSq helper + replacements ---
text = copy_src(R2[25])
text = sub(text, "if (curveEnd.distanceSq(arcEnd) < curveEnd.distanceSq(arc.getEnd(!rev))) {",
           "if (distSq(curveEnd, arcEnd) < distSq(curveEnd, arc.getEnd(!rev))) {")
text = sub(text, "if (curveEnd.distanceSq(arcP1) < curveEnd.distanceSq(arcP2)) {",
           "if (distSq(curveEnd, arcP1) < distSq(curveEnd, arcP2)) {")
anchor = "    public ArcView getArcView (Arc arc,"
helper = """    // TEAVM: Point.distanceSq is missing in TeaVM classlib.
    private static double distSq (java.awt.Point a,
                                  java.awt.Point b)
    {
        double dx = a.x - b.x;
        double dy = a.y - b.y;

        return (dx * dx) + (dy * dy);
    }

"""
if anchor not in text:
    raise SystemExit("PATCH FAILED: Curve getArcView anchor")
text = text.replace(anchor, helper + anchor, 1)
write(R2[25], text)

# --- OcrUtil: origin.translate ---
text = copy_src(R2[26])
text = sub(text, "origin.translate(-margin, -margin);",
           "origin.x -= margin; origin.y -= margin; // TEAVM: Point.translate missing")
write(R2[26], text)

# --- NumberInter: center.getX() ---
text = copy_src(R2[27])
text = sub_all(text, "center.getX()", "center.x")
write(R2[27], text)

# --- AbstractInter: distanceSq + new Point(Point) ---
text = copy_src(R2[28])
text = sub(text, "return center.distanceSq(point) <= ((bounds.width * bounds.height) / 4.0);",
           "return ((center.x - point.x) * (double) (center.x - point.x) + (center.y - point.y) * (double) (center.y - point.y)) <= ((bounds.width * bounds.height) / 4.0); // TEAVM")
text = sub(text, "return new Point(glyph.getCenter());",
           "return new Point(glyph.getCenter().x, glyph.getCenter().y); // TEAVM: no Point(Point) ctor")
write(R2[28], text)

# --- AbstractChordInter: new Point(Point) ---
text = copy_src(R2[29])
text = sub(text, "return new Point(headLocation);",
           "return new Point(headLocation.x, headLocation.y); // TEAVM")
text = sub(text, "return new Point(tailLocation);",
           "return new Point(tailLocation.x, tailLocation.y); // TEAVM")
write(R2[29], text)

# --- HeadLinker: getAreaCenter().getX() only (refPt is Point2D here!) ---
text = copy_src(R2[30])
text = sub_all(text, "s1.getAreaCenter().getX()", "s1.getAreaCenter().x")
text = sub_all(text, "s2.getAreaCenter().getX()", "s2.getAreaCenter().x")
write(R2[30], text)

# --- BeamLinker: getAreaCenter().getX() ---
text = copy_src(R2[31])
text = sub_all(text, "s1.getAreaCenter().getX()", "s1.getAreaCenter().x")
text = sub_all(text, "s2.getAreaCenter().getX()", "s2.getAreaCenter().x")
write(R2[31], text)

# --- TupletsBuilder: distanceSq inline ---
text = copy_src(R2[32])
text = sub(text, "if (center.distanceSq(tail) < center.distanceSq(head)) {",
           "if (((center.x - tail.x) * (double) (center.x - tail.x) + (center.y - tail.y) * (double) (center.y - tail.y)) < ((center.x - head.x) * (double) (center.x - head.x) + (center.y - head.y) * (double) (center.y - head.y))) { // TEAVM")
write(R2[32], text)

# --- WedgesBuilder: sEnd.getX() ---
text = copy_src(R2[33])
text = sub(text, "} else if (sEnd.getX() > xMax) {",
           "} else if (sEnd.x > xMax) { // TEAVM")
write(R2[33], text)

# --- SlurLinker: center.distanceSq(target) inline ---
text = copy_src(R2[34])
text = sub(text, "final double dist = center.distanceSq(target);",
           "final double dist = ((center.x - target.getX()) * (double) (center.x - target.getX()) + (center.y - target.getY()) * (double) (center.y - target.getY())); // TEAVM")
write(R2[34], text)

# --- ShapeClassifier: stub classifier (neural model cannot load in WASM) ---
text = copy_src(R2[35])
text = replace_method(text, r'public static Classifier getInstance \(\)',
    '''    public static Classifier getInstance ()
    {
        // TEAVM: the neural classifier model (zip + ZipFS + JAXB) cannot load in WASM;
        // Phase A runs with a stub classifier that returns no evaluations.
        return teavm.StubClassifier.INSTANCE;
    }''')
write(R2[35], text)

# --- BasicClassifier: File.toPath -> Paths.get ---
text = copy_src(R2[36])
text = sub(text, "zipPath = tmpFile.toPath();",
           "zipPath = Paths.get(tmpFile.getPath()); // TEAVM: File.toPath missing")
write(R2[36], text)

# --- TextsStep: neuter OCR (post-HEADS step; Tesseract/JNA cannot run in WASM) ---
text = copy_src(R2[37])
text = replace_method(text, r'protected Context doProlog \(Sheet sheet\)\s*\n\s*throws StepException',
    '''    protected Context doProlog (Sheet sheet)
        throws StepException
    {
        // TEAVM: OCR (Tesseract/JNA) is unavailable in WASM; no text lines.
        return new Context(null, new ArrayList<>());
    }''')
text = replace_method(text, r'public void doSystem \(SystemInfo system,\s*\n\s*Context context\)\s*\n\s*throws StepException',
    '''    public void doSystem (SystemInfo system,
                          Context context)
        throws StepException
    {
        // TEAVM: no OCR.
    }''')
write(R2[37], text)

# --- OcrUtil: no OCR in WASM (kills the BrowserOCR/TesseractOCR refs) ---
text = copy_src("org/audiveris/omr/text/OcrUtil.java")
text = sub(text, 'private static final OCR ocr = TesseractOCR.getInstance();',
           'private static final OCR ocr = null; // TEAVM: no OCR (Tesseract/JNA unavailable)')
text = sub(text, "origin.translate(-margin, -margin);",
           "origin.x -= margin; origin.y -= margin; // TEAVM: Point.translate missing")
write("org/audiveris/omr/text/OcrUtil.java", text)

print("All round-2 patches applied.")

# ============================================================ ROUND 3 =======
# Copy the repo's own patched sources as-is (0001-score-reader.patch).
# The source tree is patched but .work/lib/audiveris.jar is upstream, so
# compiling patched Sheet/Book against the jar fails (e.g. Picture.lighten).
# These are the patch files not already handled above (Book/Sheet are patched
# in rounds 1-2; OcrUtil, stock, too).
# ---------------------------------------------------------------------------
COPY_ASIS = [
    "org/audiveris/omr/CLI.java",
    "org/audiveris/omr/image/FlatMorphology.java",
    "org/audiveris/omr/image/MorphoProcessor.java",
    "org/audiveris/omr/image/Template.java",
    "org/audiveris/omr/score/PartwiseBuilder.java",
    "org/audiveris/omr/sheet/Picture.java",
    "org/audiveris/omr/sheet/grid/PeakGraph.java",
    "org/audiveris/omr/sheet/rhythm/MeasureStack.java",
    "org/audiveris/omr/sig/inter/MetronomeInter.java",
    "org/audiveris/omr/text/BrowserOCR.java",
    "org/audiveris/omr/util/Table.java",
    # score-reader 6e8dd5c: parts matched by clef, and a null measure skipped in RHYTHMS
    "org/audiveris/omr/score/PartCollation.java",
    "org/audiveris/omr/sheet/rhythm/Voices.java",
    # score-reader 54e61ff, 737e122: one-sign key changes, the tenor clef with a separate 8,
    # octave lines followed on the page
    "org/audiveris/omr/sig/inter/KeyInter.java",
    "org/audiveris/omr/sheet/clef/ClefBuilder.java",
    "org/audiveris/omr/sig/inter/OctaveShiftInter.java",
]
for rel in COPY_ASIS:
    write(rel, copy_src(rel))

print("All round-3 copies applied.")

# ============================================================ ROUND 4 =======
# Prune the UI cascade at its roots instead of shimming all of Swing:
#  - delete every `if (... OMR.gui != null ...)` display block in builders
#    and sheet classes (display-only code; headless never runs it)
#  - gut StubsController (referenced directly from SheetStub) to no-ops
#  - neuter Book's save/export/JAXB/PDFBox methods (never called by the demo
#    but TeaVM analyzes every method of every reachable class)
#  - neuter WellKnowns.getGdkMaxScale (JNA/GTK), Language DefinedLanguages
#    (Properties.loadFromXML), SectionCompound.getMembers
#    (Collections.unmodifiableSortedSet)
#  - patch the remaining java.awt.Point / Color call sites in reading-path code
# Round 4 operates on the already-patched OUT files (rounds 1-3 re-run first).
# ---------------------------------------------------------------------------
def read_out(rel):
    with open(OUT / rel, encoding="utf-8") as f:
        return f.read()

def replace_method_re(text, sig_re, new_body):
    """Replace a method whose signature matches sig_re (raw regex, may span lines)."""
    m = re.search(sig_re + r"\s*(?:throws [^{]+)?\{", text)
    if not m:
        raise RuntimeError("method not found: " + sig_re)
    start = m.start()
    i = text.index("{", m.start())
    depth = 0
    j = i
    while True:
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return text[:start] + new_body + text[j + 1:]

def delete_all_gui_blocks(text, rel):
    """Delete every `if (... OMR.gui != null ...) { ... }` block. Refuses on else."""
    count = 0
    while True:
        m = re.search(r"if\s*\([^\n]*OMR\.gui != null[^\n]*\)\s*\{", text)
        if not m:
            return text, count
        i = text.index("{", m.start())
        depth = 0
        j = i
        while True:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        k = j + 1
        while k < len(text) and text[k] in " \t\r\n":
            k += 1
        if text.startswith("else", k):
            raise RuntimeError(f"{rel}: OMR.gui block at offset {m.start()} has an else clause")
        text = text[:m.start()] + text[j + 1:]
        count += 1

# --- WellKnowns: kill the JNA/GTK display-scale probe ---
text = read_out("org/audiveris/omr/WellKnowns.java")
text = replace_method(text, "private static int getGdkMaxScale ()",
                      "private static int getGdkMaxScale ()\n    {\n        return 1; // TEAVM: no GDK/JNA in WASM\n    }")
write("org/audiveris/omr/WellKnowns.java", text)

# --- Book: neuter save/export/JAXB/PDFBox methods ---
text = read_out("org/audiveris/omr/sheet/Book.java")
text = replace_method_re(text, r"public void createStubs \(\)",
    "public void createStubs ()\n    {\n        // TEAVM: no PDFBox/ImageLoading in WASM\n    }")
text = replace_method_re(text, r"public boolean export \(List<SheetStub> theStubs,\s*\n\s*List<Score> theScores\)",
    "public boolean export (List<SheetStub> theStubs,\n                           List<Score> theScores)\n    {\n        return false; // TEAVM: no JAXB export in WASM\n    }")
text = replace_method_re(text, r"public void store \(\)",
    "public void store ()\n    {\n        // TEAVM: no saving in WASM\n    }")
text = replace_method_re(text, r"public void store \(Path bookPath,\s*\n\s*boolean withBackup\)",
    "public void store (Path bookPath,\n                       boolean withBackup)\n    {\n        // TEAVM: no saving in WASM\n    }")
text = replace_method_re(text, r"public void storeBookInfo \(Path root\)",
    "public void storeBookInfo (Path root)\n    {\n        // TEAVM: no JAXB in WASM\n    }")
text = replace_method_re(text, r"public void close \(Integer sheetNumber\)",
    "public void close (Integer sheetNumber)\n    {\n        // TEAVM: no GUI/closing in WASM\n    }")
text = replace_method_re(text, r"public boolean reachBookStep \(final OmrStep target,\s*\n\s*final boolean force,\s*\n\s*final List<SheetStub> (?:theStubs|allStubs),\s*\n\s*final boolean swap\)",  # score-reader main renamed theStubs -> allStubs
    "public boolean reachBookStep (final OmrStep target,\n                                  final boolean force,\n                                  final List<SheetStub> theStubs,\n                                  final boolean swap)\n    {\n        return false; // TEAVM: book steps not driven in WASM demo\n    }")
text = replace_method_re(text, r"public void resetTo \(OmrStep step\)",
    "public void resetTo (OmrStep step)\n    {\n        // TEAVM: no reset in WASM demo\n    }")
text = replace_method_re(text, r"private void checkRadixChange \(Path bookPath\)",
    "private void checkRadixChange (Path bookPath)\n    {\n        // TEAVM: no renaming in WASM\n    }")
text = replace_method_re(text, r"public static void closeFileSystem \(FileSystem fileSystem\)",
    "public static void closeFileSystem (FileSystem fileSystem)\n    {\n        // TEAVM: no ZipFS in WASM\n    }")
# --- Book: getStubsToUpgrade returns empty for a fresh book (§12) ---
# TEAVM §11: Book.initTransients -> getStubsToUpgrade ->
# getStubsWithTableFiles -> BookManager.getDefaultSavePath -> Main.getCli()
# == null traps under TeaVM WasmGC. No saved .omr project can exist in
# WASM, and a fresh in-memory book has no book path (the Book(Path) ctor
# sets only the input path; bookPath is set only when a book is loaded or
# stored as a project). For such a book the original logic would return
# an empty set anyway (version defaults to the current TOOL_REF, so no
# old-version upgrades; no project file, so no table files) -- but
# getStubsWithTableFiles() traps before it can check. Skip the whole
# save-path chain only for fresh books; books loaded from a project keep
# the original logic, so on the desktop this method behaves exactly as
# before. (Deliberately NOT a null-guard on Main.getCli() in
# getDefaultBookFolder: that would only move the trap to the next caller.)
text = replace_method_re(text, r"public Set<SheetStub> getStubsToUpgrade \(\)",
    """    public Set<SheetStub> getStubsToUpgrade ()
    {
        if (stubsToUpgrade == null) {
            // TEAVM §12: fresh in-memory book -- no saved .omr project can
            // exist in WASM; see make_patches.py header for the full
            // rationale. Original logic preserved for project-loaded books.
            if (getBookPath() == null) {
                stubsToUpgrade = new LinkedHashSet<>();
            } else {
                stubsToUpgrade = new LinkedHashSet<>();
                stubsToUpgrade.addAll(getStubsWithOldVersion());
                stubsToUpgrade.addAll(getStubsWithTableFiles());

                if (!stubsToUpgrade.isEmpty()) {
                    logger.info(
                            "{} stub{} to upgrade in {}",
                            stubsToUpgrade.size(),
                            (stubsToUpgrade.size() > 1) ? "s" : "",
                            this);
                }
            }
        }

        return stubsToUpgrade;
    }""")
write("org/audiveris/omr/sheet/Book.java", text)

# --- SheetStub: manual GUI sites, then delete all OMR.gui blocks ---
text = read_out("org/audiveris/omr/sheet/SheetStub.java")
text = sub(text, 'if ((OMR.gui == null) || (OMR.gui.displayConfirmation(\n                msg + WellKnowns.LINE_SEPARATOR + "OK for discarding this sheet?"))) {',
           'if (true) { // TEAVM: no GUI confirmation; headless always discards')
text = sub(text, "final StubsController ctrl = (OMR.gui != null) ? StubsController.getInstance() : null;",
           "final StubsController ctrl = null; // TEAVM: no GUI controller")
text, n = delete_all_gui_blocks(text, "SheetStub.java")
print(f"  deleted {n} OMR.gui blocks in SheetStub.java")
write("org/audiveris/omr/sheet/SheetStub.java", text)

# --- Sheet: manual if/else site, then delete all OMR.gui blocks ---
text = read_out("org/audiveris/omr/sheet/Sheet.java")
text = sub(text, """            if (OMR.gui != null) {
                OMR.gui.displayWarning(msg);
            } else {
                logger.warn(msg);
            }""",
           "            logger.warn(msg); // TEAVM: no GUI warning")
text, n = delete_all_gui_blocks(text, "Sheet.java")
print(f"  deleted {n} OMR.gui blocks in Sheet.java")
write("org/audiveris/omr/sheet/Sheet.java", text)

# --- Builder / display files: delete all OMR.gui blocks ---
for rel in [
    "org/audiveris/omr/sheet/grid/GridBuilder.java",
    "org/audiveris/omr/sheet/stem/VerticalsBuilder.java",
    "org/audiveris/omr/sheet/ledger/LedgersFilter.java",
    "org/audiveris/omr/sheet/note/DistancesBuilder.java",
    "org/audiveris/omr/sheet/beam/SpotsBuilder.java",
    "org/audiveris/omr/sheet/curve/Curves.java",
    "org/audiveris/omr/sheet/SheetDiff.java",
]:
    text = read_out(rel)
    text, n = delete_all_gui_blocks(text, rel)
    print(f"  deleted {n} OMR.gui blocks in {rel}")
    write(rel, text)

# --- CueBeamsStep: copy from repo, delete the SpotsController display block ---
text = copy_src("org/audiveris/omr/sheet/beam/CueBeamsStep.java")
text, n = delete_all_gui_blocks(text, "CueBeamsStep.java")
print(f"  deleted {n} OMR.gui blocks in CueBeamsStep.java")
write("org/audiveris/omr/sheet/beam/CueBeamsStep.java", text)

# --- Language: neuter DefinedLanguages ctor (loads languages.xml) ---
text = copy_src("org/audiveris/omr/text/Language.java")
text = replace_method(text, "public DefinedLanguages ()",
                      "public DefinedLanguages ()\n            {\n                // TEAVM: no languages.xml / Properties.loadFromXML in WASM\n            }")
write("org/audiveris/omr/text/Language.java", text)

# --- SectionCompound: unmodifiableSortedSet is missing in TeaVM ---
text = copy_src("org/audiveris/omr/glyph/dynamic/SectionCompound.java")
text = sub(text, "return Collections.unmodifiableSortedSet(members);",
           "return members; // TEAVM: unmodifiableSortedSet missing in classlib")
# score-reader: the bounds cached when members were last added or removed can be stale here by the
# time a staff line's pixels are drawn into them (a member section's own bounds have moved since):
# a row can then land outside the buffer and the page is lost in GRID (StaffFilament.toStaffLine).
# The desktop's are right at that point, so taking them afresh changes nothing there. Why they go
# stale here (perhaps TeaVM's TreeMap, with members whose sort key moved) isn't known.
text = sub(text, """        checkBounds();

        final Point offset = bounds.getLocation();
        final ByteProcessor buffer = new ByteProcessor(bounds.width, bounds.height);""", """        bounds = null; // TEAVM: taken afresh (see make_patches.py)
        checkBounds();

        final Point offset = bounds.getLocation();
        final ByteProcessor buffer = new ByteProcessor(bounds.width, bounds.height);""")
write("org/audiveris/omr/glyph/dynamic/SectionCompound.java", text)

# ------------------------------------------------------------------ DrumSet
# score-reader: Audiveris reads its drum set (res/drum-set.xml) with JAXB, which can't run here,
# from a res folder there isn't. A staff it takes for percussion (on a hard photo, a staff whose
# clef it couldn't read) then lost the whole page in HEADS ("Parent is null", the res folder). The
# entries are read from that same file here, when building, and added as Audiveris's loader adds
# them, so the drum set is the desktop's.
text = copy_src("org/audiveris/omr/score/DrumSet.java")
drum = re.sub(r"<!--.*?-->", "", (REPO.parents[2] / "res" / "drum-set.xml").read_text(), flags=re.S)
calls = []
for staff in re.finditer(r'<staff\s+line-count="(\d+)"\s*>(.*?)</staff>', drum, re.S):
    for entry in re.finditer(r"<entry\b([^>]*)/>", staff.group(2)):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', entry.group(1)))
        sign = f"Shape.{a['sign']}" if "sign" in a else "null"
        calls.append(f"        teavmAdd({staff.group(1)}, {a['pitch-position']}, HeadMotif.{a['motif']}, {sign}, DrumSound.{a['sound']});")
assert calls and len(calls) == len(re.findall(r"<entry\b", drum)), f"drum-set.xml: read {len(calls)} of its entries"
text = replace_method(text, r"private void loadAllConfigurations \(\)", """private void loadAllConfigurations ()
    {
        // TEAVM: the system drum set, from res/drum-set.xml when building (make_patches.py)
""" + "\n".join(calls) + """
    }

    /** TEAVM: add an entry as loadConfiguration does. */
    private void teavmAdd (int lineCount,
                           int pitchPosition,
                           HeadMotif motif,
                           Shape sign,
                           DrumSound sound)
    {
        Map<Integer, Map<MotifSign, DrumInstrument>> byPitch = structure.get(lineCount);
        if (byPitch == null) {
            structure.put(lineCount, byPitch = new TreeMap<>());
        }
        Map<MotifSign, DrumInstrument> msMap = byPitch.get(pitchPosition);
        if (msMap == null) {
            byPitch.put(pitchPosition, msMap = new LinkedHashMap<>());
        }
        msMap.put(new MotifSign(motif, sign), new DrumInstrument(motif, sign, sound));
    }""")
write("org/audiveris/omr/score/DrumSet.java", text)
print(f"  DrumSet: {len(calls)} entries from res/drum-set.xml")

# ------------------------------------------------------------------ ArcRetriever
# score-reader: on a hard photo (chorale-4-photo-hard) an arc's first point lay in no staff's
# area here, and isStaffArc dereferenced the null staff, losing the page in CURVES. The desktop
# finds a staff for it (or it would fail the same way): staff areas are cut by the shim's polygon
# clipping here (shims/src/java/awt/geom/Area.java), which can leave a sliver out. An arc with no
# staff around it is not part of a staff line; the other callers of getClosestStaff check already.
text = copy_src("org/audiveris/omr/sheet/curve/ArcRetriever.java")
text = sub(text, """        Staff staff = sheet.getStaffManager().getClosestStaff(p0);

        if (staff.isTablature()) {""", """        Staff staff = sheet.getStaffManager().getClosestStaff(p0);

        if (staff == null) {
            return false; // TEAVM: in no staff's area (see make_patches.py)
        }

        if (staff.isTablature()) {""")
write("org/audiveris/omr/sheet/curve/ArcRetriever.java", text)

# --- ShapeSymbol: MAGENTA/BLUE/new Color(int,boolean) ---
text = copy_src("org/audiveris/omr/ui/symbol/ShapeSymbol.java")
text = sub(text, "g.setColor(logger.isDebugEnabled() ? Color.MAGENTA : defaultImageColor);",
           "g.setColor(logger.isDebugEnabled() ? new Color(255, 0, 255) : defaultImageColor); // TEAVM")
text = sub(text, "g.setColor(logger.isDebugEnabled() ? Color.BLUE : defaultImageColor);",
           "g.setColor(logger.isDebugEnabled() ? new Color(0, 0, 255) : defaultImageColor); // TEAVM")
text = sub(text, "final Color pix = new Color(image.getRGB(x, y), true);",
           "final int argb = image.getRGB(x, y);\n                final Color pix = new Color((argb >> 16) & 0xFF, (argb >> 8) & 0xFF, argb & 0xFF, (argb >> 24) & 0xFF); // TEAVM")
write("org/audiveris/omr/ui/symbol/ShapeSymbol.java", text)

# --- BasicAttachmentHolder: Color.RED ---
text = copy_src("org/audiveris/omr/ui/util/BasicAttachmentHolder.java")
text = sub(text, "g.setColor(Color.RED);",
           "g.setColor(new Color(255, 0, 0)); // TEAVM")
write("org/audiveris/omr/ui/util/BasicAttachmentHolder.java", text)

# --- GlyphSlurInfo: Point.translate ---
text = copy_src("org/audiveris/omr/sheet/curve/GlyphSlurInfo.java")
text = sub(text, "point.translate(dx, dy);",
           "point.x += dx; point.y += dy; // TEAVM: Point.translate missing")
write("org/audiveris/omr/sheet/curve/GlyphSlurInfo.java", text)

# --- CurvesBuilder: Point.move ---
text = copy_src("org/audiveris/omr/sheet/curve/CurvesBuilder.java")
text = sub(text, "np.move(pivot.x + dxs[dir], pivot.y + dys[dir]);",
           "np.x = pivot.x + dxs[dir]; np.y = pivot.y + dys[dir]; // TEAVM: Point.move missing")
write("org/audiveris/omr/sheet/curve/CurvesBuilder.java", text)

# --- Orientation: new Point(Point) ---
text = copy_src("org/audiveris/omr/run/Orientation.java")
text = sub(text, "return new Point(absolute(xy)); // Since involutive",
           "final Point abs = absolute(xy);\n        return new Point(abs.x, abs.y); // TEAVM: Point(Point) missing")
write("org/audiveris/omr/run/Orientation.java", text)

# --- LeggedIntersBuilder: segPt.getX()/getY() (Point; top is Point2D, keep) ---
text = copy_src("org/audiveris/omr/sheet/curve/LeggedIntersBuilder.java")
text = sub(text, "double dx = top.getX() - segPt.getX();",
           "double dx = top.getX() - segPt.x; // TEAVM")
text = sub(text, "double dy = top.getY() - segPt.getY();",
           "double dy = top.getY() - segPt.y; // TEAVM")
write("org/audiveris/omr/sheet/curve/LeggedIntersBuilder.java", text)

# --- SlurLinker: Point.distance in defineAreaPair ---
text = read_out("org/audiveris/omr/sheet/curve/SlurLinker.java")
text = sub(text, "if (first.distance(last) > (2 * params.coverageVIn)) {",
           "if (Math.hypot(first.x - last.x, first.y - last.y) > (2 * params.coverageVIn)) { // TEAVM")
write("org/audiveris/omr/sheet/curve/SlurLinker.java", text)

# --- Gutted StubsController (same public API, no Swing, no-op methods) ---
STUBS_CONTROLLER = '''package org.audiveris.omr.sheet.ui;

import java.awt.Color;
import java.util.function.Predicate;

import javax.swing.JTabbedPane;
import javax.swing.event.ChangeEvent;

import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.step.OmrStep;
import org.audiveris.omr.ui.selection.StubEvent;
import org.bushe.swing.event.EventSubscriber;

/**
 * TEAVM: headless stub. The real StubsController drives the Swing UI (tabs,
 * boards, event service); none of it exists in WASM. Same public API, all
 * methods no-ops, so the reading path can reference it without pulling in Swing.
 */
public class StubsController
        implements javax.swing.event.ChangeListener, java.beans.PropertyChangeListener
{
    private static final StubsController INSTANCE = new StubsController();

    private StubsController ()
    {
    }

    public void addAssembly (SheetAssembly assembly,
                             Integer index)
    {
    }

    public void adjustStubTabs (Book book)
    {
    }

    public void callAboutStub (SheetStub stub)
    {
    }

    public void deleteAssembly (SheetStub stub)
    {
    }

    public void display (SheetStub stub,
                         boolean force)
    {
    }

    public void displayStubs (Book book,
                              Integer index)
    {
    }

    public void displayStubs (Book book,
                              Integer index,
                              Predicate<SheetStub> predicate)
    {
    }

    public void dumpCurrentSheetServices ()
    {
    }

    public JTabbedPane getComponent ()
    {
        return null;
    }

    public Integer getIndex (SheetStub stub)
    {
        return null;
    }

    public int getLastIndex ()
    {
        return 0;
    }

    public SheetStub getSelectedStub ()
    {
        return null;
    }

    public boolean isDisplayed (Book book)
    {
        return false;
    }

    public void markTab (SheetStub stub,
                         Color color)
    {
    }

    public void propertyChange (java.beans.PropertyChangeEvent evt)
    {
    }

    public void refresh ()
    {
    }

    public void removeAssembly (SheetStub stub)
    {
    }

    public void selectAssembly (SheetStub stub)
    {
    }

    public void selectOtherBook (Book currentBook)
    {
    }

    public void stateChanged (ChangeEvent e)
    {
    }

    public void subscribe (EventSubscriber<StubEvent> subscriber)
    {
    }

    @Override
    public String toString ()
    {
        return "StubsController(teavm)";
    }

    public void unsubscribe (EventSubscriber<StubEvent> subscriber)
    {
    }

    public void updateFirstStubTitle (Book book)
    {
    }

    public static Book getCurrentBook ()
    {
        return null;
    }

    public static SheetStub getCurrentStub ()
    {
        return null;
    }

    public static OmrStep getEarlyStep ()
    {
        return null;
    }

    public static StubsController getInstance ()
    {
        return INSTANCE;
    }

    public static void invokeSelect (SheetStub stub)
    {
    }

    public static void setEarlyStep (OmrStep step)
    {
    }
}
'''
write("org/audiveris/omr/sheet/ui/StubsController.java", STUBS_CONTROLLER)
print("All round-4 patches applied.")

# ============================================================ ROUND 5 =======
# Neuter the JAXB entry points that survived round 4: Sheet.store /
# getJaxbContext / unmarshal, Book.getJaxbContext / generateSchema,
# BasicClassifier.loadNorms / storeNorms. (The Jaxb.*Adapter annotations
# on fields do not pull in JAXBContext by themselves.)
# ---------------------------------------------------------------------------
# --- Sheet: store / getJaxbContext / unmarshal ---
text = read_out("org/audiveris/omr/sheet/Sheet.java")
text = replace_method_re(text, r"public void store \(Path sheetFolder,\s*\n\s*Path oldSheetFolder\)",
    "public void store (Path sheetFolder,\n                       Path oldSheetFolder)\n    {\n        // TEAVM: no JAXB saving in WASM\n    }")
text = replace_method_re(text, r"public static JAXBContext getJaxbContext \(\)",
    "public static JAXBContext getJaxbContext ()\n        throws JAXBException\n    {\n        return null; // TEAVM: no JAXB in WASM\n    }")
text = replace_method_re(text, r"public static Sheet unmarshal \(InputStream in\)",
    "public static Sheet unmarshal (InputStream in)\n        throws JAXBException\n    {\n        return null; // TEAVM: no JAXB loading in WASM\n    }")
write("org/audiveris/omr/sheet/Sheet.java", text)

# --- Book: getJaxbContext / generateSchema ---
text = read_out("org/audiveris/omr/sheet/Book.java")
text = replace_method_re(text, r"public static JAXBContext getJaxbContext \(\)",
    "public static JAXBContext getJaxbContext ()\n        throws JAXBException\n    {\n        return null; // TEAVM: no JAXB in WASM\n    }")
text = replace_method_re(text, r"public static void generateSchema \(String outputFileName\)",
    "public static void generateSchema (String outputFileName)\n    {\n        // TEAVM: no JAXB schema generation in WASM\n    }")
write("org/audiveris/omr/sheet/Book.java", text)

# --- BasicClassifier: loadNorms / storeNorms (model load/save, not in demo) ---
text = read_out("org/audiveris/omr/classifier/BasicClassifier.java")
text = replace_method_re(text, r"protected BasicNorms loadNorms \(Path root\)",
    "protected BasicNorms loadNorms (Path root)\n        throws Exception\n    {\n        return null; // TEAVM: no JAXB model loading in WASM\n    }")
text = replace_method_re(text, r"protected void storeNorms \(Path root\)",
    "protected void storeNorms (Path root)\n        throws Exception\n    {\n        // TEAVM: no JAXB model saving in WASM\n    }")
write("org/audiveris/omr/classifier/BasicClassifier.java", text)
print("All round-5 patches applied.")

# ============================================================ ROUND 6 =======
# Fix the last Audiveris-side Color/Dimension stragglers surfaced in the
# round-4 Spike run (407 problems): Color.white in UI ctors (TColor has
# only WHITE), and new Dimension(Dimension) -- the classlib TDimension
# has no copy ctor, so expand it at the call site.
# ---------------------------------------------------------------------------
# --- RunTableView: setBackground(Color.white) -> WHITE ---
text = copy_src("org/audiveris/omr/run/RunTableView.java")
text = sub(text, "setBackground(Color.white);", "setBackground(Color.WHITE);")
write("org/audiveris/omr/run/RunTableView.java", text)

# --- RubberPanel: Color.white -> WHITE; new Dimension(modelSize) -> (w,h) ---
text = copy_src("org/audiveris/omr/ui/view/RubberPanel.java")
text = sub(text, "setBackground(Color.white);", "setBackground(Color.WHITE);")
text = sub_all(text, "new Dimension(modelSize)", "new Dimension(modelSize.width, modelSize.height)")
write("org/audiveris/omr/ui/view/RubberPanel.java", text)
print("All round-6 patches applied.")

# ============================================================ ROUND 8 =======
# §14 follow-up: populateAllSymbols() pulls the symbol painters into the
# reachable set, and NonDraggableSymbol.paint uses Color.RED — but TeaVM's
# classlib TColor defines only BLACK/WHITE, so the field is "not found"
# (the shims/src Color constants are shadowed by the classlib version;
# §9 rule: for classlib-defined classes, fix at the call site).
# new Color(255, 0, 0) is exactly RED (same RGB), so template rendering
# is unchanged. No other Color.* constant is used by any reachable method
# (TeaVM reported only RED after the CubicCurve2D fix).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/ui/symbol/NonDraggableSymbol.java")
text = sub(text,
           "        g.setColor(Color.RED);",
           "        g.setColor(new Color(255, 0, 0)); // TEAVM: TColor has no RED (§14)")
write("org/audiveris/omr/ui/symbol/NonDraggableSymbol.java", text)
print("All round-8 (§14 Color.RED call-site) patches applied.")

# ============================================================ ROUND 9 =======
# §16: FloodFiller.fill is iterative.
# A recursive four-neighbour fill overflows the Wasm call stack in HEADS
# template building, with any stack size, and browsers can't set one.
# Iterative version below, via replace_method on a fresh copy of the file.
# Semantics are identical by construction:
#   * same guard: a pixel is filled iff pix == oldColor && pix != newColor
#     (oldColor == newColor, or a seed that is not oldColor, is a no-op,
#     exactly as in the recursive version);
#   * a pixel is marked (setRGB(newColor)) at push time, so each pixel is
#     pushed at most once and the stack never holds duplicates;
#   * the filled set is therefore exactly the 4-connected component of
#     oldColor pixels reachable from the seed — the same set the recursive
#     version fills. Traversal order differs (the recursive version is
#     depth-first Left/Top/Bottom/Right; the explicit stack pops in the
#     reverse push order), but order cannot affect the final image: the
#     fill is a closure over a fixed set of pixels, and every pixel in
#     the component is marked exactly once either way.
# Desktop-neutral: verified pixel-identical on desktop (§16, fill16/)
# on synthetic images (random, solid, snake, disconnected) AND on the
# real hymn page end-to-end (desktop Audiveris .mxl identical), before
# any Node run.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/image/FloodFiller.java")
text = replace_method(text, r'public void fill \(int x,\s*\n\s*int y,\s*\n\s*int oldColor,\s*\n\s*int newColor\)',
    '''    public void fill (int x,
                      int y,
                      int oldColor,
                      int newColor)
    {
        // TEAVM §16: a flood fill with its own stack. A recursive one
        // overflows the Wasm call stack in HEADS template building.
        // Same pixels, no recursion: a pixel is marked at
        // push time, so each pixel is pushed at most once, and the filled
        // set is exactly the 4-connected oldColor component reachable
        // from the seed — the same set the recursive version fills.
        if ((x < 0) || (x >= width) || (y < 0) || (y >= height)) {
            return;
        }

        if (oldColor == newColor) {
            return;
        }

        if (image.getRGB(x, y) != oldColor) {
            return;
        }

        // Neighbour offsets in the recursive version's order:
        // Left, Top, Bottom, Right.
        final int[] dx = { -1, 0, 0, 1 };
        final int[] dy = { 0, -1, 1, 0 };

        // Explicit stack of encoded positions (pos = y * width + x),
        // grown as needed; a plain int[] keeps this free of any
        // collection dependency under TeaVM.
        int[] stack = new int[256];
        int top = 0;

        image.setRGB(x, y, newColor);
        stack[top++] = (y * width) + x;

        while (top > 0) {
            int pos = stack[--top];
            int px = pos % width;
            int py = pos / width;

            for (int dir = 0; dir < 4; dir++) {
                int nx = px + dx[dir];
                int ny = py + dy[dir];

                if ((nx < 0) || (nx >= width) || (ny < 0) || (ny >= height)) {
                    continue;
                }

                if (image.getRGB(nx, ny) != oldColor) {
                    continue;
                }

                image.setRGB(nx, ny, newColor);

                if (top == stack.length) {
                    int[] grown = new int[stack.length * 2];
                    System.arraycopy(stack, 0, grown, 0, stack.length);
                    stack = grown;
                }

                stack[top++] = (ny * width) + nx;
            }
        }
    }''')
write("org/audiveris/omr/image/FloodFiller.java", text)
print("All round-9 (§16 iterative FloodFiller.fill) patches applied.")

# ============================================================ ROUND 11 (§16 cap) ======
# Cap TemplateFactory.Builder.processSymbol rebuild loop. Upstream recurses without
# limit on holes-detection failure (buildDistances null), which terminates on
# desktop (a real music font yields an enclosed hole within a couple of
# doublings) but runs away under TeaVM, where the stub font renders a blank
# glyph: buildDistances returns null forever and the image doubles
# (holeLargerRatio=2) until allocation fails. After ratio 8, give up and return
# an empty key-point list, which scores no heads for that shape (templates come
# pre-rendered, §17, so this is a guard). Desktop-neutral: with a real font the loop
# terminates before the cap, so behaviour is unchanged.
rel_tf = "org/audiveris/omr/image/TemplateFactory.java"
text = read_out(rel_tf)
text = sub(text,
           """                // Holes detection failed. Process symbol at higher resolution
                final int larger = constants.holeLargerRatio.getValue();
                logger.info("Rebuilding {} template at resolution {}", shape, larger * ps);
                return processSymbol(larger * ratio);""",
           """                // Holes detection failed. Process symbol at higher resolution
                final int larger = constants.holeLargerRatio.getValue();

                // TEAVM (§16): cap the rebuild loop (see above); blank stub-font
                // templates would otherwise double forever. Attempts at ratios
                // 1, 2, 4, 8, then give up with an empty key-point list.
                if (ratio >= 8) {
                    logger.warn("No template for {} at any resolution, giving up", shape);
                    return new ArrayList<>();
                }

                logger.info("Rebuilding {} template at resolution {}", shape, larger * ps);
                return processSymbol(larger * ratio);""")
write(rel_tf, text)
print("All round-11 (§16 processSymbol rebuild cap) patches applied.")

# ============================================================ ROUND 12 (§17 Phase B) ======
# Pre-rendered note-head templates. Catalog.buildAllTemplates first asks
# teavm.PreRenderedTemplates (entry/src/teavm, data generated offline on
# desktop Java with the real Bravura font — phaseb/TemplateDump.java +
# templates.json + gen_prerendered.py) for a complete Template built from
# stored width/height/slim-bounds/anchors/keyPoints; only when it returns
# null (unknown family, or no pre-rendered catalog near the requested point
# size) does it fall back to Builder.buildTemplate() from the stub font
# (the Phase A behaviour). The lookup maps the TeaVM-requested point size
# to the nearest pre-rendered DESKTOP point size: the shim TextLayout
# reports advance 0.5*size, so BlackHeadSizer calibrates the catalog to
# 2.0 * measuredHeadWidth under TeaVM, while desktop calibrates to
# measuredHeadWidth / 0.2950 — hence desktop = requested * 1.694827.
# Hymn: requested 54 -> desktop 92 (the desktop calibration for this
# sheet, black-head mean width 27.2 px). The returned Template carries
# the DESKTOP point size (92); nothing in the HEADS path requires
# template.getPointSize() to equal the catalog point size (verified by
# grep over NoteHeadsBuilder/HeadInter/Template), and the desktop
# round-trip test (phaseb/RoundTrip.java, 72/72 PASS) proves the
# pre-rendered Template is field-identical to the native one at 92.
text = read_out(rel_tf)
text = sub(text,
           """            for (Shape shape : ShapeSet.Heads) {
                templates.put(shape, new Builder(shape, family, pointSize).buildTemplate());
            }""",
           """            for (Shape shape : ShapeSet.Heads) {
                // TEAVM (§17 Phase B): pre-rendered template first (built
                // offline with the real Bravura font); fall back to the
                // stub-font Builder when no pre-rendered catalog covers
                // this point size.
                Template pre = teavm.PreRenderedTemplates.getTemplate(shape, family, pointSize);

                templates.put(
                        shape,
                        (pre != null) ? pre : new Builder(shape, family, pointSize).buildTemplate());
            }""")
write(rel_tf, text)
print("All round-12 (§17 pre-rendered templates) patches applied.")

# ============================================================ ROUND 13 (§18 Phase C) ======
# Real neural glyph classifier under TeaVM.
#
# What the classifier is (verified from the Audiveris sources, not assumed):
# - BasicClassifier = home-built shallow MLP (NeuralNetwork: 1 hidden layer,
#   sigmoid), NOT ONNX / DL4J / JNI. Model file app/res/basic-classifier.zip:
#   model.xml (110 -> 149 -> 149, epochs-total 160), means.xml + stds.xml
#   (110 doubles each). No native code anywhere in the inference path.
# - Input features: MixGlyphDescriptor, 110 doubles = 99 ART moments +
#   10 geometric moments + aspect, computed from the glyph's RunTable
#   (getARTMoments / getGeometricMoments — pure Java, already in the
#   pipeline). Normalization is (x - means) / stds via PoorManAlgebra
#   (Audiveris's own tiny Nd4j replacement, pure Java).
# - Loading on desktop is the ONLY WASM-hostile part: ZipFS over the zip +
#   JAXB unmarshalling of model.xml / means.xml / stds.xml (+ user train
#   folder, temp-file copy, FileUtils, ChartPlotter training UI).
#
# Fix, Phase B style: the weights/norms/labels are pre-rendered offline into
# teavm.PreRenderedClassifier (phasec/gen_classifier.py, bit-identical doubles
# via repr(); verified by phasec/ClassifierCheck on desktop) and
# BasicClassifier builds its network from those arrays. The zip/JAXB/train
# methods are neutered (ROUND 5 precedent: Sheet/Book JAXB methods), so no
# ZipFS/JAXB/FileUtils/JFreeChart code is reachable from the classifier.
# ShapeClassifier.getInstance() returns the real BasicClassifier again
# (reverting the ROUND 2 stub); StubClassifier.java stays in entry/src,
# unused. Training stays a desktop activity: train() warns and does nothing.
text = read_out("org/audiveris/omr/classifier/ShapeClassifier.java")
text = sub(text,
           """        // TEAVM: the neural classifier model (zip + ZipFS + JAXB) cannot load in WASM;
        // Phase A runs with a stub classifier that returns no evaluations.
        return teavm.StubClassifier.INSTANCE;""",
           """        // TEAVM (§18 Phase C): the real BasicClassifier, built from
        // pre-rendered weights (teavm.PreRenderedClassifier) — the zip +
        // ZipFS + JAXB path is bypassed in BasicClassifier (ROUND 13).
        return BasicClassifier.getInstance();""")
write("org/audiveris/omr/classifier/ShapeClassifier.java", text)

# --- BasicClassifier: build from pre-rendered data; neuter I/O + training ---
text = read_out("org/audiveris/omr/classifier/BasicClassifier.java")
text = sub(text,
           """        // Unmarshal from user or default data, if compatible
        network = load(MODEL_FILE_NAME);

        if (network == null) {
            network = new Network();
            network.model = createModel();
        }""",
           """        // TEAVM (§18 Phase C): model + norms from pre-rendered static data
        // (teavm.PreRenderedClassifier), not the zip — ZipFS + JAXB cannot
        // run in WASM. load()/loadModel()/loadNorms() are neutered below.
        network = loadPreRendered();

        // Fail loudly on a label mismatch: a model built for different
        // features would silently misclassify every glyph.
        if (!isCompatible(network.model, network.norms)) {
            throw new IllegalStateException(
                    "Pre-rendered classifier incompatible with MixGlyphDescriptor");
        }""")
text = sub(text,
           """    //-------------//
    // addListener //
    //-------------//""",
           """    //-----------------//
    // loadPreRendered //
    //-----------------//
    /**
     * Build the network from the pre-rendered static data (TEAVM §18).
     * The weights are the shipped basic-classifier.zip weights,
     * bit-identical (verified by phasec/ClassifierCheck on desktop).
     */
    private Network loadPreRendered ()
    {
        org.audiveris.omr.math.NeuralNetwork model = new org.audiveris.omr.math.NeuralNetwork(
                teavm.PreRenderedClassifier.INPUT_SIZE,
                teavm.PreRenderedClassifier.HIDDEN_SIZE,
                teavm.PreRenderedClassifier.OUTPUT_SIZE,
                teavm.PreRenderedClassifier.hiddenWeights(),
                teavm.PreRenderedClassifier.outputWeights(),
                teavm.PreRenderedClassifier.inputLabels(),
                teavm.PreRenderedClassifier.outputLabels(),
                teavm.PreRenderedClassifier.LEARNING_RATE,
                teavm.PreRenderedClassifier.MOMENTUM,
                teavm.PreRenderedClassifier.LAMBDA,
                teavm.PreRenderedClassifier.EPOCHS_TOTAL);

        org.audiveris.omr.math.PoorManAlgebra.INDArray means =
                org.audiveris.omr.math.PoorManAlgebra.Nd4j.create(
                        teavm.PreRenderedClassifier.means());
        org.audiveris.omr.math.PoorManAlgebra.INDArray stds =
                org.audiveris.omr.math.PoorManAlgebra.Nd4j.create(
                        teavm.PreRenderedClassifier.stds());

        return new Network(model, new BasicNorms(means, stds));
    }

    //-------------//
    // addListener //
    //-------------//""")
text = replace_method_re(text, r"protected Network load \(String\.\.\. fileNames\)",
    """    protected Network load (String... fileNames)
    {
        return null; // TEAVM (§18): zip loading unavailable in WASM; see loadPreRendered()
    }""")
text = replace_method_re(text, r"protected NeuralNetwork loadModel \(Path root\)",
    """    protected NeuralNetwork loadModel (Path root)
        throws Exception
    {
        return null; // TEAVM (§18): JAXB model loading unavailable in WASM
    }""")
text = replace_method_re(text, r"protected void store \(\)",
    """    protected void store ()
        throws Exception
    {
        // TEAVM (§18): no classifier storing in WASM
    }""")
text = replace_method_re(text, r"protected void storeModel \(Path root\)",
    """    protected void storeModel (Path root)
        throws Exception
    {
        // TEAVM (§18): no classifier storing in WASM
    }""")
text = replace_method_re(text, r"public void train \(Collection<Sample> samples,\s*int epochs\)",
    """    public void train (Collection<Sample> samples,
                       int epochs)
    {
        // TEAVM (§18): classifier training is a desktop activity; the WASM
        // build runs inference only.
        logger.warn("Classifier training unsupported in WASM");
    }""")
write("org/audiveris/omr/classifier/BasicClassifier.java", text)

# --- AbstractClassifier: neuter the train-folder probe (java.nio.file.Files
# is not reliably available under TeaVM; load()/store() are neutered above,
# so nothing in WASM needs the folder) ---
text = copy_src("org/audiveris/omr/classifier/AbstractClassifier.java")
text = replace_method_re(text, r"protected Path getTrainFolder \(boolean create\)",
    """    protected Path getTrainFolder (boolean create)
        throws IOException
    {
        return WellKnowns.TRAIN_FOLDER; // TEAVM (§18): no train folder in WASM
    }""")
write("org/audiveris/omr/classifier/AbstractClassifier.java", text)

# --- NeuralNetwork: array constructor + neuter JAXB (un)marshalling ---
text = copy_src("org/audiveris/omr/math/NeuralNetwork.java")
text = sub(text,
           """        logger.info(
                String.format(
                        "Initial complexity, hiddenW2: %.1f outputW2: %.1f",
                        w2(hiddenWeights),
                        w2(outputWeights)));
    }""",
           """        logger.info(
                String.format(
                        "Initial complexity, hiddenW2: %.1f outputW2: %.1f",
                        w2(hiddenWeights),
                        w2(outputWeights)));
    }

    /**
     * Create a neural network from pre-rendered weights (TEAVM §18 Phase C).
     * Same semantics as the JAXB-unmarshalled network; the weights, labels
     * and hyper-parameters come from teavm.PreRenderedClassifier (generated
     * offline from basic-classifier.zip) because ZipFS + JAXB cannot run
     * in WASM. The weights arrays are used as-is (not copied).
     *
     * @param inputSize     number of cells in input layer
     * @param hiddenSize    number of cells in hidden layer
     * @param outputSize    number of cells in output layer
     * @param hiddenWeights weights to hidden layer (hiddenSize x (inputSize+1))
     * @param outputWeights weights to output layer (outputSize x (hiddenSize+1))
     * @param inputLabels   labels of input cells
     * @param outputLabels  labels of output cells
     * @param learningRate  learning rate
     * @param momentum      training momentum
     * @param lambda        L2 regularization factor
     * @param epochsTotal   total count of epochs run so far
     */
    public NeuralNetwork (int inputSize,
                          int hiddenSize,
                          int outputSize,
                          double[][] hiddenWeights,
                          double[][] outputWeights,
                          String[] inputLabels,
                          String[] outputLabels,
                          double learningRate,
                          double momentum,
                          double lambda,
                          int epochsTotal)
    {
        this.inputSize = inputSize;
        this.hiddenSize = hiddenSize;
        this.outputSize = outputSize;
        this.learningRate = learningRate;
        this.momentum = momentum;
        this.lambda = lambda;
        this.epochsTotal = epochsTotal;
        this.hiddenWeights = hiddenWeights;
        this.outputWeights = outputWeights;
        this.inputLabels = new StringArray(inputLabels);

        if (inputLabels.length != inputSize) {
            throw new IllegalArgumentException(
                    "Inconsistent input labels size " + inputLabels.length + " vs " + inputSize);
        }

        this.outputLabels = new StringArray(outputLabels);

        if (outputLabels.length != outputSize) {
            throw new IllegalArgumentException(
                    "Inconsistent output labels size " + outputLabels.length + " vs " + outputSize);
        }
    }""")
text = replace_method_re(text, r"public void marshal \(OutputStream os\)",
    """    public void marshal (OutputStream os)
        throws JAXBException, XMLStreamException, IOException
    {
        // TEAVM (§18): no JAXB marshalling in WASM
    }""")
text = replace_method_re(text, r"private static JAXBContext getJaxbContext \(\)",
    """    private static JAXBContext getJaxbContext ()
        throws JAXBException
    {
        return null; // TEAVM (§18): no JAXB in WASM
    }""")
text = replace_method_re(text, r"public static NeuralNetwork unmarshal \(InputStream in\)",
    """    public static NeuralNetwork unmarshal (InputStream in)
        throws JAXBException
    {
        return null; // TEAVM (§18): no JAXB unmarshalling in WASM
    }""")
write("org/audiveris/omr/math/NeuralNetwork.java", text)
print("All round-13 (§18 neural classifier) patches applied.")

# ============================================================ ROUND 14 (§18) ======
# ClefBuilder: SUPERSEDED by §19 (ROUND 15 below). The §18 glyph-bounds
# patch is REMOVED: with pre-rendered Bravura metrics in the font shim
# (real TextLayout bounds) and pre-rendered centroid ratios (ROUND 15),
# the stock font-based chain in registerClefs is correct again, so the
# stock ClefBuilder is used unpatched. The §18 patch file
# teavm-fork/clefbuilder-glyph-bounds.patch is kept as a historical
# artifact. If the §19 metrics ever regress, re-adding ROUND 14 restores
# the §18 behaviour (clef boxes 1px off desktop, clefStop within 2px).
# (No code here: ClefBuilder is simply not copied to patched/src, so the
# stock class from the program jars is used.)

# ============================================================ ROUND 15 (§19) ======
# Durable font fix: pre-rendered Bravura symbol metrics.
#
# (a) Bounds — in the SHIM, not here: teavm/shims/src/java/awt/font/
# TextLayout.java consults BravuraMetrics (generated from
# phase-font/symbol-metrics.json) when the font name is "Bravura", so
# every getLayout().getBounds() / getAdvance() in the pipeline returns
# real Bravura geometry: AbstractInter.getSymbolBounds, HeaderTimeBuilder,
# ClefBuilder.registerClefs, TimeCustomInter/TimeWholeInter (via
# NumDenSymbol.getDimension -> getParams -> layout bounds),
# OctaveShiftInter.computeValueDimensions, BracketInter, WedgeInter,
# AbstractPitchedInter, and MusicFont.computePointSize (so the catalog
# point size is now the DESKTOP one, ~92 for the hymn — see the
# PreRenderedTemplates mapping change in phaseb/gen_prerendered.py).
# No Audiveris patch is needed for bounds.
#
# (b) Centroid — here: ShapeSymbol.computeCentroidOffset renders the
# symbol image and takes its mass centre, but under TeaVM the image is
# blank (TextLayout.draw is a no-op), so weight is 0, xBar/weight is
# 0/0 = NaN, and getCentroid returns (0,0). The pre-rendered ratios in
# teavm.PreRenderedSymbolMetrics are the exact values Audiveris computes
# from the STANDARD_INTERLINE image (verified: manual mass-centre from
# buildImage at size 80 reproduces them with error 0.0000 for every
# shape), so returning them is desktop-identical. Applied only for plain
# (non-decorated, non-tiny) symbols: tiny/decorated variants recompute
# from a different image and stay on the original path.
text = copy_src("org/audiveris/omr/ui/symbol/ShapeSymbol.java")
text = sub(text,
           """    private void computeCentroidOffset ()
    {
        if (image == null) {
            computeImage();
        }""",
           """    private void computeCentroidOffset ()
    {
        // TEAVM (§19): pre-rendered centroid ratios for plain Bravura
        // symbols (teavm.PreRenderedSymbolMetrics) — the stub font renders
        // a blank image, so the mass-centre computation below would divide
        // 0/0 -> NaN -> centroid (0,0). The stored ratios are the exact
        // values Audiveris computes from the STANDARD_INTERLINE image.
        if (!isDecorated && !isTiny) {
            double[] c = teavm.PreRenderedSymbolMetrics.centroidOffset(
                    shape.name(), musicFamily.name());
            if (c != null) {
                centroidOffset = new Point2D.Double(c[0], c[1]);
                return;
            }
        }

        if (image == null) {
            computeImage();
        }""")
write("org/audiveris/omr/ui/symbol/ShapeSymbol.java", text)
print("All round-15 (§19 pre-rendered symbol metrics) patches applied.")

# ============================================================ ROUND 16 (§23 TextsStep / OCR bridge) ======
# Un-neuter TextsStep and wire BrowserOCR to tesseract.js via JS globals.
# Design (see teavm/FIXES.md §23): TeaVM @JSBody is synchronous and tesseract.js
# is async, so a live await inside Wasm is impossible. Two-phase run:
#   phase 1 (TeavmMain, no __ocrText): run LOAD..TEXTS; SheetScanner builds
#     the clean image (NO_STAFF, inters erased, staff cores blanked) exactly
#     as on desktop; OcrUtil.scan hands it to BrowserOCR.recognize, which
#     exports the (10px-margined) grey bytes to JS and returns no lines.
#   JS (runner): PNG-encodes the bytes, runs tesseract.js (legacy engine,
#     70 dpi, PSM 3 = MULTI_BLOCK, language from __ocrLang), formats the
#     L/W/C rows BrowserOCR.parse consumes, sets __ocrText.
#   phase 2 (fresh module load, __ocrText set): full run LOAD..PAGE+export;
#     recognize() parses the prefed text; TextBuilder attaches lyrics.
# LANGUAGES is widened to the six PR 5 codes — the data itself is loaded
# JS-side by the runner, the Java set only gates supports(). parse() is
# made package-visible so the desktop TestOcr harness can call the exact
# same parser (bridge-fidelity comparison, §23.4).
# ---------------------------------------------------------------------------

# --- TextsStep: restore stock (undo ROUND 2 neutering) ---
text = copy_src(R2[37])
write(R2[37], text)
print("  TextsStep restored to stock")

# --- OcrUtil: BrowserOCR instead of null ---
text = (OUT / "org/audiveris/omr/text/OcrUtil.java").read_text()
text = sub(text,
           'private static final OCR ocr = null; // TEAVM: no OCR (Tesseract/JNA unavailable)',
           'private static final OCR ocr = BrowserOCR.getInstance(); // TEAVM (§23): BrowserOCR bridged to tesseract.js via JS globals')
write("org/audiveris/omr/text/OcrUtil.java", text)

# --- BrowserOCR: JSBody bridge + wider LANGUAGES + package-visible parse ---
text = (OUT / "org/audiveris/omr/text/BrowserOCR.java").read_text()
text = sub(text,
           "import java.util.TreeSet;",
           "import java.util.TreeSet;\n\nimport org.teavm.jso.JSBody;\n\nimport java.util.Base64;")
# score-reader main lists six languages here already (its language picker); older patches
# list only "eng". Either way the TeaVM version is a plain TreeSet of the six.
text = re.sub(r'    private static final SortedSet<String> LANGUAGES = Collections.unmodifiableSortedSet\(\r?\n'
              r'            new TreeSet<>\(List.of\((?:"eng"|"deu", "eng", "fra", "ita", "lat", "spa")\)\)\);',
              '    private static final SortedSet<String> LANGUAGES = Collections.unmodifiableSortedSet(\n'
              '            new TreeSet<>(List.of("eng")));', text, count=1)
text = sub(text,
           '''    private static final SortedSet<String> LANGUAGES = Collections.unmodifiableSortedSet(
            new TreeSet<>(List.of("eng")));''',
           '''    // TEAVM (§23): no Collections.unmodifiableSortedSet in the TeaVM classlib;
    // a plain TreeSet serves (nothing mutates LANGUAGES).
    private static final SortedSet<String> LANGUAGES =
            new TreeSet<>(List.of("eng", "deu", "fra", "ita", "spa", "lat"));''')
text = sub(text,
           '''    /**
     * Read the text in a grey image: answered by the web page (the browser build replaces this
     * with the text tesseract.js read, teavm/patched/make_patches.py).
     *
     * @return one line per item, in order: "L x0 y0 x1 y1 bx0 by0 bx1 by1 height" for a text line
     *         (its bounds, baseline and row height), "W x0 y0 x1 y1 confidence text" for each of
     *         its words, and "C x0 y0 x1 y1 text" for each of a word's characters
     */
    private static native String read (byte[] grey,
                                       int width,
                                       int height,
                                       String languages,
                                       int pageSegMode);''',
           '''    // TEAVM (§23): no native call. The OCR text is pre-run in JS
    // (tesseract.js, async in the runner) and handed back via a global;
    // see TeavmMain's two-phase run. @JSBody is synchronous, so a live
    // await inside Wasm is impossible; the split-phase design is the
    // bridge. On the first (phase-1) call there is no text yet: export
    // the clean image for the runner to OCR and return no lines.
    @JSBody(params = {}, script = "return globalThis.__ocrText;")
    private static native String readOcrText ();

    @JSBody(params = { "b64", "w", "h", "lang", "psm" },
            script = "globalThis.__ocrImageB64 = b64; globalThis.__ocrImageW = w; globalThis.__ocrImageH = h; globalThis.__ocrLang = lang; globalThis.__ocrPsm = psm;")
    private static native void setOcrImage (String b64,
                                            int w,
                                            int h,
                                            String lang,
                                            int psm);''')
text = sub(text,
           '''        final byte[] pixels = (byte[]) grey.getRaster().getDataElements(0, 0, width, height, null);
        final int mode = (layoutMode == LayoutMode.SINGLE_BLOCK) ? PSM_SINGLE_BLOCK : PSM_AUTO;
        final List<TextLine> lines = parse(sheet, read(pixels, width, height, langSpec, mode));''',
           '''        final byte[] pixels = (byte[]) grey.getRaster().getDataElements(0, 0, width, height, null);
        final int mode = (layoutMode == LayoutMode.SINGLE_BLOCK) ? PSM_SINGLE_BLOCK : PSM_AUTO;

        // TEAVM (§23): two-phase OCR. Phase 1: no prefed text yet — export
        // the clean image (already white-margined by OcrUtil.scan) for the
        // runner's tesseract.js and return no lines. Phase 2: parse the
        // prefed L/W/C text exactly as a native call's answer would be
        // parsed. Coordinates are in the margined image; the topLeft
        // translation below (stock) shifts them back to sheet coordinates.
        final String prefed = readOcrText();

        if ((prefed == null) || prefed.isEmpty()) {
            setOcrImage(Base64.getEncoder().encodeToString(pixels), width, height, langSpec, mode);
            return new ArrayList<>();
        }

        final List<TextLine> lines = parse(sheet, prefed);''')
text = sub(text,
           "    /** The page's answer as Audiveris's lines, words and characters, as TesseractOrder builds them. */\n    private static List<TextLine> parse (Sheet sheet,",
           "    /** The page's answer as Audiveris's lines, words and characters, as TesseractOrder builds them. */\n    // TEAVM (§23): package-visible (was private) so the desktop TestOcr\n    // harness can call the exact same parser — bridge-fidelity check.\n    static List<TextLine> parse (Sheet sheet,")
write("org/audiveris/omr/text/BrowserOCR.java", text)

# --- TextBuilder, TextRole: compiled from source here, as they are ---
text = copy_src("org/audiveris/omr/text/TextBuilder.java")
write("org/audiveris/omr/text/TextBuilder.java", text)
text = copy_src("org/audiveris/omr/text/TextRole.java")
write("org/audiveris/omr/text/TextRole.java", text)
print("All round-16 (§23 OCR bridge) patches applied.")

# ============================================================ ROUND 17 (§23: metronome pattern)
# TeaVM's java.util.regex doesn't support the "\x{hhhh}" escape, which
# MetronomeInter.beatUnitRegexp() builds its pattern from (MusicPane.musicCodes),
# and a failed pattern stops the read. The literal code points are used
# instead, class-special ones backslash-escaped: the same match set.
# ---------------------------------------------------------------------------
text = (OUT / "org/audiveris/omr/sig/inter/MetronomeInter.java").read_text()
text = sub(text,
           '''     * @return the regexp string, like: "\\\\x{FFFF}" for each code
     */
    private static String beatUnitRegexp ()
    {
        return MusicPane.musicCodes.stream().map(c -> "\\\\x{" + Integer.toHexString(c) + "}") //
                .collect(Collectors.joining());
    }''',
           '''     * @return the regexp string, the literal code point characters
     *         (TEAVM §23: TeaVM regex rejects the "\\\\x{hhhh}" escape)
     */
    private static String beatUnitRegexp ()
    {
        return MusicPane.musicCodes.stream().map(MetronomeInter::escapeForCharClass) //
                .collect(Collectors.joining());
    }

    // TEAVM (§23): literal code point for a negated character class, with
    // class-special characters backslash-escaped. Same match set as the
    // original "\\\\x{hhhh}" form; desktop-neutral.
    private static String escapeForCharClass (int codePoint)
    {
        final String s = new String(Character.toChars(codePoint));

        if ((codePoint == '\\\\') || (codePoint == ']') || (codePoint == '^')
                || (codePoint == '-')) {
            return "\\\\" + s;
        }

        return s;
    }''')
write("org/audiveris/omr/sig/inter/MetronomeInter.java", text)
print("  MetronomeInter beatUnitRegexp literal-chars (§23 trap 3)")

# ============================================================ ROUND 33 (§30: head-erasure fix)
# PageCleaner.visit(HeadInter) erases a note head by painting its Bravura
# glyph white (paintSymbol -> OmrFont.paint -> TextLayout.draw), and the font
# shim's TextLayout.draw draws nothing, so here the heads would stay in the
# skeleton the slurs are traced from. paintSymbol is kept, and the head is
# also erased geometrically: its glyph runs plus an ellipse over the glyph
# bounds (ROUND 36 sets its size), which also breaks the staff line through
# the head as the desktop's paint does. On the desktop both whiten pixels
# paintSymbol already whitened.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """        final Glyph glyph = head.getGlyph();
        final Point2D center = (glyph != null) ? glyph.getCenter2D() : head.getCenter2D();
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);
    }
""",
           """        final Glyph glyph = head.getGlyph();
        final Point2D center = (glyph != null) ? glyph.getCenter2D() : head.getCenter2D();
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);

        // §30 (TeaVM): paintSymbol draws through TextLayout.draw, a no-op
        // in the TeaVM font shim, so the head would stay in the skeleton.
        // Erase it geometrically as well: the
        // glyph runs (exact head ink, including the slanted tips) plus an
        // ellipse inscribed in the glyph bounds enlarged 1.1x (the desktop
        // paint's enlargement), which also breaks the staff-line segment
        // through the head the way the desktop oval paint does. On desktop
        // both additions whiten pixels paintSymbol already whitened.
        if (glyph != null) {
            processGlyph(glyph);
        }

        final java.awt.Rectangle bounds = (glyph != null) ? glyph.getBounds() : head.getBounds();
        final double cx = bounds.getCenterX();
        final double cy = bounds.getCenterY();
        final double w = bounds.getWidth() * constants.enlargementRatio.getValue();
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue();
        g.fill(new java.awt.geom.Ellipse2D.Double(cx - (w / 2), cy - (h / 2), w, h));
    }
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
print("  PageCleaner head-erasure fix (§30)")

# ============================================================ ROUND 36 (§32: ellipse enlargement 1.1 -> 1.32)
# The desktop's paint covers the Bravura glyph at 1.1x (enlargementRatio) plus
# an antialiased fringe and the slanted tips of the head, which reach 1.2 times
# past a 1.1x ellipse. So the ellipse is the glyph bounds times 1.32, which
# covers nearly all of it.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """        final double w = bounds.getWidth() * constants.enlargementRatio.getValue();
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue();
""",
           """        // §32: the desktop paint reaches 1.2 times past a 1.1x ellipse
        // (antialiasing, the head's slanted tips), so 1.1 x 1.2.
        final double w = bounds.getWidth() * constants.enlargementRatio.getValue() * 1.2;
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue() * 1.2;
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
print("  PageCleaner ellipse enlargement 1.32x (§32)")

# ============================================================ ROUND 51 (strict mode)
# TeaVM strict mode (Spike -Dteavm.strict=true) checks casts, and TeaVM 0.16's own
# Class.getAnnotation path (TClass.getDeclaredAnnotations) fails such a check: the first
# BINARY step dies with a ClassCastException in RunTableFactory.MyAdapter.isThreadSafe, which
# reads @ThreadSafe off the pixel filter's class. The answer only picks RunsRetriever's
# sequential or parallel loop, and TeaVM runs executors inline on one thread, so both loops
# produce the same runs: answer "not thread safe" (the sequential loop) without the lookup.
text = copy_src("org/audiveris/omr/run/RunTableFactory.java")
text = replace_method(text, r"public boolean isThreadSafe \(\)", """public boolean isThreadSafe ()
        {
            // TEAVM: no annotation lookup (fails TeaVM's strict-mode cast checks); executors
            // run inline on one thread here, so the sequential loop gives the same runs
            return false;
        }""")
write("org/audiveris/omr/run/RunTableFactory.java", text)
print("  RunTableFactory.isThreadSafe without annotations (ROUND 51, strict mode)")

