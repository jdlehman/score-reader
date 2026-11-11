#!/usr/bin/env python3
"""Copy Audiveris 5.11 sources and apply TeaVM-0.16.0 patches.

Reads from the read-only clone at ~/workspace/score-reader-spikes/repo/.work/audiveris/
and writes patched copies to ~/workspace/score-reader-spikes/teavm-wasm/teavm/patched/src/
(never touches the repo).

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
  UriUtil:         toURI(URI, String) prints the child file before throwing
                   on a null parent (§13 DIAG: RES_URI is null in WASM, and
                   TeaVM stack traces cannot name the caller).
  OmrFont:         createFont catches IllegalArgumentException from the res
                   lookup too, falling through to the platform font (§13).
  Book:            getStubsToUpgrade returns an empty set for a fresh book
                   (no book path, so no saved .omr project can exist; the
                   original logic would return empty anyway, but
                   getStubsWithTableFiles traps first on Main.getCli() (§12).
                   Books loaded from a project keep the original logic, so
                   the method behaves exactly as before on the desktop.
  DIAG14:          diagnostic prints only (§14): brackets every link of the
                   BINARY -> getBufferedImage -> new ByteProcessor chain in
                   Picture.buildNoStaffBuffer / getSource, plus the
                   pixelFilter in BeamsBuilder.buildBeams, to name which
                   link produces the null pixels array that traps BEAMS.
  FloodFiller:     fill rewritten as an iterative explicit-stack flood
                   fill (§16): same pixels as the recursive version, no
                   recursion, so it cannot overflow the Wasm call stack
                   in HEADS template building. Desktop-neutral (verified
                   pixel-identical on desktop before any Node run, §16).
"""
import pathlib, re, shutil, sys

REPO = pathlib.Path.home() / "workspace/score-reader-spikes/repo/.work/audiveris/app/src/main/java"
OUT = pathlib.Path(__file__).resolve().parent / "src"

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
# DIAG10 (2026-11-09): getFolder returns null, but the derived folders dereference it
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
# DIAG11 (2026-11-09): TeaVM generates class-name metadata only for types
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
# DIAG11 (2026-11-09): BookManager$Constants initialises folder defaults from
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
# DIAG11 (2026-11-09): loadAliasPatterns() builds its URI array by
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
# DIAG13 (2026-11-09): UriUtil.toURI(URI, String) throws
# IllegalArgumentException("Parent is null") when WellKnowns.RES_URI is
# null in WASM (RES_URI is hard-coded null above: no resources). The
# BEAMS step hits it twice — once inside SpotsBuilder (caught, WARN) and
# once fatally (ExecutionException) — and TeaVM stack traces are FakeClass
# frames that cannot name the caller, so print the child file before
# throwing: the child name identifies the caller (Bravura.otf =
# OmrFont.createFont, a model zip = BasicClassifier, ...).
text = (REPO / FILES[11]).read_text()
text = sub(text, '''            // Make sure parent ends with a '/'
            if (parent == null) {
                throw new IllegalArgumentException("Parent is null");
            }''',
           '''            // Make sure parent ends with a '/'
            if (parent == null) {
                // TEAVM §13 DIAG: name the caller by its child file.
                System.out.println("DIAG13 toURI null parent child=" + child);
                throw new IllegalArgumentException("Parent is null");
            }''')
write(FILES[11], text)

# ------------------------------------------------------------------ OmrFont
# TEAVM §13: OmrFont.createFont looks the music font up in the "res"
# folder via UriUtil.toURI(WellKnowns.RES_URI, fileName) — but RES_URI is
# null in WASM (no resources), so toURI throws IllegalArgumentException
# ("Parent is null"), which the existing catch (MalformedURLException
# only) does not catch. Both occurrences in the full-out20/21 runs are
# this call with child=Bravura.otf (BlackHeadSizer via MusicFont, then
# the BEAMS doSystem path via AbstractBeamInter). Catch the
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
text = sub(text, 'private static final OCR ocr = Boolean.getBoolean("scorereader.inBrowser") ? BrowserOCR.getInstance()\n            : TesseractOCR.getInstance();',
           'private static final OCR ocr = null; // TEAVM: no OCR (Tesseract/JNA unavailable)')
text = sub(text, "origin.translate(-margin, -margin);",
           "origin.x -= margin; origin.y -= margin; // TEAVM: Point.translate missing")
write("org/audiveris/omr/text/OcrUtil.java", text)
text = (OUT / "org/audiveris/omr/text/OcrUtil.java").read_text()
text = sub(text,
           "        final List<TextLine> lines = ocr.recognize(sheet, bi, origin, languages, layoutMode, label);",
           """        final List<TextLine> lines = ocr.recognize(sheet, bi, origin, languages, layoutMode, label);
        System.out.println("DIAG24 OcrUtil.scan recognized lines=" + ((lines == null) ? -1 : lines.size()));""")
write("org/audiveris/omr/text/OcrUtil.java", text)

print("All round-2 patches applied.")

# ============================================================ ROUND 3 =======
# Copy the repo's own patched sources as-is (0001-score-reader.patch).
# The source tree is patched but .work/lib/audiveris.jar is upstream, so
# compiling patched Sheet/Book against the jar fails (e.g. Picture.lighten).
# These 13 are the patch files not already handled above (Book/Sheet/OcrUtil
# are patched in rounds 1-2).
# ---------------------------------------------------------------------------
COPY_ASIS = [
    "org/audiveris/omr/CLI.java",
    "org/audiveris/omr/Main.java",
    "org/audiveris/omr/ScoreReaderHook.java",
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
text = replace_method_re(text, r"public boolean reachBookStep \(final OmrStep target,\s*\n\s*final boolean force,\s*\n\s*final List<SheetStub> theStubs,\s*\n\s*final boolean swap\)",
    "public boolean reachBookStep (final OmrStep target,\n                                  final boolean force,\n                                  final List<SheetStub> theStubs,\n                                  final boolean swap)\n    {\n        return false; // TEAVM: book steps not driven in WASM demo\n    }")
text = replace_method_re(text, r"public void resetTo \(OmrStep step\)",
    "public void resetTo (OmrStep step)\n    {\n        // TEAVM: no reset in WASM demo\n    }")
text = replace_method_re(text, r"private void checkRadixChange \(Path bookPath\)",
    "private void checkRadixChange (Path bookPath)\n    {\n        // TEAVM: no renaming in WASM\n    }")
text = replace_method_re(text, r"public static void closeFileSystem \(FileSystem fileSystem\)",
    "public static void closeFileSystem (FileSystem fileSystem)\n    {\n        // TEAVM: no ZipFS in WASM\n    }")
# --- Book: getStubsToUpgrade returns empty for a fresh book (§12) ---
# DIAG11 (2026-11-09): Book.initTransients -> getStubsToUpgrade ->
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
write("org/audiveris/omr/glyph/dynamic/SectionCompound.java", text)

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

# ============================================================ ROUND 7 =======
# DIAG14 (2026-11-09, §14): name the upstream link that produces the null
# pixels array in the NO_STAFF ByteProcessor (trap in
# AreaMask$ForeCounter.process, BEAMS doSystem, full-out22). Prints bracket
# every link of the chain BINARY -> getBufferedImage -> new ByteProcessor:
#   getSource entry: cached (WeakReference hit) vs rebuild, per key
#   getSource BINARY: image branch vs binarized branch, binarized pixels
#   buildNoStaffBuffer: BINARY pixels, bin image type / DataBuffer class /
#     getData() null-ness, and the returned NO_STAFF pixels
#   BeamsBuilder.buildBeams / buildCueBeams: pixelFilter pixels null-ness
# Diagnostic only; remove/keep as the §14 verdict directs. No behaviour
# change: prints only, plus one local (noStaff14) in buildNoStaffBuffer.
# ---------------------------------------------------------------------------
# --- Picture.java (already copied in round 3; operate on OUT) ---
text = read_out("org/audiveris/omr/sheet/Picture.java")
text = sub(text,
           "    public ByteProcessor getSource (SourceKey key)\n    {\n        ByteProcessor src = getStrongRef(key);",
           "    public ByteProcessor getSource (SourceKey key)\n    {\n        ByteProcessor src = getStrongRef(key);\n        System.out.println(\"DIAG14 getSource \" + key + \" cachedNull=\" + (src == null));")
text = sub(text,
           "                    BufferedImage image = getImage(ImageKey.BINARY);",
           "                    BufferedImage image = getImage(ImageKey.BINARY);\n                    System.out.println(\"DIAG14 getSource BINARY imageNull=\" + (image == null)\n                            + (image == null ? \"\" : (\" type=\" + image.getType())));")
text = sub(text,
           "                            src = binarized(gray);",
           "                            src = binarized(gray);\n                            System.out.println(\"DIAG14 getSource BINARY binarized null=\" + (src == null)\n                                    + (src == null ? \"\" : (\" pixelsNull=\" + (src.getPixels() == null))));")
text = sub(text,
           "        final ByteProcessor src = getSource(SourceKey.BINARY);\n        final BufferedImage img = src.getBufferedImage();",
           "        final ByteProcessor src = getSource(SourceKey.BINARY);\n        System.out.println(\"DIAG14 buildNoStaffBuffer binSrc null=\" + (src == null)\n                + (src == null ? \"\" : (\" w=\" + src.getWidth() + \" h=\" + src.getHeight()\n                + \" pixelsNull=\" + (src.getPixels() == null))));\n        final BufferedImage img = src.getBufferedImage();\n        System.out.println(\"DIAG14 buildNoStaffBuffer binImg null=\" + (img == null));\n        if (img != null) {\n            java.awt.image.DataBuffer db14 = img.getRaster().getDataBuffer();\n            String db14Info = db14.getClass().getName();\n            if (db14 instanceof java.awt.image.DataBufferByte) {\n                byte[] d14 = ((java.awt.image.DataBufferByte) db14).getData();\n                db14Info += \" dataNull=\" + (d14 == null) + \" dataLen=\" + (d14 == null ? -1 : d14.length);\n            }\n            System.out.println(\"DIAG14 buildNoStaffBuffer binImg type=\" + img.getType()\n                    + \" w=\" + img.getWidth() + \" h=\" + img.getHeight() + \" db=\" + db14Info);\n        }")
text = sub(text,
           "        g.dispose();\n\n        return new ByteProcessor(img);",
           "        g.dispose();\n\n        ByteProcessor noStaff14 = new ByteProcessor(img);\n        System.out.println(\"DIAG14 buildNoStaffBuffer noStaff pixelsNull=\" + (noStaff14.getPixels() == null)\n                + \" w=\" + noStaff14.getWidth() + \" h=\" + noStaff14.getHeight());\n        return noStaff14;")
write("org/audiveris/omr/sheet/Picture.java", text)

# --- BeamsBuilder.java (new to the patched set; wins over audiveris.jar
# because patched/classes precedes it on the program classpath) ---
text = copy_src("org/audiveris/omr/sheet/beam/BeamsBuilder.java")
text = sub_all(text,
               "        pixelFilter = sheet.getPicture().getSource(Picture.SourceKey.NO_STAFF);",
               "        pixelFilter = sheet.getPicture().getSource(Picture.SourceKey.NO_STAFF);\n        System.out.println(\"DIAG14 buildBeams pixelFilter null=\" + (pixelFilter == null)\n                + (pixelFilter == null ? \"\" : (\" w=\" + pixelFilter.getWidth() + \" h=\" + pixelFilter.getHeight()\n                + \" pixelsNull=\" + (pixelFilter.getPixels() == null))));")
write("org/audiveris/omr/sheet/beam/BeamsBuilder.java", text)
print("All round-7 (DIAG14) patches applied.")

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
# §16: FloodFiller.fill is iterative (was recursive).
# The recursive four-neighbour fill overflows the Wasm call stack in HEADS
# template building (full-out26 dies at the 216 rebuild at Node's default
# 984 kB stack; §15 confirmed depth exhaustion, and no --stack-size passes
# the 432 rebuild, and browsers expose no --stack-size flag at all).
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
        // TEAVM §16: iterative explicit-stack flood fill (was recursive).
        // The recursive version overflows the Wasm call stack in HEADS
        // template building (216 rebuild dies at Node's default 984 kB
        // stack; §15). Same pixels, no recursion: a pixel is marked at
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

# ============================================================ ROUND 10 (DIAG16) ======
# DIAG16: prove/disprove the blank-stub-template hypothesis for the runaway
# TemplateFactory rebuild loop (full-out27: NOTEHEAD_VOID rebuilds 108 -> 27648,
# then "requested new array is too large"). buildDistances returns null iff
# img(0,0)==HOLE after addHoles/adjustHoles; if the stub font renders a blank
# glyph the whole image is BACK, the hole-seed fill covers everything incl.
# (0,0), and processSymbol recurses with holeLargerRatio=2 forever (no cap
# in upstream code). Count FORE pixels per buildDistances call.
rel_tf = "org/audiveris/omr/image/TemplateFactory.java"
text = read_out(rel_tf)
text = sub(text,
           """                // Safety check: the upper left pixel cannot be a hole
                if (img.getRGB(0, 0) == HOLE) {
                    return null;
                }""",
           """                // DIAG16: blank-template hypothesis check (stub font renders no glyph?)
                {
                    int fore16 = 0;
                    for (int yy = 0; yy < img.getHeight(); yy++) {
                        for (int xx = 0; xx < img.getWidth(); xx++) {
                            if (img.getRGB(xx, yy) == FORE) {
                                fore16++;
                            }
                        }
                    }
                    System.out.println("DIAG16 buildDistances shape=" + shape + " w=" + img.getWidth()
                            + " h=" + img.getHeight() + " fore=" + fore16
                            + " rgb00=" + Integer.toHexString(img.getRGB(0, 0)));
                }

                // Safety check: the upper left pixel cannot be a hole
                if (img.getRGB(0, 0) == HOLE) {
                    return null;
                }""")
write(rel_tf, text)
print("All round-10 (DIAG16 buildDistances) patches applied.")

# ============================================================ ROUND 11 (§16 cap) ======
# Cap TemplateFactory.Builder.processSymbol rebuild loop. Upstream recurses without
# limit on holes-detection failure (buildDistances null), which terminates on
# desktop (a real music font yields an enclosed hole within a couple of
# doublings) but runs away under TeaVM: the stub font renders a blank glyph
# (DIAG16: fore=0 at every resolution, rgb00=HOLE), so buildDistances returns
# null forever and the image doubles (holeLargerRatio=2) until allocation fails
# ("requested new array is too large", full-out27/28). After ratio 8, give up
# and return an empty key-point list: Template.getKeyPoints() consumers iterate
# the list, so an empty list simply scores no heads for that shape (the Phase A
# expectation: stub fonts, 0 heads). Desktop-neutral: with a real font the loop
# terminates before the cap, so behaviour is unchanged.
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
# Design (see FORK_FIX §23): TeaVM @JSBody is synchronous and tesseract.js
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
# DIAG24 (§23): trace TextsStep entry/exit while debugging the phase-2 trap.
text = sub(text,
           '''        if (OcrUtil.getOcr().isAvailable()) {
            lines.addAll(scanner.scanSheet());
        } else {''',
           '''        System.out.println("DIAG24 TextsStep doProlog ocrAvailable=" + OcrUtil.getOcr().isAvailable());

        if (OcrUtil.getOcr().isAvailable()) {
            lines.addAll(scanner.scanSheet());
            System.out.println("DIAG24 TextsStep doProlog lines=" + lines.size());
        } else {''')
text = sub(text,
           '''        // Process texts at system level
        new TextBuilder(system, null).processSystem(context.buffer, context.textLines);''',
           '''        // Process texts at system level
        System.out.println("DIAG24 TextsStep doSystem #" + system.getId()
                + " lines=" + ((context.textLines == null) ? -1 : context.textLines.size()));
        new TextBuilder(system, null).processSystem(context.buffer, context.textLines);
        System.out.println("DIAG24 TextsStep doSystem #" + system.getId() + " done");''')
write(R2[37], text)
print("  TextsStep restored to stock (+DIAG24)")

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
text = sub(text,
           '''    private static final SortedSet<String> LANGUAGES = Collections.unmodifiableSortedSet(
            new TreeSet<>(List.of("eng")));''',
           '''    // TEAVM (§23): no Collections.unmodifiableSortedSet in the TeaVM classlib;
    // a plain TreeSet serves (nothing mutates LANGUAGES).
    private static final SortedSet<String> LANGUAGES =
            new TreeSet<>(List.of("eng", "deu", "fra", "ita", "spa", "lat"));''')
text = sub(text,
           '''    /**
     * Implemented by the web page (a CheerpJ native): read the text in a grey image.
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
           '''    // TEAVM (§23): no CheerpJ native call. The OCR text is pre-run in JS
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
        // prefed L/W/C text exactly as the CheerpJ path parses the page's
        // answer. Coordinates are in the margined image; the topLeft
        // translation below (stock) shifts them back to sheet coordinates.
        final String prefed = readOcrText();
        System.out.println("DIAG24 BrowserOCR prefed len=" + ((prefed == null) ? -1 : prefed.length()));

        if ((prefed == null) || prefed.isEmpty()) {
            setOcrImage(Base64.getEncoder().encodeToString(pixels), width, height, langSpec, mode);
            return new ArrayList<>();
        }

        final List<TextLine> lines = parse(sheet, prefed);
        System.out.println("DIAG24 BrowserOCR parse returned lines=" + lines.size());''')
text = sub(text,
           "    /** The page's answer as Audiveris's lines, words and characters, as TesseractOrder builds them. */\n    private static List<TextLine> parse (Sheet sheet,",
           "    /** The page's answer as Audiveris's lines, words and characters, as TesseractOrder builds them. */\n    // TEAVM (§23): package-visible (was private) so the desktop TestOcr\n    // harness can call the exact same parser — bridge-fidelity check.\n    static List<TextLine> parse (Sheet sheet,")
write("org/audiveris/omr/text/BrowserOCR.java", text)
text = (OUT / "org/audiveris/omr/text/BrowserOCR.java").read_text()
text = sub(text,
           """        final List<TextLine> lines = new ArrayList<>();
        TextLine line = null;""",
           """        System.out.println("DIAG24 BrowserOCR.parse entry answerLen=" + ((answer == null) ? -1 : answer.length()));
        final List<TextLine> lines = new ArrayList<>();
        TextLine line = null;""")
write("org/audiveris/omr/text/BrowserOCR.java", text)

# --- TextBuilder: DIAG24 stage prints (temporary §23 diagnostic) ---
text = copy_src("org/audiveris/omr/text/TextBuilder.java")
for _old, _msg in [
        ("        final List<TextLine> validLines = getSystemValidLines(sheetLines);",
         "DIAG24 TextBuilder validLines="),
        ("        final List<TextLine> longLines = mergeRawLines(validLines);",
         "DIAG24 TextBuilder longLines="),
        ("        purgeExternalLines(longLines);",
         "DIAG24 TextBuilder purged"),
        ("        partitionPartLines(longLines);",
         "DIAG24 TextBuilder partitioned"),
        ("        guessLongRoles(longLines);",
         "DIAG24 TextBuilder roles guessed"),
        ("        mapLyricLines(longLines);",
         "DIAG24 TextBuilder lyric lines mapped"),
        ("        final List<TextLine> lines = recomposeLines(longLines);",
         "DIAG24 TextBuilder recomposed lines="),
        ("        final List<Section> relSections = getSections(buffer, lines);",
         "DIAG24 TextBuilder sections="),
        ("        mapGlyphs(lines, relSections, null);",
         "DIAG24 TextBuilder glyphs mapped"),
        ("        createSystemInters();",
         "DIAG24 TextBuilder inters created"),
        ("        system.numberLyricLines();",
         "DIAG24 TextBuilder lyric lines numbered"),
]:
    _count = "lines.size()" if "lines=" in _msg or "validLines" in _msg or "longLines" in _msg or "recomposed" in _msg else ""
    if _msg.endswith("="):
        _var = "validLines" if "validLines" in _msg else ("longLines" if "longLines" in _msg else ("lines" if "recomposed" in _msg else "relSections"))
        text = sub(text, _old, _old + "\n        System.out.println(\"" + _msg + "\" + " + _var + ".size());")
    else:
        text = sub(text, _old, _old + "\n        System.out.println(\"" + _msg + "\");")
# DIAG24: per-line guessRole entry (which long line traps in TextRole.guess?)
text = sub(text,
           """    private void guessRole (TextLine line)
    {
        try {""",
           """    private void guessRole (TextLine line)
    {
        System.out.println("DIAG24 guessRole value=[" + line.getValue() + "] words=" + line.getWords().size());
        System.out.println("DIAG24 guessRole bounds=" + line.getBounds());
        try {""")
write("org/audiveris/omr/text/TextBuilder.java", text)
# DIAG24: bisect TextRole.guess (which long line traps, and where?)
text = copy_src("org/audiveris/omr/text/TextRole.java")
text = sub(text,
           """        // Decisions ...
        switch (systemPosition) {""",
           """        // Decisions ...
        System.out.println("DIAG24 guess sysPos=" + systemPosition + " partPos=" + partPosition
                + " leftOf=" + leftOfStaves + " isAllChords=" + isAllChords
                + " isMainlyItalic=" + isMainlyItalic + " closeToStaff=" + closeToStaff
                + " farFromStaff=" + farFromStaff + " pageCentered=" + pageCentered
                + " shortSentence=" + shortSentence + " tinySentence=" + tinySentence
                + " firstSystem=" + firstSystem + " lastSystem=" + lastSystem);
        switch (systemPosition) {""")
write("org/audiveris/omr/text/TextRole.java", text)
print("All round-16 (§23 OCR bridge) patches applied.")

# ============================================================ ROUND 17 (§23 trap 3: metroPattern \x{...})
# Trap (hymn crop, full-out49 phase 2): TextRole.guess → MetronomeInter.isLikely
# threw PatternSyntaxException at index 17 of metroPat — TeaVM's
# java.util.regex does not support the "\x{hhhh}" escape. beatUnitRegexp()
# builds metroPat from MusicPane.musicCodes as "\x{e0a2}" etc. The first
# isLikely() call (line 2) failed class init and was caught by guessRole;
# the second call (line 3) found metroPattern null and trapped the module
# (uncatchable Wasm null deref). Fix: emit the literal code points instead
# of "\x{...}" escapes. Identical match set on desktop (same characters in
# the same negated class); class-special code points are backslash-escaped.
# MusicPane.musicCodes are SMuFL PUA code points (BMP); Character.toChars
# handles supplementary code points correctly anyway.
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

# ============================================================ ROUND 18 (§23 trap 4: false TUPLET_THREE kept in Wasm, discarded on desktop)
# Divergence (hymn crop, full-out49): Wasm keeps a TUPLET_THREE at
# (1876,586,33,23) grade 0.6846 — a lyric-word glyph ("fore") — while
# desktop-with-identical-OCR discards its tuplet candidate as isolated
# (TupletInter.createValid: no head chord intersects the grown box).
# The kept tuplet corrupts rhythm: divisions 1 -> 3, triplet quarters in
# the bass, 8 tuplets / 12 time-mods on the full page. Instrument
# createValid on both sides (same file compiled into phase23/classes for
# the desktop harness) to compare glyph box, grown box, scale, and the
# nearby chords that decide the keep/discard.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sig/inter/TupletInter.java")
text = sub(text,
           '''        if (nearby.isEmpty()) {
            logger.debug("Discarding isolated tuplet candidate glyph#{}", glyph.getId());''',
           '''        System.out.println("DIAG24 TupletInter.createValid glyph#" + glyph.getId()
                + " box=" + glyph.getBounds() + " grown=" + luBox
                + " dxPx=" + scale.toPixels(constants.maxTupletChordDx)
                + " dyPx=" + scale.toPixels(constants.maxTupletChordDy)
                + " interline=" + scale.getInterline()
                + " nearby=" + nearby.size() + " grade=" + grade);
        for (Inter chord : nearby) {
            System.out.println("DIAG24 TupletInter nearby chord box=" + chord.getBounds());
        }

        if (nearby.isEmpty()) {
            logger.debug("Discarding isolated tuplet candidate glyph#{}", glyph.getId());''')
write("org/audiveris/omr/sig/inter/TupletInter.java", text)
print("  TupletInter.createValid DIAG24 (§23 trap 4)")

# ============================================================ ROUND 19 (§23 trap 4 diagnostic: which text glyphs differ)
# Wasm keeps a TUPLET_THREE built from lyric-glyph sections ("fore": the
# candidate at (1876,586,33x23) spans the OCR 'o' + 'r' char boxes);
# desktop builds no such candidate. retrieveSections builds one glyph per
# TextChar (charBox.contains(section) gate) plus one per word, all from the
# clean-buffer sections — print each built glyph (box, id, section count)
# on both sides (same file compiled into phase23/classes for desktop) to
# see exactly which glyph differs and how.
# ---------------------------------------------------------------------------
text = (OUT / "org/audiveris/omr/text/TextBuilder.java").read_text()
text = sub(text,
           '''                Glyph charGlyph = sheet.getGlyphIndex().registerOriginal(absGlyph);
                system.addFreeGlyph(charGlyph);''',
           '''                Glyph charGlyph = sheet.getGlyphIndex().registerOriginal(absGlyph);
                System.out.println("DIAG24 charGlyph charBox=" + charBox + " box=" + charGlyph.getBounds()
                        + " id=" + charGlyph.getId() + " nsec=" + charSections.size());
                system.addFreeGlyph(charGlyph);''')
text = sub(text,
           '''                    // Link TextWord -> Glyph
                    word.setGlyph(wordGlyph);''',
           '''                    // Link TextWord -> Glyph
                    word.setGlyph(wordGlyph);
                    System.out.println("DIAG24 wordGlyph word=[" + word.getValue() + "] box="
                            + wordGlyph.getBounds() + " id=" + wordGlyph.getId()
                            + " nsec=" + wordSections.size());''')
write("org/audiveris/omr/text/TextBuilder.java", text)
print("  TextBuilder charGlyph/wordGlyph DIAG24 (§23 trap 4)")

# ============================================================ ROUND 20 (§23 trap 4 diagnostic: buffer vs img pixels)
# The Wasm clean IMAGE agrees pixel-for-pixel with desktop in the lyric
# area, yet the sections built from the ByteProcessor `buffer` are
# systematically sparser (char glyphs ~1px smaller, some chars empty).
# getCleanImage holds both objects (buffer shares img's raster array on
# desktop via DataBufferByte); count foreground pixels in the "fore" ROI
# (1854,574,75x35, hymn crop) from each side to see whether the sharing
# breaks under TeaVM. Same file compiled into phase23/classes for desktop.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/text/SheetScanner.java")
text = sub(text,
           '''        TextsCleaner cleaner = new TextsCleaner(buffer, img.createGraphics(), sheet);
        cleaner.eraseInters();''',
           '''        TextsCleaner cleaner = new TextsCleaner(buffer, img.createGraphics(), sheet);
        cleaner.eraseInters();

        // DIAG24 (§23 trap 4): buffer vs img foreground in the "fore" ROI
        {
            int bx = 0;
            int ix = 0;

            for (int yy = 574; yy < 609; yy++) {
                for (int xx = 1854; xx < 1929; xx++) {
                    if (buffer.getPixel(xx, yy) == 0) {
                        bx++;
                    }

                    if ((img.getRGB(xx, yy) & 0xffffff) == 0) {
                        ix++;
                    }
                }
            }

            System.out.println("DIAG24 cleanCheck bufferFore=" + bx + " imgFore=" + ix);
        }''')
write("org/audiveris/omr/text/SheetScanner.java", text)
print("  SheetScanner cleanCheck DIAG24 (§23 trap 4)")


# ============================================================ ROUND 21 (\u00a724: trap 4 diagnostic — per-word section lists)
# Trap 4: identical clean-image pixels + identical ROIs yield different
# section sets under TeaVM (162/162 char glyphs differ, 10 chars no glyph).
# Distinguish "fewer sections built" (run retrieval / RunTable / section
# building) from "same sections, different containment" (charBox.contains
# gate in retrieveSections). Three DIAG25 prints, same file compiled into
# phase23/classes for the desktop harness:
#  (a) TextBuilder.getSections: per word ROI, section count + bounds,
#      section weight sum, and a direct fore-pixel count from the buffer
#      (independent of the RunTable) — the ground truth per ROI.
#  (b) SectionFactory.createSections(buffer, roi): per small ROI, the
#      RunTable itself — per-column run lists (start+length), total runs,
#      total fore length. Gated to roi <= 300x100 so whole-sheet tables
#      built elsewhere are not dumped.
#  (c) TextBuilder.retrieveSections: per char, charBox + assigned section
#      count + bounds — the containment stage.
# ---------------------------------------------------------------------------
text = (OUT / "org/audiveris/omr/text/TextBuilder.java").read_text()
text = sub(text,
           """                Rectangle roi = word.getBounds();
                List<Section> wordSections = factory.createSections(buffer, roi);
                allSections.addAll(wordSections);""",
           """                Rectangle roi = word.getBounds();
                List<Section> wordSections = factory.createSections(buffer, roi);
                {
                    int fore = 0;
                    int wsum = 0;
                    StringBuilder sb = new StringBuilder();
                    for (int yy = roi.y; yy < roi.y + roi.height; yy++) {
                        for (int xx = roi.x; xx < roi.x + roi.width; xx++) {
                            if (buffer.getPixel(xx, yy) == 0) {
                                fore++;
                            }
                        }
                    }
                    for (Section s : wordSections) {
                        java.awt.Rectangle b = s.getBounds();
                        wsum += s.getWeight();
                        sb.append(b.x).append(",").append(b.y).append(",")
                                .append(b.width).append("x").append(b.height).append(";");
                    }
                    System.out.println("DIAG25 SEC word=[" + word.getValue() + "] roi=" + roi
                            + " nsec=" + wordSections.size() + " fore=" + fore + " wsum=" + wsum
                            + " bounds=" + sb);
                }
                allSections.addAll(wordSections);""")
text = sub(text,
           """            if (!charSections.isEmpty()) {
                wordSections.addAll(charSections);""",
           """            {
                StringBuilder sb = new StringBuilder();
                for (Section s : charSections) {
                    java.awt.Rectangle b = s.getBounds();
                    sb.append(b.x).append(",").append(b.y).append(",")
                            .append(b.width).append("x").append(b.height).append(";");
                }
                System.out.println("DIAG25 CHAR box=" + charBox + " nsec=" + charSections.size()
                        + " bounds=" + sb);
            }
            if (!charSections.isEmpty()) {
                wordSections.addAll(charSections);""")
write("org/audiveris/omr/text/TextBuilder.java", text)
print("  TextBuilder DIAG25 SEC/CHAR (\u00a724)")

text = copy_src("org/audiveris/omr/lag/SectionFactory.java")
text = sub(text,
           """        // Runs
        final RunTable runTable = new RunTableFactory(orientation).createTable(buffer, roi);
""",
           """        // Runs
        final RunTable runTable = new RunTableFactory(orientation).createTable(buffer, roi);

        // DIAG25 (\u00a724 trap 4): dump the RunTable itself for small ROIs
        if ((roi.width <= 300) && (roi.height <= 100)) {
            StringBuilder sb = new StringBuilder();
            int totalRuns = 0;
            int totalFore = 0;
            for (int col = 0; col < runTable.getSize(); col++) {
                sb.append(" col").append(col).append(":");
                for (java.util.Iterator<org.audiveris.omr.run.Run> it = runTable.iterator(col); it.hasNext();) {
                    org.audiveris.omr.run.Run r = it.next();
                    sb.append(" ").append(r.getStart()).append("+").append(r.getLength());
                    totalRuns++;
                    totalFore += r.getLength();
                }
            }
            System.out.println("DIAG25 RUNS roi=" + roi + " nseq=" + runTable.getSize()
                    + " totalRuns=" + totalRuns + " totalFore=" + totalFore + sb);
        }
""")
write("org/audiveris/omr/lag/SectionFactory.java", text)
print("  SectionFactory DIAG25 RUNS (\u00a724)")

# ============================================================ ROUND 22 (§25: Hallelujah measure-grid diagnostic — DIAG26)
# No-OCR Hallelujah already diverges (Wasm 259 notes / 11 measures vs desktop
# 275 / 14; pitched notes 217 = 217 identical, Wasm m1 = desktop m4), so the
# gap is pre-TEXTS. Both sides log "12 raw measures [4,4,4]" and desktop
# MeasureFixer expands a "multiple measure rest: 3" in system #1 (ids 1..3,
# music starts id 4); Wasm m1 width 456 = desktop m1 (211) + m4 (245) and its
# first note sits +210px right — the signature of isRealStart merging the
# first stack into the next, i.e. under TeaVM the first stack is EMPTY
# (isEmpty true: not multi-rest, actual duration 0) so the music stack merges
# into it and the 3 rest measures vanish. DIAG26 dumps, per system, the
# MultipleRestInter list (centre/bounds/count value) and, per stack, the
# getMultipleMeasureCount result, isMultiRest, actual duration, isEmpty and
# the assigned id — to distinguish "no MultipleRestInter in the SIG" from
# "centre outside the stack" from "count relation missing (count 0)".
# Same file compiled into phase23/classes for the desktop harness (§24 pattern).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/score/MeasureFixer.java")
text = sub(text,
           "import org.audiveris.omr.sig.inter.MultipleRestInter;",
           "import org.audiveris.omr.sig.inter.MeasureCountInter;\nimport org.audiveris.omr.sig.inter.MultipleRestInter;")
text = sub(text,
           """        // Multiple measure rests
        final List<Inter> multipleRests = system.getSig().inters(MultipleRestInter.class);""",
           """        // Multiple measure rests
        final List<Inter> multipleRests = system.getSig().inters(MultipleRestInter.class);

        // DIAG26 (§25 grid gap): dump the multiple rests seen in this system
        System.out.println("DIAG26 system#" + system.getId() + " multipleRests=" + multipleRests.size());
        for (Inter mri : multipleRests) {
            MultipleRestInter mr = (MultipleRestInter) mri;
            MeasureCountInter mc = mr.getMeasureCount();
            System.out.println("DIAG26 multirest center=" + mr.getCenter() + " bounds=" + mr.getBounds()
                    + " count=" + ((mc == null) ? null : mc.getValue()) + " grade=" + mr.getGrade());
        }""")
text = sub(text,
           """            // Multiple measure rest in this stack?
            final Integer multipleRestCount = stack.getMultipleMeasureCount(multipleRests);
            if (multipleRestCount != null) {
                logger.debug("multiple measure rest: {}", multipleRestCount);
                stack.setMultiRest();
            }""",
           """            // Multiple measure rest in this stack?
            final Integer multipleRestCount = stack.getMultipleMeasureCount(multipleRests);
            if (multipleRestCount != null) {
                logger.debug("multiple measure rest: {}", multipleRestCount);
                stack.setMultiRest();
            }

            // DIAG26 (§25 grid gap): the per-stack decision inputs
            System.out.println("DIAG26 stack sys=" + system.getId() + " idx=" + idx
                    + " left=" + stack.getLeft() + " right=" + stack.getRight()
                    + " count=" + multipleRestCount + " isMultiRest=" + stack.isMultiRest()
                    + " actualDur=" + stack.getActualDuration() + " isEmpty=" + isEmpty(stack));""")
text = sub(text,
           """            // Inspect stack for repeat signs
            stack.computeRepeats();""",
           """            // DIAG26 (§25 grid gap): the assigned id after the branch chain
            System.out.println("DIAG26 stackDone sys=" + system.getId() + " idx=" + idx
                    + " id=" + stack.getIdValue() + " multiRest=" + stack.isMultiRest()
                    + " inSystem=" + system.getStacks().contains(stack));

            // Inspect stack for repeat signs
            stack.computeRepeats();""")
write("org/audiveris/omr/score/MeasureFixer.java", text)
print("  MeasureFixer DIAG26 (§25 grid gap)")

# ============================================================ ROUND 23 (§26: Hallelujah measure-grid diagnostic — DIAG27)
# §25 localised the grid gap to a missing MultipleRestInter in the Wasm SIG:
# desktop system #1 builds 4 (one per staff, centre x=584, count=3), Wasm
# builds 0, so MeasureFixer never expands the first stack and the music
# stack merges into it via isRealStart. The divergence is upstream of
# MeasureFixer, in MultipleRestsBuilder.process (BEAMS step, called from
# BeamsStep.doSystem after BeamsBuilder.buildBeams) or earlier. DIAG27
# dumps, per system, every BeamInter candidate with the verdict of each
# process() gate (width vs minLength, staff, |p1|/|p2| vs 0.2, serif peaks
# per side: count + each peak's start/stop/width/top/bottom + chosen peak)
# and, in createInters, the found map, maxWidth, allSections count and
# per-serif filament build (null? true length). Prints are read-only
# (getters only; getSerifPeaks is called exactly once per beam, as before)
# — to distinguish "no beam candidate under TeaVM" (beam detection /
# classifier upstream) from "beam found but serif or count linking failed".
# Same file compiled into phase23/classes for the desktop harness (§24/§25
# pattern).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/beam/MultipleRestsBuilder.java")
text = sub(text,
           """        final SIGraph sig = system.getSig();
        final List<Inter> beams = sig.inters(BeamInter.class);

        for (Inter bi : beams) {
            final BeamInter beam = (BeamInter) bi;

            // Long enough?
            if (beam.getBounds().width < params.minLength) {
                continue;
            }""",
           """        final SIGraph sig = system.getSig();
        final List<Inter> beams = sig.inters(BeamInter.class);

        // DIAG27 (§26 grid gap): every beam candidate and each process() gate
        System.out.println("DIAG27 system#" + system.getId() + " beams=" + beams.size()
                + " minLength=" + params.minLength + " fore=" + sheet.getScale().getFore());

        for (Inter bi : beams) {
            final BeamInter beam = (BeamInter) bi;

            // Long enough?
            if (beam.getBounds().width < params.minLength) {
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " width="
                        + beam.getBounds().width + " REJECT width<minLength");
                continue;
            }""")
text = sub(text,
           """            final Point center = beam.getCenter();
            final Staff staff = system.getStaffAtOrAbove(center);
            if ((staff == null) || staff.isTablature()) {
                continue;
            }""",
           """            final Point center = beam.getCenter();
            final Staff staff = system.getStaffAtOrAbove(center);
            if ((staff == null) || staff.isTablature()) {
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                        + " REJECT staff=" + ((staff == null) ? null : staff.getId()));
                continue;
            }""")
text = sub(text,
           """            double p1 = staff.pitchPositionOf(beam.getMedian().getP1());
            if (Math.abs(p1) > constants.maxAbsolutePitch.getValue()) {
                continue;
            }

            double p2 = staff.pitchPositionOf(beam.getMedian().getP2());
            if (Math.abs(p2) > constants.maxAbsolutePitch.getValue()) {
                continue;
            }""",
           """            double p1 = staff.pitchPositionOf(beam.getMedian().getP1());
            if (Math.abs(p1) > constants.maxAbsolutePitch.getValue()) {
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                        + " staff=" + staff.getId() + " REJECT |p1|=" + Math.abs(p1));
                continue;
            }

            double p2 = staff.pitchPositionOf(beam.getMedian().getP2());
            if (Math.abs(p2) > constants.maxAbsolutePitch.getValue()) {
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                        + " staff=" + staff.getId() + " REJECT |p2|=" + Math.abs(p2) + " p1=" + p1);
                continue;
            }""")
text = sub(text,
           """            final Map<HorizontalSide, StaffPeak> sidePeaks = getSerifPeaks(beam, staff);
            if (sidePeaks.size() != 2) {
                continue;
            }

            // All tests are OK
            found.put(beam, sidePeaks);""",
           """            final Map<HorizontalSide, StaffPeak> sidePeaks = getSerifPeaks(beam, staff);

            // DIAG27 (§26 grid gap): serif peaks per side, as returned
            for (HorizontalSide side : HorizontalSide.values()) {
                StaffPeak sp = sidePeaks.get(side);
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                        + " staff=" + staff.getId() + " side=" + side
                        + " chosen=" + ((sp == null) ? null
                                : ("start=" + sp.getStart() + " stop=" + sp.getStop()
                                        + " width=" + sp.getWidth() + " top=" + sp.getTop()
                                        + " bottom=" + sp.getBottom())));
            }
            if (sidePeaks.size() != 2) {
                System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                        + " staff=" + staff.getId() + " REJECT serifPeaks=" + sidePeaks.size()
                        + " p1=" + p1 + " p2=" + p2);
                continue;
            }

            // All tests are OK
            found.put(beam, sidePeaks);
            System.out.println("DIAG27 beam bounds=" + beam.getBounds() + " center=" + center
                    + " staff=" + staff.getId() + " grade=" + beam.getGrade() + " FOUND found="
                    + found.size());""")
text = sub(text,
           """            final int x = (side == HorizontalSide.LEFT) ? bounds.x : bounds.x + bounds.width - 1;
            final List<StaffPeak> peaks = projector.processMultiRestSide(x, side, addedChunk);
            logger.debug("{} {} {}", beam, side, peaks);""",
           """            final int x = (side == HorizontalSide.LEFT) ? bounds.x : bounds.x + bounds.width - 1;
            final List<StaffPeak> peaks = projector.processMultiRestSide(x, side, addedChunk);
            logger.debug("{} {} {}", beam, side, peaks);

            // DIAG27 (§26 grid gap): raw projector peaks per side, before choosing
            System.out.println("DIAG27 peaks beam=" + beam.getBounds() + " side=" + side
                    + " x=" + x + " addedChunk=" + addedChunk + " nPeaks=" + peaks.size());
            for (StaffPeak pk : peaks) {
                System.out.println("DIAG27 peak beam=" + beam.getBounds() + " side=" + side
                        + " start=" + pk.getStart() + " stop=" + pk.getStop()
                        + " width=" + pk.getWidth() + " top=" + pk.getTop()
                        + " bottom=" + pk.getBottom());
            }""")
text = sub(text,
           """        final List<Section> allSections = getSectionsByWidth(maxWidth);""",
           """        final List<Section> allSections = getSectionsByWidth(maxWidth);

        // DIAG27 (§26 grid gap): found map + serif-filament inputs
        System.out.println("DIAG27 createInters system#" + system.getId() + " found=" + found.size()
                + " maxWidth=" + maxWidth + " allSections=" + allSections.size());""")
text = sub(text,
           """                final Filament filament = filamentBuilder.buildFilament(peak, 0, allSections);
                final Glyph glyph = glyphIndex.registerOriginal(filament.toGlyph(null));""",
           """                final Filament filament = filamentBuilder.buildFilament(peak, 0, allSections);

                // DIAG27 (§26 grid gap): serif-filament build per side
                System.out.println("DIAG27 serif beam=" + beam.getBounds() + " side=" + side
                        + " peakStart=" + peak.getStart() + " peakWidth=" + peak.getWidth()
                        + " filamentNull=" + (filament == null)
                        + " trueLength=" + ((filament == null) ? null : filament.getTrueLength()));

                final Glyph glyph = glyphIndex.registerOriginal(filament.toGlyph(null));""")
write("org/audiveris/omr/sheet/beam/MultipleRestsBuilder.java", text)
print("  MultipleRestsBuilder DIAG27 (§26 grid gap)")

# ============================================================ ROUND 24 (§26 follow-up: DIAG28 in BeamsBuilder)
# DIAG27 answered "no beam candidate under TeaVM" — sig.inters(BeamInter)
# is 0 in all 3 systems at MultipleRestsBuilder time, and the Wasm .mxl
# has 0 <beam> elements vs desktop's 13, so BeamsBuilder.buildBeams creates
# no BeamInter at all (not just the multi-rest ones). DIAG28 dumps, per
# system, the BEAM_SPOT glyph count entering createBeams, the BeamInter /
# BeamHookInter counts in the SIG after createBeams / extendBeams /
# buildHooks, and the spot-lag section count from the BEAMS prolog — to
# distinguish "0 spots" (SpotsBuilder / spot lag upstream) from "spots
# present but all rejected in checkBeamGlyph" from "beams created then
# deleted". Same file compiled into phase23/classes for the desktop
# harness (§24/§25 pattern). Prints are read-only.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/beam/BeamsBuilder.java")
text = sub(text,
           """        // First, retrieve candidates from spots
        sortedBeamSpots = system.getGroupedGlyphs(GlyphGroup.BEAM_SPOT);
        Collections.sort(sortedBeamSpots, Glyphs.byFullOrdinate);

        // Create initial beams by checking spots individually
        createBeams();""",
           """        // First, retrieve candidates from spots
        sortedBeamSpots = system.getGroupedGlyphs(GlyphGroup.BEAM_SPOT);
        Collections.sort(sortedBeamSpots, Glyphs.byFullOrdinate);

        // DIAG28 (§26 grid gap): beam-spot input per system
        System.out.println("DIAG28 system#" + system.getId() + " beamSpots=" + sortedBeamSpots.size());

        // Create initial beams by checking spots individually
        createBeams();

        // DIAG28 (§26 grid gap): beams in SIG after createBeams
        System.out.println("DIAG28 system#" + system.getId() + " afterCreateBeams beams="
                + system.getSig().inters(BeamInter.class).size() + " hooks="
                + system.getSig().inters(BeamHookInter.class).size());""")
text = sub(text,
           """        // Finally, retrieve beam hooks
        sortedBeamSpots.removeAll(assignedSpots);
        buildHooks();""",
           """        // Finally, retrieve beam hooks
        sortedBeamSpots.removeAll(assignedSpots);
        buildHooks();

        // DIAG28 (§26 grid gap): beams in SIG after the whole buildBeams
        System.out.println("DIAG28 system#" + system.getId() + " afterBuildBeams beams="
                + system.getSig().inters(BeamInter.class).size() + " hooks="
                + system.getSig().inters(BeamHookInter.class).size()
                + " assignedSpots=" + assignedSpots.size());""")
write("org/audiveris/omr/sheet/beam/BeamsBuilder.java", text)
print("  BeamsBuilder DIAG28 (§26 grid gap)")

text = copy_src("org/audiveris/omr/sheet/beam/BeamsStep.java")
text = sub(text,
           """        // Retrieve significant spots for the whole sheet
        new SpotsBuilder(sheet).buildSheetSpots(spotLag);

        return new Context(spotLag);""",
           """        // Retrieve significant spots for the whole sheet
        new SpotsBuilder(sheet).buildSheetSpots(spotLag);

        // DIAG28 (§26 grid gap): spot-lag sections built by the prolog
        System.out.println("DIAG28 prolog spotLagSections=" + spotLag.getEntities().size());

        return new Context(spotLag);""")
write("org/audiveris/omr/sheet/beam/BeamsStep.java", text)
print("  BeamsStep DIAG28 (§26 grid gap)")

# ============================================================ ROUND 25 (§26 follow-up: DIAG29 checkBeamGlyph tally)
# DIAG28: beamSpots are IDENTICAL on both sides (221/200/110) yet Wasm
# creates 0 beams (desktop 5/2/3, assignedSpots 5/2/3) — so every spot
# glyph is rejected inside createBeams -> checkBeamGlyph, or throws
# there. DIAG29 tallies the failure string returned per spot attempt
# (std params, then small params) per system, plus the gate parameters
# (minBeamWidthLow, minHeightLow, maxBeamSlope, maxDistanceToBorder) —
# to name the single gate that rejects everything under TeaVM. Prints
# are read-only (the tally is a local map; no logic change).
# NOTE: read the ROUND 24 output, NOT the repo source — copy_src would
# wipe the DIAG14 + DIAG28 prints already in patched/src.
# ---------------------------------------------------------------------------
text = (OUT / "org/audiveris/omr/sheet/beam/BeamsBuilder.java").read_text()
text = sub(text,
           """    private void createBeams ()
    {
        for (Glyph glyph : sortedBeamSpots) {
            // First attempt with standard height
            String failure = checkBeamGlyph(glyph, false, stdParams, null);

            // Second attempt with second height, if any
            if ((failure != null) && (smallParams != null)) {
                failure = checkBeamGlyph(glyph, false, smallParams, null);
            }

            if ((failure != null) && glyph.isVip()) {
                logger.info("VIP beam#{} {}", glyph.getId(), failure);
            }
        }
    }""",
           """    private void createBeams ()
    {
        // DIAG29 (§26 grid gap): tally checkBeamGlyph failure reasons
        final java.util.Map<String, Integer> diag29 = new java.util.LinkedHashMap<>();
        final java.util.Map<String, Integer> diag29small = new java.util.LinkedHashMap<>();

        for (Glyph glyph : sortedBeamSpots) {
            // First attempt with standard height
            String failure = checkBeamGlyph(glyph, false, stdParams, null);

            if (failure != null) {
                diag29.merge(failure, 1, Integer::sum);
            }

            // Second attempt with second height, if any
            if ((failure != null) && (smallParams != null)) {
                failure = checkBeamGlyph(glyph, false, smallParams, null);

                if (failure != null) {
                    diag29small.merge(failure, 1, Integer::sum);
                }
            }

            if ((failure != null) && glyph.isVip()) {
                logger.info("VIP beam#{} {}", glyph.getId(), failure);
            }
        }

        // DIAG29 (§26 grid gap): per-system failure tally + gate params
        System.out.println("DIAG29 system#" + system.getId() + " spots=" + sortedBeamSpots.size()
                + " stdFailures=" + diag29 + " smallFailures=" + diag29small
                + " minBeamWidthLow=" + stdParams.minBeamWidthLow
                + " minHeightLow=" + stdParams.minHeightLow
                + " maxBeamSlope=" + params.maxBeamSlope
                + " maxDistanceToBorder=" + params.maxDistanceToBorder
                + " smallParams=" + ((smallParams == null) ? null : "present"));
    }""")
write("org/audiveris/omr/sheet/beam/BeamsBuilder.java", text)
print("  BeamsBuilder DIAG29 (§26 grid gap)")

# ============================================================ ROUND 26 (§26 follow-up: DIAG30 computeImpacts)
# DIAG29: every checkBeamGlyph gate agrees (width/slope/thickness/borders/
# structure width tallies identical); the ONLY difference is "no good
# item": desktop 47/32/29 vs Wasm 52/34/32 — exactly the 5+2+3 spots that
# succeed on desktop fail inside createBeamInters under TeaVM, with no
# "Could not compute impacts" exception on either side. DIAG30 prints,
# in computeImpacts' null branch, the rejection inputs (width, height,
# coreCount/coreRatio, beltCount/beltRatio + thresholds) and, in
# createBeamInters' beam path, the impacts grade vs BeamInter min grade
# — to distinguish "impacts null (core/belt ratio off)" from "grade
# below threshold". NOTE: read the ROUND 25 output, NOT the repo source
# (copy_src would wipe DIAG14 + DIAG28 + DIAG29).
# ---------------------------------------------------------------------------
text = (OUT / "org/audiveris/omr/sheet/beam/BeamsBuilder.java").read_text()
text = sub(text,
           """        if ((width < minWidthLow) || (item.height < itemParams.minHeightLow)
                || (item.height > itemParams.maxHeightHigh)
                || (coreRatio < params.minCoreBlackRatio)
                || (beltRatio > params.maxBeltBlackRatio)) {""",
           """        if ((width < minWidthLow) || (item.height < itemParams.minHeightLow)
                || (item.height > itemParams.maxHeightHigh)
                || (coreRatio < params.minCoreBlackRatio)
                || (beltRatio > params.maxBeltBlackRatio)) {
            // DIAG30 (§26 grid gap): computeImpacts rejection inputs
            System.out.println("DIAG30 reject item=" + item + " width=" + width
                    + " height=" + item.height + " coreCount=" + coreCount
                    + " coreRatio=" + coreRatio + " beltCount=" + beltCount
                    + " beltRatio=" + beltRatio + " minWidthLow=" + minWidthLow
                    + " minHeightLow=" + itemParams.minHeightLow + " maxHeightHigh="
                    + itemParams.maxHeightHigh + " minCore=" + params.minCoreBlackRatio
                    + " maxBelt=" + params.maxBeltBlackRatio);""")
text = sub(text,
           """                    if ((impacts != null) && (impacts.getGrade() >= BeamInter.getMinGrade())) {
                        success = true;
                        final AbstractBeamInter beam = itemParams.isSmall ? new SmallBeamInter(""",
           """                    // DIAG30 (§26 grid gap): beam-path grade verdict
                    System.out.println("DIAG30 beamItem item=" + item + " impactsNull="
                            + (impacts == null) + " grade=" + ((impacts == null) ? null : impacts.getGrade())
                            + " minGrade=" + BeamInter.getMinGrade());

                    if ((impacts != null) && (impacts.getGrade() >= BeamInter.getMinGrade())) {
                        success = true;
                        final AbstractBeamInter beam = itemParams.isSmall ? new SmallBeamInter(""")
write("org/audiveris/omr/sheet/beam/BeamsBuilder.java", text)
print("  BeamsBuilder DIAG30 (§26 grid gap)")

# ============================================================ ROUND 27 (§26 GH follow-up: DIAG31 StemScaler stall)
# The GH Area fix is verified on desktop (harness 552/555, beam belts
# exact; BenchTri page.subtract(staff) 1-4 ms) and IS in full-out58/59
# (teadbg has greinerHormann), and the scanline fill is verified
# pixel-identical (filltest: full page 717 ms desktop, 0 diffs) — yet
# full-out58 AND full-out59 both stall at the same 172-line point
# (last print: DIAG14 getSource NO_STAFF, inside StemScaler.getBuffer
# via StemSeedsStep.doProlog) and are killed by the 300 s timeout.
# So the stall is NOT (only) the old per-pixel fill. DIAG31 brackets
# getBuffer() with elapsed-ms timings + segment counts (per-staff core
# path, area after each subtract) to name which phase eats the time:
# eraseShapes vs subtracts vs fill vs computeStem (after getBuffer).
# Prints are read-only (a segment counter + timings; no logic change).
# NOTE: StemScaler is new to the patch script: copy from the repo.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/stem/StemScaler.java")
text = sub(text,
           """    private ByteProcessor getBuffer ()
    {
        // Obtain image without staff lines and barlines
        final ByteProcessor buf = sheet.getPicture().getSource(Picture.SourceKey.NO_STAFF);
        final BufferedImage img = buf.getBufferedImage();
        final Graphics2D g = img.createGraphics();
        new StemsCleaner(buf, g, sheet).eraseShapes(
                Arrays.asList(
                        Shape.THICK_BARLINE,
                        Shape.THICK_CONNECTOR,
                        Shape.THIN_BARLINE,
                        Shape.THIN_CONNECTOR));

        // Paint in white the exterior of staves
        final Area area = new Area(new Rectangle(0, 0, buf.getWidth(), buf.getHeight()));
        final StaffManager mgr = sheet.getStaffManager();

        for (Staff staff : mgr.getStaves()) {
            area.subtract(new Area(mgr.getCoreStaffPath(staff)));
        }

        g.setColor(Color.WHITE);
        g.fill(area);
""",
           """    // DIAG31 (§26 GH follow-up): segment count via next() only (no
    // currentSegment call, so no O(n^2) base computation).
    private static int diag31Segs (java.awt.Shape s)
    {
        java.awt.geom.PathIterator it = s.getPathIterator(null);
        int n = 0;

        while (!it.isDone()) {
            n++;
            it.next();
        }

        return n;
    }

    private ByteProcessor getBuffer ()
    {
        // DIAG31 (§26 GH follow-up): bracket the StemScaler stall
        final long diag31t0 = System.currentTimeMillis();
        System.out.println("DIAG31 getBuffer start");
        // Obtain image without staff lines and barlines
        final ByteProcessor buf = sheet.getPicture().getSource(Picture.SourceKey.NO_STAFF);
        System.out.println("DIAG31 after getSource ms=" + (System.currentTimeMillis() - diag31t0));
        final BufferedImage img = buf.getBufferedImage();
        final Graphics2D g = img.createGraphics();
        new StemsCleaner(buf, g, sheet).eraseShapes(
                Arrays.asList(
                        Shape.THICK_BARLINE,
                        Shape.THICK_CONNECTOR,
                        Shape.THIN_BARLINE,
                        Shape.THIN_CONNECTOR));
        System.out.println("DIAG31 after eraseShapes ms=" + (System.currentTimeMillis() - diag31t0));

        // Paint in white the exterior of staves
        final Area area = new Area(new Rectangle(0, 0, buf.getWidth(), buf.getHeight()));
        final StaffManager mgr = sheet.getStaffManager();

        for (Staff staff : mgr.getStaves()) {
            java.awt.geom.Path2D corePath = mgr.getCoreStaffPath(staff);
            System.out.println("DIAG31 staff#" + staff.getId() + " coreSegs=" + diag31Segs(corePath)
                    + " coreBounds=" + corePath.getBounds2D()
                    + " ms=" + (System.currentTimeMillis() - diag31t0));
            area.subtract(new Area(corePath));
            System.out.println("DIAG31 staff#" + staff.getId() + " subtracted areaSegs="
                    + diag31Segs(area) + " ms=" + (System.currentTimeMillis() - diag31t0));
        }
        System.out.println("DIAG31 after subtracts areaSegs=" + diag31Segs(area)
                + " ms=" + (System.currentTimeMillis() - diag31t0));

        g.setColor(Color.WHITE);
        System.out.println("DIAG31 before fill ms=" + (System.currentTimeMillis() - diag31t0));
        g.fill(area);
        System.out.println("DIAG31 after fill ms=" + (System.currentTimeMillis() - diag31t0));
""")
write("org/audiveris/omr/sheet/stem/StemScaler.java", text)
print("  StemScaler DIAG31 (§26 GH follow-up)")

# ============================================================ ROUND 28 (§27: CURVES slur trap — DIAG32)
# full-out61 crashes in CURVES: SlurInfo.getCurve line 200 (right.getCtrlX2())
# — rightModel.getCurve() returned null, i.e. the right-side Circle's
# computeCurve() returned early because firstAngle or lastAngle is null/NaN
# (Circle.java:271-274). The crash is general (hymn crashes with the identical
# stack), and a Wasm trap bypasses weed()'s catch (Exception). DIAG32 prints,
# in computeSideModel, every slur side model as it is built (the 3 defining
# points p0/p1/p2 + the fitted Circle's center/radius/first/last angles), and
# in getCurve(), when the right curve is null, the crashing slur's id, point
# list, both side models' Circle parameters and the global model — to
# distinguish "the slur's glyph points differ under Wasm" (curve/skeleton
# divergence upstream) from "the points agree but the Circle fit arithmetic
# diverges" (floating-point / Math difference in the bisector-intersection
# fit: defineCircle uses LineUtil.intersection of the two bisectors, so a
# near-collinear triple has den ~ 0 and a 1px point difference can tip the
# centre from huge-but-finite to NaN; CircleModel.createValid only rejects
# infinite radius, not a NaN centre/radius). Prints are read-only.
# Same file compiled into phase23/classes for the desktop harness (§24/§25/§26 pattern).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/curve/SlurInfo.java")
text = sub(text,
           """        // Choose a circle-model, otherwise a line-model
        CircleModel rough = CircleModel.createValid(p0, p1, p2);

        if (rough != null) {""",
           """        // Choose a circle-model, otherwise a line-model
        CircleModel rough = CircleModel.createValid(p0, p1, p2);

        // DIAG32 (§27 slur trap): every side model as built — defining points + fit
        System.out.println("DIAG32 SIDEMODEL id=" + getId() + " reverse=" + reverse
                + " p0=" + p0 + " p1=" + p1 + " p2=" + p2 + " roughNull=" + (rough == null)
                + " center=" + ((rough == null) ? null : rough.getCircle().getCenter())
                + " radius=" + ((rough == null) ? null : rough.getCircle().getRadius())
                + " firstAngle=" + ((rough == null) ? null : rough.getCircle().getFirstAngle())
                + " lastAngle=" + ((rough == null) ? null : rough.getCircle().getLastAngle())
                + " ccw=" + ((rough == null) ? null : rough.getCircle().ccw()));

        if (rough != null) {""")
text = sub(text,
           """            CubicCurve2D left = (CubicCurve2D) leftModel.getCurve();
            CubicCurve2D right = (CubicCurve2D) rightModel.getCurve();
""",
           """            CubicCurve2D left = (CubicCurve2D) leftModel.getCurve();
            CubicCurve2D right = (CubicCurve2D) rightModel.getCurve();

            // DIAG32 (§27 slur trap): the crashing slur, right curve null
            if (right == null) {
                System.out.println("DIAG32 NULLRIGHT id=" + getId() + " npts=" + points.size()
                        + " firstPt=" + points.get(0) + " lastPt=" + points.get(points.size() - 1)
                        + " bounds=" + getBounds() + " sideLength=" + sideLength
                        + " leftClass=" + leftModel.getClass().getSimpleName()
                        + " rightClass=" + rightModel.getClass().getSimpleName()
                        + " leftCurveNull=" + (left == null)
                        + " leftSidePts=" + getSidePoints(true)
                        + " rightSidePts=" + getSidePoints(false)
                        + " globalModel=" + ((model == null) ? null : model.getClass().getSimpleName()));
                if (leftModel instanceof CircleModel) {
                    CircleModel lm = (CircleModel) leftModel;
                    System.out.println("DIAG32 NULLRIGHT leftCircle center=" + lm.getCircle().getCenter()
                            + " radius=" + lm.getCircle().getRadius()
                            + " firstAngle=" + lm.getCircle().getFirstAngle()
                            + " lastAngle=" + lm.getCircle().getLastAngle()
                            + " ccw=" + lm.getCircle().ccw());
                }
                if (rightModel instanceof CircleModel) {
                    CircleModel rm = (CircleModel) rightModel;
                    System.out.println("DIAG32 NULLRIGHT rightCircle center=" + rm.getCircle().getCenter()
                            + " radius=" + rm.getCircle().getRadius()
                            + " firstAngle=" + rm.getCircle().getFirstAngle()
                            + " lastAngle=" + rm.getCircle().getLastAngle()
                            + " ccw=" + rm.getCircle().ccw());
                }
            }
""")
write("org/audiveris/omr/sheet/curve/SlurInfo.java", text)
print("  SlurInfo DIAG32 (§27 slur trap)")

# ============================================================ ROUND 30 (§28: DIAG33 bisect — guard getBounds in WEED prints, step prints before each purge stage)
# Out64 crashed in EnumMap.put right after a WEED-IN n=1 print; the id print never appeared.
# Guard the getBounds() call (curve may be null) and bracket purgeIdenticalEndings /
# purgeStaffLines / purgeShortests / grade filter so the crash localises to a stage.
# ============================================================ ROUND 29 (§28: hymn slur residual — DIAG33)
# full-out63 hymn: Slurs 5 vs desktop 0 (8 extra <slur> notations, P1 m6-8).
# Appeared between out51 (Slurs 0) and out63, i.e. after the §26 Area fix.
# The 5 candidates' start points (x=362/460/875/996, y~=805/806) occur 0 times
# in the desktop log — desktop never builds those candidates at all (not merely
# weeds them). DIAG33 prints, in SlursBuilder only (same patched file both
# sides; desktop + Wasm .mxl byte-identical to the §27 controls with prints
# on — to be verified this round):
#  (a) buildSlurs: every seed arc (first/last point, length, shape) + count.
#  (b) computeModel: per call p0/p1/p2, rough radius, fitted radius, chosen
#      circle, dist, verdict (accept / radius-too-small / angle-too-large /
#      bad-fit / exception).
#  (c) weed: per-clump WEED-IN (id/grade/box), counts after each purge step,
#      WEED-OUT kept ids; purgeStaffLines/purgeShortests drop reasons.
#  (d) createInter: accepted vs rejected (impacts null / grade low / curve
#      null / glyph null) — the final SIG decision.
# Together these distinguish "candidate never built on desktop" (seed arcs /
# skeleton upstream, plausibly the §26 Area/fill change feeding CurvesBuilder
# different arcs) from "candidate built but fit/weeding diverges" (computeModel
# dist / Jama fit / weed purge). Prints are read-only. Note: Wasm DEBUG logging
# is neutered, so desktop's 1,088 "Bad circle fit" lines have no Wasm
# counterpart — System.out prints are the comparison, as DIAG32 did.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/curve/SlursBuilder.java")

# (a) seed arcs in buildSlurs
text = sub(text,
           """            final List<Arc> relevants = getSeedArcs();
            maxLength = null;
""",
           """            final List<Arc> relevants = getSeedArcs();
            System.out.println("DIAG33 SEEDS n=" + relevants.size());
            for (Arc a : relevants) {
                List<Point> ap = a.getPoints();
                System.out.println("DIAG33 SEED first=" + ap.get(0) + " last=" + ap.get(ap.size() - 1)
                        + " len=" + a.getLength() + " shape=" + a.getShape());
            }
            maxLength = null;
""")

# (b) computeModel — entry values (after rough + minRadius are known)
text = sub(text,
           """        // Compute rough circle values for quick tests
        Circle rough = new Circle(p0, p1, p2);

        // Minimum circle radius
        double radius = rough.getRadius();
        double minRadius = isSeed ? params.minSeedCircleRadius : params.minCircleRadius;

        if (radius < minRadius) {
            logger.debug("Arc radius too small {} at {}", radius, p0);

            return null;
        }
""",
           """        // Compute rough circle values for quick tests
        Circle rough = new Circle(p0, p1, p2);

        // Minimum circle radius
        double radius = rough.getRadius();
        double minRadius = isSeed ? params.minSeedCircleRadius : params.minCircleRadius;

        // DIAG33 (§28 slur residual): per-candidate model inputs
        System.out.println("DIAG33 MODEL isSeed=" + isSeed + " npts=" + points.size()
                + " p0=" + p0 + " p1=" + p1 + " p2=" + p2 + " roughRadius=" + radius
                + " minRadius=" + minRadius);

        if (radius < minRadius) {
            logger.debug("Arc radius too small {} at {}", radius, p0);

            System.out.println("DIAG33 VERDICT p0=" + p0 + " verdict=radius-too-small radius=" + radius
                    + " minRadius=" + minRadius);
            return null;
        }
""")

# (b) angle-too-large verdict
text = sub(text,
           """            if (arcAngle > params.maxArcAngleHigh) {
                logger.debug("Arc angle too large {} at {}", arcAngle, p0);

                return null;
            }
""",
           """            if (arcAngle > params.maxArcAngleHigh) {
                logger.debug("Arc angle too large {} at {}", arcAngle, p0);

                System.out.println("DIAG33 VERDICT p0=" + p0 + " verdict=angle-too-large arcAngle=" + arcAngle
                        + " max=" + params.maxArcAngleHigh);
                return null;
            }
""")

# (b) fitted circle + dist + verdicts
text = sub(text,
           """            if (dist > params.maxArcsDistance) {
                logger.debug("Bad circle fit {} at {}", dist, p0);

                return null;
            } else {
                logger.debug("{} to {} Circle {}", p0, p2, circle);

                return new CircleModel(circle);
            }
        } catch (Exception ex) {
            logger.debug("Could not compute circle at {}", p0);

            return null;
        }
""",
           """            System.out.println("DIAG33 FIT p0=" + p0 + " fittedRadius=" + r2 + " roughRadius=" + r1
                    + " chosen=" + ((circle == fitted) ? "fitted" : "rough") + " dist=" + dist
                    + " maxArcsDistance=" + params.maxArcsDistance);

            if (dist > params.maxArcsDistance) {
                logger.debug("Bad circle fit {} at {}", dist, p0);

                System.out.println("DIAG33 VERDICT p0=" + p0 + " verdict=bad-fit dist=" + dist);
                return null;
            } else {
                logger.debug("{} to {} Circle {}", p0, p2, circle);

                System.out.println("DIAG33 VERDICT p0=" + p0 + " verdict=accept dist=" + dist
                        + " circle=" + circle);
                return new CircleModel(circle);
            }
        } catch (Exception ex) {
            logger.debug("Could not compute circle at {}", p0);

            System.out.println("DIAG33 VERDICT p0=" + p0 + " verdict=exception ex=" + ex);
            return null;
        }
""")

# (d) createInter — final SIG decision
text = sub(text,
           """        SlurInfo slur = (SlurInfo) seq;
        GradeImpacts impacts = computeImpacts(slur, true);

        if ((impacts != null) && (impacts.getGrade() >= SlurInter.getMinGrade()) && (slur
                .getCurve() != null)) {
            slur.retrieveGlyph(sheet, params.maxRunDistance, params.minRunRatio);

            if (slur.getGlyph() != null) {
                inters.add(new SlurInter(slur, impacts));
            }
        }
    }
""",
           """        SlurInfo slur = (SlurInfo) seq;
        GradeImpacts impacts = computeImpacts(slur, true);

        if ((impacts != null) && (impacts.getGrade() >= SlurInter.getMinGrade()) && (slur
                .getCurve() != null)) {
            slur.retrieveGlyph(sheet, params.maxRunDistance, params.minRunRatio);

            if (slur.getGlyph() != null) {
                inters.add(new SlurInter(slur, impacts));
                System.out.println("DIAG33 CREATE-INTER id=" + slur.getId() + " grade=" + impacts.getGrade()
                        + " box=" + slur.getBounds() + " ACCEPT");
            } else {
                System.out.println("DIAG33 CREATE-INTER id=" + slur.getId() + " grade=" + impacts.getGrade()
                        + " box=" + slur.getBounds() + " REJECT glyph-null");
            }
        } else {
            System.out.println("DIAG33 CREATE-INTER id=" + slur.getId()
                    + " impactsNull=" + (impacts == null)
                    + " grade=" + ((impacts == null) ? null : impacts.getGrade())
                    + " minGrade=" + SlurInter.getMinGrade()
                    + " curveNull=" + (slur.getCurve() == null)
                    + " box=" + slur.getBounds() + " REJECT");
        }
    }
""")

# (c) weed — entry list + counts after each purge step + kept ids
text = sub(text,
           """        clump.clear();

        // In the provided clump, all candidates start from the same point.
        // If several candidates stop at the same point, keep the one with best grade.
        purgeIdenticalEndings(inters);

        // Discard candidates that end as a portion of staff line
        purgeStaffLines(inters);

        // Discard the ones with too short distance from one end to the other
        SlurInter longest = purgeShortests(inters);

        if (longest == null) {
            return;
        }

        // Discard those with grade lower than grade of longest candidate
        double longestGrade = longest.getGrade();

        for (Iterator<SlurInter> it = inters.iterator(); it.hasNext();) {
            if (it.next().getGrade() < longestGrade) {
                it.remove();
            }
        }

        for (SlurInter slur : inters) {
            clump.add(slur.getInfo());
        }
""",
           """        System.out.println("DIAG33 WEED-IN n=" + inters.size());
        for (SlurInter si : inters) {
            System.out.println("DIAG33 WEED-IN id=" + si.getInfo().getId() + " grade=" + si.getGrade()
                    + " curveNull=" + (si.getCurve() == null)
                    + " box=" + ((si.getCurve() == null) ? "null" : si.getBounds()));
        }

        clump.clear();

        // In the provided clump, all candidates start from the same point.
        // If several candidates stop at the same point, keep the one with best grade.
        System.out.println("DIAG33 WEED-STEP sort n=" + inters.size());
        purgeIdenticalEndings(inters);
        System.out.println("DIAG33 WEED-AFTER-IDENTICAL n=" + inters.size());

        // Discard candidates that end as a portion of staff line
        System.out.println("DIAG33 WEED-STEP stafflines n=" + inters.size());
        purgeStaffLines(inters);
        System.out.println("DIAG33 WEED-AFTER-STAFFLINES n=" + inters.size());

        // Discard the ones with too short distance from one end to the other
        System.out.println("DIAG33 WEED-STEP shortest n=" + inters.size());
        SlurInter longest = purgeShortests(inters);
        System.out.println("DIAG33 WEED-AFTER-SHORTEST n=" + inters.size()
                + " longestId=" + ((longest == null) ? null : longest.getInfo().getId())
                + " longestGrade=" + ((longest == null) ? null : longest.getGrade()));

        if (longest == null) {
            return;
        }

        // Discard those with grade lower than grade of longest candidate
        System.out.println("DIAG33 WEED-STEP filter n=" + inters.size());
        double longestGrade = longest.getGrade();

        for (Iterator<SlurInter> it = inters.iterator(); it.hasNext();) {
            if (it.next().getGrade() < longestGrade) {
                it.remove();
            }
        }

        System.out.println("DIAG33 WEED-OUT n=" + inters.size());
        for (SlurInter si : inters) {
            System.out.println("DIAG33 WEED-OUT id=" + si.getInfo().getId() + " grade=" + si.getGrade()
                    + " curveNull=" + (si.getCurve() == null)
                    + " box=" + ((si.getCurve() == null) ? "null" : si.getBounds()));
        }

        for (SlurInter slur : inters) {
            clump.add(slur.getInfo());
        }
""")

# (c) purgeStaffLines — drop reasons at both toDelete.add sites
text = sub(text,
           """            // Delete slur ending as a STAFF_ARC
            Arc endPart = slur.getPartAt(end);

            if ((endPart != null) && (endPart.getShape() == STAFF_ARC)) {
                if (debugArc) {
                    logger.info("{} ending as STAFF_ARC", slur);
                }

                toDelete.add(inter);

                continue;
            }
""",
           """            // Delete slur ending as a STAFF_ARC
            Arc endPart = slur.getPartAt(end);

            if ((endPart != null) && (endPart.getShape() == STAFF_ARC)) {
                if (debugArc) {
                    logger.info("{} ending as STAFF_ARC", slur);
                }

                System.out.println("DIAG33 PURGE-STAFFLINE id=" + inter.getInfo().getId()
                        + " reason=STAFF_ARC end=" + end);
                toDelete.add(inter);

                continue;
            }
""")
text = sub(text,
           """            if (debugArc) {
                logger.info("{} ending as staff line", slur);
            }

            toDelete.add(inter);
""",
           """            if (debugArc) {
                logger.info("{} ending as staff line", slur);
            }

            System.out.println("DIAG33 PURGE-STAFFLINE id=" + inter.getInfo().getId()
                    + " reason=staff-line-incidence end=" + end);
            toDelete.add(inter);
""")

# (c) purgeShortests — longest/quorum + each drop
text = sub(text,
           """        int quorum = (int) Math.ceil(params.quorumRatio * params.quorumRatio * maxExt2);

        for (Iterator<SlurInter> it = inters.iterator(); it.hasNext();) {
            SlurInfo slur = it.next().getInfo();

            if (slur.getSegmentSq() < quorum) {
                it.remove();
            }
        }
""",
           """        int quorum = (int) Math.ceil(params.quorumRatio * params.quorumRatio * maxExt2);

        System.out.println("DIAG33 PURGE-SHORTEST longestId=" + longest.getInfo().getId()
                + " maxExt2=" + maxExt2 + " quorum=" + quorum + " n=" + inters.size());

        for (Iterator<SlurInter> it = inters.iterator(); it.hasNext();) {
            SlurInfo slur = it.next().getInfo();

            if (slur.getSegmentSq() < quorum) {
                System.out.println("DIAG33 PURGE-SHORTEST drop id=" + slur.getId()
                        + " ext2=" + slur.getSegmentSq() + " quorum=" + quorum);
                it.remove();
            }
        }
""")

write("org/audiveris/omr/sheet/curve/SlursBuilder.java", text)
print("  SlursBuilder DIAG33 (§28 slur residual)")

# ============================================================ ROUND 31 (\u00a729: DIAG34 skeleton-buffer comparison)
# \u00a728: hymn slurs 5 vs desktop 0 is upstream of SlursBuilder, in skeleton /
# arc extraction (extra diagonal SHORT spurs, 1-4 px longer staff-line arcs),
# but the split "thinning diverges" vs "arc retrieval diverges on an
# identical skeleton" is not established. DIAG34 dumps the skeleton buffer
# at three points, same patched files both sides, print-only:
#   DIAG34A: right after buffer.skeletonize() (raw skeleton, before erasing)
#   DIAG34B: final buf after buildSkeleton (what ArcRetriever walks)
#   DIAG34C: junction-valued pixels after JunctionRetriever.scanImage()
#   DIAG34D: arc counts after ArcRetriever.scanImage()
# If A differs -> ij skeletonize() diverges under TeaVM. If A matches but B
# differs -> CurvesCleaner.eraseShapes / eraseDistantRegions (Area subtract,
# \u00a726 GH fix) / the BufferedImage round-trip diverges. If A+B match but C
# differs -> JunctionRetriever diverges. If A+B+C match but D differs ->
# ArcRetriever diverges. Secondary hypothesis checked by code reading in
# \u00a729: Skeleton does NOT prune spurs (no prune step exists; SHORT is
# just ArcRetriever's label for too-short arcs), so any spur difference
# comes straight from skeletonize() output or from the erasing path.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/curve/Skeleton.java")
text = sub(text,
           """        buffer.skeletonize();
""",
           """        buffer.skeletonize();

        // DIAG34 (\u00a729): raw skeleton, before any erasing
        diag34Dump("DIAG34A", buffer);
""")
text = sub(text,
           """        buf = buffer;

        return img;
""",
           """        buf = buffer;

        // DIAG34 (\u00a729): final skeleton buffer ArcRetriever walks
        diag34Dump("DIAG34B", buf);

        return img;
""")
text = sub(text,
           """    //-----------------//
    // getErasedInters //
""",
           """    // DIAG34 (\u00a729): per-row FNV + sum + zeros dump of a skeleton
    // buffer, DIAG22 style. Print-only; same code runs on desktop and
    // under TeaVM.
    private static void diag34Dump (String tag,
                                    ByteProcessor bp)
    {
        byte[] px = (byte[]) bp.getPixels();
        int w = bp.getWidth();
        int h = bp.getHeight();
        int totalZeros = 0;

        for (int y = 0; y < h; y++) {
            long fnv = 0xcbf29ce484222325L;
            long sum = 0;
            int zeros = 0;

            for (int x = 0; x < w; x++) {
                int v = px[y * w + x] & 0xff;
                fnv = (fnv ^ v) * 0x100000001b3L;
                sum += v;

                if (v == 0) {
                    zeros++;
                }
            }

            totalZeros += zeros;
            System.out.println(tag + " row=" + y + " fnv=" + Long.toHexString(fnv)
                    + " sum=" + sum + " zeros=" + zeros);
        }

        System.out.println(tag + " TOTAL w=" + w + " h=" + h + " zeros=" + totalZeros);
    }

    //-----------------//
    // getErasedInters //
""")
write("org/audiveris/omr/sheet/curve/Skeleton.java", text)
print("  Skeleton DIAG34A/B (\u00a729)")

text = read_out("org/audiveris/omr/sheet/curve/Curves.java")
text = sub(text,
           """        new JunctionRetriever(skeleton).scanImage();
""",
           """        new JunctionRetriever(skeleton).scanImage();

        // DIAG34 (\u00a729): junction-valued pixels after JunctionRetriever
        {
            int junctionCount = 0;
            StringBuilder junctionList = new StringBuilder();

            for (int y = 0; y < skeleton.buf.getHeight(); y++) {
                for (int x = 0; x < skeleton.buf.getWidth(); x++) {
                    if (Skeleton.isJunction(skeleton.buf.get(x, y))) {
                        junctionCount++;

                        if (junctionList.length() > 0) {
                            junctionList.append(' ');
                        }

                        junctionList.append(x).append(',').append(y);
                    }
                }
            }

            System.out.println("DIAG34C junctions=" + junctionCount + " pts=" + junctionList);
        }
""")
text = sub(text,
           """        new ArcRetriever(this).scanImage();
""",
           """        new ArcRetriever(this).scanImage();

        // DIAG34 (\u00a729): arc counts after ArcRetriever
        {
            java.util.Map<String, Integer> shapeCounts = new java.util.TreeMap<>();
            int totalPoints = 0;

            for (Arc arc : skeleton.arcsMap.values()) {
                String shape = (arc.getShape() == null) ? "null" : arc.getShape().toString();
                shapeCounts.merge(shape, 1, Integer::sum);
                totalPoints += arc.getPoints().size();
            }

            System.out.println("DIAG34D arcs=" + skeleton.arcsMap.size()
                    + " arcsEnds=" + skeleton.arcsEnds.size()
                    + " voidArcs=" + skeleton.voidArcsMap.size()
                    + " totalPoints=" + totalPoints
                    + " shapes=" + shapeCounts);
        }
""")
write("org/audiveris/omr/sheet/curve/Curves.java", text)
print("  Curves DIAG34C/D (\u00a729)")

# ============================================================ ROUND 32 (§30: DIAG35 per-stage buffer dumps)
# §29: thinning is bit-identical; the divergence is in the erasing path
# inside Skeleton.buildSkeleton() (final buf desktop 41,558 vs Wasm 45,681
# fore px, +4,123, all Wasm-extra, system 1 only, rows 122-1126).
# DIAG35 dumps the image buffer after each stage of buildSkeleton, same
# patched file both sides, print-only. Note the erasing draws on `img`
# (the BufferedImage view of the skeletonized buffer) via Graphics2D, so
# stage dumps read `img` through a fresh ByteProcessor copy; the final
# stage is the existing DIAG34B dump of `buf` after the round-trip.
#   DIAG35A: after non-crossable eraseShapes (+ erased counts by shape)
#   DIAG35B: after crossable eraseShapes (+ erased counts by shape)
#   DIAG35C: after eraseDistantRegions (+ band x-runs, rows 179-257)
#   DIAG35D-BAND: final buf band x-runs, rows 179-257
#   DIAG35-REGION: per-staff rects + sheetArea segment count before fill
# If A diverges -> non-crossable eraseShapes (which shape type survives
# is in the erased counts). If B diverges -> crossable eraseShapes. If C
# diverges -> eraseDistantRegions; the segCount then splits GH-subtract
# (count differs) from scanline fill (same area, different fill).
# If only D diverges -> the BufferedImage round-trip / threshold(127).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/curve/Skeleton.java")
text = sub(text,
           """        nonCrossables = cleaner.eraseShapes(nonCrossableShapes);
""",
           """        nonCrossables = cleaner.eraseShapes(nonCrossableShapes);
        diag35Erased("DIAG35-NONCROSS", nonCrossables);
        diag35DumpImg("DIAG35A", img);
""")
text = sub(text,
           """                        Shape.STEM));
""",
           """                        Shape.STEM));
        diag35Erased("DIAG35-CROSS", crossables);
        diag35DumpImg("DIAG35B", img);
""")
text = sub(text,
           """        cleaner.eraseDistantRegions();
""",
           """        cleaner.eraseDistantRegions();
        diag35DumpImg("DIAG35C", img);
        diag35Band("DIAG35C-BAND", new ByteProcessor(img), 179, 257);
""")
text = sub(text,
           """        // DIAG34 (§29): final skeleton buffer ArcRetriever walks
        diag34Dump("DIAG34B", buf);
""",
           """        // DIAG34 (§29): final skeleton buffer ArcRetriever walks
        diag34Dump("DIAG34B", buf);
        diag35Band("DIAG35D-BAND", buf, 179, 257);
""")
text = sub(text,
           """                staffRect.grow(maxDx, maxDy);

                Area staffArea = new Area(staffRect);
""",
           """                staffRect.grow(maxDx, maxDy);
                System.out.println("DIAG35-REGION staff rect=" + staffRect);

                Area staffArea = new Area(staffRect);
""")
text = sub(text,
           """            g.fill(sheetArea);
""",
           """            // DIAG35 (§30): segment count of the distant-region area before fill —
            // distinguishes a GH-subtract divergence (segment count differs) from a
            // scanline-fill divergence (same area, different fill result).
            try {
                java.awt.geom.PathIterator pi = sheetArea.getPathIterator(null);
                double[] coords = new double[6];
                int segCount = 0;

                while (!pi.isDone()) {
                    pi.currentSegment(coords);
                    segCount++;
                    pi.next();
                }

                System.out.println("DIAG35-REGION maxDx=" + maxDx + " maxDy=" + maxDy
                        + " segCount=" + segCount);
            } catch (Exception ex) {
                System.out.println("DIAG35-REGION segCount=ERR " + ex);
            }

            g.fill(sheetArea);
""")
text = sub(text,
           """    //-----------------//
    // getErasedInters //
""",
           """    // DIAG35 (§30): dump an image buffer (fresh ByteProcessor copy of
    // the BufferedImage the erasing draws on) with the DIAG34 row format.
    // Print-only; same code runs on desktop and under TeaVM.
    private static void diag35DumpImg (String tag,
                                       BufferedImage img)
    {
        diag34Dump(tag, new ByteProcessor(img));
    }

    // DIAG35 (§30): fore-pixel x-runs (value 0) for rows y0..y1 of a
    // skeleton buffer, to identify which shape type survives in a band.
    private static void diag35Band (String tag,
                                    ByteProcessor bp,
                                    int y0,
                                    int y1)
    {
        byte[] px = (byte[]) bp.getPixels();
        int w = bp.getWidth();

        for (int y = y0; y <= y1; y++) {
            StringBuilder runs = new StringBuilder();
            int runStart = -1;
            int fore = 0;

            for (int x = 0; x < w; x++) {
                boolean isFore = (px[y * w + x] & 0xff) == 0;

                if (isFore) {
                    fore++;

                    if (runStart < 0) {
                        runStart = x;
                    }
                } else if (runStart >= 0) {
                    if (runs.length() > 0) {
                        runs.append(' ');
                    }

                    runs.append(runStart).append('-').append(x - 1);
                    runStart = -1;
                }
            }

            if (runStart >= 0) {
                if (runs.length() > 0) {
                    runs.append(' ');
                }

                runs.append(runStart).append('-').append(w - 1);
            }

            System.out.println(tag + " row=" + y + " fore=" + fore + " runs=" + runs);
        }
    }

    // DIAG35 (§30): erased-inter counts by shape for one eraseShapes call.
    private static void diag35Erased (String tag,
                                      java.util.Map<SystemInfo, java.util.List<Inter>> erasedMap)
    {
        for (java.util.Map.Entry<SystemInfo, java.util.List<Inter>> entry : erasedMap.entrySet()) {
            java.util.Map<String, Integer> counts = new java.util.TreeMap<>();

            for (Inter inter : entry.getValue()) {
                String shape = (inter.getShape() == null) ? "null" : inter.getShape().toString();
                counts.merge(shape, 1, Integer::sum);
            }

            System.out.println(tag + " sys=" + entry.getKey()
                    + " total=" + entry.getValue().size() + " shapes=" + counts);
        }
    }

    //-----------------//
    // getErasedInters //
""")
write("org/audiveris/omr/sheet/curve/Skeleton.java", text)
print("  Skeleton DIAG35A/B/C/D (§30)")

# ============================================================ ROUND 33 (§30: head-erasure fix)
# DIAG35 proved the divergence lands in the NON-CROSSABLE eraseShapes
# stage: erased counts identical (80 NOTEHEAD_BLACK sys1, 48 sys2), but
# the stage removes 5,166 px under Wasm vs 10,167 on desktop, and the
# surviving ink in band 179-257 is notehead skeletons (rows 179-185 have
# 0 fore px on desktop, small oval clusters on Wasm). Mechanism, by code
# reading: PageCleaner.visit(HeadInter) erases a head by painting its
# Bravura glyph white via paintSymbol -> OmrFont.paint -> TextLayout.draw,
# and the TeaVM font shim's TextLayout.draw is a no-op (no real glyph
# rendering), so under Wasm the head is never erased. Fix (patched
# PageCleaner only): keep paintSymbol, and also erase the head
# geometrically — its glyph runs (exact head ink, including the slanted
# tips) plus an ellipse inscribed in the glyph bounds enlarged 1.1x (the
# desktop paint's enlargement ratio), which also breaks the staff-line
# segment through the head the way the desktop oval paint does. On
# desktop both additions are no-ops in effect (paintSymbol already
# whitened those pixels); desktop-neutrality is verified in §30 by
# re-running the desktop harness (harness .mxl and DIAG34B unchanged).
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
        // in the TeaVM font shim, so under Wasm the head is never erased
        // from the skeleton (DIAG35). Erase it geometrically as well: the
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

# ============================================================ ROUND 34 (§31: DIAG36 per-head erasure accounting)
# §30 residual: Wasm erases ~800 px too much in the final skeleton
# (stage totals A -931, B -762, C -762, final -807), ~7 px/head, no
# downstream effect on either verified page. Prime suspects:
# (a) shim Ellipse2D.contains edge rule — the shim Ellipse2D has NO
# contains override, so it inherits RectangularShape.contains, i.e.
# the bounding-rectangle test; fill(Shape) falls back to the
# per-pixel loop for Ellipse2D (getPathIterator returns null), so
# under TeaVM the "ellipse" fill fills the whole rectangle. JDK
# ground truth measured 2026-11-10 (JDK 25, typical head ellipse
# 31.9x25.3): rectangle 832 pixel centres vs true ellipse 640 —
# 192 corner pixels a rectangle fill erases that a true ellipse
# fill would not. The skeleton only carries ~7 fore px/head in
# those corners, which matches the observed overshoot.
# (b) glyph bounds differing ~1 px under Wasm for some heads.
# (c) processGlyph ink differing.
# DIAG36 instruments visit(HeadInter) (same patched file both
# sides, print-only): per head, fore pixels in the ellipse bounding
# rect before paintSymbol, after paintSymbol, after processGlyph,
# and after the ellipse fill, plus cornerFore — fore pixels in the
# rect lying OUTSIDE the true ellipse (JDK equation, strict < 1.0
# inside), measured after processGlyph / before the fill. If
# glyph bounds are identical and the Wasm ellipse step erases
# cornerFore more than desktop, (a) is proven; if bounds differ,
# (b); if processGlyph counts differ, (c).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """    @Override
    public void visit (HeadInter head)
""",
           """    // DIAG36 (§31): per-head erasure accounting helpers, print-only.
    private int diag36Index = 0;

    // Fore (value 0) pixels in the int rect, read from the skeleton buffer.
    private int diag36Count (int x0, int y0, int x1, int y1)
    {
        final byte[] px = (byte[]) buffer.getPixels();
        final int w = buffer.getWidth();
        final int h = buffer.getHeight();
        int n = 0;

        for (int y = Math.max(0, y0); y <= Math.min(h - 1, y1); y++) {
            for (int x = Math.max(0, x0); x <= Math.min(w - 1, x1); x++) {
                if ((px[y * w + x] & 0xff) == 0) {
                    n++;
                }
            }
        }

        return n;
    }

    // Fore pixels in the int rect lying OUTSIDE the true ellipse
    // (JDK ellipse equation on pixel centres, strict < 1.0 inside).
    private int diag36Corner (int x0, int y0, int x1, int y1,
                              double cx, double cy, double ew, double eh)
    {
        final byte[] px = (byte[]) buffer.getPixels();
        final int w = buffer.getWidth();
        final int h = buffer.getHeight();
        final double rx = ew / 2.0;
        final double ry = eh / 2.0;
        int n = 0;

        for (int y = Math.max(0, y0); y <= Math.min(h - 1, y1); y++) {
            for (int x = Math.max(0, x0); x <= Math.min(w - 1, x1); x++) {
                if ((px[y * w + x] & 0xff) != 0) {
                    continue;
                }

                final double nx = ((x + 0.5) - cx) / rx;
                final double ny = ((y + 0.5) - cy) / ry;

                if ((nx * nx + ny * ny) >= 1.0) {
                    n++;
                }
            }
        }

        return n;
    }

    @Override
    public void visit (HeadInter head)
""")
text = sub(text,
           """        final Glyph glyph = head.getGlyph();
        final Point2D center = (glyph != null) ? glyph.getCenter2D() : head.getCenter2D();
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);

        // §30 (TeaVM): paintSymbol draws through TextLayout.draw, a no-op
        // in the TeaVM font shim, so under Wasm the head is never erased
        // from the skeleton (DIAG35). Erase it geometrically as well: the
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
""",
           """        final Glyph glyph = head.getGlyph();
        final Point2D center = (glyph != null) ? glyph.getCenter2D() : head.getCenter2D();

        final java.awt.Rectangle bounds = (glyph != null) ? glyph.getBounds() : head.getBounds();
        final double cx = bounds.getCenterX();
        final double cy = bounds.getCenterY();
        final double w = bounds.getWidth() * constants.enlargementRatio.getValue();
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue();
        final java.awt.geom.Ellipse2D.Double ell =
                new java.awt.geom.Ellipse2D.Double(cx - (w / 2), cy - (h / 2), w, h);
        final int rx0 = (int) Math.floor(ell.getX());
        final int ry0 = (int) Math.floor(ell.getY());
        final int rx1 = (int) Math.ceil(ell.getX() + ell.getWidth()) - 1;
        final int ry1 = (int) Math.ceil(ell.getY() + ell.getHeight()) - 1;

        // DIAG36 (§31): per-head erasure accounting, print-only.
        final int foreBefore = diag36Count(rx0, ry0, rx1, ry1);
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);
        final int foreAfterPaint = diag36Count(rx0, ry0, rx1, ry1);

        // §30 (TeaVM): paintSymbol draws through TextLayout.draw, a no-op
        // in the TeaVM font shim, so under Wasm the head is never erased
        // from the skeleton (DIAG35). Erase it geometrically as well: the
        // glyph runs (exact head ink, including the slanted tips) plus an
        // ellipse inscribed in the glyph bounds enlarged 1.1x (the desktop
        // paint's enlargement), which also breaks the staff-line segment
        // through the head the way the desktop oval paint does. On desktop
        // both additions whiten pixels paintSymbol already whitened.
        if (glyph != null) {
            processGlyph(glyph);
        }
        final int foreAfterGlyph = diag36Count(rx0, ry0, rx1, ry1);
        final int cornerFore = diag36Corner(rx0, ry0, rx1, ry1, cx, cy, w, h);
        g.fill(ell);
        final int foreAfterEllipse = diag36Count(rx0, ry0, rx1, ry1);
        System.out.println("DIAG36 head#" + (diag36Index++) + " shape=" + head.getShape()
                + " center=" + (int) cx + "," + (int) cy
                + " glyphBounds=" + ((glyph != null) ? glyph.getBounds() : "null")
                + " headBounds=" + head.getBounds()
                + " ellipse=[" + ell.getX() + "," + ell.getY()
                + "," + ell.getWidth() + "," + ell.getHeight() + "]"
                + " foreBefore=" + foreBefore
                + " foreAfterPaint=" + foreAfterPaint
                + " foreAfterGlyph=" + foreAfterGlyph
                + " cornerFore=" + cornerFore
                + " foreAfterEllipse=" + foreAfterEllipse);
    }
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
print("  PageCleaner DIAG36 (§31)")

# --- ROUND 34b: DIAG36 live-image counting (§31) ---
# The first DIAG36 build counted from `buffer` — but ByteProcessor.
# getBufferedImage() copies the pixels into a new array (verified
# 2026-11-10 with a standalone test: fillRect on the image leaves
# buffer.getPixels() unchanged, and getBufferedImage() returns a
# fresh copy from the stale pixels on every call), so the buffer
# counts were flat and only the raw-skeleton corner ink was
# measurable. Thread the live `img` from buildSkeleton into the
# cleaner and read its raster directly (DataBufferByte.getData(),
# O(1), in-place mutations visible); fall back to the buffer if
# the image is unset or not byte-backed.
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """    // DIAG36 (§31): per-head erasure accounting helpers, print-only.
    private int diag36Index = 0;
""",
           """    // DIAG36 (§31): the live image the erasing draws on (set by
    // buildSkeleton; see ROUND 34b). PageCleaner's `buffer` is a stale
    // copy — ByteProcessor.getBufferedImage() copies the pixels — so
    // per-head counts must read from this image, not from `buffer`.
    protected java.awt.image.BufferedImage diag36Img;

    /** DIAG36: point the per-head counters at the live erased image. */
    public void setDiag36Img (java.awt.image.BufferedImage img)
    {
        diag36Img = img;
    }

    // Live pixel array: the image raster when set, else the buffer.
    private byte[] diag36Pixels ()
    {
        if (diag36Img != null) {
            try {
                final java.awt.image.DataBuffer db =
                        diag36Img.getRaster().getDataBuffer();

                if (db instanceof java.awt.image.DataBufferByte) {
                    return ((java.awt.image.DataBufferByte) db).getData();
                }
            } catch (Exception ex) {
                // fall through to buffer
            }
        }

        return (byte[]) buffer.getPixels();
    }

    private int diag36Width ()
    {
        return (diag36Img != null) ? diag36Img.getWidth() : buffer.getWidth();
    }

    private int diag36Height ()
    {
        return (diag36Img != null) ? diag36Img.getHeight() : buffer.getHeight();
    }

    // DIAG36 (§31): per-head erasure accounting helpers, print-only.
    private int diag36Index = 0;
""")
text = sub(text,
           """    private int diag36Count (int x0, int y0, int x1, int y1)
    {
        final byte[] px = (byte[]) buffer.getPixels();
        final int w = buffer.getWidth();
        final int h = buffer.getHeight();
""",
           """    private int diag36Count (int x0, int y0, int x1, int y1)
    {
        final byte[] px = diag36Pixels();
        final int w = diag36Width();
        final int h = diag36Height();
""")
text = sub(text,
           """    private int diag36Corner (int x0, int y0, int x1, int y1,
                              double cx, double cy, double ew, double eh)
    {
        final byte[] px = (byte[]) buffer.getPixels();
        final int w = buffer.getWidth();
        final int h = buffer.getHeight();
""",
           """    private int diag36Corner (int x0, int y0, int x1, int y1,
                              double cx, double cy, double ew, double eh)
    {
        final byte[] px = diag36Pixels();
        final int w = diag36Width();
        final int h = diag36Height();
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
text = read_out("org/audiveris/omr/sheet/curve/Skeleton.java")
text = sub(text,
           """        CurvesCleaner cleaner = new CurvesCleaner(buffer, g, sheet);
""",
           """        CurvesCleaner cleaner = new CurvesCleaner(buffer, g, sheet);
        cleaner.setDiag36Img(img);
""")
write("org/audiveris/omr/sheet/curve/Skeleton.java", text)
print("  PageCleaner DIAG36 live-image counting (§31)")

# ============================================================ ROUND 35 (§32: DIAG37 paint-footprint dump)
# §31 residual: Wasm leaves ~150-230 fore px EXTRA in the final skeleton
# (stage A +453 hymn / +274 Hallelujah, final +150 / +230), uniform
# ~+3.7 px/head, no downstream effect on either verified page. Decomposition
# (per-head totals, hymn): desktop paintSymbol whitens 4,989 fore px;
# Wasm glyph runs cover 4,181 of them; the ellipse recovers 355 of the gap.
# DIAG37 dumps, per head, the pixel footprint of the paint step vs the glyph
# runs vs the ellipse: snapshot the (widened) ellipse-rect fore set before
# paint (S0), after paint (S1), after processGlyph (S2), after the ellipse
# fill (S3), and classify every paint-whitened pixel (S0\S1) by: inside the
# 1.1x ellipse, inside the glyph bounds, on a staff-line row (S0 fore on
# both sides of the glyph bounds in that row), 8-adjacent to a glyph-run
# pixel (fringe), in the glyph runs at all (via RunTable.getRunAt, so the
# classification does not depend on the Wasm run). Also dump the
# paint-not-glyph pixels of the first 12 such heads (DIAG37P lines) so the
# actual shape of the extra footprint is visible. Print-only: snapshots
# only read the live image; the DIAG36 line is unchanged.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """    @Override
    public void visit (HeadInter head)
""",
           """    // DIAG37 (§32): paint-footprint dump helpers, print-only.
    private int diag37Index = 0;
    private int diag37HeadsDumped = 0;

    // Fore snapshot over the int window [x0..x1] x [y0..y1], row-major.
    private boolean[] diag37Snap (int x0, int y0, int x1, int y1)
    {
        final byte[] px = diag36Pixels();
        final int w = diag36Width();
        final int h = diag36Height();
        final int ww = x1 - x0 + 1;
        final int hh = y1 - y0 + 1;
        final boolean[] snap = new boolean[ww * hh];

        for (int y = 0; y < hh; y++) {
            final int iy = y0 + y;

            if ((iy < 0) || (iy >= h)) {
                continue;
            }

            for (int x = 0; x < ww; x++) {
                final int ix = x0 + x;

                if ((ix >= 0) && (ix < w)) {
                    snap[y * ww + x] = ((px[iy * w + ix] & 0xff) == 0);
                }
            }
        }

        return snap;
    }

    // True iff (x,y) is a pixel of the glyph's run table.
    private boolean diag37InGlyphRun (Glyph glyph, int x, int y)
    {
        if (glyph == null) {
            return false;
        }

        return glyph.getRunTable().getRunAt(
                x - glyph.getTopLeft().x, y - glyph.getTopLeft().y) != null;
    }

    // True iff the pixel centre lies strictly inside the ellipse.
    private boolean diag37InEllipse (int x, int y, double cx, double cy, double rx, double ry)
    {
        final double nx = ((x + 0.5) - cx) / rx;
        final double ny = ((y + 0.5) - cy) / ry;

        return (nx * nx + ny * ny) < 1.0;
    }

    @Override
    public void visit (HeadInter head)
""")
text = sub(text,
           """        // DIAG36 (§31): per-head erasure accounting, print-only.
        final int foreBefore = diag36Count(rx0, ry0, rx1, ry1);
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);
        final int foreAfterPaint = diag36Count(rx0, ry0, rx1, ry1);
""",
           """        // DIAG36 (§31): per-head erasure accounting, print-only.
        final int foreBefore = diag36Count(rx0, ry0, rx1, ry1);
        // DIAG37 (§32): widened snapshot window (ellipse rect + 8 px);
        // the paint glyph may extend past the glyph bounds.
        final int wx0 = rx0 - 8;
        final int wy0 = ry0 - 8;
        final int wx1 = rx1 + 8;
        final int wy1 = ry1 + 8;
        final boolean[] diag37S0 = diag37Snap(wx0, wy0, wx1, wy1);
        fs.symbol.paintSymbol(g, fs.font, center, Alignment.AREA_CENTER);
        final int foreAfterPaint = diag36Count(rx0, ry0, rx1, ry1);
        final boolean[] diag37S1 = diag37Snap(wx0, wy0, wx1, wy1);
""")
text = sub(text,
           """        final int foreAfterGlyph = diag36Count(rx0, ry0, rx1, ry1);
""",
           """        final int foreAfterGlyph = diag36Count(rx0, ry0, rx1, ry1);
        final boolean[] diag37S2 = diag37Snap(wx0, wy0, wx1, wy1);
""")
text = sub(text,
           """        final int foreAfterEllipse = diag36Count(rx0, ry0, rx1, ry1);
""",
           """        final int foreAfterEllipse = diag36Count(rx0, ry0, rx1, ry1);
        final boolean[] diag37S3 = diag37Snap(wx0, wy0, wx1, wy1);
""")
text = sub(text,
           """                + " foreAfterEllipse=" + foreAfterEllipse);
""",
           """                + " foreAfterEllipse=" + foreAfterEllipse);
        // DIAG37 (§32): paint-footprint classification, print-only.
        final int ww = wx1 - wx0 + 1;
        final int wh = wy1 - wy0 + 1;
        final boolean[] inG = new boolean[ww * wh];
        for (int yy = 0; yy < wh; yy++) {
            for (int xx = 0; xx < ww; xx++) {
                inG[yy * ww + xx] = diag37InGlyphRun(glyph, wx0 + xx, wy0 + yy);
            }
        }
        // Staff-line rows: S0 fore on both sides of the glyph bounds in this row.
        final boolean[] staffRow = new boolean[wh];
        final int gbx0 = bounds.x;
        final int gbx1 = bounds.x + bounds.width - 1;
        for (int yy = 0; yy < wh; yy++) {
            boolean leftFore = false;
            boolean rightFore = false;
            for (int xx = 0; xx < ww; xx++) {
                if (diag37S0[yy * ww + xx]) {
                    final int ax = wx0 + xx;
                    if (ax < gbx0) {
                        leftFore = true;
                    }
                    if (ax > gbx1) {
                        rightFore = true;
                    }
                }
            }
            staffRow[yy] = leftFore && rightFore;
        }
        int paintN = 0;
        int paintInEll = 0;
        int paintInBnd = 0;
        int paintOutBnd = 0;
        int paintStaff = 0;
        int paintFringe = 0;
        int paintGlyph = 0;
        int paintNotGlyph = 0;
        int paintNotGlyphInEll = 0;
        int paintNotGlyphStaff = 0;
        int paintBorder = 0;
        int glyphN = 0;
        int glyphStep = 0;
        int ellN = 0;
        int ellOutEll = 0;
        int leftN = 0;
        final StringBuilder diag37Px = new StringBuilder();
        for (int yy = 0; yy < wh; yy++) {
            for (int xx = 0; xx < ww; xx++) {
                final int idx = yy * ww + xx;
                final int ax = wx0 + xx;
                final int ay = wy0 + yy;
                final boolean b0 = diag37S0[idx];
                final boolean b1 = diag37S1[idx];
                final boolean b2 = diag37S2[idx];
                final boolean b3 = diag37S3[idx];
                final boolean isGlyphRun = inG[idx];
                if (isGlyphRun) {
                    glyphN++;
                }
                if (b1 && !b2) {
                    glyphStep++;
                }
                if (b2 && !b3) {
                    ellN++;
                    if (!diag37InEllipse(ax, ay, cx, cy, w / 2.0, h / 2.0)) {
                        ellOutEll++;
                    }
                }
                if (b3) {
                    leftN++;
                }
                if (!b0 || b1) {
                    continue;
                }
                paintN++;
                final boolean inEll = diag37InEllipse(ax, ay, cx, cy, w / 2.0, h / 2.0);
                final boolean inBnd = (ax >= bounds.x) && (ax < bounds.x + bounds.width)
                        && (ay >= bounds.y) && (ay < bounds.y + bounds.height);
                if (inEll) {
                    paintInEll++;
                }
                if (inBnd) {
                    paintInBnd++;
                } else {
                    paintOutBnd++;
                }
                if (staffRow[yy]) {
                    paintStaff++;
                }
                boolean fringe = false;
                for (int dy = -1; dy <= 1 && !fringe; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        if ((dx == 0) && (dy == 0)) {
                            continue;
                        }
                        final int nx2 = xx + dx;
                        final int ny2 = yy + dy;
                        if ((nx2 >= 0) && (nx2 < ww) && (ny2 >= 0) && (ny2 < wh)
                                && inG[ny2 * ww + nx2]) {
                            fringe = true;
                            break;
                        }
                    }
                }
                if (fringe) {
                    paintFringe++;
                }
                if (isGlyphRun) {
                    paintGlyph++;
                } else {
                    paintNotGlyph++;
                    if (inEll) {
                        paintNotGlyphInEll++;
                    }
                    if (staffRow[yy]) {
                        paintNotGlyphStaff++;
                    }
                    if (diag37HeadsDumped < 1000) {
                        diag37Px.append(ax).append(",").append(ay)
                                .append(inEll ? "E" : "-")
                                .append(staffRow[yy] ? "S" : "-")
                                .append(fringe ? "F" : "-").append(" ");
                    }
                }
                if ((xx == 0) || (xx == ww - 1) || (yy == 0) || (yy == wh - 1)) {
                    paintBorder++;
                }
            }
        }
        if (paintNotGlyph > 0) {
            diag37HeadsDumped++;
        }
        System.out.println("DIAG37 head#" + (diag37Index++) + " shape=" + head.getShape()
                + " glyphBounds=" + ((glyph != null) ? glyph.getBounds() : "null")
                + " ellipse=[" + ell.getX() + "," + ell.getY()
                + "," + ell.getWidth() + "," + ell.getHeight() + "]"
                + " paintN=" + paintN + " paintInEll=" + paintInEll
                + " paintInBnd=" + paintInBnd + " paintOutBnd=" + paintOutBnd
                + " paintStaff=" + paintStaff + " paintFringe=" + paintFringe
                + " paintGlyph=" + paintGlyph + " paintNotGlyph=" + paintNotGlyph
                + " paintNotGlyphInEll=" + paintNotGlyphInEll
                + " paintNotGlyphStaff=" + paintNotGlyphStaff
                + " paintBorder=" + paintBorder
                + " glyphN=" + glyphN + " glyphStep=" + glyphStep
                + " ellN=" + ellN + " ellOutEll=" + ellOutEll + " leftN=" + leftN);
        if (diag37Px.length() > 0) {
            System.out.println("DIAG37P head#" + (diag37Index - 1) + " px=" + diag37Px);
        }
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
print("  PageCleaner DIAG37 (§32)")

# ============================================================ ROUND 36 (§32: ellipse enlargement 1.1 -> 1.32)
# DIAG37 (§32) measured the desktop paint footprint per head (hymn, 128
# heads): paint whitens 4,989 fore px, of which 4,156 (83.3%) are glyph-run
# ink and 833 (16.7%) are not; of the 833, 399 lie inside the 1.1x ellipse
# (recovered by the ROUND 33 ellipse on Wasm) and 434 outside it, with
# normalised radius 1.04-1.20 (median 1.14, p90 1.19) — ALL within r < 1.20
# of the ellipse, max 1-2 px outside the glyph bounds, 53.9% on staff-line
# rows, 94.4% of all paint pixels 8-adjacent to a glyph run. The paint
# footprint is the Bravura glyph at 1.1x (enlargementRatio) plus an
# anti-aliasing fringe and the slanted notehead tips that stick out past
# the axis-aligned ellipse. Enlarging the ROUND 33 ellipse by a further
# 1.2x (1.32x glyph bounds) covers 830/833 paint-not-glyph pixels (99.6%).
# Scoped to the ellipse w/h computation in visit(HeadInter) only; the
# paintSymbol call and the glyph runs are unchanged. Verify by re-running
# hymn + Hallelujah no-OCR on both sides: stage totals should move toward
# desktop and both .mxl files must stay byte-identical to their controls.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/PageCleaner.java")
text = sub(text,
           """        final double w = bounds.getWidth() * constants.enlargementRatio.getValue();
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue();
""",
           """        // §32 (ROUND 36): DIAG37 measured the desktop paint footprint as the
        // Bravura glyph at 1.1x plus an anti-aliasing fringe and slanted tips
        // reaching normalised radius 1.20 past the 1.1x ellipse (median 1.14,
        // 431/434 non-ellipse paint pixels within r < 1.20). Enlarge the
        // ROUND 33 ellipse by a further 1.2x so it covers the paint footprint.
        final double w = bounds.getWidth() * constants.enlargementRatio.getValue() * 1.2;
        final double h = bounds.getHeight() * constants.enlargementRatio.getValue() * 1.2;
""")
write("org/audiveris/omr/sheet/PageCleaner.java", text)
print("  PageCleaner ellipse enlargement 1.32x (§32)")

# ============================================================ ROUND 37 (§33: DIAG38 HEADERS CME phase localisation)
# Lindenbaum HEADERS CME (§23.8, now deterministic on two pages — Lindenbaum +
# Snow p1 — and 7/37 multi-page pages): DIAG24 FAILED AT LATEST=GRID, dies in
# HEADERS inside a parallel executor task, method unidentified (FakeClass
# stack, unusable). The executor is INLINE under TeaVM (shim
# ThreadPoolExecutor runs every task on the submitting thread), so the CME is
# NOT a true race: it is a single-threaded concurrent modification during
# iteration, where a shim collection's iterator is fail-fast while the JDK
# collection's iterator tolerates the modification (same family as the §10
# CME: shim ConcurrentSkipListMap handed out fail-fast iterators). DIAG38
# brackets each phase of HeaderBuilder.processHeader() with enter/exit prints
# (system id included; systems run in order #1, #2, #3) and catches the CME
# to name the phase. Print-only.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/header/HeaderBuilder.java")
text = replace_method(text, r"public void processHeader \(\)", """    public void processHeader ()
    {
        logger.debug("header processing for S#{}", system.getId());

        // DIAG38 (§33): HEADERS CME phase localisation, print-only.
        String diag38Phase = "entry";

        try {
            // Compute header start abscissae based on bar lines (or staff left abscissa)
            // and store the information in staves themselves.
            diag38Phase = "computeHeaderStarts";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            computeHeaderStarts();
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // Retrieve header clefs
            diag38Phase = "retrieveClefs";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            int clefOffset = clefColumn.retrieveClefs();
            setSystemClefStop(clefOffset);
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // Retrieve header key-sigs
            diag38Phase = "retrieveKeys";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            int keyOffset = keyColumn.retrieveKeys(maxHeaderWidth);
            setSystemKeyStop(keyOffset);
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // Retrieve header time-sigs
            diag38Phase = "retrieveTime";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            int timeOffset = timeColumn.retrieveTime();
            setSystemTimeStop(timeOffset);
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // We should be able now to select the best clef for each staff
            diag38Phase = "selectClefs";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            clefColumn.selectClefs();
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // Purge barline inters found within headers
            diag38Phase = "purgeBarlines";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            purgeBarlines();
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);

            // Freeze header inters
            diag38Phase = "freezeHeaders";
            System.out.println("DIAG38 sys=" + system.getId() + " enter " + diag38Phase);
            freezeHeaders();
            System.out.println("DIAG38 sys=" + system.getId() + " exit " + diag38Phase);
        } catch (java.util.ConcurrentModificationException ex) {
            System.out.println("DIAG38 CME phase=" + diag38Phase + " sys=" + system.getId());
            throw ex;
        }
    }""")
write("org/audiveris/omr/sheet/header/HeaderBuilder.java", text)
print("  HeaderBuilder DIAG38 (§33)")

# ============================================================ ROUND 38 (§33: DIAG39 retrieveKeys sub-phases)
# DIAG38 localised the Lindenbaum HEADERS CME to system #1, phase retrieveKeys
# (KeyColumn.retrieveKeys). DIAG39 brackets its sub-phases — builder
# construction, per-staff KeyBuilder.process(), checkSystemSlices(),
# per-staff finalizeKey(), maxKeyOffset loop — plus the sub-steps inside
# KeyBuilder.process() (retrieveHiLoPeaks, per-ShapeBuilder process,
# selectBestClef), with a CME catch naming the sub-phase. Print-only.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/key/KeyColumn.java")
text = replace_method(text, r"public int retrieveKeys \(int projectionWidth\)", """    public int retrieveKeys (int projectionWidth)
    {
        // DIAG39 (§33): retrieveKeys sub-phase localisation, print-only.
        String diag39Phase = "entry";

        try {
            // Define each staff key-signature area
            diag39Phase = "buildBuilders";
            System.out.println("DIAG39 sys=" + system.getId() + " enter " + diag39Phase);

            for (Staff staff : system.getStaves()) {
                if (staff.isTablature()) {
                    continue;
                }

                int measStart = staff.getHeaderStart();

                Integer clefStop = staff.getClefStop(); // Not very reliable...
                int browseStart = (clefStop != null) ? (clefStop + 1) : (staff.getHeaderStop() + 1);
                builders.put(
                        staff,
                        new KeyBuilder(this, staff, projectionWidth, measStart, browseStart, true));
            }
            System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase);

            // Process each staff to get peaks, slices, alters, trailing space, clef compatibility
            for (KeyBuilder builder : builders.values()) {
                diag39Phase = "process staff=" + builder.getId();
                System.out.println("DIAG39 sys=" + system.getId() + " enter " + diag39Phase);
                builder.process();
                System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase);
            }

            if (system.isMultiStaff()) {
                // Check keys alignment across staves at system level
                diag39Phase = "checkSystemSlices";
                System.out.println("DIAG39 sys=" + system.getId() + " enter " + diag39Phase);

                if (!checkSystemSlices()) {
                    for (KeyBuilder builder : builders.values()) {
                        builder.destroyAll();
                    }

                    System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase + " NOKEY");
                    return 0; // No key in system
                }
                System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase);
            }

            // Adjust each individual alter pitch, according to best matching key-sig
            // A staff may have no key-sig while the others have some in the same system
            for (KeyBuilder builder : builders.values()) {
                diag39Phase = "finalizeKey staff=" + builder.getId();
                System.out.println("DIAG39 sys=" + system.getId() + " enter " + diag39Phase);
                builder.finalizeKey();
                System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase);
            }

            // Push header key stop
            diag39Phase = "maxKeyOffset";
            System.out.println("DIAG39 sys=" + system.getId() + " enter " + diag39Phase);
            int maxKeyOffset = 0;

            for (Staff staff : system.getStaves()) {
                if (!staff.isTablature()) {
                    int measureStart = staff.getHeaderStart();
                    Integer keyStop = staff.getKeyStop();

                    if (keyStop != null) {
                        maxKeyOffset = Math.max(maxKeyOffset, keyStop - measureStart);
                    }
                }
            }
            System.out.println("DIAG39 sys=" + system.getId() + " exit " + diag39Phase);

            return maxKeyOffset;
        } catch (java.util.ConcurrentModificationException ex) {
            System.out.println("DIAG39 CME phase=" + diag39Phase + " sys=" + system.getId());
            throw ex;
        }
    }""")
write("org/audiveris/omr/sheet/key/KeyColumn.java", text)
print("  KeyColumn DIAG39 (§33)")

text = copy_src("org/audiveris/omr/sheet/key/KeyBuilder.java")
text = replace_method(text, r"public void process \(\)", """    public void process ()
    {
        if (isVip) {
            logger.info("VIP process key for S#{} staff#{}", system.getId(), getId());
        }

        // DIAG39 (§33): process() sub-step localisation, print-only.
        System.out.println("DIAG39B staff=" + getId() + " enter retrieveHiLoPeaks");
        List<Range> hiloPeaks = retrieveHiLoPeaks(); // Retrieve all hilo peaks
        System.out.println("DIAG39B staff=" + getId() + " exit retrieveHiLoPeaks n=" + hiloPeaks.size());

        for (ShapeBuilder shapeBuilder : shapeBuilders.values()) {
            System.out.println("DIAG39B staff=" + getId() + " enter shapeBuilder.process " + shapeBuilder.getKeyShape());
            shapeBuilder.process(hiloPeaks);
            System.out.println("DIAG39B staff=" + getId() + " exit shapeBuilder.process " + shapeBuilder.getKeyShape());
        }

        System.out.println("DIAG39B staff=" + getId() + " enter selectBestClef");
        selectBestClef(); // In case staff clef has not yet been selected
        System.out.println("DIAG39B staff=" + getId() + " exit selectBestClef");
    }""")
write("org/audiveris/omr/sheet/key/KeyBuilder.java", text)
print("  KeyBuilder DIAG39B (§33)")

# ============================================================ ROUND 39 (§35: DIAG41 LEDGERS %f failure)
# Hallelujah p06 dies in LEDGERS (not BEAMS — §33.6.2's attribution was
# wrong: TeavmMain's DIAG24 FAILED AT LATEST prints SheetStub.getLatestStep(),
# which reports the latest step DONE, so the failure is in the NEXT step
# after BEAMS, i.e. LEDGERS; the 225 consecutive DIAG14 getSource(NO_STAFF)
# lines between system #3's BEAMS prints and the failure are
# LedgersBuilder.ConvexityCheck.getValue(), called per ledger candidate).
# LedgersStep.doEpilog runs LedgersPostAnalysis.process() -> collect() ->
# filter(), and filter() calls String.format with SIX boxed Doubles that
# stay null when their Population is empty (cardinality 0):
#   min/maxDeltaAboveRatio (popDeltaAbove, ledgers with key < 0),
#   min/maxDeltaBelowRatio (popDeltaBelow, ledgers with key > 0),
#   min/maxHeightRatio (popHeight, every ledger).
# String.format("%.2f", (Double) null) throws exactly
# IllegalFormatConversionException "Can't format argument of null using f
# conversion" — the observed exception. The format argument is evaluated
# eagerly before logger.debug is invoked, so desktop would throw too if a
# population were empty there; desktop completes p06, so on desktop all
# three populations are non-empty. DIAG41 prints the cardinalities and the
# six ratios (null prints as "null") before the format, plus a per-staff
# ledger census in collect(), on both sides. Print-only.
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/ledger/LedgersPostAnalysis.java")
text = sub(text, """                    // Only isolated ledgers are representative for their width
                    if (wRatio <= maxWRatio) {
                        popWidth.includeValue(wRatio);
                    }
                }
            }
        }

        logger.debug("deltaAboveRatio: {}", popDeltaAbove);""", """                    // Only isolated ledgers are representative for their width
                    if (wRatio <= maxWRatio) {
                        popWidth.includeValue(wRatio);
                    }
                }
            }

            // DIAG41 (§35): per-staff ledger census, print-only.
            int diag41Above = 0;
            int diag41Below = 0;

            for (Map.Entry<Integer, List<LedgerInter>> diag41e : map.entrySet()) {
                if (diag41e.getKey() < 0) {
                    diag41Above += diag41e.getValue().size();
                } else if (diag41e.getKey() > 0) {
                    diag41Below += diag41e.getValue().size();
                }
            }

            System.out.println("DIAG41 collect staff#" + staff.getId() + " keys=" + map.keySet()
                    + " above=" + diag41Above + " below=" + diag41Below);
        }

        // DIAG41 (§35): population cardinalities before filter(), print-only.
        System.out.println("DIAG41 collect infos=" + infoMap.size()
                + " cardAbove=" + popDeltaAbove.getCardinality()
                + " cardBelow=" + popDeltaBelow.getCardinality()
                + " cardHeight=" + popHeight.getCardinality()
                + " cardWidth=" + popWidth.getCardinality());

        logger.debug("deltaAboveRatio: {}", popDeltaAbove);""")
text = sub(text, """        logger.debug(
                "{}",
                String.format(
                        "Filter minDeltaAboveRatio:%.2f maxDeltaAboveRatio:%.2f"
                                + " minDeltaBelowRatio:%.2f maxDeltaBelowRatio:%.2f"
                                + " minHeightRatio:%.2f maxHeightRatio:%.2f",
                        minDeltaAboveRatio,
                        maxDeltaAboveRatio,
                        minDeltaBelowRatio,
                        maxDeltaBelowRatio,
                        minHeightRatio,
                        maxHeightRatio));""", """        // DIAG41 (§35): name the null ratio before the %f format, print-only.
        System.out.println("DIAG41 filter cardAbove=" + popDeltaAbove.getCardinality()
                + " cardBelow=" + popDeltaBelow.getCardinality()
                + " cardHeight=" + popHeight.getCardinality()
                + " minAbove=" + minDeltaAboveRatio + " maxAbove=" + maxDeltaAboveRatio
                + " minBelow=" + minDeltaBelowRatio + " maxBelow=" + maxDeltaBelowRatio
                + " minHeight=" + minHeightRatio + " maxHeight=" + maxHeightRatio);

        logger.debug(
                "{}",
                String.format(
                        "Filter minDeltaAboveRatio:%.2f maxDeltaAboveRatio:%.2f"
                                + " minDeltaBelowRatio:%.2f maxDeltaBelowRatio:%.2f"
                                + " minHeightRatio:%.2f maxHeightRatio:%.2f",
                        minDeltaAboveRatio,
                        maxDeltaAboveRatio,
                        minDeltaBelowRatio,
                        maxDeltaBelowRatio,
                        minHeightRatio,
                        maxHeightRatio));

        // DIAG41 (§35): reached only if the %f format above did not throw.
        System.out.println("DIAG41 filter formatted ok");""")
write("org/audiveris/omr/sheet/ledger/LedgersPostAnalysis.java", text)
print("  LedgersPostAnalysis DIAG41 (§35)")

# ============================================================ ROUND 42 (§36: DIAG42 catalog-cliff calibration)
# Cliff map from the multi-page run (full-out63) + desktop .omr scale blocks:
#   desktop point size is CONSTANT per piece (Hallelujah 71-72, w~21;
#   BWV 227 64, w~19-20; Gute Nacht 92, w~27.1; hymn 92, w=27.2),
#   but Wasm requests 72 on working Hallelujah pages and 140/142 on
#   p04/p05/p06/p08, 128 on every BWV 227 page, 92 on Gute Nacht —
#   i.e. the Wasm-side calibrated point size is ~2x the desktop value on
#   the failing pages, with identical interline (16-17) and image size
#   on working vs failing Hallelujah pages. The chain (stock code):
#     Staff.getHeadPointSize() = MusicFont.getHeadPointSize(scale,
#       specificInterline): rint((staffInterline / sheetInterline)
#       * musicFontScale.pointSize) when the sizer set a scale, else the
#       fallback getPointSize(rint(staffInterline * headRatio=1.0)) =
#       4 * staffInterline (~68 for Hallelujah — NOT 140, so the
#       fallback is already ruled out by arithmetic).
#     musicFontScale.pointSize = MusicFont.computePointSize(w), w =
#       BlackHeadSizer core black-head mean width: v1=rint(w*3.3),
#       w1 = layout width at v1, v2 = v1 +/- rint(w*0.25),
#       v = rint(v1 + (v2-v1)*(w-w1)/(w2-w1)).
#   DIAG42 prints the three links on both sides, print-only: the sizer
#   population (singles/core counts, w/h mean/sd, resulting point size),
#   the computePointSize intermediates (w, v1, w1, v2, w2, v), and the
#   per-staff head point size with its ratio inputs. That splits
#   (a) measured width ~2x (sizer population differs under Wasm) from
#   (b) interpolation divergence (shim layout widths wrong) from
#   (c) ratio divergence (staff/sheet interline inputs differ).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/beam/BlackHeadSizer.java")
text = sub(text, """    private void measureSingles (List<Glyph> singles)
    {
        if (singles.size() < params.singlesQuorum) {
            return;
        }""", """    private void measureSingles (List<Glyph> singles)
    {
        if (singles.size() < params.singlesQuorum) {
            // DIAG42 (§36): quorum fail means no musicFontScale is set.
            System.out.println("DIAG42 sizer QUORUM-FAIL singles=" + singles.size()
                    + " quorum=" + params.singlesQuorum);
            return;
        }""")
text = sub(text, """        final double w = blackHeadScale.getWidthMean();
        final MusicFamily family = sheet.getStub().getMusicFamily();
        final MusicFont font = MusicFont.getHeadFont(family, sheet.getScale(), 0);
        final MusicFontScale musicFontScale = font.buildMusicFontScale(w);
        sheet.getScale().setMusicFontScale(musicFontScale);""", """        final double w = blackHeadScale.getWidthMean();
        final MusicFamily family = sheet.getStub().getMusicFamily();
        final MusicFont font = MusicFont.getHeadFont(family, sheet.getScale(), 0);
        final MusicFontScale musicFontScale = font.buildMusicFontScale(w);
        sheet.getScale().setMusicFontScale(musicFontScale);
        // DIAG42 (§36): sizer population + resulting point size, print-only.
        System.out.println("DIAG42 sizer singles=" + singles.size() + " core=" + core.size()
                + " wMean=" + widths.getMeanValue() + " wSd=" + widths.getStandardDeviation()
                + " hMean=" + heights.getMeanValue() + " hSd=" + heights.getStandardDeviation()
                + " mfsPoint=" + musicFontScale.getPointSize());""")
write("org/audiveris/omr/sheet/beam/BlackHeadSizer.java", text)
print("  BlackHeadSizer DIAG42 (§36)")

text = copy_src("org/audiveris/omr/ui/symbol/MusicFont.java")
text = sub(text, """        {
            // Just for verification
            final MusicFont font = new MusicFont(musicFamily, v);
            final TextLayout layout = font.layoutShapeByCode(shape);
            final double w = layout.getBounds().getWidth();
            logger.debug("width:{}", width);
            logger.debug("v1:{},w1:{} v:{},w:{} v2:{},w2:{}", v1, w1, v, w, v2, w2);
        }""", """        {
            // Just for verification
            final MusicFont font = new MusicFont(musicFamily, v);
            final TextLayout layout = font.layoutShapeByCode(shape);
            final double w = layout.getBounds().getWidth();
            logger.debug("width:{}", width);
            logger.debug("v1:{},w1:{} v:{},w:{} v2:{},w2:{}", v1, w1, v, w, v2, w2);
            // DIAG42 (§36): interpolation intermediates, print-only.
            System.out.println("DIAG42 cps width=" + width + " v1=" + v1 + " w1=" + w1
                    + " v2=" + v2 + " w2=" + w2 + " v=" + v + " wAtV=" + w);
        }""")
text = sub(text, """        if (musicFontScale != null) {
            // Interpolate from large staff information
            final double ratio = (double) staffInterline / scale.getInterline();
            return (int) Math.rint(ratio * musicFontScale.getPointSize());
        } else {
            // No precise information available, fall back using head ratio constant...
            logger.debug("MusicFont. Using head ratio constant");
            return getPointSize((int) Math.rint(staffInterline * constants.headRatio.getValue()));
        }""", """        if (musicFontScale != null) {
            // Interpolate from large staff information
            final double ratio = (double) staffInterline / scale.getInterline();
            // DIAG42 (§36): per-staff head point size + ratio inputs, print-only.
            System.out.println("DIAG42 headps staffInterline=" + staffInterline
                    + " sheetInterline=" + scale.getInterline()
                    + " mfsPoint=" + musicFontScale.getPointSize()
                    + " -> " + (int) Math.rint(ratio * musicFontScale.getPointSize()));
            return (int) Math.rint(ratio * musicFontScale.getPointSize());
        } else {
            // No precise information available, fall back using head ratio constant...
            logger.debug("MusicFont. Using head ratio constant");
            // DIAG42 (§36): fallback path taken, print-only.
            System.out.println("DIAG42 headps FALLBACK staffInterline=" + staffInterline
                    + " -> " + getPointSize((int) Math.rint(staffInterline * constants.headRatio.getValue())));
            return getPointSize((int) Math.rint(staffInterline * constants.headRatio.getValue()));
        }""")
write("org/audiveris/omr/ui/symbol/MusicFont.java", text)
print("  MusicFont DIAG42 (§36)")

# ============================================================ ROUND 44 (§38: DIAG44 StackRhythm divergence)
# Re-established on full-out84 (compare_rhythm.py, phase44/):
#   Hallelujah p01: 2 of 56 measures differ, both rhythm-only —
#     P2 m9: desktop ties two A/4 eighths (tie start/stop), Wasm none;
#       slur elements 22=22 in every part, ties 4 vs 2, all in P2.
#     The P2 m9 slur exists on desktop as a tie; under Wasm it is
#     either missing from the SIG or not flagged as a tie.
#     (The §25.5 six-measure rhythm split is GONE: Wasm no longer
#     fails S2 #5 / S3 #9 — both sides now fail only S2 #8.)
#     P3 m10: tuplet assignment differs in the S2 #8 "no correct
#       rhythm" stack (fails on BOTH sides, yet resolves differently):
#       desktop R:6 plain / E:2 tuplet / R:6 plain;
#       Wasm   R:4 tuplet / E:3 plain / R:4 tuplet.
#   Lindenbaum: 0 of 24 measures differ in rhythm (deep diff 10, all
#     filename/±1); its four "no correct rhythm" stacks are identical
#     on both sides — no divergence to diagnose there.
# DIAG44 splits the two Hallelujah divergences:
#   DIAG44A in SlurInter.checkStaffTie (LINKS doEpilog, runs for EVERY
#     slur in every system): decision inputs + result. A missing P2 m9
#     line means the slur is absent from the Wasm SIG; a line with
#     tie=false names which input differs.
#   DIAG44B in TupletsBuilder (SYMBOLS, SymbolsLinker): candidate order
#     per tuplet sign, collector outcome, linked chords. The collector
#     depends on candidate order (ByEuclidean sort), beam siblings
#     (distanceSq — already inlined, R2[32]) and durations, so an order
#     or inclusion difference here is the smoking gun for P3 m10.
#     implicitTuplets defaults to false, so the MeasureRhythm
#     findImplicitTuplets / analyzeTimes 3/2 paths are OFF — the P3 m10
#     tuplets are explicit TupletInter signs, linked by TupletsBuilder.
#   DIAG44C in StackRhythm.doProcess + MeasureRhythm.finalCheck:
#     per-measure rhythm outcome + un-timed/voiceless chords.
# All prints are print-only (same patched files both sides).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sig/inter/SlurInter.java")
text = sub(text, """        HeadInter h1 = getHead(LEFT);
        HeadInter h2 = getHead(RIGHT);
        boolean result = (h1 != null) && (h2 != null) && (h1.getStaff() == h2.getStaff())
                && areTieCompatible(h1, h2) && isSpaceClear(h1, h2, systemHeadChords);
        setTie(result);""", """        HeadInter h1 = getHead(LEFT);
        HeadInter h2 = getHead(RIGHT);
        boolean sameStaff = (h1 != null) && (h2 != null) && (h1.getStaff() == h2.getStaff());
        boolean compatible = areTieCompatible(h1, h2);
        boolean spaceClear = isSpaceClear(h1, h2, systemHeadChords);
        boolean result = sameStaff && compatible && spaceClear;
        setTie(result);
        // DIAG44A (§38): tie decision trace, print-only. isSpaceClear is
        // null-safe; head centers locate the slur without getBounds()
        // (null curve would trap, §28 lesson).
        String d1 = (h1 == null) ? "null"
                : ("#" + h1.getId() + " " + h1.getStep() + h1.getOctave()
                + " staff#" + h1.getStaff().getId() + " @" + h1.getCenter());
        String d2 = (h2 == null) ? "null"
                : ("#" + h2.getId() + " " + h2.getStep() + h2.getOctave()
                + " staff#" + h2.getStaff().getId() + " @" + h2.getCenter());
        System.out.println("DIAG44 tie slur#" + getId() + " left=" + d1 + " right=" + d2
                + " sameStaff=" + sameStaff + " compatible=" + compatible
                + " spaceClear=" + spaceClear + " tie=" + result);""")
write("org/audiveris/omr/sig/inter/SlurInter.java", text)
print("  SlurInter DIAG44A (§38)")

text = copy_src("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java")
text = sub(text, """        Collections.sort(chords, new ByEuclidean(tupletCenter));
        logger.trace("Chords: {}", Inters.ids(chords));""", """        Collections.sort(chords, new ByEuclidean(tupletCenter));
        logger.trace("Chords: {}", Inters.ids(chords));
        // DIAG44B (§38): candidate order for this tuplet sign, print-only.
        System.out.println("DIAG44 tupletCand tuplet#" + tuplet.getId() + " "
                + tuplet.getShape() + " @" + tupletCenter
                + " cands=" + Inters.ids(chords));""")
text = sub(text, """            if (collector.isNotOk()) {
                logger.debug("{} {}", tuplet, collector.getStatusMessage());

                return null;
            } else if (collector.isOk()) {
                if (logger.isDebugEnabled()) {
                    collector.dump();
                }

                return collector.getChords(); // Normal exit
            }""", """            if (collector.isNotOk()) {
                logger.debug("{} {}", tuplet, collector.getStatusMessage());
                // DIAG44B (§38): collector failure, print-only.
                System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage());
                return null;
            } else if (collector.isOk()) {
                if (logger.isDebugEnabled()) {
                    collector.dump();
                }
                // DIAG44B (§38): embraced chords, print-only.
                System.out.println("DIAG44 tupletOk tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage()
                        + " chords=" + Inters.ids(collector.getChords()));
                return collector.getChords(); // Normal exit
            }""")
text = sub(text, """        // Candidates are exhausted, we lack chords
        logger.debug("{} {}", tuplet, collector.getStatusMessage());

        return null;""", """        // Candidates are exhausted, we lack chords
        logger.debug("{} {}", tuplet, collector.getStatusMessage());
        // DIAG44B (§38): exhausted candidates, print-only.
        System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                + collector.getStatusMessage());
        return null;""")
text = sub(text, """            final Collection<Link> links = lookupLinks(tuplet);

            for (Link link : links) {
                link.applyTo(tuplet);
            }""", """            final Collection<Link> links = lookupLinks(tuplet);

            for (Link link : links) {
                link.applyTo(tuplet);
            }

            // DIAG44B (§38): linked chords for this tuplet sign, print-only.
            {
                StringBuilder sb = new StringBuilder();
                sb.append("DIAG44 tupletLink tuplet#").append(tuplet.getId());
                for (Link link : links) {
                    sb.append(" #").append(link.partner.getId());
                }
                System.out.println(sb.toString());
            }""")
write("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java", text)
print("  TupletsBuilder DIAG44B (§38)")

text = copy_src("org/audiveris/omr/sheet/rhythm/StackRhythm.java")
text = sub(text, """        // Process measure by measure
        for (Measure measure : stack.getMeasures()) {
            final boolean measureOk = new MeasureRhythm(measure).process();

            if (!measureOk) {
                measure.setAbnormal(true);
            }

            stackOk &= measureOk;
        }""", """        // Process measure by measure
        for (Measure measure : stack.getMeasures()) {
            final boolean measureOk = new MeasureRhythm(measure).process();

            if (!measureOk) {
                measure.setAbnormal(true);
            }

            stackOk &= measureOk;
            // DIAG44C (§38): per-measure rhythm outcome, print-only.
            System.out.println("DIAG44 rhythm " + stack + " " + measure
                    + " ok=" + measureOk + " abnormal=" + measure.isAbnormal());
        }""")
write("org/audiveris/omr/sheet/rhythm/StackRhythm.java", text)
print("  StackRhythm DIAG44C (§38)")

text = copy_src("org/audiveris/omr/sheet/rhythm/MeasureRhythm.java")
text = sub(text, """        // Check if every measure chord has a voice and a time offset
        for (AbstractChordInter ch : measure.getStandardChords()) {
            ok &= (ch.getVoice() != null);
            ok &= (ch.getTimeOffset() != null);
        }""", """        // Check if every measure chord has a voice and a time offset
        for (AbstractChordInter ch : measure.getStandardChords()) {
            ok &= (ch.getVoice() != null);
            ok &= (ch.getTimeOffset() != null);
            // DIAG44C (§38): un-timed / voiceless chord, print-only.
            if ((ch.getVoice() == null) || (ch.getTimeOffset() == null)) {
                System.out.println("DIAG44 rhythmNoTime " + measure + " chord#" + ch.getId()
                        + " voice=" + ch.getVoice() + " timeOffset=" + ch.getTimeOffset());
            }
        }""")
write("org/audiveris/omr/sheet/rhythm/MeasureRhythm.java", text)
print("  MeasureRhythm DIAG44C (§38)")

# ============================================================ ROUND 45 (§39: DIAG45 StackRhythm upstream SIG)
# DIAG44 (§38) pinned both remaining Hallelujah rhythm divergences to
# upstream SIG differences and exonerated StackRhythm/MeasureRhythm:
#   (A) P2 m9 tie: the tie-slur inter is absent from the Wasm SIG at
#       LINKS (checkStaffTie 13x desktop, 12x Wasm; missing call is the
#       A4 (1273,1697) -> A4 (1340,1697) slur). Mining the full-out85
#       logs with the existing DIAG33 prints localises it further
#       BEFORE this build: the tie arc IS modelled identically
#       (seed MODEL p0=(1290,1657) npts=59 accept, 11 MODELs identical
#       both sides) and enters weed in block #433/#429 with the same 5
#       candidates and grades — but purgeStaffLines deletes 4 of 5 on
#       Wasm (255/264/265/266; only 267 survives) vs 1 of 5 on desktop
#       (261 only; 270/271/272/273 survive and extend into the final
#       tie slurs 274/276/278, boxes (1284,1656,68,4) etc., which never
#       appear on Wasm). The Wasm deletions are reason=
#       staff-line-incidence at ends (1284,1658), (1286,1658),
#       (1288,1658); the desktop counterparts are never purged. So the
#       divergence is the incidence gate in purgeStaffLines, at the 1px
#       level (maxIncidence 15 deg; tangentLength 0.5 interline ~8 px).
#       DIAG45B dumps the gate inputs per candidate to name the exact
#       differing number (end / staff-line y / toLine / tangent p1,p2 /
#       dx,dy / incidence).
#   (B) P3 m10 tuplet: collector candidate order identical, but Wasm
#       skips the 16th chord (6312 = 6867) by the staff check — proved
#       by the collector's arithmetic (§38.4.2) — while desktop
#       embraces 16th+eighth (base 1/16). DIAG45A dumps, per candidate
#       in getEmbracedChords, top staff, duration, member heads
#       (staff + center y) and the skip reason, to prove/refute the
#       "16th chord's top staff != staff 7 under Wasm" hypothesis and
#       find why (1px boundary head? extra head? getTopStaff?).
#       Also routes the collector dump() through System.out (the
#       logger.info dump is invisible under Wasm, §38.4.5).
# All prints are print-only (same patched files both sides).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java")  # ROUND 44 output, not pristine src
text = sub(text, """        final Staff targetStaff = getTargetStaff(candidates);
""", """        final Staff targetStaff = getTargetStaff(candidates);
        // DIAG45A (§39): target staff for this tuplet sign, print-only.
        System.out.println("DIAG45 tupletTarget tuplet#" + tuplet.getId() + " "
                + tuplet.getShape() + " @" + tuplet.getCenter()
                + " targetStaff=" + ((targetStaff == null) ? null : targetStaff.getId()));
""")
text = sub(text, """        for (AbstractChordInter chord : candidates) {
            // We assume that chords with 2 staves have their tuplet sign above...
            Staff staff = chord.getTopStaff();

            // Check that all chords are on the same staff
            if (staff != targetStaff) {
                continue;
            }
""", """        for (AbstractChordInter chord : candidates) {
            // We assume that chords with 2 staves have their tuplet sign above...
            Staff staff = chord.getTopStaff();

            // DIAG45A (§39): per-candidate staff/duration/members, print-only.
            // (Pure getters only; getDurationSansTuplet may be null.)
            {
                StringBuilder sb = new StringBuilder();
                sb.append("DIAG45 tupletCand2 tuplet#").append(tuplet.getId());
                sb.append(" chord#").append(chord.getId());
                sb.append(" rest=").append(chord.isRest());
                sb.append(" topStaff=").append((staff == null) ? null : staff.getId());
                Rational d45dur = chord.getDurationSansTuplet();
                sb.append(" dur=").append(d45dur);
                sb.append(" members=[");
                boolean first = true;
                for (org.audiveris.omr.sig.inter.Inter m : chord.getMembers()) {
                    if (!first) {
                        sb.append(",");
                    }
                    first = false;
                    sb.append("#").append(m.getId()).append(":")
                            .append(m.getShape())
                            .append(":staff=").append((m.getStaff() == null) ? null : m.getStaff().getId())
                            .append("@y=").append(m.getCenter().y);
                }
                sb.append("]");
                System.out.println(sb.toString());
            }

            // Check that all chords are on the same staff
            if (staff != targetStaff) {
                // DIAG45A (§39): staff-check skip, print-only.
                System.out.println("DIAG45 tupletSkip tuplet#" + tuplet.getId()
                        + " chord#" + chord.getId()
                        + " reason=staff-mismatch topStaff="
                        + ((staff == null) ? null : staff.getId())
                        + " targetStaff=" + ((targetStaff == null) ? null : targetStaff.getId()));
                continue;
            }
""")
text = sub(text, """            if (collector.isNotOk()) {
                logger.debug("{} {}", tuplet, collector.getStatusMessage());
                // DIAG44B (§38): collector failure, print-only.
                System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage());
                return null;
            } else if (collector.isOk()) {
                if (logger.isDebugEnabled()) {
                    collector.dump();
                }
                // DIAG44B (§38): embraced chords, print-only.
                System.out.println("DIAG44 tupletOk tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage()
                        + " chords=" + Inters.ids(collector.getChords()));
                return collector.getChords(); // Normal exit
            }
""", """            if (collector.isNotOk()) {
                logger.debug("{} {}", tuplet, collector.getStatusMessage());
                // DIAG44B (§38): collector failure, print-only.
                System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage());
                // DIAG45A (§39): collector dump through System.out, print-only.
                System.out.println("DIAG45 tupletDump tuplet#" + tuplet.getId()
                        + " status=" + collector.status
                        + " base=" + collector.base
                        + " expectedTotal=" + collector.expectedTotal
                        + " total=" + collector.total
                        + " chords=" + Inters.ids(collector.getChords()));
                return null;
            } else if (collector.isOk()) {
                if (logger.isDebugEnabled()) {
                    collector.dump();
                }
                // DIAG44B (§38): embraced chords, print-only.
                System.out.println("DIAG44 tupletOk tuplet#" + tuplet.getId() + " "
                        + collector.getStatusMessage()
                        + " chords=" + Inters.ids(collector.getChords()));
                // DIAG45A (§39): collector dump through System.out, print-only.
                System.out.println("DIAG45 tupletDump tuplet#" + tuplet.getId()
                        + " status=" + collector.status
                        + " base=" + collector.base
                        + " expectedTotal=" + collector.expectedTotal
                        + " total=" + collector.total
                        + " chords=" + Inters.ids(collector.getChords()));
                return collector.getChords(); // Normal exit
            }
""")
text = sub(text, """        // Candidates are exhausted, we lack chords
        logger.debug("{} {}", tuplet, collector.getStatusMessage());
        // DIAG44B (§38): exhausted candidates, print-only.
        System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                + collector.getStatusMessage());
        return null;
""", """        // Candidates are exhausted, we lack chords
        logger.debug("{} {}", tuplet, collector.getStatusMessage());
        // DIAG44B (§38): exhausted candidates, print-only.
        System.out.println("DIAG44 tupletFail tuplet#" + tuplet.getId() + " "
                + collector.getStatusMessage());
        // DIAG45A (§39): collector dump through System.out, print-only.
        System.out.println("DIAG45 tupletDump tuplet#" + tuplet.getId()
                + " status=" + collector.status
                + " base=" + collector.base
                + " expectedTotal=" + collector.expectedTotal
                + " total=" + collector.total
                + " chords=" + Inters.ids(collector.getChords()));
        return null;
""")
write("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java", text)
print("  TupletsBuilder DIAG45A (§39)")

text = read_out("org/audiveris/omr/sheet/curve/SlursBuilder.java")  # ROUND 29/30 output, not pristine src
text = sub(text, """            // Vertical distance from slur end to closest staff line
            Staff staff = sheet.getStaffManager().getClosestStaff(end);

            if (!staff.isTablature()) {
                final LineInfo line = staff.getClosestStaffLine(end);
                final double toLine = line.yAt(end.x) - end.y;

                if (abs(toLine) > params.maxStaffLineDy) {
                    continue;
                }
            }
""", """            // Vertical distance from slur end to closest staff line
            Staff staff = sheet.getStaffManager().getClosestStaff(end);

            // DIAG45B (§39): hoisted for the purge diagnostic, print-only.
            double diag45lineY = Double.NaN;
            double diag45toLine = Double.NaN;

            if (!staff.isTablature()) {
                final LineInfo line = staff.getClosestStaffLine(end);
                diag45lineY = line.yAt(end.x);
                diag45toLine = diag45lineY - end.y;

                if (abs(diag45toLine) > params.maxStaffLineDy) {
                    // DIAG45B (§39): keep, end far from staff line, print-only.
                    System.out.println("DIAG45 purge id=" + inter.getInfo().getId()
                            + " end=" + end + " lineY=" + diag45lineY
                            + " toLine=" + diag45toLine + " maxDy=" + params.maxStaffLineDy
                            + " decision=keep-far");
                    continue;
                }
            }
""")
text = sub(text, """            // Delete slur ending as a STAFF_ARC
            Arc endPart = slur.getPartAt(end);
""", """            // Delete slur ending as a STAFF_ARC
            Arc endPart = slur.getPartAt(end);

            // DIAG45B (§39): purge gate inputs for every candidate that
            // reaches here, print-only. (Tangent values duplicated from
            // below; pure getters, no side effects.)
            {
                List<Point> d45pts = slur.getSidePoints(reverse, params.tangentLength);
                Point d45p1 = d45pts.isEmpty() ? null
                        : (reverse ? d45pts.get(d45pts.size() - 1) : d45pts.get(0));
                Point d45p2 = d45pts.isEmpty() ? null
                        : (reverse ? d45pts.get(0) : d45pts.get(d45pts.size() - 1));
                double d45dx = (d45p1 == null) ? Double.NaN : Math.abs(d45p2.x - d45p1.x);
                double d45dy = (d45p1 == null) ? Double.NaN : Math.abs(d45p2.y - d45p1.y);
                double d45inc = (d45dx < 1) ? Double.NaN : Math.atan(d45dy / d45dx);
                System.out.println("DIAG45 purge id=" + inter.getInfo().getId()
                        + " end=" + end + " lineY=" + diag45lineY
                        + " toLine=" + diag45toLine + " maxDy=" + params.maxStaffLineDy
                        + " endPart=" + ((endPart == null) ? null : endPart.getShape())
                        + " p1=" + d45p1 + " p2=" + d45p2
                        + " dx=" + d45dx + " dy=" + d45dy
                        + " incidenceDeg=" + Math.toDegrees(d45inc)
                        + " maxIncDeg=" + Math.toDegrees(params.maxIncidence));
            }
""")
write("org/audiveris/omr/sheet/curve/SlursBuilder.java", text)
print("  SlursBuilder DIAG45B (§39)")

# ============================================================ ROUND 46 (§40: DIAG46 StackRhythm 1px inputs)
# DIAG45 (§39) measured both remaining Hallelujah rhythm divergences to
# their exact gate inputs, and both are 1px knife-edges — but the exact
# 1px input that flips each gate is still unproven:
#   (A) P2 m9 tie: purgeStaffLines kills the slur under Wasm at incidence
#       14.036 deg (atan(2/8)) vs desktop 15.945 deg (atan(2/7)), 15 deg
#       threshold. Staff-line Y 1656.0 vs 1657.0, tangent dx 7 vs 8.
#       DIAG46A dumps, for the tie-region candidates, the staff-line fit
#       (defining points + unrounded spline yAtX) and the full arc point
#       list, to name the pixel(s) moving the line fit and the arc by 1px.
#   (B) P3 m10 tuplet: filterChordsOnAbscissa discards 6902 on desktop
#       (keeps 6880, the staff-7 16th) and discards 6290 (== 6880) under
#       Wasm (keeps 6312 == 6902); ByEuclidean order swaps at positions
#       5/6. DIAG46B dumps, for the (2067,1970) sign only, the candidate
#       order with each chord's bounds/center/bounds-distance to the sign,
#       plus every overlapping-pair comparison (bounds, centers, d1/d2,
#       which was discarded), to name the exact flipping pixel.
# All prints are print-only (same patched files both sides).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/curve/SlursBuilder.java")  # ROUND 29/30/45 output, not pristine src
text = sub(text, """                        + " maxIncDeg=" + Math.toDegrees(params.maxIncidence));
            }
""", """                        + " maxIncDeg=" + Math.toDegrees(params.maxIncidence));
            }

            // DIAG46A (§40): staff-line fit + arc points for the P2 m9
            // tie region, print-only. (Pure getters; the line fit is the
            // StaffLine's defining points + spline evaluation.)
            if (!staff.isTablature()
                    && (end.x >= 1270) && (end.x <= 1360)
                    && (end.y >= 1640) && (end.y <= 1670)) {
                LineInfo d46line = staff.getClosestStaffLine(end);
                StringBuilder d46sb = new StringBuilder();
                d46sb.append("DIAG46 lineFit id=").append(inter.getInfo().getId());
                d46sb.append(" end=").append(end);
                d46sb.append(" staff=").append(staff.getId());
                d46sb.append(" lineBounds=").append(d46line.getBounds());
                d46sb.append(" thickness=").append(d46line.getThickness());
                d46sb.append(" yAtDbl(end.x)=").append(d46line.yAt((double) end.x));
                d46sb.append(" yAtDbl1284=").append(d46line.yAt(1284.0));
                d46sb.append(" yAtDbl1290=").append(d46line.yAt(1290.0));
                d46sb.append(" yAtDbl1300=").append(d46line.yAt(1300.0));
                d46sb.append(" yAtDbl1340=").append(d46line.yAt(1340.0));
                d46sb.append(" yAtDbl1348=").append(d46line.yAt(1348.0));
                d46sb.append(" defPts=[");
                boolean d46first = true;
                for (Point2D d46p : ((org.audiveris.omr.sheet.StaffLine) d46line).getPoints()) {
                    if ((d46p.getX() >= 1100) && (d46p.getX() <= 1500)) {
                        if (!d46first) {
                            d46sb.append(",");
                        }
                        d46first = false;
                        d46sb.append("(").append(d46p.getX()).append(",").append(d46p.getY()).append(")");
                    }
                }
                d46sb.append("]");
                System.out.println(d46sb.toString());
                List<Point> d46arc = slur.getSidePoints(reverse);
                StringBuilder d46ab = new StringBuilder();
                d46ab.append("DIAG46 arcPts id=").append(inter.getInfo().getId());
                d46ab.append(" end=").append(end);
                d46ab.append(" n=").append(d46arc.size());
                d46ab.append(" pts=[");
                for (int d46i = 0; d46i < d46arc.size(); d46i++) {
                    if (d46i > 0) {
                        d46ab.append(",");
                    }
                    Point d46q = d46arc.get(d46i);
                    d46ab.append("(").append(d46q.x).append(",").append(d46q.y).append(")");
                }
                d46ab.append("]");
                System.out.println(d46ab.toString());
            }
""")
write("org/audiveris/omr/sheet/curve/SlursBuilder.java", text)
print("  SlursBuilder DIAG46A (§40)")

text = read_out("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java")  # ROUND 44/45 output, not pristine src
text = sub(text, """        final Point pt = tuplet.getCenter();

        for (int idx1 = 0; idx1 < candidates.size(); idx1++) {
""", """        final Point pt = tuplet.getCenter();

        // DIAG46B (§40): for the P3 m10 tuplet sign only, dump the
        // ByEuclidean candidate order with each chord's bounds, center
        // and bounds-distance to the sign, print-only.
        boolean diag46 = (Math.abs(pt.x - 2067) <= 10) && (Math.abs(pt.y - 1970) <= 10);
        if (diag46) {
            StringBuilder d46sb = new StringBuilder();
            d46sb.append("DIAG46 filterList sign=").append(pt).append(" order=[");
            boolean d46first = true;
            for (AbstractChordInter d46ch : candidates) {
                if (!d46first) {
                    d46sb.append(",");
                }
                d46first = false;
                d46sb.append("#").append(d46ch.getId())
                        .append(":b=").append(d46ch.getBounds())
                        .append(":c=").append(d46ch.getCenter())
                        .append(":dSq=").append(GeoUtil.ptDistanceSq(d46ch.getBounds(), pt.x, pt.y));
            }
            d46sb.append("]");
            System.out.println(d46sb.toString());
        }

        for (int idx1 = 0; idx1 < candidates.size(); idx1++) {
""")
text = sub(text, """                if (GeoUtil.xOverlap(b1, b2) > 0) {
                    // Discard ch1 or ch2, based on y-distance
                    final Point p2 = ch2.getCenter();
                    final int d1 = Math.abs(p1.y - pt.y);
                    final int d2 = Math.abs(p2.y - pt.y);

                    if (d1 < d2) {
""", """                if (GeoUtil.xOverlap(b1, b2) > 0) {
                    // Discard ch1 or ch2, based on y-distance
                    final Point p2 = ch2.getCenter();
                    final int d1 = Math.abs(p1.y - pt.y);
                    final int d2 = Math.abs(p2.y - pt.y);

                    if (diag46) {
                        // DIAG46B (§40): pair comparison, print-only.
                        System.out.println("DIAG46 filterPair sign=" + pt
                                + " ch1=#" + ch1.getId() + " b1=" + b1 + " c1=" + p1 + " d1=" + d1
                                + " ch2=#" + ch2.getId() + " b2=" + b2 + " c2=" + p2 + " d2=" + d2
                                + " overlap=" + GeoUtil.xOverlap(b1, b2)
                                + " discard=#" + ((d1 < d2) ? ch2.getId() : ch1.getId()));
                    }

                    if (d1 < d2) {
""")
write("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java", text)
print("  TupletsBuilder DIAG46B (§40)")

# ============================================================ ROUND 47 (§41: DIAG47 chord member bounds)
# DIAG46B (§40) named the exact flipping pixel for Divergence B (P3 m10
# tuplet): the filter pair is a 89 = 89 tie decided by chord-bounds width
# (23 vs 21 -> right edge 1987 vs 1985), and head-chord bounds are
# systematically 1-2 px narrower on Wasm while rests are byte-identical.
# The rint fix changed neither the bounds nor the filter outcome, so the
# bounds-width source is still unproven. HeadChordInter.getBounds() is the
# union of the member heads' glyph bounds, plus the stem tail point
# (stemBox.x + stemBox.width/2, stemBox.y or bottom) when a stem exists —
# so the width difference must come from the head glyph bounds, the stem
# bounds, or the tail point. DIAG47 dumps, for every candidate chord of
# the (2067,1970) sign only, each member head (id, shape, glyph bounds),
# the stem (id, bounds, center) and the tail location, so the analyser
# can say which member sets each chord-bounds edge. All prints are
# print-only (same patched file both sides).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java")  # ROUND 44/45/46 output, not pristine src
text = sub(text, """            d46sb.append("]");
            System.out.println(d46sb.toString());
        }
""", """            d46sb.append("]");
            System.out.println(d46sb.toString());

            // DIAG47 (§41): member bounds for each candidate chord — which
            // member (head glyph bounds vs stem bounds vs tail point) sets
            // the chord-bounds left/right edges. Print-only.
            for (AbstractChordInter d47ch : candidates) {
                StringBuilder d47sb = new StringBuilder();
                d47sb.append("DIAG47 members sign=").append(pt);
                d47sb.append(" ch=#").append(d47ch.getId());
                d47sb.append(" cb=").append(d47ch.getBounds());
                d47sb.append(" heads=[");
                boolean d47first = true;
                for (org.audiveris.omr.sig.inter.Inter d47m : d47ch.getMembers()) {
                    if (!d47first) {
                        d47sb.append(",");
                    }
                    d47first = false;
                    d47sb.append("#").append(d47m.getId())
                            .append(":").append(d47m.getShape())
                            .append(":b=").append(d47m.getBounds());
                }
                d47sb.append("]");
                StemInter d47stem = d47ch.getStem();
                d47sb.append(" stem=");
                if (d47stem != null) {
                    d47sb.append("#").append(d47stem.getId())
                            .append(":b=").append(d47stem.getBounds())
                            .append(":c=").append(d47stem.getCenter());
                } else {
                    d47sb.append("none");
                }
                d47sb.append(" tail=").append(d47ch.getTailLocation());
                System.out.println(d47sb.toString());
            }
        }
""")
write("org/audiveris/omr/sheet/rhythm/TupletsBuilder.java", text)
print("  TupletsBuilder DIAG47 (§41)")

# ============================================================ ROUND 48 (§42: DIAG48 HeadHeadRelation SIGraph symptom)
# §26.12 identified the failing support class as HeadHeadRelation from the
# claim that SigReducer.java:326 is the only insertSupport call site — but
# that is wrong: there are THREE call sites (SigReducer.java:326 and
# ChordsBuilder.java:484 both pass HeadHeadRelation.class;
# BeamGroupInter.java:158 passes BeamBeamRelation.class). The Wasm ERROR
# log prints the class opaquely as javaClass@<id>, so which class fails
# is unproven. DIAG48 prints supportClass.getName() in insertSupport's
# catch, so the failing class is named on both sides. Print-only (same
# patched file both sides). SIGraph.java was never patched before, so
# copy_src is correct here (per §39.1, read_out is only for files an
# earlier round already patched).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sig/SIGraph.java")
text = sub(text, """        } catch (IllegalAccessException | NoSuchMethodException | InstantiationException
                | InvocationTargetException ex) {
            logger.error("Could not instantiate {} {}", supportClass, ex.toString(), ex);
        }""", """        } catch (IllegalAccessException | NoSuchMethodException | InstantiationException
                | InvocationTargetException ex) {
            // DIAG48 (§42): name the failing support class — the ERROR log
            // prints it opaquely as javaClass@<id> under TeaVM. Print-only.
            System.out.println("DIAG48 insertSupport FAIL class=" + supportClass.getName()
                    + " ex=" + ex.toString());
            logger.error("Could not instantiate {} {}", supportClass, ex.toString(), ex);
        }""")
write("org/audiveris/omr/sig/SIGraph.java", text)
print("  SIGraph DIAG48 (§42)")

# ============================================================ ROUND 50 (§44.2: DIAG50 time-signature grades, Widmung)
# Widmung's Wasm .musicxml reads 3/4 where desktop reads 3/2, and the
# rhythm step then caps every voice at 3/4 — 128 chords get no timeOffset
# and are skipped at export (the -122 pitched gap, exactly). Desktop
# grades the two candidates {3/2=0.952, 3/4=0.752} (TimeColumn DEBUG).
# DIAG50 mirrors the two DEBUG decision sites through System.out (the
# Wasm runner does not surface DEBUG), same patched files both sides:
# HeaderTimeBuilder evaluateGlyph (WHOLE + NUM/DEN evals per glyph) and
# TimeColumn checkConsistency (grades map + chosen value per system).
# Print-only. Neither file was patched before, so copy_src is correct
# (per §39.1). Tier-1 strip removes the prints (no scaffolding added).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java")
text = sub(text, """                if (halfShapes.contains(shape)) {
                    final double grade = Grades.intrinsicRatio * eval.grade;
                    logger.debug("   {} eval {} for glyph#{}", half, eval, glyph.getId());
""", """                if (halfShapes.contains(shape)) {
                    final double grade = Grades.intrinsicRatio * eval.grade;
                    logger.debug("   {} eval {} for glyph#{}", half, eval, glyph.getId());
                    // DIAG50 (§44.2): mirror the DEBUG eval line. Print-only.
                    System.out.println("DIAG50 timeEval half=" + half + " glyph#" + glyph.getId()
                            + " bounds=" + glyph.getBounds() + " eval=" + eval + " grade=" + grade);
""")
text = sub(text, """                if (wholeShapes.contains(shape)) {
                    final double grade = Grades.intrinsicRatio * eval.grade;
                    logger.debug("   WHOLE eval {} for glyph#{}", eval, glyph.getId());
""", """                if (wholeShapes.contains(shape)) {
                    final double grade = Grades.intrinsicRatio * eval.grade;
                    logger.debug("   WHOLE eval {} for glyph#{}", eval, glyph.getId());
                    // DIAG50 (§44.2): mirror the DEBUG eval line. Print-only.
                    System.out.println("DIAG50 timeEval half=WHOLE glyph#" + glyph.getId()
                            + " bounds=" + glyph.getBounds() + " eval=" + eval + " grade=" + grade);
""")
write("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java", text)
print("  HeaderTimeBuilder DIAG50 (§44.2)")

text = copy_src("org/audiveris/omr/sheet/time/TimeColumn.java")
text = sub(text, """        logger.debug("System#{} time sig grades {}", system.getId(), grades);
""", """        logger.debug("System#{} time sig grades {}", system.getId(), grades);
        // DIAG50 (§44.2): mirror the DEBUG grades map. Print-only.
        System.out.println("DIAG50 timeGrades system=" + system.getId() + " grades=" + grades);
""")
text = sub(text, """        logger.debug("System#{} TimeSignature: {}", system.getId(), timeValue);
""", """        logger.debug("System#{} TimeSignature: {}", system.getId(), timeValue);
        // DIAG50 (§44.2): mirror the DEBUG choice. Print-only.
        System.out.println("DIAG50 timeChoice system=" + system.getId() + " chosen=" + timeValue);
""")
write("org/audiveris/omr/sheet/time/TimeColumn.java", text)
print("  TimeColumn DIAG50 (§44.2)")

# DIAG50b (§44.2, same round): entry-level prints — the first DIAG50
# eval prints never fired on Wasm while the grades map still holds a
# 3/4, so distinguish "evaluateGlyph never called" from "called but no
# time shape". HeaderTimeBuilder was already patched above this run, so
# read_out (per §39.1), not copy_src.
text = read_out("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java")
text = sub(text, """        // Projection can help refine the abscissa range
        browseProjection();

        if (range.hasStart() && (range.getWidth() >= params.minTimeWidth)) {
""", """        // Projection can help refine the abscissa range
        browseProjection();

        // DIAG50 (§44.2): entry print — did the range open at all?
        System.out.println("DIAG50 timeFind staff=" + staff.getId()
                + " hasStart=" + range.hasStart()
                + " width=" + (range.hasStart() ? range.getWidth() : -1)
                + " minWidth=" + params.minTimeWidth);

        if (range.hasStart() && (range.getWidth() >= params.minTimeWidth)) {
""")
text = sub(text, """        new GlyphCluster(wholeAdapter, null).decompose();
        logger.debug(
                "Staff#{} WHOLE {} trials:{}",
                staff.getId(),
                Glyphs.ids("parts", parts),
                wholeAdapter.trials);
""", """        new GlyphCluster(wholeAdapter, null).decompose();
        logger.debug(
                "Staff#{} WHOLE {} trials:{}",
                staff.getId(),
                Glyphs.ids("parts", parts),
                wholeAdapter.trials);
        // DIAG50 (§44.2): mirror the DEBUG trials line. Print-only.
        System.out.println("DIAG50 timeTrials half=WHOLE staff=" + staff.getId()
                + " " + Glyphs.ids("parts", parts) + " trials=" + wholeAdapter.trials);
""")
text = sub(text, """        new GlyphCluster(adapter, null).decompose();
        logger.debug(
                "Staff#{} {} {} trials:{}",
                staff.getId(),
                half,
                Glyphs.ids("parts", parts),
                adapter.trials);
""", """        new GlyphCluster(adapter, null).decompose();
        logger.debug(
                "Staff#{} {} {} trials:{}",
                staff.getId(),
                half,
                Glyphs.ids("parts", parts),
                adapter.trials);
        // DIAG50 (§44.2): mirror the DEBUG trials line. Print-only.
        System.out.println("DIAG50 timeTrials half=" + half + " staff=" + staff.getId()
                + " " + Glyphs.ids("parts", parts) + " trials=" + adapter.trials);
""")
text = sub(text, """                    null);

            for (Evaluation eval : evals) {
                final Shape shape = eval.shape;

                if (halfShapes.contains(shape)) {
""", """                    null);

            // DIAG50 (§44.2): entry print — every classifier call, even
            // with no time shape in the results. Print-only.
            System.out.println("DIAG50 timeEvalCall half=" + half + " glyph#" + glyph.getId()
                    + " bounds=" + glyph.getBounds() + " evals=" + evals.length
                    + " top=" + ((evals.length == 0) ? "none" : evals[0].toString()));

            for (Evaluation eval : evals) {
                final Shape shape = eval.shape;

                if (halfShapes.contains(shape)) {
""")
text = sub(text, """                    null);

            for (Evaluation eval : evals) {
                final Shape shape = eval.shape;

                if (wholeShapes.contains(shape)) {
""", """                    null);

            // DIAG50 (§44.2): entry print — every classifier call, even
            // with no time shape in the results. Print-only.
            System.out.println("DIAG50 timeEvalCall half=WHOLE glyph#" + glyph.getId()
                    + " bounds=" + glyph.getBounds() + " evals=" + evals.length
                    + " top=" + ((evals.length == 0) ? "none" : evals[0].toString()));

            for (Evaluation eval : evals) {
                final Shape shape = eval.shape;

                if (wholeShapes.contains(shape)) {
""")
write("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java", text)
print("  HeaderTimeBuilder DIAG50b (§44.2)")

# DIAG50c (§44.2, same round): ROI + spaces — the Wasm range is width 61
# starting too far left (junk glyphs) vs desktop width 35 on the real
# time sig. This print says whether the ROI or the spaces differ.
text = read_out("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java")
text = sub(text, """    private void browseProjection ()
    {
        List<Space> spaces = getSpaces();
""", """    private void browseProjection ()
    {
        List<Space> spaces = getSpaces();

        // DIAG50 (§44.2): ROI + spaces — the range itself differs Wasm vs
        // desktop. Print-only.
        System.out.println("DIAG50 timeSpaces staff=" + staff.getId()
                + " roi=" + roi + " browseStart=" + range.browseStart
                + " spaces=" + spaces);
""")
write("org/audiveris/omr/sheet/time/HeaderTimeBuilder.java", text)
print("  HeaderTimeBuilder DIAG50c (§44.2)")

# ============================================================ ROUND 52 (§44.3: DIAG52 Wiegenlied pickup numbering)
# Wiegenlied: desktop numbers the pickup measure 0 (matching GT), Wasm
# numbers it 1, shifting every bar +1 (exact-pitch 95 vs 155; pitches
# correct). The writer only renders stack.getScoreId() / stack.isImplicit()
# (MxlWriter.processMeasure), so the decision lives in MeasureFixer.isPickup:
# first system + first stack + stackTermination < 0. stackTermination is
# null when the stack has no expected duration, i.e. no time signature.
# DIAG52 mirrors the pickup-decision inputs (expected/actual duration,
# termination, first-stack flag) and the assigned id + implicit flag through
# System.out (the Wasm runner does not surface DEBUG). MeasureFixer was
# patched by ROUND 22 (DIAG26), so read_out, not copy_src (per §39.1).
# Also keep DIAG26 (decision inputs: left/right, count, isMultiRest,
# actualDur, isEmpty) and DIAG50 (time grades + header time ROI) alive via
# TEAVM_KEEP_DIAG=26,50,52 — this round adds no prints to those files.
# Print-only. Tier-1 strip removes the prints (no scaffolding added).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/score/MeasureFixer.java")
text = sub(text, """            logger.debug(
                    "stackFinal:{}{}",
                    stackTermination,
                    (stackTermination != null) ? ("=" + stackTermination) : "");
""", """            logger.debug(
                    "stackFinal:{}{}",
                    stackTermination,
                    (stackTermination != null) ? ("=" + stackTermination) : "");

            // DIAG52 (§44.3): mirror the pickup-decision inputs. Print-only.
            System.out.println("DIAG52 stack sys=" + system.getIndexInPage()
                    + " pageId=" + stack.getPageId()
                    + " first=" + (stack == system.getFirstStack())
                    + " expected=" + stack.getExpectedDuration()
                    + " actual=" + stack.getActualDuration()
                    + " term=" + stackTermination);
""")
text = sub(text, """            // Inspect stack for repeat signs
            stack.computeRepeats();
""", """            // DIAG52 (§44.3): assigned id + implicit flag after the branch chain. Print-only.
            System.out.println("DIAG52 decision pageId=" + stack.getPageId()
                    + " id=" + stack.getIdValue()
                    + " implicit=" + stack.isImplicit());

            // Inspect stack for repeat signs
            stack.computeRepeats();
""")
write("org/audiveris/omr/score/MeasureFixer.java", text)
print("  MeasureFixer DIAG52 (§44.3)")

# ---------------------------------------------------------------- prune stale
# Delete any .java under OUT that no round wrote this run (see WRITTEN
# above): a removed round must not leave a stale patched file behind.
for _old in sorted(OUT.rglob("*.java")):
    _rel = str(_old.relative_to(OUT))
    if _rel not in WRITTEN:
        print(f"pruning stale patched file: {_rel}")
        _old.unlink()

# ============================================================ ROUND 53 (§45: DIAG51 flat-key KeyBuilder)
# Widmung (-4 flats) and Wiegenlied (-3 flats) lose the key signature on
# Wasm; 8/8 flat-key pages lose it, 7/7 sharp-key pages keep it (§44.3.6).
# The Wasm header projection DOES see the flat ink (DIAG50 timeSpaces are
# the white gaps between the flat glyphs), so the divergence is in
# KeyBuilder's own projection peaks or its peak-pattern logic, not the
# pixels it reads. DIAG51 prints the full ShapeBuilder.process chain per
# staff and shape (FLAT and SHARP builders both run): the hilo peak list,
# peaks after each stage (browse/merge/purge), the inferSignature inputs
# (meanShort vs minFlatDelta/maxSharpDelta, heading), the refineSignature
# outcome, the checkPeakDeltas dxs/mean/cutOver, computeStarts, and the
# final keyInter. Rejection paths (createPeak invalid / not stem-like /
# first-peak too late, checkSpace "no key signature", purgeLightPeaks
# discards, computeStarts heading) are printed at the point of rejection
# so a truncated chain names its own gate. Print-only. Tier-1 strip
# removes the prints (no scaffolding added). KeyBuilder was patched by
# ROUND 38 (DIAG39), so read_out, not copy_src (per §39.1).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/key/KeyBuilder.java")
text = sub(text, """        Collections.sort(hiloPeaks, Range.byMain);
        logger.debug("Staff#{} hilos: {}", getId(), hiloPeaks);
""", """        Collections.sort(hiloPeaks, Range.byMain);
        logger.debug("Staff#{} hilos: {}", getId(), hiloPeaks);

        // DIAG51 (§45): hilo peak list per staff. Print-only.
        System.out.println("DIAG51 hilos staff=" + getId() + " inHeader=" + inHeader + " " + hiloPeaks);
""")
text = sub(text, """            browseArea(hiloPeaks); // Pick up raw peaks before end of key area

            refineAreaStart();

            mergePeaks(); // Merge close peaks

            purgeLightPeaks(); // Discard some light peaks

            int signature = inferSignature(); // Infer signature from peaks

            signature = refineSignature(signature); // Check trailing and regular peaks spacing

            List<Integer> starts = computeStarts(signature); // Compute start for each key item
""", """            browseArea(hiloPeaks); // Pick up raw peaks before end of key area

            // DIAG51 (§45): peaks after browse + range. Print-only.
            System.out.println("DIAG51 browse staff=" + getId() + " shape=" + keyShape
                    + " peaks=" + peaks + " range=" + range.getStart() + "-" + range.getStop());

            refineAreaStart();

            mergePeaks(); // Merge close peaks

            // DIAG51 (§45): peaks after merge. Print-only.
            System.out.println("DIAG51 merged staff=" + getId() + " shape=" + keyShape
                    + " peaks=" + peaks);

            purgeLightPeaks(); // Discard some light peaks

            // DIAG51 (§45): peaks after light-purge. Print-only.
            System.out.println("DIAG51 purged staff=" + getId() + " shape=" + keyShape
                    + " peaks=" + peaks);

            int signature = inferSignature(); // Infer signature from peaks

            // DIAG51 (§45): inferred signature. Print-only.
            System.out.println("DIAG51 infer staff=" + getId() + " shape=" + keyShape
                    + " sig=" + signature + " peaks=" + peaks);

            signature = refineSignature(signature); // Check trailing and regular peaks spacing

            // DIAG51 (§45): refined signature. Print-only.
            System.out.println("DIAG51 refine staff=" + getId() + " shape=" + keyShape
                    + " sig=" + signature + " peaks=" + peaks + " range=" + range.getStart()
                    + "-" + range.getStop());

            List<Integer> starts = computeStarts(signature); // Compute start for each key item

            // DIAG51 (§45): slice starts (empty = no key). Print-only.
            System.out.println("DIAG51 starts staff=" + getId() + " shape=" + keyShape
                    + " starts=" + starts);
""")
text = sub(text, """                final double meanShort = sum / shorts;
""", """                final double meanShort = sum / shorts;

                // DIAG51 (§45): inferSignature decision inputs. Print-only.
                System.out.println("DIAG51 inferMean staff=" + getId() + " shape=" + keyShape
                        + " peakCount=" + peakCount + " meanDx=" + meanDx + " meanShort=" + meanShort
                        + " heading=" + heading + " minFlatDelta=" + params.minFlatDelta
                        + " maxSharpDelta=" + params.maxSharpDelta
                        + " maxFlatHeading=" + params.maxFlatHeading);
""")
text = sub(text, """            logger.debug(
                    "Staff#{} peak dxs:{} mean:{} maxPeakDx:{} cutOver:{}",
                    getId(),
                    dxs,
                    meanDx,
                    params.maxPeakDx,
                    max);
""", """            logger.debug(
                    "Staff#{} peak dxs:{} mean:{} maxPeakDx:{} cutOver:{}",
                    getId(),
                    dxs,
                    meanDx,
                    params.maxPeakDx,
                    max);

            // DIAG51 (§45): mirror the dxs/cutOver decision. Print-only.
            System.out.println("DIAG51 dxs staff=" + getId() + " shape=" + keyShape
                    + " dxs=" + Arrays.toString(dxs) + " mean=" + meanDx
                    + " maxPeakDx=" + params.maxPeakDx + " cutOver=" + max);
""")
text = sub(text, """                if (dx < minDx) {
                    logger.debug("Staff#{} light {}", getId(), peak);
                    it.remove();
                }
""", """                if (dx < minDx) {
                    logger.debug("Staff#{} light {}", getId(), peak);

                    // DIAG51 (§45): light-peak discard. Print-only.
                    System.out.println("DIAG51 light staff=" + getId() + " shape=" + keyShape
                            + " peak=" + peak + " area=" + peak.area + " quorum=" + quorum
                            + " dx=" + dx + " minDx=" + minDx);
                    it.remove();
                }
""")
text = sub(text, """            peaks.retainAll(sortedPeaks);
""", """            // DIAG51 (§45): purge quorum. Print-only.
            System.out.println("DIAG51 purgeQuorum staff=" + getId() + " shape=" + keyShape
                    + " quorum=" + quorum + " peakCount=" + peakCount);

            peaks.retainAll(sortedPeaks);
""")
text = sub(text, """            if ((height > params.maxPeakCumul) || (peak.getWidth() > params.maxPeakWidth)) {
                logger.debug("Invalid height or width for peak");
""", """            if ((height > params.maxPeakCumul) || (peak.getWidth() > params.maxPeakWidth)) {
                logger.debug("Invalid height or width for peak");

                // DIAG51 (§45): peak rejected on height/width. Print-only.
                System.out.println("DIAG51 badPeak staff=" + getId() + " shape=" + keyShape
                        + " peak=" + peak + " height=" + height + " maxPeakCumul="
                        + params.maxPeakCumul + " maxPeakWidth=" + params.maxPeakWidth);
""")
text = sub(text, """                    if (dx > params.maxPeakDx) {
                        // A large dx indicates we are beyond end of key signature
                        logger.debug("Too large delta since previous peak");
""", """                    if (dx > params.maxPeakDx) {
                        // A large dx indicates we are beyond end of key signature
                        logger.debug("Too large delta since previous peak");

                        // DIAG51 (§45): peak rejected on delta. Print-only.
                        System.out.println("DIAG51 bigDx staff=" + getId() + " shape=" + keyShape
                                + " peak=" + peak + " dx=" + dx + " maxPeakDx=" + params.maxPeakDx);
""")
text = sub(text, """                    if (offset > params.maxFirstPeakOffset) {
                        logger.debug("First peak arrives too late");
""", """                    if (offset > params.maxFirstPeakOffset) {
                        logger.debug("First peak arrives too late");

                        // DIAG51 (§45): first peak rejected on offset. Print-only.
                        System.out.println("DIAG51 lateFirst staff=" + getId() + " shape=" + keyShape
                                + " peak=" + peak + " offset=" + offset + " maxFirstPeakOffset="
                                + params.maxFirstPeakOffset);
""")
text = sub(text, """            if (!stem) {
                logger.debug("Staff#{} {} no stem", getId(), peak);
            }
""", """            if (!stem) {
                logger.debug("Staff#{} {} no stem", getId(), peak);

                // DIAG51 (§45): peak ignored, not stem-like. Print-only.
                System.out.println("DIAG51 noStem staff=" + getId() + " shape=" + keyShape
                        + " peak=" + peak);
            }
""")
text = sub(text, """                if (spaceWidth > params.maxFirstSpaceWidth) {
                    // No key signature!
                    logger.debug("Staff#{} no key signature.", getId());
                    keepOn = false;
""", """                if (spaceWidth > params.maxFirstSpaceWidth) {
                    // No key signature!
                    logger.debug("Staff#{} no key signature.", getId());

                    // DIAG51 (§45): first space too wide, no key. Print-only.
                    System.out.println("DIAG51 noKey staff=" + getId() + " shape=" + keyShape
                            + " space=" + spaceStart + "-" + spaceStop + " width=" + spaceWidth
                            + " maxFirstSpaceWidth=" + params.maxFirstSpaceWidth);
                    keepOn = false;
""")
text = sub(text, """            } else if (spaceWidth > params.maxInnerSpace) {
                range.shrinkStop(spaceStart - 1);
                keepOn = false;
            }
""", """            } else if (spaceWidth > params.maxInnerSpace) {
                // DIAG51 (§45): inner space too wide, key ends here. Print-only.
                System.out.println("DIAG51 wideSpace staff=" + getId() + " shape=" + keyShape
                        + " space=" + spaceStart + "-" + spaceStop + " width=" + spaceWidth
                        + " maxInnerSpace=" + params.maxInnerSpace);
                range.shrinkStop(spaceStart - 1);
                keepOn = false;
            }
""")
text = sub(text, """                if (trail < params.minFlatTrail) {
                    logger.debug("Removing too narrow flat");
""", """                if (trail < params.minFlatTrail) {
                    logger.debug("Removing too narrow flat");

                    // DIAG51 (§45): last flat removed, trail too narrow. Print-only.
                    System.out.println("DIAG51 narrowFlat staff=" + getId() + " shape=" + keyShape
                            + " trail=" + trail + " minFlatTrail=" + params.minFlatTrail);
""")
text = sub(text, """                } else {
                    logger.debug("Too large heading {} before first flat peak", flatHeading);
                }
""", """                } else {
                    logger.debug("Too large heading {} before first flat peak", flatHeading);

                    // DIAG51 (§45): flat heading too large, no starts. Print-only.
                    System.out.println("DIAG51 bigHeading staff=" + getId() + " shape=" + keyShape
                            + " flatHeading=" + flatHeading + " maxFlatHeading="
                            + params.maxFlatHeading);
                }
""")
text = sub(text, """                staff.getHeader().key = keyInter;
                roi.freezeAlters();
""", """                staff.getHeader().key = keyInter;
                roi.freezeAlters();

                // DIAG51 (§45): final key outcome for this staff/shape. Print-only.
                System.out.println("DIAG51 final staff=" + getId() + " shape=" + keyShape
                        + " keyInter=" + ((keyInter == null) ? "null" : keyInter.getFifths())
                        + " roiSize=" + roi.size());
""")
write("org/audiveris/omr/sheet/key/KeyBuilder.java", text)
print("  KeyBuilder DIAG51 (§45)")

# ============================================================ ROUND 54 (§45: DIAG51b — checkWithClefs gate)
# DIAG51 (ROUND 53) proved the whole ShapeBuilder.process chain is
# identical desktop vs Wasm (hilos, peaks, infer, dxs, starts) and the
# ONLY difference is the DIAG51 final line: desktop emits it (one per
# system, FLAT, keyInter=-4/-3), Wasm emits zero. So getBestKeyInter()
# returns null on Wasm: both ShapeBuilders' keyInter are null. keyInter
# is only created in checkWithClefs() (after a compatible clef with
# alterCount > 0), so the gate is there or in the alter retrieval just
# before it. DIAG51b prints: per-slice alter state after
# retrieveComponents, the competing clefs, per-clef alterCount, the
# computePitchedGrades dPitch gate (one out-of-tolerance alter returns 0
# for the whole key), the checkWithClefs outcome, and the createKeyInter
# alters count. Same DIAG51 number so TEAVM_KEEP_DIAG=51 keeps them.
# Print-only. KeyBuilder was patched by ROUNDs 38/53, so read_out.
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/key/KeyBuilder.java")
text = sub(text, """                extractor.retrieveComponents(range, roi, peaks, keyShape);
""", """                extractor.retrieveComponents(range, roi, peaks, keyShape);

                // DIAG51 (§45): per-slice alter state after component retrieval. Print-only.
                {
                    StringBuilder sb51 = new StringBuilder();
                    sb51.append("DIAG51 alters staff=").append(getId()).append(" shape=").append(keyShape);
                    for (KeySlice slice51 : roi) {
                        KeyAlterInter alt51 = slice51.getAlter();
                        sb51.append(" [slice#").append(slice51.getId());
                        if (alt51 == null) {
                            sb51.append(" alter=null");
                        } else {
                            sb51.append(" grade=").append(String.format("%.3f", alt51.getGrade()))
                                    .append(" pitch=").append(String.format("%.1f", alt51.getMeasuredPitch()));
                        }
                        sb51.append("]");
                    }
                    System.out.println(sb51.toString());
                }
""")
text = sub(text, """                clefs.addAll(staff.getCompetingClefs(starts.get(0)));
""", """                clefs.addAll(staff.getCompetingClefs(starts.get(0)));

                // DIAG51 (§45): competing clefs. Print-only.
                {
                    StringBuilder sb51 = new StringBuilder();
                    sb51.append("DIAG51 clefs staff=").append(getId()).append(" shape=").append(keyShape)
                            .append(" n=").append(clefs.size());
                    for (ClefInter c51 : clefs) {
                        sb51.append(" [").append(c51.getKind()).append(" grade=")
                                .append(String.format("%.3f", c51.getGrade())).append("]");
                    }
                    System.out.println(sb51.toString());
                }
""")
text = sub(text, """                    final double[] pitchedGrades = new double[roi.size()];
                    final int alterCount = computePitchedGrades(clefKind, pitchedGrades);
""", """                    final double[] pitchedGrades = new double[roi.size()];
                    final int alterCount = computePitchedGrades(clefKind, pitchedGrades);

                    // DIAG51 (§45): per-clef pitched-grade outcome. Print-only.
                    System.out.println("DIAG51 pitched staff=" + getId() + " shape=" + keyShape
                            + " clef=" + clefKind + " alterCount=" + alterCount
                            + " grades=" + Arrays.toString(pitchedGrades));
""")
text = sub(text, """                    if (dPitch > maxDeltaPitch) {
                        logger.debug(
                                "Staff#{} slice#{} invalid {} pitch {} vs {} for {}",
""", """                    if (dPitch > maxDeltaPitch) {
                        // DIAG51 (§45): one out-of-tolerance alter zeroes the key. Print-only.
                        System.out.println("DIAG51 badPitch staff=" + getId() + " shape=" + keyShape
                                + " slice#" + slice.getId() + " alterPitch=" + alterPitch
                                + " expected=" + clefPitches[i] + " dPitch=" + dPitch
                                + " maxDeltaPitch=" + maxDeltaPitch);
                        logger.debug(
                                "Staff#{} slice#{} invalid {} pitch {} vs {} for {}",
""")
text = sub(text, """            if ((bestCompatibleClef == null) || (bestCompatibleClef != bestClef)) {
                roi.stuffSlicesFrom(0);

                return false;
            } else {
                return true;
            }
""", """            // DIAG51 (§45): checkWithClefs outcome. Print-only.
            System.out.println("DIAG51 checkClefs staff=" + getId() + " shape=" + keyShape
                    + " bestCompat=" + ((bestCompatibleClef == null) ? "null" : bestCompatibleClef.getKind())
                    + " best=" + ((bestClef == null) ? "null" : bestClef.getKind())
                    + " keyInter=" + ((keyInter == null) ? "null" : keyInter.getFifths()));

            if ((bestCompatibleClef == null) || (bestCompatibleClef != bestClef)) {
                roi.stuffSlicesFrom(0);

                return false;
            } else {
                return true;
            }
""")
text = sub(text, """            if (alters.isEmpty()) {
                return;
            }
""", """            // DIAG51 (§45): createKeyInter gate. Print-only.
            System.out.println("DIAG51 createKey staff=" + getId() + " shape=" + keyShape
                    + " alters=" + alters.size() + " roiSize=" + roi.size());

            if (alters.isEmpty()) {
                return;
            }
""")
write("org/audiveris/omr/sheet/key/KeyBuilder.java", text)
print("  KeyBuilder DIAG51b (§45)")

# ============================================================ ROUND 55 (§45: DIAG51c — flat pitch components)
# DIAG51b localised the loss exactly: every flat alter's measured pitch
# is +16.0 on Wasm (Widmung staff 1: desktop -0.1/-3.1/0.9/-2.1, Wasm
# 15.9/12.8/16.9/13.9; grades identical), so computePitchedGrades returns
# 0 on the first slice (dPitch ~15.9 > maxDeltaPitch 2.0/1.5), no
# compatible clef, no keyInter, no finalizeKey. Sharps work, so
# staff.pitchPositionOf itself is correct; the flat-only inputs are
# flatMassPitchOffset (Constant.Double 0.65) and getAreaPitchOffset(FLAT)
# (from populatePitchOffsets font-layout metrics). DIAG51c prints both:
# the populatePitchOffsets inputs (staffHeight/lineHeight/pitchHeight and
# the FLAT rect/offset) and the computePitch components per alter
# (centroid, center, raw pitchPositionOf values, both offsets, massPitch,
# geoPitch, mix), plus the sharp-path massPitch as a control. Print-only.
# Two NEW patched files (copy_src; neither was patched before).
# ---------------------------------------------------------------------------
text = copy_src("org/audiveris/omr/sig/inter/AbstractPitchedInter.java")
text = sub(text, """        // Retrieve pitch height from 5-line and 1-line symbols
        final double staffHeight = font.layout(MusicFont.getString(BravuraSymbols.STAFF_CODE))
                .getBounds().getHeight();
        final double lineHeight = font.layout(MusicFont.getString(BravuraSymbols.LINE_CODE))
                .getBounds().getHeight();
        final double pitchHeight = (staffHeight - lineHeight) / 8; // 4 interlines = 8 pitches
""", """        // Retrieve pitch height from 5-line and 1-line symbols
        final double staffHeight = font.layout(MusicFont.getString(BravuraSymbols.STAFF_CODE))
                .getBounds().getHeight();
        final double lineHeight = font.layout(MusicFont.getString(BravuraSymbols.LINE_CODE))
                .getBounds().getHeight();
        final double pitchHeight = (staffHeight - lineHeight) / 8; // 4 interlines = 8 pitches

        // DIAG51 (§45): pitch-offset scale inputs. Print-only.
        System.out.println("DIAG51 pitchScale staffHeight=" + staffHeight + " lineHeight=" + lineHeight
                + " pitchHeight=" + pitchHeight);
""")
text = sub(text, """                .forEach(s -> {
                    final TextLayout layout = font.layoutShapeByCode(s);
                    final Rectangle2D rect = layout.getBounds();
                    final double offset = (-rect.getY() - rect.getHeight() / 2) / pitchHeight;
                    pitchOffsets.put(s, offset);
                });
""", """                .forEach(s -> {
                    final TextLayout layout = font.layoutShapeByCode(s);
                    final Rectangle2D rect = layout.getBounds();
                    final double offset = (-rect.getY() - rect.getHeight() / 2) / pitchHeight;

                    // DIAG51 (§45): per-shape pitch offset. Print-only.
                    System.out.println("DIAG51 pitchOffset shape=" + s + " rect=" + rect
                            + " offset=" + offset);
                    pitchOffsets.put(s, offset);
                });
""")
write("org/audiveris/omr/sig/inter/AbstractPitchedInter.java", text)
print("  AbstractPitchedInter DIAG51c (§45)")

text = copy_src("org/audiveris/omr/sig/inter/AlterInter.java")
text = sub(text, """            // Average value of both heuristics
            double mix = 0.5 * (massPitch + geoPitch);
""", """            // Average value of both heuristics
            double mix = 0.5 * (massPitch + geoPitch);

            // DIAG51 (§45): flat pitch components. Print-only.
            System.out.println("DIAG51 flatPitch glyph=" + glyph.getId() + " shape=" + shape
                    + " centroid=" + centroid + " center=" + center
                    + " ppCentroid=" + staff.pitchPositionOf(centroid)
                    + " flatOffset=" + constants.flatMassPitchOffset.getValue()
                    + " massPitch=" + massPitch
                    + " ppCenter=" + staff.pitchPositionOf(center)
                    + " areaOffset=" + getAreaPitchOffset(Shape.FLAT)
                    + " geoPitch=" + geoPitch + " mix=" + mix);
""")
text = sub(text, """        } else {
            return new Pitches((int) Math.rint(massPitch), massPitch);
        }
""", """        } else {
            // DIAG51 (§45): non-flat pitch control. Print-only.
            System.out.println("DIAG51 sharpPitch glyph=" + glyph.getId() + " shape=" + shape
                    + " centroid=" + centroid + " massPitch=" + massPitch);
            return new Pitches((int) Math.rint(massPitch), massPitch);
        }
""")
write("org/audiveris/omr/sig/inter/AlterInter.java", text)
print("  AlterInter DIAG51c (§45)")

# ============================================================ ROUND 56 (§45: DIAG51 print NPE fix)
# The DIAG51 browse/refine prints (ROUND 53) call range.getStart()
# unconditionally. StaffHeader.Range.getStart() auto-unboxes the
# nullable Integer start — null when no peaks were found (empty hilos),
# so the print itself throws NPE. Found on the two Fauré organ pages
# (23 staves, 1 system): staff 1 has empty hilos, Wasm died with
# "dereferencing a null pointer" right after the hilos print, and the
# desktop harness died identically (NPE at StaffHeader.java:237 via
# KeyBuilder.java:2247) — proving it is the diagnostic print, not a
# TeaVM defect and not the BravuraMetrics fix. Stock code never calls
# getStart() on an unpopulated range, so the fix is print-only:
# guard with hasStart(). KeyBuilder was patched by ROUND 53, so
# read_out, not copy_src (per §39.1).
# ---------------------------------------------------------------------------
text = read_out("org/audiveris/omr/sheet/key/KeyBuilder.java")
text = sub(text, """            System.out.println("DIAG51 browse staff=" + getId() + " shape=" + keyShape
                    + " peaks=" + peaks + " range=" + range.getStart() + "-" + range.getStop());""",
"""            System.out.println("DIAG51 browse staff=" + getId() + " shape=" + keyShape
                    + " peaks=" + peaks + " range=" + (range.hasStart() ? range.getStart() : -1)
                    + "-" + range.getStop());""")
text = sub(text, """            System.out.println("DIAG51 refine staff=" + getId() + " shape=" + keyShape
                    + " sig=" + signature + " peaks=" + peaks + " range=" + range.getStart()
                    + "-" + range.getStop());""",
"""            System.out.println("DIAG51 refine staff=" + getId() + " shape=" + keyShape
                    + " sig=" + signature + " peaks=" + peaks + " range="
                    + (range.hasStart() ? range.getStart() : -1)
                    + "-" + range.getStop());""")
write("org/audiveris/omr/sheet/key/KeyBuilder.java", text)
print("  KeyBuilder DIAG51 null-safe range prints (§45)")

# ============================================================ ROUND 49 (§43: clean build)
# Strip ALL DIAG prints (DIAG14 through DIAG48) from the freshly
# generated patched sources. The DIAG prints were left in deliberately
# through §42 for re-verifiability; the clean build removes them.
# Implementation lives in patched/strip_diag.py (two tiers: a generic
# System.out print removal plus targeted scaffolding removal, each
# removal asserting its expected count so a future change to DIAG code
# fails loudly here instead of silently leaving dead code or silently
# removing live code). Real fixes are untouched: the ROUND fixes, shim
# fixes, classlib patches, MxlWriter, pre-rendered templates/classifier/
# metrics, policy entries, indentations=false. Kept deliberately:
#   * diag45lineY/diag45toLine in SlursBuilder (the purge gate reads them)
#   * DIAG mentions inside // comments (documentation of why a fix exists)
#   * stock Audiveris prints and TeavmMain's operational progress prints
#     (entry/src, not touched by this script)
# A future diagnostic ROUND must be inserted BEFORE this section, or its
# prints will be stripped too. If a future ROUND changes DIAG code,
# update strip_diag.py first — the strip fails loudly on a mismatch.
# Diagnostic builds (§44.2): set TEAVM_KEEP_DIAG=<n> to keep one DIAG
# number's prints through the strip (e.g. TEAVM_KEEP_DIAG=50); default
# strips everything.
import strip_diag
strip_diag.strip_tree(OUT)
print("  ROUND 49 strip (§43 clean build)")
