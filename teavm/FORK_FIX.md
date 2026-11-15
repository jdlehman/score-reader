# TeaVM fork fix — TPoint extends Point2D, TDimension extends Dimension2D

Date: 2026-11-08. TeaVM 0.16.0, Node v24.22.1, Java 25 (jdk-25.0.5+8),
Audiveris 5.11, headless entry point `teavm.TeavmMain`.

## Verdict: DONE at §47 — DIAG55 hymnal −28 split, measured (2026-11-11). The −28 (batch 125 pitched vs Wasm 97) is fully split with ZERO Wasm-side loss: 22 template-driven (stock-template harness SYMBOLS-END 119 vs pre-rendered 97, same gray, same harness) + 6 gray-conversion (batch 125 pitched vs stock-harness 119 heads; batch gray is max-RGB, harness/Wasm gray is PIL-L luma — all 2,338,180 px differ, max 22 levels; GRID already diverges: 4 vs 2 spurious clusters destroyed). Wasm == pre-rendered desktop harness at every measured step (HEADS 572, REDUCTION/MEASURES/CHORDS/CURVES/SYMBOLS 97, identical checksums and COLUMN dumps to full float precision). The loss HEADS→REDUCTION sits inside STEMS on both sides. The 2 barline deletions are template-driven too (GRID-END has both barlines on all sides; pre-rendered COLUMN drops S2 x≈878 s4 and S3 x≈340 s5 on both desktop and Wasm; stock keeps groups=2, 13 raw measures = batch). The harness TEXTS crash is solved: no inter — it was the ROUND 20 DIAG24 dead block (hard-coded ROI x 1854..1929 on a 1196-wide page) at SheetScanner.getCleanImage:143; removed (stock-restoring), harness now passes TEXTS on the hymnal both template variants. Contained fix applied as the §47 round; clean build full-out113 verified byte-identical (hymnal + 3 controls) and is the new current clean build (full-out112 diagnostic-only, DIAG54+55 kept). §46 in one line: Wasm right on Cantique p13/p01 — desktop harness, not batch .mxl, is the authoritative comparator. Still open: DIAG53 (BWV p14 +2), real-browser Chrome run, upstream filings (#272, #21244, §11, §19 TColor, §27 hypot, §33 retainAll, §35 TFormatter, §40 rint/round), BrowserOCR follow-up, photometric recovery, multi-file export N>1, Lindenbaum batch-vs-harness gap, Beethoven typeset p165, StackRhythm wobbles, Beethoven p229 wall time (profiled §46.5). CheerpJ 5 remains the only working option.

- The #272 defect is **fixed**: the minimal repro now loads in Node and runs
  with correct results, and the full TeavmMain module compiles with
  **0 problems** and no longer fails at function #272.
- The full module **still does not load**. The evening continuation (§7)
  fixed three further masked failures — #3027 (Font shim), #18066
  (TimeoutException shim), #19489 (FontFormatException shim) — and then hit
  **#21244, a genuine TeaVM WasmGC async-codegen defect** (a suspension
  continuation block declares a non-nullable result type for a value that is
  nullable on the fallthrough path). No shim/classlib fix applies, per-site
  Audiveris rewrites are ruled out, and the iteration was stopped there
  per the task's stop rule. Step 4c (run TeavmMain on hymn-satb.png) was
  therefore **not reached**: no WasmGC timing and no HEADS result exist yet.

## 1. Source

TeaVM source cloned 2026-11-08 into `teavm-fork/src/`:

- Repo: https://github.com/konsoletyper/teavm.git
- Tag: `0.16.0`, commit `e87d452e4bd70c77b9e19314a46c3d6971c148b6`
  (2026-10-02, "js: improve performance of char array to string conversion
  for short strings"), shallow clone (`--depth 1 --branch 0.16.0`).
- Only two files modified (see §2); `git status` in `src/` shows exactly
  those two. Patch: `teavm-classlib-fix.patch` (210 lines, `git diff`).

## 2. The classlib changes

How the substitution works (for the next person): TeaVM maps
`java.awt.Point` → `org.teavm.classlib.java.awt.TPoint` via
`ClasslibSubstitutionPolicy` (package prefix `org.teavm.classlib.`,
simple-name prefix `T`). There is **no** `TPoint2D` / `TDimension2D` in
the classlib — `java.awt.geom.*` is not provided by TeaVM at all, so in
this spike those classes come from the user's `shims.jar`. The fix below
therefore makes `TPoint` extend the *shim* `Point2D` (via substitution
fallback: no `TPoint2D` exists, so the program's own `Point2D` is used).

### `classlib/src/main/java/org/teavm/classlib/java/awt/TPoint.java`

Was: `public class TPoint { public int x; public int y; TPoint(int,int); }`
— superclass `java.lang.Object`, no `getX`/`getY`.

Now: `public class TPoint extends java.awt.geom.Point2D`, mirroring
`java.awt.Point` (JDK 25):

- ctors: `TPoint()`, `TPoint(int, int)`, `TPoint(Point)` (copy);
- implements the three abstract `Point2D` methods: `getX()`, `getY()`,
  `setLocation(double, double)` (JDK rounding: `(int) Math.floor(x + 0.5)`);
- plus `getLocation()`, `setLocation(int, int)`, `setLocation(Point)`,
  `move(int, int)`, `translate(int, int)`, `equals(Object)`
  (JDK behaviour, including the `super.equals(obj)` fallback),
  `toString()`; `hashCode()` is inherited from `Point2D`.

### `classlib/src/main/java/org/teavm/classlib/java/awt/TDimension.java`

Was: `public class TDimension { public int width; public int height;
TDimension(int,int); }` — superclass `Object`.

Now: `public class TDimension extends java.awt.geom.Dimension2D`,
mirroring `java.awt.Dimension` (JDK 25):

- ctors: `TDimension()`, `TDimension(int, int)`,
  `TDimension(Dimension)` (copy ctor — was missing);
- implements the three abstract `Dimension2D` methods: `getWidth()`,
  `getHeight()`, `setSize(double, double)` (JDK rounding:
  `(int) Math.ceil(...)`);
- plus `getSize()`, `setSize(Dimension)`, `setSize(int, int)`,
  `equals(Object)`, `hashCode()`, `toString()` (JDK formulae).

This is **not** a clean 2-line change: the parent classes are abstract,
so each subclass must implement their abstract methods, and restoring
the JDK API surface (ctors, `move`/`translate`, copy ctor) is part of
making the emulation faithful. It is still a small, contained change:
2 files, +174/−2 lines. No other TeaVM source was touched.

### Upstreamability

The fix as written is **not directly upstreamable as-is**, because in a
vanilla TeaVM program there is no `java.awt.geom.Point2D` at all, so
`TPoint extends Point2D` would leave `TPoint` with a missing superclass.
The proper upstream fix is: add classlib
`org.teavm.classlib.java.awt.geom.TPoint2D` (with nested `Double`/`Float`,
as real `Point2D` has) and `TDimension2D`, and make `TPoint`/`TDimension`
extend those. That is a larger change and was **not** attempted here —
this fork proves the *mechanism* (restoring the hierarchy fixes the
invalid module), not the upstream patch shape. The issue draft in
`../teavm/ISSUE_272_DRAFT.md` should be updated to say this before
filing: suggested fix is `TPoint extend Point2D` *with a new classlib
`TPoint2D`*, likewise for `TDimension`.

Checkstyle: the repo's `config/checkstyle/checkstyle.xml` caps lines at
120 chars; both new files were checked and have no line over 120.
`checkstyleMain` itself was not run (Gradle does not work in this VM —
see §3).

## 3. Build — Gradle does NOT work in this VM; direct javac build used

### Gradle: attempted, failed (three distinct failures)

JDK 25 at `~/workspace/score-reader-spikes/repo/.work/jdk/jdk-25.0.5+8/bin`.
Gradle 9.7.1 (wrapper `gradle/wrapper/gradle-wrapper.properties`).
`GRADLE_USER_HOME` was set to `teavm-fork/gradle-home`; proxy system
properties were passed via `GRADLE_OPTS` constructed at runtime from the
ambient egress-proxy env var (never written to disk or printed).

1. **Wrapper download fails** (`gradle-classlib.log`): the `gradlew`
   downloader (Java `HttpURLConnection`) fails the proxy CONNECT tunnel
   with `java.util.NoSuchElementException` at
   `HttpURLConnection.doTunneling0` — it cannot handle this egress proxy.
2. **Workaround**: Gradle 9.7.1 was downloaded with `curl -L`
   (`gradle-9.7.1-bin.zip`, 151,433,392 bytes, kept in this folder) and
   run directly; `gradle --version` works.
3. **Client→daemon dispatch fails** (`gradle-classlib2/3/4.log`): the
   daemon JVM starts and listens on `127.0.0.1` (see
   `gradle-home/daemon/9.7.1/daemon-*.out.log`), but every build fails
   in ~4 s with `Could not dispatch a message to the daemon`, root cause
   (`--stacktrace`, `gradle-classlib4.log`):
   `java.io.IOException: Connection reset by peer` writing to
   `127.0.0.1:<port>`. Retried three times, including with
   `-Dorg.gradle.jvmargs=-Xmx384m` (one attempt was cut short by my own
   `pkill -f GradleDaemon` matching its own shell — that run produced no
   log and is not counted as a Gradle result). The daemon's VM shutdown
   hook runs ~30 s after start. Conclusion: **Gradle's daemon model
   (loopback TCP client↔daemon) does not work in this VM**; the daemon
   starts but the connection is reset. This is an environment limitation,
   not a TeaVM source problem.

### Direct source build (what was actually used)

The classlib module was built from the forked source with `javac`
(`direct/`; commands in `direct/javac.log`):

```
javac -J-Xmx1g -nowarn -cp <stock teavm-core, platform, jso*, metaprogramming*,
  interop, extension-spi*, jzlib, joda-time 0.16.0 jars> \
  -d direct/classes  <all 1057 files under src/classlib/src/main/java>
```

Result: **exit 0, 1,510 classes**, one pre-existing warning only
(`finalize()` deprecation in `TObject.java:572`).

The two Gradle `jar`-task generator steps were run by hand with the same
mains and arguments as `classlib/build.gradle.kts`, and their outputs
are **byte-identical to the stock 0.16.0 jar**:

- `org.teavm.classlib.impl.tz.TimeZoneCache` → `impl/tz/cache`
  (first attempt failed: the tzdata zip resource must be on the
  classpath — fixed by adding `src/classlib/src/main/resources`;
  second attempt also needed the output to be the *file* `.../tz/cache`,
  not a directory);
- `org.teavm.classlib.impl.currency.CurrenciesGenerator
  src/main/data/iso4217.xml` → `impl/currency/iso4217.bin`.

Jar assembly (`direct/jar.log`): copy of the stock
`teavm-classlib-0.16.0.jar` with **all 1,510 `.class` entries replaced**
by the freshly compiled ones and the two generated files refreshed.
Result: `lib-fork/teavm-classlib-0.16.0.jar` (17,445,120 bytes).
All 1,510 classfiles differ byte-wise from stock (different compiler:
JDK 25 javac vs the stock build's compiler — expected for a rebuild),
class count identical (1,510 = 1,510). Verified with `javap`:
`TPoint extends java.awt.geom.Point2D`, `TDimension extends
java.awt.geom.Dimension2D`, with the new methods listed.

`lib-fork/` also holds copies of the other stock 0.16.0 jars
(core/interop/jso*/metaprogramming*/platform, asm/hppc/joda-time/jzlib/
rhino) — only the classlib is fork-built; the rest are stock.

A **smoke-test jar** was built first (`smoke/`): the two new classes
compiled standalone and patched into a copy of the stock classlib jar.
Both the smoke jar and the full source-built jar pass the repro (§4a)
identically, so the fix is validated at the classfile level *and* as a
full source build.

## 4. Tests

### 4a. Minimal repro — PASSES

`../teavm/fn272/repro/Repro.java` (`area.contains(p)` with a `Point`,
plus the `Point2D p2d = p` assignment form), compiled with `Spike`
(TeaVMTool, WasmGC, SIMPLE) against the fork classlib:

- Stock 0.16.0 (from `FN272_DIAGNOSIS.md`):
  `Compiling function #197 failed: call_ref[1] expected type
  (ref null 22), found local.get of type (ref null 90)`.
- **Fork, smoke jar** (`repro-out/`, 99 classes, 1,135 methods):
  `REPRO: LOADED OK`.
- **Fork, source-built jar** (`repro-out2/`, 99 classes, 1,135 methods):
  `SOURCE-BUILT REPRO: LOADED OK`.
- Running it in Node (`run-repro.mjs`, `runtime.mjs` copied from
  `teavm-core` as in the original spike):
  ```
  direct: false
  via Point2D local: false
  main() returned
  ```
  Correct: the shim `Area()` is empty, so `contains(3, 4)` is false on
  desktop too; both the direct call and the `Point2D`-local form agree.
- Control `ReproFixed` (`area.contains(p.x, p.y)`, `repro-out-fixed/`):
  still `LOADED OK` — no regression.

### 4b. Full headless TeavmMain — compiles, does NOT load (new failure #3027)

Clean tree first: `teavm/build.sh` was re-run (`build-clean.log`,
BUILD OK, 261 patched classes). That reverted 5 of the 10 per-site
#272 workaround fixes (AbstractInter, CurvesBuilder, SlurLinker,
WedgesBuilder, ShapeSymbol). The other 5 (LedgerInter,
AbstractHorizontalInter, SIGraph, Staff, ObjectEditor) survived because
`make_patches.py` does not regenerate those copied-in files — the
`FN272_DIAGNOSIS.md` claim that `build.sh` wipes the workaround is
**wrong for the copied-in files**. They were reverted by hand (exact
reverse of `fn272/apply_272_workaround.py`'s strings) and verified
identical to the repo originals ignoring CR line endings (the copies
were LF-normalised when the workaround script rewrote them). The one
remaining `Point2D.Double(...)` use in the tree,
`NumberInter.java:391`, is original Audiveris code, not a workaround.
`ShapeSymbol.java`'s remaining diff vs the repo original is the
legitimate TEAVM patch (`Color.MAGENTA`/`BLUE`/`getRGB` → manual
equivalents), not a workaround.

Compile (`full-build.log`, ~56 s):

```
INFO: Output file successfully built
INFO: Classes compiled: 2864
INFO: Methods compiled: 27690
generated: [teavm-fork/full-out/classes.wasm]   (10,202,825 bytes)
```

0 problems. (Stock: 2,863 classes / 27,661 methods / 10,190,425 bytes;
the +1 class / +29 methods are the new `TPoint`/`TDimension` members
and the classes they pull in.)

Load test in Node:

```
FULL MODULE: COMPILE ERROR: WebAssembly.compile(): Compiling function #3027 failed:
call[1] expected type i32, found block of type f32 @+1947593
```

### 4c. Run on hymn-satb.png — NOT REACHED

The module does not load, so there is no run, no LOAD→HEADS timing,
and no head count. (Native baseline for reference: LOAD→HEADS 30.8 s;
Phase A would be expected to find 0 heads — stub-font templates — and
that expectation is unchanged.)

## 5. The new failure #3027 — identified, different defect, NOT fixed here

Identified with the same tools as #272 (`fn272/DumpDebug.java`,
`fn272/typemap.py`, `fn272/disasm.py`; helper `fn3027.py` in this
folder locates a function body by file offset):

- **Function #3027** = defined function #2968, type
  `func (ref null 2659, ref null 467) -> void` =
  **`org.audiveris.omr.ui.symbol.MusicFont.<init>(Font)`** (the private
  constructor), body at file offset 1947538, 451 bytes.
- **Failing call**: `MusicFont.getMusicFont(MusicFamily family, int size)`
  — its 2nd parameter is `int`, but the value supplied is `f32`.
  The suspension-continuation block at the reported offset (type 20406,
  yields `(ref 2659, ref 1782, f32)`) carries the float as its third
  value, which becomes that argument. (Same reporting shape as #272:
  Node names the block that produced the value, not the `call` itself.)
- **Root cause — a shim defect, not a TeaVM defect, and not caused by
  this fork's change**: the call site is `MusicFont.java:130`,
  `backupFont = MusicFont.getMusicFont(musicFamily.getBackup(), size);`,
  where `size` is the **protected field inherited from
  `java.awt.Font`**. In real JDK, `Font.size` is **`int`** (with a
  separate `float pointSize`). In the spike's shim
  (`teavm/shims/src/java/awt/Font.java:11`) the field is declared
  **`protected float size`** — a single float field serving both roles.
  So the field read yields `f32`, TeaVM faithfully emits it, and the
  call to the `int`-parameter method is ill-typed. Corroboration from
  the module's own type section: type 467 (`java.awt.Font`) is
  `struct [vtable, eqref, ref 39, i32, f32]` — fields
  name/style/**size:f32**; real JDK `Font` would be
  `[ref, i32, i32, f32]` (name/style/size/pointSize).
- **Why it was invisible until now**: Node reports only the first
  failing function, so #272 masked it. The stock module fails at #272
  and never gets here; this defect is pre-existing in the shim, not
  introduced by the `TPoint`/`TDimension` change (no `Font` code was
  touched).
- **Other direct uses of the inherited `size` field** in the font
  subclasses: `MusicFont.java:147` uses the constructor's own `int`
  parameter (safe); `MusicFont.java:321` uses `(int) Math.rint(...)`
  (explicit cast — safe). Line 130 is the only unguarded
  int-expecting use in `MusicFont`. (`TextFont`/`OmrFont` were grepped
  the same way; no other unguarded use found — but that grep was
  limited to direct `size` mentions in those three files.)
- **Identified fix (not applied — see below)**: in
  `teavm/shims/src/java/awt/Font.java`, split the field per real JDK:
  `protected int size; protected float pointSize;`, with
  `Font(String,int,int)` setting both, `Font(String,int,float)` setting
  `size=(int)size, pointSize=size`, `getSize()` returning `size`,
  `getSize2D()` returning `pointSize`, and the `Font(Font)` copy ctor /
  `deriveFont` overloads updated accordingly. That is a one-class shim
  correction in the same spirit as this fork's fix (restoring JDK
  fidelity in the emulation layer). It was **not** applied here, per
  the task instruction to record new failures rather than chase them —
  and because Node stops at the first failure, further masked defects
  may exist behind #3027, so fixing one more site does not by itself
  prove the module loads.

## 6. What remains / next steps

1. **Apply the Font shim fix** (§5) — rebuild `shims.jar`, recompile
   `patched/classes`, recompile TeavmMain with the fork classlib, load
   in Node. Expect further masked failures to surface one at a time;
   each needs the same treatment (identify the function, check whether
   it is a shim/classlib fidelity gap vs a TeaVM codegen bug).
2. **Decide the Gradle question**: if TeaVM is to be built from source
   repeatedly, Gradle's daemon must be made to work in the build VM
   (or the direct-`javac` build in §3 documented here becomes the
   sanctioned path — it builds the identical classlib from the same
   sources, with generated files byte-identical to stock).
3. **Upstream**: update `../teavm/ISSUE_272_DRAFT.md` before filing —
   the suggested fix should be "add classlib `TPoint2D`/`TDimension2D`
   and make `TPoint`/`TDimension` extend them" (§2), not just "extend
   `Point2D`". File the #272 issue (with the minimal repro in
   `../teavm/fn272/repro/`); #3027 is a spike-shim issue, not a TeaVM
   issue, and should not be filed against TeaVM.
4. **If the module eventually loads**: run TeavmMain in Node on
   `hymn-satb.gray` (`../teavm/hymn-satb.gray`, 2480×3507) via the
   existing `run-teavm.mjs` pattern (adapted to `full-out/`), with a
   generous timeout, and report LOAD→HEADS time vs native 30.8 s and
   heads found (expect 0 in Phase A).

## 7. Continuation — masked-failure iteration, 2026-11-08 evening (STOPPED at #21244)

Authorised as "try to get TeaVM working": fix #3027, then iterate on masked
failures one at a time while each is a classified shim/classlib defect with
a contained fix; stop on a genuine TeaVM codegen defect, an unworkable
fork-build failure, or >~5 masked failures in a row with no load. Work only
in `~/workspace/score-reader-spikes/teavm-wasm/`; the user repo was not
touched; nothing pushed, filed, or merged. Each iteration: rebuild
`teavm/build.sh` (~35 s), recompile TeavmMain with the fork classlib
(~60 s, `java -Xmx3g -cp "lib/*:classes" Spike wasm-gc
../teavm-fork/full-outN teavm.TeavmMain @../teavm-fork/teavm-main-jars-fork.txt
@program-jars.txt`, from `teavm/`), load-test with `node load-test.mjs
full-outN` (from `teavm-fork/`). All compiles report **0 problems**.

Failure log:

| # | Function | Error shape | Classification | Fix | Result |
|---|----------|-------------|----------------|-----|--------|
| #3027 | `MusicFont.<init>(Font)` | `call[1] expected i32, found f32` | (a) shim defect | Split shim `Font`: `int size` + `float pointSize` (§7.1) | Fixed → #18066 |
| #18066 | `SheetStub.doOneStep` | `br_on_cast: (ref null 33) is not a subtype of (ref null 1044)` | (a) shim defect — missing catch type | New shim `java.util.concurrent.TimeoutException` (§7.2) | Fixed → #19489 |
| #19489 | `OmrFont.createFont` | `br_on_cast: (ref null 33) is not a subtype of (ref null 1043)` | (a) shim defect — missing catch type | New shim `java.awt.FontFormatException` (§7.3) | Fixed → #21244 |
| #21244 | `LineCluster.getPointsAt` | `type error in fallthru[0] (expected (ref 780), got (ref null 780))` | (c) genuine TeaVM codegen defect | None — see §7.4 | **BLOCKER — iteration stopped** |

### 7.1 #3027 — FIXED (shim defect)

- **Function #3027** = `org.audiveris.omr.ui.symbol.MusicFont.<init>(Font)`
  (private ctor). Call site `MusicFont.java:130`,
  `getMusicFont(musicFamily.getBackup(), size)` — 2nd arg is `int`, value
  supplied is `f32`, because the spike's shim `Font` declared a single
  `protected float size`. Real JDK `Font` has `int size` plus a separate
  `float pointSize`.
- **Fix** (`teavm/shims/src/java/awt/Font.java`, hand-written, not generated
  by `gen_awt*.py`): split the field per JDK — `protected int size;
  protected float pointSize;` — and updated both ctors, `getSize()` (now
  returns int `size`), `getSize2D()` (now returns `pointSize`), the copy
  ctor (now uses `pointSize`, preserving fractional sizes),
  `deriveFont(float)` / `deriveFont(int, float)` (previously truncated to
  int; now preserve the float point size), `equals` (compares both fields),
  `hashCode`/`toString` (use int `size`). Verified in the rebuilt
  `shims.jar` with `javap`: `protected int size; protected float pointSize;`.
- **Cleanliness check**: re-running `teavm/build.sh` regenerates
  `patched/src`; the `FN272_DIAGNOSIS.md` claim that it "wipes the
  workaround" is **wrong for the copied-in files** — 5 of the 10 per-site
  #272 workarounds survived (LedgerInter, AbstractHorizontalInter, SIGraph,
  Staff, ObjectEditor). They were reverted by hand and each verified
  identical to the repo original ignoring CR line endings; the remaining
  `Point2D.Double` use (`NumberInter.java:391`) is original Audiveris code.
  The patched tree is clean of the old #272 workarounds.
- **Result**: `full-out2/` (0 problems, 2,864 classes, 27,690 methods,
  `classes.wasm` 10,202,852 bytes). #3027 fixed; Node now fails at #18066.
- Patch: `shims-continuation.patch` (Font.java hunk; the pre-fix side is a
  reconstruction — see the patch header).

### 7.2 #18066 — FIXED (shim defect, missing catch type)

- **Function #18066** = `org.audiveris.omr.sheet.SheetStub.doOneStep`
  (via `fn272/DumpDebug.java` on `full-out2/classes.wasm.teadbg`; line info
  is method-granular only, line -1; no class-layout section in the
  `.teadbg`, so `DumpLayout` NPEs — layout info present=false).
- **Error**: `Compiling function #18066 failed: invalid types for br_on_cast:
  (ref null 33) is not a subtype of (ref null 1044) @+5623694`. The failing
  instruction is a `br_on_cast` in the try/catch dispatch: TeaVM's
  `WasmGCInstructionGenerationVisitor` (line ~1687) emits
  `castBranch(SUCCESS, throwableType, exceptionType, ...)` for each catch
  clause, where source = `java.lang.Throwable`'s struct and target = the
  caught exception type's struct. Decoded from the raw bytes (`fb 18` +
  flags byte + label + sleb heap types — the flags byte is why a naive
  parse misaligns): `br_on_cast flags=3 label=0 src=1044 dst=33`. Type
  1043/1044's field shape matches `TThrowable` (String, self, 2× bool,
  2× array-holder, 2× JSObject externref); type 33 is an empty root struct
  `[vtable, eqref]`, supers=[] — the shape TeaVM gives a class it cannot
  find in the class source (no supertype, no fields).
- **Which class is type 33**: `doOneStep`'s only catch clause is
  `catch (TimeoutException tex)` at `SheetStub.java:505`. A classpath scan
  (all jars in `lib/`, `shims.jar`, `lib-patched/`, `repo/.work/lib/`,
  accounting for TeaVM's `T`-prefixed substitution classes) showed
  `java.util.concurrent.TimeoutException` is the ONLY catch type in the
  whole program missing from TeaVM's classpath (all others — IOException,
  FileNotFoundException, ParseException, ExecutionException,
  IllegalAccessException, NumberFormatException, InterruptedException,
  ArrayIndexOutOfBoundsException, CloneNotSupportedException,
  ClassNotFoundException, ConcurrentModificationException, JAXBException,
  StepException, StepPause, ProcessingCancellationException,
  ImageFormatException, CmdLineException — are present; `ParsingException`
  is a private nested class in `MetronomeInter`, present in patched/src).
  The disassembler `fn272/disasm.py` desyncs on `try_table` (opcode 0x1f)
  and on blocktypes that are ref types — fixed in a copy
  `teavm-fork/disasm2.py` (ref-type blocktypes + `try_table`
  catch-clause immediates), which is how the suspension blocks were read.
  A new helper `fn272/DumpLine.java` (uses `LineInfo.deobfuscate`) was also
  written; it only returns method names (line -1) for these addresses.
- **Minimal repro proved the mechanism end-to-end** (`teavm-fork/repro2/`,
  `repro2.Repro2`, `repro2-jars.txt`, runner `run-repro2.mjs`): a catch-only
  `try { f.get(1, TimeUnit.SECONDS); } catch (TimeoutException e) {...}`
  reproduces the defect exactly — TeaVM compiles it with **0 problems**
  and emits the module, Node fails with `Compiling function #184 failed:
  invalid types for br_on_cast: (ref null 13) is not a subtype of
  (ref null 19)`, where type 13 is the empty root struct
  (TimeoutException) and type 19 is Throwable's struct (decoded
  br_on_cast bytes: flags=3 label=0 src=19 dst=13; the other two clauses
  dst=60/61 are InterruptedException/ExecutionException, present in the
  classlib). Note the TeaVM reporting inconsistency: when the missing class
  is referenced from a method signature/throw (`throws TimeoutException`),
  TeaVM reports `PROBLEM ERROR | Class
  java.util.concurrent.TimeoutException was not found` and refuses to emit
  a module; when it is referenced ONLY in a catch clause (plus the shim
  `Future.get` signature), TeaVM silently emits the module with the empty
  struct and 0 problems. The first repro form (with `throws
  TimeoutException` and a null Future) also showed the runtime trap is
  `RuntimeError: unreachable` for an uncaught NPE — that was a flaw in the
  repro (null Future), not the fix.
- **Fix** (category (a) shim defect): new shim
  `teavm/shims/src/java/util/concurrent/TimeoutException.java` —
  `public class TimeoutException extends Exception` with `()` and
  `(String)` ctors, matching the style of other exception shims (e.g.
  `UnsupportedFlavorException`, `BadLocationException`). Rebuilt
  `build.sh` (BUILD OK); verified in `shims.jar`: `TimeoutException
  extends java.lang.Exception`, Font fix intact. Repro re-run with the
  shim: **LOAD OK, `caught TimeoutException: boom`, `done`, `main()
  returned`** — mechanism proven.
- **Result**: `teavm-fork/full-out3/` (0 problems, 2,865 classes, 27,692
  methods, `classes.wasm` 10,203,039 bytes, `full-build3.log`). #18066 is
  FIXED — the module now fails at a NEW function #19489, same error shape:
  `Compiling function #19489 failed: invalid types for br_on_cast:
  (ref null 33) is not a subtype of (ref null 1043) @+6106371`.

### 7.3 #19489 — FIXED (shim defect, missing catch type)

- **Function #19489** = `org.audiveris.omr.ui.symbol.OmrFont.createFont`
  (via DumpDebug on `full-out3/classes.wasm.teadbg`). Type 1043 =
  Throwable's struct (same field shape as before, supers=[5]); type 33 =
  empty root struct again.
- Decoded br_on_cast at 6106371: flags=3 label=0 src=1043 dst=33. Two
  further br_on_casts follow in the same dispatch: src=1043 dst=1062
  (label 1) and src=1043 dst=4221 (label 2) — three catch clauses,
  matching `OmrFont.createFont` (Audiveris source, same `.work/audiveris`
  tree): `catch (FontFormatException | IOException ex)` at line 316
  (multi-catch, two types) and `catch (MalformedURLException ex)` at
  line 319.
- Classpath check (same method as #18066):
  `java.awt.FontFormatException` is MISSING (nowhere in any jar, no
  `TFontFormatException`); `java.io.IOException` OK (via `TIOException`);
  `java.net.MalformedURLException` OK (via `TMalformedURLException`).
- **Proactive audit**: every catch type across the whole Audiveris source
  tree (39 distinct types, incl. all multi-catch second/third types:
  DocumentException, FileNotFoundException, UnsupportedEncodingException,
  IOException, InterruptedException, JAXBException, XMLStreamException,
  URISyntaxException, ExecutionException, InvocationTargetException,
  NoSuchMethodException, SecurityException) was checked against the
  classpath (jars + shims.jar + lib-patched + repo/.work/lib, with
  T-prefix mapping and Audiveris's own classes). **FontFormatException was
  the only other missing catch type** besides TimeoutException — so no
  further missing-catch-type failure is expected from Audiveris sources
  (library jars' own catch clauses were not audited; they would surface
  the same way if hit).
- **Fix** (category (a)): new shim
  `teavm/shims/src/java/awt/FontFormatException.java` —
  `public class FontFormatException extends Exception` with a `(String)`
  ctor (JDK-faithful: the real class has only the `FontFormatException(String
  reason)` ctor). Rebuilt `build.sh` (BUILD OK); verified in `shims.jar`
  with `javap`: `public class java.awt.FontFormatException extends
  java.lang.Exception { public java.awt.FontFormatException(java.lang.String); }`.
- **Result**: `teavm-fork/full-out4/` (0 problems, 2,866 classes, 27,693
  methods, `classes.wasm` 10,203,257 bytes — see `full-build4.log`). #19489
  fixed; Node now fails at #21244, a **different error shape**.

### 7.4 #21244 — BLOCKER (genuine TeaVM codegen defect, class (c))

- **Error** (`full-out4`, `node load-test.mjs full-out4`):
  `CompileError: WebAssembly.compileStreaming(): Compiling function #21244
  failed: type error in fallthru[0] (expected (ref 780), got (ref null 780))
  @+6583845`.
- **Function #21244** = `org.audiveris.omr.sheet.grid.LineCluster.getPointsAt`
  (identified with `fn272/DumpDebug.java` on
  `full-out4/classes.wasm.teadbg`; confirmed with a new helper
  `fn272/DumpSeq.java`, which lists debug sequences by address range —
  getPointsAt is [6580793..6584230), containing the failing offset
  6583845). Raw bytes confirm: byte at 6583845 is `0x0b` (`end`), and
  bytes at 6582266 are `02 99 ae 01` = `block` with blocktype sleb 22297.
- **The block**: the `end` at 6583845 closes the block at 6582266 with
  blocktype 22297, whose results are
  `['ref typeidx(780)', 'ref null typeidx(748)', 'ref null typeidx(1810)']`
  — the FIRST result is declared **non-nullable** `(ref 780)`, the others
  nullable. The fallthrough path yields `(ref null 780)` in slot 0.
  The enclosing block at 6582260 (type 13170) declares the *same logical
  values* as `['ref null typeidx(780)', 'ref null typeidx(748)',
  'ref null typeidx(1810)', 'ref null typeidx(1262)']` — **all nullable**.
  TeaVM's own two nested blocks disagree about the same value's
  nullability. The restore sequence inside the block restores the three
  frame values with `ref.cast 780` (non-null assertion) for slot 0 but
  `ref.cast_null` for slots 1–2 — TeaVM's analysis believed slot 0
  non-null. These are TeaVM's async/suspension continuation blocks: the
  block body starts with a `br_table` state-machine dispatch on local 28
  (the resume state) at 6582352.
- **What the types are** (via `fn272/typemap.py` on `full-out4`):
  type 780 = struct `[vtable, eqref, ref null 5, ref null 5]`, supers=[5]
  — a direct-Object-subclass with exactly two Object fields; among
  `getPointsAt`'s locals the only match is the `Map.Entry` loop variable
  (a `TreeMap$TreeNode`, i.e. a `TAbstractMap$SimpleEntry` with its
  `key`/`value` fields — `TTreeMap.TreeNode extends SimpleEntry`, and
  `EntryIterator.next()` returns `last`, a TreeNode). Type 748 =
  `[vtable, eqref, i32]`, supers=[447] — `java.lang.Integer` (single int
  field, extends Number): the boxed `pos` / `entry.getKey()`. Type 1810 =
  `[vtable, eqref, f64, f64]`, supers=[46] — `Point2D.Double` (x, y):
  the `end` / ternary-constructed point. Type 1262 (enclosing block's 4th
  result) is a func type — the continuation funcref.
- **Why it is class (c), not (a) or (b)**:
  1. The mismatch is between TeaVM's *nullability analysis* (slot 0
     non-null) and the *code it emitted* (a nullable value on the
     fallthrough path). The value is a **program local** (a Map.Entry
     from `lines.entrySet()` in Audiveris code), not a JDK API return —
     no shim or classlib class is unfaithful here, and no shim/classlib
     change can alter whether TeaVM proves a program local non-null.
     `TTreeMap$EntryIterator.next()` really never returns null (it throws
     `NoSuchElementException` instead), so the classlib is *correct* to
     let TeaVM prove the entry non-null; the nullable value on the
     fallthrough path comes from the *caller's* control flow (the loop
     variable's initial/null state on the path that enters the
     continuation block by fallthrough rather than by resume), which is a
     property of TeaVM's async transformation, not of any JDK class.
  2. The pattern is **rare, not systematic**: a scan of all 31,907 types
     in `full-out4` found only **10** func types with any non-null ref
     result, and only **3** multi-result ones (the continuation-block
     shape): 22297/22298 (both in getPointsAt, same 780 value) and
     26401/26402 (in `PeakGraph.getConnectedPeaks`, a *different*
     non-null type 758 — a no-field class extending no-field type 45,
     with second result type 1847, a 15-field class). So there are **two
     independent sites** with this defect; fixing the 780 site alone would
     immediately surface the 758 site. A targeted per-site fix does not
     exist — the fix belongs in TeaVM's async codegen (continuation block
     result types must be the join over all incoming paths, i.e. nullable
     if any incoming value is nullable), most likely in the async
     state-machine generation (`WasmGCMethodGenerator` /
     `WasmGCInstructionGenerationVisitor`, with the nullability source in
     the async parts' variable types — `org.teavm.ast.AsyncMethodNode` /
     `AsyncMethodPart` → `WasmGCTypeMapper`). That is a **compiler**
     change, not a classlib fix; building TeaVM's core in this VM is
     unproven (Gradle does not work here; only the classlib was built
     with javac), and it is outside the "contained fix" criterion.
  3. **Per-site Audiveris rewrites are ruled out** by the task brief
     (that path was already rejected for #272 as whack-a-mole).
- **Minimal-repro attempts — both FAILED to reproduce** (so there is no
  minimal repro to file yet; the trigger is a whole-program analysis
  interaction, not the method shape alone):
  - `repro3/Repro3.java` — faithful mirror of `getPointsAt` (TreeMap
    entrySet for-each, `Thread.sleep(0)` suspension inside the loop body,
    nullable `Double y`, nullable `Map.get` lookup, nullable ternary,
    second `for (int dir : new int[]{-1,1})` loop). Compiles 125 classes /
    1,253 methods, 0 problems; **LOADS OK and runs** (`points: 2`,
    `done`). Its `getPointsAt` *does* have the async state machine
    (br_table dispatch, frame restore) and even uses `ref.cast` (non-null)
    in places — but no block declares a non-null continuation result
    that the fallthrough violates.
  - `repro3/Repro3b.java` — closer still: instance method, `lines` an
    instance field declared `SortedMap` (not a static TreeMap), `Line
    extends BaseLine` (like StaffFilament extends CurvedFilament), and an
    async caller (`process()` calling `Thread.sleep`) instead of main
    calling getPointsAt directly. Compiles 127 classes / 1,256 methods,
    0 problems; **LOADS OK**.
  - Both repros built against the fork classlib
    (`lib-fork/teavm-classlib-0.16.0.jar`) with the current shims.jar,
    following the `fn272/repro/README.md` pattern; outputs `repro3/out/`
    and `repro3/out-b/`, runner `run-repro2.mjs`.
- **Tools added during this iteration** (in `teavm-fork/` unless noted):
  `load-test.mjs` (load a wasm dir in Node), `run-repro2.mjs` (run a
  repro wasm), `repro2/` (TimeoutException repro + classes + out),
  `repro2-jars.txt`, `repro2-out/`, `disasm2.py` (disassembler fixed for
  `try_table` 0x1f and ref-type blocktypes), `fntype.py` (print a
  function's type via typemap's parser — note: subtype markers are
  0x4f/0x50, not 0x4d/0x4f, which is why a first version of this tool
  mis-parsed), `fn21244.txt` / `fn29180.txt` (disassembly dumps),
  `fn272/DumpSeq.java` + `fn272/DumpLine.java` (in `teavm/fn272/`),
  `repro3/` (Repro3 + Repro3b + classes + out/out-b + build logs),
  `full-out2/`, `full-out3/`, `full-out4/`, `full-build3.log`,
  `full-build4.log`.
- **Status**: iteration STOPPED per the task's stop rule (genuine TeaVM
  codegen defect). The module does not load; Step 3 (run TeavmMain on
  hymn-satb.png) was not reached. No further masked failure can be
  reached without fixing #21244 in TeaVM itself.

### 7.5 What remains / next steps

1. **File the #21244 issue upstream** (TeaVM repo) — but there is no
   minimal repro yet; the issue would have to be filed against the full
   Audiveris program (or a repro must be found by further bisection,
   e.g. by reducing the real `getPointsAt` call graph rather than
   rebuilding it from scratch). Do NOT file the #272 issue and the #21244
   issue as one thing — they are different defects (#272 = classlib
   hierarchy; #21244 = async-codegen nullability). Update
   `../teavm/ISSUE_272_DRAFT.md` first (it needs the
   `TPoint2D`/`TDimension2D` note from §6.3) and file #272 separately;
   #3027/#18066/#19489 are spike-shim issues, not TeaVM issues, and
   should not be filed against TeaVM.
2. **Alternative path if the exit is still wanted**: a fork fix in
   TeaVM's async codegen (widen continuation block result types to
   nullable) is the principled fix, but it requires building TeaVM's core
   from source — Gradle does not work in this VM, so that path needs a
   working TeaVM-core build first (or a machine where Gradle works).
   Until then, staying on CheerpJ 5 remains the only working option, and
   the JS backend is still not a proven fallback (47 min, zero output).
3. **Housekeeping**: `fn272/classes.wat` (578 MB Binaryen dump from the
   earlier worker) is still sitting in `teavm/fn272/` and is worth
   deleting. The `teavm-classlib-fix.patch` is unchanged (still only
   TPoint + TDimension — verified with `git status` in `src/`); the shim
   changes are recorded in `shims-continuation.patch` (new-file diffs for
   the two exception shims are exact; the Font.java hunk is against a
   reconstruction — see that file's header).

## 8. Files in this folder

- `FORK_FIX.md` — this report.
- `teavm-classlib-fix.patch` — `git diff` of the TeaVM source changes
  (2 files, TPoint + TDimension).
- `src/` — TeaVM 0.16.0 source, tag `0.16.0` @ `e87d452`, with the fix
  applied (only the 2 files differ from the tag).
- `lib-fork/` — runtime jars for the fork tests: source-built
  `teavm-classlib-0.16.0.jar` + stock 0.16.0 jars.
- `direct/` — the direct source build: `sources.txt`, `javac.log`,
  compiled `classes/`, generator outputs `generated/`, `jar.log`.
- `smoke/` — the preliminary jar-patch smoke test (two classes compiled
  standalone, patched into a stock-jar copy).
- `repro-out/`, `repro-out-fixed/` — repro + control compiled against
  the smoke jar. `repro-out2/` — repro compiled against the
  source-built jar. `run-repro.mjs` — Node runner for the repro.
- `full-out/` — TeavmMain compiled with the fork classlib
  (`classes.wasm` 10,202,825 bytes, `classes.wasm.teadbg`).
- `full-build.log`, `build-clean.log`, `build-clean2.log`,
  `gradle-classlib*.log` — build logs.
- `teavm-main-jars-fork.txt` — TeavmMain classpath with the fork
  classlib substituted for the stock one.
- `fn3027.py` — locate a function body by file offset + disassembly
  window (used for §5).
- `shims-continuation.patch` — shim changes from the §7 continuation
  (Font.java split; new TimeoutException + FontFormatException shims).
  The Font.java hunk is against a reconstruction — see its header.
- `full-out2/`, `full-out3/`, `full-out4/` — TeavmMain compiled with the
  fork classlib after each §7 fix (`full-out4/classes.wasm` 10,203,257
  bytes; fails at #21244). `full-build3.log`, `full-build4.log`.
- `load-test.mjs`, `run-repro2.mjs` — Node load/run helpers for wasm dirs.
- `repro2/` (+ `repro2-out/`, `repro2-jars.txt`) — minimal repro proving
  the #18066 missing-catch-type mechanism; loads and runs with the shim.
- `repro3/` — Repro3 + Repro3b, two faithful mirrors of `getPointsAt`
  that do NOT reproduce #21244 (both load and run); outputs `out/`,
  `out-b/`.
- `disasm2.py`, `fntype.py`, `fn21244.txt`, `fn29180.txt` — disassembler
  (fixed for `try_table`/ref-type blocktypes), function-type printer,
  disassembly dumps for the #21244/#26401 sites.
  (`../teavm/fn272/` also gained `DumpSeq.java` and `DumpLine.java`.)
- `gradle-9.7.1-bin.zip` (151 MB) — the Gradle distribution downloaded
  for the failed Gradle attempt; the extracted `gradle-dist/` was
  deleted (re-derivable from the zip). `gradle-home/` is the
  `GRADLE_USER_HOME` used (daemon registry/logs only; no usable build
  cache — the build never got past daemon dispatch).

## 9. Core patch for #21244 — WasmTypeInference nullability, 2026-11-09 (PARTIAL: #21244 fixed, module loads, run stalls earlier)

### 9.1 The defect, restated (§7.4)
Function #21244, `LineCluster.getPointsAt`: a suspension continuation block
(blocktype 22297) declares its first result non-nullable `(ref 780)`, but the
fallthrough path yields `(ref null 780)`. TeaVM's own enclosing block (type
13170) declares the same value nullable. The value is a `Map.Entry` loop
variable (a `TreeNode`/`SimpleEntry` program local), so no shim or classlib
fix applies. A second independent site exists in `PeakGraph.getConnectedPeaks`
(type 758).

### 9.2 Root cause found (not the first hypothesis)
`WasmTypeInference` has a `forceNullable` flag that
`CoroutineTransformation.ListSplitter` enables (`new WasmTypeInference(true)`),
but it is only honoured in a few `visit` methods (GetGlobal, StructNew,
StructNewDefault, StructGet). `visit(WasmCast)` pushes the raw (non-null)
target type, `visit(WasmGetLocal)` / `visit(WasmTeeLocal)` push the raw local
type, and call / block / conditional / try / array / function-reference sites
likewise push raw types. A `ref.cast 780` in the original codegen therefore
puts a non-null `ref 780` onto the splitter's stack, which flows into block
signatures — notably `processOptimizedBlock`, which sets a block type from the
raw `typeInference.typeStack` — and into restore casts
(`CoroutineFunctions.restoreValue` emits `ref.cast` for a non-null type,
`ref.cast_null` for a nullable one). Verified against the disassembly of
function #21244 in `full-out4` (`fn21244.txt`): block type 22297 results
`[ref 780, ref null 748, ref null 1810]`, enclosing block 13170 all nullable;
restore sequence at offsets 6583757–6583777 restores `entry` with
`ref.cast 780` but `pos`/`end` with `ref.cast_null`.
`WasmTypeInference(true)` is used ONLY by the coroutine splitter (the other
caller, `WasmInstructionBuilder`, uses the default `false`), so honouring
`forceNullable` consistently is safe and contained.

### 9.3 The patch
One file:
`src/core/src/main/java/org/teavm/backend/wasm/model/instruction/WasmTypeInference.java`
(saved as `teavm-core-21244.patch`, 171 lines; `git diff` of `src/`).
Added a `mapToNullableTypes(List)` helper reusing the existing
`mapToNullable(WasmType)`, and applied it at every push site — Block,
Conditional, CastBranch (source/target), NullConstant, GetLocal, TeeLocal,
Call, IndirectCall, CallReference, Try, Cast, ArrayNewDefault, ArrayNewFixed,
ArrayGet, FunctionReference — and guarded the `WasmNullBranch` non-null
refinement with `!forceNullable`. Remaining raw pushes are numeric types,
I31, and ANY/EXTERN specials (already nullable variants).
`git diff --stat` for the whole fork source: 3 files changed (TPoint,
TDimension, WasmTypeInference), 207 insertions / 22 deletions. The
WasmTypeInference diff alone is 53 lines changed. The patch is principled
and upstreamable: continuation block result types are now the join over all
incoming paths (nullable if any incoming value is nullable).

### 9.4 Build — Gradle definitively unusable; javac jar patch used
- Gradle 9.7.1 zip in `teavm-fork/` had never been extracted (extracted dir
  was deleted earlier); extracted to `teavm-fork/gradle-dist/`;
  `gradle-home/caches` is empty (0 bytes), so an offline build had no
  dependencies. Ran Gradle 9.7.1 `--no-daemon --offline` off / online
  `:core:compileJava -x checkstyleMain` (JAVA_HOME =
  `~/workspace/score-reader-spikes/repo/.work/jdk/jdk-25.0.5+8`,
  GRADLE_USER_HOME = `teavm-fork/gradle-home`): failed in ~7 s with
  "Could not dispatch a message to the daemon" — even `--no-daemon` forks a
  single-use daemon and the client→daemon loopback TCP write fails
  (`MessageIOException: Could not write '/127.0.0.1:37729'`, caused by
  `java.io.IOException: Connection reset by peer` at
  `SocketDispatcher.write0`). Gradle is definitively unusable in this VM.
- Approach (2): javac patch of the compiled core jar. Stock
  `teavm/lib/teavm-core-0.16.0.jar` class files are major version 61 (Java
  17). Compiled the patched `WasmTypeInference.java` with `javac --release 17`
  against the stock core jar (exit 0; output `WasmTypeInference.class`
  17,088 bytes + synthetic `WasmTypeInference$1.class` 2,333 bytes for the
  enum switch); verified by `javap` that the compiled class contains
  `mapToNullable`/`mapToNullableTypes` and the visit methods call them.
  Built `lib-fork/teavm-core-0.16.0-patched.jar` (copy of stock jar with the
  two recompiled classes replaced via `jar uf`), and
  `teavm-main-jars-corepatch.txt` (copy of `teavm-main-jars-fork.txt` with
  only the core-jar line changed to the patched jar).
  Caveat: the patched jar replaces only `WasmTypeInference` (+ its synthetic
  switch class). If the fix needs changes in other core classes, the same
  javac-against-the-stock-jar procedure applies per class.

### 9.5 Tests
(a) Minimal repros — PASS, no regression. Recompiled `repro3.Repro3` →
`repro3/out-patched/` (125 classes / 1,253 methods) and `repro3.Repro3b` →
`repro3/out-b-patched/` (127 / 1,256) with the patched core; both load and
run in Node (`LOAD OK`, `main() returned`, `points: 2`, `done`).
(b) Full TeavmMain with patched core + fork classlib — #21244 GONE.
`full-out5/`: 0 problems, 2,866 classes, 27,693 methods,
`classes.wasm` 10,203,257 bytes (same byte count as full-out4). Node load:
new failure at function #32683: `Compiling function #32683 failed: invalid
types for br_on_cast: (ref null 32) is not a subtype of (ref null 1042)
@+9053143`.
- #32683 identified (via `fn272/DumpDebug.java` on
  `full-out5/classes.wasm.teadbg`, offset 9053143):
  `com.jgoodies.common.base.SystemUtils.isLowResolution`. Its bytecode (from
  `jgoodies-common-1.8.1.jar`) catches `java.awt.HeadlessException`
  (`Toolkit.getDefaultToolkit().getScreenResolution() < 120`, catch
  HeadlessException → return true). Type 32 is the empty-root-struct
  signature of a missing class; type 1042 is Throwable's struct.
  Classification: (a) shim defect, same class as #18066/#19489. Verified
  `HeadlessException` is absent from `shims.jar`, the stock classlib, and
  the fork classlib.
- Full catch-type audit (new tool `AuditCatchTypes.java`, ASM-based,
  compiled against `teavm/lib/asm-9.10.1.jar`): scanned every class in every
  jar of the TeaVM program classpath (239 distinct catch types). 53 missing
  from the classpath. To filter to what matters, wrote
  `teavm/fn272/DumpClasses.java` (lists distinct class names from the
  `.teadbg` debug sequences) — `full-out5` has 2,539 classes with debug info
  (of 2,866 compiled) — and cross-checked every (catch type, containing
  class) pair (`audit-catch-pairs.txt`, 4,221 pairs) against the compiled
  classes. Result: only **2** missing types have a catch in a compiled
  class: `java.awt.HeadlessException` (in
  `com.jgoodies.common.base.SystemUtils` — the current failure) and
  `java.beans.IntrospectionException` (in `org.jdesktop.application.ResourceMap`,
  bsaf). The earlier audit's explicit gap ("library jars' own catch clauses
  were not audited") is what let this one through.
- Both shims added, modelled on the existing exception shims:
  `teavm/shims/src/java/awt/HeadlessException.java` (`extends
  UnsupportedOperationException`, `()` and `(String)` ctors; superclass
  provided by the classlib as `TUnsupportedOperationException`) and
  `teavm/shims/src/java/beans/IntrospectionException.java` (`extends
  Exception`, `(String)` ctor). No generator (`shims/gen_*.py`) mentions
  either class; `shims/src/java/beans/` already holds hand-written shims.
  Rebuilt via `teavm/build.sh` (BUILD OK, ~32 s; `patched/classes` 261
  classes); verified in `shims.jar` with `javap`: `HeadlessException extends
  UnsupportedOperationException` with both ctors, `IntrospectionException
  extends Exception` with the String ctor.
- `full-out6/` (patched core + fork classlib + both new shims): 0 problems,
  2,867 classes, 27,695 methods, `classes.wasm` 10,203,503 bytes
  (`full-build6.log`). **Node load test: LOAD OK in 327 ms.** The module
  loads. #21244 is fixed; the #32683/IntrospectionException shim defects are
  fixed.
(c) Run TeavmMain on hymn-satb.png — module loads, run does NOT reach HEADS.
- Full page (`run-fullout.mjs full-out6`, `timeout 600`): wasm loaded in
  364 ms, `IMAGE w=2480 h=3507`, `GREY BYTES 8697360`, then inside
  `stub.reachStep(OmrStep.HEADS, false)` with no further output. Node at
  96.5% CPU, ~5:01 CPU time at ~6 min wall — genuinely working, not
  deadlocked. Killed by `timeout 600` with no HEADS reached, no `TEAVM
  DONE`, no timing. Native LOAD→HEADS is 30.8 s, so WasmGC is >19× slower
  here or stuck in a pathological path — the same symptom as the JS backend
  (47 min, zero output).
- Crop discriminator (`hymn-crop.gray`, 2480×700 top strip, 1,736,000 bytes;
  `run-crop.mjs full-out6`, `timeout 300`): also killed at 300 s with no
  HEADS. A 5×-smaller input does not finish either, so it is not merely
  "slow on a big page".
- Per-step diagnostic (diagnostic `TeavmMain`, `full-out7`, crop,
  `timeout 300`): NOT EVEN `STEP LOAD` printed. The stall is before/during
  the first step, NOT in HEADS template matching — this kills the
  stub-font-blank-templates hypothesis (JS §7) for this stall.
- Split further (`full-out8`, crop, `timeout 180`): `RESTART DONE` (printed
  after `OmrExecutors.restart()`) never appeared. `restart()` itself is
  trivial — `creationAllowed = true; logger.debug(...)` — and creates no
  thread pools (those are lazy), so the stall is in `OmrExecutors`' static
  initialisation, triggered by the first use of the class.
- Split further (`full-out9`, crop, `timeout 180`): `IMAGE READY` (printed
  after the `BufferedImage` + `arraycopy` setup) DID print; `RESTART DONE`
  still never did. So the image setup is fine and the stall is inside
  `OmrExecutors` static init: `LoggerFactory.getLogger(...)`,
  `Constants constants = new Constants()` (whose `ConstantSet()` ctor calls
  `UnitManager.getInstance().addSet(this)` — reflection-heavy
  `getClass().getDeclaringClass()`, singleton lazy init), `cpuCount =
  Runtime.getRuntime().availableProcessors()`, the three `Pool` instances,
  or the static block `if (constants.printEnvironment.isSet())`. Which of
  these spins at ~96% CPU is NOT yet identified — that is the next
  investigation, not this one. The diagnostic `TeavmMain` was saved as
  `TeavmMain-diagnostic.java` in this folder and the clean entry restored
  (`teavm/entry/src/teavm/TeavmMain.java` + `build.sh` re-run so
  `patched/classes` matches the clean entry).

### 9.6 Verdict: PARTIAL
The core patch works: #21244 is gone, the module loads in Node, the minimal
repros still pass, and the two masked shim defects it exposed are fixed. But
TeavmMain still does not read a page: the run now stalls earlier than HEADS,
inside `OmrExecutors` static initialisation (before `STEP LOAD`), at ~96%
CPU. No WasmGC timing exists; no heads count exists. CheerpJ 5 remains the
only working option. The #21244 fix is a genuine, upstreamable TeaVM-core
fix (file it separately from #272 — different defect; the patch is the
candidate upstream fix) and should NOT be conflated with the new stall,
which is in Audiveris's startup path under WasmGC, not in the async codegen.
Next step if the exit is still wanted: instrument `OmrExecutors` static init
(one print per field / per static-block line, or a minimal class-init repro)
to find which component spins, then decide whether it is a TeaVM
reflection/class-init gap or an Audiveris-side workaround (e.g. a
single-threaded / headless startup path that avoids the executor pools and
the constants machinery until after the first page).

### 9.7 Files added in §9
- `teavm-core-21244.patch` — the WasmTypeInference fix (git diff of `src/`).
- `lib-fork/teavm-core-0.16.0-patched.jar` — stock core jar with the two
  recompiled `WasmTypeInference` classes replaced (`jar uf`); source patch
  is the durable artifact, the jar is derived.
- `teavm-main-jars-corepatch.txt` — TeavmMain classpath with the patched
  core jar substituted.
- `full-out5/`, `full-out6/`, `full-out7/`, `full-out8/`, `full-out9/` +
  `full-build5.log`…`full-build9.log` — TeavmMain builds (full-out5: #21244
  gone, fails #32683; full-out6: LOADS; full-out7–9: diagnostic entry
  builds).
- `AuditCatchTypes.java`, `audit-catch-types.txt`, `audit-catch-pairs.txt`,
  `compiled-classes.txt` — catch-type audit (239 distinct catch types, 53
  missing, only 2 mattering).
- `load-test.mjs`, `run-fullout.mjs`, `run-crop.mjs`,
  `run-fullout6.log`, `run-crop6.log`, `run-crop7.log`, `run-crop8.log`,
  `run-crop9.log` — Node load/run helpers and logs.
- `hymn-crop.gray`, `hymn-crop.json` — 2480×700 top-strip crop of
  hymn-satb.png (1,736,000 bytes) for the slow-vs-stuck discriminator.
- `repro3/out-patched/`, `repro3/out-b-patched/` — repros rebuilt with the
  patched core.
- `TeavmMain-diagnostic.java` — diagnostic entry (per-step prints + RESTART
  DONE + IMAGE READY); clean entry restored in `teavm/entry/src/`.
- New shims (in `teavm/shims/src/`, not in this folder):
  `java/awt/HeadlessException.java`, `java/beans/IntrospectionException.java`.
  (`/tmp/corepatch/` holds ephemeral copies of the recompiled core classes —
  do not rely on it; the source patch and the jar in `lib-fork/` are the
  durable artifacts.)
- `teavm/fn272/DumpClasses.java` — lists distinct class names from a
  `.teadbg` file (used by the catch audit).

## 10. OmrExecutors stall — diagnosed and fixed; run now reaches `new Book`, then a null-pointer trap — 2026-11-09 (PARTIAL, stopped at the next failure per the task's stop rule)

Task: instrument the `OmrExecutors` static-init stall that blocked TeavmMain
under TeaVM WasmGC (full-out6 LOADS OK, 10 min at 96.5% CPU, no output past
GREY BYTES; IMAGE READY prints, RESTART DONE never does), name the spinning
component, classify it, and if a contained fix exists, apply it and re-run.

### 10.1 Instrumentation method (diag10, as in §7/§9)

Diagnostic copies only — `jdlehman/score-reader` and the repo's Audiveris
sources were never touched. Work in
`~/workspace/score-reader-spikes/teavm-wasm/teavm-fork/diag10/`:
instrumented copies of `OmrExecutors`, `Constant`, `ConstantSet`,
`UnitManager`, `ConstantManager`, `Main`, `WellKnowns` (built by
`make_diag_exec.py` / `make_diag_const.py`, `/tmp/make_diag_wk.py`),
compiled ahead of the program classpath via `diag-jars.txt`
(`diag10/classes` first). Runs: `timeout 60 node run-diag.mjs outN`.
A minimal repro pair (`diag/DiagMain.java`, `diag/ReflMain.java`) isolated
the reflection behaviour. All runs used the §9 patched core jar
(`lib-fork/teavm-core-0.16.0-patched.jar`) on the *program* classpath and
the stock `teavm/lib` jars on the Spike compiler classpath — see §10.5 for
why that distinction matters.

### 10.2 Last-print evidence — the stall, named

- **Minimal repro reproduces the stall.** `DiagMain` (prints "DIAG A", calls
  `OmrExecutors.restart()`, prints "DIAG B"): `out` (157 classes, 1,737
  methods, 0 problems) — "DIAG A" prints, then nothing for 60 s. The stall
  is inside `OmrExecutors` static init (or first touch), confirmed in
  isolation.
- **Field-level instrumentation (`out2`).** Static field initialisers
  restructured into one static block with prints EXEC 1–9: EXEC 1 logger
  done, EXEC 2 constants done, EXEC 3 defaultParallelism done, EXEC 4
  cpuCount done, EXEC 5 highs done, EXEC 6 lows done, EXEC 7 cachedLows
  done, EXEC 8 allPools done — then "EXEC 9 static-block isSet" prints and
  nothing more. **The stall is in the static block's
  `constants.printEnvironment.isSet()` call.**
- **Constant/ConstantSet/UnitManager instrumentation (`out3`).** Bounded
  `Constant.checkInitialized()` (prints every 1,000 iterations, bails with
  `RuntimeException` after 20,000), per-field `ConstantSet.initMap()`
  prints, per-iteration `UnitManager.checkDirtySets()` prints. Bailed in
  321 ms: first `checkDirtySets` has `dirtySize=1`, name
  `org.audiveris.omr.util.OmrExecutors`, unit non-null; then
  **`DIAG initMap fields=0`** — `cl.getDeclaredFields()` returns an EMPTY
  array for the `Constants` class under TeaVM; `initMap` assigns an empty
  map (size=0), `initialize()` returns true, the dirty set is cleared;
  thereafter every `checkDirtySets` reports `dirtySize=0`, rookies=0,
  while `checkInitialized` spins on `printEnvironment` ("Should we print
  out current environment?") until the 20,000-iteration bail (`DIAG FAILED:
  java.lang.RuntimeException: DIAG: checkInitialized spin`). 19,999
  `checkDirtySets enter dirtySize=0` lines logged (`run-diag3.log`, ~2 MB).
  **Root cause of the stall, proven: `getDeclaredFields()` returns 0
  fields, so no Constant ever gets a qualified name, and
  `checkInitialized()` busy-spins forever.**

### 10.3 Why `getDeclaredFields()` returns 0 — TeaVM reflection metadata

- **Minimal reflection repro (`ReflMain`).** A `Holder` class with 4 fields
  (private `a`, private `b`, public `c`, static `d`). Native desktop Java:
  `getDeclaredFields=4`, `getFields=1` (c), `getDeclaredField("a")` works.
  TeaVM WasmGC (`out-refl`, 115 classes): **`getDeclaredFields=0`,
  `getFields=0`, `getDeclaredField("a")` throws `NoSuchFieldException`** —
  same for public fields.
- **Mechanism (read from fork source `teavm-fork/src/`).**
  `TClass.getDeclaredFields()` (`classlib/.../TClass.java:207`) returns an
  empty array when `classInfo.reflection() == null`. Reflection metadata is
  generated ONLY for members a `ReflectionPolicy` declares accessible:
  `DefaultReflectionSupplier` loads `ReflectionPolicy` implementations via
  `ServiceLoader.load(ReflectionPolicy.class, ...)`; the
  `ReflectionDependencyListener` links only fields in
  `getAccessibleFields()`. With no policy registered in the Spike build,
  accessible fields are empty for every class.
- **Fix tested on the minimal repro — WORKS.** `diag/AllReflectablePolicy.java`
  (`SimpleReflectionPolicy`,
  `allClasses().reflectableMembers(m -> true)`) + a
  `META-INF/services/org.teavm.extension.spi.reflection.ReflectionPolicy`
  entry. Rebuilt ReflMain (`out-refl2`): **`getDeclaredFields=4`,
  `getFields=1` (c), `getDeclaredField("a")` works, `REFL DONE`** —
  identical to native.

### 10.4 The stall is gone — but a trap replaces it (narrowed step by step)

- **DiagMain with the all-classes policy (`out4`, 264 classes):** initMap
  now sees `fields=3`, first field `printEnvironment` non-null — but then a
  **`RuntimeError: unreachable`** trap (wasm-function[166]) inside the
  first field's `setUnitAndName`. The stall is gone; a trap replaces it.
- **Trap narrowed (`out5`, `out6`):** finer prints in
  `Constant.setUnitAndName` and `ConstantManager.addConstant`: `putIfAbsent`
  works (`oldNull=true`); the trap is inside **`Main.getCli()`** — i.e.
  `Main` class static initialisation, called from `addConstant` ("Value set
  at CLI level?"). `Main.getCli()` just returns the static `cli` field;
  reading it triggers `Main` `<clinit>`.
- **Trap narrowed again (`out7`):** instrumented `Main.java` (static block
  restructured with prints): "DIAG Main 1 WellKnowns.ensureLoaded" prints,
  then the trap — inside **`WellKnowns` static init**
  (`ensureLoaded()` itself is empty; the call triggers `<clinit>`).
- **Trap narrowed again (`out8`):** instrumented `WellKnowns.java` (prints
  per field group): identity done, platform done
  (`FILE_SEPARATOR=/` from `System.getProperty("file.separator")` — works),
  classContainer done — then "DIAG WK folders" / `config=true data=true`
  (both null, as the patched `getFolder` returns null) and the trap.
  **The trap is at `DOC_FOLDER = DATA_FOLDER.resolve("www")` with
  `DATA_FOLDER == null`.** Under TeaVM WasmGC a null receiver on
  `Path.resolve` traps with `RuntimeError: unreachable`
  (wasm-function[166] is the innermost frame in every trap) instead of
  throwing NPE. Classification: **(a) spike-shim/patch defect** — the
  existing TEAVM patch in `make_patches.py` made `getFolder` return null
  but left the `.resolve(...)` call sites dereferencing null.

### 10.5 Durable fixes applied (in the spike, not the repo)

1. **`teavm/patched/make_patches.py` — WellKnowns section:**
   `DOC_FOLDER`, `EXAMPLES_FOLDER`, `TRAIN_FOLDER`, `TEMP_FOLDER` made
   null-safe (`(DATA_FOLDER == null)? null: DATA_FOLDER.resolve("www")`,
   etc., each marked `// TEAVM: getFolder null`); `createFolder` now
   returns early if `folder == null` (`// TEAVM: no user folders in
   WASM`). Verified after a `build.sh` re-run: patched `WellKnowns.java`
   contains the fixes (lines 159, 181, 231).
2. **Reflection policy, durably:**
   `teavm/policy/src/teavm/TeavmReflectionPolicy.java` — a **narrow**
   policy (not all-classes): `selectClasses(extending(
   "org.audiveris.omr.constant.ConstantSet")).reflectableFields(f -> true)`,
   `selectClass("org.audiveris.omr.WellKnowns").reflectableFields(f -> true)`,
   `selectClass("org.audiveris.omr.glyph.ShapeSet").reflectableFields(f -> true)`.
   Rationale: `getDeclaredFields` users in Audiveris are
   `ConstantSet.initMap` (critical), `WellKnowns.logDeclaredData`
   (trace-only, shim logger has trace disabled), `ShapeSet` (shape
   enumeration, used in SYMBOLS and beyond), plus `Dumper`/`Trimmable`
   (debugging utilities, probably not in the pipeline) and `BookBrowser`
   (UI, not headless); `getDeclaredConstructor().newInstance()` users are
   mostly UI plus `SIGraph`/`TremoloInter`/`RelationVector` (in-pipeline,
   constructor reflection — a separate metadata requirement, not yet
   tested). `Class.forName` is used in `UnitManager.preLoadUnits()` (not
   called in the headless path). Policy compiled by a new step 3 in
   `teavm/build.sh` (`javac -cp
   lib/teavm-extension-spi-0.16.0.jar:lib/teavm-extension-apis-0.16.0.jar`
   — the apis jar was needed because `IntrospectClass` lives there; first
   attempt with only the spi jar failed) into `teavm/policy-classes/`
   with `META-INF/services/...ReflectionPolicy` containing
   `teavm.TeavmReflectionPolicy`.
   `teavm-fork/teavm-main-jars-corepatch.txt` gained a `policy-classes`
   line (after `shims.jar`). Full `build.sh` re-run succeeds:
   `patched/classes OK: 261 classes`, `policy-classes OK: 1 classes`.
   The all-classes policy was used only for the diag tests; the durable
   policy is the narrow one above. The diag `AllReflectablePolicy` remains
   in `diag10/classes` only.

### 10.6 Clean full build — NEW FAILURE #15448 (same defect class as #21244, second block)

`Spike wasm-gc ../teavm-fork/full-out10 teavm.TeavmMain
@../teavm-fork/teavm-main-jars-corepatch.txt @program-jars.txt` — 0
problems, 2,867 classes, 27,697 methods. Node load test
(`load-test.mjs full-out10`) FAILS:
`CompileError: WebAssembly.compileStreaming(): Compiling function #15448
failed: type error in fallthru[0] (expected (ref 779), got (ref null 779))
@+4501749`.
This is the SAME error shape as #21244 (continuation block declares
non-null, fallthrough yields null). `DumpDebug` on
`full-out10/classes.wasm.teadbg` at offset 4501749 identifies function
#15448 as **`org.audiveris.omr.sheet.grid.LineCluster.getPointsAt`** —
the SAME method as #21244 (which was function #21244, type 780). Disassembly
(`fn15448.txt`, via `disasm2.py`; body found with a code-section parser —
defined fn #15389, body [4498693..4502134)): the failing block is at
4500170, `block typeidx(17778)`; its results are `[ref 779 (non-null),
ref null 747, ref null 1809]`, while the enclosing block type 12311
declares all-nullable results including `ref null 779`. Type 779 is the
`Map.Entry` struct (same as §7.4's 780 in the old build — numbering
shifted by one).

### 10.7 The missed push site — `processOptimizedBlock` / `processOptimizedConditional`

Reading `CoroutineTransformation.java` (fork `src/`): the generic
suspending-instruction path (line ~218) and `createRestoreInstructions`
(line ~368) already map frame types with `mapToNullableTypes(inputTypes)`,
but `processOptimizedBlock` (line ~258) and the two
`processOptimizedConditional` wrapper sites (lines ~276, ~300) build their
block signatures with **`List.copyOf(inputTypes)` raw** — the frame
variable types, which the analysis infers non-null for the `Map.Entry`
loop variable. The §9 `WasmTypeInference` patch fixed the type-stack side;
these three sites are the remaining un-mapped path, and they produce
exactly the failing block 17778 (results = the frame values).
Fix (3 lines, same principle — continuation block result types are the
join over incoming paths): replace `List.copyOf(inputTypes)` with
`mapToNullableTypes(inputTypes)` at those three sites. Patch saved as
**`teavm-core-21244b.patch`** (6 lines changed). The `params` side of
`processOptimizedBlock`'s signature (`typeInference.typeStack`) is already
nullable via the §9 inference patch, so it is left alone; the
conditional's `outputTypes` are likewise stack-derived.

### 10.8 The compiler-classpath correction — the §9 jar-patch procedure as documented does NOT affect the compiler

This was the expensive discovery of §10, and it corrects §9.4's record:

- `Spike` runs TeaVMTool from `-cp "lib/*:classes"` — stock
  `teavm/lib/teavm-core-0.16.0.jar` on the host JVM. The `@jars` files are
  the *program* classpath (classes compiled into the wasm).
  `CoroutineTransformation` / `WasmTypeInference` are instantiated with
  plain `new` from backend code, so they load from the **compiler**
  classpath, not the program classpath.
- Controlled experiment: `full-out11` (program classpath =
  `teavm-core-0.16.0-patched2.jar` with the §10.7 fix, compiler =
  stock) vs `full-out10`: **0 differing function bodies** (byte-identical
  size 10,476,328; `wasmdiff` over all 38,571 bodies) and the identical
  #15448 failure at the identical offset. The program-classpath core jar
  alone changes nothing in the output.
- `full-out13` (same program classpath as out11, but the Spike command
  run with the patched2 core jar **first** on the compiler classpath:
  `-cp "../teavm-fork/lib-fork/teavm-core-0.16.0-patched2.jar:lib/*:classes"`)
  — 0 problems, 2,867 classes, 27,697 methods — **LOADS OK in Node in
  1,037 ms** (`load-test.mjs full-out13`). The compiler classpath is the
  operative one.
- **Open discrepancy, stated honestly:** §9 reports that swapping the
  program-classpath core jar (stock → patched `WasmTypeInference`)
  changed 53 function bodies between `full-out4` and `full-out5` and made
  #21244 disappear — but the controlled out10/out11 experiment proves
  that exact change alters 0 bodies. The 53-body difference must have
  come from an unrecorded input difference for out4/out5 (the build logs
  do not record the Spike command line for those builds; both used the
  fork classlib per §7 line 342 and §9 line 667). It was not resolved in
  §10. What §10 proves: the §9 `WasmTypeInference` fix works when (and
  only when, in this setup) the patched core jar is on the **compiler**
  classpath; the `teavm-core-21244.patch` jar-patch procedure in §9.4
  should be read with that correction — the jar in `lib-fork/` must be
  placed first on the Spike `-cp`, not only substituted in the `@jars`
  file. (The §9 repro3 results are unaffected: they were built with the
  patched core and pass.)
- Durable artifacts for the core patch, second round:
  `teavm-core-21244b.patch`; `lib-fork/teavm-core-0.16.0-patched2.jar`
  (copy of the §9 patched jar with the four recompiled
  `CoroutineTransformation*.class` files replaced via `jar uf`; compiled
  with `javac --release 17` against the §9 patched jar, verified by
  `javap` — bytecode references `mapToNullableTypes` 7 times);
  `teavm-main-jars-corepatch2.txt` (copy of corepatch with only the core
  line changed); `corepatch-b/` (patched source + compiled classes).
  The §9 jar `teavm-core-0.16.0-patched.jar` is left intact.
  The canonical build command is now:
  `java -Xmx3g -cp "../teavm-fork/lib-fork/teavm-core-0.16.0-patched2.jar:lib/*:classes" Spike wasm-gc ../teavm-fork/full-outN teavm.TeavmMain @../teavm-fork/teavm-main-jars-corepatch2.txt @program-jars.txt`
  (run from `teavm/`).
- Determinism check: rebuilding out10's exact inputs as `full-out12`
  gives a byte-identical wasm (md5 `498381cedab545deb964dc803430dd7a`),
  so the out4/out5 difference is not build nondeterminism.

### 10.9 The stall is gone — run starts, then a fast CME in `restart()`

`full-out13` crop run (`run-crop.mjs full-out13`, 2480×700): IMAGE,
GREY BYTES, then `TEAVM FAILED: java.util.ConcurrentModificationException`
in 129 ms (Node does not crash; TeavmMain catches it). No STEP LOAD.
A diagnostic entry (`teavm/entry/src/teavm/TeavmMainDiag.java`, new file —
clean `TeavmMain.java` untouched; markers around each startup call)
built as `diag-out13` pins it: "DIAG pre-restart" prints,
"DIAG post-restart" never does. **The CME is inside
`OmrExecutors.restart()`** — i.e. in the static init that previously
spun, now completing far enough to throw.

Cause (read from the code, then confirmed by the fix): `UnitManager`
holds `dirtySets` as a `java.util.concurrent.ConcurrentSkipListSet`, and
`checkDirtySets()` iterates it while `initialize()` re-entrantly
registers another `ConstantSet` (`addSet` → `dirtySets.add(...)`). Real
`ConcurrentSkipListSet` has weakly consistent iterators and tolerates
that. The spike's shim `ConcurrentSkipListMap extends TreeMap`
(`teavm/shims/src/java/util/concurrent/ConcurrentSkipListMap.java`) hands
out TreeMap's **fail-fast** iterators, so the re-entrant add throws CME.
Classification: **(a) shim defect** — the shim violates the JDK
weakly-consistent-iterator contract for the concurrent collections.

Fix (contained, shim-side): the collection views of
`ConcurrentSkipListMap` now iterate over a snapshot taken at
`iterator()` time, while `iterator.remove()` still removes from the live
map — snapshot-iteration + live-remove is the faithful single-threaded
emulation of weakly consistent iteration. Implemented in
`teavm/shims/src/java/util/concurrent/ConcurrentSkipListMap.java`
(`SnapIterator`, `SnapSet`, `SnapCollection`, `SnapNavSet`, plus a
values-iterator that snapshots entries and removes by entry key).
`ConcurrentSkipListSet.iterator()` needed no change — it delegates to
`map.navigableKeySet().iterator()`. Rebuilt via `build.sh`
(`shims.jar OK: 295,404 bytes`, `patched/classes OK: 262 classes`).
Note: an intermediate build failed to compile the shim (missing
`java.util.SortedSet` import, lines 133–135) and a Spike build run in the
same shell command against the stale `shims.jar` produced a
`full-out14` that was discarded and rebuilt — the stale artifact was not
used for any verdict.

### 10.10 Result after the CME fix — loads, starts, then a null-pointer trap in `new Book`

`full-out14` (clean entry, new shims, compiler-cp patched2): 0 problems,
2,872 classes (+5: the new shim inner classes), 27,736 methods,
**LOADS OK in 343 ms**. Crop run (`run-crop.mjs full-out14`):
```
IMAGE w=2480 h=700
GREY BYTES 1736000
RuntimeError: dereferencing a null pointer
    at wasm://wasm/027fb972:wasm-function[84]:0xf0a83
```
Node crashes (a wasm trap, not a Java exception, so TeavmMain's catch
does not catch it). The diag entry rebuilt with the new shims
(`diag-out14`) names the place:
```
DIAG pre-restart
DIAG post-restart
DIAG pre-book
RuntimeError: dereferencing a null pointer
```
**The trap is inside `new Book(Paths.get("hymn-satb.png"))`** — restart()
now completes, Book construction traps. (The V8 trap pcs
(`wasm-function[84]:0xf0a83`, etc.) could not be mapped reliably to Java
methods with the available tools — both the file-offset and the
code-section-relative interpretations of the offsets give incoherent
method chains through `DumpDebug`, so no method name is claimed for the
innermost frame; the call-level localisation above is the reliable
evidence.) The full-page run was not attempted: the crop already traps
before STEP LOAD, so a full page cannot reach HEADS either. **No WasmGC
timing and no HEADS count exist.**

### 10.11 Verdict: PARTIAL — the stall is fixed, the run gets further, stopped at the next failure

- The §10 task's stall is **diagnosed and fixed**: root cause was
  `getDeclaredFields()` returning 0 fields under TeaVM (no reflection
  metadata without a `ReflectionPolicy`), which made
  `Constant.checkInitialized()` busy-spin forever; fixed durably with a
  narrow reflection policy + a WellKnowns null-safety patch.
- Along the way, two further blockers were found and fixed with contained
  changes: the second #21244-class continuation block in
  `LineCluster.getPointsAt` (core patch `teavm-core-21244b.patch`, applied
  on the **compiler** classpath — §10.8 corrects §9.4 on this point) and
  the `ConcurrentSkipListMap` fail-fast-iterator CME (snapshot-iterator
  shim fix).
- The run now loads in ~0.3–1.0 s, passes `OmrExecutors.restart()`, and
  traps with a null-pointer dereference inside `new Book(...)` before
  STEP LOAD. CheerpJ 5 remains the only working option. Next step if the
  exit is still wanted: instrument `Book.<init>` (its first touches —
  likely a static init or a null `Path`/folder dereference in the same
  family as the WellKnowns trap) with the `TeavmMainDiag` pattern, one
  print per call, until the trapping call is named; then decide shim fix
  vs Audiveris-side change. Do not file #15448 against TeaVM separately
  yet — it is the same defect class as #21244, and the candidate upstream
  fix is now the two-part core patch (`teavm-core-21244.patch` +
  `teavm-core-21244b.patch`); file them together with the #21244 issue
  when the time comes, noting the compiler-classpath build route.

### 10.12 Files added/changed in §10

- `teavm-core-21244b.patch` — CoroutineTransformation fix (3 sites).
- `lib-fork/teavm-core-0.16.0-patched2.jar` — §9 patched jar +
  recompiled `CoroutineTransformation*.class`; source patch is the
  durable artifact.
- `teavm-main-jars-corepatch2.txt` — program classpath pointing at the
  patched2 core jar.
- `corepatch-b/` — patched `CoroutineTransformation.java` + compiled
  classes used for the jar patch.
- `teavm/policy/src/teavm/TeavmReflectionPolicy.java` + step 3 in
  `teavm/build.sh` + `teavm/policy-classes/` — narrow reflection policy
  (ConstantSet / WellKnowns / ShapeSet fields).
- `teavm/patched/make_patches.py` — WellKnowns null-safe folders
  (durably in the patch generator; verified in regenerated
  `patched/src`).
- `teavm/shims/src/java/util/concurrent/ConcurrentSkipListMap.java` —
  snapshot-iterator views (fail-fast → weakly consistent).
- `teavm/entry/src/teavm/TeavmMainDiag.java` — diagnostic entry with
  startup markers (clean `TeavmMain.java` untouched).
- `full-out10/`, `full-out11/`, `full-out12/`, `full-out13/`,
  `full-out14/`, `diag-out13/`, `diag-out14/` + `full-build10.log`…
  `full-build14.log`, `full-build-diag13.log` — builds
  (out10: #15448; out11: same, program-cp-only change, 0 body diff;
  out12: byte-identical rebuild of out10; out13: LOADS, CME in restart;
  out14: LOADS, null-pointer trap in `new Book`).
- `diag10/` — all §10.1–10.4 instrumentation (sources, `out`,
  `out2`–`out8`, `out-refl`, `out-refl2`, `run-diag*.log`,
  `run-refl*.log`, `build-diag*.log`); `run-crop14.log`,
  `run-crop-diag14.log` — the trap runs.
- `fn15448.txt` — disassembly of `LineCluster.getPointsAt` in full-out10
  (failing block at file offset 4501749, block type 17778).
- New tools (in `/tmp`, not durable — recreate from §10.6/§10.8 if
  needed): a code-section body parser (`fnbody2.py`/`fnfind.py`,
  `defn_off.py`, `fnmap.py`) and a wasm body-diff script (`wasmdiff.py`).
  The 578 MB `teavm/fn272/classes.wat` scratch file from §7 is still
  sitting in `teavm/fn272/` and is worth deleting.
- Nothing was pushed, filed, or merged; `jdlehman/score-reader` untouched.
  `lib-fork/teavm-main-jars-corepatch.txt` (0 bytes, stray empty file) is
  not the real jars file — the real one is `teavm-fork/teavm-main-jars-corepatch.txt`.

## 11. Instrumenting Book.<init> — trapping calls named and fixed; stopped at Main.getCli() null — 2026-11-09 (PARTIAL, stopped at the next failure per the task's stop rule)

Task: instrument `Book.<init>` with the `TeavmMainDiag` pattern (one print
per call / per field touched, diagnostic copies only, in
`~/workspace/score-reader-spikes/teavm-wasm/`), run on the hymn crop
(2480×700, `teavm-fork/hymn-crop.gray`) first, name the trapping call,
classify it, fix it if a contained shim/classlib defect, rebuild, re-run.
Stop rule (as in §10): if the run still traps at a new place, name that
place and stop — no new open-ended iteration.

State at the start of §11: `full-out14` (0 problems, 2,872 classes) LOADS
OK in Node in 343 ms, passes `OmrExecutors.restart()`, then traps with
`RuntimeError: dereferencing a null pointer` inside
`new Book(Paths.get("hymn-satb.png"))` — diag entry showed `DIAG
post-restart` then `DIAG pre-book`, no `post-book`, no STEP LOAD. V8 trap
PCs unmappable (see §11.6).

### 11.1 Instrumentation method

Diagnostic copies only, in `teavm-fork/diag11/` — `jdlehman/score-reader`
and the repo's Audiveris sources untouched. New entry
`TeavmMainDiag11.java` (splits `Paths.get` from `new Book`, prints around
each). Generators copy the repo file and insert prints by exact-string
replacement (fail loudly if not found):
`make_diag_book.py` (Book.java: static-init block, ctor around
`requireNonNull` / `FileUtil.getNameSansExtension` / `initTransients`,
`initTransients` / `initParameters` / `setParamParents` / `checkAlias` /
`getStubsToUpgrade` / `getStubsWithTableFiles`), `make_diag_params.py`
(Params.java), `make_diag_profiles.py` (Profiles.java),
`make_diag_constantset.py` (ConstantSet.java — not in `teavm/patched/src`,
comes from `audiveris.jar`), `make_diag_alias.py` (AliasPatterns.java),
`make_diag_bookmanager.py` (BookManager.java: static fields restructured
into a static block, LazySingleton holder given a static block, field
initialisers moved into the ctor body so prints bracket
`LinkedHashMap` / `new AliasPatterns()`).
Diagnostic copies compile into `diag11/classes`, first on the program
classpath via `diag11/diag11-jars.txt` (= `diag11/classes` +
`teavm-main-jars-corepatch2.txt` contents). Builds use the canonical
command from §10 (patched2 core jar FIRST on the compiler classpath).
All builds 0 problems, 2,872 classes, 27,736 methods. Crop runs use a
60 s timeout; a null-pointer trap crashes Node fast.

### 11.2 Round 1–4: the Profiles / ConstantSet trap (FIXED)

- Round 1 (`out11`, `run-crop11.log`): `Paths.get` is FINE
  (`paths=hymn-satb.png`). Book clinit completes, ctor completes through
  `getNameSansExtension` (`nameSansExt=hymn-satb`), `initParameters`
  completes twice, then the trap inside
  `parameters.setParents(null)` in `Book.setParamParents` — last print
  `setParamParents 2 setParents`. `Param.setParent` is a trivial
  assignment, so the trap is in evaluating one of the nine static
  defaults in `BookParams.setParents`.
- Round 2 (`out11b`, `run-crop11b.log`, instrumented copy of repo
  `Params.java`): prints per default — 1 musicFamily done, 2 textFamily
  done, 3 inputQuality printed, then trap — i.e. in
  `inputQuality.setParent(Profiles.defaultQualityParam)`, evaluating
  `Profiles.defaultQualityParam` (`Profiles` `<clinit>`).
- Round 3 (`out11c`, `run-crop11c.log`, instrumented copy of repo
  `Profiles.java`): `Profiles clinit 1 new Constants` prints, then trap
  — inside `new Constants()` for Profiles, before the ctor-body print,
  i.e. in the superclass `ConstantSet()` ctor. `Profiles.Constants`
  holds a single field, `Constant.Enum<InputQuality> defaultQuality`.
  (MusicFont/TextFont `Constants` also hold `Constant.Enum` fields and
  survived, so the Enum ctor is not the trap per se.)
- Round 4 (`out11d`, `run-crop11d.log`, instrumented copy of repo
  `ConstantSet.java`): `ConstantSet()` has only two statements:
  `unit = getClass().getDeclaringClass().getName();` and
  `UnitManager.getInstance().addSet(this)`. For `Profiles$Constants`:
  ctor 1 `class=org.audiveris.omr.sheet.Profiles$Constants`, ctor 2
  `declaringClass=javaClass@557968442` (non-null), ctor 3 **`unit=null`**
  — `dc.getName()` returned null — ctor 4 `addSet`, then the trap
  (addSet calls `set.getName()` = null → `retrieveUnit(null)` → null
  deref). For every other `Constants` class in the same run (Book,
  MusicFont, TextFont, OmrFont, UIUtil, …) `unit` is a proper name.
  **Trapping call, named at the mechanism level:
  `Class.getName()` returns null for
  `org.audiveris.omr.sheet.Profiles` under TeaVM WasmGC.**

Why the name is null: `TClass.getName()` (fork source
`classlib/.../TClass.java:97`) returns `classInfo.name()` — the metadata
name string — or null if that metadata is null (falling back only for
array types). TeaVM generates class-name metadata only for types that
flow into a `Class.getName()` call site: `ClassMetadataRequirements`
(fork source `core/.../ClassMetadataRequirements.java:77-83`) records
`getName()`'s variable-0 types as requiring `name`. `Profiles` is
reached only via `getDeclaringClass()` and evidently never flows into a
`getName()` receiver in the analysed program, so no name metadata is
generated for it — while `Book`, `MusicFont`, `TextFont`, `OmrFont`,
`UIUtil`, etc. do get it. The diag print proves the asymmetry directly:
`getClass().getName()` works for the nested `Profiles$Constants` class
itself (ctor 1 prints its full name); only the *declaring* class's name
is null. Classification: **(b) TeaVM metadata-generation gap**
(`getName()` on a legitimate class returns null, violating the JDK
contract) — a genuine TeaVM defect of the same family as #272 (classlib
type metadata incomplete for a JDK-legal program), but with a contained
spike-side workaround (below). A proper upstream fix would be in
`ClassMetadataRequirements` (e.g. when `getDeclaringClass` metadata is
required, also require the name of the declaring class); that was not
attempted here.

Fix (tested in the diag copy first, then made durable): in
`ConstantSet()` derive the unit name from the nested class's own name
when the declaring class's `getName()` is null —
`"a.b.C$Constants" -> "a.b.C"`. Durable patch in
`teavm/patched/make_patches.py` (new FILES[8],
`org/audiveris/omr/constant/ConstantSet.java`, `replace_method` on the
ctor, marked `TEAVM §11`). On the desktop `dc.getName()` is never null,
so behaviour is unchanged there — the patch is upstream-safe in
semantics.

### 11.3 Round 5: the fix works — setParents completes; next trap is BookManager$Constants (FIXED)

`out11e` (`run-crop11e.log`): `Profiles$Constants` now derives
`unit=org.audiveris.omr.sheet.Profiles`, `setParents` 1–10 all complete,
`setParamParents` done, `checkAlias` 1–3 done, then a new trap — last
print `checkAlias 3 getInstance` (+ `BookManager$Constants` ctor done).
`loadAliasPatterns` was the first suspect (`AliasPatterns.getAlias` →
`getPatterns()` → `loadAliasPatterns()` → first line
`WellKnowns.CONFIG_FOLDER.resolve(...)`, `CONFIG_FOLDER` null under the
TeaVM WellKnowns patch), but round 6 (`out11f`, instrumented copy of
`AliasPatterns.java`, `run-crop11f.log`) shows `loadAliasPatterns 1`
never prints — the trap is *before* it, inside `BookManager.getInstance()`
itself.

Round 7 (`out11g`, instrumented copy of `BookManager.java`,
`run-crop11g.log`): `BookManager clinit 1 constants` prints,
`BookManager$Constants` ctor prints complete (ctor 1–5 done), then the
trap before `clinit 2 constants done` — i.e. inside the Constants
*class* field initialisers, after the `ConstantSet` super-ctor returns.
`BookManager$Constants` has three fields dereferencing WellKnowns
folders, first in textual order `baseFolder`:
`WellKnowns.DEFAULT_BASE_FOLDER.toString()` (`defaultBookFolder` the
same, `defaultImageFolder` uses `EXAMPLES_FOLDER.toString()`), and
`DEFAULT_BASE_FOLDER` / `EXAMPLES_FOLDER` are null in WASM (`getFolder`
returns null). **Trapping call: `BookManager$Constants.baseFolder`,
`WellKnowns.DEFAULT_BASE_FOLDER.toString()` with
`DEFAULT_BASE_FOLDER == null`.** Classification: **(a) spike-patch
defect** — the §10.4 WellKnowns patch made folders null without
null-proofing all use sites (same family as the §10.4 `DOC_FOLDER`
trap). Contained fix, same pattern as §10.4, made durable in
`teavm/patched/make_patches.py` (new FILES[9], `BookManager.java`):
the three folder defaults become null-safe ternaries (`... == null ?
"" : ...toString()`, `/* TEAVM §11 */` block comments — a `//` comment
would eat the rest of the argument line; and plain `replace()` is used
for the two `DEFAULT_BASE_FOLDER` sites because `sub()` re-matches
inside its own replacement).

The `AliasPatterns.loadAliasPatterns` trap identified in round 5 is real
and one step later in the same init path (its URI array is built outside
the `IOException` catch, so a null `CONFIG_FOLDER` traps before any
catch), so it was fixed in the same round, durably in
`make_patches.py` (new FILES[10], `AliasPatterns.java`): the URI list is
built only from whichever of `CONFIG_FOLDER` / `RES_URI` is non-null
(both are null in WASM, so the patterns list comes back empty — correct
there, since no patterns file exists in the WASM environment).

Build note: the first `build.sh` re-run after adding these sections
failed twice in `make_patches.py` itself — `sub_all` is defined in the
ROUND 2 part of the file, after the ROUND 1 sections (NameError), then
a `//` comment eating an argument line plus a double-wrapped ternary
from the second `sub()` call (see above). Both were script bugs, fixed
in the script; `build.sh` then passed (`patched/classes OK: 269
classes`, `BUILD OK`). `make_patches.py` re-reads from the repo on every
run, so no corrupted output persisted.

### 11.4 Clean build full-out15 — past BookManager/AliasPatterns, stopped at Main.getCli() null

`full-out15` (clean `TeavmMain` entry, canonical command, 0 problems,
2,872 classes, 27,736 methods, `classes.wasm` 10,483,352 bytes)
**LOADS OK in Node in 348 ms**. Crop run
(`run-crop15.log`): `IMAGE w=2480 h=700`, `GREY BYTES 1736000`, then
`RuntimeError: dereferencing a null pointer` — innermost frame now
`wasm-function[20726]` (was `[17283]` at the BookManager trap), outer
frames `[22382][21154][20964][19488][17727][16468]` unchanged (the
Book-path frames). No STEP LOAD.

Localisation run (`out11h`, `run-crop11h.log`): the diag `BookManager` /
`AliasPatterns` / `ConstantSet` copies were stale shadows of the now-fixed
patched classes, so they were removed from `diag11/src` (the generators
remain but their outputs are no longer compiled; `diag11/src` now holds
only `Book` / `Params` / `Profiles` / `TeavmMainDiag11`). Last prints:
`checkAlias 4 getAlias`, `initTransients 3b alias=null`,
`initTransients 4 getStubsToUpgrade`, `getStubsToUpgrade 1 oldVersion`,
`getStubsToUpgrade 2 tableFiles`, `tableFiles 1 lock`,
`tableFiles 2 getDefaultSavePath` — then the trap, same innermost frame
`[20726]` as the clean run, confirming the same place. **Trapping call,
named: `Book.getStubsToUpgrade` → `Book.getStubsWithTableFiles` →
`BookManager.getDefaultSavePath(this)` →
`BookManager.getDefaultBookFolder(Book)` →
`Main.getCli().getOutputFolder()` with `Main.getCli() == null`.**
`Book.getBookPath()` is null for a fresh in-memory book, so
`getDefaultSavePath` falls through to `getDefaultBookFolder(book)`,
whose first expression dereferences the null CLI. (The fallback branch
would also be a problem: `useInputBookFolder` defaults true, and the
input path `hymn-satb.png` has a null parent.) Classification: **(c)
Audiveris code assuming a CLI exists, in a headless path TeaVM runs
without one** — the same `Main.getCli() == null` family already patched
once in `SheetStub` (round 1). NOT fixed in §11, per the stop rule.

Concrete next step (proposed, not applied): the most contained fix is
in `Book.getStubsToUpgrade` (patched copy in `make_patches.py`): return
an empty set under TeaVM — no saved `.omr` book project can exist in
the WASM environment, so "no stubs to upgrade" is semantically correct
for a fresh in-memory book, and it avoids the whole save-path chain.
Alternative: null-guard `Main.getCli()` in
`BookManager.getDefaultBookFolder(Book)` (same pattern as the SheetStub
patch) and make the fallback return a dummy non-null folder — but that
only moves the problem to the next `getDefaultBookFolder` caller
(`getDefaultExportPathSansExt`, `getDefaultPrintPathSansExt`, and the
export path at the end of a successful read), so expect further
`Main.getCli()` / folder traps after it. Either way the fix belongs in
`make_patches.py`, not in the TeaVM fork.

### 11.5 Verdict: PARTIAL — Book.<init>'s first trap fixed, run gets further, stopped at the next failure

- The §11 task's trapping call is **named and fixed**: `Profiles`
  had no `getName()` metadata under TeaVM (metadata-generation gap,
  class (b)), fixed with a contained, desktop-neutral derivation in
  `ConstantSet` (durable in `make_patches.py`).
- Two further same-family blockers were found and fixed in the same
  bounded round: `BookManager$Constants` folder defaults and
  `AliasPatterns.loadAliasPatterns` (both null WellKnowns folders,
  class (a)).
- The run now loads in ~0.35 s, passes restart, passes `Book` static
  init, `initParameters`, `setParamParents` (all 9 defaults) and
  `checkAlias`, and traps in `Book.initTransients` →
  `getStubsToUpgrade` → `getDefaultSavePath` on `Main.getCli() == null`
  (class (c)). **No STEP LOAD, no WasmGC timing, no HEADS count exist.**
  CheerpJ 5 remains the only working option. Do not file the
  `Profiles.getName()` gap against TeaVM separately yet — it is a
  metadata-generation gap worth one issue together with the #21244 /
  #15448 core patches when the time comes (see §10.11); the
  `BookManager` / `AliasPatterns` traps are spike-patch issues, not
  TeaVM defects, and `Main.getCli()` null is an Audiveris-side
  headless-path gap.

### 11.6 V8 trap PCs — still unmappable

As in §10.10, the trap PCs could not be mapped reliably to Java methods
with the available tools. The innermost frame index changed with the
trap site (`[84]` §10 → `[17283]` BookManager trap → `[20726]`
getDefaultSavePath trap), and the same `[20726]` appears in both the
clean `full-out15` run and the instrumented `out11h` run, which
corroborates the print-order localisation — but no method name is
claimed from the PCs themselves. Print order remains the reliable path.

### 11.7 Files added/changed in §11

- `teavm/patched/make_patches.py` — three new patched files (FILES[8–10]):
  `ConstantSet.java` (unit-name derivation), `BookManager.java`
  (null-safe folder defaults), `AliasPatterns.java` (null-safe URI
  list). Docstring header updated. This is the durable artifact for all
  three fixes; `teavm/patched/src/` is regenerated from it by
  `build.sh`.
- `teavm-fork/diag11/` — `TeavmMainDiag11.java`,
  `make_diag_book.py`, `make_diag_params.py`, `make_diag_profiles.py`,
  `make_diag_constantset.py`, `make_diag_alias.py`,
  `make_diag_bookmanager.py`; `diag11-jars.txt`; `out11`, `out11b`,
  `out11c`, `out11d`, `out11e`, `out11f`, `out11g`, `out11h` +
  `full-build11*.log`, `run-crop11*.log`, `build-diag11*.log`.
  `diag11/src` now contains only `Book` / `Params` / `Profiles` /
  `TeavmMainDiag11` (the `ConstantSet` / `BookManager` / `AliasPatterns`
  diag copies were deleted once the durable patches landed, so the
  fixed `patched/classes` versions are used).
- `full-out15/` + `full-build15.log` + `run-crop15.log` + `build15.log`
  — clean build with all three §11 fixes (LOADS OK 348 ms, traps in
  `getDefaultSavePath`).
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched. `full-out15/classes.wasm` is 10,483,352 bytes (vs
  10,203,503 for full-out6 — the three newly patched files and their
  extra methods account for the growth; build log re-verified: 0
  problems, 2,872 classes, 27,736 methods, fresh `Spike` run).
## 12. Book.getStubsToUpgrade returns empty for a fresh book — STEP LOAD reached; three same-family blockers fixed, stopped at BufferedImage.getRGB illegal cast — 2026-11-09 (PARTIAL, stopped at the next failure per the task's stop rule)

Task: apply the §11-proposed fix (make `Book.getStubsToUpgrade` return an
empty set under TeaVM), rebuild, re-run TeavmMain on the hymn crop first
(then the full page if the crop passes STEP LOAD). If a new trap is a
contained shim/classlib fix in the same family (null folder/path, missing
exception, reflection metadata), apply it in the same bounded round and
re-run; otherwise name it and stop.

State at the start of §12: `full-out15` (0 problems, 2,872 classes,
27,736 methods) LOADS OK in Node in 348 ms, passes restart() and Book
init through checkAlias, then traps in `Book.getStubsToUpgrade` →
`getStubsWithTableFiles` → `BookManager.getDefaultSavePath` →
`getDefaultBookFolder(Book)` → `Main.getCli().getOutputFolder()` with
`Main.getCli() == null`. No STEP LOAD, no WasmGC timing, no HEADS count.

### 12.1 The §12 fix — getStubsToUpgrade (in make_patches.py, durable)

Applied in `teavm/patched/make_patches.py`, in the Round 4 "Book: neuter
save/export/JAXB/PDFBox methods" section (`read_out` + `replace_method_re`,
same pattern as the neighbouring `storeBookInfo` / `reachBookStep`
replacements), plus a header entry in the module docstring. The repo is
untouched: `make_patches.py` only reads the repo clone, and the clone's
`Book.java` modifications are the user's own pre-existing patches
(`scorereader.keepSheets`, `skipFailedPages`, mtime 2026-11-08 14:04 UTC)
— verified via `git diff`, which shows none of this §12 change.

New body (patched copy only):

```java
public Set<SheetStub> getStubsToUpgrade ()
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
            // ... (original logging, unchanged)
        }
    }
    return stubsToUpgrade;
}
```

Deliberately NOT a null-guard on `Main.getCli()` in
`getDefaultBookFolder` (that only moves the trap to the next caller, as
§11.4 notes).

Desktop-neutrality, verified from the repo source rather than asserted:
- `Book(Path inputPath)` (Book.java:326) sets only `this.path`; `bookPath`
  is set only when a book is loaded from / stored to an `.omr` project
  (lines 1569, 2258, 2549). So `getBookPath() == null` exactly for a
  fresh in-memory book — including TeavmMain's
  `new Book(Paths.get("hymn-satb.png"))`.
- For such a book the original logic would return an empty set anyway:
  `version` defaults to `WellKnowns.TOOL_REF` (current) when null
  (Book.java:1580), so `getStubsWithOldVersion()` finds no upgrade
  versions newer than the book; and `getStubsWithTableFiles()` returns
  empty when no project file exists — it just traps before it can check,
  in `getDefaultSavePath`.
- Books loaded from a project (`bookPath != null`) run the original
  logic unchanged. So on the desktop this method behaves exactly as
  before. (The patch lives only in the spike's `make_patches.py` in any
  case — desktop Audiveris never sees it.)

Cosmetic note: as with the other `replace_method` / `replace_method_re`
replacements in this file (e.g. `ConstantSet`, §11), the replaced method
signature carries an extra 4 spaces of indent (8 total) because the
replacement text starts with its own indent after the original one.
Compiles fine; not fixed, to stay consistent with the file's existing
outputs.

### 12.2 Run full-out16 — STEP LOAD reached; new trap in FilamentFactory

`build.sh` re-run (`build16.log`: `patched/classes OK: 269 classes`,
BUILD OK). `full-out16` (canonical command, 0 problems, 2,872 classes,
27,736 methods, `classes.wasm` 10,483,503 bytes) **LOADS OK in Node in
370 ms** (`load-out16.log`). Crop run (`run-crop16.log`, 60 s timeout):

```
IMAGE w=2480 h=700
GREY BYTES 1736000
INFO [ScaleBuilder] ... Scale{ interline(21,21,22) line(2,2,4) beam(10)}
ERROR [org.audiveris.omr.glyph.dynamic.FilamentFactory] null <java.lang.NoSuchMethodException>
RuntimeError: dereferencing a null pointer
    at wasm-function[4643] ...
```

The getStubsToUpgrade fix works: the run passes Book init, reaches
**STEP LOAD for the first time**, completes **SCALE**
(`Scale{ interline(21,21,22) line(2,2,4) beam(10)}`), and traps in the
**GRID** step. The ERROR line names the place: `FilamentFactory`'s ctor
does `filamentClass.getConstructor(int.class)` (FilamentFactory.java:143)
inside a try/catch that logs the exception and leaves
`filamentConstructor` null; `createFilament` (line 405) then calls
`filamentConstructor.newInstance(...)` on the null field and traps.
Classification: **(b) TeaVM reflection-metadata gap**, same family as
the §11 `Profiles.getName()` gap — with no ReflectionPolicy entry, no
constructor metadata is generated for the class, so `getConstructor`
throws.

### 12.3 Fix — filament constructors in the ReflectionPolicy (FIXED)

Mechanism verified in the TeaVM fork source before patching (not
assumed from the symptom):
- `TClass.getDeclaredConstructors()` returns an empty array when
  `classInfo.reflection()` is null, and `getConstructor(int.class)` then
  throws `TNoSuchMethodException` (classlib `TClass.java:324-368`).
- `ClassMetadataRequirements` treats `getDeclaredConstructors` usage as
  `hasGetMethods`, so constructor metadata rides on the same reflection
  metadata as methods.
- `IntrospectClassImpl.declaredMethods()` includes everything except
  `<clinit>` — so `<init>` constructors ARE `IntrospectMethod`s, and
  `SimpleReflectionPolicy.classAccessibleMembers` (which iterates
  declared fields + declared methods) can surface them via
  `reflectableMethods(...)`; `DefaultReflectionSupplier.fillMembers`
  adds `IntrospectMethodImpl` members to the reflection method set.

Fix (in `teavm/policy/src/teavm/TeavmReflectionPolicy.java`, compiled by
`build.sh` step 3 into `policy-classes`, same durable route as §10):

```java
selectClass("org.audiveris.omr.sheet.grid.StaffFilament")
        .reflectableMethods(named("<init>"));
selectClass("org.audiveris.omr.glyph.dynamic.StraightFilament")
        .reflectableMethods(named("<init>"));
```

`StaffFilament(int)` is the first factory built (LinesRetriever, GRID;
its javadoc says the ctor exists precisely for FilamentFactory's
reflective `newInstance`); `StraightFilament(int)` is the second
(LeggedIntersBuilder, CURVES step). `CurvedFilament` is NOT a
FilamentFactory target — its ctor takes two ints, so
`getConstructor(int.class)` could never find it — and is not listed.
(Only two `new FilamentFactory` sites exist in the app.)

### 12.4 Run full-out17 — FilamentFactory error gone; new trap in Path2D.append

`full-out17` (0 problems, 2,876 classes, 27,746 methods, `classes.wasm`
10,529,724 bytes) **LOADS OK in 399 ms**. Crop run (`run-crop17.log`):
SCALE completes as before, the `FilamentFactory` ERROR line is **gone**,
and the run traps at a new place, innermost frame `[1581]`.

PC mapping (DumpSeq on `full-out17/classes.wasm.teadbg`, module-offset
interpretation — see §12.9 on why this is trusted here): 9 of 10 frames
form a coherent call chain, corroborated by call edges in the repo
source:

| frame | method (DumpSeq) |
|---|---|
| [1581] innermost | `java.awt.geom.Path2D.append` |
| [2931] | `org.audiveris.omr.math.NaturalSpline.<init>` |
| [17841] | `NaturalSpline.interpolate` |
| [2112] | `NaturalSpline.interpolate` (Collection → array overload) |
| [3405] | `org.audiveris.omr.glyph.dynamic.CurvedFilament.computeLine` |
| [8165] | unmapped (no containing sequence in a 500k window) |
| [2485] | `Filament.getStartPoint` |
| [4670] | `FilamentFactory.canMerge` |
| [4418] | `FilamentFactory.mergeFilaments` |
| [15048] | `FilamentFactory.retrieveFilaments` |

Mechanism, read from the sources: `NaturalSpline.interpolate(double[],
double[])` builds a `QuadCurve2D.Double` for the 3-point case (n == 2),
`new NaturalSpline(curves)` appends each shape via
`Path2D.append(shape, true)` → `s.getPathIterator(null)` → `it.isDone()`.
The spike's shim `QuadCurve2D.getPathIterator` (both overloads) **returns
null** — the only shape iterator in the geom shims that does so (besides
`RectangularShape`, see §12.9). `Line2D` and `CubicCurve2D` iterators are
implemented; the quad case was left as a stub. Classification: **(a)
shim defect** — a stub method returning null where the JDK contract
requires an iterator.

### 12.5 Fix — QuadIterator in the QuadCurve2D shim (FIXED)

Implemented `QuadIterator` in
`teavm/shims/src/java/awt/geom/QuadCurve2D.java`, mirroring the existing
`CubicIterator` in `CubicCurve2D.java` exactly (MOVETO with (x1, y1),
then QUADTO with (ctrlx, ctrly, x2, y2); AffineTransform applied when
non-null; `isDone()` after segment 1). Both `getPathIterator`
overloads now return `new QuadIterator(this, at)` /
`getPathIterator(at)`.

### 12.6 Run full-out18 — past GRID line retrieval; new trap in Raster.<init>

`full-out18` (0 problems, 2,877 classes, 27,752 methods, `classes.wasm`
10,531,089 bytes) **LOADS OK in 337 ms**. Crop run (`run-crop18.log`):
SCALE completes, then GRID progresses visibly —

```
INFO [LinesRetriever] Global slope: 0.00000
INFO [ClustersRetriever] Retrieved raw line clusters: 2 of sizes [5] with interline(21,21,22)
INFO [PeakGraph] Systems: #1[1, 2]
```

— then traps, innermost frame `[17953]`. PC mapping (same method):

| frame | method |
|---|---|
| [17953] innermost | `java.awt.image.Raster.<init>` |
| [2138] | `WritableRaster.<init>` |
| [1446] | `Raster.createWritableRaster` |
| [3583] | `ij.process.ByteProcessor.createBufferedImage` |
| [3555] | `ij.process.ByteProcessor.createImage` |
| [9233] | unmapped |
| [3559] | `ij.process.ByteProcessor.getBufferedImage` |
| [9237] | unmapped |
| [17114] | `org.audiveris.omr.sheet.Picture.buildNoStaffBuffer` |
| [13575] | `org.audiveris.omr.sheet.Picture.getSource` |

Mechanism, proven with `javap -c` on the real ImageJ jar (not guessed):
`ByteProcessor.createBufferedImage()` does `Raster.createWritableRaster(
getIndexSampleModel(), new DataBufferByte(pixels, w*h, 0), null)` — the
third argument is `aconst_null` (bytecode offset 37). The shim's
`Raster.createWritableRaster` passes the null origin straight to
`new WritableRaster(sm, db, origin)` → `Raster(sm, db, origin)` →
`new Rectangle(origin.x, ...)` → trap on the null origin. The real JDK
defaults a null origin to `(0,0)` in `createWritableRaster`; the shim
did not. Classification: **(a) shim defect** — the shim does not mirror
the JDK's null tolerance.

### 12.7 Fix — null origin default in Raster.createWritableRaster (FIXED)

In `teavm/shims/src/java/awt/image/Raster.java`:

```java
public static WritableRaster createWritableRaster(SampleModel sm, DataBuffer db, Point origin) {
    // TEAVM §12: mirror the JDK, which defaults a null origin to (0,0). ...
    if (origin == null) {
        origin = new Point(0, 0);
    }
    return new WritableRaster(sm, db, origin);
}
```

Note: the sibling factory methods (`createInterleavedRaster`,
`createBandedRaster`) take an explicit `Point location` and do not
null-check it either; the JDK versions do the same defaulting. They
have not trapped yet — recorded here as the same family, to fix if one
does.

### 12.8 Run full-out19 — past Raster; new failure: illegal cast in BufferedImage.getRGB (STOPPING POINT)

`full-out19` (0 problems, 2,877 classes, 27,752 methods, `classes.wasm`
10,531,125 bytes) **LOADS OK in 356 ms**. Crop run (`run-crop19.log`):
SCALE, LinesRetriever, ClustersRetriever and PeakGraph as in full-out18,
then a **new error shape** — `RuntimeError: illegal cast` (not a
null-pointer trap), innermost frame `[3620]`. PC mapping:

| frame | method |
|---|---|
| [3620] innermost | `java.awt.image.BufferedImage.getRGB` |
| [24255] | `BufferedImageGraphics.drawImage` |
| [24256] | unmapped |
| [3559] | `ij.process.ByteProcessor.getBufferedImage` |
| [9237] | unmapped |
| [17114] | `Picture.buildNoStaffBuffer` |
| [13575] | `Picture.getSource` |
| [13582] | `Picture.buildNoStaffTable` |
| [13691] | `LagManager.rebuildHLag` |
| [14895] | `StaffLineCleaner.process` (GRID step) |

Mechanism, read from the shim source: `BufferedImage.getRGB(int, int)`
branches on `imageType` — BYTE_GRAY / BYTE_BINARY / BYTE_INDEXED take
the sample path, everything else does
`((DataBufferInt) raster.getDataBuffer()).getElem(...)`. But
`ByteProcessor.createBufferedImage` builds `new BufferedImage(cm,
raster, false, null)` where the raster is byte-backed (DataBufferByte),
and the shim's `BufferedImage(ColorModel, WritableRaster, ...)` ctor
sets `imageType = TYPE_CUSTOM` unconditionally — so `getRGB` takes the
else branch and casts a DataBufferByte to DataBufferInt → illegal cast.
On the desktop the same code path would throw a (catchable)
ClassCastException; under TeaVM WasmGC it surfaces as a wasm
`illegal cast` RuntimeError that crashes Node and is uncatchable by
TeavmMain's catch. Classification: **(a) shim defect** — `getRGB` /
`setRGB` branch on `imageType` instead of on the raster's actual
DataBuffer type.

**Proposed fix (not applied, per the stop rule — this round fixed three
blockers already):** in the `BufferedImage` shim, make `getRGB` and
`setRGB` branch on the DataBuffer's runtime type (e.g. if
`raster.getDataBuffer() instanceof DataBufferByte`, use the sample
path; else cast to DataBufferInt), or equivalently on the raster
SampleModel's data type. That is the contained shim fix for the next
round; it should let the run past `buildNoStaffBuffer` and into the
rest of GRID.

### 12.9 Verdict: PARTIAL — STEP LOAD reached; stopped at BufferedImage.getRGB

- The §12 task's fix **works**: `getStubsToUpgrade` returns empty for
  the fresh book, the run passes Book init and reaches **STEP LOAD for
  the first time**, completes SCALE, and is now inside the GRID step
  (staff-line retrieval, systems, no-staff buffer). **No WasmGC timing
  and no HEADS count exist yet** — the full-page run was not attempted
  (the crop traps first in every build). CheerpJ 5 remains the only
  working option.
- Three same-family blockers were found and fixed in this bounded round,
  each verified by a rebuild + re-run: the FilamentFactory constructor
  reflection gap (policy), the QuadCurve2D null iterator (shim), the
  Raster null-origin default (shim).
- Current stopping point, named precisely: `RuntimeError: illegal cast`
  in `BufferedImage.getRGB`, reached via
  `StaffLineCleaner.process` → `LagManager.rebuildHLag` →
  `Picture.buildNoStaffTable` → `Picture.getSource` →
  `Picture.buildNoStaffBuffer` → `ByteProcessor.getBufferedImage` →
  `BufferedImageGraphics.drawImage` → `BufferedImage.getRGB`, because
  the buffer image is TYPE_CUSTOM over a DataBufferByte raster.
  Proposed fix is in §12.8 (branch getRGB/setRGB on the DataBuffer's
  runtime type).
- On PC mapping: §11.6 recorded V8 trap PCs as unmappable. In §12 the
  module-offset interpretation gave coherent chains for the §12.4, §12.6
  and §12.8 traps (9/10, 8/10 and 8/10 frames respectively, with the
  remaining frames unmapped — no containing sequence in a 60k/500k
  window — and never claimed). The chains were corroborated by call
  edges in the repo/shim sources (e.g. `NaturalSpline.<init>` →
  `Path2D.append` is in the source; `retrieveFilaments` →
  `mergeFilaments` → `canMerge` is the real call sequence), so method
  names in the tables above are claimed on the combined evidence, not
  on PCs alone. One caution from the work: my first mapping pass used
  wrong decimal conversions of the hex PCs and produced incoherent
  results — the correct conversions are the ones in the tables above.
- Adjacent known gaps, not yet hit: `RectangularShape.getPathIterator`
  also returns null in the shim (Ellipse2D / Rectangle2D shapes would
  trap the same way as QuadCurve2D did if appended); the other `Raster`
  factory methods do not null-check their `Point location` argument.
- Do not file any of the §12 shim issues against TeaVM — they are
  spike-shim defects, not TeaVM defects. (The §11 `Profiles.getName()`
  metadata gap and the #21244 / #15448 core patches remain the
  candidate upstream TeaVM filings.)

### 12.10 Files added/changed in §12

- `teavm/patched/make_patches.py` — `getStubsToUpgrade` replacement in
  the Round 4 Book section + docstring header entry. Durable artifact
  for the §12 fix; `teavm/patched/src/` is regenerated from it by
  `build.sh`.
- `teavm/policy/src/teavm/TeavmReflectionPolicy.java` — StaffFilament /
  StraightFilament `<init>` reflectableMethods (§12.3). Compiled by
  `build.sh` step 3 into `policy-classes`.
- `teavm/shims/src/java/awt/geom/QuadCurve2D.java` — `QuadIterator`
  (§12.5); `teavm/shims/src/java/awt/image/Raster.java` — null-origin
  default in `createWritableRaster` (§12.7). Both rebuilt into
  `shims.jar` by `build.sh`.
- `teavm-fork/full-out16/` + `full-build16.log` + `load-out16.log` +
  `run-crop16.log` + `build16.log` — getStubsToUpgrade fix (LOADS OK
  370 ms, STEP LOAD + SCALE, traps in FilamentFactory).
- `teavm-fork/full-out17/` + `full-build17.log` + `load-out17.log` +
  `run-crop17.log` + `build17.log` — policy fix (LOADS OK 399 ms, ERROR
  gone, traps in Path2D.append).
- `teavm-fork/full-out18/` + `full-build18.log` + `load-out18.log` +
  `run-crop18.log` + `build18.log` — QuadIterator fix (LOADS OK 337 ms,
  GRID line retrieval + systems, traps in Raster.<init>).
- `teavm-fork/full-out19/` + `full-build19.log` + `load-out19.log` +
  `run-crop19.log` + `build19.log` — Raster fix (LOADS OK 356 ms,
  past Raster, illegal cast in BufferedImage.getRGB).
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.
## 13. getRGB/setRGB branch on DataBuffer type; OmrFont tolerates a null RES_URI — run reaches BEAMS, stops at a null pixel array in the NO_STAFF ByteProcessor — 2026-11-09 (PARTIAL, stopped at the next failure per the task's stop rule)

Task: fix `BufferedImage.getRGB`/`setRGB` in the TeaVM spike shims to
branch on the DataBuffer's runtime type instead of imageType (§12.8
stopping point), rebuild, re-run TeavmMain on the hymn crop first,
then the full page if the crop reaches HEADS. Bounded round: one
contained same-family fix + one re-run; stop and name the next trap
otherwise. This round in fact took three builds: the getRGB fix
(full-out20), a diagnostic build to name the fatal call site
(full-out21), and the OmrFont fix (full-out22). Each step is recorded
below in order.

### 13.1 The §12 fix — getRGB/setRGB branch on DataBuffer runtime type (FIXED)

- File: `teavm/shims/src/java/awt/image/BufferedImage.java` (shim
  only; `jdlehman/score-reader` untouched). Old code branched on
  `imageType`: grey types took a grey-ramp sample path, everything
  else cast to `DataBufferInt`. The
  `(ColorModel, WritableRaster, boolean, Hashtable)` ctor sets
  `imageType = TYPE_CUSTOM` unconditionally, so a byte-backed raster
  (ImageJ `ByteProcessor.getBufferedImage`, the §12 trap in
  `Picture.buildNoStaffBuffer`) fell into the `DataBufferInt` branch
  and trapped with an illegal cast under WasmGC.
- New code: `getRGB(int, int)` and `setRGB(int, int, int)` branch on
  `raster.getDataBuffer()` — `DataBufferByte` takes the sample path
  (1 band: sample → `colorModel.getRGB(sample)`, or the grey ramp if
  the color model is null; multi-band: samples in stored band order,
  2-band treated as grey+alpha); `DataBufferInt` takes the raw
  packed-pixel path as before; any other buffer type (no
  USHORT/SHORT/FLOAT/DOUBLE shims exist) falls back to the sample path
  rather than casting. The bulk overloads delegate to the single-pixel
  versions, so they are covered. One build error on the way:
  `raster.getPixel(x, y, null)` is ambiguous between
  `getPixel(int, int, int[])` and `getPixel(int, int, float[])` —
  fixed with an explicit `(int[]) null` cast.
- Behaviour for correctly-typed images is unchanged: byte rasters
  take the sample path they always took (for TYPE_BYTE_GRAY and
  ImageJ's grey IndexColorModel the palette lookup returns exactly the
  old `0xff000000|(v<<16)|(v<<8)|v`; for a non-grey indexed palette it
  returns the palette colour, which the old grey ramp got wrong); int
  rasters take the raw packed-pixel path they always took
  (`TemplateFactory`'s `getRGB == FORE/BACK/HOLE` comparisons rely on
  the stored value, alpha included).
- Adjacent same-family gap from §12 also fixed in this round:
  `Raster.createInterleavedRaster(DataBuffer, …)` and
  `Raster.createBandedRaster(int, …)` now default a null `Point
  location` to `(0,0)` in
  `teavm/shims/src/java/awt/image/Raster.java`, mirroring the §12.7
  `createWritableRaster` fix. `RectangularShape.getPathIterator`
  (returns null; only Ellipse2D and RoundRectangle2D are affected —
  Rectangle2D has its own RectIterator, so §12's parenthetical naming
  Rectangle2D was slightly wrong) was deliberately NOT proactively
  fixed: it is a larger per-subclass iterator job, to be fixed if the
  run traps there.
- Desktop verification (JDK 25, shims as a `java.desktop` patch
  module; the patch copy had to exclude `java/awt/datatransfer`,
  which belongs to the `java.datatransfer` module): a 15-check unit
  test (`/tmp/test13/Test13.java`) passed ALL 15 — TYPE_CUSTOM
  byte-backed image with grey IndexColorModel (the §12 trap case:
  getRGB `0xFFC8C8C8` for sample 200, setRGB grey-average round-trip),
  TYPE_BYTE_GRAY unchanged (white/black, grey average
  (128+64+32)/3 = 74 = `0x4A`), TYPE_INT_RGB unchanged (FORE
  `0xFFFFFF00`, stored `0xFF010203`), colour indexed palette returns
  the palette colour (`0xFF640000` for sample 100 — the old code
  would have returned a grey ramp), bulk getRGB, getSubimage
  round-trip, Raster null-location defaults, multi-band byte 3-band
  round-trip.

### 13.2 Run full-out20 — past getRGB and GRID; new failure in BEAMS: "Parent is null"

- Build: canonical command from §10 (patched2 core jar FIRST on the
  compiler classpath), `full-build20.log`. 0 problems, 2,877 classes,
  27,752 methods, `classes.wasm` 10,531,943 bytes (out19: 10,531,125,
  +818). Load: `LOAD OK` in 374 ms (`load-out20.log`).
- Crop run (`run-crop20.log`, load 337 ms, main() returned in
  4,975 ms): the getRGB fix WORKS — the run got past
  `buildNoStaffBuffer` and GRID, logged `Systems: #1[1, 2]`,
  `SystemManager 2 parts along 1 system`, `Book Created scores:
  [{Score 1}]`, clef warnings (Staff#1/#2 no recognized header clef
  — expected with stub fonts), `StemSeedsStep stem(3 max:4)`, then a
  NEW failure — not a wasm trap (Node did not crash) but a catchable
  Java exception:
  `WARN [SpotsBuilder] Error building spots
  <java.lang.IllegalArgumentException: Parent is null>` followed by
  `TEAVM FAILED: java.util.concurrent.ExecutionException:
  java.lang.RuntimeException: java.lang.IllegalArgumentException:
  Parent is null`.
- Step order in `OmrStep`: LOAD, BINARY, SCALE, GRID, HEADERS,
  STEM_SEEDS, BEAMS, LEDGERS, HEADS, … — so the failure is in BEAMS
  (doProlog warns, then doSystem) or at the start of LEDGERS/HEADS.
  `TeavmMain.run()` calls `stub.reachStep(OmrStep.HEADS, false)` and
  catches Throwable in main() printing "TEAVM FAILED".
- The only "Parent is null" in the whole app is
  `UriUtil.toURI(URI parent, String child)`
  (`UriUtil.java:84`), thrown when parent is null.
  `UriUtil.toURI(URL)` returns null for a null URL, so
  `WellKnowns.RES_URI` is null in WASM (hard-coded null in the
  WellKnowns patch: no resources; established in §11). Callers of
  `toURI(URI, String)` with `WellKnowns.RES_URI` as parent:
  BasicClassifier (model file — bypassed by the StubClassifier patch;
  all reading-path classifier uses go through
  `ShapeClassifier.getInstance()`, and `BasicClassifier.getInstance`
  appears only in UI code), LogUtil (already ran at WellKnowns static
  init), DrumSet, AliasPatterns (fixed in §11), ShapeShortcuts,
  Language, AboutAction, MacApplication, ActionManager, OmrFont
  (line 303: `UriUtil.toURI(WellKnowns.RES_URI, fileName).toURL()`).
- The WARN's throw traced with confidence from the source:
  `BeamsStep.doProlog` → `SpotsBuilder.buildSheetSpots` →
  `buildSpots` → `BlackHeadSizer.process` →
  `MusicFont.getHeadFont(family, scale, 0)` (`BlackHeadSizer.java:198`)
  → `MusicFont.getMusicFont` → `OmrFont.getFont` →
  `OmrFont.createFont` (line 303, fileName "Bravura.otf" for the
  default `MusicFamily.Bravura`) → `toURI(null, "Bravura.otf")` →
  IllegalArgumentException. `OmrFont.createFont` catches only
  `MalformedURLException`, not `IllegalArgumentException`, so it
  propagates; `buildSheetSpots` catches Exception and only warns, so
  this occurrence is non-fatal by itself.
- The FATAL throw was not yet definitively named at this point:
  `BeamsStep.doSystem` (per-system parallel tasks) runs
  `BeamsBuilder.buildBeams()` + `MultipleRestsBuilder.process()` —
  neither references MusicFont/OmrFont/UriUtil/Classifier directly —
  and the next step, HEADS, runs `HeadsStep.doProlog` →
  `HeadSpotsBuilder.getSpots()` (a separate class, not extending
  SpotsBuilder; calls `GlyphFactory.buildGlyphs` on the saved head
  runs, no font reference found). `AbstractBeamInter` takes a
  `MusicFont` as a constructor parameter, so a beam-inter
  construction inside `buildBeams` was the prime suspect, but the
  stack frames are TeaVM `Throwable$FakeClass` and unusable for
  method names. A diagnostic was needed rather than a guess.

### 13.3 Diagnostic — DIAG13 names the fatal call site: OmrFont, child=Bravura.otf (FIXED the diagnosis)

- Added to `teavm/patched/make_patches.py` (durable, regenerated by
  `build.sh`): `UriUtil.java` added to FILES (index 11), and a
  DIAG13 section that prints the child file before throwing in
  `toURI(URI, String)` — `DIAG13 toURI null parent child=<child>` —
  because TeaVM stack traces are FakeClass frames and cannot name the
  caller. The child name identifies the caller ("Bravura.otf" =
  OmrFont.createFont, a model zip name = BasicClassifier). Docstring
  header updated the same way.
- Build full-out21 (`build21.log`, exit 0, `patched/classes OK: 270
  classes`): the DIAG13 print is present at patched
  `UriUtil.java:85`. Full build (`full-build21.log`): 0 problems,
  2,877 classes, 27,752 methods.
- Crop run full-out21 (`run-crop21.log`): both occurrences are
  `child=Bravura.otf` — the WARN site AND the fatal site are both
  `OmrFont.createFont`. The fatal throw is the second
  `MusicFont.getMusicFont(Bravura, …)` call (the BEAMS doSystem path
  via `AbstractBeamInter`), reaching the same `toURI(null,
  "Bravura.otf")`. BasicClassifier is ruled out as the fatal site.
- Recursion safety of the platform-font fall-through, checked before
  fixing: Bravura's backup is null ("No backup needed for this
  comprehensive font", `MusicFamily.java`), so `new
  MusicFont(platformFont)` cannot recurse; the shim `Font.getFamily()`
  returns the name ("Bravura"), `Font(Font)` copy ctor exists,
  `valueOfName("Bravura")` resolves to Bravura, and `OmrFont.getFont`
  caches by (fontName, size).

### 13.4 The §13 fix — OmrFont.createFont catches IllegalArgumentException (FIXED)

- Added to `teavm/patched/make_patches.py` (durable): `OmrFont.java`
  added to FILES (index 12), and a section widening the catch in
  `createFont` from `MalformedURLException` alone to
  `MalformedURLException | IllegalArgumentException`, falling through
  to the platform font below — the code's existing fallback (`new
  Font(fontName, Font.PLAIN, size)`). The log message becomes
  "Could not load res font".
- Desktop-neutral: on the desktop RES_URI is never null and the res
  file exists, so this branch never triggers there; and if `toURI`
  threw IAE for another reason (child absolute/empty, bad URI syntax),
  falling through to the platform font is the same "res lookup
  failed" handling the code already intends (it already catches
  `FontFormatException`/`IOException` from the res attempt and falls
  through).
- Classification: (a) spike-patch defect — same family as the §11
  null-WellKnowns-folder fixes (RES_URI is null by spike design, and
  the Audiveris code's catch list did not cover the exception the
  null parent actually produces).

### 13.5 Run full-out22 — past OmrFont, into BEAMS doSystem; new trap: null pointer in AreaMask$ForeCounter.process (STOPPING POINT)

- Build full-out22 (`build22.log`, exit 0, `patched/classes OK: 272
  classes` — the OmrFont catch is present at patched
  `OmrFont.java:319`). Full build (`full-build22.log`): 0 problems,
  2,877 classes, 27,752 methods, `classes.wasm` 10,532,405 bytes
  (out20: 10,531,943; out21: 10,532,169; out19: 10,531,125). Load:
  `LOAD OK` in 350 ms (`load-out22.log`).
- Crop run (`run-crop22.log`, Node exit 1 — wasm trap, Node
  crashed):
  ```
  INFO [ScaleStep] Scale{ interline(21,21,22) line(2,2,4) beam(10)}
  INFO [LinesRetriever] Global slope: 0.00000
  INFO [ClustersRetriever] Retrieved raw line clusters: 2 of sizes [5] with interline(21,21,22)
  INFO [PeakGraph] Systems: #1[1, 2]
  INFO [SystemManager] 2 parts along 1 system
  INFO [Book] Created scores: [{Score 1}]
  WARN [ClefBuilder] Staff#1 no recognized header clef.
  WARN [ClefBuilder] Staff#2 no recognized header clef.
  INFO [StemSeedsStep] stem(3 max:4)
  DIAG13 toURI null parent child=Bravura.otf
  WARN [OmrFont] Could not load res font <java.lang.IllegalArgumentException: Parent is null>
  WARN [TemplateSymbol] TemplateSymbol. No symbol for NOTEHEAD_BLACK_SMALL in family Bravura
  RuntimeError: dereferencing a null pointer
      at wasm-function[35030]:0x872220
      at wasm-function[35028]:0x871c4c
      at wasm-function[35029]:0x871c89
      at wasm-function[5104]:0x2c1f85
      at wasm-function[35031]:0x872521
      at wasm-function[28512]:0x71535a
      at wasm-function[18370]:0x55a91d
      at wasm-function[17615]:0x4fb308
      at wasm-function[15718]:0x45cef2
      at wasm-function[16128]:0x46dc3c
  ```
- The OmrFont fix works: DIAG13 fires only ONCE now (the first
  lookup, in BEAMS doProlog via BlackHeadSizer), is caught and
  warned, and the second lookup — the fatal site in full-out20/21 —
  never reaches `toURI` again, because the first `createFont` cached
  the platform font under "Bravura" and `OmrFont.getFont` returns the
  cached font on the second call. The "Parent is null" failure is
  fully resolved; both occurrences are gone as failures.
- The run then proceeds into BEAMS doSystem and traps in
  `AreaMask$ForeCounter.process`. What is established, on combined
  evidence:
  - Innermost frame [35030], PC 0x872220 (8,865,312): the containing
    debug sequence in `full-out22/classes.wasm.teadbg` (via
    `fn272/DumpSeq.java`, which lists sequences by address range) is
    `[8865289..8865430) org.audiveris.omr.image.AreaMask$ForeCounter.process`.
    `DumpDebug.find()` alone is NOT reliable here — it returns the
    nearest sequence below the target, not the containing one
    (e.g. find(8865312) first returned `AreaMask$ForeCounter.process
    [874609..874696)`, a floor hit in a different address range);
    containment in a DumpSeq window is the check that names the
    method. A few other frames check out by containment too:
    [35031] → `Jama.QRDecomposition.solve`, [18370] →
    `MultipleRestsBuilder.getSectionsByWidth`, [15718] →
    `ScaleBuilder$HistoKeeper.retrieveInterlinePeaks`, [16128] →
    `StaffProjector.refineRightEnd` — but those middle/outer frames
    do not form a coherent synchronous Java call chain with the BEAMS
    log position (SCALE/GRID methods cannot be live callers after
    STEM_SEEDS), so they are best read as TeaVM coroutine-continuation
    artefacts, not as the call chain; only the innermost frame is
    claimed as the trapping method, and the caller is claimed from
    the source, not from the PCs.
  - Caller, from the source: the only `.fore(` callers in the whole
    app are `BeamsBuilder.java:568, 578, 962, 1032`, all passing the
    field `pixelFilter` — so the trap is in
    `BeamsBuilder.computeImpacts` (line 568, `coreMask.fore(core,
    pixelFilter)`) or the same shape at 962/1032, reached from
    `BeamsStep.doSystem` → `BeamsBuilder.buildBeams()` (line 248:
    `pixelFilter =
    sheet.getPicture().getSource(Picture.SourceKey.NO_STAFF)`).
  - The null itself: `ByteProcessor.get(int, int)` is a single
    `pixels[y*width + x] & 0xff` load (verified by `javap -c` on the
    patched ij jar), so a null-pointer trap inside it means the
    NO_STAFF `ByteProcessor`'s `pixels` byte[] is null. The filter
    object itself is non-null — `ForeCounter`'s constructor already
    read `filter.getWidth()`/`getHeight()` without trapping — and the
    counter is sound (`AreaMask.fore` sets `fore.value = 0` before
    apply; `WrappedInteger` stores its initial value). So the
    NO_STAFF buffer exists with valid width/height but a null pixel
    array. The `TemplateSymbol` WARN immediately before the trap ("No
    symbol for NOTEHEAD_BLACK_SMALL in family Bravura" — the stub
    fonts have no glyphs) is adjacent, not causal: it comes from the
    BlackHeadSizer template path in BEAMS doProlog, which completed.
  - Upstream path: the NO_STAFF buffer is built by
    `Picture.buildNoStaffBuffer` (`getSource(BINARY)` →
    `src.getBufferedImage()` → staff-line erasure with
    `BufferedImageGraphics.drawImage` → `new ByteProcessor(img)`),
    the same method the §12 getRGB trap ran through; `getSource`
    caches sources via `WeakReference` and rebuilds when the strong
    ref is gone, and `new ByteProcessor(img)` takes its pixels from
    `((DataBufferByte) img.getRaster().getDataBuffer()).getData()`.
- What is NOT proven (and why the round stops here): which link in
  that upstream path yields the null array. The candidates checked
  do not close the loop:
  - The shim `BufferedImage(w, h, TYPE_BYTE_GRAY)` allocates its
    `DataBufferByte` (`new DataBufferByte(width*height)`), and
    `BufferedImageGraphics.drawImage` does not replace the raster —
    so the default-LUT branch of ImageJ's
    `ByteProcessor.getBufferedImage()` (new TYPE_BYTE_GRAY image +
    drawImage) should yield non-null pixels.
  - The non-default-LUT branch yields a TYPE_CUSTOM image
    (`new BufferedImage(cm, raster, false, null)`), which would make
    `new ByteProcessor(img)` throw `IllegalArgumentException
    ("Type!=TYPE_BYTE_GRAYY")` — but no such IAE surfaces anywhere
    (the failure is a null trap, not a TEAVM FAILED with IAE), so
    that branch evidently is not what happened, or the IAE is being
    swallowed somewhere not yet found. No `setLut` call exists in
    `Picture.java`, and the binarized filter returns a default-LUT
    processor.
  - The `WeakReference` cache in `Picture.getSource` is a third
    suspect (a cleared weak ref forces a rebuild; a TeaVM
    WeakReference quirk could return a cleared/stale ref), but
    `getSource` rebuilds on a null strong ref, so it does not by
    itself explain a null-pixels processor.
  - A speculative fix (e.g. null-guarding `ForeCounter`, or forcing
    a LUT) would mask the symptom — a null-guarded `fore()` would
    silently count zero foreground pixels and reject every beam —
    without knowing which link is null. Per the task's stop rule this
    is not a contained shim fix in the same family (DataBuffer-type
    branching, null PathIterator, null Raster location) that can be
    applied with confidence, so the round stops here and names the
    trap instead of iterating further.
- Furthest step reached: BEAMS (doSystem — past HEADERS, STEM_SEEDS,
  and the BEAMS doProlog spots build). No WasmGC timing and no HEADS
  count exist yet — the full hymn-satb.png page was not attempted
  (the crop traps first in every build). CheerpJ 5 remains the only
  working option.
- Note for the next person: the fastest way to name the null link is
  a DIAG print in the patched copy (same pattern as DIAG13) at the
  `buildNoStaffBuffer` return — log `img.getType()`,
  `img.getRaster().getDataBuffer()` class, and whether
  `((DataBufferByte) …).getData()` is null — plus one at
  `BeamsBuilder.buildBeams` logging whether the `pixelFilter`
  returned by `getSource(NO_STAFF)` is null and whether its
  `getPixels()` is null. One diagnostic build + one crop run would
  separate the three candidates above. Do NOT file this as a TeaVM
  issue: on the evidence so far it is a shim/ImageJ-round-trip
  defect, not a TeaVM codegen defect.

### 13.6 Verdict: PARTIAL — getRGB fix and OmrFont fix both work; run reaches BEAMS; stopped at a null pixel array in the NO_STAFF ByteProcessor

- The §12 stopping point is resolved: `getRGB`/`setRGB` no longer
  trap on byte-backed TYPE_CUSTOM images (verified by a 15-check
  desktop unit test and by the full-out20 run passing
  `buildNoStaffBuffer` and GRID).
- The "Parent is null" failure found in full-out20 is resolved:
  both occurrences are `OmrFont.createFont` with
  child="Bravura.otf", and catching `IllegalArgumentException` there
  falls through to the platform font; the second lookup is then a
  cache hit, so DIAG13 fires only once in full-out22.
- Current stopping point, named precisely: `RuntimeError:
  dereferencing a null pointer` in
  `AreaMask$ForeCounter.process` (PC 0x872220, function [35030]),
  reached via `BeamsStep.doSystem` → `BeamsBuilder.buildBeams` →
  `computeImpacts` → `AreaMask.fore(core, pixelFilter)`, because the
  NO_STAFF `ByteProcessor`'s `pixels` array is null. Which upstream
  link produces the null array is unproven — see §13.5 for the three
  candidates and the proposed one-build diagnostic.
- No WasmGC timing and no HEADS count exist yet. CheerpJ 5 remains
  the only working option.
- Do not file any §13 shim issue against TeaVM — they are
  spike-shim / spike-patch defects, not TeaVM defects. (The §11
  `Profiles.getName()` metadata gap and the #21244 / #15448 core
  patches remain the candidate upstream TeaVM filings.)

### 13.7 Files added/changed in §13

- `teavm/shims/src/java/awt/image/BufferedImage.java` — getRGB/setRGB
  branch on DataBuffer runtime type (§13.1); bulk overloads delegate
  to the single-pixel versions. Rebuilt into `shims.jar` by
  `build.sh`.
- `teavm/shims/src/java/awt/image/Raster.java` — null-location
  defaults in `createInterleavedRaster(DataBuffer, …)` and
  `createBandedRaster(int, …)` (§13.1). Rebuilt into `shims.jar` by
  `build.sh`.
- `teavm/patched/make_patches.py` — `UriUtil.java` added to FILES
  (index 11) + DIAG13 print of the child file on null parent
  (§13.3); `OmrFont.java` added to FILES (index 12) + catch
  `IllegalArgumentException` in `createFont` (§13.4); docstring header
  entries for both. Durable artifacts; `teavm/patched/src/` is
  regenerated from them by `build.sh`.
- `teavm-fork/full-out20/` + `full-build20.log` + `load-out20.log` +
  `run-crop20.log` + `build20.log` — getRGB fix (LOADS OK 374 ms,
  past GRID, "Parent is null" in BEAMS).
- `teavm-fork/full-out21/` + `full-build21.log` + `run-crop21.log` +
  `build21.log` — DIAG13 diagnostic (both occurrences
  child=Bravura.otf).
- `teavm-fork/full-out22/` + `full-build22.log` + `load-out22.log` +
  `run-crop22.log` + `build22.log` — OmrFont fix (LOADS OK 350 ms,
  past OmrFont, traps in `AreaMask$ForeCounter.process` in BEAMS
  doSystem).
- `/tmp/test13/Test13.java` — 15-check desktop unit test for the
  §13.1 shim change (all pass; ephemeral, not kept in the spike
  tree).
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 14. buildNoStaffBuffer diagnostic — the §13 null-pixels hypothesis is refuted; the real trap was TemplateSymbol.getParams; fixed; new stop at FloodFiller.fill recursion — 2026-11-09 (PARTIAL, stopped at the next failure per the task's stop rule)

### 14.1 Diagnostic method (DIAG14)

One diagnostic build, TeavmMainDiag pattern, diagnostic copies only —
`jdlehman/score-reader` untouched. ROUND 7 in
`teavm/patched/make_patches.py` (durable, prints only) brackets every link
of the chain `BINARY → getBufferedImage → new ByteProcessor` plus the
consumer:

- `Picture.getSource` entry: `DIAG14 getSource <key> cachedNull=<bool>`
  (WeakReference cache hit vs rebuild, per key).
- `Picture.getSource` BINARY branch: image-branch vs binarized-branch
  (`imageNull`, `type`), and binarized `pixelsNull`.
- `Picture.buildNoStaffBuffer`: BINARY `pixelsNull`, bin image
  `type` / DataBuffer class / `getData()` null-ness and length, and the
  returned NO_STAFF `pixelsNull`.
- `BeamsBuilder.buildBeams` / `buildCueBeams` (both sites, `sub_all`):
  `pixelFilter` null-ness and `pixelsNull`.

Build: `teavm/build.sh` (277 classes), then the canonical command (§10)
to `full-out23` (0 problems, 2,877 classes, 27,752 methods,
`classes.wasm` 10,537,049 bytes — size from `ls`, see build log).
Load: `LOAD OK in 324 ms`. Run: hymn crop 2480×700
(`run-crop.mjs full-out23` → `run-crop23.log`).

### 14.2 Print evidence — every link of the §13 chain is NON-null

The §13 hypothesis was: the NO_STAFF `ByteProcessor` exists with valid
width/height but a null `pixels` array, produced by one of three upstream
links (default-LUT image path, non-default-LUT TYPE_CUSTOM path,
WeakReference cache in `Picture.getSource`). The prints refute all three:

```
DIAG14 getSource BINARY cachedNull=true
DIAG14 getSource BINARY imageNull=false type=10
DIAG14 getSource NO_STAFF cachedNull=true
DIAG14 getSource BINARY cachedNull=false
DIAG14 buildNoStaffBuffer binSrc null=false w=2480 h=700 pixelsNull=false
DIAG14 buildNoStaffBuffer binImg null=false
DIAG14 buildNoStaffBuffer binImg type=10 w=2480 h=700 db=java.awt.image.DataBufferByte dataNull=false dataLen=1736000
DIAG14 buildNoStaffBuffer noStaff pixelsNull=false w=2480 h=700
...
DIAG14 buildBeams pixelFilter null=false w=2480 h=700 pixelsNull=false
```

- BINARY comes from the image branch (`imageNull=false`, `type=10`
  = `TYPE_BYTE_GRAY`), not the binarized branch (the binarized print
  never fires — the grey→binary path is not taken here).
- The bin image's `DataBufferByte.getData()` is non-null, length
  1,736,000 = 2480×700.
- The returned NO_STAFF processor has non-null pixels, and so does the
  `pixelFilter` that reaches `BeamsBuilder.buildBeams`.
- The WeakReference cache works: later `getSource NO_STAFF` calls all
  report `cachedNull=false` (dozens of them), so no cache drop is in
  play either.

**The null-pixels hypothesis is dead.** No `null`-guard on `fore()`
was added (it would have silently zeroed beam counts, as §13 warned),
and none is needed: the object `fore()` reads is intact.

### 14.3 Correction: §13 misidentified the trapping method (hex→decimal error)

§13 claimed the trap was `AreaMask$ForeCounter.process`, PC 0x872220,
"confirmed by containment" in `full-out22/classes.wasm.teadbg`. That
containment check used the wrong decimal: **0x872220 = 8,856,096, not
8,865,312** as §13 wrote. The sequence §13 cited,
`[8865289..8865430) AreaMask$ForeCounter.process`, contains 8,865,312
(= 0x874620) — a different address from the actual trap PC. Re-mapping
the §13 stack against the correct decimals, and mapping the §14 stack
(`full-out23`, same function indices, PCs shifted by the rebuild) with
`fn272/DumpSeq.java` (containment, not floor lookup — see §13.5 for why
floor lookup is unreliable):

| Frame (full-out23) | PC | Decimal | Containing sequence |
|---|---|---|---|
| [35030] (innermost) | 0x873254 | 8,860,244 | `[8858822..8861000) org.audiveris.omr.ui.symbol.TemplateSymbol.getParams` |
| [35028] | 0x872c80 | 8,858,752 | `[8858636..8858800) org.audiveris.omr.ui.symbol.TemplateSymbol.getParams` |
| [35029] | 0x872cbd | 8,858,813 | 22-byte gap just past getParams `[8858636..8858800)`; nearest below is getParams |
| [35031] | 0x873555 | 8,861,013 | 13-byte gap just past getParams `[8858822..8861000)`; nearest below is getParams |
| [5104] | 0x2c1ed4 | 2,891,476 | `[2891917..2892972) org.audiveris.omr.sig.inter.DataHolder.toString` (coroutine-continuation artefact, not a real caller — see §13.5) |

The innermost three frames are all `TemplateSymbol.getParams`, not
`ForeCounter.process`. The same holds for full-out22: its trap PC
0x872220 = 8,856,096 falls in the out22 `getParams` sequence (out23's
sequences shifted by ≈ +4,148 from out22, the same shift as
`ForeCounter.process` 8,865,289 → 8,869,437), and §13's own log excerpt
already showed the `TemplateSymbol` WARN as the last line before the
trap. **§13.5–13.7's "null pixel array in the NO_STAFF ByteProcessor"
and "AreaMask$ForeCounter.process (PC 0x872220)" attributions are
superseded by this section.** The `getFatBounds` sequence
(`[8861021..8861280)`) sits immediately after `getParams`, consistent
with the call `getFatBounds → getParams` (see §14.4).

### 14.4 The real null source, traced to its origin

The run log (full-out23) ends:

```
DIAG14 buildBeams pixelFilter null=false w=2480 h=700 pixelsNull=false
... (many getSource NO_STAFF cachedNull=false — later steps)
WARN [org.audiveris.omr.ui.symbol.TemplateSymbol] TemplateSymbol. No symbol for NOTEHEAD_BLACK_SMALL in family Bravura
RuntimeError: dereferencing a null pointer
    at wasm-function[35030]:0x873254   (TemplateSymbol.getParams)
```

The chain, verified in repo source
(`~/workspace/score-reader-spikes/repo/.work/audiveris/`):

1. `TemplateSymbol.getParams(MusicFont font)`
   (`ui/symbol/TemplateSymbol.java:91-114`):
   ```java
   ShapeSymbol symbol = font.getSymbol(shape);
   while (symbol == null && font.getBackup() != null) { ... font = font.getBackup(); ... }
   if (symbol == null) {
       logger.warn("TemplateSymbol. No symbol for {} in family {}", shape, font.getMusicFamily());
   }
   final Params symParams = symbol.getParams(font);   // <-- NPE when symbol == null
   ```
   The code **warns and then dereferences `symbol` unconditionally** on
   the next line. On desktop this never fires (see step 4); under
   TeaVM it is the trap. Caller: `getFatBounds(font)` →
   `getParams(font).rawRect.getBounds()` (`TemplateSymbol.java:82-84`),
   called from `TemplateFactory.java:830` and `:925` while building
   templates — i.e. the run is in **HEADS template building**, not BEAMS
   doSystem as §13 claimed.
2. `MusicFont.getSymbol(shape)` (`ui/symbol/MusicFont.java:333-335`)
   returns `musicFamily.getSymbols().getSymbol(shape)`.
3. `Symbols.getSymbol(shape)` (`ui/symbol/Symbols.java:124-141`):
   first `symbolMap.get(shape)`, then `getCode(shape)` → `new
   CodedSymbol(...)`, else null. For `NOTEHEAD_BLACK_SMALL`:
   `BravuraSymbols.getCode` has **no `NOTEHEAD_BLACK_SMALL` case**
   (it has `NOTEHEAD_BLACK -> 0xE0A4`), so the code path returns null;
   the only way the symbol exists is the prepopulated `symbolMap`
   entry from `Symbols.populateSymbols()` (`Symbols.java:270`:
   `mapSmall(NOTEHEAD_BLACK_SMALL, NOTEHEAD_BLACK)`).
4. `populateSymbols()` is called exactly once in the app, from
   `MusicFont.populateAllSymbols()` (`MusicFont.java:683-689`), which is
   called from `MusicFont.checkMusicFont()` (`MusicFont.java:514-516`)
   and from the standalone `TemplateFactory.main()`. The runtime
   startup call is **`Main.java:269`: `MusicFont.checkMusicFont()`**
   (GUI path: `MainGui.java:545`). **`TeavmMain` bypasses `Main.main`
   entirely** — it constructs `Book` directly — so
   `checkMusicFont()` / `populateAllSymbols()` **never runs under
   TeaVM**, `BravuraSymbols.symbolMap` stays empty, `getSymbol`
   returns null, and `TemplateSymbol.getParams` NPEs on the first
   small-head template.

**Null source named:** the empty `Symbols.symbolMap`, because the
startup population call in `Main.main` is never made by the headless
entry point. Not the NO_STAFF pixels (refuted, §14.2), not a TeaVM
codegen defect, not a shim returning null.

Classification: **(c) Audiveris code assuming desktop/startup state**
— the symbol tables are populated only by a startup call the headless
path never makes — with a latent Audiveris null-deref
(warn-then-dereference in `TemplateSymbol.getParams`) that desktop
never triggers because the font always loads and `populateAllSymbols`
always runs. The contained spike-side fix is a one-liner in the entry
point (no Audiveris patch needed): restore the exact state `Main.main`
establishes on desktop.

### 14.5 Fix applied — and two shim gaps it surfaced

Fix (in `teavm/entry/src/teavm/TeavmMain.java`, after
`OmrExecutors.restart()`, before `new Book(...)`):

```java
org.audiveris.omr.ui.symbol.MusicFont.checkMusicFont();
System.out.println("DIAG14 populateAllSymbols done");
```

`checkMusicFont()` is the exact desktop startup call
(`Main.java:269`); it populates all families' symbol tables and
returns true. Calling `populateAllSymbols()` directly would be
equivalent; `checkMusicFont()` was chosen to mirror desktop startup.

Calling it pulls the symbol painters into the reachable set, which
surfaced two new TeaVM PROBLEMS (full-out24: 2 problems, previously 0):

1. `Field java.awt.Color.RED was not found` —
   `NonDraggableSymbol.paint` (`ui/symbol/NonDraggableSymbol.java:81`,
   `g.setColor(Color.RED)`). Cause: TeaVM's classlib `TColor` defines
   only `BLACK`/`WHITE` (§9 rule: for classlib-defined classes the
   classlib version wins over user shims, so fix at the call site).
   The `Color` constants added to `teavm/shims/src/java/awt/Color.java`
   in this round are **shadowed by TColor and ineffective** — left in
   place as documentation, not relied on. Fix (ROUND 8 in
   `make_patches.py`, durable): `g.setColor(new Color(255, 0, 0))` —
   exactly RED, so template rendering is unchanged. No other
   `Color.*` constant is used by any reachable method (TeaVM reported
   only RED after the next fix).
2. `Method java.awt.geom.CubicCurve2D.setCurve([Ljava/awt/geom/Point2D;I)V
   was not found` — `SlurSymbol.paint`. Fix (shim,
   `teavm/shims/src/java/awt/geom/CubicCurve2D.java`): added the JDK
   `setCurve` overloads, mirroring the `QuadCurve2D` shim
   (`double[]`, `Point2D×4`, `Point2D[]`, `CubicCurve2D`).

Full-out25 still had 1 problem (Color.RED); after the ROUND 8
call-site patch, **full-out26: 0 problems**, 2,932 classes, 27,932
methods, `classes.wasm` 10,646,079 bytes (see `full-build26.log`).
**Load: `LOAD OK in 344 ms`.**

### 14.6 Run result — past BEAMS, into HEADS, new stop at FloodFiller.fill

`run-crop.mjs full-out26` → `run-crop26.log`, hymn crop 2480×700,
wall ≈ 5.5 s to the crash (the run is fast; it crashes, it does not
hang):

```
DIAG14 populateAllSymbols done
... SCALE / GRID / HEADERS / STEM_SEEDS as before ...
DIAG14 buildBeams pixelFilter null=false w=2480 h=700 pixelsNull=false
INFO [org.audiveris.omr.image.TemplateFactory] Rebuilding NOTEHEAD_VOID template at resolution 108
INFO [org.audiveris.omr.image.TemplateFactory] Rebuilding NOTEHEAD_VOID template at resolution 216
RangeError: Maximum call stack size exceeded
    at wasm-function[36326]:0x8a3fc5
    at wasm-function[36326]:0x8a4076
    at wasm-function[36326]:0x8a4095
    ... (self-recursive, same function)
```

- The `TemplateSymbol` NPE is **gone**: no "No symbol for" WARN, and
  `NOTEHEAD_VOID` templates rebuild at resolution 108 and 216.
- Furthest step reached: **HEADS template building** (past LOAD, SCALE,
  GRID, HEADERS, STEM_SEEDS, BEAMS). No heads count yet (HEADS never
  completes), no `.mxl`, no WasmGC timing vs native 30.8 s LOAD→HEADS.
  The full hymn page was not attempted (crop crashes first).
- CheerpJ 5 remains the only working option.

### 14.7 New stopping point — FloodFiller.fill recursion depth (named precisely, per the stop rule)

`DumpSeq` containment on `full-out26/classes.wasm.teadbg`:

- 0x8a3fc5 = 9,060,293 → `[9060293..9060569)
  org.audiveris.omr.image.FloodFiller.fill` (sequence starts exactly
  at the trap PC).
- 0x8a4076 = 9,060,470 and 0x8a4095 = 9,060,501 → same sequence.
- The stack is one function calling itself: `FloodFiller.fill` is
  the recursive flood fill (`image/FloodFiller.java:68-83`):
  `fill` → `fill(x-1,y)` / `fill(x,y-1)` / `fill(x,y+1)` /
  `fill(x+1,y)`, called from `TemplateFactory.java:684/693` (`fillHoles`)
  and `:711` (`adjustHoles`) while building templates.

Why depth exhaustion, not a stuck `setRGB` (infinite ping-pong):

- The template image is `new BufferedImage(..., BufferedImage.TYPE_INT_RGB)`
  (`TemplateFactory.java:243-246`) → `DataBufferInt` → the §13 shim
  `getRGB`/`setRGB` take the raw packed-pixel path, an exact round-trip,
  so `setRGB(HOLE)` sticks and a re-visit sees `pix != BACK` and stops.
- `BACK = Color.WHITE.getRGB()` (0xFFFFFFFF), `HOLE =
  Color.PINK.getRGB()` (0xFFFFAFAF), `FORE = Color.YELLOW.getRGB()` —
  all distinct, so the fill's `pix == oldColor && pix != newColor`
  guard terminates on revisit.
- The run survived the resolution-108 rebuild and died on the
  resolution-216 rebuild (4× the pixels): depth scales with template
  size, which is what stack-depth exhaustion looks like, not a
  colour-equality bug.

Classification: **(c) Audiveris code assuming desktop/JVM state** —
the recursive flood fill assumes a call stack deep enough for the
longest simple path through a template's background region; Node's
Wasm call stack is smaller than a JVM thread stack, so the same
recursion that runs fine on desktop overflows here. (Adjacent (b):
the Wasm/Node stack limit is the binding constraint, not TeaVM
codegen.)

Proposed next step (not started here, per the stop rule): (1) confirm
depth is the only issue by re-running Node with a larger stack
(`node --stack-size=<n> run-crop.mjs full-out26`) — if the crop then
passes BEAMS/HEADS, depth is confirmed; (2) then either raise the
stack in the runner or, better, replace the recursive `fill` with an
iterative explicit-stack version in the patched set (desktop-neutral:
same pixels, no recursion) — a small `FloodFiller.java` patch via
`make_patches.py`, mirroring the other Audiveris-side patches.

### 14.8 Files

- `teavm/patched/make_patches.py` — ROUND 7 (DIAG14 prints in
  `Picture.java` + `BeamsBuilder.java`, new to the patched set) and
  ROUND 8 (`NonDraggableSymbol.java` Color.RED call-site patch);
  docstring updated for DIAG14.
- `teavm/entry/src/teavm/TeavmMain.java` — `checkMusicFont()` call
  (§14.5).
- `teavm/shims/src/java/awt/Color.java` — standard constants added
  (shadowed by TColor; ineffective, see §14.5 — the working fix is the
  ROUND 8 call-site patch).
- `teavm/shims/src/java/awt/geom/CubicCurve2D.java` — `setCurve`
  overloads (§14.5).
- Builds/logs: `teavm-fork/full-out23/` + `full-build23.log` +
  `run-crop23.log` (diagnostic), `full-out24/` + `full-build24.log`
  (2 problems), `full-out25/` + `full-build25.log` (1 problem),
  `full-out26/` + `full-build26.log` (0 problems) + `run-crop26.log`
  (new stopping point). DIAG14 prints are still in the full-out26
  build; strip ROUND 7 (or keep it behind a flag) before any "clean"
  build — the prints are diagnostic noise, not behaviour.
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched. Do not file the §14 `TemplateSymbol.getParams`
  warn-then-dereference against TeaVM — it is Audiveris code, and on
  desktop the path never executes; the upstream-relevant items remain
  #272 (issue draft, needs the `TPoint2D`/`TDimension2D` note),
  #21244/#15448 (two-part core patch), and the §11
  `Profiles.getName()` metadata gap.

## 15. Larger-stack confirmation — FloodFiller.fill is depth exhaustion, and no --stack-size passes the 432 rebuild — 2026-11-09 (CONFIRMED, stopped at the next step per the task)

### 15.1 Method

Build: `full-out26` (0 problems, 2,932 classes, `classes.wasm`
10,646,079 bytes), the §14 build with DIAG14 prints still in it —
used as-is for this test, per the task (diagnostic build is fine
here; the prints are noise, not behaviour). No rebuild, no code
change, no `fill` change in this task.

Runner: `teavm-fork/run-crop.mjs full-out26` on the hymn crop
2480×700 (`hymn-crop.gray`, 1,736,000 bytes), Node v24.22.1.
Each run capped with `timeout 300`; every run below finished in
~5.5 s on its own, so the cap never bit.

Flag semantics, verified on this Node version (`node --v8-options`):
`--stack-size` is "default size of stack region v8 is allowed to
use (in kBytes)", **default 984 kB** on this build. (The adjacent
`--wasm-stack-switching-stack-size`, also default 984 kB, applies
only to Wasm stack-switching and was not used — the run does not
use stack switching.) Exact flags used: `node run-crop.mjs
full-out26` (default) and `node --stack-size=<N> run-crop.mjs
full-out26` for N in 2048, 4096, 6144, 7168, 7680, 8192 (twice),
16384. Scripts: `teavm-fork/stack15/run_stacks.sh`,
`run_stacks2.sh` (the 8192/6144/16384 round), plus the 7168/7680
pair run inline; logs in `teavm-fork/stack15/run-crop-stack-*.log`.

### 15.2 Per-run results

| --stack-size (kB) | Load | Wall | Furthest template rebuild | Outcome |
|---|---|---|---|---|
| default (984) | 332 ms | ~5.5 s | 216 (108 passes) | `RangeError: Maximum call stack size exceeded`, wasm-function[36326] PC 0x8a4095, exit 1 |
| 2048 | 368 ms | ~5.5 s | 216 | `RangeError`, same function, same PC 0x8a4095, exit 1 |
| 4096 | 354 ms | ~5.5 s | 432 (216 passes) | `RangeError`, same function, PC 0x8a40b4, exit 1 |
| 6144 | 314 ms | 5.4 s | 432 | `RangeError`, same function, PC 0x8a4095, exit 1 |
| 7168 | 428 ms | 5.5 s | 432 | `RangeError`, same function, PC 0x8a40b4, exit 1 |
| 7680 | 437 ms | 5.6 s | 432 | `RangeError`, same function, PC 0x8a40b4, exit 1 |
| 8192 | 368 ms | 5.4 s | 432 | **SIGSEGV, exit 139, no RangeError printed** (reproduced 2/2) |
| 16384 | 379 ms | 5.6 s | 432 | **SIGSEGV, exit 139, no RangeError printed** |

Notes on the table:

- "Furthest template rebuild" is the last `INFO
  [org.audiveris.omr.image.TemplateFactory] Rebuilding
  NOTEHEAD_VOID template at resolution …` line before the crash.
  Resolutions are successive rebuilds of the same template (108 →
  216 → 432, each 4× the pixels of the previous). The 108 rebuild
  passes at every stack size; the 216 rebuild is the first failure
  at default/2048; the 432 rebuild is the first failure at
  4096–16384.
- The two RangeError PCs (0x8a4095, 0x8a40b4) are both inside
  wasm-function[36326] = `FloodFiller.fill` (§14.7 mapping); the
  PC varies with which sub-call of the recursive fill overflows
  first, not with a different method.
- In **no** run did `main()` return, and in no run was HEADS (or
  any later step) reached — `grep -c HEADS` is 0 in every log.
  No heads count, no `.mxl`, no WasmGC timing vs native 30.8 s
  LOAD→HEADS exists. The full hymn page was not attempted (the
  crop traps first in every build, per the task).
- Load time is unaffected by stack size (309–437 ms across runs,
  no trend) — the stack flag changes only how deep the recursion
  gets before it dies.

### 15.3 Verdict: depth exhaustion CONFIRMED — and raising the stack does not fix it

The crash moves forward monotonically with stack size, which is
exactly what depth exhaustion looks like and what a stuck fill
(an infinite ping-pong / cycle) would not do:

- 216 rebuild: needs more than 2048 kB (fails at default and
  2048, passes at 4096).
- 432 rebuild: needs more than 7680 kB (still `RangeError` at
  7680), and at 8192 the failure mode changes — the process
  dies with **SIGSEGV (exit 139)** instead of a catchable
  `RangeError`, reproduced twice at 8192 and again at 16384.
  The segfault happens at the same log position as the
  RangeErrors (during the 432 rebuild, after the same last
  DIAG14 lines), so it is the same recursion overflowing, with
  V8's stack-overflow guard failing to catch it cleanly at
  large `--stack-size` values and the process dying natively
  instead.

So there is **no `--stack-size` that passes the 432 rebuild**:
7680 still RangeErrors, 8192 segfaults. The window, if one
existed, would be between 7680 and 8192 kB, and it is closed by
the segfault — not by a passing run. Even if a size in that
window passed the crop's 432 rebuild, the full hymn page is
larger than the 2480×700 crop and template depth scales with
template size, so the same wall would be hit later, harder.

Pure depth exhaustion is therefore confirmed **and** the
larger-stack route is a dead end: the only durable fix is to
remove the recursion, not to feed it more stack.

### 15.4 Browser implication

This matters beyond Node: browsers do **not** expose a
`--stack-size` flag. A browser tab's Wasm stack is fixed by
the engine (Chrome/V8's default is in the same ~1 MB band as
Node's 984 kB default — the run already overflows that at the
216 rebuild). So even the 4096 kB result, which only gets the
crop to the 432 rebuild, is not reproducible in a browser at
all. Raising the stack is a Node-only diagnostic lever, not a
shippable fix. The shippable fix has to be the iterative
`fill` (see §15.5) — or, failing that, a smaller template
resolution, which would trade accuracy for depth and is not
recommended without measuring it.

### 15.5 Next step (not started here, per the task)

Make `FloodFiller.fill` iterative in the patched set
(desktop-neutral: same pixels, explicit stack instead of
recursion), via `make_patches.py`, mirroring the other
Audiveris-side patches. `FloodFiller.java:68-83` is a
four-neighbour recursive fill (`fill(x-1,y)` / `fill(x,y-1)` /
`fill(x,y+1)` / `fill(x+1,y)`); the iterative version keeps
the same `pix == oldColor && pix != newColor` guard and the
same BACK/HOLE/FORE semantics (§14.7), so the pixels it
produces must be identical — verify that on desktop first
(same template images before/after), then re-run the crop
under Node at the default stack and confirm it passes HEADS.
If the iterative fill passes HEADS, the next wall (if any)
will be the first real WasmGC timing vs native 30.8 s
LOAD→HEADS.

### 15.6 Files

- `teavm-fork/stack15/run_stacks.sh` — default/2048/4096/8192
  round.
- `teavm-fork/stack15/run_stacks2.sh` — 8192 (repeat) / 6144 /
  16384 round.
- `teavm-fork/stack15/run-crop-stack-default.log`,
  `run-crop-stack-2048.log`, `run-crop-stack-4096.log`,
  `run-crop-stack-6144.log`, `run-crop-stack-7168.log`,
  `run-crop-stack-7680.log`, `run-crop-stack-8192.log`,
  `run-crop-stack-16384.log` — one log per stack size (the
  8192 log is the second of two identical segfault runs).
- No code was changed in this task; no `fill` patch was made.
  Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 16. Iterative FloodFiller.fill — HEADS passes at the default stack; first TeavmMain completion under TeaVM WasmGC — 2026-11-09 (DONE)

### 16.1 The fix: FloodFiller.fill goes iterative (ROUND 9)

Upstream `FloodFiller.fill` (`FloodFiller.java:68-83`) is a recursive
four-neighbour DFS (`fill(x-1,y)` / `fill(x,y-1)` / `fill(x,y+1)` /
`fill(x+1,y)`), called only from `TemplateFactory.addHoles` (`:684/693`)
and `adjustHoles` (`:711`). §15 proved it overflows the Wasm call stack
during HEADS template building (216 rebuild dies at Node's default 984 kB
stack; no `--stack-size` passes the 432 rebuild; browsers expose no such
flag). The durable fix is an explicit stack, in the spike's patched set
only (`teavm/patched/make_patches.py`, ROUND 9) — `jdlehman/score-reader`
untouched.

Design, mirroring the other Audiveris-side patches:

- Plain `int[]` stack, no collection dependency under TeaVM; positions
  encoded `pos = y * width + x`; initial capacity 256, grown x2 with
  `System.arraycopy`.
- A pixel is marked (`setRGB(newColor)`) at push time, so each pixel is
  pushed at most once and the stack never holds duplicates.
- Neighbours pushed in the recursive version's order Left/Top/Bottom/
  Right. Pop order is therefore reversed vs recursive DFS — that does
  not affect the final image: the filled set is exactly the 4-connected
  component of `oldColor` pixels reachable from the seed, so traversal
  order cannot change the result. (Recorded here because the task asked
  explicitly; the desktop comparison in §16.2 is the proof.)
- Guard preserved exactly: early returns for out-of-bounds seed,
  `oldColor == newColor`, and seed pixel `!= oldColor` — the exact
  equivalents of the recursive version's guard
  `pix == oldColor && pix != newColor`.

### 16.2 Desktop verification FIRST: identical pixels (DONE before any Node run)

Two levels, both run before the first Node rebuild.

Unit level — `teavm-fork/fill16/FillTest.java` (JDK 25.0.5+8):
loads the original recursive class and the iterative class as two
distinct classes via separate `URLClassLoader`s, runs the recursive
reference in a thread with a 512 MB stack, and compares every pixel
plus a SHA-256 hash per image. **19/19 PASS, 0 failed** — solid
300x300 centre/corner, solid 500x200, random 400x300 (seeds 1, 2),
random 200x200 FORE->HOLE, snake 200x200, snake 500x100 (longest
simple path), notehead 108/216/432 interior, notehead 432 exterior,
seed-out-of-bounds (neg/west), seed-on-FORE, old==new, 1x1,
no-oldColor-pixels, grey 120x90 (TYPE_BYTE_GRAY). Example hashes:
solid-300x300 `86c83aefcc086f25`, notehead-432 interior
`123a0cbfd8dee213`.

End-to-end — native Audiveris (`java -Xmx4g
org.audiveris.omr.Main -batch`, same constants as
`run_photo_spikes.py`: `TesseractOCR.useOCR=false`,
`sheetStepTimeOut=3600`, `indentations=false`, `maxSlopeDiff=0.05`,
`-transcribe -export`) on `test-material/hymn-satb.png`, twice:
original jars (`fill16/desktop-orig/`, exit 0, 26 s) and iterative
`FloodFiller` prepended on the classpath (`fill16/desktop-iter/`,
exit 0, 25 s). The inner MusicXML files are **byte-identical**
(SHA-256
`8ea083dd076667b77126b8a4595282d0699022f9c395e943fcc85a30de1c8e69`
for both), 128/128 non-rest notes, 2 parts, 16 measures in both.
(The `.mxl` zip hashes differed only due to zip metadata.)

The `.omr` sheet XML differed in ID-like fields
(`last-persistent-id` 3619 orig vs 3736 iter; `staff-barlines` IDs;
diff 4,822 lines). This was investigated, NOT assumed to be a fill
effect: a control run, original fill a second time
(`fill16/desktop-orig2/`, exit 0), also differs from the first
original run in the same way (`last-persistent-id` 3794;
orig-vs-orig2 diff 4,821 lines; its `.mxl` inner XML is again
byte-identical, same SHA-256). Conclusion: the `.omr` ID differences
are run-to-run nondeterminism in Audiveris (ID assignment order),
not a fill effect; the exported MusicXML — the observable output —
is byte-identical across orig, iter, and orig2.

### 16.3 The new trap: runaway template rebuild (full-out27) — NOT a fill bug

With the iterative fill, full-out27 (0 problems, 2,932 classes,
`classes.wasm` 10,646,486 bytes, LOAD OK 317 ms) passed the old crash
points — template rebuilds at 108, 216, 432 completed — and then kept
doubling: 864, 1728, 3456, 6912, 13824, 27648, before dying after
~34 s with `RuntimeError: requested new array is too large`
(wasm-function[79]). PC-mapping the trap frames with DumpSeq was
tried and NOT trusted: the sequences near the PCs do not form a
coherent chain (unrelated methods), the same failure mode §13
warned about — no PC-to-method claim is made here.

The mechanism, read from upstream source:
`Template.getKeyPoints()` lazily calls
`TemplateFactory.retrieveKeyPoints()` → `Builder.processSymbol(1)`;
`processSymbol` returns `null` from `buildDistances` when the
upper-left pixel is HOLE after `addHoles`/`adjustHoles`, and on null
it recurses at `holeLargerRatio = 2` — with **no cap anywhere in
upstream code**. On desktop this terminates because a real music font
always yields an enclosed hole within a couple of doublings. Under
TeaVM the stub font renders no glyph at all, so the hole-seed fill
covers the whole image, `(0,0) == HOLE` at every resolution, and the
image doubles until allocation fails. The recursive fill would do
exactly the same on a blank image — the fill is not at fault; §15's
crash at 216 was the whole-image fill overflowing, and the rebuild
loop behind it was already running.

DIAG16 (ROUND 10, `buildDistances` FORE-pixel count) proves it —
full-out28, every call, same shape at every resolution:

```
DIAG16 buildDistances shape=NOTEHEAD_VOID w=31 h=58 fore=0 rgb00=ffffafaf
DIAG16 buildDistances shape=NOTEHEAD_VOID w=62 h=116 fore=0 rgb00=ffffafaf
DIAG16 buildDistances shape=NOTEHEAD_VOID w=124 h=232 fore=0 rgb00=ffffafaf
... (fore=0 at 864, 1728, 3456, 6912, 13824; image 7834x14746 at 13824)
RuntimeError: requested new array is too large
```

`fore=0` (no FORE pixel anywhere in the template image) and
`rgb00=ffffafaf` (HOLE, pink) at every resolution. Blank template,
proven — not inferred.

### 16.4 The cap (ROUND 11) — bounded, desktop-neutral

`Builder.processSymbol` in the patched set only: when holes
detection fails and `ratio >= 8`, log
`No template for {} at any resolution, giving up` and return an
empty `ArrayList` instead of recursing. Attempts at ratios 1, 2, 4,
8, then give up. An empty list (not null) is required:
`Template.getKeyPoints()` callers iterate the list, and a null
return would NPE there; an empty list simply scores no heads for
that shape — the Phase A expectation (stub fonts, 0 heads).
Desktop-neutral: with a real font the loop terminates before the
cap, so behaviour is unchanged; and this patch lives only in the
spike's patched set, never in the repo.

### 16.5 Build and runs — HEADS passes, full page, default stack

Canonical build (patched core jar FIRST on the compiler classpath,
per the §10.8 correction):

```
cd teavm && ./build.sh            # regenerates patched/src, shims.jar, patched/classes
java -Xmx3g -cp "../teavm-fork/lib-fork/teavm-core-0.16.0-patched2.jar:lib/*:classes" \
  Spike wasm-gc ../teavm-fork/full-out29 teavm.TeavmMain \
  @../teavm-fork/teavm-main-jars-corepatch2.txt @program-jars.txt
```

full-out29: 0 problems, 2,932 classes, 27,932 methods,
`classes.wasm` 10,647,563 bytes. DIAG14/DIAG16 prints still in the
build (diagnostic noise, not behaviour — strip ROUND 7/10 before
any "clean" build, per §14).

Crop first (2480x700, `run-crop.mjs full-out29`, Node v24.22.1,
**default stack, no `--stack-size` flag**), exit 0:

```
wasm loaded in 509 ms
Scale{ interline(21,21,22) line(2,2,4) beam(10)}
Systems: #1[1, 2] — 2 parts along 1 system — Score 1 created
WARN No template for NOTEHEAD_VOID / BREVE / WHOLE_NOTE at any resolution, giving up
REACH HEADS ms=5920
LATEST STEP HEADS — STAVES 2 HEADS 0 CHECK 0
TEAVM DONE — main() returned in 6074 ms
```

Full page next (`run-fullout.mjs full-out29`, hymn-satb.png
2480x3507), exit 0:

```
wasm loaded in 376 ms
Scale{ interline(21,21,22) line(2,2,4) beam(13)}
Systems: #1[1, 2] #2[3, 4] — 2 parts along 2 systems — Score 1 created
REACH HEADS ms=20768
LATEST STEP HEADS — SYSTEMS 2 STAVES 4 HEADS 0 CHECK 0
TEAVM DONE — main() returned in 21250 ms
```

Load time across builds: 317–509 ms. Furthest step reached: HEADS
— TeavmMain stops there by design, so there is no later step to
reach in this entry point and no `.mxl` is produced. Heads found: **0**,
exactly the Phase A expectation (blank stub-font templates; the
`HeadInter` "No foreground pixels" lines and the empty
`HeadSeedTally: HeadSeeds{}` in the log are the same story from the
matching side). Structure matches native: 2 systems, 4 staves,
2 parts, 1 score.

Wall time vs native 30.8 s LOAD→HEADS: TeaVM WasmGC reaches HEADS
in 20.8 s on the full page — but this is NOT a like-for-like timing
and must not be quoted as one. Native's 30.8 s includes real template
building (rendering Bravura glyphs, distance transforms) and real
head matching; the Wasm run does none of that work (blank templates,
empty key points, 0 heads, no template matching). The first real
WasmGC timing comes after Phase B (pre-rendered note-head
templates), when heads are actually found.

### 16.6 Verdict: DONE — the first TeavmMain completion under TeaVM WasmGC

- The iterative fill works: pixel-identical on desktop (19/19 unit,
  byte-identical end-to-end `.mxl`), and it removes the §15 stack
  overflow at the default Node stack.
- The rebuild cap works: the runaway loop that the fill fix exposed
  is stopped, with the blank-template mechanism proven by DIAG16
  rather than assumed.
- **TeavmMain now loads and completes under Node at the default
  stack** — LOAD, SCALE, GRID, HEADS on both the crop (~6.1 s) and
  the full hymn page (~21.3 s), exit 0, `main()` returns. This is
  the first time any Audiveris run under TeaVM WasmGC has finished
  a step sequence instead of trapping.
- No new trap in this round. The stopping point is no longer a
  crash — it is Phase B: pre-rendered note-head templates
  (~2–4 days, per the §14/§15 plan) so HEADS can find real heads,
  after which the first honest WasmGC-vs-native timing and then
  export (JAXB/MusicXML story) and OCR follow. Nothing here should
  be filed against TeaVM: the fill, the cap, and the DIAG prints
  are all spike-side; the upstream items remain #272,
  #21244/#15448, and the §11 `Profiles.getName()` metadata gap.

### 16.7 Files

- `teavm/patched/make_patches.py` — ROUND 9 (iterative
  `FloodFiller.fill`), ROUND 10 (DIAG16), ROUND 11
  (`processSymbol` rebuild cap).
- `teavm-fork/floodfiller-iterative.patch` — the ROUND 9 diff
  (FloodFiller.java vs upstream, 82 lines).
- `teavm-fork/templatefactory-patched-vs-upstream.patch` —
  patched TemplateFactory.java vs upstream (`--strip-trailing-cr`;
  the repo file is CRLF, the patched copy LF — the §16 hunks
  inside it are DIAG16 and the rebuild cap; the rest is the
  earlier R2 Color-literal / binarize rewrite).
- `teavm-fork/fill16/` — `FillTest.java`, `test-classes/`,
  `orig-classes/`, `iter-classes/`, `run_desktop.sh`,
  `run_desktop_orig2.sh`, `desktop-orig/`, `desktop-iter/`,
  `desktop-orig2/`, logs, `mxl-orig/`, `mxl-iter/`,
  `mxl-orig2/`, `omr-orig/`, `omr-iter/`, `omr-orig2/`.
- `teavm-fork/build27.log`, `full-build27.log`, `run-crop27.log`
  — iterative fill only; runaway rebuild trap.
- `teavm-fork/build28.log`, `full-build28.log`, `run-crop28.log`
  — DIAG16 proof (fore=0 at every resolution).
- `teavm-fork/build29.log`, `full-build29.log`, `run-crop29.log`,
  `run-fullout29.log` — cap in place; HEADS passes, crop and full
  page, default stack.
- `teavm-fork/full-out27/`, `full-out28/`, `full-out29/` —
  successive WasmGC builds.
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 17. Pre-rendered note-head templates (Phase B) — HEADS finds real heads; first honest timing; known +46 overcount diagnosed — 2026-11-09 (DONE, with a named divergence)

### 17.1 Design: pre-rendered COMPLETE templates, not glyph rasters

The stub font fails template building in two ways, not one — so
pre-rendering only the glyph raster would not have been enough:

1. **Blank glyphs** (§14/§16): the shim `TextLayout.draw` / `Graphics2D`
   paint path renders nothing, so `buildDistances` sees `fore=0` and
   `processSymbol` runs away (capped in §16 at ratio >= 8, empty key
   points, 0 heads).
2. **Wrong geometry**: the shim `TextLayout.getBounds()` returns
   `advance = 0.5 * size` per character and `height = size`, which is not
   Bravura's geometry at all. Template width/height, slim bounds and
   anchors are all derived from those bounds, so even a perfectly painted
   raster would land in a wrongly-sized, wrongly-anchored template box.

The fix pre-renders the whole `Template` — width, height, slim bounds,
anchors and the key-points list — offline on desktop Java with the real
Bravura font, and substitutes it in `Catalog.buildAllTemplates`
(ROUND 12 in `make_patches.py`, durable). `Template.getKeyPoints()`
then returns the stored list and `retrieveKeyPoints` / `processSymbol`
never run under TeaVM, so no font rendering happens in the HEADS path
at all. When the lookup returns null (unknown family, or no catalog
near the requested size) the code falls back to the stub-font
`Builder.buildTemplate()` — the Phase A behaviour.

**Point-size mapping (the calibration distortion).** The catalog point
size is itself stub-distorted. Desktop, `BlackHeadSizer` measures the
black-head width `w` and `computePointSize` interpolates against real
Bravura layout widths; the desktop `.omr` scale block for the hymn
reads `black-head mean-width="27.2"`, `music-font point-size="92"`.
Under TeaVM the same interpolation runs against shim layouts
(advance `0.5 * size`, one character), which lands exactly on
`TeaVM pointSize = 2.0 * w` (verified analytically in §17.2 and
empirically: DIAG16's first `processSymbol` ran at 54, and
`2.0 * 27.2 = 54.4`). Real Bravura `NOTEHEAD_BLACK` layout width is
linear in font size with advance ratio `a = 0.2950` (measured constant
across sizes 54/80/92/108), so `desktop pointSize = w / a` and

```
desktop = requested * (1 / (2*a)) = requested * 1.694827
```

Hymn: requested 54 -> 91.6 -> nearest pre-rendered catalog 92, which
is exactly the desktop calibration for this sheet. The lookup picks
the nearest of the pre-rendered catalogs {80, 92, 108} when it is
within 8 of the mapped value, else null (fall back). The returned
`Template` carries the DESKTOP point size (92). Nothing in the HEADS
path requires `template.getPointSize()` to equal the catalog point
size — verified by grep over `NoteHeadsBuilder` / `HeadInter` /
`Template`: the only point-size consumers there are the two catalog
lookups (`NoteHeadsBuilder.java:351`, `HeadInter.java:817`), both of
which go through the remapped catalog.

**What is serialized.** Per catalog (family Bravura) and per shape
(all 24 in `ShapeSet.Heads`): width, height, slim bounds, every
anchor offset (exact doubles), and the full key-points list `(x, y, d)`.
`d` values are all integral doubles in -27..+11 (the `reduce()`
quantization maps |d|==1 to 0), so they serialize exactly as ints.
Key-point counts per catalog: 54 -> 6,008; 80 -> 14,728; 92 -> 19,410;
108 -> 27,132. NOTEHEAD_BLACK at 92: 36x31, slim 27x22 at (4,5)
(slim width 27 = the measured head width 27.2), 700 key points
(454 fore, 246 back, 0 hole).

**Format.** Generated Java source (`teavm/PreRenderedTemplates.java`,
784 KB, 61,270 key points in catalogs {80, 92, 108}), produced by
`phaseb/gen_prerendered.py` from `phaseb/templates.json`, which
`phaseb/TemplateDump.java` dumps from native Audiveris. Static data
compiled into the Wasm module: no file I/O, no new shim surface, no
runtime dependency on the font. One implementation lesson recorded
here: the first generator emitted the 72 key-point arrays as `static
final` fields and javac refused with "code too large" — all static
array initializers land in a single `<clinit>`, which has the 64 KB
method limit. The arrays are now locals inside each per-shape builder
method (largest shape 2,263 key points, well under the limit).

### 17.2 Desktop verification FIRST (all before any Node run)

**Template dump.** `TemplateDump` (desktop JDK, stock Audiveris jars)
builds Bravura catalogs at 54/80/92/108 and dumps every template field
plus a SHA-256 of each key-point list (`phaseb/templates.json`,
821 KB). It also confirms the advance ratio is constant (0.2951 /
0.2949 / 0.2950 / 0.2950) and that the hymn's desktop calibration is
92 (from the `.omr` scale block, cross-checked against the dump's
`blackLayoutWidth` 27.14 at 92).

**Round-trip: 72/72 PASS, 0 failures** (`phaseb/RoundTrip.java`,
`roundtrip.log`). For each desktop size 80/92/108 it simulates the
TeaVM request that maps to it (requested 47/54/64), builds the
pre-rendered `Template` via `PreRenderedTemplates.getTemplate`, and
compares it field-by-field against the live native template at that
size: width, height, slim bounds, point size, every anchor offset
(exact double equality), and every key point `(x, y, d)` plus a
SHA-256 of the whole list. All 72 templates (24 shapes x 3 catalogs)
match exactly. Fallback checks pass too: Leland family, requested 10
and requested 200 all return null.

**Desktop HEADS mirror (the comparator).**
`phaseb/DesktopHeads.java` mirrors `TeavmMain.run()` on desktop Java
— same `Book` / `SheetStub` / `reachStep(HEADS)` path and the same
head counting — with the real Bravura font. Two harness-only notes:
it installs a default `CLI` into `Main` via reflection first, because
`SheetStub.doOneStep` reads `Main.getCli().isSave()` and `Book.<init>`
reads `Main.getCli().getOutputFolder()` (the same Audiveris-assumes-a-
CLI family as the §12 TeaVM trap); and it is a test harness, not a
patch to Audiveris or to the spike's patched set. Results on the full
hymn page (PNG input): **REACH HEADS 16,545 ms, SYSTEMS 2, STAVES 4,
HEADS 307, CHECK 539192, music-font point size 92.** Two repeat runs
gave 19,259 ms and 20,304 ms (host load varies) with identical
307 / 539192 — the count is stable, the timing is not single-number
precise. Note the ground truth at the HEADS step is **307 heads**,
not 128: 128 is the final `.mxl` note count after later steps prune
heads. The Wasm target is therefore 307, CHECK 539192.

**Input exoneration.** The Wasm run reads `teavm/hymn-satb.gray`,
which is a luminance conversion of the PNG, while desktop Audiveris
converts max-RGB to grey (49,629 pixels differ by up to 99). To rule
the input out, the desktop mirror was run on the exact `.gray` bytes
(`/tmp/hymn-gray.png`): **HEADS 307, CHECK 539192 — identical to the
PNG run.** The input difference is not the cause of any Wasm/desktop
divergence below.

### 17.3 Build and runs — HEADS finds real heads, default stack

Canonical build (`build.sh`, then the §10 command with the patched
core jar first on the compiler classpath):

- `full-out30`: **0 problems, 2,934 classes** (was 2,932: +`PreRenderedTemplates`
  and one more reachable class), 28,011 methods, `classes.wasm`
  12,570,618 bytes (was 10,647,563 — +1.92 MB for the template data;
  array initializers compile to code, hence more than the 784 KB of
  source). Load 354 ms.
- Crop first (2480x700, `run-crop.mjs full-out30`, default stack,
  exit 0): `PreRenderedTemplates: requested 54 maps to desktop catalog
  92` (printed once), no `Rebuilding ... template` lines, no
  `No template ... giving up` lines, **REACH HEADS ms=7354, SYSTEMS 1,
  STAVES 2, HEADS 220, CHECK 361795, main() returned in 7500 ms.**
- Full page next (`run-fullout.mjs full-out30`, exit 0):
  **REACH HEADS ms=22550, SYSTEMS 2, STAVES 4, HEADS 353,
  CHECK 575525, main() returned in 23051 ms.**
- `full-out31` (same build plus a DIAG17 per-head dump in `TeavmMain`,
  kept as a diagnostic aid) reproduces the full page exactly:
  HEADS 353, CHECK 575525, in 24,371 ms (the dump printing itself
  costs ~1.8 s; full-out30 is the timing run). The count is
  deterministic across builds.

### 17.4 The divergence: 353 vs 307 (+46, +15%) — diagnosed, not a template defect

The per-head dump (`HEAD <sys> staff=<n> shape=<s> pitch=<p>
grade=<g> box=<x,y,w,h>`, sorted, in both `TeavmMain` and
`DesktopHeads`; `phaseb` holds `heads-wasm.txt` /
`heads-desktop.txt`) gives:

- **251 heads match exactly** (same system/staff/shape/pitch/box),
  grades differing by max 0.027, mean 0.0001 (only 3 differ by
  >0.001). Template matching itself (`evaluate()`) is sound — the
  templates and the sheet distance tables agree.
- **~49 paired 1–2 px offsets, net-zero**: 49 of the 102 Wasm-only
  heads sit within 2 px of a desktop head of the same shape and pitch,
  and 49 of the 56 desktop-only heads sit within 2 px of a Wasm head.
  For ~49 locations the two runs pick a best-x 1–2 px apart — a
  near-tie in `evaluate()` grades flipping the winner. Benign in
  itself; the likely cause is tiny distance-table/grade differences
  at the margin (max grade diff 0.027 on matched heads). Not chased
  further in this round.
- **~53 unpaired Wasm-only heads — the real overcount.** They
  concentrate at system starts: 49 of the 102 Wasm-only heads are at
  x < 500, vs 2 of the 56 desktop-only heads. System 1, staff 1,
  x 372–462: desktop finds **0** heads, Wasm finds **20**, all
  low-grade (0.19–0.38). That x-range is the clef/key-signature area
  (stack #1 starts at x=360); the "heads" are template matches
  against clef strokes.

**Root cause (named, with the log line).** The Wasm run logs
`WARN [ClefBuilder] Staff#1..4 no recognized header clef` — no clef
recognized on any staff. `ClefBuilder` recognizes header clefs ONLY
via `classifier.evaluate(...)` (`ClefBuilder.java:565`), and the
ROUND 2 patch makes `ShapeClassifier.getInstance()` return
`teavm.StubClassifier.INSTANCE` because "the neural classifier model
(zip + ZipFS + JAXB) cannot load in WASM; Phase A runs with a stub
classifier that returns no evaluations." With no clef (and key)
inters in the sig, there are no competitors for
`NoteHeadsBuilder`'s abscissa-based pass to veto, so the low-grade
clef-area candidates survive in the Wasm run and are vetoed on
desktop. Classification: **(c) spike-side stub** — the missing neural
classifier, not a template defect (templates are proven identical by
the 72/72 round-trip) and not a TeaVM codegen defect. The remaining
~7 unpaired desktop-only heads are marginal candidates in the other
direction, same family of tie/purge differences.

This was NOT fixed in this round: loading the neural classifier
model under TeaVM (model zip + ZipFS + JAXB) is a separate phase of
work, not a contained shim fix — per the task's stop rule it is
reported here as the next step, not started.

### 17.5 First honest WasmGC timing vs native

| run | REACH HEADS | heads (CHECK) |
|---|---|---|
| Wasm full-out30, full page, default stack | 22,550 ms | 353 (575525) |
| Desktop mirror, full page (3 runs) | 16,545 / 19,259 / 20,304 ms | 307 (539192) |
| Wasm full-out30, crop | 7,354 ms | 220 (361795) |
| Desktop mirror, crop | 11,033 ms | 195 (349915) |

Wasm is ~1.1–1.4x native on LOAD→HEADS for the full page. This
supersedes the 30.8 s native figure quoted in `TEAVM_WASM.md` (an
earlier bench under different host load); the mirror numbers above
are the like-for-like comparator on this host, same metric
(in-process `reachStep`), same input pixels. Caveats, stated plainly:

- The Wasm run still skips template construction from glyphs (data
  is precomputed offline and initialized from the module; +1.92 MB
  of Wasm). In a real deployment that cost is paid once per point
  size and amortized, but it is not in the 22.6 s.
- The Wasm run does extra work the desktop run does not (matching
  ~46 false heads) and skips work the desktop run does (clef
  recognition via the neural classifier). The workloads are not
  identical; the timing is honest about the pipeline as it stands,
  not a clean-room benchmark.
- Both metrics exclude startup (Wasm load 354 ms; JVM startup
  seconds, unmeasured here).
- The crop timing (Wasm 7.35 s vs desktop 11.03 s) runs the other
  way and is most likely host-load noise across runs; do not quote
  it as a Wasm win.

### 17.6 Verdict: DONE — real heads found, timing honest, overcount diagnosed

- Phase B's goal is met in substance: HEADS goes 0 -> 353, with 251
  heads exactly matching desktop (same box, grades within 0.027),
  at the default Node stack, exit 0, `main()` returns. The
  pre-rendered templates are proven identical to native ones
  (72/72 round-trip), and the point-size remap (54 -> 92) is derived
  from measured font metrics, not fitted to the outcome.
- The +46 overcount is diagnosed to a named cause outside the
  templates: the stub neural classifier means no header clefs are
  recognized, so clef-area false heads survive. Nothing here should
  be filed against TeaVM (templates, remap and dump are all
  spike-side); upstream items remain #272, #21244/#15448, and the
  §11 `Profiles.getName()` metadata gap.
- No new trap in this round. The next wall is Phase C, in this
  order: (1) the neural glyph classifier under TeaVM (model loading:
  zip + ZipFS + JAXB) — that should remove the clef-area false
  positives and is the biggest remaining fidelity gap in the HEADS
  path; (2) the 1–2 px paired offsets (tie-breaking; minor,
  net-zero); (3) export (JAXB/MusicXML) and OCR (tesseract.js),
  which are still entirely ahead of this entry point — TeavmMain
  stops at HEADS by design and produces no `.mxl`.

### 17.7 Files

- `teavm/patched/make_patches.py` — ROUND 12 (pre-rendered
  template lookup in `Catalog.buildAllTemplates`, fall back to
  stub-font Builder).
- `teavm/entry/src/teavm/PreRenderedTemplates.java` — generated
  (784 KB; do not hand-edit; regenerate with
  `phaseb/gen_prerendered.py`).
- `teavm/entry/src/teavm/TeavmMain.java` — DIAG17 per-head dump
  (kept; same format as the desktop mirror's dump).
- `teavm-fork/phaseb/` — `TemplateDump.java`, `RoundTrip.java`,
  `DesktopHeads.java` (sources in `src/`, classes in `classes/`),
  `templates.json` (821 KB desktop dump),
  `gen_prerendered.py`, `roundtrip.log` (72/72 PASS),
  `desktop-heads.log` (PNG, 307), `desktop-heads-gray.log`
  (.gray bytes, 307), `desktop-heads-gray2.log` (with dump),
  `desktop-heads-crop.log` (195), `measure_heads.py` (superseded
  crude component measurement — the `.omr` scale block is the
  authority for head width / point size).
- `teavm-fork/build30.log`, `full-build30.log`, `run-crop30.log`,
  `run-fullout30.log` — timing runs (full-out30).
- `teavm-fork/build31.log`, `full-build31.log`, `run-fullout31.log`
  — diagnostic build with the DIAG17 dump (full-out31).
- `teavm-fork/full-out30/`, `full-out31/` — successive WasmGC
  builds (0 problems; 2,934 classes; 12,570,618 / 12,573,367 bytes).
- `phaseb/heads-desktop-full.txt` (307 heads) and
  `phaseb/heads-desktop-crop.txt` (195 heads) — desktop per-head
  dumps used for the §17.4 diff; the Wasm dump is in
  `run-fullout31.log` (`HEAD ...` lines).
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 18. Phase C: neural glyph classifier under TeaVM — classifier works bit-identically; the divergence was the stub font, not the classifier — 2026-11-09 (DONE)

Phase C goal (task brief): get the neural glyph classifier running under
TeaVM WasmGC so clef recognition works and the §17 clef-area false heads
disappear. Outcome: **the classifier itself works, bit-identically to
desktop**. The run that followed it (full-out32) still showed HEADS 276
vs desktop 307, misplaced clefs and missing times — but the classifier
was exonerated at every step of the diagnosis (DIAG19/20/21 below). The
divergence was the **stub music font's wrong geometry** breaking
`ClefBuilder.registerClefs`, which forces *font-based* symbol bounds onto
the clef inter. With a contained spike-side fix (ROUND 14: use glyph
bounds for clefs), the final build (full-out39) gives **HEADS 306 vs
desktop 307** — the single difference is a non-good duplicate head
desktop keeps and Wasm drops — with header clefs recognised and time
signatures back at exact desktop grades.

### 18.1 What the classifier is (verified from the Audiveris sources)

- `BasicClassifier` = Audiveris's home-built shallow MLP
  (`NeuralNetwork`: 1 hidden layer, sigmoid), **not** ONNX / DL4J / JNI —
  no native code in the inference path. So there is no native/JNI
  blocker; the only WASM-hostile part is *loading* the model.
- Model file: `app/res/basic-classifier.zip` — `model.xml` (110 →
  149 → 149, epochs-total 160, learning-rate 0.1, momentum 0.9,
  lambda 1.0E-4), `means.xml` + `stds.xml` (110 doubles each).
  Desktop loading is ZipFS over the zip + JAXB unmarshalling of the
  three XML files (+ user train folder, temp-file copy, FileUtils,
  ChartPlotter training UI). ZipFS + JAXB cannot run in WASM.
- Input features: `MixGlyphDescriptor`, 110 doubles = 99 ART moments +
  10 geometric moments + aspect, computed from the glyph's RunTable
  (`getARTMoments` / `getGeometricMoments` — pure Java, already in the
  pipeline). Normalization is (x − means)/stds via PoorManAlgebra
  (Audiveris's own tiny Nd4j replacement, pure Java).
- First classifier use is at the HEADERS step (ClefBuilder,
  KeyExtractor, HeaderTimeBuilder), long before HEADS; the HEADS path
  also calls it from SymbolsBuilder and MetronomeInter. Callers in the
  HEADS path: ClefBuilder, KeyExtractor, SymbolsBuilder,
  HeaderTimeBuilder, MetronomeInter.
- Step order: LOAD, BINARY, SCALE, GRID, HEADERS, STEM_SEEDS, BEAMS,
  LEDGERS, HEADS, …, SYMBOLS (much later).

### 18.2 The loading path chosen: pre-rendered weights (ROUND 13)

Same pattern as Phase B — pre-render offline into static data, do not
teach TeaVM ZIP/JAXB at runtime. Rationale: the weights are fixed
constants (the model never changes at runtime in this spike), the
pre-render is a one-time offline conversion, and it keeps the runtime
path pure Java (the inference code itself needed no changes).

- Generator `phasec/gen_classifier.py` reads `basic-classifier.zip`
  and emits `teavm/PreRenderedClassifier.java` plus per-chunk classes
  `PreRenderedClassifierH0..H9` / `O0..O9.java` (842 KB total source).
  Two generator gotchas, both fixed in the script: `model.xml` rows
  are `<row><item>…` elements, not space-separated text; and each
  double literal costs TWO constant-pool slots, so 38,889 doubles blow
  javac's 65,535-entry pool limit — hence the ≤16-rows-per-method chunk
  split. Python `repr()` round-trips doubles exactly.
- SHA-256 recorded in `phasec/classifier.json`: hidden `ee109ef6…`,
  output `0a4632df…`, means `72aa7455…`, stds `46d88791…`.
- `BasicClassifier` constructor now builds from `loadPreRendered()`
  (new array constructor added to `NeuralNetwork`, patched copy in the
  spike set) with an `isCompatible` label check that throws loudly on
  mismatch. ZipFS/JAXB/train methods neutered (ROUND 5 precedent):
  load/loadModel/store/storeModel/train (train warns "unsupported in
  WASM"), plus `AbstractClassifier.getTrainFolder`
  (`java.nio.file.Files` not reliably available under TeaVM).
  `ShapeClassifier.getInstance()` reverted from the ROUND 2 stub to
  return `BasicClassifier.getInstance()`; `StubClassifier.java` stays
  in `entry/src`, unused. TeaVM analyzes every method of every
  reachable class (per the `make_patches.py` ROUND 2 comment), which
  is why neutering was needed rather than leaving the I/O methods
  unreachable.
- Patches live in `teavm/patched/make_patches.py` ROUND 13;
  generated data in `teavm/entry/src/teavm/PreRenderedClassifier*.java`.

### 18.3 Desktop verification first: classifier equivalence PROVEN

Harness `phasec/src/ClassifierCheck.java` (run on `hymn-satb.png` from
`test-material/`), `phasec/check-stock.txt`, `check-stock2.txt`,
`check-patched.txt` (+ `.log` files):

- Stock run: REACH HEADS 16,262 ms, HEADS 307, CHECK 539192 (matches
  the §17 mirror); descriptor length 110; LABELS_MATCH=true; network
  110/149/149, epochs 160; RANDOM_SHA (200 seeded random vectors
  through `model.run()`) =
  `a5a01ebbdce1e8d7fe0214c96a313f81b5cbfad439edf0b06c5c5e95e621fcab`,
  RANDOM_MAX 0.8386747653361212; GLYPHS_DUMPED 691 of 691. Clefs: 4
  (G_CLEF 0.7996/0.7995, F_CLEF 0.7761/0.7611, boxes 372,94,56,148 /
  372,419,58,75 / 73,697,56,148 / 73,1021,58,75); TIME: 2 (grades
  0.9104/0.9144, boxes 451,123,36,85 / 451,422,36,85); KEY: 0 (hymn
  has no key signature). True clef glyph (id=61, box=372,94,55,149)
  evaluates G_CLEF=0.999440 on desktop.
- Patched-first run (`phasec/classes-patched` first on the classpath,
  isolating only the 3 classifier files): REACH HEADS 16,906 ms,
  HEADS 307, CHECK 539192, RANDOM_SHA identical, patched=true,
  GLYPHS_DUMPED 600 of 600. Diff vs stock: only the `patched=` marker
  plus glyph-count lines — all 600 shared glyphs have identical
  featSHA, evalSHA, top5.
- Stock-vs-stock control (second stock run): REACH HEADS 16,976 ms,
  HEADS 307, CHECK 539192, RANDOM_SHA identical, GLYPHS_DUMPED 602 of
  602; diff vs first stock run = 93 lines (the same 91 TENUTO-topped
  dash glyphs ids 579–799 missing, plus one glyph id=74 TIME_FOUR_FOUR
  0.72 present in stock2 only). Conclusion: the residual glyph index
  is nondeterministic run-to-run (stock 691, stock2 602, patched 600 —
  patched is inside the stock range); HEADS/CHECK/clefs/keys/times and
  all shared-glyph evaluations are deterministic. The 91 missing
  glyphs are tiny dash-like glyphs (boxes ~22–27×1–4 at y≈222–235 and
  y≈826–837, top5 TENUTO 0.94–0.99). Desktop classifier equivalence
  is therefore PROVEN: network bit-identical, pipeline outcome
  identical.
- `build.sh` passes after ROUND 13: 307 patched classes, BUILD OK.

### 18.4 First Wasm runs: classifier works, heads still short (full-out32/33)

TeaVM build full-out32: 0 problems, 3,002 classes (was 2,934: +68 for
the classifier tree), 28,294 methods. Default stack, exit 0.

- Crop (2480×700): REACH HEADS 7,400 ms, SYSTEMS 1, STAVES 2,
  **HEADS 163** (was 220 in §17; desktop crop 195), CHECK 314245,
  main() returned in 7,565 ms, load 372 ms.
- Full page: REACH HEADS 22,271 ms, SYSTEMS 2, STAVES 4, **HEADS 276**
  (vs desktop 307, vs §17 Wasm 353), CHECK 508076, main() returned
  in 22,801 ms, load 373 ms. The `WARN [ClefBuilder] no recognized
  header clef` line is GONE (only the known OmrFont WARN "Could not
  load res font <IllegalArgumentException: Parent is null>" remains).
- The divergence (276 vs 307, −31): paired head analysis (tolerance
  6 px, same sys/staff/shape/pitch): all 276 Wasm heads pair with a
  desktop head; **Wasm-only: 0**; desktop-only: 31. The 31 are at the
  FIRST note columns of each system: system 1 staff 1 x=516, 605, 694
  (pitches 3.0–8.0, BLACK grades 0.76–0.79, plus matching VOID
  companions 0.19–0.35) and staff 2 x=516, 605, 694, 786 (pitches
  −6.0 to 5.0), system 2 x=164 (staff 3 pitch 5.0, staff 4 pitch 4.0).
  All 31 were present in the §17 stub-classifier Wasm run (353) at the
  exact same boxes — so the real classifier REMOVED them (353 − 46
  clef-area false = 307; 307 − 31 = 276). Paired-grade diffs are larger
  than §17: max 0.092, mean 0.0059, 33 pairs >0.01, 15 >0.05 (largest:
  pitch 6.0, desktop 0.664–0.698 at y=217 → Wasm 0.752–0.777 at
  y=218); dy mean +0.24, range 0…+5.
- DIAG18 (added to `TeavmMain.java`, full-out33) + desktop counterpart
  `phasec/src/SigDump.java` compared the full SIG at HEADS (desktop
  375 inters, Wasm 338):
  - **TIME inters MISSING in Wasm**: desktop has 4 TimeNumberInter +
    2 TimePairInter; Wasm has ZERO.
  - **Clef positions WRONG in Wasm**: desktop clefs at x=372 (sys1) /
    x=73 (sys2), boxes 56×148 (G) and 58×75 (F); Wasm clefs at
    x=778/780 (sys1) / 180/182 (sys2), ALL boxes 42×84. Grades nearly
    identical to desktop (G 0.7996/0.7995 exact; F 0.7792 vs 0.7761,
    0.7611 exact) — the evaluations match but the glyph/box is wrong.
  - Barlines/ledgers: same counts, only 1–2 px box jitter (benign,
    §17-style). HeadInter 276 vs 307 is the only count difference
    besides times.
  - Note: the first SIG diff attempt was misleading because the Wasm
    dump had its "SIG " prefix stripped by sed while the desktop file
    kept it; the corrected diff (prefix stripped from both, files
    `sig-desktop-s.txt` / `sig-wasm33-s.txt`) is the authoritative one.
  - `NoteHeadsBuilder.getSystemCompetitors()` collects "really good"
    inters whose shape is in COMPETING_SHAPES = THICK/THIN_BARLINE,
    THICK/THIN_CONNECTOR, BEAM, BEAM_HOOK, BEAM_SMALL, BEAM_HOOK_SMALL,
    MULTIPLE_REST, TREMOLO_1/2/3, VERTICAL_SERIF — clefs/keys/times
    are NOT in the set, so the §17 "clef competitors veto false heads"
    mechanism as originally stated is imprecise; the actual veto path
    for the −31 heads is the wrong clefStop / header geometry (§18.5),
    not a competitor overlap. (See the §18.5 chain: 30 of the 31 sit
    at x < clefStop 777; the 31st, at x=786, overlaps the misplaced
    clef box 778–820.)

### 18.5 Diagnosis: the stub font, not the classifier (DIAG19/20/21)

Three diagnostics, each ruling out one suspect. All three run the
same code on desktop (`SigDump.java`) and Wasm (`TeavmMain.java`).

**DIAG19 — source images.** BINARY (control: template matching proves
it right) vs NO_STAFF (HEADERS reads clef/key/time parts from it).
FNV-1a over the pixel bytes (plain Java: TeaVM's MessageDigest /
`String.format("%02x")` proved unusable — DIAG19 printed an empty sha
in full-out34).

- BINARY: **IDENTICAL** both sides (fnv `2ec748066257305c`,
  sum 2157206415, zeros 237727) — same input, same binarization.
- NO_STAFF: **differs slightly** — desktop fnv `46aeb40be647074`,
  sum 2174103735, zeros 171463; Wasm fnv `eef833d79e8efb16`,
  sum 2174104755 (+1020), zeros 171459 (−4). A small staff-line-removal
  difference (∼1020 grey-levels over 8.7M pixels), not a gross shift;
  recorded as a residual (§18.7), not the clef cause — the parts
  extracted from NO_STAFF are correct (DIAG21).
- Desktop-on-`.gray` control (SigDump on `/tmp/hymn-gray.png`,
  regenerated from `teavm/hymn-satb.gray` after a service restart
  cleared /tmp): clefs at x=372, times present, 375 inters — input
  exonerated for clefs/times too.

**DIAG20 — header ranges.** For each staff: headerStart, clefRange,
clefStop, header.clef box + glyph box.

- Desktop: sys1 staff1 headerStart=362, bStart=362, bStop=456,
  stop=426, clefStop=427, clef box 372,94,56,148, glyph 372,94,55,149;
  sys1 staff2 stop=429; sys2 staff3 headerStart=63, bStart=63,
  bStop=157, stop=127; sys2 staff4 stop=130.
- Wasm (pre-fix): headerStart=362/63 (correct), bStart=362/63,
  bStop=457/158 (correct to 1px) — **but stop=777/779/179/181,
  clefStop=777/779/179/181, header.clef=null for all four staves**.
  The search window is right; the range *stop* is wrong and no header
  clef is selected. That also explains the missing WARN: clefStop is
  non-null (777), so `retrieveClefs` does not warn.

**DIAG21 — clef parts and evaluations (full-out37).** Added to the
patched `ClefBuilder` (ROUND 14, stripped after the fix was verified):
search rects, every extracted part, and every compound evaluating as
a clef shape.

- Parts are PERFECT under Wasm: staff 1 outer=(365,60,90,217),
  inner=(369,71,86,195), 3 parts — the true G clef as ONE part
  [372,94,55x149] w=2541, plus two 3×6/3×7 specks; staff 2: F clef
  curve [372,421,46x72] w=1235 + two dots [421,428,11x10],
  [421,448,11x11]; staff 3: [72,697,56x148] w=2576; staff 4: F clef
  curve + two dots. (DIAG19's NO_STAFF difference does not corrupt
  the parts.)
- Evaluations are CORRECT under Wasm: staff 1 glyph [372,94,55x149]
  G_CLEF grade **0.9994398345019615** (desktop 0.999440); staff 2
  compound [372,421,60x72] F_CLEF 0.97401…; staff 3 G_CLEF 0.99933…;
  staff 4 F_CLEF 0.95141…. **The classifier is exonerated: right
  glyphs, right positions, right grades.**

**Root cause — the font-based bounds forcing in `registerClefs`.**
`ClefBuilder.registerClefs` (`ClefBuilder.java`, "Force theoretical
bounds as inter bounds!") replaces the inter bounds with
`inter.getSymbolBounds(interline)` plus a centroid translation:

```java
Rectangle clefBox = inter.getSymbolBounds(staff.getSpecificInterline());
Point symbolCentroid = fs.symbol.getCentroid(clefBox);
Point glyphCentroid = inter.getGlyph().getCentroid();
int dx = glyphCentroid.x - symbolCentroid.x;
clefBox.translate(dx, 0);
inter.setBounds(clefBox);
```

Under TeaVM every link of that chain is stub-font geometry:

1. `AbstractInter.getSymbolBounds` centers the font symbol's layout
   box on the glyph center. The shim `TextLayout.getBounds()` returns
   `(0, -ascent, advance, ascent+descent)` with
   `advance = text.length() * size * 0.5`. For the G clef at point
   size 84 (MusicFont.getPointSize(interline 21) = 84): box 42×84,
   vs real Bravura ~56×148. Centered on the glyph center (399,168)
   that gives clefBox (378,126,42,84).
2. `ShapeSymbol.getCentroid` uses `computeCentroidOffset()`, which
   renders the symbol image and computes its mass center. Under the
   stub font the image is BLANK → weight = 0 → `xBar /= weight`
   is 0/0 = NaN → centroidOffset (NaN, NaN) → `getCentroid` does
   `(int) Math.rint(...)` and `(int) NaN == 0` in Java → symbol
   centroid **(0,0)**.
3. `dx = glyphCentroid.x − 0 = 400` (the true G clef's mass-center
   x), so `clefBox.translate(400, 0)` → **(778,126,42,84)**. Every
   number checks out: 42 = 0.5×84, 126 = 168−42, 778 = 378+400.
4. `staff.setClefStop(end)` with `end = (box.x + box.width) − 1`
   where box = glyph bounds ∩ clefBox = EMPTY (no overlap) → width 0
   → end = 778 − 1 = **777** (desktop 427).
5. `selectClef()` → `staff.getCompetingClefs(range.getStop()=777)`:
   looks for clefs with `xClef < 777`; the clef's x is 778 → not
   competing → `header.clef` stays **null**.
6. `HeaderTimeBuilder`'s browseStart is the clefStop (777); the time
   digits at x=451 are before it → **no time inters**.
7. First-column heads: 30 of the 31 sit at x < clefStop 777 (516,
   605, 694 sys1; 164 sys2 vs clefStop 179); the 31st, at x=786,
   overlaps the misplaced clef box (778–820). With the fix (§18.6)
   all 31 return, confirming the chain.

Classification: **spike-side stub-font defect** (same family as §17's
stub-font geometry note), not a TeaVM codegen defect, not an
Audiveris bug (on desktop the font is real, so the chain is correct),
and not a classifier defect.

### 18.6 The fix: glyph bounds for clefs under TeaVM (ROUND 14)

In the patched `ClefBuilder.registerClefs` (spike-only file, repo
untouched), replace the font-based symbol bounds with the glyph
bounds:

```java
Rectangle clefBox = (inter.getGlyph() != null)
        ? inter.getGlyph().getBounds()
        : inter.getSymbolBounds(staff.getSpecificInterline());

if (inter.getGlyph() != null) {
    inter.setBounds(clefBox);
    sig.addVertex(inter);
}
```

(The centroid-translation block is dropped with it.) Patch:
`teavm-fork/clefbuilder-glyph-bounds.patch` (36 lines with headers;
repo file is CRLF, patched copy LF — the patch was generated with
line endings normalized, as in §16). On the hymn the glyph bounds
differ from the desktop font-based bounds by 1px (G clef 55×149 vs
56×148; F clef 60×72 vs 58×75) and restore clefStop=426 (desktop
427). Desktop-neutrality check: the patched `ClefBuilder` alone,
compiled into `phasec/classes-clef/` and run first on the desktop
classpath (`SigDump` on the `.gray` bytes), gives 375 inters with
**only the 4 clef boxes differing** from stock desktop — all 307
heads and everything else byte-identical; clefStop 426/431/127/132;
F staff-1 grade 0.7761 (the stock value).

Durable fix (NOT built here): pre-rendered Bravura symbol metrics
(bounds + centroid) in the font shim, Phase B style — see §18.8.

### 18.7 Results after the fix (full-out38, final build full-out39)

DIAG21 stripped from the patched `ClefBuilder` (ROUND 14 now holds
only the fix); final build full-out39 reproduces out38 exactly.
0 problems, 3,003 classes, 28,298 methods,
`classes.wasm` 13,018,677 bytes. Default stack, exit 0.

- Crop (2480×700): wasm loaded 374 ms, REACH HEADS **7,373 ms**,
  SYSTEMS 1, STAVES 2, **HEADS 189** (was 163; desktop crop 195),
  CHECK 339511 (desktop crop 349915), main() returned in 7,542 ms.
  Clefs correct, times present with exact grades.
- Full page: wasm loaded 391 ms, REACH HEADS **22,512 ms**,
  SYSTEMS 2, STAVES 4, **HEADS 306** (was 276; desktop 307),
  CHECK 538011 (desktop 539192), main() returned in 23,262 ms.
  374 SIG inters (desktop 375).
- Header clefs: sys1 G 0.7996 box 372,94,55,149 and F 0.7792 box
  372,421,60,72; sys2 G 0.7995 box 72,697,56,148 and F 0.7611 box
  73,1023,60,73. Desktop grades: G 0.7996/0.7995 exact, F 0.7761
  (staff 1: Wasm 0.7792, +0.003) / 0.7611 exact. clefStop
  426/431/127/132 (desktop 427/429/128/130 — within 2px).
  `header.clef` non-null on all four staves; the WARN line is gone
  because a clef is genuinely recognised now.
- Times are BACK with **exact desktop grades**: 4 TimeNumberInter
  (0.6672/0.6860/0.7030/0.7392) + 2 TimePairInter (0.9104/0.9144).
  Their boxes are still wrong — see residual (a) below.
- Paired-head analysis (exact-box first, then 6px tolerance, same
  sys/staff/shape): **306/306 paired, 0 Wasm-only, 251 exact-box
  matches** (same 251 as §17). Grade diff mean 0.0054, max 0.0922,
  >0.01: 31, >0.05: 15. dx mean −0.12 (range −2..0), dy mean +0.26
  (range 0..5), 55/306 with y-offset >0. Same class of 1–2px
  near-tie jitter as §17.
- The single full-page difference vs desktop 307: desktop-only head
  (786,394) NOTEHEAD_BLACK grade **0.2423, good=false** — a low-grade
  duplicate 3px right / 6px up from the real head at (783,400)
  grade 0.7846, which Wasm has. On the crop the 6 desktop-only heads
  are the same class (grades 0.426–0.434, all 1px-offset duplicates
  of real heads). No real head is missing on either run.
- Timing vs native: Wasm full page 22,512 ms vs desktop mirror
  16,545 / 19,259 / 20,304 ms — **~1.1–1.4× native LOAD→HEADS**,
  unchanged from §17 (the classifier + fix add no measurable time;
  out38 full was 22,763 ms, out39 22,512 ms — run-to-run noise).
  Caveats from §17 still apply (Wasm skips glyph-rendering /
  distance-transform template construction — precomputed — and skips
  clef recognition work in the old sense; both metrics exclude
  startup: Wasm load ~390 ms).

### 18.8 Residual divergences (all named, none blocking HEADS)

(a) **Time-number boxes still wrong — same stub-font disease, next
builder.** TimeNumberInter boxes are (448,102,42,84) vs desktop
(451,123,36,42); TimePairInter (448,102,42,127) vs (451,123,36,85).
Grades are exact; only the boxes are off (42×84 = the stub
TextLayout box again, y shifted −21). `HeaderTimeBuilder` also
derives bounds from font geometry. Same fix family as the clef fix;
left as-is because the grades (the recognition result) are exact
and the boxes do not affect HEADS.
(b) **Barline/ledger 1–2px jitter.** BarlineInter heights 87–88 vs
desktop 88–89; LedgerInter heights 3–4 vs desktop 4–6 (e.g. ledger
(1465,227,39,3) vs (1465,227,39,5)). Same class as §17; does not
affect HEADS.
(c) **NO_STAFF slight difference** (DIAG19: sum +1020, zeros −4).
Unlocalised (not tiled); parts extracted from it are correct, so it
is not chased here. A per-tile fingerprint would localise it if it
ever matters downstream.
(d) **F_CLEF staff-1 grade 0.7792 vs desktop 0.7761** (+0.003; the
other three clef grades are exact). Unexplained at this level; the
§18.3 patched-vs-stock desktop comparison shows the desktop
patched-classifier F grade is the stock 0.7761, so the +0.003 is a
TeaVM-side evaluation nuance (moments computation under WasmGC),
not the pre-rendered weights. Immaterial at this grade level.
(e) **Low-grade duplicate heads dropped** (one on the full page, six
on the crop; §18.7). Desktop keeps these non-good duplicates; Wasm
drops them. All are 1px-offset duplicates of real heads. Not chased:
they are `good=false` and do not change the note count.

### 18.9 What remains (Phase C completion + beyond)

- **Durable font fix (next step, not built here): pre-rendered
  Bravura symbol metrics — bounds + centroid — in the font shim,
  Phase B style.** `getSymbolBounds` / `getCentroid` are used by many
  inter types, not just clefs and times; every symbol whose bounds
  are forced from the font will show the same disease at the SYMBOLS
  step and beyond. The fix is to pre-render, per shape at the needed
  point sizes, the layout bounds and the centroid offset from the
  real Bravura font on desktop, and have the shim `TextLayout` /
  `ShapeSymbol` return them — the same static-data pattern as Phase B
  templates and the Phase C classifier weights. Until then, the
  spike uses glyph bounds for clefs (ROUND 14) and accepts wrong
  time-number boxes. Do NOT "fix" this by null-guarding the centroid
  or by per-site Audiveris rewrites.
- **Export (JAXB/MusicXML) and OCR (tesseract.js)** are still open;
  TeavmMain still stops at HEADS by design and produces no `.mxl`.
  JAXB is neutered in the spike set (ROUND 5/13); export will need
  either a JAXB replacement or a pre-rendered export path.
  Tesseract cannot run natively under TeaVM (JNI); tesseract.js
  language packs are the GO path (deu 6.77MB, fra 5.99MB, spa 7.98MB
  traineddata), per the PR 5 work.
- **Diagnostic prints still in the builds:** DIAG14 (ROUND 7),
  DIAG16, DIAG17 and DIAG18 prints are still in `TeavmMain.java`
  and the full-out39 build; DIAG19/DIAG20 are in both harnesses.
  DIAG21 was stripped (ROUND 14 now holds only the fix). Strip the
  rest before any "clean" build, per the §14 note.
- **Upstream filings unchanged:** nothing filed. #272 draft (add the
  TPoint2D/TDimension2D note, then Jonathan/his agent files),
  #21244 + two-part core patch. Do NOT file #15448 separately. Do not
  file any issue from the robbie-muse account without Jonathan's
  explicit approval.

### 18.10 Files

- `teavm/patched/make_patches.py` ROUND 13 (classifier) + ROUND 14
  (clef glyph bounds; DIAG21 stripped).
- `teavm/entry/src/teavm/PreRenderedClassifier.java`,
  `PreRenderedClassifierH0..H9` / `O0..O9.java` (842 KB generated
  source); `teavm-fork/phasec/gen_classifier.py`,
  `phasec/classifier.json` (weight SHA-256s), `phasec/src/ClassifierCheck.java`,
  `phasec/src/SigDump.java` (DIAG18/19/20), `phasec/classes-data/`,
  `phasec/classes-patched/`, `phasec/classes-clef/`,
  `phasec/check-stock.txt`, `check-stock2.txt`,
  `check-patched.txt` (+ `.log` files), `phasec/sig-desktop.txt`,
  `phasec/sig-desktop-gray.txt`, `phasec/sig-desktop-cleffix.txt`,
  `phasec/sig-wasm33.txt`, `phasec/heads-wasm32.txt`.
- `teavm-fork/clefbuilder-glyph-bounds.patch` (36 lines, endings
  normalized).
- `teavm-fork/build32.log`, `build33.log`, `build34.log`,
  `build35.log`, `build36.log`, `build37.log`, `build38.log`,
  `build39.log`, `full-build32.log` … `full-build39.log`,
  `run-crop32.log`, `run-crop38.log`, `run-crop39.log`,
  `run-fullout32.log`, `run-fullout33.log`, `run-fullout34.log`,
  `run-fullout35.log`, `run-fullout36.log`, `run-fullout37.log`,
  `run-fullout38.log`, `run-fullout39.log` — builds and runs
  (full-out32/33 pre-fix, full-out34/35 DIAG19, full-out36 DIAG20,
  full-out37 DIAG21, full-out38 fix, full-out39 final, DIAG21
  stripped).
- `teavm-fork/full-out32/` … `full-out39/` — successive WasmGC builds
  (0 problems; full-out39: 3,003 classes, 28,298 methods,
  `classes.wasm` 13,018,677 bytes).
- Nothing was pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 19. Pre-rendered Bravura symbol metrics (bounds + centroid) in the font shim — time boxes now exact; SYMBOLS completes — 2026-11-09 (DONE; SYMBOLS probe done, next wall named)

### 19.1 What §18 left

§18 fixed clefs with a contained patch (ROUND 14: glyph bounds for
clefs in `ClefBuilder`) and left everything else on the stub font. The
open fidelity item was the time-signature boxes: Wasm
`TimeNumberInter (448,102,42,84)` vs desktop `(451,123,36,42)`, and
`TimePairInter (448,102,42,127)` vs `(451,123,36,85)` — same
stub-font disease, one builder downstream (`HeaderTimeBuilder`
derives bounds from font geometry). The §18 residuals were: (a) time
boxes wrong; (b) barline/ledger 1–2 px jitter; (c) NO_STAFF slight
difference (sum +1020, zeros −4); (d) F_CLEF staff-1 grade +0.003;
(e) one dropped low-grade duplicate head on the full page (desktop-only
(786,394) grade 0.2423, `good=false`).

### 19.2 Call-site enumeration — what the stub font gets wrong

Greps over the Audiveris tree (HEADS + SYMBOLS paths) for the
metric calls:

| Call | Stub-font value | Consumers (all confirmed by grep) |
|---|---|---|
| `TextLayout.getBounds()` | `(0, -ascent, advance, ascent+descent)` with `advance = text.length() * size * 0.5f` | `AbstractInter.getSymbolBounds` (every inter's theoretical bounds); `HeaderTimeBuilder` (time numbers); `ClefBuilder.registerClefs` ("Force theoretical bounds as inter bounds!"); `NumDenSymbol.getDimension` → `getParams` → layout bounds (`TimeCustomInter`/`TimeWholeInter`); `OctaveShiftInter.computeValueDimensions`; `BracketInter`; `WedgeInter`; `AbstractPitchedInter`; `MusicFont.computePointSize` (calibration) |
| `TextLayout.getAdvance()` | `text.length() * size * 0.5f` | same layout paths; `MusicFont` point-size calibration |
| `ShapeSymbol.computeCentroidOffset()` → `getCentroid(Rectangle)` | renders the symbol image, takes its mass centre; under the stub font the image is BLANK → weight 0 → `xBar /= weight` is 0/0 = NaN → centroidOffset (NaN, NaN) → `(int) NaN == 0` → centroid **(0,0)** | `ClefBuilder.registerClefs` (centroid translation — the §18 mechanism: clef box translated +400 px, clefStop 777, header.clef null); every later `getCentroid` consumer in SYMBOLS |
| `TextLayout.getAscent()` / `getDescent()` | stub 0.8/0.2 × size | **No callers anywhere in the Audiveris tree** (grep) — left stub |
| `TextLayout.getPixelBounds()` | delegates to `getBounds()` | fixed automatically by the bounds fix |
| `TextLayout.getOutline()` | stub | **No callers** — left stub |
| `TextLayout.draw` | no-op | painting not needed in the pipeline; symbol images stay blank (template building for non-head shapes at SYMBOLS is the §19.10 wall) |
| `FontMetrics` | stub | **No pipeline callers** — left stub |
| `Font.deriveFont(AffineTransform)` | shim returns `this` (transform dropped) | `BraceSymbol.getParams` (`layoutShapeByCode(BRACE, at)`) and `MusicFont.layoutSymbol` (SheetPainter, GUI) — pre-existing, out of HEADS scope, recorded here, not fixed |

Font name under TeaVM: `OmrFont.createFont` falls back to
`new Font(fontName, PLAIN, size)` (RES_URI is null → `UriUtil.toURI`
throws IllegalArgumentException before `Font.createFont` is reached),
so the MusicFont name IS `"Bravura"` under TeaVM (desktop log
confirms `MusicFont[family=Bravura,name=Bravura,style=plain,size=84]`).
Only Bravura is pre-rendered. Other families (Leland/Primus/
FinaleJazz/MusicalSymbols, all with Bravura as backup) fall back to
stub values — existing behaviour, unchanged.

### 19.3 Design — two interception points, Phase B style

1. **Bounds — the `TextLayout` shim**
   (`teavm/shims/src/java/awt/font/TextLayout.java`, hand-written;
   `gen_awt*.py` do NOT overwrite it). When the font name is
   `"Bravura"` and every code point of the text is in the pre-rendered
   table, `getBounds()` / `getAdvance()` compose real Bravura geometry
   from per-codepoint unit metrics (advance + bounds per point size).
   Other fonts / unknown code points fall back to stub values. This
   fixes every `getLayout().getBounds()` consumer at once (§19.2
   table).
2. **Centroid — patched `ShapeSymbol.computeCentroidOffset`**
   (make_patches.py ROUND 15). If the symbol is plain (not decorated,
   not tiny) and pre-rendered centroid ratios exist for
   (shape, family), set `centroidOffset` from the table and return;
   else the original image computation. This fixes `getCentroid`
   everywhere (`ClefBuilder`, and SYMBOLS uses).

**ROUND 14 is SUPERSEDED (deliberately, not by accident):** the §18
`ClefBuilder` glyph-bounds patch is removed; stock `ClefBuilder` is
used unpatched, so the metrics fix alone must prove clefs land
correctly. The patch file
`teavm-fork/clefbuilder-glyph-bounds.patch` is kept as a historical
artifact. The desktop checks (§19.6) and the Wasm runs (§19.8) prove
it: clef boxes, clefStop values and time boxes are now exact with
stock ClefBuilder.

### 19.4 Format, generation, point-size mapping

Generated offline on desktop Java with the real Bravura font
(`Bravura.otf`, loaded via `Font.createFont`), same approach as Phase
B's `templates.json` → generated Java source with static data, no file
I/O, no new shim surface beyond the shim itself:

- **Dump** — `teavm-fork/phase-font/src/SymbolMetricsDump.java`
  (desktop JDK 25 + stock jars, `-Djava.awt.headless=true`) →
  `phase-font/symbol-metrics.json` (113,690 bytes). Results:
  **shapes=225, noSymbol=22, noLayout=15, centroidErr=0,
  codepoints=157; maxLinearityErr=5.02e-4** (per-unit deviation
  across sizes 40/84/168; ≤0.09 px at size 168);
  **composition n=22 fail=0 maxBoundsErr=0.0 maxAdvErr=0.0**
  (multi-code strings compose exactly from singles);
  centroidSizeCheck n=478 imgErr=0 maxErr=0.225 (see below). Sample
  values at size 84: G_CLEF bounds (0.0, −92.234375, 56.359375,
  147.5), advance 56.36407470703125 — matches §18's "Bravura
  ~56×148"; NOTEHEAD_BLACK bounds (0.0, −10.5, 24.78125, 21.0),
  advance 24.780029296875 → ratio 0.2950; TIME_FOUR bounds (1.6875,
  −21.078125, 36.109375, 42.078125), advance 39.48005676269531; space
  (0x20) advance 0.1/size, bounds empty. TIME_FOUR_FOUR is NOT in
  the shapes dump (composite NumDenSymbol, no single code) — handled
  via digit strings in TextLayout. Ascent/descent at 84 are both
  169.0082244873047 (2.012×size, font-level) for both NOTEHEAD_BLACK
  and G_CLEF. Unit metrics in the JSON are taken from reference size
  84 (the size `getSymbolBounds` uses at interline 21); 40/168 only
  check linearity. Dump gotchas fixed en route: `TextLayout` has no
  `getText()` (digit strings rebuilt from TIME_ZERO codes);
  `MetronomeSymbol.getParams` pulls in GUI singletons
  (`StubsController` / BSAF "Application is not launched", surfacing
  as `ExceptionInInitializerError`, an Error — per-shape guards must
  catch `Throwable`, not `Exception`); those shapes are skipped as
  noLayout.
- **Centroid size-dependence diagnosed**
  (`phase-font/src/CentroidDiag.java`): manual mass-centre ratios
  from `buildImage` at size 80 reproduce the reflected
  `centroidOffset` with error **0.0000 for every shape** — the manual
  computation is correct and the stored table is exact. Errors at
  sizes 40/168 (up to 0.225, e.g. STEM 0.177 at 168, THIN_BARLINE
  0.167 at 40) are genuine size-dependence (thin glyphs quantize
  differently at small sizes). Irrelevant to correctness:
  `computeCentroidOffset` always uses the STANDARD_INTERLINE image
  (interline 20 → size 80; `SampleRepository.STANDARD_INTERLINE =
  20`), a single per-symbol value; no code path recomputes the
  centroid at another size (except tiny variants, which use
  TINY_INTERLINE — GUI icons only; the patch leaves tiny/decorated
  symbols on the original path).
- **Generator** — `teavm-fork/phase-font/gen_symbol_metrics.py`
  (run from phase-font/) emits:
  - `teavm/shims/src/java/awt/font/BravuraMetrics.java` (18,709
    bytes; 157 codepoints; static sorted `CPS` + parallel
    `ADV/X/Y/W/H` unit arrays + binary-search `get(cp)` returning
    `{adv,x,y,w,h}` or null);
  - `teavm/entry/src/teavm/PreRenderedSymbolMetrics.java` (16,800
    bytes; 225 shapes; sorted `SHAPES` + `OX`/`OY` arrays + binary
    search; `centroidOffset(shapeName, familyName)` returns null for
    non-Bravura or unknown shapes).
- **TextLayout shim patch**: `getAdvance()` returns composed advance
  (`sum(m[0] * size2D)`) when the table covers the whole string, else
  stub `text.length() * font.getSize() * 0.5f`; `getBounds()` returns
  composed union (each glyph's unit bounds scaled by
  `font.getSize2D()` and translated by cumulative advance; zero-area
  glyphs like space contribute advance only; an all-space string
  returns (0,0,0,0)), else stub `(0, -ascent, advance,
  ascent+descent)`.
- **1/64 snapping was TRIED and REVERTED**: snapping composed bounds
  to the nearest 1/64 (FreeType 26.6 rationale) made the comparison
  WORSE — 9 mismatches/510 vs 4/510 unsnapped, including 5 new rint
  flips at size 92 (e.g. notehead shapes y −14.265625 → −14.25, h
  28.53125 → 28.5) — because the real scaler's per-size values
  wobble by ±1/64 between sizes, so the true value at a given size is
  not reliably on the 1/64 grid implied by the size-84 unit. The snap
  code (`snap64`) was removed from the shim; the unsnapped version is
  the shipped one.
- **Point-size mapping (derived, not fitted)**: with real TextLayout
  bounds, `MusicFont.computePointSize` now calibrates to the DESKTOP
  point size (~92 for the hymn) instead of the stub 54, so the Phase
  B template mapping changed: `DESKTOP_PER_TEAVM_POINT` (1.694827) →
  `DESKTOP_PER_REQUESTED_POINT` = 1.0 (requested == desktop).
  `phaseb/gen_prerendered.py` was updated (derivation comment,
  RATIO = 1.0, constant renamed) and `PreRenderedTemplates.java`
  regenerated — diff vs §17 version is ONLY the mapping + comment
  (24 diff lines, 784,288 bytes, 61,270 key points,
  RATIO=1.000000). The advance ratio a = 0.2950 is still asserted
  constant across catalogs as a sanity check.
- **Stale-file trap found and fixed**: `make_patches.py` never
  cleaned `patched/src`, so the removed ROUND 14 `ClefBuilder.java`
  survived the §19 revert and was compiled into the first build40
  (313 classes). Cross-check found 6 stale files in `patched/src`:
  ClefBuilder.java (with the TEAVM §18 patch — the only harmful one)
  plus 5 verbatim repo copies with NO TEAVM markers
  (ObjectEditor.java, Staff.java, LedgerInter.java,
  AbstractHorizontalInter.java, SIGraph.java — harmless, identical to
  stock). All 6 were deleted manually; a prune step was added to
  `make_patches.py` (`WRITTEN` set populated by `write()`, plus a
  trailing loop deleting any `.java` under OUT not in WRITTEN). After
  deletion + rebuild, patched/classes = 287 (313 − 26: the 6 files
  contain 23 named classes + anonymous/lambda classes ≈ 26). The
  prune printed nothing on the rebuild (nothing stale remained).
  Verified: no "wrote... ClefBuilder" line in build40.log;
  `ShapeSymbol.java` written with the §19 patch.

### 19.5 Shim verification (desktop, before any Wasm build)

`phase-font/src/ShimCheck.java` + `test-strings.txt` (170 strings:
all shape code lists + all 157 single codepoints + digit strings
0/1/2/4/10/12/44/100/120/200/444): stock mode = real JDK TextLayout
with real Bravura.otf loaded via `Font.createFont` (510 lines,
`shimcheck-stock.txt`); shim mode = `--patch-module
java.desktop=<shim-font-classes>` with `new Font("Bravura", PLAIN,
size)`. Two harness gotchas fixed en route: (1) the patch dir must
mirror the package path (`java/awt/font/*.class`) — a flat
`font/*.class` dir silently did NOT override TextLayout (real JDK
TextLayout ran with a fallback font, all 510 mismatched, max diff
204.03); (2) patching the whole `shims/classes` breaks module
resolution (`java.awt.datatransfer` belongs to
`java.datatransfer`), and patching the full `java/awt/font/` dir
breaks JDK internals (`NoSuchFieldError: TextAttribute.WIDTH` from
`sun.font.EAttribute`) — the patch dir must contain ONLY
`TextLayout.class` + `BravuraMetrics.class` (real JDK
`TextAttribute`/`FontRenderContext` are used; TextLayout's Map ctor
referencing `TextAttribute.FONT` links lazily and is never called in
this path). **Final result (unsnapped): 506/510 match exactly on
rinted ints; 4 mismatches, max abs diff 0.0268 px.** The 4:
('57466' G_CLEF_SMALL, 108) w 47.515625 vs 47.51116, h 125.5 vs
125.49777; ('57473,57472' "10" digit pair, 108) x 2.15625 vs 2.16964,
y −27.109375 vs −27.10045, w 82.50951 vs 82.49838, h 54.109375 vs
54.10045; ('58669' DYNAMICS_MF, 108) x −2.15625 vs −2.16964, w 90.5
vs 90.52232, h 64.359375 vs 64.36607; ('59526' TUPLET_SIX, 84) w 25.5
vs 25.499999999999996 (pure double round-trip: 25.5/84*84). Rint
flips by size: 84: 1, 92: 0, 108: 3. All are 1 px, all on values
sitting on a .5 boundary; at the hymn's pipeline sizes (84 for
bounds, 92 for calibration) there is exactly one flip (TUPLET_SIX
width 25 vs 26 — the hymn has no tuplets; immaterial). Accepted and
recorded; the residual 58669@108 (DYNAMICS_MF width 91 vs 90 rinted)
is the same class as the accepted 1–2 px jitter.

### 19.6 Desktop verification (patched Audiveris vs stock)

- **Template mapping** — `phase-font/src/TemplateMappingCheck.java`
  (successor to the Phase B RoundTrip, whose simulated requests
  47/54/64 and `DESKTOP_PER_TEAVM_POINT` no longer exist; RoundTrip
  itself is left untouched as the §17 record): for requested sizes
  80/92/108, compare `PreRenderedTemplates.getTemplate(shape,
  Bravura, requested)` field-by-field against the live catalog
  template at that size. **72/72 PASS, 0 failures**; fallbacks
  (Leland/54, Bravura/10, Bravura/200) all correctly null
  (`template-mapping.log`).
- **DesktopHeads patched-first vs stock** — stock: REACH HEADS
  16,365 ms, HEADS 307, CHECK 539192. Patched-first (isolated
  `classes-patched19/` containing ONLY the patched `ShapeSymbol`,
  first on the classpath; `teavm/patched/classes` LAST so the stock
  `LoadStep`/classifier win and only the `teavm.*` data classes are
  visible): REACH HEADS 16,933 ms, **HEADS 307, CHECK 539192 —
  identical**. (First attempt failed instructively: putting the whole
  `patched/classes` first loads the patched `LoadStep`, which reads
  its image from the JS-supplied `TeavmImageHolder` — "No image
  supplied from JS". Second attempt failed with
  `ClassNotFoundException: teavm.PreRenderedSymbolMetrics` — the
  isolated dir does not contain the data class. Both are harness
  classpath facts, not product defects.)
- **SigDump patched-first vs stock** — **0 diff lines** over the
  whole SIG (all inters, boxes, grades, clefStop identical).
- **ClassifierCheck patched-first** — HEADS 307 CHECK 539192,
  `patched=false` (stock classifier on this classpath — correct, this
  isolates the centroid patch); clefs at exact desktop boxes/grades
  (G 0.7996 box 372,94,56,148; F 0.7761 box 372,419,58,75; TIME
  0.9104 box 451,123,36,85 / 0.9144 box 451,422,36,85; sys2 clefs
  exact). The stock ClassifierCheck run itself could not write its
  file (it references `teavm.PreRenderedClassifier` at line 114 even
  in the stock run — needs `patched/classes` on the classpath; the
  SigDump 0-diff comparison is the decisive one). Conclusion: the
  centroid patch + ROUND 14 revert are **fully desktop-neutral at
  HEADS**.

### 19.7 The TColor blocker (fork classlib fix — same family as #272)

First full-out40 compile: exit 0, wasm generated, but **2 PROBLEM
ERRORs**, both in `ShapeSymbol`:

```
PROBLEM ERROR | Method java.awt.Color.<init>(IZ)V was not found
    | org.audiveris.omr.ui.symbol.ShapeSymbol.computeCentroidOffset()V
PROBLEM ERROR | Field java.awt.Color.MAGENTA was not found
    | org.audiveris.omr.ui.symbol.ShapeSymbol.buildImage(...)L...SymbolImage;
```

**Why out39 had 0 problems and out40 has 2:** TeaVM's analysis is
reachability-driven. The §18 ClefBuilder patch REMOVED the
`fs.symbol.getCentroid(clefBox)` call — the only reachable
`ShapeSymbol.getCentroid` call in the HEADS path (other
`getCentroid()` hits are Glyph/Section centroids, different
classes) — so `computeCentroidOffset` and `buildImage` were dead code
in out39. Reverting ROUND 14 in §19 restored the stock call, making
both methods reachable and exposing the two missing `TColor`
members. Verified by javap on the fork classlib jar: `TColor` has
ONLY BLACK/WHITE + 5 ctors + getters — no MAGENTA, no
`Color(int, boolean)` ctor. The shim `Color.java` HAS them, but the
classlib wins over the shim (per §7/§14: "Color constants added to
the shim are shadowed and ineffective").

**Fix (contained, fork-classlib, same family as the TPoint/TDimension
fix):** `teavm-fork/teavm-classlib-color.patch` (47 lines) against
`src/classlib/.../TColor.java` in the fork (0.16.0 tag e87d452): the
11 JDK standard colour constants (values identical to the shim's)
plus `TColor(int rgba, boolean hasAlpha)` with JDK semantics
(hasAlpha ? alpha from top byte : 255). Scope note: `getRGB()` and
`decode()` are NOT added — already known-missing and worked around
spike-side (`Constant.java:579`, `TemplateFactory.java:123–129`,
`DistanceTable.java:125`). The jar entry was replaced in place
(`lib-fork/teavm-classlib-0.16.0.jar`; pre-color jar kept as
`teavm-classlib-0.16.0-pre-color.jar`); single-entry replacement
rather than a full 1,510-class rebuild, since TColor is a leaf class
(verified by javap on the jar: 11 constants + `(int, boolean)` ctor
present). Classification: **TeaVM classlib defect** (incomplete JDK
surface), fixed in the fork; candidate for upstreaming with the
#272/#21244 filings. The failed out40 build is kept as-is
(`full-out40/`, `full-build40.log` with the 2 problems); the §19
build is full-out41.

### 19.8 Wasm runs — full-out41 (default stack, Node v24.22.1)

0 problems, 3,005 classes, 28,311 methods, `classes.wasm`
13,043,980 bytes.

| | Crop (2480×700) | Full hymn (2480×3507) |
|---|---|---|
| Load | 392 ms | 392 ms |
| Template line | `requested 92 maps to desktop catalog 92` (§19 mapping confirmed in the log) | same |
| REACH HEADS | 7,491 ms | 22,772 ms |
| SYSTEMS / STAVES / HEADS / CHECK | 1 / 2 / 189 / 339511 | 2 / 4 / **306 / 538011** |
| main() returned | 7,658 ms (exit 0) | 23,409 ms (exit 0) |

HEADS count and CHECK are **identical to §18** (306/538011 full,
189/339511 crop). Timing vs native: Wasm full page 22,772 ms vs
desktop mirror 16,545 / 19,259 / 20,304 ms — **~1.1–1.4× native
LOAD→HEADS**, unchanged from §17/§18 (same caveats: Wasm skips
glyph-rendering/distance-transform template construction; Wasm does
extra work on false heads and skips clef recognition; both exclude
startup).

**The §19 target is HIT — time boxes now match desktop exactly:**

| Inter | Wasm out41 | Desktop | §18 Wasm |
|---|---|---|---|
| G_CLEF sys1 | 0.7996, box 372,94,56,148 | 0.7996, 372,94,56,148 | same box |
| F_CLEF sys1 | 0.7792, box 372,419,58,75 | 0.7761, 372,419,58,75 | same box |
| G_CLEF sys2 | 0.7995, box 73,697,56,148 | 0.7995, 73,697,56,148 | same box |
| F_CLEF sys2 | 0.7611, box 73,1021,58,75 | 0.7611, 73,1021,58,75 | same box |
| TimeNumber ×4 | 0.6672/0.6860/0.7030/0.7392, boxes 451,465 / 451,123 / 451,166 / 451,422, all 36×42 | identical | 448,102,42,84 |
| TimePair ×2 | 0.9104/0.9144, boxes 451,123,36,85 / 451,422,36,85 | identical | 448,102,42,127 |
| clefStop (DIAG20) | 427 / 429 / 128 / 130 | 427 / 429 / 128 / 130 | 426 / 431 / 127 / 132 |

**§18 residuals — status:**
(a) Time boxes — **FIXED** (table above).
(b) Barline/ledger 1–2 px jitter — **unchanged** (e.g. barline
1647,122,4,87 vs desktop 1647,121,4,89; grades 0.8000 vs 0.7966).
(c) NO_STAFF slight difference — **unchanged** (DIAG19 identical to
§18: fnv `eef833d79e8efb16`, sum 2174104755, zeros 171459; BINARY
identical both sides).
(d) F_CLEF staff-1 grade +0.003 — **unchanged** (0.7792 vs 0.7761;
other three clef grades exact).
(e) Dropped low-grade duplicate heads — **unchanged in kind, refined
in detail**: paired analysis (exact-box first, then ≤3 px): 251
exact-box pairs (identical to §18); 300 paired total; 6 Wasm heads
unpaired, 7 desktop heads unpaired. The 6 Wasm-unpaired are
NOTEHEAD_BLACK grade ~0.431 at y=211 (x=516/605/1072/1670/2063/
2152); the 6 corresponding desktop heads are at y=206, x+1/+2, w
24/25, grades 0.430–0.436 — the SAME six notes, 5 px lower and
1–2 px narrower in Wasm (dy range 0..5 was already in §18's paired
stats, so this is not a §19 regression). The 7th desktop-only head
is the §18 one: (786,394) grade 0.2423, `good=false`. Three
exact-box shape flips: Wasm NOTEHEAD_VOID ~0.195–0.202 vs desktop
NOTEHEAD_BLACK ~0.789 at (516,421), (1072,421), (1283,421) — with
the complementary flip 1 px away (Wasm BLACK 0.791 vs desktop VOID
0.195 at the same positions): both a BLACK and a VOID head exist 1
px apart in both runs, and which one lands on the exact box is
swapped — a near-tie in `evaluate()` flipping, benign, same class
as §17's near-tie note. Excluding the 3 flips, pass-1 grade diffs
are max ≤0.05 (4 pairs >0.01, 3 of them the flips).

### 19.9 SYMBOLS probe — full-out42 (contained extension, then restored)

Task step 3 allowed attempting the extension past HEADS only if
small/contained. It was: `TeavmMain.java` line 75 hardcodes
`stub.reachStep(OmrStep.HEADS, false)` (no CLI step parameter), so
the probe temporarily changed it to `OmrStep.SYMBOLS`, rebuilt
(build42.log, BUILD OK), compiled full-out42 (0 problems, 3,005
classes, 28,311 methods — same counts as out41), ran crop then full,
then **restored `TeavmMain.java` to HEADS byte-identically** (diff
against the saved copy: identical) and re-ran build.sh (build43.log,
BUILD OK, 287 classes). The tree is back in the canonical HEADS
state; out41 remains the §19 HEADS build, out42 the SYMBOLS probe.

| | Crop | Full hymn |
|---|---|---|
| Exit / LATEST STEP | 0 / SYMBOLS | 0 / SYMBOLS |
| Time to step ("REACH HEADS" label) | 14,066 ms | 38,167 ms |
| SYSTEMS / STAVES / HEADS / CHECK | 1 / 2 / 80 / 144035 | 2 / 4 / **128 / 225604** |
| main() returned | 14,248 ms | 38,824 ms |

**SYMBOLS completes cleanly under WasmGC — no trap.** The head
count after SYMBOLS is the telling number: 128 on the full page,
exactly the desktop final `.mxl` note count — SYMBOLS prunes the
BLACK/VOID duplicate pairs HEADS leaves behind (189 → 80 on the
crop for the same reason).

Desktop SYMBOLS reference — new harness
`phase-font/src/SigDumpSymbols.java` (SigDump with HEADS→SYMBOLS
plus the TeavmMain post-step counts): **SYSTEMS 2 STAVES 4 HEADS
128 CHECK 225596, 590 inters** (`sig-desktop-symbols.txt`,
`sig-desktop-symbols.log`). Comparison vs Wasm (539 inters):

- Heads: **128/128, all paired within 3 px, 0 unpaired either
  side**; grade diff max 0.0899, mean 0.0050. CHECK 225604 vs
  225596 (diff 8 = a few 1 px box diffs). **The note content after
  SYMBOLS is identical in count and position.**
- Total SIG: desktop 590 vs Wasm 539 (−51). The deficit is
  concentrated in non-head symbol recognition — exactly the
  predicted wall: `SymbolsBuilder` matches glyphs against templates
  built from font images, which are BLANK under the stub font (Phase
  B pre-rendered templates cover ONLY the 24 head shapes in
  `ShapeSet.Heads`). By class/shape: TUPLET_SIX 38 → 12, TUPLET_THREE
  6 → 3, OctaveShift QUINDICESIMA 17 → 2, Alter FLAT 10 → 5,
  Fermata 4 → 1, Articulation ACCENT 4 → 1, Dynamics F 30 → 27.
  (Wasm also finds some desktop misses: Dynamics P 9 → 11, PP 0 →
  3, MORDENT 0 → 3.)
- `good=true` counts (what actually affects output): TUPLET_SIX
  desktop 3, Wasm 0 (−3 real tuplets missed); DYNAMICS_F desktop
  19, Wasm 15 (−4 real dynamics missed); DYNAMICS_P desktop 2,
  Wasm 3 (+1); FERMATA 1 = 1; everything else (clefs, times,
  barlines, stems, chords, ledgers) matches in count. So the
  material SYMBOLS gap is small but real: **3 good tuplets + 4 good
  dynamics missed (net)**, from blank non-head templates.

### 19.10 Verdict: DONE — metrics fix works; SYMBOLS completes; next wall is pre-rendered symbol templates for non-head shapes

- Pre-rendered Bravura symbol metrics (bounds + centroid) work:
  time-signature boxes are now **exact** vs desktop with stock
  ClefBuilder (ROUND 14 superseded deliberately), clefStop values
  exact, HEADS 306/538011 unchanged from §18, Wasm still ~1.1–1.4×
  native LOAD→HEADS.
- The fork-classlib TColor fix (11 constants + `(int, boolean)`
  ctor) is a second classlib defect in the same family as #272,
  found because the ROUND 14 revert re-exposed the reachable
  `getCentroid` path. Candidate for upstreaming with #272/#21244.
- **SYMBOLS now completes under WasmGC** (full-out42, exit 0, 38.8
  s full page) with head content identical to desktop (128/128).
  This was NOT expected to work in this task — it worked because
  the metrics fix removed the font-geometry blocker and the
  SYMBOLS step itself needs no further shim/classlib fix on this
  page.
- **Next wall (recorded, not started): pre-rendered symbol
  templates for non-head shapes**, Phase B style — the same
  treatment Phase B gave the 24 head shapes, extended to the shapes
  `SymbolsBuilder` matches (tuplets, octave shifts, fermatas,
  articulations, alters, dynamics, and the rest of `ShapeSet`). The
  gap to close is small and measured: 3 good tuplets + 4 good
  dynamics (net) on the hymn page. After that: export (JAXB/
  MusicXML) and OCR (tesseract.js) — still open; TeavmMain stops at
  HEADS by design in the canonical build, no `.mxl`.
- **DIAG prints: LEFT IN, deliberately.** DIAG14/16/17/18/19/20
  prints are still in the builds (out41/out42). They are the
  instrumentation every §19 comparison rested on (DIAG19/20
  fingerprints, DIAG17 head dump, SIG dump); stripping them now
  would destroy the ability to re-verify out41/out42 without
  rebuilding. A "clean" build still needs them stripped — a
  mechanical step for later, not done here.

### 19.11 Files

- `teavm-fork/phase-font/` — `src/SymbolMetricsDump.java`,
  `src/CentroidDiag.java`, `src/ShimCheck.java`,
  `src/TemplateMappingCheck.java`, `src/SigDumpSymbols.java`,
  `symbol-metrics.json`, `gen_symbol_metrics.py`,
  `test-strings.txt`, `shimcheck-stock.txt`,
  `shimcheck-shim.txt`, `shim-font-classes/` (TextLayout.class +
  BravuraMetrics.class only), `template-mapping.log`,
  `desktop-heads-19stock.log`, `desktop-heads-19patched.log`,
  `check-19patched.txt`, `sig-19stock.txt`, `sig-19patched.txt`,
  `sig-desktop-symbols.txt`, `sig-desktop-symbols.log`,
  `sig-wasm42.txt`, `sig-symbols-diff.txt`,
  `heads-wasm41.txt`, `classes-patched19/` (isolated patched
  ShapeSymbol only).
- Generated sources — `teavm/shims/src/java/awt/font/BravuraMetrics.java`,
  `teavm/entry/src/teavm/PreRenderedSymbolMetrics.java`;
  regenerated `teavm/entry/src/teavm/PreRenderedTemplates.java`
  (RATIO = 1.0).
- Patches — `teavm-fork/teavm-classlib-color.patch` (47 lines,
  TColor); `teavm/patched/make_patches.py` ROUND 15 (centroid patch)
  + prune step, ROUND 14 now a supersession comment only;
  `teavm-fork/clefbuilder-glyph-bounds.patch` kept as a historical
  artifact (superseded).
- Jars — `teavm-fork/lib-fork/teavm-classlib-0.16.0.jar` (TColor
  entry replaced); `teavm-classlib-0.16.0-pre-color.jar` (rollback
  copy).
- Builds/logs — `teavm-fork/build40.log` (BUILD OK, 287 classes),
  `full-build40.log` (the 2-problem failed compile),
  `full-build41.log` (0 problems, 3,005 classes, 28,311 methods),
  `run-crop41.log`, `run-fullout41.log`, `build42.log`,
  `full-build42.log`, `run-crop42.log`, `run-fullout42.log`,
  `build43.log` (restore build, BUILD OK).
- `full-out40/` (failed compile, kept), `full-out41/` (§19 HEADS
  build), `full-out42/` (SYMBOLS probe build).
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 20. The §19 SYMBOLS "gap" is an input artefact; the pipeline runs to PAGE, identical to desktop — 2026-11-09 (DONE; next wall is export, §21)

### 20.1 The §19 attribution was wrong — no non-head template consumer exists

§19.9 attributed the SYMBOLS deficit (desktop 590 vs Wasm 539 inters,
concentrated in TUPLET_SIX 38→12, QUINDICESIMA 17→2, FLAT 10→5,
DYNAMICS_F 30→27) to "templates built from font images, which are BLANK
under the stub font". That mechanism does not exist in the production
path, verified by grep over the Audiveris tree:

- `TemplateFactory.Catalog.buildAllTemplates` builds templates ONLY for
  `ShapeSet.Heads` (the 24 head shapes Phase B pre-rendered). No catalog
  exists for any other shape.
- `Template.getKeyPoints()` lazily calls
  `TemplateFactory.retrieveKeyPoints(shape, family, pointSize)` — but its
  only production callers are head paths (`HeadInter.getTemplate`,
  `SymbolsFilter` head erasure) and UI (`TemplateBoard`, `TemplateView`,
  `TemplateFactory.buildDecoratedImage`). Nothing in
  `SymbolsBuilder` / `InterFactory` / `TupletsBuilder` / `RhythmsStep`
  builds or evaluates a non-head template.
- `SymbolsBuilder.evaluateGlyph` creates every one of the missing shapes
  (TUPLET_SIX, QUINDICESIMA, FLAT, DYNAMICS_F/P, ACCENT, FERMATA,
  MORDENT, TR) from `classifier.evaluate(glyph, ...)` — the neural
  classifier, which §18 proved bit-identical to desktop (G_CLEF 0.99944).
  `DistanceMatching.matchAll` (the only template-matching consumer
  outside heads) has NO callers in the app.

So pre-rendering non-head templates could not have changed any of those
counts. The task's step 1 was therefore re-scoped on the evidence: find
the real mechanism first, build templates only if a consumer exists.
None does.

### 20.2 The real mechanism: the desktop comparison ran on a different input

The §19 desktop reference (`SigDumpSymbols` on
`test-material/hymn-satb.png`) and the Wasm run read DIFFERENT grey
images:

- Desktop Audiveris converts max-RGB to grey on load
  (`ImageUtil: Converting max RGB to gray`).
- Wasm reads `teavm/hymn-satb.gray`, a luminance conversion of the same
  PNG. 49,629 of 8,697,360 pixels differ (max abs diff 99; verified with
  PIL on the regenerated `/tmp/hymn-gray.png`).
- §17 exonerated the input at HEADS only (307 identical on both inputs);
  §18 exonerated it for clefs/times only (375 inters). Nobody had run
  the SYMBOLS comparison on identical input.

DIAG19 proves the input difference propagates: desktop-on-PNG BINARY
fnv `6d153878f2250bcb`, sum 2159121720, zeros 230216; desktop-on-gray
and Wasm BINARY fnv `2ec748066257305c`, sum 2157206415, zeros 237727 —
identical. The PNG-vs-gray BINARY difference (7,511 zero pixels) is the
same order as the NO_STAFF difference that follows it.

### 20.3 Decisive experiment — desktop SigDumpSymbols on the .gray bytes

`/tmp/hymn-gray.png` regenerated from `teavm/hymn-satb.gray` (PIL,
mode L, 2480×3507); stock jars, `SigDumpSymbols` unchanged:

- **SYSTEMS 2 STAVES 4 HEADS 128 CHECK 225596, 539 inters** —
  exactly the Wasm out42 numbers (539 inters, HEADS 128, CHECK 225604;
  CHECK differs by 8 = a few 1 px box diffs).
- Per-shape counts desktop-gray vs Wasm out42: IDENTICAL for every
  shape (TUPLET_SIX 12/12, QUINDICESIMA 2/2, FLAT 5/5, DYNAMICS_F 27/27
  good 15/15, DYNAMICS_P 11/11, MORDENT 3/3, ACCENT 1/1, FERMATA_BELOW
  1/1, TR 1/1). Good counts identical everywhere.
- Pairing (≤3 px): **539 paired, 0 unpaired either side**; grade diff
  max 0.0899, mean 0.0019, 17 pairs >0.01; no good-flips.

The §19 "gap" (590 vs 539, 3 good tuplets + 4 good dynamics missed)
is ENTIRELY input-driven. On identical input the SYMBOLS step under
WasmGC is exactly equal to desktop in counts. The PNG-vs-gray
difference flips marginal classifier evaluations (the missing inters
are mostly good=false, grades 0.12–0.45, near the min-grade cutoff) —
which is also why Wasm finds some desktop-PNG misses (DYNAMICS_PP
0→3, MORDENT 0→3): borderline flips, symmetric, not a one-sided
template failure. Files: `phase20/sig-desktop-gray-symbols.txt`
(539), `phase20/sig-desktop-gray-symbols.log` (44 MB, full log).

### 20.4 TeavmMain now runs to PAGE — stepwise, canonical (full-out44/46/47)

`TeavmMain.java` no longer stops at HEADS by design. After the HEADS
counts and DIAG17/18 dumps it loops
`SYMBOLS → LINKS → RHYTHMS → PAGE` with `stub.reachStep(step, false)`
(incremental — each call runs only the steps after the latest reached
one), printing `REACH <step> ms=<step> totalMs=<since LOAD> LATEST=...
HEADS=... SIG=... CHECK=...` at each, then a full SIG dump after PAGE
(prefix `SIGP`, same format as DIAG18) and a score summary
(`SCORE parts=... measures=...`). The HEADS numbers are unchanged and
still comparable to §17–§19. Desktop mirror: new harness
`phase20/src/SigDumpPage.java` (same step sequence, same REACH/SIGP/
SCORE lines, plus DIAG19/DIAG22/DIAG23), run on `/tmp/hymn-gray.png`.

Full hymn page, default stack, Node v24.22.1:

| Step | Wasm out44 (ms) | Wasm out46/47 (ms) | Desktop-gray (ms) | SIG (both) |
|---|---|---|---|---|
| LOAD→HEADS | 22,771 | 22,775 / 22,7xx | 15,957 | 306 heads |
| +SYMBOLS | +16,276 (total 39,160) | +16,391 / +16,536 | +5,244 (total 21,204) | 539 |
| +LINKS | +122 (39,283) | +104 / +109 | +94 (21,302) | 494 |
| +RHYTHMS | +128 (39,412) | +117 / +161 | +106 (21,409) | 494 |
| +PAGE | +15 (39,460) | +37 / +10 | +60 (21,470) | 491 |
| SCORE | parts=2 measures=8 | parts=2 measures=8 | parts=2 measures=8 | — |

- `full-out44`: 0 problems, 3,007 classes, 28,319 methods, load
  365 ms, main() returned 39,957 ms, exit 0. Crop: HEADS 7,358 ms,
  SYMBOLS 80 heads / SIG 331, LINKS 308, RHYTHMS 308, PAGE 308,
  SCORE parts=2 measures=5, 14,353 ms, exit 0.
- `full-out46` (DIAG22) and `full-out47` (DIAG22+DIAG23): same counts
  at every step (SIGP 491, byte-identical SIGP dumps across
  out44/46/47 — `diff` empty), 0 problems, 3,007 classes.
- Desktop-gray SigDumpPage runs: 21,470 ms (first), 24,216 ms and
  24,826 ms (repeats with DIAG22/23; host load varies) — same SIG
  539/494/494/491 and SCORE 2/8 every time.
- **SIGP comparison (desktop-gray vs Wasm out44): 491 = 491, all
  paired within 3 px, 0 unpaired either side, per-shape counts
  identical, grade diff max 0.0899, mean 0.0021, 17 pairs >0.01, no
  good-flips.** The whole pipeline through PAGE is identical to
  desktop on identical input, modulo small grade/box noise (barline
  1–2 px jitter, e.g. 1647,121,4,89 vs 1647,122,4,87, grades 0.7932 vs
  0.8000 — same class as §18/§19).
- Timing: Wasm total to PAGE ~39.5 s vs desktop-gray ~21.5–24.8 s
  (~1.6–1.8×). SYMBOLS is the slowest relative step under Wasm
  (~3.1×: 16.3 s vs 5.2 s — classifier evaluations + glyph
  clustering, pure-Java doubles); HEADS ~1.4×; LINKS/RHYTHMS/PAGE
  are ~100 ms each on both sides. The crop timing runs the other way
  on SYMBOLS in §17's table and is host-load noise — not quoted.

### 20.5 NO_STAFF residual — localised to 4 pixels (DIAG22/DIAG23)

The §18 residual (NO_STAFF sum +1020, zeros −4 under Wasm on identical
BINARY input) is now localised exactly:

- DIAG22 (per-row FNV/sum/zeros, 3,507 rows both sides): only rows
  483 and 484 differ. Row 483: sum +255, zeros −1. Row 484: sum +765,
  zeros −3. (Total +1020, −4 — matches DIAG19 exactly.)
- DIAG23 (zero-pixel x lists for rows 483/484): the differing pixels
  are **(387,483), (385,484), (386,484), (387,484)** — value 0 on
  desktop, 255 under Wasm. Each is the leftmost pixel of a short
  zero-run (row 483: 387–395; row 484: 385–394), at x≈385–395,
  y≈483–484 — just below staff 2 of system 1, at the left edge of a
  small ink blob (a stem/head edge). Wasm's staff removal eats 4
  edge pixels desktop keeps.
- Classification: staff-removal rounding/threshold difference under
  TeaVM (code site unlocalised — `StaffLineCleaner`/`LagManager`
  family, the §12–13 area); zero effect on this page's SIG (539/539,
  491/491). Not chased further in this round: fixing it would need
  instrumenting the cleaner, and the effect is nil here. It is the
  last known Wasm-vs-desktop image difference.

### 20.6 Verdict: DONE — pipeline complete to PAGE; export is the wall (§21)

- The §19 SYMBOLS gap does not exist on like-for-like input. No
  non-head templates were built (none are consumed); the Phase B
  treatment stays heads-only, correctly.
- TeavmMain runs LOAD→PAGE end to end under TeaVM WasmGC at the
  default stack, exit 0, with SIG counts identical to desktop at
  every step on identical input.
- Remaining known divergences: NO_STAFF 4 pixels (§20.5, nil effect);
  grade noise max 0.0899 (17 pairs >0.01, no good-flips); barline
  1–2 px jitter; the single non-good duplicate head (786,394) from
  §18; TextsStep is neutered (no OCR — lyrics need tesseract.js,
  as in the repo's BrowserOCR path, out of scope for TeavmMain).
- DIAG prints: LEFT IN, deliberately (DIAG14/16/17/18/19/20/22/23 —
  every §20 comparison rests on them). Strip only before a "clean"
  build.
- Next wall: **export (§21)** — JAXB marshalling does not build under
  TeaVM. After that: OCR (tesseract.js) for lyrics, then a clean
  build (strip DIAGs).

### 20.7 Files

- `teavm/entry/src/teavm/TeavmMain.java` — stepwise loop to PAGE,
  SIGP dump, SCORE print, DIAG22, DIAG23.
- `teavm-fork/phase20/` — `src/SigDumpPage.java`, `classes/`,
  `sig-desktop-gray-symbols.txt` + `.log` (desktop SYMBOLS on .gray),
  `sigp-desktop-gray.txt`, `sigp-desktop-gray2.log`,
  `sigp-desktop-gray3.log`, `sigp-wasm44.txt`, `sigp-wasm46.txt`,
  `sigp-wasm47.txt` (identical across builds), `diag22-desktop.txt`,
  `diag22-wasm.txt`, `diag23-desktop.txt`, `diag23-wasm.txt`.
- Builds/logs — `build44.log`, `full-build44.log` (0 problems, 3,007
  classes), `run-crop44.log`, `run-fullout44.log`; `build46.log`,
  `full-build46.log`, `run-crop46.log`, `run-fullout46.log`;
  `build47.log`, `full-build47.log`, `run-fullout47.log`;
  `full-out44/`, `full-out46/`, `full-out47/` (all 0 problems).
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 21. Export attempt — JAXB marshalling does not build under TeaVM — 2026-11-09 (BLOCKED: genuine blocker, no .mxl)

### 21.1 What was attempted

`TeavmMain` called `ScoreExporter` directly after PAGE (full-out45),
bypassing the neutered `Book.export` (ROUND 4: "no JAXB export in
WASM"):

```java
Score score0 = book.getScores().get(0);
ByteArrayOutputStream baos = new ByteArrayOutputStream();
new ScoreExporter(score0).export(baos, false, "score", false);
```

`ScoreExporter.export(OutputStream, ...)` does
`PartwiseBuilder.build(score)` (pure Java, in the patched set since
ROUND 3) then `Marshalling.marshal(scorePartwise, os, signed, 2)`
— `org.audiveris.proxymusic.util.Marshalling`, which does
`JAXBContext.newInstance(ScorePartwise.class)` +
`Marshaller.marshal(...)` via the JAXB RI 4.0.5
(`jakarta.xml.bind` + `org.glassfish.jaxb.runtime`). The XML was to
be printed base64 for comparison with desktop's `.mxl`.

### 21.2 Result — the build itself fails: 102 PROBLEM ERRORs, no wasm

`full-build45.log`: "Output file built with errors", **102 PROBLEM
ERRORs**, and although TeaVM prints `generated:
[../teavm-fork/full-out45/classes.wasm]`, the directory is EMPTY —
no wasm is emitted. The export call cannot even be attempted at
runtime; it breaks the whole module build. The only change between
the green full-out44 (0 problems) and full-out45 is the export
try-block, so the export call is the cause.

Grouped missing surface (102 errors):

| Missing | Count | Notes |
|---|---|---|
| `javax.xml.namespace.QName` | 44 | Used pervasively by the JAXB RI model (NameBuilder, TypeInfo, PropertyInfo, QNameMap, ...) |
| `java.lang` module/classloader surface | 29 | `Class.getModule()` (13), `java.lang.Module` (8), `ClassLoader.getResource/loadClass` (4), `Class.getPackageName`, `StackWalker`, `java.beans.Introspector`, `Package.getImplementationVersion`, `SecurityManager.checkPackageAccess` |
| `javax.xml.datatype` | 8 | `DatatypeFactory`, `Duration`, `DatatypeConstants` (DATETIME/GMONTH/GDAY) |
| `org.xml.sax` | 6 | `SAXException`, `SAXParseException`, `DefaultHandler`, `Locator`, `LocatorImpl` |
| `javax.xml.transform` | 4 | `TransformerFactory`, `StreamResult`, `SAXResult`, `DOMSource` |
| `javax.xml.validation.Schema` | 1 | |
| `java.util.zip.ZipOutputStream(OutputStream, Charset)` ctor | 1 | `.mxl` (compressed) path in `Mxl.Output` — the uncompressed path was attempted, but the ctor is reachable |
| `java.util.logging.Logger.setUseParentHandlers` | 1 | `jakarta.xml.bind.ContextFinder` |
| `java.security.BasicPermission` / `jakarta.xml.bind.JAXBPermission` | 2 | |
| `com.sun.istack.SAXParseException2` | 1 | |
| `org.audiveris.omr.ui.view.RubberPanel` GUI methods | 3 | `revalidate/getVisibleRect/scrollRectToVisible` — a secondary reachability leak: some newly reachable class pulls in UI view classes (RubberPanel is referenced by SheetView/ImageView/etc.); shim-able in isolation, irrelevant while JAXB is blocked |

### 21.3 Classification — genuine blocker, not a contained shim fix

Shimming the listed classes alone would not suffice. The JAXB RI
builds its binding model **reflectively at runtime**
(`JAXBContext.newInstance` → model introspection over the whole
proxymusic model, `Class.forName`, `ServiceLoader` for the
`JAXBContextFactory`, `java.beans` introspection, annotation reading).
TeaVM's reflection support is the narrow `ReflectionPolicy` the spike
uses for a handful of ConstantSet fields (§10) — extending it to the
entire proxymusic model (hundreds of generated classes, fields and
annotations) plus the RI's reflective machinery is a project of its
own, not a bounded round. The `javax.xml.*` shims alone (QName,
DatatypeFactory, SAX, transform) are each small, but they only move
the failure to the next runtime reflection step.

### 21.4 Next step (not built): Phase D — a hand-rolled MusicXML writer

The product-correct path is a **non-JAXB MusicXML writer in Java**:
walk the already-computed `Score`/`Page`/`Measure`/`Note` model
directly (the same data `PartwiseBuilder` walks) and write MusicXML
text with `StringBuilder`/`ByteArrayOutputStream` — no proxymusic
marshalling, no JAXB, no reflection. Verify on desktop first (run
the writer on desktop against the same Score and diff against
Audiveris's own `.mxl`: 128 notes, 2 parts, 16 measures for the
hymn — §16), then wire it into TeavmMain and print/return the XML
base64. Estimated 1–2 days: notes/rests/clefs/keys/times/barlines/
divisions/durations/pitches first (enough for MuseScore/Sectional
to open it), then ties/beams/tuplets/dynamics. The JS-side
alternative (expose the Score model to JS via JSO and serialise
there) is the same modelling work split across languages; the
Java-side writer keeps it in one place and is desktop-testable.

### 21.5 Cleanup and state

- The export try-block was REMOVED from `TeavmMain.java` again; the
  canonical build is green (full-out47, 0 problems, 3,007 classes).
  `full-out45/` is kept as an empty dir with its `full-build45.log`
  (the 102-error record); no wasm was ever produced for it.
- `Book.export` stays neutered (ROUND 4). Nothing else changed for
  export; `PartwiseBuilder` remains in the patched set (ROUND 3).
- Harness gotcha recorded: if `build.sh` fails (e.g. the §20
  `w`/`h` variable shadowing in DIAG22 — fixed by renaming to
  `nw`/`nh`), the full compile crashes with a misleading NPE in
  `EntryPointTransformation.getMainMethod` ("cls is null") because
  `TeavmMain.class` is absent — check `build.sh` first.

### 21.6 Files

- `teavm-fork/full-build45.log` (102 PROBLEM ERRORs), `build45.log`,
  `run-crop45.log` (ENOENT: no `full-out45/classes.wasm`).
- `full-out45/` (empty — no wasm emitted).
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

---

## 22 Phase D — hand-rolled non-JAXB MusicXML writer (2026-11-09) — DONE, first WasmGC .mxl

### 22.1 Design

`teavm/entry/src/teavm/MxlWriter.java` (3,104 lines), package `teavm`,
`public static String build(Score score)`. It mirrors `PartwiseBuilder`'s
traversal (`processScore → processPartList → processStub → processLogicalPart
→ processSystem → processPart → processMeasure → processChord → processNote`,
plus the direction/articulation/ornament/tuplet/slur/syllable/wedge/pedal/
marker/rehearsal/sentence/chord-name handlers) but emits MusicXML 4.0.3
text with a plain `StringBuilder` and a minimal `X` node class (tag,
insertion-ordered attributes, children, optional text, 2-space indent,
self-closing empty elements). No JAXB, no proxymusic marshalling, no
reflection, no `BigDecimal` — only TeaVM-safe JDK classes (`java.util`,
`java.lang`, `String.format`). Element order follows the proxymusic
`propOrder` verified in §22.0 via `javap` (Attributes, Note,
ScorePartwise, Print, Direction, Barline; enum XML values are the
lowercase-hyphenated constant names, with explicit maps for `ClefSign`,
`Step`, `NoteheadValue`, and the `DOUBLE_FLAT → "flat-flat"` special case).

Key design points:

- **Measure items are `List<Object>` with an `ATTR_MARKER`.** The
  `<attributes>` element's position is its first-use position, exactly as
  JAXB insertion order produces it: every attributes mutation goes
  through `setDivisions`/`setStaves`/`addKey`/`addTime`/`addClef`/
  `addStaffDetails`/`addMeasureStyle`, each calling `Attrs.touch()`,
  which appends the marker once. `renderMeasure()` replaces the marker
  with the rendered `<attributes>` (in propOrder) and appends everything
  else to the measure shell.
- **Measure-render lifecycle.** `renderMeasure()` runs at the end of
  `processMeasure` (non-copy path), before allocating the next shell in
  the measure-repeat copy loop, and before allocating the next dummy shell
  in `insertMultipleRest`. It is idempotent per shell (sets `items`/`attrs`
  to null after rendering). `Current.endMeasure()` deliberately does NOT
  clear `pmMeasure`/`items`/`attrs` — the copy loop relies on them
  surviving the inner `processMeasure` call.
- **`processNote` assembles note children into slots and emits them in
  Note propOrder** (grace, chord, pitch/unpitched/rest, duration, tie,
  instrument, voice, type, dot, accidental, time-modification, stem,
  notehead, staff, beam, notations, lyric). `current.notations` /
  `pendingTies` / `pendingLyrics` are cleared at note start, before chord
  events create notations; ties are inserted after duration, lyrics after
  notations.
- **Direction staff ordering:** direction-type first, then `<staff>`,
  then `<sound>` (in `processDirection`, `processDynamics`,
  `processPedal`, `processWedge`, `processMarker`, `checkOctaveShift`).
- Inner classes mirror the originals: `Current`, `IsFirst`, `Attrs`,
  `ClefKey`, `MeasurePrint` (print element allocated first in the items,
  removed if unused), `ClefIterators`, `WedgeIterators` (+ `TimedWedge`,
  sorted by time offset, LEFT before RIGHT at the same offset).
- Helpers: `toTenths` (`(int) rint(10*dist/interline)`), `yOf`,
  `stepOf`, `getNoteTypeName` (note + `Rational`), `accidentalValueOf`,
  `barStyleOf` (incl. the `LIGHT_HEAVY_LIGHT` by-location trick),
  `dynamicsTag`, `articulationElement`, `ornamentElement`,
  `pauseElement`, `findChild`/`textOf`, `buildAttributes`.
- Scope implemented: the full `PartwiseBuilder` surface as reviewed —
  notes/rests/clefs/keys/times/barlines/divisions/durations/pitches, then
  ties/beams/tuplets/dynamics, plus slurs, lyrics, articulations,
  ornaments, wedges, pedals, markers, rehearsals, sentences, chord names,
  multiple rests, measure repeats, octave shifts, fermatas, drum parts,
  grace notes.

### 22.2 Two bugs caught by the second-page comparison (fixed, §22.3)

1. **`<pitch>` child order was wrong: octave before alter.** The
   MusicXML schema order is step, alter, octave. The hymn has no
   accidentals, so it passed silently; Lindenbaum (83 `<alter>`
   elements) caught it. Fixed by moving the alter emission before the
   octave emission in `processNote`.
2. **`<tuplet bracket="no">` was emitted unconditionally.** The
   original sets it only when Audiveris's `avoidTupletBrackets`
   constant is set (default false — `PartwiseBuilder.java:3298`).
   Removed the unconditional attribute.

### 22.3 Desktop verification — writer vs Audiveris's own .mxl

Harnesses in `teavm-fork/phase22/src/`: `WriterExport.java` (run to
PAGE on the input, `MxlWriter.build(score)`, write the string) vs the
pre-existing `DesktopExport.java` (same run, `ScoreExporter` reference).
Both run on the same `Score` from the same input, so the comparison is
pure exporter equivalence. Comparators in `phase22/`:
`compare_mxl.py` (counts, per-note fields, measure tag sequences) and
`compare_deep.py` (recursive semantic-tree diff: tag, attributes, text,
child order; pure-whitespace text ignored).

| Page | Notes | Parts / measures | Exercised beyond notes | Deep diffs |
|---|---|---|---|---|
| hymn-satb (`/tmp/hymn-gray.png`) | 128 | 2 / 16 | dynamics (21 dirs), backup 16 | **0** |
| Lindenbaum (`open-music/pages/lieder-lindenbaum.png`) | 190 | 2 / 22 | rests 18, chords 53, forwards 9, alters 83, tuplets 4, ties 8, beams 174, slurs 29, wedges 3, fermatas 3, dots 17, time-mod 9, key 1 | **0** |
| divisi-tuplet (`test-material/divisi-tuplet.png`) | 72 | 2 / 8 | tuplets 10, time-mod 10 | **0** |
| single-staff (`test-material/single-staff.png`) | 16 | 1 / 4 | — | **0** |

Total: **406 notes, 0 deep semantic diffs on all four pages.**
Well-formed XML on all four; DOCTYPE + `version="4.0.3"` header,
`<identification>`, `<defaults>` identical; `<part-list>` identical
(the shallow comparator's single "diff" on every page is trailing
whitespace after `</part-list>`, an artefact — deep diff is 0).
Writer file sizes: hymn 44,113 B (ref 45,553 B), Lindenbaum 81,782 B
(ref 83,885 B) — the difference is serialization style only
(self-closing `<tag ... />` vs JAXB's `<tag ...></tag>`).

NOT validated: no music21 in this VM, no xmllint, and the DTD fetch
from musicxml.org returned a 146-byte stub instead of the DTD, so no
DTD validation was performed. Validation rests on semantic identity
with the reference exporter's output, which is valid MusicXML 4.0.3
by construction on every element these pages exercise.

Still **unexercised** by these four pages (implemented per
`PartwiseBuilder`, but no such element in any test Score): real
`<lyric>` elements (no lyrics in any Score — TextsStep is neutered,
no OCR), pedal, grace notes, chord names, multiple rests, measure
repeats, octave shifts, fermatas on a grace, drum parts. (The
`lyric: 1` hit in the coverage grep is `<lyric-font>` inside
`<defaults>`, not a lyric.)

Two harness gotchas, recorded:

- The desktop run must use the **stock `audiveris.jar`**, NOT
  `patched/classes` first: the patched `LoadStep` (ROUND 4) reads the
  image from `TeavmImageHolder` and throws `StepException: No image
  supplied from JS` on the desktop path. `MxlWriter*.class` is copied
  from `patched/classes/teavm/` into `phase22/classes/teavm/` for the
  run; classpath is `phase22/classes` + program jars.
- The writer calls one patched-only API,
  `MetronomeInter.isParsed()` (a jdlehman score-reader patch in the
  spike's Audiveris source, absent from the stock jar). It is never
  resolved on these pages (no metronome sentences — lazy method
  resolution saves the desktop-stock-jar run). On a page WITH a
  metronome mark the desktop harness would `NoSuchMethodError`; under
  TeaVM the patched class is used, so this is a harness limitation,
  not a writer bug.
- The 1,228 `NullPointerException` lines in `writer-export.log` are
  the known harmless SLF4J `toString` failures in `StemBuilder`
  logging (`getTotalLength`, `TreeMap.get` null), same class as in the
  reference `export.log` (§22.0) — not from the writer.

### 22.4 Wiring into TeavmMain + the .mxl-out bridge

`TeavmMain.java`: the §21 comment block is replaced by a Phase D
export block after PAGE + SCORE print — for each score,
`MxlWriter.build(score)`, Base64-encode (UTF-8), expose via a new
`@JSBody` setter `setMxlB64` to `globalThis.__mxlB64`, and print
`MXL len=… exportMs=… totalMs=…`. New runner
`teavm-fork/run-fullout-mxl.mjs` (a copy of `run-fullout.mjs` with a
save step; `run-fullout.mjs` untouched) reads `__mxlB64` after
`main()` returns, decodes it, and writes the `.musicxml` file. The
result is retrievable, not just computed in-module — this closes the
"wire the .mxl out" step from the task.

### 22.5 Build and runs (Node v24.22.1, DEFAULT stack, no --stack-size)

- `build.sh` OK (`patched/classes`: 298 classes — MxlWriter +
  wired TeavmMain compile cleanly against the patched API).
- TeaVM build, canonical command (§10.8, patched core jar FIRST on
  the compiler classpath):
  `java -Xmx3g -cp "../teavm-fork/lib-fork/teavm-core-0.16.0-patched2.jar:lib/*:classes" Spike wasm-gc ../teavm-fork/full-out48 teavm.TeavmMain @../teavm-fork/teavm-main-jars-corepatch2.txt @program-jars.txt`
  → **full-out48: 0 problems** (0 PROBLEM matches in
  `full-build48.log`), 3,027 classes, 28,467 methods,
  `classes.wasm` 13,336,491 bytes (+283 KB vs full-out47's
  13,053,133 — MxlWriter + export-path reachability).
- Crop first (`run-crop.mjs full-out48`, 2480×700): exit 0,
  `MXL len=28632 exportMs=66 totalMs=13931`, `TEAVM DONE`, main()
  14,080 ms. (The crop .mxl is not saved — the old runner has no
  save step; the full run is the saved artifact.)
- Full hymn (`run-fullout-mxl.mjs full-out48 wasm-hymn.musicxml`):
  load 438 ms; `REACH HEADS ms=22236`; `REACH SYMBOLS ms=16277
  totalMs=38659`; `REACH LINKS ms=130 totalMs=38791`; `REACH RHYTHMS
  ms=111 totalMs=38903`; `REACH PAGE ms=10 totalMs=38914`;
  **SIG 539/494/494/491 identical to desktop at every step**;
  `SCORE parts=2 measures=8`; **`MXL len=44105 exportMs=51
  totalMs=39095`**; `TEAVM DONE`; main() returned in 39,593 ms;
  exit 0. **First WasmGC .mxl ever produced**
  (`teavm-fork/wasm-hymn.musicxml`, 44,105 bytes).

Wasm .mxl vs desktop (same writer on desktop: 44,113 bytes;
reference: 45,553 bytes): **128 notes / 2 parts / 16 measures, same
element counts, 12 deep diffs** — 2 are the input filename in
`<source>` / `<miscellaneous-field name="source-file">`
(`/hymn-satb.png` under Wasm vs `/tmp/hymn-gray.png` on desktop —
expected, different input paths); 9 are `default-x` exactly +1 tenth
on 9 notes (62→63, 144→145, 137→138, 52→53, 93→94, 147→148, …);
1 is `staff-distance` 102→101. The 10 position diffs are ±1-tenth
roundings from the known Wasm-vs-desktop sub-pixel divergence
(§18/§20: 1–2 px box jitter, 4-pixel NO_STAFF residual) — pitch,
duration, voice, type, stem, and every other field match on all 128
notes. No writer bug; no new trap anywhere in this phase.

### 22.6 Verdict and what remains

**Phase D DONE. The JAXB wall is gone**: the first `.mxl` out of
TeaVM WasmGC is musically identical to the desktop-produced one
(128/128 notes, same pitches/durations/voices/structure). Export
took 51 ms on top of a 39.1 s LOAD→PAGE run; the .mxl-out bridge
(base64 global + runner save) works.

What remains for a working end-to-end run, in order:

1. **TextsStep / OCR (lyrics) — the only remaining functional piece.**
   The pipeline still neuters TextsStep; the in-browser path is
   tesseract.js (per the PR 5 / BrowserOCR work) bridged into TeaVM.
   Without it the .mxl has notes but no lyrics — fine for
   instrumental scores, incomplete for the choir/SATB goal. This is a
   new phase (§23), not a small contained piece — NOT started here.
2. **Clean build** — strip the DIAG14/16/17/18/19/20/22/23 prints
   (still in deliberately, per §20 — every §20 comparison rests on
   them) before any "clean" build.
3. **Real-browser run** — everything so far is Node v24.22.1; a Chrome
   run of the WasmGC module is still untested (CheerpJ replacement
   needs the browser, where there is no `--stack-size` and the ~1 MB
   V8 stack band applies).
4. **Unexercised writer paths** (§22.3) need a page that actually
   contains lyrics, pedal, grace notes, chord names, multiple rests,
   measure repeats, octave shifts, or a drum part before they are
   called verified.

### 22.7 Files

- `teavm/entry/src/teavm/MxlWriter.java` (3,104 lines) — the writer.
- `teavm/entry/src/teavm/TeavmMain.java` — Phase D export block +
  `setMxlB64` (replaces the §21 comment block).
- `teavm-fork/run-fullout-mxl.mjs` — runner that saves `__mxlB64`.
- `teavm-fork/phase22/src/WriterExport.java` — desktop writer harness.
- `teavm-fork/phase22/compare_mxl.py`, `compare_deep.py` — comparators
  (now take `[ref] [new]` args, defaulting to the hymn pair).
- `teavm-fork/phase22/desktop-{hymn,lindenbaum,divisi-tuplet,single-staff}.musicxml`
  (reference) and `writer-{…}.musicxml` (writer) — the four desktop
  comparison pairs, with `export-*.log` / `writer-*.log`.
- `teavm-fork/full-out48/` (`classes.wasm` 13,336,491 bytes),
  `full-build48.log`, `full-run48.log`, `wasm-hymn.musicxml`
  (44,105 bytes — the first WasmGC .mxl).
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 23 — TextsStep / OCR (lyrics) — 2026-11-09

### 23.0 Headline

**The OCR bridge works end to end: lyrics now appear in the Wasm .mxl.**
Hymn: 52 lyric elements, the identical syllable sequence to desktop.
Hallelujah p.1: 153 lyric elements, 145/208 = 70% syllable recall against
ground truth, every correctly-recognised syllable attached to the right
note. The `deu` language wiring is proven (hymn crop, 37 lyrics). The
two-phase bridge (phase 1 exports the clean image, JS runs tesseract.js,
phase 2 re-runs with the prefed text) is the design that fits TeaVM's
synchronous `@JSBody` against tesseract.js's async API.

**But desktop verification finds a genuine divergence — trap 4.** The
Wasm+OCR .mxl is NOT musically identical to desktop+OCR on the same page
and the same OCR text: on the hymn Wasm keeps false TUPLET_THREE inters
built from lyric-word glyphs (8 tuplets, divisions 3 vs desktop 1 / 0
tuplets), and on Hallelujah the measure grid differs (11 measures/part
vs desktop's 14) with an 11-syllable lyric gap. Root cause is localised
to text-glyph section construction: identical clean-image pixels and
identical ROIs yield different section sets under TeaVM (162/162 char
glyphs differ, 10 chars produce no glyph at all). The clean image and
buffer sharing are both exonerated. Classification: most plausibly a
TeaVM-side behavioural/codegen defect in pure-Java run/section
construction (same class as #21244/#15448) — needs a minimal repro +
upstream filing, not a contained shim fix. **This is the fully-blocked
point for §23's "verify against desktop" step.**

Lindenbaum is blocked earlier (§23.8): a HEADERS ConcurrentModification-
Exception in the base pipeline, before TEXTS/OCR — so `deu` on real
German lyrics is still untested end to end.

Verdict: **OCR bridge DONE; desktop-fidelity of OCR runs BLOCKED on
trap 4; Lindenbaum blocked on its own HEADERS CME.**

### 23.1 TextsStep flow on desktop (what it asks OCR for)

Step order (OmrStep): LOAD, BINARY, SCALE, GRID, HEADERS, STEM_SEEDS,
BEAMS, LEDGERS, HEADS, STEMS, REDUCTION, CUE_BEAMS, **TEXTS**, MEASURES,
CHORDS, CURVES, SYMBOLS, LINKS, RHYTHMS, PAGE.

- `TextsStep.doProlog`: `new SheetScanner(sheet)`; if
  `OcrUtil.getOcr().isAvailable()` then
  `lines.addAll(scanner.scanSheet())`; returns
  `Context(scanner.getBuffer(), lines)`. `doSystem`: `new
  TextBuilder(system, null).processSystem(context.buffer,
  context.textLines)`.
- `SheetScanner.scanSheet`: `getCleanImage()` (NO_STAFF source →
  `TextsCleaner.eraseInters()` — erases good inters, fills staff core
  areas, `buffer.threshold(127)`, rebuilds glyphs, erases border glyphs)
  → `OcrUtil.scan(image, OCR.LayoutMode.MULTI_BLOCK, languages, sheet,
  id)` where languages = `sheet.getStub().getOcrLanguages()` (default
  "eng"; settable via `stub.getOcrLanguagesParam().setSpecific(lang)`).
- `OcrUtil.scan`: if OCR unavailable or language unsupported → empty
  list; else adds a 10px white margin (origin −10,−10), calls
  `ocr.recognize(sheet, bi, origin, languages, layoutMode, label)`;
  sorts lines by `TextLine.byOrdinate(sheet.getSkew())`; each word
  `adjustFont()`.
- `OCR.recognize` contract: returns `List<TextLine>` — lines/words/chars
  with boxes and baselines. PSM_AUTO=3 for MULTI_BLOCK, PSM_SINGLE_BLOCK=6.
- Flow into attachment: `TextBuilder.processSystem` → validLines /
  longLines / purge / partition → `guessRole` per line → mapLyricLines
  → recompose → createSystemInters (SentenceInter / WordInter /
  LyricItemInter) → numberLyricLines → glyph mapping → inters.
  Lyric-to-note attachment is via LyricItemInter ↔ note relations, with
  syllabic begin/middle/end.
- Where TeavmMain neutered it: ROUND 2 replaced TextsStep.doProlog /
  doSystem with a no-op returning an empty context (`OcrUtil.ocr =
  null`). The repo's BrowserOCR is the CheerpJ bridge (native `read()`
  → JS `readText`); under TeaVM the native method has no implementation.
- What OCR is asked for: grey image bytes (clean, staff-removed),
  width/height, a languages string, a pageSegMode; it returns
  lines/words/chars with boxes, baselines, and confidences.

### 23.2 Bridge design (two-phase)

The async problem: TeaVM `@JSBody` is synchronous and tesseract.js is
async, so a live await inside Wasm is impossible. Two designs were
considered:

- (a) Pre-run OCR in JS before invoking the Wasm step. Impossible as a
  single pre-run: the clean image only exists AFTER LOAD..TEXTS runs
  (SheetScanner builds it), so JS cannot OCR it before Wasm starts.
- (b) Two-phase (CHOSEN — simplest workable): phase 1 runs LOAD..TEXTS;
  `SheetScanner` builds the clean image exactly as on desktop;
  `OcrUtil.scan` hands it to `BrowserOCR.recognize`, which exports the
  (10px-margined) grey bytes to JS globals and returns no lines; main()
  returns after TEXTS. JS (the runner) PNG-encodes the bytes, runs
  tesseract.js, formats L/W/C rows, sets `__ocrText`. Phase 2 is a
  FRESH module load with `__ocrText` set: full run LOAD..PAGE+export;
  `recognize()` parses the prefed text; TextBuilder attaches lyrics.

Two fresh module loads (not re-entering `main()` twice in one instance)
avoid static-state persistence risk; the cost is a re-run of
LOAD..HEADS (~20 s full hymn, ~7 s crop). Data format is the repo's own
L/W/C text rows (`BrowserOCR.parse` input) — it reuses the exact parser
Audiveris already has, so no new format needs validating. PNG encoding
in JS is a pure-JS encoder (zlib deflate, filter 0, CRC32).

Language parameter: `__ocrLang` global →
`stub.getOcrLanguagesParam().setSpecific(lang)` → `OcrUtil.scan`
passes it through → `BrowserOCR` LANGUAGES gates `supports()` → the JS
worker loads the pack. Proven with `deu` (§23.5).

### 23.3 Implementation

- **ROUND 16 patches** (`teavm/patched/make_patches.py`, appended
  before the prune-stale block): (a) TextsStep restored to stock (undo
  ROUND 2 neutering) + DIAG24 prints in doProlog/doSystem; (b) OcrUtil
  `ocr = null` → `BrowserOCR.getInstance()` + DIAG24 print after
  recognize (this print was inserted at the end of ROUND 2's OcrUtil
  block by an edit that matched the first of two identical anchors —
  functionally fine, placement misleading); (c) BrowserOCR: `@JSBody
  readOcrText()` (returns `globalThis.__ocrText`; undefined → null,
  verified in phase 1: prefed len=-1) + `@JSBody setOcrImage(b64,w,h,
  lang,psm)`; `recognize()`: if prefed null/empty → export image +
  return empty list, else `parse(sheet, prefed)` + DIAG24 prints;
  LANGUAGES widened to eng/deu/fra/ita/spa/lat (data is JS-side; the set
  only gates `supports()`); `parse` made package-visible (was private)
  so the desktop TestOcr harness can call the exact same parser;
  `Collections.unmodifiableSortedSet` removed (TeaVM classlib lacks it —
  first full-out49 build failed with exactly 1 PROBLEM ERROR on
  `BrowserOCR.<clinit>`; plain TreeSet serves, nothing mutates
  LANGUAGES); (d) TextBuilder DIAG24 stage prints (validLines/longLines/
  purged/partitioned/roles guessed/lyric lines mapped/recomposed/
  sections/glyphs mapped/inters created/lyric lines numbered) + per-line
  guessRole entry prints (value, words, bounds); (e) TextRole DIAG24
  bisect print before the role switch (sysPos, partPos, leftOf,
  isAllChords, isMainlyItalic, closeToStaff, farFromStaff, pageCentered,
  shortSentence, tinySentence, firstSystem, lastSystem).
- **TeavmMain phase dispatch** (`teavm/entry/src/teavm/TeavmMain.java`):
  `@JSBody ocrText()` / `ocrLang()` getters; after stub creation, if
  `__ocrLang` set → `stub.getOcrLanguagesParam().setSpecific(ocrLang)` +
  print `OCR LANG …`; after the HEADS dumps, `OCR PREFED <bool>`; if no
  prefed text → `reachStep(TEXTS)` + `PHASE1 TEXTS ms=…` + `PHASE1 DONE
  — clean image exported to JS, OCR pending` and return (no export);
  else full pipeline as before. Also added during the Lindenbaum
  diagnosis: try/catch around `reachStep(HEADS)` printing `DIAG24
  FAILED AT LATEST=<stub.getLatestStep()>` before rethrowing.
- **Node OCR module** (`teavm-fork/phase23/ocr-run.mjs`, with
  `phase23/node_modules` = tesseract.js 6.0.1, installed via npm in ~3
  s): mirrors repo `readText` exactly (legacy engine, 70 dpi, PSM passed
  through, L/W/C emitter); pure-JS PNG encoder for grey bytes; worker
  per language spec (split on `+`), pack-load failure falls back to
  English + warn. Smoke-tested standalone: raw hymn grey (2480×3507)
  eng → 3,865 ms, 16 blocks, 31 lines / 88 words / 319 chars (438 rows)
  — raw page is noisy (music symbols read as garbage, e.g. "JJJJJJJJ",
  "FF\" M ”M"), confirming the clean image matters; Lindenbaum raw grey
  deu → 3,846 ms, 426 rows, correctly reads "Winterreise, D.911", "Der
  Lindenbaurn" [sic], "Wilhelm Müller", "Franz Schubert". Hymn lyrics
  are present on the page ("Adore thee…", "Joy—ful joy—ful").
- **Runner** (`teavm-fork/run-fullout-ocr.mjs`): args `<wasm-dir> <grey>
  <meta.json> <out.musicxml> [lang] [tag]`; phase 1 → saves
  `phase23/<tag>-clean.gray/.json`; OCR → saves
  `phase23/<tag>-ocr.txt`; phase 2 → saves .mxl, logs lyric-element
  count (regex `/<lyric>|<lyric /g`, excludes `<lyric-font>`).
  `run-fullout-noocr.mjs` is the no-OCR control (sets
  `__ocrText=" "` so TeavmMain takes the full-pipeline path while
  BrowserOCR.parse returns 0 lines).
- **Test pages** (PIL `convert('L')` — verified byte-identical to the
  `hymn-satb.gray` method): `phase23/hallelujah-satb.gray` (2480×3509,
  218 notes, 208 lyrics ground truth), `phase23/lieder-lindenbaum.gray`
  (2480×3507, German), `phase23/lieder-gute-nacht.gray` (2480×3507).
  Hymn crop: `teavm-fork/hymn-crop.gray` (2480×700) + `hymn-crop.json`.
- **Desktop harness** (written and RUN 2026-11-09):
  `phase23/src/org/audiveris/omr/text/TestOcr.java` (OCR impl returning
  lines from `BrowserOCR.parse` on the file in system property
  `testocr.file`, with topLeft translation; same parser as Wasm),
  `phase23/src/org/audiveris/omr/text/OcrUtil.java` (desktop variant
  with `ocr = TestOcr.getInstance()`),
  `phase23/src/teavm/DesktopOcrExport.java` (like phase22 WriterExport:
  run to PAGE on a PNG regenerated from the .gray bytes, export via
  MxlWriter, print lyric count + syllable sequence). Desktop run model
  (phase22): classpath `phase23/classes` + program jars; MxlWriter.class
  copied from `patched/classes/teavm/`; patched BrowserOCR also compiled
  into phase23/classes (its `@JSBody` methods are never called on
  desktop; teavm-jso jar on the desktop classpath to be safe). Note: no
  native Tesseract exists in this VM (`which tesseract` empty), so a
  desktop-native OCR reference is impossible; the TestOcr comparison is
  bridge fidelity (same OCR input → same lyrics), while absolute recall
  vs native Tesseract is already known from PR 4 (BrowserOCR 64–77%
  syllables vs desktop native 76–86%; 98.3% chars right; do NOT re-tweak
  engine/DPI/PSM/binarisation — exhausted in PR 4). Also found during
  §23: `~/workspace/score-reader-spikes/eng.traineddata` and
  `deu.traineddata` exist at the spikes root, plus
  `~/workspace/score-reader-spikes/node_modules/tesseract.js` and
  `repo/.work/audiveris/app/dev/tessdata/eng.traineddata`.
- **Shim facts established in §23:** `BufferedImageGraphics` (shim
  Graphics2D) is real pixel-wise (fillRect/drawLine/fill/draw of rects
  and paths; drawImage copies pixels 1:1 at natural size; text/font ops
  no-ops) — the clean image is genuinely built. `Font.createGlyphVector`
  returned null (see trap 1). `GraphicsEnvironment.
  getAvailableFontFamilyNames()` shim returns an empty array.
  `Raster.getDataElements(x,y,w,h,obj)` exists in the shim.
  `Font.java` and `java/awt/font/*` shims are hand-written (not in any
  `gen_awt*.py` FILES dict) — safe to edit directly; `gen_awt.py` only
  regenerates Component/Container/Window/etc.
- **DumpSeq unavailable for PC mapping:** the
  `org.teavm.backend.wasm.debug` classes are in no jar under
  `teavm/lib/`, `~/.m2`, or `~/workspace` (searched 2026-11-09). PC
  mapping therefore proceeds by DIAG prints, not DumpSeq. The wasm has
  no name section (custom sections present are only
  `teavm.memoryRequirements` and `teavm.imports`).

### 23.4 Traps 1–3 (fixed, contained)

- **Trap 1 — `Font.createGlyphVector` returns null (shim defect, same
  family as §12/§13):** Phase 2 trapped inside `BrowserOCR.parse` on
  the first 'W' row: `TextWord` ctor →
  `FontInfo.adjustedTextFont(value, bounds)` → static
  `adjustedTextFont(attrs, pointSize, value, bounds)` →
  `TextFont.getBestFont(attrs, pointSize)` → `new TextFont(...)` →
  `OmrFont.computeSize(value, bounds.getSize())` →
  `createGlyphVector(frc, content)` returns null (shim `Font.java:55`)
  → `glyphVector.getVisualBounds()` NPE → uncatchable Wasm trap. DIAG24
  sequence: `BrowserOCR prefed len=4979`, `parse entry answerLen=4979`,
  then trap. **Fix applied:** new
  `teavm/shims/src/java/awt/font/SimpleGlyphVector.java` (concrete
  GlyphVector; visual bounds reuse the TextLayout model exactly —
  Bravura composed advance when applicable, else 0.5 × size per char;
  ascent 0.8 × size, descent 0.2 × size; per-glyph positions evenly
  spaced) + `Font.createGlyphVector` (all three overloads) now return
  it. After the fix, parse returns 6 lines, `OcrUtil.scan recognized
  lines=6`, `TextsStep doProlog lines=6`. Note: shim font sizes will
  differ slightly from desktop real-font sizes — TextBuilder uses bounds,
  not font size, for lyric attachment; report honestly.
- **Trap 2 — in `TextBuilder.processSystem` → `guessLongRoles` →
  `TextRole.guess` (localised and fixed as trap 3):** After trap 1's fix,
  phase 2 reaches `doSystem #1 lines=6`; stage prints: phase 1 (0
  lines) passes all stages; phase 2: `validLines=6`, `longLines=5`,
  `purged`, `partitioned`, then trap before `roles guessed`. Per-line
  guessRole prints: line 1 `Soprano/Alto`, words=1, bounds
  `Rectangle[83, 142, 254x44]` — guessed OK; line 2 `we a — dore—thee
  HeaIts un — fold like ﬂow'rsbe — fore thee Joy—ful joy—ful`, words=15,
  bounds `Rectangle[883, 307, 1490x45]` — guessed OK; line 3 `Joy—ful
  joy — ful`, words=4, bounds `Rectangle[506, 307, 319x45]` — **traps
  inside `TextRole.guess`**. `guessRole` wraps the call in try/catch
  (Exception) but Wasm null traps are uncatchable (established §12/§13).
  Ruled out: `getPartAtOrAbove` (never returns null — falls back to
  `getFirstPart()`); `TesseractOCR.getInstance()` (empty ctor;
  `getMinConfidence()` returns a Constant value; it ran fine for lines
  1–2 via `isMainlyItalic`).
- **Trap 3 — metroPattern `\x{...}` (TeaVM regex gap, fixed 2026-11-09,
  ROUND 17):** Root cause found from the full log (not the tail): line
  2's guessRole threw `java.util.regex.PatternSyntaxException: 17,
  (?<tempo>[^\...` — TeaVM's java.util.regex does not support the
  `\x{hhhh}` escape. `MetronomeInter.beatUnitRegexp()` builds metroPat
  from `MusicPane.musicCodes` as `"\x{e0a2}"` etc. (SMuFL PUA codepoints,
  all BMP, from `ShapeSet.BeatUnits` via `MusicFamily.Bravura.
  getSymbols()`). Index 17 of the full pattern is inside `\x{e0a2}`
  (named groups `(?<tempo>...)` parsed fine). First `isLikely()` call
  (line 2) failed class init and was caught by guessRole's try/catch
  (WARN "Error in guessRole"); second call (line 3) found `metroPattern`
  null → NPE → uncatchable Wasm trap. **Fix (ROUND 17 in
  make_patches.py, MetronomeInter.java already in COPY_ASIS round 3):**
  `beatUnitRegexp()` now emits literal code-point characters via
  `Character.toChars(codePoint)` (class-special `\\`, `]`, `^`, `-`
  backslash-escaped), identical match set on desktop; javadoc updated.
  `sub()` in make_patches.py is plain `text.replace` (not regex) —
  escaping verified. Desktop-neutrality proven: patched MetronomeInter
  compiles on desktop JDK and the desktop-OCR harness runs through
  `isLikely` with it (see §23.6). After the fix, all 5 long lines guess
  roles, no WARN "Error in guessRole", phase 2 completes through PAGE +
  export.

### 23.5 Run results — OCR bridge WORKS end to end

Build: full-out49, 0 problems, `classes.wasm` 13,508,206 bytes (13,494,415
at the first §23 build; +13,791 from the ROUND 18/19/20 DIAG prints).
Default stack throughout.

- **Hymn crop (2480×700), full-out49:** Phase 1: REACH HEADS 7,296 ms,
  TEXTS 5,235 ms, total 12,563 ms; phase-1 OCR on clean image 217 rows
  (6 L / 39 W / 172 C), ~3.1 s. Phase 2: REACH HEADS 7,361 ms, HEADS 189
  (same as §20 crop), TextsStep 6 lines → 5 long, roles guessed, lyric
  lines mapped, recomposed lines=5, sections=1951, glyphs mapped, inters
  created, lyric lines numbered; SYMBOLS HEADS=80 SIG=416, LINKS 362,
  RHYTHMS 362, PAGE 362; SCORE parts=2 measures=5; MXL len=34,334,
  exportMs=75, totalMs=15,490, **38 lyric elements**, 80 notes. Clean
  image saved `phase23/hymn-crop-clean.gray` (+ `.json`, 2500×720
  margined); OCR text `phase23/hymn-crop-ocr.txt` (216 lines).
- **Full hymn (2480×3507), full-out49:** Phase 1: REACH HEADS 22,471 ms,
  TEXTS 9,464 ms, total 32,066 ms. Phase 2: REACH HEADS 19,071 ms,
  SYMBOLS +18,505 ms (HEADS 128 SIG 691), LINKS +162 ms (SIG 573),
  RHYTHMS +139 ms (573), PAGE +43 ms (SIG 571), total 37,982 ms;
  **128 notes, 2 parts, 16 measures, 52 lyric elements**, MXL 54,048
  bytes (`teavm-fork/wasm-hymn-ocr.musicxml`). OCR returned 7 lines
  (system 1: validLines=4, longLines=3, recomposed=3; system 2:
  validLines=4, longLines=4). Syllables include OCR noise ("HeaIts",
  "dare" vs "dore", "ﬂow'rsbe" split oddly) but attachment works
  including begin/middle/end syllabic splits. Part P2 named "Tenor/Bass"
  (from OCR text line) and `<rights>M Ell engraved with</rights>` credit
  picked up from the page.
- **Hallelujah p.1 (2480×3509), full-out49, eng:** Phase 1: REACH HEADS
  35,325 ms, TEXTS 27,669 ms, total 63,163 ms. Phase 2: REACH HEADS
  32,497 ms, SYMBOLS +40,881 ms (HEADS 218, SIG 2283), LINKS +519 ms
  (1533), RHYTHMS +255 ms, PAGE +46 ms (SIG 1526), total 74,568 ms;
  **HEADS 218 = ground truth, 299 notes, 153 lyric elements, divisions
  4, 0 tuplets**. Lyric recall vs GT (`open-music/pages/
  hallelujah-satb.json`, 208 syllables, per-note lyric fields): syllable
  multiset recall 145/208 = 70%; attached (bar,pitch,syllable) recall
  145/208 = 70% after measure offset 3 (GT bars 4–14, .mxl measures
  1–11) — every correctly-recognised syllable lands on the right note.
  Missing GT syllables are the "Hal/le/lu/jah" repetitions (OCR misses);
  Wasm-only syllables include 'Creative', 'Commons', 'licens', 'BY',
  'NC' — the CPDL footer license text OCR'd and attached as lyrics. File
  `teavm-fork/wasm-hallelujah-ocr.musicxml` (130,760 bytes).
- **Language wiring (`deu`):** Hymn crop with `deu` → exit 0, `OCR LANG
  deu` printed in both phases, tesseract.js deu pack used, **37 lyric
  elements** (vs 38 eng — German model on English text, as expected).
  Wiring proven: `__ocrLang` → `setSpecific("deu")` → OcrUtil.scan
  passes "deu" → BrowserOCR recognises with deu pack. The `deu` pack was
  already verified standalone in §23 (test-deu.mjs reads German
  correctly). Lindenbaum-with-`deu` itself is blocked (see §23.8) — `deu`
  on real German lyrics remains untested end to end.
- **No-OCR control (same build, new runner
  `teavm-fork/run-fullout-noocr.mjs` — sets `__ocrText=" "` so TeavmMain
  takes the full-pipeline path while BrowserOCR.parse returns 0 lines):**
  full hymn reproduces §22 EXACTLY — 128 quarters, divisions 1, 0
  tuplets, SIG 491 at PAGE, 44,105 bytes
  (`wasm-hymn-noocr49.musicxml`). Proves the tuplet/divisions change in
  the OCR run is caused by TextsStep with real OCR lines, not by the
  build. (The §22 runner `run-fullout-mxl.mjs` can no longer do a full
  no-OCR run — TeavmMain returns after TEXTS when no prefed text is
  present.)

### 23.6 Desktop verification — bridge fidelity PROVEN for lyrics, trap 4 divergence found

Harness compiled 2026-11-09: `phase23/classes` = TestOcr + OcrUtil
desktop variant + patched BrowserOCR + patched MetronomeInter (ROUND 17)
+ DesktopOcrExport + MxlWriter, classpath `phase23/classes` + program
jars (stock `audiveris.jar` after; teavm-jso jar for compilation). PNGs
regenerated from .gray bytes with PIL (`phase23/hymn.png`,
`phase23/hymn-crop.png`, `phase23/hallelujah.png`).

- **Full hymn, same prefed OCR text (`phase23/hymn-ocr.txt`):** desktop
  run exit 0, `DESKTOP-OCR-EXPORTED len=46659, LYRIC elements=52` —
  **exactly the same lyric count (52) and the same syllable sequence**
  as Wasm. BUT desktop: divisions 1, 0 tuplets, all quarters; Wasm:
  divisions 3, 8 tuplets, 12 time-modifications. Deep diff
  (phase22/compare_deep.py) desktop-vs-Wasm: **146 diffs** full hymn (98
  crop). Categories: duration scaling from divisions 1→3 (the tuplet
  corruption), syllabic begin/end on 28 notes (downstream of the rhythm
  change — syllables attach to different notes when durations change),
  ±1 default-x on 5 notes (known sub-pixel divergence), source filename
  ×2 (expected, different input paths), credit-words font-size 10 vs 9
  ×1 (stub-font metric difference, cosmetic).
- **Hymn crop desktop:** 80 notes, 38 lyrics (same counts as Wasm), 0
  tuplets, divisions 1. Deep diff 98.
- **Mechanism of the divergence (established 2026-11-09):** Wasm keeps
  TUPLET_THREE inters built from lyric-word glyphs; desktop discards its
  tuplet candidate as isolated. `TupletInter.createValid` grows the glyph
  box by `maxTupletChordDx/Dy` = 3 fractions = 63 px (interline 21) and
  looks for intersecting head chords. Desktop log: "Discarding isolated
  tuplet candidate glyph#3335" (one candidate, full page). Wasm crop: 4
  createValid calls (ROUND 18 DIAG24) — glyph#2313 (1078,586,29x23)
  grade 0.2164 nearby=2; #2349 (1877,319,28x23) grade 0.1605 nearby=4;
  #2367 (1876,586,29x23) grade 0.2164 nearby=2; #2369 (1876,586,33x23)
  grade 0.6846 nearby=2 (survived as good=true; the other three were
  later removed by SigReducer for low grade). Nearby chords are bass
  down-stem chords whose boxes reach into the grown box, e.g.
  (1863,496,27x67), (1952,464,27x78). Constants are CORRECT under TeaVM
  (dxPx=63 dyPx=63 interline=21). The candidate glyphs sit on lyric
  words: #2369's box (1876,586,33x23) spans the OCR 'o' (1870,586,22x23)
  + 'r' (1894,586,15x23) char boxes of "fore" (word box 1854,574,75x35).
  On desktop the same lyric glyphs never become tuplet candidates in
  system 1 (0 createValid calls on the crop).
- **Glyph-level difference (ROUND 19 DIAG24, `TextBuilder.mapGlyphs` /
  `retrieveSections`):** For "fore" (y=574): desktop char glyphs f 15×35
  nsec=8, o 22×23 nsec=12, r 15×23 nsec=8 (bounds EQUAL the OCR char
  boxes); Wasm f 14×15 nsec=4, o 21×22 nsec=8, r 13×5 nsec=4; the "e"
  char produced NO glyph on Wasm. Word glyph "fore": desktop 75×35
  nsec=47/41; Wasm 74×34 nsec=32/26. Across all 162 common char boxes:
  **0 identical, 162 differing**; Wasm has 162 chars vs desktop 172 (10
  chars produce no glyph at all under Wasm). Pattern: Wasm glyphs
  consistently ~1px smaller per dimension with fewer sections, some
  dramatically truncated (hyphen "-" 1×3 vs 13×4; "r" 13×5 vs 15×23; a
  12×3 vs 13×29 case). `retrieveSections` builds one glyph per TextChar
  (`charBox.contains(section.getBounds())` gate — a section is assigned
  only if fully inside the char box) plus one per word, all from
  clean-buffer sections; `mapGlyphs` does NOT reuse original glyphs, it
  always builds new ones from sections.
- **Clean image is NOT the cause:** Wasm clean image vs desktop clean
  image (desktop dumped via TestOcr `testocr.saveimage` →
  `phase23/desktop-hymn-crop-clean.png`, 2500×720 margined): "fore" area
  pixel-identical (867/221/250/166/230 black in word/f/o/r/e on both);
  total black 38,014 (Wasm) vs 37,589 (desktop); pixel-diff: Wasm-only
  425 px all at y 237–240 (414) and y 259–261 (11) — staff area, not
  lyric area; desktop-only 0. (An earlier "smoking gun" reading was a
  coordinate error: the exported clean image is 2500×720 margined, not
  2480×700 — re-read with the correct stride it matches.)
- **Buffer sharing is NOT the cause (ROUND 20 DIAG24,
  `SheetScanner.getCleanImage`):** `DIAG24 cleanCheck bufferFore=867
  imgFore=867` on BOTH Wasm and desktop (printed twice on Wasm, phase 1
  + phase 2). `buffer` (ByteProcessor) and `img` share pixels correctly;
  threshold(127) operates on the shared array. So identical pixels +
  identical ROIs (charBox keys match exactly) still yield different
  section sets.
- **Localised suspect (not yet proven):** the section-building path
  itself — `TextBuilder.getSections` → `SectionFactory.createSections
  (buffer, roi)` → `RunTableFactory(VERTICAL).createTable(buffer, roi)`
  → `RunsRetriever.retrieveRuns` → `VerticalAdapter.isFore`
  (`source.get(pos, coord) == 0`, i.e. `ByteProcessor.get(x,y)` =
  `pixels[y*width+x]`) → `RunTable.setSequence` →
  `SectionFactory.buildDynamicSections` → `CompoundFactory.buildCompound`.
  Filter is null for the text path (`new RunTableFactory(orientation)` →
  `this(orientation, null)`). Retrieval is SEQUENTIAL on both sides:
  `MyAdapter.isThreadSafe()` checks
  `source.getClass().getAnnotation(ThreadSafe.class)`; ImageJ
  ByteProcessor carries no @ThreadSafe annotation (verified: no
  RuntimeVisibleAnnotations in javap -v) → returns false → sequential
  branch. `ByteProcessor.threshold(int)` → `threshold(level+1, 255)` loops
  the raw `pixels[]` array directly. `ByteProcessor(BufferedImage)`
  requires `getType()==10`, takes `getRaster().getDataBuffer()` cast to
  DataBufferByte, `getData()` (shared, no copy).
  `ByteProcessor.getBufferedImage()` default-LUT branch creates a fresh
  TYPE_BYTE_GRAY image and COPIES via `drawImage(createImage(),…)` (shim
  drawImage is getRGB/setRGB per pixel through the raster — verified
  correct by the export); non-default branch (`createBufferedImage()`)
  wraps `pixels` directly in a `DataBufferByte` (shared) via
  `Raster.createWritableRaster(sm, db, null)` (the §12 null-origin case).
  Shim `DataBufferByte.getData()` returns the live array; shim
  `BufferedImage.getRGB/setRGB` branch on the DataBuffer runtime type
  (§13). The exact defective operation inside run/section construction is
  NOT identified. Classification: most plausibly a TeaVM-side
  behavioural/codegen defect in pure-Java run/section construction on
  identical inputs (same class as #21244/#15448) — needs a minimal repro
  + upstream filing, not a contained shim fix. **This is the
  fully-blocked point for §23's "verify against desktop" step.** The OCR
  bridge itself is done and working; the remaining gap is this TeaVM
  fidelity defect in text-glyph section construction. Next step named:
  dump the per-word section lists (`getSections` output: section bounds
  + count per ROI) on both sides to distinguish "fewer sections built"
  from "same sections, different containment" — then a minimal repro of
  the differing operation for an upstream filing.

### 23.7 Hallelujah desktop comparison (resolved this session)

- **Desktop Hallelujah+OCR initially failed exit 1 with AIOOBE:**
  `ArrayIndexOutOfBoundsException: Index 11742 out of bounds for length
  3538` at `TextBuilder.getSections(TextBuilder.java:393)` called from
  `RehearsalsBuilder.createInter` (line 194) → `processSegment` →
  `buildRehearsals` → `Curves.buildCurves` → `CurvesStep.doit` (CURVES
  step). Root cause was a **harness artifact, not a stock bug**: TestOcr
  returned the WHOLE page's lines for every call, including the small
  rehearsal-enclosure buffers scanned by RehearsalsBuilder (BlockScanner
  → OcrUtil.scan) — lines far outside the enclosure buffer blew up
  getSections. **Fix (TestOcr only):** keep only lines intersecting the
  image rect after topLeft translation (whole-sheet calls unaffected —
  all lines intersect). Desktop Hallelujah then completes: exit 0,
  len=123,074, **164 lyrics, 330 notes, 8 parts, 14 measures/part**.
  Wasm Hallelujah succeeds identically in structure (no trap) —
  consistent with trap 4 (different text glyphs → different downstream
  inters → different rehearsal candidates).
- **Part assignment:** BOTH desktop+OCR and Wasm+OCR produce 8 parts
  with identical part NAMES (S./A./T./B., Voice/Alto/Tenor/Voice) — the
  OCR-read voice labels split the staves into per-system parts. The Nov 8
  no-OCR desktop ref (4 parts, 275 notes) is NOT a valid comparator for
  OCR runs — OCR changes part assignment on desktop too (4→8 parts).
- **The "missing measures" alarm, resolved:** an early P1-only
  comparison looked like the first 3 music measures (D5 opening, GT bars
  4-6) had vanished in both OCR runs. They had not — they are in P5-P8
  (desktop: m4-6 D5/A4/F4/D3, 5/7/9 notes; Wasm: m1-3, identical 5/7/9
  counts). The real difference is **measure numbering**: desktop pads
  every part to a common 14-measure grid (rests in slots where that
  part's system is silent); Wasm numbers each part's measures from its
  own first bar (11 measures each). Same music, same parts, same order;
  per-bar note counts differ slightly in P1-P4 (e.g. P1 m7 desktop 5
  notes vs Wasm m4 6 notes; m9 7 vs 6; m11 5 vs 4) and are identical in
  P5-P8 — the 31-note gap (330 vs 299) is chord/voice-assignment
  difference in the later bars. A filtered-OCR desktop run (title/footer
  lines dropped, 39 lines, 159 lyrics) changed nothing — the
  title/footer lines are not the cause of anything here.
- **Lyric recall, correctly scored:** desktop multiset 156/208 = 75%,
  attached 156/208 = 75% (measure offset 0); Wasm multiset 145/208 =
  70%, attached 145/208 = 70% (offset 3). Every recognised syllable
  lands on the right note on both sides. The earlier "desktop attached
  recall 8%" was a scorer error (offset 3 applied to a file that needs
  offset 0). Wasm's gap vs desktop is 11 syllables — consistent with
  trap 4 (fewer chars → fewer words → fewer lyrics).
- **Deep comparator limitation:** compare_deep.py reported "1 diff" for
  Hallelujah (one extra `<credit>` in the Wasm file) while the files
  differ structurally (measure grid 14 vs 11, lyric counts 164 vs 153,
  per-bar note counts) — it stops at the first structural (child-count)
  mismatch and does not descend. Do not quote its Hallelujah count as a
  verdict.
- **Desktop no-OCR control on the same luma PNG:** 275 notes, 4 parts, 0
  lyrics, 14 measures, D5 opening present — proves the luma input is
  fine (the §20 max-RGB vs luma difference is NOT the cause of anything
  here); the part/measure differences are OCR-lines effects, and the
  Wasm-vs-desktop differences within OCR runs are trap-4 downstream
  effects.

### 23.8 Lindenbaum — HEADERS CME (base pipeline, pre-OCR)

Lindenbaum (`lieder-lindenbaum.gray`, 3 systems, 9 staves, triplet-heavy)
was never run under TeaVM Wasm before §23. Phase 1 dies fast (main()
~5.9 s) with `ExecutionException: RuntimeException:
ConcurrentModificationException` (FakeClass stack, method unidentified),
`DIAG24 FAILED AT LATEST=GRID` — i.e. dies in HEADERS, inside a parallel
executor task. Last log lines before failure: `Systems: #1[1, 2, 3] #2[4,
5, 6] #3[7, 8, 9]`, `Indentation detected for system #1`, `2 parts along
3 systems`, `Created scores: [{Score 1}]`, OmrFont WARN, several NO_STAFF
getSource calls. This is a pre-existing page-specific TeaVM failure in
the base pipeline (before TEXTS/OCR), same family as the §10 CME
(fail-fast iterator vs weakly-consistent collection) but at a new,
unlocalised site. The `deu` language wiring itself is proven separately
(hymn crop, §23.5); Lindenbaum-with-`deu` on real German lyrics remains
untested. Next step named: localise the HEADERS CME to a method
(per-system/per-staff task instrumentation in HEADERS), then judge
contained-fix vs genuine defect.

### 23.9 Verdict + what remains

- §23 verdict: **OCR bridge DONE** (lyrics flow end to end; hymn
  syllable sequence identical to desktop; Hallelujah 70% recall with
  correct attachment; `deu` wiring proven). **Desktop-fidelity of OCR
  runs BLOCKED on trap 4** (text-glyph section divergence — likely TeaVM
  defect, needs minimal repro + upstream filing; do not start as
  unbounded bisection — one diagnostic round, the per-word section dump,
  then judge). **Lindenbaum blocked on its own HEADERS CME** (§23.8).
- What remains for a working end-to-end run, in order (updates §22.7's
  list):
  1. **Trap 4 next step:** per-word section-list dump on both sides
     (`getSections` output: section bounds + count per ROI) to
     distinguish "fewer sections built" from "same sections, different
     containment"; then a minimal repro of the differing run/section
     operation for a TeaVM upstream filing. (Named, not started — one
     diagnostic round, then judge.)
  2. **Lindenbaum HEADERS CME localisation** (per-system/per-staff task
     instrumentation in HEADERS), then judge contained-fix vs genuine
     defect. Until it clears, `deu` on real German lyrics is untested.
  3. **Clean build** — strip the DIAG24 prints (temporary diagnostics)
     and eventually DIAG14/16/17/18/19/20/22/23 (still in deliberately,
     per §20 — every §20 comparison rests on them) before any "clean"
     build.
  4. **Real-browser run** — everything so far is Node v24.22.1; a Chrome
     run of the WasmGC module is still untested (CheerpJ replacement
     needs the browser, where there is no `--stack-size` and the ~1 MB V8
     stack band applies). Cannot run in this VM (no Chrome) — needs
     Jonathan's machine.
  5. **Unexercised writer paths** (§22.3): lyrics are now exercised (§23
     — `<lyric>` elements in the Wasm .mxl, syllabic begin/middle/end).
     Still unexercised: pedal, grace notes, chord names, multiple rests,
     measure repeats, octave shifts, drum parts.

### 23.10 Files

- Patches: `teavm/patched/make_patches.py` ROUND 16 (§23 bridge +
  DIAG24), ROUND 17 (metroPattern literal chars), ROUND 18 (TupletInter
  .createValid DIAG24), ROUND 19 (TextBuilder charGlyph/wordGlyph
  DIAG24), ROUND 20 (SheetScanner cleanCheck DIAG24, via `copy_src` —
  SheetScanner was not previously in OUT).
  `teavm/entry/src/teavm/TeavmMain.java` (phase dispatch +
  FAILED-AT-LATEST catch). Shims:
  `teavm/shims/src/java/awt/font/SimpleGlyphVector.java` (new).
- Runners: `teavm-fork/run-fullout-ocr.mjs` (two-phase),
  `teavm-fork/run-fullout-noocr.mjs` (control),
  `teavm-fork/phase23/ocr-run.mjs` + `phase23/node_modules`
  (tesseract.js 6.0.1), `phase23/test-ocr.mjs`, `phase23/test-deu.mjs`.
- Builds: `teavm-fork/full-out49/` (current; classes.wasm 13,508,206
  bytes, 0 problems on every rebuild in §23). Logs:
  `full-build49.log`, `run-ocr-crop49.log`, `run-ocr-hymn49.log`,
  `run-ocr-hallelujah49.log`, `run-ocr-lindenbaum49.log`,
  `run-ocr-crop-deu49.log`, `run-noocr49.log`.
- Produced .mxl: `wasm-hymn-crop-ocr.musicxml` (34,334 B, 38 lyrics),
  `wasm-hymn-ocr.musicxml` (54,048 B, 52 lyrics),
  `wasm-hymn-noocr49.musicxml` (44,105 B, 0 lyrics),
  `wasm-hymn-crop-deu.musicxml` (34,199 B, 37 lyrics),
  `wasm-hallelujah-ocr.musicxml` (130,760 B, 153 lyrics).
- Desktop harness: `teavm-fork/phase23/src/` (TestOcr.java incl.
  `testocr.saveimage` dump + image-rect line filter, OcrUtil.java,
  DesktopOcrExport.java), `phase23/classes/`, `phase23/hymn.png`,
  `phase23/hymn-crop.png`, `phase23/hallelujah.png` (regenerated from
  .gray bytes), `phase23/desktop-hymn-ocr.musicxml` (46,659 B),
  `phase23/desktop-hymn-crop-ocr.musicxml` (30,708 B),
  `phase23/desktop-hallelujah-ocr.musicxml` (123,074 B),
  `phase23/desktop-hallelujah-noocr.musicxml` (105,578 B),
  `phase23/desktop-hallelujah-nontitle.musicxml` (121,972 B),
  `phase23/desktop-*.log`, `phase23/hymn-ocr.txt`,
  `phase23/hymn-crop-ocr.txt`, `phase23/hymn-crop-deu-ocr.txt`,
  `phase23/hallelujah-ocr.txt` (29,360 B),
  `phase23/hallelujah-ocr-nontitle.txt`, `phase23/empty-ocr.txt`,
  `phase23/desktop-hymn-crop-clean.png`.
- Nothing pushed, filed, or merged; `jdlehman/score-reader` untouched.

## 24 — Trap 4: NOT a TeaVM defect — a shim `Rectangle.contains` bug; contained fix, hymn fixed — 2026-11-09 (DONE; verdict (a))

### 24.0 Headline

**Trap 4 is closed for the hymn, and it was never a TeaVM defect.**
The §23 classification ("most plausibly a TeaVM-side behavioural/codegen
defect") was wrong. The per-word section-list dump proves the section
building is identical on both sides — SEC 56/56 and RUNS 56/56 identical
after normalisation — and the divergence is entirely in the containment
stage, `TextBuilder.retrieveSections`: `charBox.contains(section.getBounds())`
rejects every section touching the char box's right or bottom edge under
TeaVM, because the hand-written shim `Rectangle2D.contains(x,y,w,h)` uses
a half-open point test (`contains(x,y) && contains(x+w,y+h)`) and the shim
`Rectangle` has no `contains(int,int,int,int)` overload at all. The JDK
semantics are inclusive on the far edge. The fix is two shim methods
(§24.4); after it, the hymn crop's CHAR lists are 172/172 identical, the
full hymn has 0 tuplets, divisions 1, 52 lyrics, and the deep diff vs
desktop is down to the known ±1-tenth sub-pixel residuals. Hallelujah's
lyric gap is fully closed too (164 = 164, was 153), but a separate
29-note / measure-grid gap remains (§24.5) — named as the next diagnostic,
not started in this round.

### 24.1 Diagnostic method (ROUND 21, DIAG25)

Three prints, same patched files compiled into `phase23/classes` for the
desktop harness, so both sides run identical diagnostic code:

- (a) `TextBuilder.getSections`: per word ROI — section count + bounds,
  section weight sum, and a direct fore-pixel count from the buffer
  (independent of the RunTable).
- (b) `SectionFactory.createSections(buffer, roi)`: the RunTable itself
  for small ROIs (≤300×100) — per-column run lists (start+length), total
  runs, total fore length.
- (c) `TextBuilder.retrieveSections`: per char — charBox + assigned
  section count + bounds (the containment stage).

Hymn crop, both sides: 284 DIAG25 lines each (56 SEC + 56 RUNS + 172
CHAR), same order. Desktop: `DesktopOcrExport` on
`phase23/hymn-crop.png` with `testocr.file=phase23/hymn-crop-ocr.txt`
(77 s). Wasm: `full-out50` (0 problems, 3,050 classes), two-phase OCR
run `run-ocr-crop50.log` (28 s). Comparators:
`phase24/compare_diag25.py`, `phase24/prove_edge.py`.

### 24.2 Results — section building identical; containment diverges

After normalising the two `Rectangle.toString` spellings
(desktop `java.awt.Rectangle[x=83,y=142,width=254,height=44]` vs TeaVM
shim `Rectangle[83, 142, 254x44]`) and the log-encoding of the em-dash /
`ﬂ` ligature in word values (desktop `?` vs Wasm `—`/`ﬂ` — rendering
only, bounds identical):

- **SEC: 56/56 identical** — same word ROIs, same section counts, same
  bounds lists, same fore counts (total fore 37,359 both sides, wsum =
  fore everywhere). E.g. "fore" (1854,307,75x35): nsec 47, fore 858,
  identical bounds on both sides.
- **RUNS: 56/56 identical** — same per-column run lists, total runs
  4,981 and total fore 37,359 on both sides. Run retrieval,
  `RunTable.encode`, the `RunTable.Itr` iterator, and
  `SectionFactory.Build` (dynamic-section construction, junction policy,
  compound building) are all exonerated: identical inputs in, identical
  sections out.
- **CHAR: 172/172 DIFFERENT before the fix** — Wasm assigns fewer
  sections per char (e.g. 'S' 12 vs desktop 18; '/' 1 vs 6; hyphen 0 vs
  2). The §23 glyph numbers are explained exactly: desktop 'f' 15×35
  nsec=8 vs Wasm 14×15 nsec=4 is the compound of the sections the gate
  kept, not a section-building difference.

Edge-touch proof (`prove_edge.py`, all 172 chars):

| | touch char-box right/bottom edge | do not touch |
|---|---|---|
| missed by Wasm (741) | **741** | **0** |
| kept by Wasm (1,215) | **0** | **1,215** |

Plus 5 Wasm-only sections, all displaced: desktop assigned each to an
earlier char, Wasm rejected it there (edge touch) and it stayed in the
pool until a later char whose box also contains it. So the containment
gate is the single differing operation, and its rule is exactly
"reject iff the section touches the right or bottom edge of the char
box". That is the signature of a half-open point test applied to the
far corner.

### 24.3 Root cause — shim `Rectangle2D.contains`, verified against JDK 25

Call chain: `retrieveSections` calls
`charBox.contains(section.getBounds())` where both are
`java.awt.Rectangle`. The shim `Rectangle` defines
`contains(Rectangle r) { return contains(r.x, r.y, r.width, r.height); }`
but NO `contains(int,int,int,int)` overload, so the call resolves to
the inherited `Rectangle2D.contains(double,double,double,double)`:

```java
// shim, BEFORE the fix
public boolean contains(double x, double y, double w, double h) {
    return contains(x, y) && contains(x + w, y + h);
}
```

with point containment half-open (`px >= x && px < x + width`). For any
section with `x + w == charBox.x + charBox.width` or
`y + h == charBox.y + charBox.height`, `contains(x+w, y+h)` is false,
so the whole test is false — regardless of the section being fully
inside. The same two-corner formula also lives in shim
`RectangularShape.contains(double,double,double,double)`.

JDK ground truth, measured on this VM's JDK 25 (`/tmp/recttest`,
`RectTest{,2,3,4}.java`):

- `Rectangle.contains(int,int,int,int)`: **inclusive** far edge
  (`x+w <= maxX`, `y+h <= maxY`), false when `w <= 0 || h <= 0`.
  Edge-bottom section (86,171,2,5) in box (83,144,21,32): true;
  zero-size at far corner (104,176,0,0): false; zero-size interior:
  false; negative w: false; overflow by 1 px: false.
- `Rectangle2D.Double.contains(double,double,double,double)`: same —
  inclusive far edge, false for `w <= 0 || h <= 0` (zero-size interior:
  false).
- `Ellipse2D.Double.contains(5,5,0,0)`: **true** — so
  `RectangularShape`'s two-corner formula IS JDK-faithful for
  non-rectangular shapes, and must be left alone. The defect is that
  `Rectangle`/`Rectangle2D` must override it and the shim's
  `Rectangle2D` didn't (and shim `Rectangle` lacked the int overload
  entirely). This also explains why the bug was invisible elsewhere:
  point containment (`contains(x,y)`) is correct in the shim, and most
  other `contains(Rectangle)` callers in the pipeline either never hit
  an exactly-touching edge or their misses were absorbed downstream.

Why the glyphs looked "systematically ~1 px smaller with fewer
sections" (§23.6): a char's sections that touch its box edges are
exactly the outermost ink (ascender tops, descender bottoms, rightmost
strokes) — dropping them shrinks the compound glyph from the edges
inward, and chars whose every section touches an edge (hyphen
12×3 in a 13×3 box) get no glyph at all.

### 24.4 Fix (contained, shim-side only)

Files (hand-written shims; `gen_awt*.py` does not regenerate them):

- `teavm/shims/src/java/awt/Rectangle.java` — added the missing
  `contains(int,int,int,int)` overload, JDK semantics:
  `w > 0 && h > 0 && x >= this.x && y >= this.y && (x+w) <= this.x+width
  && (y+h) <= this.y+height`. `contains(Rectangle)` now resolves to it.
- `teavm/shims/src/java/awt/geom/Rectangle2D.java` — `contains(double,
  double,double,double)` now: `if (w <= 0 || h <= 0) return false;`
  then the inclusive far-edge test. Its `Double`/`Float` subclasses
  inherit the fix.
- `RectangularShape.java` deliberately UNCHANGED (see §24.3 — the
  two-corner form is JDK-faithful there).

Desktop-neutrality: desktop Java uses the real JDK classes, not the
shim, so no desktop behaviour changes. Shim unit test
(`/tmp/recttest/ShimRectTest.java`, shim classes patched in via
`--patch-module java.desktop=/tmp/shimtest`): **15/15 PASS** against
the JDK-measured cases in §24.3 (edge-bottom/right, interior, outside,
zero-size far corner/interior, negative w, overflow by 1 px,
`contains(Rectangle)`, `contains(Rectangle2D)`, double forms, point
far corner still false, point interior true).

### 24.5 Re-run results (full-out51, default stack, Node v24.22.1)

Build: `full-out51`, 0 problems, 3,050 classes (DIAG25 still in).
No-OCR control first (`run-noocr51.log`): 44,105 bytes — the same size
as §22 — 128 notes, 0 lyrics, 0 tuplets, divisions 1. No regression.

- **Hymn crop** (`run-ocr-crop51.log`, 12,554 ms): DIAG25 SEC/RUNS/CHAR
  **all 172 CHAR lines now identical** to desktop (56/56 SEC, 56/56
  RUNS, 172/172 CHAR). 38 lyrics, 80 notes, 0 tuplets, divisions 1.
  Deep diff vs desktop crop: **10** — 2 source filename (expected,
  different input paths) + 8 × ±1 `default-x` (the known §22 sub-pixel
  residuals). The §23 crop categories (divisions 1→3, tuplet
  corruption) are gone.
- **Full hymn** (`run-ocr-hymn51.log`, main() 37,496 ms): 128 notes,
  2 parts, 16 measures, **52 lyrics**, **0 tuplets**, divisions 1,
  46,526 bytes (`phase24/wasm-hymn-ocr51.musicxml`). Deep diff vs
  desktop full hymn: **13** — 2 filename + 1 credit-words font-size
  10 vs 9 (known stub-font cosmetic, §23.6) + 9 × ±1 `default-x` +
  1 × `staff-distance` 101→102 (±1). Zero duration/syllabic diffs:
  the §23.6 categories (duration scaling from divisions 1→3,
  syllabic begin/end on 28 notes) are gone. This is now at the same
  fidelity level as the §22 no-OCR comparison (12 diffs, same kinds).
- **Hallelujah** (`run-ocr-hallelujah51.log`, main() 68,688 ms):
  **lyrics 164 = desktop 164** (was 153 — the 11-lyric-element gap
  is closed; the lyric-element counts now match exactly. Multiset
  recall vs the 208-syllable ground truth was NOT re-scored for the
  new file in this round — §23.7 scored desktop 156/208 and Wasm
  145/208, so do not quote a new recall figure until it is re-scored.)
  BUT the note /
  measure-grid gap remains: Wasm 301 notes, 11 measures/part vs
  desktop 330 notes, 14 measures/part. Per part: desktop P1–P4
  [1,1,1,1,…] (3 rest measures padded first), Wasm P1–P4 [1,1,1,5,…]
  (the D5 opening is measure 1); P5–P8 identical in structure
  (Wasm [5,7,9,1,…] vs desktop [1,1,1,5,…] — same music, different
  padding). This is NOT trap 4's text-glyph mechanism: the text
  glyphs are now identical, and the padding decision (whether a part
  gets leading rest measures to a common grid) happens in measure /
  part assembly, not in `retrieveSections`. **Next diagnostic named,
  not started:** run no-OCR Hallelujah under Wasm vs desktop on the
  same luma input — if the grid already differs there, the divergence
  is pre-TEXTS (measure-stack / first-bar logic, possibly the §18
  barline/ledger 1–2 px jitter); if it only differs with OCR lines,
  dump the per-part first-bar / measure-stack decisions on both
  sides. Do not start unbounded bisection here.

### 24.6 Verdict — (a) contained fix applied

Trap 4 is a **contained shim fix, applied and proven on the hymn**:
the §23 "most plausibly a TeaVM defect" classification is withdrawn —
no minimal repro for TeaVM exists because there is no TeaVM defect
here, and nothing should be filed against TeaVM for trap 4. The
candidate upstream items remain #272, #21244/#15448, and the §11
`Profiles.getName()` gap (plus the §19 TColor classlib defect, fixed
in the fork). What remains for a working end-to-end run, in order
(updates §23.9):

1. **Hallelujah measure-grid / note gap** (301 vs 330 notes, 11 vs 14
   measures/part) — next diagnostic named in §24.5, not started.
2. **Lindenbaum HEADERS CME** (§23.8) — still open; `deu` on real
   German lyrics still untested end to end.
3. **Clean build** — strip the DIAG25 prints (this round) and
   DIAG14/16/17/18/19/20/22/23/24 before any "clean" build.
4. **Real-browser run** — everything so far is Node v24.22.1; a Chrome
   run of the WasmGC module is still untested (needs Jonathan's
   machine — no Chrome in this VM).

### 24.7 Files

- §24 diagnostic: `teavm/patched/make_patches.py` ROUND 21 (DIAG25);
  `teavm-fork/phase24/` — `desktop-hymn-crop-ocr.log`,
  `run-ocr-crop50.log` (pre-fix Wasm), `run-ocr-crop51.log`,
  `run-ocr-hymn51.log`, `run-ocr-hallelujah51.log`,
  `run-noocr51.log`, `compare_diag25.py`, `prove_edge.py`,
  `wasm-hymn-crop-ocr51.musicxml` (30,566 B),
  `wasm-hymn-ocr51.musicxml` (46,526 B),
  `wasm-hallelujah-ocr51.musicxml` (115,965 B, 164 lyrics),
  `wasm-hymn-noocr51.musicxml` (44,105 B),
  `desktop-hymn-crop-ocr.musicxml` (30,708 B, DIAG25 desktop run),
  `full-build50.log`, `full-build51.log`, `build-diag25.log`,
  `build-fix.log`, `desktop-compile.log`.
- Fix: `teavm/shims/src/java/awt/Rectangle.java` (int `contains`
  overload), `teavm/shims/src/java/awt/geom/Rectangle2D.java`
  (inclusive `contains(double,double,double,double)`).
  Shim unit test in `/tmp/recttest/ShimRectTest.java` (15/15 PASS;
  JDK ground-truth probes in `/tmp/recttest/RectTest{,2,3,4}.java`).
- Builds: `teavm-fork/full-out50/` (pre-fix, DIAG25), `full-out51/`
  (fixed, 0 problems, 3,050 classes).
- Nothing pushed, filed, or merged; `jdlehman/score-reader` untouched.

## 25 — Hallelujah measure-grid / note gap: NO-OCR control diverges pre-TEXTS; localised to a missing MultipleRestInter in the Wasm SIG — 2026-11-09 (INCONCLUSIVE, verdict (c); next diagnostic named, stopped per the task)

### 25.0 Headline

**The grid gap is NOT an OCR/text effect at all.** The no-OCR control
diverges on the same luma input: Wasm 259 notes / 11 measures per part vs
desktop 275 / 14, with pitched notes **217 = 217 identical** (same
multiset, same order, Wasm m1 = desktop m4 through Wasm m11 = desktop
m14). The entire 16-note no-OCR gap is rests, and 12 of the 16 are the
three leading whole-measure rests per part. The OCR gap decomposes the
same way: pitched 218 = 218 identical, rests 112 vs 83 (29 = the same 3
leading rest measures per part × 8 parts = 24, plus 5 rhythm-split rests
in the music measures, see §25.5).

**Localisation (DIAG26, this round):** both sides build the same 12 raw
measure stacks (4+4+4) with identical stack bounds, and the first stack
has actual duration 0 on both sides. The difference is a single SIG
fact: desktop system #1 contains **4 MultipleRestInter** (one per staff,
centre x=584, count=3, grades 0.57–0.63); Wasm system #1 contains
**0**. With the flag set, desktop `MeasureFixer` expands the first
stack to ids 1–3 and the music starts at id 4 (14 measures); without it
the Wasm stack is empty, the next (music) stack merges into it via
`isRealStart` (Wasm m1 width 456 = desktop m1 211 + m4 245, first note
+210 px right), and the page has 11 measures. The divergence is
therefore upstream of `MeasureFixer`, in `MultipleRestsBuilder`
(SYMBOLS) or earlier — which step drops the multiple rest is NOT
identified in this round. **Verdict (c): inconclusive, with the next
diagnostic named (§25.6).** No fix applied, no repro, nothing filed.

### 25.1 Method (one diagnostic round)

- No-OCR pair on the same luma input (`phase23/hallelujah-satb.gray`,
  2480×3509, + `.json`): Wasm `full-out51` via
  `run-fullout-noocr.mjs` (`phase25/run-noocr-wasm51.log`,
  `phase25/wasm-hallelujah-noocr51.musicxml`, 98,789 B, 0 lyrics);
  desktop `DesktopOcrExport` on `phase23/hallelujah.png` with
  `testocr.file=phase23/empty-ocr.txt`
  (`phase25/desktop-hallelujah-noocr51.log`,
  `phase25/desktop-hallelujah-noocr51.musicxml`, 105,578 B, 0 lyrics).
  The desktop file is **byte-identical** to the §23.7 reference
  (`phase23/desktop-hallelujah-noocr.musicxml`) — the §23.7 control is
  reproduced exactly (275 notes, 4 parts, 0 lyrics, 14 measures).
- Comparators (new, `phase25/`): `compare_noocr.py` (per-part /
  per-measure counts + pitched-sequence alignment) and
  `compare_offset.py` (offset-aware diff: Wasm measure *i* vs desktop
  measure *i*+3). Outputs `compare-noocr51.txt`,
  `compare-ocr51.txt` (same tools on the §24 OCR pair:
  `phase23/desktop-hallelujah-ocr.musicxml` vs
  `phase24/wasm-hallelujah-ocr51.musicxml`),
  `compare-offset-noocr51.txt`, `compare-offset-ocr51.txt`.
- DIAG26 (ROUND 22 in `teavm/patched/make_patches.py`, same pattern as
  §24 DIAG25): prints in `MeasureFixer.process(SystemInfo)` — per
  system, the `MultipleRestInter` list (centre/bounds/count value/
  grade); per stack, `getMultipleMeasureCount`, `isMultiRest`,
  `getActualDuration`, `isEmpty`, and the assigned id after the branch
  chain. Same patched file compiled into `phase23/classes` for the
  desktop harness (`phase25/desktop-compile-diag26.log`) and into
  `full-out52` for Wasm (0 problems, 3,050 classes, 28,609 methods,
  LOADS OK in 350 ms; `phase25/full-build52.log`). DIAG26 runs
  (`phase25/run-noocr-wasm52.log`,
  `phase25/desktop-hallelujah-noocr52.log`) reproduce the §25.1
  `.mxl` files **byte-identically** — DIAG26 is print-only.

### 25.2 No-OCR comparison — the gap is rests only, offset 3

| | Desktop no-OCR | Wasm no-OCR |
|---|---|---|
| Parts | 4 (all "Voice") | 4 (all "Voice") |
| Measures/part | 14 | 11 |
| Total notes | 275 | 259 |
| Pitched notes | 217 | 217 (identical multiset + order) |
| Rests | 58 | 42 |
| Divisions (m1) | 12 | 12 |

Per part (notes / pitched / rests): P1 68/53/15 vs 65/53/12; P2
68/54/14 vs 64/54/10; P3 70/55/15 vs 66/55/11; P4 69/55/14 vs
64/55/9. After offset 3 (Wasm m*i* = desktop m*i*+3) the pitched
sequences align exactly in every part; desktop m1–m3 are whole rests
(duration 48) with no Wasm counterpart. The 16-note gap is 12 leading
rests (3 × 4 parts) + 4 rests inside music measures (§25.5).

Raw measure stacks are identical: both logs print `12 raw measures:
[4 in system#1, 4 in system#2, 4 in system#3]`. So barline/measure-
stack building (§18 jitter hypothesis) is exonerated at the stack
level — the divergence is in what happens to the first stack after
that.

### 25.3 OCR pair decomposes the same way (existing §24 files, re-compared)

Desktop OCR 330 notes / 8 parts / 14 measures; Wasm OCR 301 / 8 / 11.
Pitched: **218 = 218 identical** (per-part 37/37/38/38/17/17/17/17).
Rests: 112 vs 83 (delta 29). With offset 3 the pitched sequences
align exactly in all 8 parts; the leading-rest difference is exactly
3 measures in every part (desktop P1–P4: 6 leading rest measures vs
Wasm 3; P5–P8: desktop music starts m4 vs Wasm m1). The remaining 5
notes of the 29 are the §25.5 music-measure rhythm rests (P1 m11,
P2 m7, P3 m11, P4 m7, P4 m11 — one extra rest each on desktop).
Separately, the trailing whole-rest measures in P5–P8 differ in
duration only (Wasm rest duration 18 vs desktop 16 in m7/m11 —
recorded, not explained; plausibly a knock-on of the merged first
stack's expected duration, not pursued here). Lyric recall was NOT re-scored
in this round — the Hallelujah OCR `.mxl` files are unchanged from
§24, so the §23.7 figures (desktop 156/208, Wasm 145/208) stand as
the last scored values and no new figure is claimed.

### 25.4 DIAG26 — the decision trace (the localisation)

Desktop system #1:

```
DIAG26 system#1 multipleRests=4
DIAG26 multirest center=java.awt.Point[x=584,y=597] bounds=...[x=500,y=592,width=168,height=11] count=3 grade=0.6337...
DIAG26 multirest center=...[x=584,y=839] ... count=3 grade=0.6337...
DIAG26 multirest center=...[x=584,y=1057] ... count=3 grade=0.5657...
DIAG26 multirest center=...[x=584,y=1273] ... count=3 grade=0.5657...
DIAG26 stack sys=1 idx=0 left=329 right=687 count=3 isMultiRest=true actualDur=0 isEmpty=false
DIAG26 stackDone sys=1 idx=0 id=1 multiRest=true inSystem=true
DIAG26 stack sys=1 idx=1 left=687 right=1104 count=null ... isEmpty=false
DIAG26 stackDone sys=1 idx=1 id=4 ...
```

Wasm system #1 (full-out52):

```
DIAG26 system#1 multipleRests=0
DIAG26 stack sys=1 idx=0 left=329 right=687 count=null isMultiRest=false actualDur=0 isEmpty=true
DIAG26 stackDone sys=1 idx=0 id=1 multiRest=false inSystem=true
DIAG26 stack sys=1 idx=1 left=687 right=1104 count=null isMultiRest=false actualDur=1 isEmpty=false
DIAG26 stackDone sys=1 idx=0 id=1 multiRest=false inSystem=true   <- isRealStart merge: music stack merged into prev, removed
DIAG26 stack sys=1 idx=1 left=1104 right=1657 ... id=2
DIAG26 stack sys=1 idx=2 left=1657 right=2301 ... id=3
```

Systems #2/#3 are identical on both sides (`multipleRests=0`,
stacks ids 7–10 / 11–14 desktop, 4–7 / 8–11 Wasm — the shift is
entirely the system-1 expansion).

Mechanism, read from the sources (`MeasureFixer.java`,
`MeasureStack.java:996`, `PartwiseBuilder.java:975,2168`):

- `MeasureStack.getMultipleMeasureCount(multipleRests)` returns null
  when the list is empty or no inter centre falls in `[left, right]`;
  0 when the inter has no `MeasureCountInter`; else the count value.
  Desktop centres (x=584) sit comfortably inside stack [329, 687],
  so the centre-range test is not the discriminator here.
- `MeasureFixer.isEmpty(stack)` returns false if `isMultiRest()`,
  else true iff actual duration is 0. The first stack's actual
  duration is **0 on both sides** — the multi-rest bar contributes no
  chord on either side; only the flag distinguishes the stack.
- With the flag, desktop takes the multi-rest branch (`lastId +=
  count-1`, ids 1–3) and `PartwiseBuilder.insertMultipleRest` emits
  3 measures (the first carrying `<multiple-rest>3</multiple-rest>`,
  all with `print-object="no"` whole rests — 4 such elements in the
  desktop file, one per part; 0 in the Wasm file).
- Without the flag, Wasm takes the empty branch, then the music stack
  at idx=1 takes `isRealStart` (`im == 1 && isEmpty(prevStack)`):
  `prevStack.mergeWithRight(stack)` + `removeStack`. The merged
  measure keeps the first stack's left edge: Wasm m1 width **456 =
  desktop m1 (211) + m4 (245)**, first note default-x 238 vs
  desktop m4's 28 (+210). The merge signature in the `.mxl` matches
  the DIAG26 trace exactly.

Ruled out in this round: TEXTS/OCR (gap exists with no OCR lines);
barline/ledger jitter at stack level (raw stacks 4+4+4, stack bounds
identical left/right on both sides); `MeasureFixer` logic itself
(same code; given `multipleRests=0` the Wasm outcome follows
deterministically, given 4 rests the desktop outcome does); the
centre-range test (no inter exists to test on Wasm); the count
relation (no inter to attach a count to on Wasm; desktop counts are
all 3). What remains unknown: why `MultipleRestsBuilder` (SYMBOLS
step) creates 0 `MultipleRestInter` under TeaVM — beam-candidate
detection, serif filament building, or count linking. That is the
next diagnostic, not this one.

### 25.5 Secondary divergence — StackRhythm "no correct rhythm" (separate, smaller)

Offset-aware diff of the aligned music measures: only 6 of 44
no-OCR aligned measures differ, all with identical pitched
sequences, all in the same shape — desktop halves the first notes'
durations and adds a short rest where Wasm keeps quarters:

- P1 desk m11: desk durs [6,6,8,8,8] vs Wasm [12,12,8,8,8]
  (durations only, same rest count).
- P2 desk m7: desk [6,6,6,6,12,12] (6 notes, 1 rest) vs Wasm
  [12,12,12,6,12] (5 notes, 0 rests).
- P3 desk m10: desk [6,6,4,3,3,6,4,4,6] vs Wasm
  [6,6,6,3,2,6,4,6,6] (same counts, different rhythm split).
- P3 desk m11: desk [6,6,6,4,8,12] (6 notes, 1 rest) vs Wasm
  [12,12,12,4,8] (5 notes, 0 rests).
- P4 desk m7: desk [6,6,6,4,8,12] vs Wasm [12,12,12,4,8].
- P4 desk m11: desk [6,6,12,12,12] (5 notes, 1 rest) vs Wasm
  [12,12,12,12] (4 notes, 0 rests).

These are the same 6 measures in the OCR pair (durations scaled by
divisions 4 instead of 12). They correlate with the RHYTHMS-step
logs: Wasm logs `StackRhythm ... no correct rhythm` for S2 #5, S2
#8, S3 #9; desktop only for S2 #8 (global stack numbering:
#5 = system-2 stack 1 = desktop id 7; #8 = system-2 stack 4 =
desktop id 10; #9 = system-3 stack 1 = desktop id 11). So Wasm
fails rhythm resolution on two stacks desktop resolves (#5, #9)
and both fail #8 yet still differ there. This is a **separate**
divergence in `StackRhythm`/voice termination, downstream of (and
independent of) the multi-rest gap — it accounts for 4 of the 16
no-OCR notes and none of the measure-count gap. Named as its own
open item; not diagnosed further in this round.

### 25.6 Verdict — (c) inconclusive, next diagnostic named

- (a) Contained fix: **no.** No fix is identified — the missing
  `MultipleRestInter`'s cause is upstream of `MeasureFixer` and
  unlocalised within `MultipleRestsBuilder`/beam detection.
- (b) Genuine TeaVM defect with localised operation + minimal repro:
  **no.** The failure is localised to "no `MultipleRestInter` created
  in system #1's SIG under TeaVM", but not to a single small
  operation, and there is no minimal repro.
- (c) Inconclusive: **yes.** Ruled out: OCR/TEXTS, stack building,
  `MeasureFixer` logic, centre-range test, count relation.
  **Next diagnostic (named, not started): DIAG27 in
  `MultipleRestsBuilder.createInters` (and its caller)** — dump, per
  system on both sides, the `found` beam map (each `BeamInter`
  candidate: centre/bounds/grade + its LEFT/RIGHT `StaffPeak`s),
  `getSectionsByWidth` counts, and whether each candidate's serif
  filaments build — to distinguish "no beam candidate under TeaVM"
  (beam detection / classifier upstream) from "beam found but serif
  or count linking failed". If the beam candidate is absent, the
  diagnostic moves one step further up (beam building /
  `BeamsBuilder`); if present, it stays in the serif/count linking.
- Lindenbaum HEADERS CME (§23.8) still open — not touched in this
  round, per the task.
- Lyric recall not re-scored (§25.3).

### 25.7 Files

- `teavm/patched/make_patches.py` ROUND 22 (DIAG26 in
  `MeasureFixer.java` — diagnostic prints only; stays in the build
  like DIAG24/25, to be stripped in a clean build).
- `teavm-fork/phase25/` — `run-noocr-wasm51.log`,
  `wasm-hallelujah-noocr51.musicxml` (98,789 B),
  `desktop-hallelujah-noocr51.log`,
  `desktop-hallelujah-noocr51.musicxml` (105,578 B, byte-identical
  to the §23.7 reference),
  `run-noocr-wasm52.log`, `wasm-hallelujah-noocr52.musicxml`
  (byte-identical to the 51 run),
  `desktop-hallelujah-noocr52.log`,
  `desktop-hallelujah-noocr52.musicxml` (byte-identical to the 51
  run), `compare_noocr.py`, `compare_offset.py`,
  `compare-noocr51.txt`, `compare-ocr51.txt`,
  `compare-offset-noocr51.txt`, `compare-offset-ocr51.txt`,
  `build-diag26.log`, `desktop-compile-diag26.log`,
  `full-build52.log`, `SECTION25.md` (this section's working copy).
- Builds: `teavm-fork/full-out52/` (DIAG26, 0 problems, 3,050
  classes, 28,609 methods, LOADS OK in 350 ms).
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.

## 26 — Hallelujah grid gap: DIAG27→30 localise it to missing beams; root cause is a shim `Area` defect; two performance defects on the way out; now blocked on a CURVES-step slur trap — 2026-11-09/10 (verdict (a) for the beam/grid-gap root cause and the performance blockers; BLOCKED on the slur trap, next diagnostic DIAG32 named)

### 26.0 Headline

**The §25 grid gap is fixed at its root cause — and the fix is verified
in the running pipeline.** Wasm now builds the same beams as desktop
(DIAG28 system #1: 5 beams + 1 hook, assignedSpots 5, identical to
desktop), the 4 multi-rest beams are FOUND (DIAG27, grades 0.6158,
centres x=584), and the run reaches PAGE with **12 raw measures:
[4 in system #1, 4 in system #2, 4 in system #3]** — the desktop
structure. The root cause was a shim defect, not a TeaVM defect:
`java.awt.geom.Area.subtract`/`intersect`/`exclusiveOr` were no-ops
and `Path2D.contains` was bounds-based, so `BeamItem.getBeltArea`
(`beltArea.subtract(coreArea)`) never removed the core and every good
beam's beltRatio came out above the 0.4 cap.

Getting the fix out exposed **two performance defects**, both fixed
in this round:

1. The first `Area` fix used ear-clipping triangulation for non-convex
   clips — it blows up exponentially on page-minus-staff (`BenchTri`:
   OOM in `Area.toArray` ← `clipHalfPlane` ← `subtractConvex`) and the
   run stalled pre-HEADS (out57 killed after 6+ min at 172 log lines).
   Replaced by Greiner–Hormann (see §26.6).
2. Even with GH, the run still stalled at the same 172 lines.
   DIAG31 localised it precisely: `subtractConvex` returned
   OVERLAPPING pieces (one per clip edge), so the area segment count
   grew ~×2.2 per staff strip — **286,655 segments after 12 strips vs
   65 on desktop** — and `BufferedImageGraphics.fill(area)` (per-pixel
   `contains()`) could never finish. Fixed two ways: `subtractConvex`
   now emits disjoint pieces (each piece clipped to the inside of all
   earlier half-planes), and `fill(Shape)` is a scanline sweep
   (pixel-identical, full page 717 ms on desktop vs ~330 s for the old
   loop). After both, the area has 185 segments and the fill takes
   244 ms under Wasm.

**Current stopping point (new, §26.11):** the pipeline now crashes in
the CURVES step, `RuntimeError: dereferencing a null pointer` in
`SlurInfo.getCurve` (SlurInfo.java line 200, `right.getCtrlX2()`):
the right-side CircleModel's `Circle` has a null/NaN first or last
angle, so `Circle.computeCurve()` returns early and `getCurve()`
returns null. The crash is general — the hymn crashes with the
identical stack — and independent of the SIGraph `HeadHeadRelation`
reflection symptom (58 lines on Hallelujah, 0 on the hymn). Next
diagnostic named: DIAG32 (§26.13). No `.mxl` has been produced since
the beam fix, so the Hallelujah measure/note counts are still
unverified; the OCR comparison is likewise unrun (the run crashes
before export). Lyric recall not re-scored.

### 26.1 DIAG27 — the beam candidate is absent (ROUND 23)

DIAG27 in `MultipleRestsBuilder.createInters` (same patched file both
sides; desktop + Wasm `.mxl` byte-identical to the §25 controls with
prints on). Per system, the `found` beam map (BeamInter candidates +
side StaffPeaks):

- Desktop system #1: **5 beams** — 1 too-narrow reject at x=1316
  (w=29), plus the 4 multi-rest beams at x=500 (w=168), centres
  (584, 597 / 839 / 1057 / 1273), staff 1–4, grades
  0.6337/0.6337/0.5657/0.5657, each with 1 LEFT peak (start=500,
  width 4) and 1 RIGHT peak (start=665, width 3), all FOUND.
  Systems #2/#3: 2/3 beams, all rejected on |p1| ≈ 4.0–5.5.
- **Wasm: `beams=0` in all three systems.** `createInters` therefore
  never runs under TeaVM. The divergence is NOT in
  MultipleRestsBuilder at all — it moves one step up to
  `BeamsBuilder.buildBeams` (BEAMS step). Corroboration: the Wasm
  no-OCR `.mxl` has **0 `<beam>` elements vs desktop's 13** (both OCR
  and no-OCR runs); the hymn has 0 beams on both sides (no beamed
  notes — it cannot tell us whether beam building works generally
  under Wasm).

### 26.2 DIAG28 — spots exist; every spot is rejected inside `createBeams` (ROUND 24)

Prints in `BeamsBuilder.buildBeams` (BEAM_SPOT glyph count;
BeamInter/BeamHookInter counts in SIG after createBeams and after
buildBeams; assignedSpots) and in `BeamsStep.doProlog` (spot-lag
section count). full-out54, 0 problems, 3,050 classes. Both sides
reproduce their §25 control `.mxl` files byte-identically.

- Spot-lag sections **0 on both sides** (identical — not the
  discriminator).
- **beamSpots IDENTICAL on both sides: 221 / 200 / 110** (systems
  #1/#2/#3). After createBeams: desktop **5 / 2 / 3 beams (+1 hook
  in system #1), assignedSpots 5 / 2 / 3**; Wasm **0 / 0 / 0,
  assignedSpots 0**. So spots exist under TeaVM; the divergence is
  INSIDE `createBeams` → `checkBeamGlyph` — every spot glyph is
  rejected (or throws) under TeaVM.

### 26.3 DIAG29 — all gates agree; the divergence is inside `createBeamInters` (ROUND 25)

Tally of `checkBeamGlyph` failure strings per spot attempt (std
params, then small params) per system, plus gate params. NOTE on the
patch script: ROUND 25 reads the ROUND 24 output from
`patched/src/.../BeamsBuilder.java`, NOT the repo source via
`copy_src` — `copy_src` re-reads the repo and would wipe the DIAG14 +
DIAG28 prints already in `patched/src`. Build OK; DIAG14+DIAG28+DIAG29
all present (9 occurrences). full-out55, 0 problems, **3,052 classes,
28,616 methods**. Both sides reproduce their §25 control `.mxl`
files byte-identically.

- Desktop tally (system #1, 221 spots): `{too narrow=140, too
  steep=6, too narrow width=15, no good item=47, wavy or inconsistent
  borders=8}` — 216 failures, 5 succeed (= assignedSpots 5). System
  #2: `{too narrow=111, no good item=32, too narrow width=17, wavy=37,
  too steep=1}` (198 failures, 2 succeed). System #3: `{too narrow=50,
  too steep=1, no good item=29, too narrow width=12, wavy=15}` (107
  failures, 3 succeed). "too slim" never appears on either side.
  smallParams=null, so no second attempt. Gate params identical both
  sides: minBeamWidthLow=17.0, minHeightLow=6.3, maxBeamSlope=1.0,
  maxDistanceToBorder=2.55.
- Wasm tally: system #1 `{too narrow=140, too steep=6, too narrow
  width=15, **no good item=52**, wavy=8}`; system #2 no-good-item 32 →
  **34**; system #3 29 → **32**. Every other bucket is identical.
  **The ONLY difference is "no good item": +5 / +2 / +3 — exactly the
  10 spots that succeed on desktop.** So all `checkBeamGlyph` gates
  agree (width, mean thickness, slope, border consistency via
  `BeamStructure.computeLines()`, structure width, slope comparison) —
  the divergence is INSIDE `createBeamInters`: for the 10 spots that
  pass all gates, it returns false under TeaVM (→ "no good item") but
  true on desktop. `createBeamInters` per item: hook path (if width ≤
  maxHookWidth) and beam path `computeBeamImpacts(...)` → if impacts
  != null && grade ≥ `BeamInter.getMinGrade()` → `new BeamInter(...)`
  + `registerBeam`; exceptions are caught per item
  (`logger.warn("Could not compute impacts for beam...")` — 0 such
  WARN lines in either log, desktop or Wasm). So the next distinction
  is: impacts null vs grade below threshold vs exception swallowed
  elsewhere.
- Separate, unlinked symptom found while reading the Wasm log:
  **94 `ERROR [org.audiveris.omr.sig.SIGraph] Could not instantiate
  javaClass@1291568759 java.lang.NoSuchMethodException` lines in the
  Wasm Hallelujah log, 0 in the hymn Wasm log and 0 on desktop.**
  Source: `SIGraph.insertSupport` (SIGraph.java:971) —
  `supportClass.getDeclaredConstructor().newInstance()` throws
  NoSuchMethodException under TeaVM; the class prints opaquely as
  `javaClass@1291568759` under TeaVM, so the support class is not
  identified from the log alone. The errors cluster between REACH
  HEADS (line 476) and ReductionStep (line ~2065) — i.e. during
  STEMS/REDUCTION, before TEXTS — NOT at BEAMS time (DIAG27 lines are
  180–186), so they cannot cause beams=0 at MultipleRestsBuilder time;
  whether they are the same root cause as the `createBeamInters`
  failure is unproven. Smells like the §10/§11 reflection-metadata gap
  (TeaVM generates reflection metadata only for members a
  ReflectionPolicy declares accessible; the policy covers
  ConstantSet/WellKnowns/ShapeSet fields, not support-class
  constructors) — hypothesis only, not established. (See §26.12: the
  class is now identified as `HeadHeadRelation`, and the symptom is
  independent of the slur crash.)

### 26.4 DIAG30 — the failure is `impacts == null`, caused by beltRatio (ROUND 26)

Prints in `computeImpacts`' null branch (width, height,
coreCount/coreRatio, beltCount/beltRatio + thresholds) and in
`createBeamInters`' beam path (impacts null?, grade,
`BeamInter.getMinGrade()`). full-out56, 0 problems, 3,052 classes.
Desktop + Wasm `.mxl` byte-identical to §25 controls with prints on.
Decisive result — **the failure is `impacts == null` (not grade below
threshold) for all 10 good items, caused by beltRatio**:

- Multi-rest beam item (500.0,597.5)-(668.0,597.5), height 11.0:
  desktop impacts NOT null, grade **0.6337715158943545** (and
  0.5657861396938116 for the 1057/1273 staves), no reject line; Wasm
  coreCount=1512, **coreRatio=1.0**, beltCount=2640,
  **beltRatio=0.7106** → rejected (beltRatio > maxBelt 0.4).
- 1316 item (1316.0,340.5)-(1345.0,340.5), height 7.0: desktop grade
  0.5681260525209958, no reject; Wasm coreRatio 0.9901,
  beltCount=481, **beltRatio=0.4948** → rejected.
- Inferred desktop beltRatios (Wasm fore − core fore)/(beltCount −
  coreCount): multi-rest (1876−1512)/(2640−1512) = **0.323**; 1316
  (238−201)/(481−203) = **0.133** — both ≤ 0.4, consistent with desktop
  accepting.
- Other items agree: height-rejected items (height 15.06 >
  maxHeightHigh 12.6) reject identically on both sides.

**ROOT CAUSE (verified in source, §26): the shim
`java.awt.geom.Area` has `subtract`/`intersect`/`exclusiveOr` as
no-ops and `add` as a bare path append, and the shim `Path2D.contains`
is bounds-based (`getBounds2D().contains`).** `BeamItem.getBeltArea`
(BeamItem.java:96) does `beltArea.subtract(coreArea)` — a no-op under
TeaVM — so the belt Area still contains the 100%-black core, inflating
beltRatio above maxBelt 0.4 for every good beam → `computeImpacts`
returns null → `createBeamInters` returns false → zero `BeamInter` →
zero `MultipleRestInter` → the Hallelujah grid gap. Arithmetic check:
coreCount=1512 = 168×9 is consistent with the bounds-based contains +
`Rectangle2D.getBounds()` truncation (core bounds height 10.976 → 10
rows; row y=592 excluded since 592 < 592.012; 9 rows × 168 = 1512).
Belt dx=4, dy=2 inferred from beltCount 2640 = 176×15 (beltMarginDx
0.25 / beltMarginDy 0.15 fractions of interline).

### 26.5 The `Area`/`Path2D` fix (shim-side only)

Two shim files rewritten (hand-written, NOT regenerated by
`shims/gen_awt*.py` — only RoundRectangle2D among geom files is
generated, verified by grep):

- `teavm/shims/src/java/awt/geom/Path2D.java`: exact
  `contains(double,double)` (winding-number test honouring the winding
  rule, curves flattened by de Casteljau subdivision, flatness 0.25;
  NO on-boundary shortcut — the JDK uses the half-open crossing rule,
  verified by ProbeBoundary/ProbeRect); `contains(x,y,w,h)` = closed
  rect ⊆ closed shape (all four corners inside-or-on AND no flattened
  edge has a point strictly inside the open rect, via Liang–Barsky
  clip + midpoint test); `intersects(x,y,w,h)` = positive-area overlap
  (a rect corner strictly inside, or a path edge passing through the
  open rect, or an interior sample point just inside the shape lying
  strictly inside the open rect — the identical-rect case);
  `getPathIterator(at, flatness)` now actually flattens curves (it
  used to ignore flatness); flattened-polygon cache keyed on
  (coords.size, types.size, windingRule, flatness), invalidated by
  transform()/append()/setWindingRule() (all other mutators only
  append/clear, so the size check catches them). Also fixed
  nested-class shadowing: bare `Double` inside Path2D resolves to
  `Path2D.Double`, so all uses are now fully qualified
  `java.lang.Double`.
- `teavm/shims/src/java/awt/geom/Area.java`: real polygon boolean ops
  on flattened polygons (flatness 0.5). Sutherland–Hodgman clipping
  when the clip polygon is convex (exact decomposition P−Q =
  ∪ᵢ(P ∩ outside-Hᵢ) for convex Q — see §26.9 for why that
  decomposition had to be made disjoint); ear-clipping triangulation
  + sequential convex steps when non-convex (later replaced by
  Greiner–Hormann, §26.6); `add` stays append (union via
  multi-subpath contains); `exclusiveOr` = (A−B) ∪ (B−A). Degenerate
  (zero-area) polygons dropped; if a non-convex operand cannot be
  triangulated, that operand is left unapplied (previous no-op
  behaviour for that operand only).

**JDK boundary semantics measured empirically (ProbeBoundary.java,
ProbeRect.java, on this VM's JDK 25):** point-contains is the half-open
crossing rule — left/top edge inside, right/bottom outside (rect
(0,0)-(20,20): (0,0) true, (20,0)/(0,20)/(20,20) false; triangle
(20,20) true, (40,20)/(30,40) false; slanted parallelogram (0,10)
false, (0,18) true, (15,12) false, (15,20) true). Rect-contains =
closed rect ⊆ closed shape (e.g. (10,10,10,10) inside (0,0,20,20) is
true; (0,0,21,21), (5,5,20,20), (-1,0,21,20) false; zero-size rects
false). Rect-intersects = positive-area overlap: touching at an
edge/corner only is NOT an intersection ((20,20,5,5), (-5,-5,5,5),
(0,20,10,10), (20,0,10,10) all false; (0,0,21,21) true).

**Desktop verification harness** (`teavm-fork/phase26/areatest/`:
renamed `tshim.*` copies of the shim geom tree + stubs for
Point/Dimension/Rectangle (TeaVM classlib classes, absent from the shim
tree) + `TestArea.java` (JDK as oracle), `ProbeBoundary.java`,
`ProbeRect.java`, `DebugQuad.java`, `DebugXor.java`, `DebugXor2.java`,
`BenchTri.java`): baseline with old shims **501 checks, 192 failures**
(beam belts: JDK multirest 0.276 accept vs shim 0.808 reject; beam1316
JDK 0.0 vs shim 0.499; slanted contains wrong; boolean ops broadly
broken). After the fix: **552/555 pass, 3 residual failures** — all the
same single-pixel class on an integer-coordinate synthetic pair
(slanted parallelograms (0,10,30,14,8) vs (5,12,35,8,6)): point (5,9)
[a vertex of the clip polygon] and (15,8) [a point exactly on P's top
edge] classified inside by the shim, outside by the JDK. Mechanism:
the SH pieces' boundaries are the clip's half-plane LINES (not its
segments), so at a clip vertex the winding test sees a different local
boundary configuration than the JDK's minimal boundary. Accepted as a
documented known residual: beam belt/core cases are EXACT (multirest
belt JDK 168/608=0.2763, shim identical; beam1316 0/204 identical;
slanted core/belt identical); the random simple-polygon battery is
clean; a 1px AreaMask difference shifts a ratio by <0.002, far below
the beam grade margins (0.57–0.63 vs minGrade 0.08).

**Triangulation bug found and fixed during harnessing:** the ear test
"no other vertex inside the triangle" is NOT sufficient — the ear
diagonal can pass outside the polygon near a reflex vertex (found: a
triangle of the triangulation stuck out of a concave quad, 1px xor
mismatch). Added diagonal-midpoint-inside (winding test on the current
polygon) + diagonal-clear-of-non-incident-edges checks. Also found the
random-battery generator produced SELF-INTERSECTING polygons (bowtie:
edges A-B and C-D cross at (39.79,62.27); signed area −9.48 over a
12×26 span) — fixed the generator to sort around the polygons' own
centroid (star-shaped, hence simple). After the diagonal checks,
`triangulate()` returns null for that pathological self-intersecting
quad (correct fallback behaviour, not a bug).

**Separate pre-existing shim gap noted (not in scope):** shim
`RectangularShape.getPathIterator` returns null (both overloads), so
`new Area(ellipse)` NPEs under TeaVM. No Audiveris call site
constructs an Area from an Ellipse2D (verified by grep). The harness's
ellipse case was replaced with a cubic-blob built via curveTo (tests
flattening).

### 26.6 Performance blocker #1 — triangulation blows up; Greiner–Hormann replaces it

**PERFORMANCE BLOCKER (2026-11-10):** full-out57 (0 problems, 3,053
classes, 28,660 methods, built from the fixed shims) Wasm run was
KILLED with SIGTERM after 6+ min, still pre-HEADS (172 log lines vs
out56's 831 lines to REACH HEADS at 35.7 s; log static for 45 s at
98.8% CPU). Root cause localised: `StemScaler.getBuffer()`
(StemScaler.java:182-197) does `area.subtract(new
Area(mgr.getCoreStaffPath(staff)))` per staff; `getCoreStaffPath`
builds a path from the staff's first/last line splines (thin wavy
strip, ~100–500 vertices, non-convex) → my triangulation path →
sequential per-triangle SH subtraction MULTIPLIES pieces
exponentially (up to 3 pieces per triangle, ~98 triangles) → **OOM
measured on desktop** (`BenchTri.java`: triangulate 98 tris in 33.3 ms
at n=100, but `page.subtract(staff)` dies with `OutOfMemoryError:
Java heap space` in `Area.toArray` ← `clipHalfPlane` ←
`subtractConvex`). The stall is in/just after SCALE (StemScaler runs
during stem-scale retrieval), consistent with the log (last lines are
DIAG14 getSource NO_STAFF, the call at StemScaler.java:182).
`Skeleton.java:589` subtracts a RECTANGLE (convex, fast path) — not
affected. `StaffManager.computeStaffArea` intersects with a rectangle
slice (convex fast path) — not affected.

**DECIDED NEXT STEP (implemented this round): Greiner–Hormann for
subtract/intersect, replacing the triangulation path.** SH kept for
convex clips (fast path). GH design (verified on paper with the
two-squares example): entry flag = following edge inside the OTHER
polygon (midpoint test); INTERSECT: S forward entry→exit, C forward
exit→entry (start at unvisited S-entries); UNION: S forward
exit→entry, C forward entry→exit; DIFF: S forward exit→entry, C
BACKWARD until a C-entry node (start at unvisited S-exits).
No-intersection cases: INTERSECT → inside polygon or empty; UNION →
append both; DIFF with C strictly inside S → S plus C appended
REVERSED (opposite orientation, so non-zero winding cancels inside the
hole). Degeneracy handling: if any intersection is within eps of a
segment endpoint, or any edges are collinear-overlapping → perturb C's
vertices by a tiny deterministic offset (~1e-7, varying per attempt, up
to 4 attempts) and retry; if all attempts degenerate → fall back to
the triangulation path (small n) or leave unapplied. Then remove
`triangulate()`/`windingOf()`/`pointInTriangleStrict()` if unused.

Implementation (`teavm/shims/src/java/awt/geom/Area.java`, GH section;
`subtractOne`/`intersectOne` now call `greinerHormann` for non-convex
operands; `triangulate`/`windingOf`/`pointInTriangleStrict` removed):
entry/exit flags as designed; identical polygons handled exactly up
front (a nudge would turn an empty difference into a 1e-7 frame);
`greinerHormannAttempt` finds proper crossings only (any endpoint
touch or collinear overlap returns null → retry nudged); twins linked
by coordinate match; traces per the rules above with a 10,000-step
guard. **Harness after GH: 552/555, same 3 residuals** (the (5,9) /
(15,8) exact-vertex/edge points). **BenchTri after GH:
`page.subtract(staff)` 1.4 ms (n=100), 1.2 ms (n=200), 2.0 ms
(n=400), 4.0 ms (n=800)** — the OOM case is gone; result is 2
polygons with the expected vertex counts.

### 26.7 Performance blocker #2 (suspected) — scanline `fill(Shape)`

While the out58 run (GH in the build) was still stalling, the other
per-pixel hotspot in the same call was fixed pre-emptively:
`BufferedImageGraphics.fill(Shape s)` scanned EVERY pixel in the
shape's bounds and called `s.contains(xx+0.5, yy+0.5)` per pixel —
O(pixels × edges). For StemScaler's page-minus-staff area (2480×3509 =
8.7M pixels × thousands of edges) that is tens of billions of winding
tests. Rewritten as a scanline sweep that reproduces
`s.contains(xx+0.5, yy+0.5)` exactly (same half-open crossing rule as
`Path2D.contains`: an edge contributes iff it crosses the scanline in
the half-open y-range and its x-intercept is strictly right of the
pixel centre), in O(rows × edges + filled pixels); falls back to the
per-pixel loop when the shape has no usable flattened iterator (e.g.
shim Ellipse2D: `RectangularShape.getPathIterator` returns null) or
yields a curve segment.

Verification (`teavm-fork/phase26/filltest/TestFill.java`, run with the
shim patched into `java.desktop` via a desktop-only jar built from the
current `shims/src`): **page-minus-12-staff: new=716.8 ms, old (200
rows only)=18,966 ms, diffs=0**; triangle/rectangle/even-odd-frame/
nonzero-frame: 0 diffs; ellipse-fallback: 0 diffs. Re-run after the
§26.9 fix: page 698.8 ms, still 0 diffs everywhere. The old loop on the
full page would take ~330 s on desktop — it is the pathology, not a
measurement artefact.

(Note: the fill was NOT the (only) blocker — out59, with GH + scanline
fill, still stalled at the same 172 lines. DIAG31, §26.8, found the
real remaining blocker.)

### 26.8 DIAG31 — the stall is a segment-count explosion in `subtractConvex` (ROUND 27)

DIAG31 in `StemScaler.getBuffer()` (same patched file both sides,
print-only, with elapsed-ms timings + segment counts via a
next()-only counter, so no O(n²) `currentSegment` cost).

Desktop control (phase23/classes, DIAG31 compiled in): getBuffer
takes **88 ms total** (getSource 0 ms, eraseShapes 74 ms, all 12
subtracts ~8 ms, fill 1 ms). **coreSegs=4 per staff** (the core path
is a quadrilateral: bounds e.g. [330, 549.5, 1971×96.5]);
**areaSegs grows +5 per subtract: 10, 15, 20, …, 65.** Desktop `.mxl`
byte-identical to the §26 control (105,578 B).

Wasm full-out60 (0 problems, 3,056 classes; killed by the 240 s
timeout, but DIAG31 printed): coreSegs=4 (same as desktop), but
**areaSegs EXPLODES: 20, 65, 180, 455, 1090, 2525, 5720, 12755,
28110, 61385, 133060, 286655** — roughly ×2.2 per subtract — and the
last print is "DIAG31 before fill ms=1031". The run is stuck IN the
fill with 286,655 segments (the fill's edge collection via
`FlatIter.currentSegment` is O(n²) in the segment count, and the
scanline loop is O(rows × edges) — both explode).

**Root cause: `subtractConvex` returned OVERLAPPING pieces.** For
each subject polygon P and each edge i of the convex clip Q it
emitted P ∩ outside-Hᵢ, and those pieces overlap at the corners
(piece i and piece j both cover the region outside Hᵢ and Hⱼ). The
Area stores them as separate subpaths, so `contains()` double-counts
the overlaps (winding 2 — still "inside", which is why the harness
beam ratios were exact) — but the NEXT subtract splits EVERY
overlapping piece again, so the piece count multiplies per subtract.
The desktop JDK `Area` merges/overlaps correctly, hence +5 per
strip there.

### 26.9 Fix — disjoint pieces in `subtractConvex`

`subtractConvex` now clips piece i to the INSIDE of every earlier
half-plane Hⱼ (j < i): piece i = P ∩ outside-Hᵢ ∩ H₀ ∩ … ∩ Hᵢ₋₁.
The pieces are pairwise disjoint (piece i is outside Hᵢ, piece j>i
is inside Hᵢ) and their union is still P−Q (a point of P−Q is outside
some Hᵢ; take the smallest such i). Cost: O(k²) clips per subject
(k=4 → 10 clips), trivial.

Re-verification:

- Harness (`after-gh2.log`): **552/555, 3 failures** — same count,
  but the xor case now has 2 diff pixels instead of 1: new point
  (30,10), a VERTEX of the first parallelogram (30,10) [the other two
  are (5,9), a vertex of the second, and (15,8), exactly on the first
  parallelogram's top edge]. Mechanism: with disjoint pieces each
  boundary point is covered by exactly one piece, so a clip
  interpolation rounding at a shared boundary can drop it; the old
  overlapping pieces masked that. Same single-pixel exact-vertex/edge
  residual class as before; beam belt/core cases unchanged and EXACT
  (multirest 0.2763, beam1316 0.0). `BenchTri`: page.subtract(staff)
  1.2–9.3 ms.
- Fill test re-run (`filltest2.log`): page 698.8 ms, **0 diffs
  everywhere**.

### 26.10 full-out61 — beams restored, PAGE reached, then the slur trap

full-out61: 0 problems, 3,056 classes, 28,678 methods,
`classes.wasm` 13,586,085 bytes. Wasm Hallelujah no-OCR run
(`phase26/run-noocr-wasm61.log`, 2,347 lines, exit 1 after ~56 s):

- DIAG31 (Wasm): coreSegs=4; **areaSegs 20, 35, 50, 65, 80, 95, 110,
  125, 140, 155, 170, 185** — linear, +15 per subtract (desktop is
  +5; the disjoint decomposition yields up to 4 pieces per strip
  instead of the JDK's minimal 2 bands, but the count is bounded and
  small). eraseShapes 626 ms, subtracts ~3 ms, **fill 244 ms**
  (ms=631→875). The StemScaler stall is gone.
- **REACH HEADS ms=30786** (desktop 15,957 ms on the same luma
  input; out56 was 35,692 ms).
- **DIAG28 system #1: afterCreateBeams beams=5 hooks=1,
  assignedSpots=5** — identical to desktop (was 0/0/0 in out56).
- **DIAG27: the 4 multi-rest beams are FOUND** (grades 0.6158,
  centres x=584, staff 1–2 shown in the log excerpt; found=1,
  found=2, …). The §25 mechanism is restored end to end.
- **PAGE: `12 raw measures: [4 in system#1, 4 in system#2, 4 in
  system#3]`** — the desktop structure. The grid gap is fixed at
  the structural level.
- Then the run crashes in the CURVES step (see §26.11). **No `.mxl`
  was produced**, so the Hallelujah measure/note comparison
  (expect 275 notes / 14 measures per part) is still unverified, and
  the OCR comparison is unrun (the run crashes before export).

### 26.11 New blocker — CURVES-step null Bézier in `SlurInfo.getCurve`

```
RuntimeError: dereferencing a null pointer
    at wasm-function[11470]:0x3f3fff   SlurInfo.getCurve
    at wasm-function[4635]:0x29f144    SlurInter.<init>
    at wasm-function[16089]:0x48a2cc   SlursBuilder.weed
    at wasm-function[16090]:0x48a8a4   (caller of weed)
    at wasm-function[4227]:0x275224    CurvesBuilder.buildCurve
    at wasm-function[16104]:0x48c175   (caller of buildCurve)
    at wasm-function[16109]:0x48d317   SlursBuilder.buildSlurs
    at wasm-function[16048]:0x488588   Curves.buildCurves
    at wasm-function[27646]:0x8e2de4   CurvesStep.doit
    at wasm-function[27647]:0x8e2e1e   (step driver)
```

Mapped with `teavm/fn272/DumpSeq.java` + `DumpLine.java` on
`full-out61/classes.wasm.teadbg`. DumpLine gives the exact line:
**SlurInfo.java line 200: `double cx2 = right.getCtrlX2();`** — i.e.
`rightModel.getCurve()` returned null (the first deref of `right`;
lines 196–199 deref `left`, so `left` is non-null). Chain:
`SlurInfo.getCurve()` → `CircleModel.getCurve()` →
`Circle.getCurve()` → `Circle.computeCurve()` returns early, leaving
`curve` null, when `firstAngle` or `lastAngle` is null or NaN
(Circle.java:271-274). So the right-side CircleModel's Circle has a
null/NaN first or last angle under TeaVM. On desktop the same slur's
Circle has valid angles (desktop Hallelujah completes). The divergence
is upstream: either the slur glyph's points differ under Wasm, or the
Circle fit arithmetic differs (floating-point — a borderline
arcsin/acos argument or a degenerate fit tipping to NaN on one side).

**The crash is general, not Hallelujah-specific:** the hymn no-OCR
run with full-out61 (`phase26/run-noocr-hymn61.log`, REACH HEADS
17,818 ms) crashes with the **identical stack** (same function
indices and PCs). Any page with such a slur crashes in CURVES.

### 26.12 SIGraph `HeadHeadRelation` symptom — identified, independent of the slur crash

- Hallelujah Wasm log: **58 `ERROR [org.audiveris.omr.sig.SIGraph]
  Could not instantiate javaClass@1046586853
  java.lang.NoSuchMethodException` lines**, starting right after "OCR
  PREFED true" (line 2215), before TextsStep doProlog. (In the §26
  DIAG29 runs it was 94 lines with a different class id — the id is
  run-dependent.)
- The hymn Wasm log has **0** such lines — and the hymn still crashes
  with the identical slur stack. **So the SIGraph symptom is NOT the
  cause of the slur crash.** They are independent.
- Identification: the only `insertSupport` call site in the codebase
  is `SigReducer.java:326` —
  `sig.insertSupport(head, sameDur, HeadHeadRelation.class)` — so the
  failing support class is `HeadHeadRelation`. `insertSupport`
  (SIGraph.java:971) does
  `supportClass.getDeclaredConstructor().newInstance()`; under TeaVM
  that throws NoSuchMethodException, the catch logs the ERROR and
  returns null (the support is silently missing). Hypothesis (same
  family as §10/§11): TeaVM generates reflection metadata only for
  members a ReflectionPolicy declares accessible, and the policy
  covers ConstantSet/WellKnowns/ShapeSet fields, not support-class
  constructors. Unproven; a candidate contained fix is a ReflectionPolicy
  entry for the support classes (or for `HeadHeadRelation`'s no-arg
  constructor). Open item, not the cause of the beams=0 (DIAG27 lines
  are before it in step order) and not the cause of the slur crash.

### 26.13 Next diagnostic named: DIAG32 (not started)

In `Circle` / `SlurInfo.getCurve`, for the crashing slur: dump, on
both sides, the right-side Circle's parameters (center, radius,
firstAngle, lastAngle, the fitted slur-glyph points) and the
left-side's, plus which slur (glyph id, system/staff, bounds) it is —
to distinguish "the slur's glyph points differ under Wasm" (curve /
skeleton divergence upstream) from "the points agree but the Circle
fit arithmetic diverges" (floating-point / `Math` function difference
in the fit). If the points agree and the fit diverges, the next step
is a minimal repro of the Circle fit with those points (desktop vs
Wasm). If the points differ, the diagnostic moves one step up (slur
glyph construction / `CurvesBuilder` / `SlursBuilder`).

Also open from this round: whether the 58 missing `HeadHeadRelation`
supports change any downstream result once the slur crash is fixed
(they are silently null today — the chord reduction proceeds without
them); and the hymn regression (no `.mxl` since the slur crash blocks
export on both pages).

### 26.14 Files

- `teavm/patched/make_patches.py` ROUND 23 (DIAG27), ROUND 24
  (DIAG28), ROUND 25 (DIAG29), ROUND 26 (DIAG30), ROUND 27 (DIAG31
  in `StemScaler.java` — diagnostic prints only; stays in the build
  like DIAG24/25/26, to be stripped in a clean build).
- `teavm/shims/src/java/awt/geom/Path2D.java` and `Area.java`
  (rewritten in §26: exact contains/intersects, real boolean ops, GH
  for non-convex, disjoint `subtractConvex`); `teavm/shims/src/java/
  awt/image/BufferedImageGraphics.java` (scanline `fill(Shape)` +
  `fillPixels` fallback).
- `teavm-fork/phase26/` — `build-diag27/28/29/30/31.log`,
  `desktop-compile-diag27/28/29/30/31.log`,
  `full-build53/54/55/56/57/58/59/60/61.log`,
  `full-build58/59/60/61-shims.log`,
  `run-noocr-wasm53/54/55/56/57/58/59/60/61.log` +
  `.musicxml` (53–56 byte-identical to the §25 controls; 57/58/59/60
  killed by timeout at 172 lines / DIAG31; 61 crashes in CURVES, no
  `.mxl`),
  `desktop-hallelujah-noocr53/54/55/56/60.musicxml`
  (105,578 B; 60 byte-identical to 56),
  `diag27-desktop.txt`, `diag27-wasm.txt`,
  `desktop-hallelujah-noocr56.musicxml` (105,578 B),
  `wasm-hallelujah-noocr56.musicxml` (98,789 B),
  `build-area-fix.log`, `run-noocr-hymn61.log`,
  `areatest/` (harness: `TestArea.java`, `ProbeBoundary.java`,
  `ProbeRect.java`, `DebugQuad.java`, `DebugXor.java`, `DebugXor2.java`,
  `BenchTri.java`, `BenchIntersect.java`, `after.log`,
  `after-gh.log`, `after-gh2.log` (552/555), `bench-gh.log`,
  `bench-intersect.log`, `shimsrc/`, `shimclasses/`, `testclasses/`,
  `stubs/`),
  `filltest/` (`TestFill.java`, `filltest.log`, `filltest2.log`,
  `classes/`).
- Builds `full-out53/` (DIAG27), `full-out54/` (DIAG28),
  `full-out55/` (DIAG29), `full-out56/` (DIAG30), `full-out57/`
  (Area/Path2D fix, run killed), `full-out58/` (GH, run killed),
  `full-out59/` (GH + scanline fill, run killed), `full-out60/`
  (DIAG31, run killed at "before fill"), `full-out61/` (disjoint
  subtractConvex, 0 problems, 3,056 classes, 28,678 methods; run
  reaches PAGE then crashes in CURVES).
- Nothing pushed, filed, or merged; jdlehman/score-reader untouched.
- Still open, untouched in this round per the task: Lindenbaum HEADERS
  CME (§23.8); StackRhythm divergence (§25.5); BrowserOCR follow-up;
  photometric recovery for hard photos; clean build (strip DIAG
  prints); real-browser Chrome run; upstream filings (#272 draft +
  TPoint2D note, #21244 + two-part core patch, possibly §11
  Profiles.getName() and §19 TColor).
## Verdict: DONE at §27 — slur trap fixed at its root cause (genuine TeaVM Math.hypot defect); Hallelujah counts verified end to end (275 notes / 14 measures per part, rests 58=58, beams 13=13, slurs 22=22); new hymn slur residual (5 slurs vs desktop 0), next diagnostic DIAG33 named.

## 27 — CURVES slur trap: DIAG32 localises it to TeaVM `Math.hypot` returning NaN for hypot(NaN, +Infinity); contained fix applied, crash gone, Hallelujah counts verified — 2026-11-10 (verdict (a) for the crash; new hymn 8-slur residual, next diagnostic DIAG33 named)

### 27.0 Headline

**The §26 slur trap is fixed at its root cause — a genuine TeaVM classlib
defect, not a shim bug and not an Audiveris bug.** TeaVM's `TMath.hypot`
is `sqrt(x*x + y*y)`, which returns `NaN` for `hypot(NaN, +Infinity)` where
the JDK specifies positive infinity. For a perfectly collinear slur triple
the circle fit's centre is `(NaN, +Infinity)` (parallel bisectors, denominator
0), so the radius is `hypot(NaN, +Infinity)`: `+Infinity` on the JDK, `NaN`
under TeaVM. `CircleModel.createValid` rejects only infinite radius, so
desktop rejects the model and falls back to a line model, while Wasm accepted
a NaN-radius circle whose Bézier curve came back null — and `SlurInfo.getCurve`
dereferenced it, an uncatchable Wasm trap where the JDK throws a catchable
`NullPointerException` (which is why `weed()`'s `catch (Exception)` cannot
save the Wasm run).

Fix applied (fork classlib, same family as #272/TColor): `TMath.hypot` now
honours the two JDK special cases (`teavm-classlib-hypot.patch`, 29 lines),
jar entry replaced in place (pre-hypot jar kept as
`lib-fork/teavm-classlib-0.16.0-pre-hypot.jar`). Minimal repro
(`phase27/hypot-repro/`) proves it independently of Audiveris: pre-fix
`hypot(NaN,Inf)=NaN`, post-fix `Infinity`, all 6 cases JDK-exact.

**Verification (full-out63, 0 problems, 3,056 classes, 28,678 methods):**
hymn completes — `.mxl` 45,223 B, 128 notes, 2 parts, 16 measures, 0
NULLRIGHT, 0 RuntimeError; Hallelujah completes — `.mxl` 105,119 B,
**275 notes / 14 measures per part, rests 58 = 58, beams 13 = 13, slurs
22 = 22** — the §25/§26 grid gap is now VERIFIED fixed end to end, not
just structurally. Deep diffs vs desktop: Hallelujah 97 (2 source filename
+ 51 × ±1 position + 6 structural, all in the known §25.5 StackRhythm
measures); hymn 18 (2 filename + 1 credit text + 9 × ±1 default-x + 6
structural, all Wasm-extra slur notations).

**New residual (not the crash): hymn Slurs 5 vs desktop 0** (8 slur notations
in the Wasm `.mxl`, 0 on desktop). It appeared between out51 (Slurs 0) and
out63, i.e. after the §26 Area fix, and the 5 candidates' start points are
absent from the desktop log. Next diagnostic named: DIAG33 (§27.6). The
hypot fix is (a) for the crash; the slur residual is a separate open item.

### 27.1 DIAG32 — the crashing slur, both sides (ROUND 28)

DIAG32 in `SlurInfo` (same patched file both sides; desktop + Wasm `.mxl`
byte-identical to the §26 controls with prints on — desktop hymn completes
44,237 B, Wasm hymn crashes with the identical stack as out61).
Two prints: in `computeSideModel`, every side model as built (the 3 defining
points p0/p1/p2 + fitted Circle centre/radius/first/last angles); in
`getCurve()`, when the right curve is null, the slur id, point list, both
side models' Circle parameters and the global model.

Wasm hymn run (full-out62, 0 problems, 3,056 classes; crashes after ~31 s
with the identical stack, `wasm-function[11470]`):

- 244 `DIAG32 NULLRIGHT` lines (×2 calls each: `createInter`'s
  `getCurve() != null` check, then `weed`'s `SlurInter` ctor). Every one is
  a perfectly straight horizontal line (bounds height 1, all points same y)
  — staff-line fragments as slur candidates, e.g. id=253: 69 pts
  (1802,421)–(1870,421), sideLength=126. Most are harmless: when BOTH side
  curves are null, `left == right` (both null) is true, `getCurve()` returns
  null safely. The trap needs left valid + right null.
- The crashing slur (last NULLRIGHT before the trap): id=352, 152 pts,
  bounds `Rectangle[2090, 203, 153x8]` — a real curved slur with a flat
  tail. Left circle valid (centre (2153.0, −1777.0), radius 1985.0, angles
  1.6025/1.5391); right circle centre `(NaN, Infinity)`, radius `NaN`,
  angles NaN/NaN. So the right side's 3-point fit is exactly collinear.
- SIDEMODEL (Wasm, pre-fix): 26 lines, **roughNull=false for all 26** —
  `createValid` accepted every collinear triple.
- SIDEMODEL (desktop): 23 lines, 16 roughNull=true, 4 false. The 3 triples
  common to both sides are decisive — identical p0/p1/p2 on both sides,
  desktop roughNull=true, Wasm roughNull=false, e.g.
  (632,164),(695,164),(759,164) (all y=164) and (967,164),(1033,164),
  (1095,164). **The points agree; the fit diverges.** (The two SIDEMODEL
  sets are not fully comparable as sets: Wasm's run dies in `weed`, so its
  set is truncated at the crash, and ids differ; the 3 common triples are
  the comparison that matters.)
- Desktop: **0 NULLRIGHT, 0 "Could not create SlurInter"** — desktop never
  sees a null right curve, because its side models are LineModels for these
  triples.

### 27.2 The arithmetic chain (desktop repro)

`phase27/HypotRepro.java` (desktop JDK 25) replicates `Circle.defineCircle`
(`LineUtil.bisector` + `intersection`) for the common triple
(632,164),(695,164),(759,164):

```
den=0.0
center=Point2D.Double[NaN, Infinity]
dx=NaN dy=Infinity
JDK Math.hypot(dx,dy)=Infinity isInfinite=true
TeaVM TMath.hypot formula sqrt(dx*dx+dy*dy)=NaN isNaN=true
JDK Math.hypot(NaN,Inf)=Infinity
TeaVM formula sqrt(NaN*NaN+Inf*Inf)=NaN
```

Chain, verified end to end: bisectors of a collinear triple are parallel →
`LineUtil.intersection` divides by `den = 0.0` → centre `(NaN, +Infinity)`
(plain IEEE arithmetic, identical both sides) → `defineCircle` radius =
`hypot(NaN, +Infinity)` → JDK `+Infinity` → `CircleModel.createValid`
(`radius.isInfinite()`) returns null → `computeSideModel` falls back to
`new LineModel(points)` → `getCurve()` returns a line curve, never null.
Under TeaVM the radius was `NaN` → `isInfinite(NaN)` is false → a
CircleModel with NaN angles was returned → `Circle.computeCurve()` returns
early (first/last angle null or NaN, `Circle.java:271-274`) → `getCurve()`
null → `SlurInfo.getCurve` line 200 `right.getCtrlX2()` traps. On the JDK
the same dereference would throw a catchable `NullPointerException`
(`weed()` catches `Exception`); under TeaVM/WasmGC it is an uncatchable
`RuntimeError` trap — the same trap-vs-exception asymmetry as §13
(ClassCastException) and §14 (NPE).

Root cause in TeaVM source
(`src/classlib/src/main/java/org/teavm/classlib/java/lang/TMath.java:601`,
0.16.0 tag e87d452):

```java
public static double hypot(double x, double y) {
    return sqrt(x * x + y * y);
}
```

`TStrictMath.hypot` delegates to `TMath.hypot`, so it has the same defect.
No native generator overrides it (grep: only TMath/TStrictMath define
`hypot` in the fork source). JDK spec (`java.lang.Math.hypot`): "If either
argument is infinite, then the result is positive infinity. If either
argument is NaN and neither argument is infinite, then the result is NaN."

### 27.3 The fix (fork classlib — genuine TeaVM defect)

`teavm-classlib-hypot.patch` (29 lines, `git diff` in the fork `src/`):
the two JDK special cases before the existing formula, finite inputs
bit-identical to the old formula (no scaled algorithm, so no 1-ulp change
for finite values):

```java
public static double hypot(double x, double y) {
    // TEAVM §27: JDK semantics ... (see patch for the full comment)
    if (Double.isInfinite(x) || Double.isInfinite(y)) {
        return Double.POSITIVE_INFINITY;
    }
    if (Double.isNaN(x) || Double.isNaN(y)) {
        return Double.NaN;
    }
    return sqrt(x * x + y * y);
}
```

Procedure (same as §19 TColor): `TMath.java` compiled with
`javac -cp <classlib.jar>:<teavm>/lib/*` (the first attempt with only the
classlib jar failed with 87 errors — TMath imports interop/backend
annotation classes from the core/interop jars), verified with `javap -c`
(the new `isInfinite`/`isNaN` branches are present), then the jar entry
replaced in place (`lib-fork/teavm-classlib-0.16.0.jar`; pre-hypot jar kept
as `lib-fork/teavm-classlib-0.16.0-pre-hypot.jar`). Classification:
**TeaVM classlib defect** (JDK contract violated), fixed in the fork;
candidate for upstreaming with #272/#21244/TColor. Draft issue text:
`phase27/ISSUE_HYPOT_DRAFT.md` — NOT filed (Jonathan 2026-11-09: file the
TeaVM upstream PRs after our own work is done). Note on upstream process:
the TeaVM repo's own `src/AGENTS.md` prescribes Gradle (`./gradlew
:tests:test` with `teavm.tests.wasm-gc` / `teavm.tests.js` / `teavm.tests.c`
and `teavm.tests.optimized` set) plus checkstyle; Gradle does not work in
this VM (proxy CONNECT failure, established §7), so the fix was verified
here with javac + in-place jar replacement instead — run the Gradle suite
on a machine where Gradle works before submitting.

### 27.4 Minimal repro (TeaVM-level, independent of Audiveris)

`phase27/hypot-repro/`: `src/repro/HypotMain.java` (prints `Math.hypot`
for 6 cases), `jars-fixed.txt` / `jars-prefixed.txt` (repro2-jars pattern:
shims.jar + fork classlib + teavm libs + repro classes), `out-fixed/` /
`out-prefixed/`, runner `run-repro2.mjs`. Both builds 0 problems, 87
classes, 924 methods.

| case | JDK | pre-fix Wasm | post-fix Wasm |
|---|---|---|---|
| hypot(NaN, Inf) | Infinity | **NaN** | Infinity |
| hypot(Inf, NaN) | Infinity | **NaN** | Infinity |
| hypot(NaN, 1.0) | NaN | NaN | NaN |
| hypot(Inf, 1.0) | Infinity | Infinity | Infinity |
| hypot(3, 4) | 5.0 | 5.0 | 5.0 |
| hypot(0, 0) | 0.0 | 0.0 | 0.0 |

The repro fails exactly on the two spec-violating cases pre-fix and passes
all six post-fix. (Desktop `HypotRepro.java` in the same folder is the
JDK-side chain repro from §27.2.)

### 27.5 Verification — full-out63 (fix in)

full-out63: 0 problems, 3,056 classes, 28,678 methods,
`classes.wasm` 13,596,291 bytes (build.sh + Spike, canonical command).
DIAG32 prints still in the build (like DIAG14/24/25/26/27/31 — strip in a
clean build).

- Hymn no-OCR (`phase27/run-noocr-hymn63.log`, `wasm-hymn-noocr63.musicxml`,
  45,223 B): exit 0, MXL len=45223 exportMs=189 totalMs=57324, main()
  57,809 ms. **0 NULLRIGHT, 0 RuntimeError.** 128 notes, 2 parts,
  16 measures. Deep diff vs desktop62: **18** = 3 text (2 source filename
  + 1 credit font-size, known §24 cosmetic) + 9 attrib (±1 default-x,
  known sub-pixel residuals) + 6 child-count — all 6 are Wasm-extra
  `notations` (the §27.6 slur residual). No other structural diff.
- Hallelujah no-OCR (`phase27/run-noocr-wasm63.log`,
  `wasm-hallelujah-noocr63.musicxml`, 105,119 B): exit 0, MXL len=105119
  exportMs=96 totalMs=100284, main() 101,495 ms. **275 notes, 4 parts,
  56 measures (14/part), rests 58, beams 13, slurs 22 — all exactly the
  desktop numbers** (desktop56: 105,578 B, same counts). Deep diff vs
  desktop56: **97** = 3 text (2 filename + 1 credit) + 51 attrib
  (±1 default-x / relative-x) + 6 child-count — all 6 in
  part[4]/measure[8] and part[5]/measure[9] (tie / time-modification /
  notations), i.e. the known §25.5 StackRhythm divergence, not slurs
  (Hallelujah slurs match 22 = 22).
- SIDEMODEL on Wasm63: 81 lines, 26 roughNull=true (the collinear triples
  now rejected exactly like desktop, e.g. id=11 (1366,186)/(1253,186) —
  same ids as desktop now, where the pre-fix run had different ids).
  The hypot fix is therefore in the build and behaving identically to
  desktop at the `createValid` gate.

### 27.6 New residual — hymn Slurs 5 vs desktop 0 (separate open item)

Wasm63 hymn: `Slurs: 5` (SIGP: 2 good, grades 0.4614/0.5199, boxes
(460,805,103,9) and (996,805,85,10); 2 not good, 0.1409/0.1575) → 8
`<slur>` notations in P1 measures 6–8 (two slurs, numbers 1–2, placement
above, bezier-y 3–4). Desktop hymn: `Slurs: 0`, 0 slur notations.
out51 (pre-Area-fix) hymn: `Slurs: 0` — same as desktop. So the 5 slurs
appeared between out51 and out63, i.e. after the §26 Area fix (the hypot
fix cannot produce them: these are real curved arcs, height 9–10, whose
3-point fits are finite — the hypot change only affects Inf/NaN inputs).
The 5 candidates' start points (x=362/460/875/996, y≈805/806) occur **0
times** in the desktop log — desktop never builds those candidates at all
(not merely weeds them). Whether the divergence is in curve/skeleton
extraction upstream of `SlursBuilder` or in `computeModel`'s fit distance
(`SlursBuilder.java:400-460`: rough vs Jama-fitted circle, `dist >
maxArcsDistance` → "Bad circle fit") is NOT established in this round.
Note: Wasm DEBUG logging is neutered (LogUtil minimal rewrite), so the
desktop's 1,088 "Bad circle fit" lines have no Wasm counterpart to compare
against — the diagnostic must use `System.out` prints, as DIAG32 did.

**Next diagnostic named (not started): DIAG33** — in
`SlursBuilder.computeModel` (same patched file both sides): dump per
candidate p0/p2, rough radius, fitted radius, chosen circle, dist and the
verdict (accept / bad-fit / radius-too-small / angle-too-large), plus in
`weed`/`purgeStaffLines`/`purgeShortests` the per-slur keep/drop decision
— to distinguish "candidate never built on desktop" (curve extraction
upstream) from "candidate built but fit/weeding diverges". If the
candidates exist on both sides with the same points, the next step is a
minimal repro of the Jama-fitted Circle distance for those points.

### 27.7 Files

- `teavm/patched/make_patches.py` ROUND 28 (DIAG32 in `SlurInfo.java` —
  diagnostic prints only; stays in the build like DIAG24/25/26/27/31, to
  be stripped in a clean build).
- `teavm-fork/teavm-classlib-hypot.patch` (29 lines, fork `src/` git diff);
  `teavm-fork/lib-fork/teavm-classlib-0.16.0.jar` (TMath entry replaced in
  place; pre-hypot jar kept as
  `lib-fork/teavm-classlib-0.16.0-pre-hypot.jar`); fork `src/` git status
  now shows TMath modified alongside the earlier TColor/TDimension/TPoint/
  WasmTypeInference/CoroutineTransformation fork changes.
- `teavm-fork/phase27/` — `build-diag32.log`, `full-build62.log`,
  `build63.log`, `full-build63.log`, `run-noocr-hymn62.log` (crash, DIAG32),
  `run-noocr-hymn63.log`, `wasm-hymn-noocr63.musicxml` (45,223 B),
  `run-noocr-wasm63.log`, `wasm-hallelujah-noocr63.musicxml` (105,119 B),
  `desktop-hymn-noocr62.log`, `desktop-hymn-noocr62.musicxml` (44,237 B),
  `desktop-compile-diag32.log`, `HypotRepro.java` (desktop chain repro),
  `ISSUE_HYPOT_DRAFT.md` (draft only, NOT filed),
  `hypot-repro/` (`src/repro/HypotMain.java`, `classes/`,
  `jars-fixed.txt`, `jars-prefixed.txt`, `out-fixed/`, `out-prefixed/`,
  `build-fixed.log`, `build-prefixed.log`, `run-fixed.log`,
  `run-prefixed.log`), `compile-tmath.log`, `tmath-classes/`.
- Builds: `full-out62/` (DIAG32, crashes in CURVES — the diagnostic build),
  `full-out63/` (hypot fix in, 0 problems, 3,056 classes; current build).
- Nothing pushed, filed, or merged; `jdlehman/score-reader` untouched.
- Still open, untouched in this round per the task: Lindenbaum HEADERS CME
  (§23.8); StackRhythm divergence (§25.5 — now confirmed present in the
  out63 Hallelujah deep diff, 6 structural diffs in P4 m8 / P5 m9);
  HeadHeadRelation SIGraph symptom (§26.12, 58 lines on Hallelujah);
  BrowserOCR follow-up; photometric recovery for hard photos; clean build
  (strip DIAG prints); real-browser Chrome run; upstream filings (#272
  draft + TPoint2D note, #21244 + two-part core patch, §11
  Profiles.getName(), §19 TColor, §27 hypot draft).

## 28. DIAG33 — hymn slur residual (2026-11-10)

### 28.0 Verdict: (c) inconclusive, localised

DIAG33 ran to completion on both sides (after fixing a crash in the
diagnostic itself, §28.1). The slur residual is **not** a `computeModel`
fit-distance divergence and **not** a weed-logic divergence. It is
upstream of `SlursBuilder`, in skeleton / arc extraction: on Wasm the
skeleton carries extra diagonal SHORT spurs and 1–4 px longer staff-line
arcs, so extension merges staff-line fragments into taller curves whose
end part is not a `STAFF_ARC`; `purgeStaffLines` therefore keeps them,
weed keeps them, `createInter` accepts them — 5 slurs vs desktop 0.
The skeleton input (`NO_STAFF`) is proven identical except the known
§20 4 pixels, so the split "thinning diverges" vs "arc retrieval
diverges on an identical skeleton" is **not** established. No contained
fix identified; no genuine TeaVM defect localised. Next diagnostic
named: DIAG34 — dump the skeletonized buffer on both sides (§28.5).
No regression: full-out65 completes and its `.mxl` is byte-identical
to full-out63.

### 28.1 The out64 crash — a DIAG33 print bug, not a product bug

The first diagnostic build, full-out64 (ROUND 29 DIAG33), crashed on
the hymn no-OCR run where full-out63 completes: `RuntimeError:
dereferencing a null pointer`, PCs 0x3e013c/0x3e01df, deterministic 2/2
(piped run and a `script` pty run — identical DIAG output, 1,006
DIAG33 lines each, same last lines), last lines `DIAG33 WEED-IN n=1`
with the id line never printed. DumpSeq containment on
`full-out64/classes.wasm.teadbg` maps both PCs into
`[4062394..4062765) java.util.EnumMap.put` (TEnumMap.java lines
113/122 — `Class<?> cls = key.getClass()`, a null key).

The crash trigger is the WEED-IN id print itself. It called
`si.getBounds()`, and `SlurInter.getBounds()` line 506 is
`return new Rectangle(bounds = curve.getBounds())` — a virtual call
on `curve`, which is null for that inter. The crashing clump is
Wasm-only (desktop's 24th weed call has 0 inters, Wasm's has 1) and
the inter is id=14, grade=0.8, `curveNull=true` in the fixed build.
`getCurve()` returns null whenever either side model is null or not a
`CircleModel`, which is common for candidates still in weed()
(out65 shows `curveNull=true` for ids 14, 57, 58, 59, 69, 70, 109,
204, 207, 252, …) — desktop's weed never calls `getBounds()` on
them, so this is a diagnostic-print hazard only. The earlier id=4
prints worked because id=4's curve is non-null (empty bounds
`[0,0,0x0]`).

Control first: full-out63 re-run before bisecting completes,
45,223 B `.mxl` byte-identical to the §27 file (`Slurs: 5`).
ROUND 30 (`make_patches.py`): guard the `getBounds()` call in the
WEED-IN and WEED-OUT prints with a `curveNull` flag, and add
`WEED-STEP sort/stafflines/shortest/filter` prints bracketing each
purge stage. `TPrintStream.println` writes through immediately
(autoFlush false but `printSB()` flushes per call), and the pty run
agrees, so the log tail was a trustworthy crash point. full-out65
(ROUND 30, 3,056 classes, 28,678 methods, builds successfully):
exit 0, `MXL len=45223`, `.mxl` byte-identical to out63.

Attribution caveat (recorded, not resolved): the trap PC maps to
`EnumMap.put`, but the only dereference in the print evaluation that
can trap is `curve.getBounds()` (whose own range is
`[4063402..4063700)`). The two ranges are ~900 bytes apart; the
mapping is presumably a debug-info imprecision (inlining / address
base), not evidence of a second trap. No TeaVM defect is claimed
here and nothing is filed. The empirical result is unambiguous
either way: guarding `getBounds()` removes the crash, and nothing
else in the product code changed between out64 and out65.

### 28.2 DIAG33 method

ROUND 29 prints in `SlursBuilder` (same patched file both sides):
(a) `buildSlurs` seed arcs (first/last point, length, shape) + count;
(b) `computeModel` entry (isSeed, npts, p0/p1/p2, rough radius,
minRadius) and verdicts; (c) weed `WEED-IN` (id/grade/box),
counts after `purgeIdenticalEndings` / `purgeStaffLines` /
`purgeShortests`, `WEED-OUT` kept ids, `PURGE-STAFFLINE` drop
reasons, `PURGE-SHORTEST` longest/quorum/drops; (d) `createInter`
ACCEPT/REJECT (impacts null / grade low / curve null / glyph null).
Desktop: patched `SlursBuilder.java` + `SlurInfo.java` compiled
into `phase23/classes`, run `DesktopOcrExport phase23/hymn.png
phase33/desktop-hymn-noocr64.musicxml` with
`testocr.file=phase23/empty-ocr.txt` — exit 0, 1,786 DIAG33 lines,
`.mxl` 44,237 B byte-identical to desktop62 (DIAG33 is print-only
on desktop). Wasm: full-out65, hymn no-OCR, 33,993 DIAG33 lines,
`.mxl` 45,223 B byte-identical to out63.

### 28.3 Findings — the mechanism chain, each link measured

Seed arcs (`buildSlurs` relevants): desktop 764, Wasm 768.
`STAFF_ARC` 261 on both sides; `SHORT` 503 vs 507. Total seed
length 27,120 vs 27,683 (+563 px, +2%). At the bottom staff line
(y≈810) the shapes agree (`STAFF_ARC` both sides) but Wasm arcs
run 0–4 px longer, e.g. desktop (276,810)–(349,810) len=74 vs
Wasm (276,810)–(353,811) len=78; (798,810)–(862,810) len=65 vs
(798,810)–(866,811) len=69. Wasm also has extra diagonal SHORT
arcs desktop has no arc for in the same box, e.g.
(567,814)→(584,808) len=18, (672,814)→(688,808),
(1085,814)→(1101,808), (1179,814)→(1195,808),
(1273,814)→(1289,807) — spurs rising from just below the staff
line (y=814) to the line (y≈808).

`computeModel` calls: desktop 228 (51 seed / 177 extension) vs
Wasm 5,343 (764 seed / 4,579 extension). Wasm models every seed
arc; desktop models 51 — on desktop most arcs are consumed as
extensions of earlier curves (`arc.isAssigned()`), on Wasm they
stay unassigned and each gets its own `buildCurve`. The extension
attempt explosion, not the fit, is the first divergence.

Weed: desktop 102 calls, every one ends `longest==null`
(`purgeShortests` returns null only on an empty list), 0
`WEED-OUT` lines, 0 `CREATE-INTER` lines. Wasm 1,090 calls, 654
with a non-null longest, 2,200 `CREATE-INTER` lines, 100+
ACCEPTs, 5 surviving slurs. `purgeStaffLines` is the gate:
desktop drops all 7–8 non-empty candidates (ids 4, 32, 44, 57,
all `reason=STAFF_ARC`, ends e.g. (1773,506), (888,767),
(678,1045), (807,165)); Wasm drops 186 the same way but keeps
the 5. The 5 accepted slurs are ids 162 (362,806,98x11),
240/241 (997/992,809), 278 (787,809), 329/330 (461/456,809),
377 (875,806,121x11) — ~90–120 px long, 8–15 px tall, i.e.
merged curves, not single seeds: a staff-line fragment bridged
by the extra diagonal SHORT arcs to neighbouring ink, so the
merged curve's end part is not a `STAFF_ARC` and
`purgeStaffLines` (which deletes only when the end part
`getPartAt(end)` is a `STAFF_ARC` within `maxStaffLineDy` of a
staff line) lets it through. The 100+ other ACCEPTs die in
later stages (`handleTieCollisions` / `dispatchToParts` /
`connectOrphanSlurs` / `handleCollisions`); only these 5 reach
`pageSlurs` (`Slurs: 5`, 8 `<slur>` notations in P1 m6–8).

`NO_STAFF` re-verified post-§26: DIAG22 per-row FNV diff of
out65 against `phase20/diag22-desktop.txt` — only rows 483/484
differ (desktop zeros 247/229 vs Wasm 246/226; sums differ by
255 + 765 = the same §20 4 pixels). The §26 Area/fill change
did not change staff-removal output. Those 4 pixels are in
system 1 (rows 483/484) while the extra skeleton spurs are
spread across the whole page including system 2, so they cannot
explain the seed divergence.

### 28.4 Ruled out

- `computeModel` fit distance: candidates differ before any fit
  runs (desktop builds 0 candidates that reach `createInter`).
- Weed / `purgeStaffLines` / `purgeShortests` logic: same code,
  deterministic given the SIG; desktop's weed empties every
  clump because every candidate's end part is a `STAFF_ARC`.
- Seed-shape classification: `STAFF_ARC` on both sides at the
  slur locations; the difference is length and the extra
  diagonal SHORT spurs, not shape labels.
- `NO_STAFF` input: identical except the §20 4 pixels (§28.3).
- The §26 Area fix as a `NO_STAFF` change: DIAG22 re-verified
  (§28.3). (Whether the §26 fix changed the skeleton through
  some other path is not ruled out — see §28.5.)
- The out64 crash as a product bug: diagnostic-print hazard
  (§28.1); out65 completes byte-identically to out63.
- TEXTS/OCR: no-OCR runs both sides; the residual is in CURVES.

### 28.5 Verdict (c) — inconclusive, next diagnostic named

No contained fix: the divergence lives in the skeleton
(`Skeleton` / `buffer.skeletonize()` on the binary image, then
`ArcRetriever` / `JunctionRetriever`), and the precise split is
not established — it could be the thinning itself leaving
spurs on identical input, or arc retrieval walking an
identical skeleton differently (junction/branch handling).
Nothing here localises to a single small TeaVM operation, so
(b) does not apply either; in particular the `EnumMap.put` PC
from the out64 crash is a diagnostic-print artefact (§28.1),
not a product-code defect. Do not file anything from this
round.

Next diagnostic — DIAG34 (skeleton-buffer comparison): dump
the skeletonized buffer (per-row FNV + zero counts, DIAG22
style) on both sides for the hymn, and compare. If the buffers
match, the divergence is in `ArcRetriever`/`JunctionRetriever`
(segmentation of an identical skeleton — then bisect by
dumping junction lists); if they differ, it is in
`skeletonize()` (then bisect by operation inside the thinning
loop). A secondary hypothesis to check in the same round: the
spur pattern (diagonal bridges at stem/staff-line junctions)
is what a thinning spur-pruning difference looks like — check
whether `Skeleton` prunes spurs and whether that step reads
anything TeaVM-sensitive. Do not keep bisecting beyond DIAG34
in the next round without a fresh judgement.

### 28.6 Files

- `teavm/patched/make_patches.py` ROUND 29 (DIAG33) + ROUND 30
  (guard `getBounds()` in WEED prints; `WEED-STEP` prints).
- `teavm-fork/phase33/` — `build-diag33.log`,
  `desktop-compile-diag33.log`, `desktop-hymn-noocr64.log`
  (1,786 DIAG33 lines), `desktop-hymn-noocr64.musicxml`
  (44,237 B, = desktop62), `full-build64.log`,
  `run-noocr-wasm64.log`, `run-noocr-wasm64b.log` (pty re-run,
  crash, identical), `build-diag33b.log`, `full-build65.log`,
  `run-noocr-wasm65.log` (33,993 DIAG33 lines),
  `wasm-hymn-noocr65.musicxml` (45,223 B, = out63),
  `run-noocr-wasm63b.log`, `wasm-hymn-noocr63b.musicxml`
  (45,223 B, = out63, control re-run), `diag22-wasm65.txt` /
  `diag22-wasm65s.txt` (DIAG22 extract, prefix-stripped),
  `desktop-seeds.txt`, `wasm-seeds.txt`,
  `desktop-seedlens.txt`, `wasm-seedlens.txt`,
  `desktop-weed.txt`, `wasm-weed.txt`.
- Builds: `full-out64/` (ROUND 29 DIAG33 — crashes in CURVES,
  diagnostic-print bug, §28.1), `full-out65/` (ROUND 30, 3,056
  classes, 28,678 methods, builds successfully; current
  diagnostic build; `.mxl` byte-identical to out63).
  full-out63 remains the last good non-diagnostic build.
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.
- Still open, untouched in this round per the task: Lindenbaum
  HEADERS CME (§23.8); StackRhythm divergence (§25.5);
  HeadHeadRelation SIGraph symptom (§26.12, 58 lines on
  Hallelujah); BrowserOCR follow-up; photometric recovery for
  hard photos; clean build (strip DIAG prints); real-browser
  Chrome run; upstream filings (#272 draft + TPoint2D note,
  #21244 + two-part core patch, §11 Profiles.getName(), §19
  TColor, §27 hypot draft).

## 29 — DIAG34 skeleton-buffer comparison: thinning is bit-identical; the divergence is in the erasing path inside buildSkeleton (system 1 only) — 2026-11-10 (verdict (c) inconclusive, localised; next diagnostic DIAG35 named)

### 29.0 Verdict: (c) inconclusive, localised

DIAG34 (ROUND 31) dumps the skeleton buffer at three points, same
patched files both sides, print-only. The split §28 left open is now
established:

- **Thinning is BIT-IDENTICAL under TeaVM.** DIAG34A (raw skeleton,
  right after `buffer.skeletonize()` on the BINARY duplicate): desktop
  61,789 fore pixels, Wasm 61,789 — **0 differing rows out of 3,507.**
  ImageJ's `skeletonize()` (integer thinning on identical BINARY
  input, DIAG19-proven identical) produces the identical skeleton.
  The "thinning diverges" branch is dead.
- **The divergence is in the erasing path inside
  `Skeleton.buildSkeleton()`, after skeletonize.** DIAG34B (final
  `buf`, what ArcRetriever walks): desktop 41,558 fore pixels, Wasm
  45,681 — **+4,123 pixels, 324 differing rows, every single one
  Wasm-extra (0 rows where desktop has more).** All differing rows
  are in system 1 (rows 122–1126); system 2 (rows >1209) is clean.
- **Junctions and arcs follow the buffer.** DIAG34C: desktop 373
  junctions, Wasm 571. The four staff junction clusters match
  exactly on both sides (308–340, 575–607, 910–942, 1178–1209);
  every extra Wasm junction cluster lies inside a DIAG34B differing
  band (182–236, 428–439, 471–479, 511–513, 784–838, 1031–1041,
  1073–1080, 1113–1116). DIAG34D: arcs desktop 3,722 vs Wasm 4,746;
  `STAFF_ARC` **522 = 522**, `SHORT` 3,200 vs 4,224 (+1,024) —
  the extra ink produces only SHORT arcs, no extra staff arcs,
  which is exactly the §28 seed picture (extra diagonal SHORT
  spurs + 1–4 px longer staff-line arcs feeding extension merges).
- **Secondary hypothesis (§28.5) answered by code reading plus the
  A result:** `Skeleton` does NOT prune spurs — no prune step
  exists anywhere in the curve package (SHORT is just
  ArcRetriever's label for too-short arcs), and thinning is
  bit-identical anyway, so the spur pattern cannot come from
  thinning. The spurs are ink the erasing path fails to remove
  under Wasm (or removes differently).
- No contained fix identified; nothing here localises to a single
  small TeaVM operation, so (b) does not apply either. Do not file
  anything from this round.

### 29.1 DIAG34 method

ROUND 31 (`make_patches.py`): `Skeleton.java` — `diag34Dump(tag, bp)`
helper (per-row FNV + sum + zeros, DIAG22 style), called as DIAG34A
right after `buffer.skeletonize()` and DIAG34B after `buf = buffer;`
`Curves.java` — DIAG34C junction-valued pixels after
`JunctionRetriever.scanImage()`, DIAG34D arc counts after
`ArcRetriever.scanImage()` (arcs / arcsEnds / voidArcs /
totalPoints / shape histogram). Desktop: same patched files
compiled into the harness classes (see §29.2 for the harness
rebuild), `DesktopOcrExport phase23/hymn.png
phase34/desktop-hymn-noocr66.musicxml` with
`testocr.file=phase23/empty-ocr.txt` — exit 0, 7,018 DIAG34 lines,
`.mxl` 44,255 B. Wasm: full-out66 (ROUND 31, 0 problems, 3,057
classes, 28,682 methods), hymn no-OCR — exit 0, `MXL len=45223`,
`.mxl` byte-identical to out63. Both `.mxl` files reproduce their
controls, so DIAG34 is print-only on both sides (the desktop
44,255 B vs §28's 44,237 B is only the input-path string in
`<source>`/`<miscellaneous-field>` — my invocation path differed;
deep diff = 2, both the path string).

### 29.2 Harness incident — full-source recompile poisons the desktop harness (lesson, fixed)

The first desktop compile this round recompiled ALL of
`patched/src` + `phase23/src` + `entry/src` into
`phase23/classes`. That broke the desktop harness three times in
succession, each masking the next:

1. Patched `LoadStep` (ROUND 4, reads the image from
   `TeavmImageHolder`) → "No image supplied from JS".
2. Patched `SheetStub.loadGrayImage` (same ROUND 4) → stock
   `LoadStep` then threw "No image".
3. Restoring stock `LoadStep`/`SheetStub` from `audiveris.jar`
   was not enough: extracting the whole jar into
   `phase23/classes` made `WellKnowns` load from a directory
   instead of the jar, so `RUNNING_FROM_JAR=false` and `RES_URI`
   no longer pointed into the jar — `Bravura.otf` was not found,
   the platform font (Dialog) was used, and `MusicFont.<init>`
   NPE'd (`MusicFamily.valueOfName("Dialog")` is null).

Fix (the correct harness shape, now in place): `phase23/classes`
must contain ONLY compiled-from-source classes — the 78 selected
patched sources (all of `patched/src` EXCEPT the TeaVM-functional
files `WellKnowns`, `ConstantManager`, `LogUtil`, `StepMonitoring`,
`LoadStep`, `OmrExecutors`, `SheetStub`, `ConstantSet`,
`BookManager`, `AliasPatterns`, `UriUtil`, `OmrFont`, `Book`,
`OcrUtil`) + `phase23/src` + `entry/src` — with everything else
resolving from stock `audiveris.jar` on the classpath. Rebuilt
as `phase34/classes-fresh` (296 classes, no `WellKnowns.class`)
and swapped in as `phase23/classes`; the poisoned directory is
kept at `phase34/classes-backup-before-diag34`. Lesson for later
rounds: never do a full-source recompile into `phase23/classes`;
compile only the changed diagnostic files (the §28 pattern), or
rebuild the fresh directory as above. The Wasm build was never
affected (`build.sh` + canonical command are separate paths).

### 29.3 Differing-band geometry (DIAG34B)

324 differing rows in 18 ranges, all Wasm-extra. Per-band zero
deltas (Wasm − desktop): rows 179–257: +1,179; 403–524: +1,376;
781–859: +689; 1006–1126: +855; plus 3 single rows (122, 143,
164: +5 each) and 3 single rows (724, 746, 767: +3 each).
Largest single-row deltas: row 210 (+78), 226 (+61), 207 (+51),
205 (+49), 436 (+49), 504 (+47). The four bands sit just above
each staff's junction cluster — i.e. in the regions the erasing
path should have cleared (erased inters and/or distant regions).
Which shapes survive is NOT established from row totals alone
(no x-positions were dumped); that is part of DIAG35.

### 29.4 Verdict (c) — inconclusive, next diagnostic named

Ruled out: thinning (`skeletonize()` — bit-identical, 0/3,507
rows differ); `NO_STAFF`/BINARY input (proven identical, §20);
`computeModel` fit distance and weed logic (§28); spur pruning
(no such step exists); TEXTS/OCR (no-OCR runs both sides).
Not yet split: which stage inside `buildSkeleton()` diverges —
`CurvesCleaner.eraseShapes` (non-crossable heads/beams/lyrics/
text, then crossable barlines/connectors/ledgers/stems) vs
`eraseDistantRegions` (Area subtract — the §26 Greiner–Hormann
fix is the prime suspect, since the slur residual appeared
between out51 and out63, i.e. after §26) vs the
`BufferedImage` round-trip (`new ByteProcessor(img)` +
`threshold(127)`).

**Next diagnostic — DIAG35 (per-stage buffer dumps):** dump the
buffer after each stage of `buildSkeleton()` on both sides —
after non-crossable `eraseShapes`, after crossable `eraseShapes`,
after `eraseDistantRegions`, after the round-trip/threshold —
plus the x-positions of the extra pixels in one differing band,
to identify which shape type survives. If the divergence lands
in `eraseDistantRegions`, bisect the §26 Area/fill path (GH
subtract vs scanline fill) next. Do not keep bisecting beyond
DIAG35 in the next round without a fresh judgement.

### 29.5 Files

- `teavm/patched/make_patches.py` ROUND 31 (DIAG34A/B in
  `Skeleton.java`, DIAG34C/D in `Curves.java`).
- `teavm-fork/phase34/` — `build-diag34.log` (`build.sh`,
  patched/classes 328, BUILD OK), `desktop-compile-diag34.log`
  (first attempt, 17 errors — missing `entry/src` generated
  classes), `desktop-compile-diag34b.log` (78 patched sources +
  phase23/src + entry/src, exit 0), `desktop-compile-diag34c.log`
  (classes-fresh rebuild, exit 0), `desktop-hymn-noocr66.log`
  (7,018 DIAG34 lines), `desktop-hymn-noocr66.musicxml`
  (44,255 B), `run-noocr-wasm66.log`,
  `wasm-hymn-noocr66.musicxml` (45,223 B, = out63),
  `full-build66.log` (0 problems, 3,057 classes, 28,682 methods),
  `compare_diag34.py` (row comparison + band deltas +
  junction clustering), `classes-fresh/` (296 classes, the
  corrected desktop harness, now also `phase23/classes`),
  `classes-backup-before-diag34/` (poisoned full-recompile
  directory, kept for reference).
- Builds: `full-out66/` (ROUND 31 DIAG34, current diagnostic
  build; `.mxl` byte-identical to out63). full-out63 remains
  the last good non-diagnostic build.
- Edit-error note (§29 write-up): the first attempt to update the top
  verdict line matched the standalone "## Verdict: DONE at §27" line
  (which sits between §26's files list and the §27 heading) and
  overwrote its wording. It was reconstructed from §27's known outcome
  (see the restored line above §27); the top verdict line now carries
  §29, as in §28. No §26/§27 diagnostic content was affected — only
  that one verdict line.
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched.
- Still open, untouched in this round per the task: Lindenbaum
  HEADERS CME (§23.8); StackRhythm divergence (§25.5);
  HeadHeadRelation SIGraph symptom (§26.12, 58 lines on
  Hallelujah); BrowserOCR follow-up; photometric recovery for
  hard photos; clean build (strip DIAG prints); real-browser
  Chrome run; upstream filings (#272 draft + TPoint2D note,
  #21244 + two-part core patch, §11 Profiles.getName(), §19
  TColor, §27 hypot draft).

## 30. DIAG35 — head erasure is the root cause; ROUND 33 fix, hymn slur residual GONE (2026-11-10)

**Verdict: (a) contained fix applied and verified.** The hymn slur residual is fixed at its
root cause: under TeaVM, `PageCleaner.visit(HeadInter)` never erased noteheads, because it
erases by painting the Bravura glyph white and the font shim's `TextLayout.draw` is a no-op.
The fix erases each head from its glyph runs plus a 1.1× inscribed ellipse. Hymn no-OCR:
**slurs 0 = 0, 128 notes, 16 measures, 2 parts**, `.mxl` byte-identical to the §22 canonical
file, deep diff vs desktop 12 (2 filename + 9 × ±1 default-x + 1 staff-distance — the §22
no-OCR fidelity level). Hallelujah no-OCR: **275 notes, 14 measures/part, rests 58 = 58,
beams 13 = 13, slurs 22 = 22**, deep diff vs desktop 8 (was 97 in §27). Skeleton graph
converges: junctions 373 = 373 (was 373 vs 571), arcs 3,695 vs 3,696 (was 4,746 vs 3,722).
Residual: Wasm now erases ~800 px too much in the final skeleton (overshoot, §30.5) — no
downstream effect on either verified page; named next diagnostic DIAG36, not started.

### 30.1 DIAG35 localisation (full-out67, ROUND 32)

Per-stage buffer dumps inside `Skeleton.buildSkeleton()`, same patched files both sides,
prints side-effect-free (both `.mxl` reproduced byte-identically with prints on).
Hymn-satb, fore pixels, desktop vs Wasm (full numbers in
`teavm-fork/phase35/compare-diag35.txt`, `compare_diag35.py`, `compare_band.py`):

| stage | desktop | Wasm | delta |
|---|---|---|---|
| DIAG34A raw skeleton (after `skeletonize()`) | 61,789 | 61,789 | 0, 0 rows differ |
| DIAG35A after non-crossable `eraseShapes` | 51,622 | 56,623 | **+5,001**, 358 rows, all Wasm-extra, system 1 only |
| DIAG35B after crossable `eraseShapes` | 42,745 | 47,016 | +4,271, 324 rows |
| DIAG35C after `eraseDistantRegions` | 41,410 | 45,681 | +4,271 |
| DIAG34B final (after round-trip/threshold) | 41,558 | 45,681 | +4,123 |

- The divergence is **already present at DIAG35A** — the first erasing stage. It is NOT in
  `eraseDistantRegions` (removes exactly 1,335 px on both sides; delta unchanged A→C).
- **The §26 Area/fill path is exonerated for this divergence**, despite `DIAG35-REGION`
  segCount differing (desktop 17 vs Wasm 70 — the §26 disjoint-pieces decomposition stores
  more subpaths, but the fill result is identical). One staff rect differs 1 px
  (desktop `[41,814,1351,506]` vs Wasm `[41,815,1351,505]`, 4th staff, §18 jitter family)
  — did not affect the fill outcome. The §26 fix is therefore NOT the cause of the slur
  residual appearing between out51 and out63; the residual was latent in the head-erasure
  path and only became visible once the §26 beam fix let the pipeline reach CURVES cleanly.
- Erased counts identical both sides at every stage: non-crossable sys1 80 NOTEHEAD_BLACK,
  sys2 48; crossable sys1 LEDGER 20 / STEM 80 / THIN_BARLINE 12 / THIN_CONNECTOR 1 (total
  113), sys2 total 69. The shapes are *found* identically — desktop removes 10,167 px in
  the non-crossable stage, Wasm only 5,166. The crossable stage removes 730 more under Wasm
  (9,607 vs 8,877) — it incidentally covers some of the extra Wasm ink where stems/ledgers
  overlap it.
- Secondary divergence, opposite direction, small: desktop gains +148 fore px in the
  round-trip (C 41,410 → B 41,558, system 1) — grey pixels in (0,127) thresholded to black
  on desktop; Wasm produces pure 0/255. Reduces the gap from 4,271 to 4,123.
- Band x-runs (rows 179–257, `compare_band.py`): desktop has 0 fore px in rows 179–185;
  Wasm has small oval clusters at x≈797–807, 908–917, 2344–2354 etc., plus scattered singles
  at rows 187–190. Total Wasm-only fore in band: 1,201 px (C) / 1,179 (D) over ~835 runs,
  spread across the whole page width (x-buckets 500–2400) — **notehead skeletons surviving**,
  not one shape in one place.

### 30.2 Root cause (code reading, `PageCleaner.java`)

`visit(HeadInter)` erases a head by painting its Bravura glyph white:
`paintSymbol` → `ShapeSymbol.paint` → `OmrFont.paint(g, params.layout, …)` →
`TextLayout.draw(g, x, y)`. The TeaVM font shim's `TextLayout.draw` is a no-op
(`teavm/shims/src/java/awt/font/TextLayout.java:62`, comment: "TextLayout.draw stays a
no-op: painting is not needed in the pipeline"), and shim `BufferedImageGraphics.drawGlyphVector`
/ `drawString` are also no-ops. So under TeaVM the head is never erased; desktop paints real
Bravura glyphs at enlarged size (1.1×). Same stub-font disease as §14/§18, now in the
erasing path. It also explains §28's 1–4 px longer staff-line arcs: desktop's oval paint
breaks the staff line at each head; Wasm leaves it continuous. **Not a TeaVM defect** — a
shim gap (painting is genuinely absent from the shim) combined with Audiveris assuming a
real font renderer. No minimal repro to file, nothing to file against TeaVM for this.

### 30.3 ROUND 33 fix (in `teavm/patched/make_patches.py` only)

`PageCleaner.java` added as R2[38] (copied verbatim). ROUND 33 patches `visit(HeadInter)`:
keep the existing `paintSymbol` call, then (a) `processGlyph(glyph)` — glyph runs (exact
head ink, including slanted tips) — and (b) fill a white ellipse inscribed in the glyph
bounds (or head bounds if glyph is null) enlarged 1.1×
(`constants.enlargementRatio.getValue()`), via `g.fill(new Ellipse2D.Double(…))`, which
also breaks the staff-line segment through the head the way the desktop oval paint does.
Rationale: on desktop both additions whiten pixels `paintSymbol` already whitened
(desktop-neutral in effect — verified §30.4, with a −335 px buffer caveat below); shim
`fill(Shape)` handles Ellipse2D via the §26.7 per-pixel fallback (verified 0 diffs in
filltest). Deliberately scoped to `PageCleaner.visit(HeadInter)` only — NOT to the shim's
`TextLayout.draw`, which is also reached from `TemplateFactory` (lines 267–343) and
`StemBuilder:1268` / `HeadLinker:1951` paintSymbol calls; changing draw() globally would
change template building / head matching.

### 30.4 Verification (full-out68: 0 problems, 3,058 classes, 28,688 methods)

- **Desktop-neutrality:** desktop harness with the patched PageCleaner (only that file
  compiled into `phase23/classes`, per §29.2) — hymn `.mxl` **byte-identical** to the
  out67 control, 44,237 B (`phase35/desktop-hymn-noocr68.musicxml`). Buffer effect, for
  the record: final DIAG34B 41,558 → 41,223 (−335 px, −0.8%); A −253, B −232, C −232.
  The ellipse covers slightly more than `paintSymbol` alone — same notes, measures, slurs,
  beams on both pages, so semantically neutral; the −335 px is a real (small) desktop-side
  change, not zero.
- **Wasm hymn no-OCR** (`phase35/wasm-hymn-noocr68.musicxml`, 44,105 B, main() 81,650 ms):
  **byte-identical to the §22 canonical `wasm-hymn.musicxml`**; 128 notes, 0 slurs,
  16 measures, 2 parts. Re-run reproduces byte-identically
  (`phase35/wasm-hymn-noocr68b.musicxml`). Deep diff vs desktop68: **12** — 2 source
  filename (expected) + 9 × ±1 `default-x` + 1 staff-distance 101→102 (known §22
  sub-pixel residuals). Zero slur/duration/pitch/syllabic diffs.
- **Wasm Hallelujah no-OCR** (`phase35/wasm-hallelujah-noocr68.musicxml`, 105,118 B,
  main() 193,709 ms): 275 notes, 14 measures/part, rests 58 = 58, beams 13 = 13,
  slurs 22 = 22, parts 4 — all counts identical to desktop68 (105,442 B). Deep diff vs
  desktop68: **8** (file `phase35/compare-deep-hallelujah68.txt`) — 2 filename + 2
  staff-distance ±1 + 1 slur bezier ±1–2 + 1 `default-x` ±1 + **2 missing `<tie>` elements
  on Wasm in P4 m8** (the known §25.5 StackRhythm measures, pre-existing, not the slur
  fix). Was 97 deep diffs in §27 (Wasm63 vs desktop62); the drop is mostly the two sides
  now erasing heads the same way, so skeleton-derived positions converge. For reference,
  desktop68 vs the pre-fix desktop control is 87 deep diffs, all ±1 positions, counts
  identical — the patch shifts desktop positions ~1 tenth in places, semantically neutral.
- **Skeleton graph convergence (hymn, DIAG34C/D):** junctions **373 = 373** (was 373 vs
  571); arcs **3,695 vs 3,696** (was 4,746 vs 3,722); STAFF_ARC 508 vs 522, SHORT 3,187 vs
  3,174; totalPoints 60,905 vs 62,214; voidArcs 133 = 133.
- **§26 Area/fill exonerated** (§30.1) — no change to the §26 fix, no regression in beams
  (Hallelujah beams 13 = 13, slurs 22 = 22).

### 30.5 Residual: Wasm overshoot (~800 px), next diagnostic DIAG36

Stage totals after the fix (hymn): A desktop 51,369 vs Wasm 50,438 (**−931**), B 42,513 vs
41,751 (−762), C 41,178 vs 40,416 (−762), final 41,223 vs 40,416 (**−807**). The fix
removed 6,185 px under Wasm at stage A vs 253 on desktop: Wasm now erases ~7 px/head too
much. Prime suspects, untested: (a) shim `Ellipse2D.contains` edge rule vs JDK's (the
§26.7 fallback uses `s.contains(xx+0.5, yy+0.5)` — pixel-centre test, should match, but
the shim Ellipse2D contains formula was never compared against JDK on boundary pixels);
(b) glyph bounds under Wasm differing ~1 px from desktop for some heads. Effect on the
two verified pages: none measurable (counts identical, deep diffs 12 / 8, junctions exact,
arcs within 1; the −14 STAFF_ARC / −1,309 totalPoints are the visible trace). **DIAG36
(named, not started):** per-head glyph-bounds comparison + per-ellipse pixel-count
comparison (desktop vs Wasm) on the hymn, to say which of (a)/(b) it is; if (a), fix the
shim contains rule; if (b), localise the bounds difference. Do not start DIAG36 in this
round — the slur residual is fixed and the overshoot has no downstream effect on the
pages verified.

### 30.6 What remains open (unchanged from §29, minus the slur residual)

Lindenbaum HEADERS CME (§23.8, now deterministic on two pages — Lindenbaum + Snow p1);
StackRhythm divergence (§25.5 — Hallelujah P4 m8 ties, still present in the §30 deep
diff); HeadHeadRelation SIGraph symptom (§26.12); template catalog coverage cliff
({80,92,108} ± 8 — Snow p5 point size 140 → HEADS 0); Wasm head-erasure overshoot
(§30.5, DIAG36 named); BrowserOCR follow-up; photometric recovery for hard photos; clean
build (strip DIAG prints — DIAG35/DIAG34 prints still in, deliberately, for
re-verifiability); real-browser Chrome run; upstream filings (#272 draft + TPoint2D note,
#21244 + two-part core patch, §11 Profiles.getName(), §19 TColor, §27 hypot draft —
deferred until our own work is done, per Jonathan 2026-11-09). CheerpJ 5 remains the only
working option for the shipped app until the browser run lands.

### 30.7 Artefacts

- Build: `teavm-fork/full-out68/` (0 problems, 3,058 classes, 28,688 methods).
- Logs / `.mxl`: `teavm-fork/phase35/` — `build-fix.log`, `full-build68.log`,
  `desktop-compile-fix.log`, `desktop-hymn-noocr68.log` + `.musicxml` (44,237 B),
  `run-noocr-wasm68-hymn.log` + `wasm-hymn-noocr68.musicxml` (44,105 B, byte-identical
  to §22 canonical) + `wasm-hymn-noocr68b.musicxml` (reproducibility re-run),
  `desktop-hallelujah-noocr68.log` + `.musicxml` (105,442 B),
  `run-noocr-wasm68.log` (Hallelujah Wasm run — note: this file name was reused for the
  Hallelujah run after the hymn run; the hymn Wasm log is `run-noocr-wasm68-hymn.log`)
  + `wasm-hallelujah-noocr68.musicxml` (105,118 B), `compare-fix68.txt`
  (stage totals — the `compare_diag35_fix.py` comparator run mixed the hymn desktop log
  with the Hallelujah Wasm log after the file-name reuse and is not reliable; the stage
  totals in §30.4/§30.5 are from direct TOTAL-line reads, recorded in `compare-fix68.txt`),
  `compare-deep-hallelujah68.txt`, `compare_diag35.py`, `compare_band.py`.
- Patch: ROUND 33 in `teavm/patched/make_patches.py` (PageCleaner R2[38] + head-erasure
  fix); `teavm/patched/src/org/audiveris/omr/sheet/PageCleaner.java` (patched copy).

## 31. DIAG36 — head-erasure overshoot: shim `Ellipse2D` geometry defect; contained fix, overshoot reduced 4–6× and flipped sign (2026-11-10)

**Verdict: (a) contained fix applied and verified.** DIAG36 proved the §30 overshoot was a shim
geometry defect, not a TeaVM defect and not a glyph-bounds difference: the shim `Ellipse2D`
had no `contains` override, so it inherited the bounding-rectangle test, and `getBounds()`
truncated instead of flooring/ceiling — the ROUND 33 ellipse fill erased the whole rectangle
(including ~192 corner pixels per head) and missed the right/bottom strips. Fix (shim-side
only, JDK-verbatim): `Ellipse2D.contains` / `contains(rect)` / `intersects` plus floor/ceil
`getBounds()` in `RectangularShape` and `Rectangle2D`. Full-out71 (0 problems, 3,058 classes,
28,697 methods): hymn no-OCR `.mxl` byte-identical to out68 and to the §22 canonical file
(128 notes, slurs 0 = 0, deep diff 12); Hallelujah no-OCR byte-identical to out68 (275 notes /
14 measures / rests 58 = 58 / beams 13 = 13 / slurs 22 = 22, deep diff 8). Stage-A overshoot
−931 → +453 (hymn), −1,277 → +274 (Hallelujah); final −807 → +150 (hymn), −843 → +230
(Hallelujah). Residual: Wasm now leaves ~150–230 fore px EXTRA (paint shortfall — desktop's
`paintSymbol` whitens ~800 px the glyph runs don't cover, of which the ellipse recovers ~355);
uniform ~+3.7 px/head, no downstream effect on either verified page; named next diagnostic
DIAG37 (paint-footprint dump).

### 31.1 DIAG36 comparison (full-out70 vs desktop, live counts)

Per-head accounting, hymn, 128 heads, same patched `PageCleaner` both sides (ROUND 34/34b,
live-image counting — see §31 summary in the handoff; full totals in
`phase36/compare-diag36-71.txt` for out71, `phase36/compare_diag36_live.py` for out70):

| total (128 heads) | desktop | Wasm out70 | Δ (W−D) |
|---|---|---|---|
| foreBefore (ellipse rect, before paint) | 6,976 | 6,976 | 0 |
| foreAfterPaint | 1,987 | 6,976 | +4,989 (paint-erased 4,989 vs 0 — stub-font draw no-op) |
| foreAfterGlyph | 1,987 | 2,779 | +792 (glyph-erased 0 vs 4,197) |
| cornerFore at fill time | 1,750 | 2,159 | +409 |
| foreAfterEllipse | 1,722 | 791 | −931 (ellipse-erased 265 vs 1,988) |

Three candidate causes, judged:
- (a) **Ellipse edge rule — PROVEN.** Standalone JDK 25 tests (`/tmp/ellipsetest/`, recreated
  after `/tmp` was wiped; saved in `phase36/shim-ellipse-diff/`): for a typical head ellipse
  (31.9×25.3) the rectangle holds 832 pixel centres vs the true ellipse 640 — 192 corner
  pixels a rectangle fill erases that a true ellipse fill would not. Differential test
  (§31.3) measured 132 point mismatches on the head frame (781.65,173.9,29.7,24.2) alone.
  The 791 px left on Wasm after the old fill are exactly the corner pixels in the
  right/bottom strips the truncated `getBounds()` window misses.
- (b) **Glyph bounds differ ~1 px — RULED OUT as the cause.** Bounds differ on 24/128 heads,
  all by exactly (−1 or 0 in x, +1 in y) — the §18 jitter family; total corner delta +4.
  Unchanged by the fix (same 24/128 in out71).
- (c) **processGlyph ink differs — RULED OUT.** Glyph-erased 4,197 (Wasm) vs paint-erased
  4,989 (desktop) is a paint-*footprint* difference, not an ink difference: the desktop
  paint whitens ~800 px beyond the glyph runs (see §31.5). The runs themselves are the
  exact head ink on both sides (foreBefore identical, 6,976 = 6,976).

Fill path (confirmed by code reading, `BufferedImageGraphics.fill`): `fill(Shape)` takes the
fill window from `s.getBounds()` and, because shim `Ellipse2D.getPathIterator` returns null,
falls back to the per-pixel loop `fillPixels`, which tests `s.contains(xx + 0.5, yy + 0.5)`
per pixel. Both defects sit directly on that path: the window (truncated `getBounds`) and
the test (bounding-rectangle `contains`).

### 31.2 Ground truth: OpenJDK 25 source, and the §24 correction

Ground truth is the OpenJDK 25 source shipped with this VM's JDK
(`jdk-25.0.5+8/lib/src.zip`, `java.desktop/java/awt/geom/{Ellipse2D,RectangularShape,
Rectangle2D}.java`), read directly — not reconstructed from memory:
- `Ellipse2D.contains(double,double)`: normalise to centre (0,0), radius 0.5;
  `normx² + normy² < 0.25`, with `ellw <= 0` / `ellh <= 0` guards returning false.
- `Ellipse2D.contains(x,y,w,h)`: **four-corner** test (no w≤0/h≤0 guard — a zero-size rect at
  an interior point IS contained).
- `Ellipse2D.intersects(x,y,w,h)`: normalised nearest-point test, `nearx² + neary² < 0.25`,
  false for w≤0/h≤0. The probe anomaly that looked like a contradiction — rect
  [−2,4,2,2] on ellipse (0,0,10,10) intersects, [−1,4,1,2] does not, although both have
  x+w = 0 — is reproduced *exactly* by the JDK algorithm: `normx1` is −0.49999999999999994
  (one ulp below −0.5) for the first and exactly −0.5 for the second. Copying the JDK code
  verbatim preserves that floating-point behaviour; re-deriving it would not.
- `RectangularShape.getBounds()`: floor origin / ceil far edge, empty `Rectangle()` for
  negative width/height. (`Rectangle2D` inherits it in the JDK; the shim's `Rectangle2D`
  is standalone, so it needs its own copy.)
- `RectangularShape` defines **no** `contains(x,y,w,h)` in the JDK — each subclass defines
  its own. The shim's two-corner version was a shim invention.

**§24 correction:** the comment left in `Rectangle2D.java` in §24 claimed "RectangularShape's
two-corner form is left as-is: it is JDK-faithful for non-rectangular shapes such as
Ellipse2D". That is WRONG, and Probe2 refutes it: rect [6,1,3,3] on ellipse (0,0,10,10) is
**false** on JDK 25 (both diagonal corners inside, one off-diagonal corner outside) while
the two-corner test says true. JDK `Ellipse2D` overrides with the four-corner test. The
comment is corrected in `Rectangle2D.java` as part of this fix. (The §24 note's other claim
— a zero-size rect at an interior point IS contained by an ellipse — remains true: the
four-corner test has no w≤0/h≤0 guard, unlike the rectangle version.)

### 31.3 The fix (shim-side only, three files)

Files (all hand-written shims; none is generator-produced — `gen_awt2.py` generates only
`RoundRectangle2D`, so hand edits here survive `build.sh` step 0):
- `teavm/shims/src/java/awt/geom/Ellipse2D.java`: added `contains(double,double)`,
  `contains(double,double,double,double)`, `intersects(double,double,double,double)` —
  verbatim OpenJDK 25 code, comments included.
- `teavm/shims/src/java/awt/geom/RectangularShape.java`: `getBounds()` floor/ceil, verbatim
  OpenJDK 25; `contains(x,y,w,h)` changed two-corner → four-corner (for a rectangle the
  two forms coincide, so this changes nothing for rectangular shapes; `Ellipse2D` carries
  its own verbatim override, so the base change affects only `RoundRectangle2D`, making
  it strictly closer to JDK).
- `teavm/shims/src/java/awt/geom/Rectangle2D.java`: `getBounds()` floor/ceil, verbatim
  OpenJDK 25 (same truncation defect as `RectangularShape`); §24 comment corrected (above).

Deliberately NOT touched: `RoundRectangle2D.java` (generator-produced by `gen_awt2.py` —
a hand edit would be overwritten by `build.sh` step 0) and its `contains(double,double)`,
which remains the bounding-box approximation in the shim (pre-existing gap, not in this
causal chain; it inherits the four-corner rect-contains now). `RectangularShape.contains
(double,double)` (bounding-box default) is likewise left as-is — in the JDK it is abstract;
after this fix its only consumer is `RoundRectangle2D`.

Desktop-neutrality holds by construction: the shims compile only into `shims.jar` for the
TeaVM build; the desktop harness uses real JDK classes. No patched Audiveris source changed
in this round (`make_patches.py` untouched; DIAG36 prints still in, deliberately).

Differential test (`phase36/shim-ellipse-diff/ShimEllipseDiff.java`, with `Probe2.java` /
`Probe3.java`): same binary run under stock JDK 25 and under the shim via `--patch-module`.
4 frames × (1,254 + 289 + 176 + 64 point centres on a ±3 grid, 13 named rects, 784 grid
rects over positions × sizes) + zero/negative-width frames. **Before the fix:** 132 point
mismatches on the head frame, `getBounds()` 29×24 vs JDK 31×26, corner-rect `contains` and
zero-size/corner `intersects` mismatches. **After the fix: `diff` between the JDK run and
the shim run is EMPTY — 0 mismatches on all ~2,600 cases**, including the [6,1,3,3]
four-corner case, the [−2,4,2,2] intersects FP edge, and zero/negative-size frames.
Two `--patch-module` pitfalls recorded (both bit the first attempts): `~` after `=` is NOT
expanded by bash (`--patch-module java.desktop=~/...` silently patches nothing — classes
still load from `jrt:/java.desktop`, verified with `-Xlog:class+load`); and the full
`shims/classes` dir breaks module resolution (it contains `java.awt.datatransfer`, owned by
`java.datatransfer`) — use a minimal dir with only the geom classes + `Rectangle`/`Shape`.

### 31.4 Verification (full-out71: 0 problems, 3,058 classes, 28,697 methods)

`build.sh` exit 0, Spike exit 0, `classes.wasm` 13,629,867 bytes. DIAG36 prints still in.

Hymn no-OCR (`phase36/run-noocr-wasm71.log`, main() 54,314 ms): exit 0, `.mxl`
44,105 B — **byte-identical to out68 and to the §22 canonical file**; HEADS 306, CHECK
538011 (identical to out68/desktop); deep diff vs desktop 12 (unchanged).
Hallelujah no-OCR (`phase36/run-noocr-hallelujah71.log`, main() 125,391 ms): exit 0,
`.mxl` 105,118 B — **byte-identical to out68**; 275 notes, 4 parts × 14 measures, rests
58 = 58, beams 13 = 13, slurs 22 = 22; deep diff vs desktop 8 (unchanged — same 2 filename
+ position roundings + the known §25.5 StackRhythm P4 m8 ties).

Stage totals (DIAG35 `zeros`, fore px in the skeleton buffer; desktop baselines from
`phase36/desktop-hymn-noocr69b.log` and `phase35/desktop-hallelujah-noocr68.log`):

| stage | hymn desktop | hymn out70 | hymn out71 | hall desktop | hall out68 | hall out71 |
|---|---|---|---|---|---|---|
| A (non-crossable) | 51,369 | 50,438 (−931) | 51,822 (**+453**) | 169,898 | 168,621 (−1,277) | 170,172 (**+274**) |
| B (crossable) | 42,513 | 41,751 (−762) | 42,708 (**+195**) | 155,361 | 154,608 (−753) | 155,681 (**+320**) |
| C (distant regions) | 41,178 | 40,416 (−762) | 41,373 (**+195**) | 148,055 | 147,302 (−753) | 148,375 (**+320**) |
| final (DIAG34B) | 41,223 | 40,416 (−807) | 41,373 (**+150**) | 148,145 | 147,302 (−843) | 148,375 (**+230**) |

DIAG36 out71 vs desktop (`phase36/compare-diag36-71.txt`, `compare_diag36_71.py`):
foreBefore 6,976 vs 6,991 (+15); foreAfterPaint 1,987 vs 6,991; foreAfterGlyph 1,987 vs
2,810 (+823); cornerFore 1,750 vs 2,190 (+440); foreAfterEllipse 1,722 vs 2,190
(**+468**); paint-erased 4,989 vs 0; glyph-erased 0 vs 4,181; ellipse-erased 265 vs 620
(+355). Per-head final delta +1..+7 px on all 128 heads — distribution [(3,55), (4,45),
(5,13), (2,8), (7,5), (6,1), (1,1)] — uniform, no outliers, not shape-concentrated.
Glyph bounds differ on the same 24/128 heads as before, same deltas.

Two second-order notes: (1) foreBefore is +15 on Wasm now (was 0 in out70) and
glyph-erased 4,181 (was 4,197) — both are the order-dependence of per-head counting:
heads are visited in order, and earlier heads' fills now erase fewer corner pixels, so
later heads' rects start with slightly more fore. (2) The per-head net +468 vs the
stage-A +453 differ by 15 px — the per-head rects overlap, so shared pixels are
double-counted in the per-head sums; the stage totals are the authoritative figures.

Wrong-input incident (not a regression): the first Hallelujah out71 attempt used
`phase23/hallelujah-clean.gray` (2500×3529) and failed fast at BINARY (`Sheet ignored`,
interline 190) — that file is not the no-OCR comparison input. The correct input is
`phase23/hallelujah-satb.gray` (2480×3509, 8,702,320 bytes), same as §30; the hymn run
had already passed on the same build. No `.mxl` was produced by the failed run and its
log is kept (`phase36/run-noocr-hallelujah71.log` was overwritten by the good run; the
failed attempt's tail is recorded here, not as a file).

### 31.5 Residual: paint shortfall (+150 hymn / +230 Hallelujah final), next diagnostic DIAG37

The geometry defect is fixed; what remains is the paint shortfall, and it is a *different*
defect with the opposite sign. Decomposition on the hymn (per-head totals): desktop's
`paintSymbol` whitens 4,989 fore px; Wasm's glyph runs cover 4,181 of them. The 823 px
gap at the glyph step is ink the paint whitens that is neither glyph ink nor inside the
1.1× ellipse — the Bravura glyph image's footprint (anti-aliased fringe and/or the paint's
oval extent) vs the runs' exact ink. The ellipse fill recovers 355 of the gap (Wasm
ellipse-erased 620 vs desktop 265 — Wasm's ellipse finds more inside-ellipse fore because
more is left); 468 remain per-head, and later stages clean most of it (stage A +453 →
B +195 → C +195 → final +150). Hallelujah shows the same shape (A +274 → final +230).
The residual is uniform (~+3.7 px/head), and it has **no downstream effect on either
verified page** — both `.mxl` files are byte-identical to their pre-fix builds, so the
extra ink is staff-line/corner fragments the later stages already handle (the §28 slur
mechanism needed *head* skeletons, which are gone).

This is the stub-font gap again (`TextLayout.draw` no-op, §30) — closing it needs a model
of the paint footprint or real glyph rendering, not more geometry. Named next diagnostic:
**DIAG37** — per-head paint-footprint dump on desktop: which fore pixels does
`paintSymbol` whiten that `processGlyph` doesn't, and where do they lie relative to the
glyph bounds and the 1.1× ellipse (inside/outside, fringe vs staff-line)? That decides
whether the footprint is modellable (e.g. ellipse enlargement ratio) or needs real glyph
rendering.

### 31.6 What remains open (unchanged, minus the overshoot)

Lindenbaum HEADERS CME (§23.8, now deterministic on two pages); StackRhythm divergence
(§25.5 — Hallelujah P4 m8 ties still missing); HeadHeadRelation SIGraph symptom (§26.12);
template catalog coverage cliff ({80,92,108} ± 8 — Snow p5 point size 140 → HEADS 0);
BrowserOCR follow-up; photometric recovery for hard photos; clean build (strip DIAG prints
— DIAG36/DIAG35/DIAG34 prints still in, deliberately, for re-verifiability); real-browser
Chrome run; upstream filings (#272 draft + TPoint2D note, #21244 + two-part core patch, §11
Profiles.getName(), §19 TColor, §27 hypot draft — deferred until our own work is done, per
Jonathan 2026-11-09). CheerpJ 5 remains the only working option for the shipped app until
the browser run lands. No new upstream filing from this round: the defects fixed were shim
defects, not TeaVM defects (the §24 comment correction is a shim-comment fix, not a TeaVM
issue).

### 31.7 Artefacts

- Build: `teavm-fork/full-out71/` (0 problems, 3,058 classes, 28,697 methods;
  `classes.wasm` 13,629,867 bytes).
- Logs / `.mxl`: `teavm-fork/phase36/` — `build71.log`, `full-build71.log`,
  `run-noocr-wasm71.log` + `wasm-hymn-noocr71.musicxml` (44,105 B, byte-identical to out68
  and §22 canonical), `run-noocr-hallelujah71.log` + `wasm-hallelujah-noocr71.musicxml`
  (105,118 B, byte-identical to out68), `compare-diag36-71.txt`, `compare_diag36_71.py`.
- Fix record: `teavm-fork/phase36/shim-fix/` (the three fixed shim sources as built);
  `teavm-fork/phase36/shim-ellipse-diff/` (`ShimEllipseDiff.java`, `Probe2.java`,
  `Probe3.java`, `diff-jdk-after-fix.txt`, `diff-shim-after-fix.txt` — diff empty).
- Fix files: `teavm/shims/src/java/awt/geom/{Ellipse2D,RectangularShape,Rectangle2D}.java`.
  Ground truth: OpenJDK 25 `src.zip` in `repo/.work/jdk/jdk-25.0.5+8/lib/src.zip`.

## 32. DIAG37 paint-footprint dump — ellipse enlargement 1.1x -> 1.32x (2026-11-10)

**Verdict: (a) contained fix applied and verified.** The §31 residual — Wasm leaving
~150–230 fore px extra because desktop's `paintSymbol` whitens ~800 px the glyph runs
don't cover — is a modellable footprint, not a TeaVM defect: the desktop paint is the
Bravura glyph at 1.1x plus an anti-aliasing fringe and slanted notehead tips that stick
out past the axis-aligned 1.1x ellipse, reaching normalised radius 1.20. Enlarging the
ROUND 33 ellipse by a further 1.2x (1.32x glyph bounds) covers 99.6% of the paint
footprint. Stage-A residual +453/+274 -> +37/−94, stage-C +195/+320 -> +97/+168;
both .mxl files byte-identical to their 1.1x controls on both sides, Wasm-vs-desktop
deep diffs unchanged (hymn 12, Hallelujah 8). The residual is now at the level of the
other second-order differences (fill rasterisation ~118 px, glyph-bound windows ±104 px)
and no further diagnostic is warranted for this item.

### 32.0 Source of the 1.1x factor (located)

The earlier grep had failed on a wrong path. The stock source is
`repo/.work/audiveris/app/src/main/java/org/audiveris/omr/sheet/PageCleaner.java`:
`Constants.enlargementRatio = 1.1` — "Size augmentation to use with eraser music font"
— applied in `enlarged()` to the head point size (`enlargedHeadSize`), and the head is
painted with the Bravura glyph at that enlarged size (`visit(HeadInter)`, line ~438:
`size = head.getShape().isSmallHead() ? smallHeadSize : enlargedHeadSize`). So the
paint footprint is a real font glyph at 1.1x, not the detected glyph bounds — the
ROUND 33 ellipse (1.1x glyph bounds) matches its scale but not its anti-aliasing fringe
nor the slanted notehead tips.

### 32.1 DIAG37 (ROUND 35)

Same patched `PageCleaner` both sides, print-only, verified `.mxl` reproduces with
prints on. Per head, snapshots of the widened ellipse-rect (ellipse rect + 8 px) fore
set before paint (S0), after paint (S1), after `processGlyph` (S2), after ellipse fill
(S3); every paint-whitened pixel (S0\S1) classified by inside-1.1x-ellipse, inside
glyph bounds, staff-line row (S0 fore on both sides of glyph bounds in that row),
8-adjacent to a glyph-run pixel (fringe, via `RunTable.getRunAt`), in the glyph runs
at all; plus DIAG37P pixel lists (cap raised from 12 to 1,000 heads for the full
distribution — see §32.2). Helpers `diag37Snap`, `diag37InGlyphRun`, `diag37InEllipse`
in `PageCleaner`. One parser bug fixed in the comparator: DIAG37P tokens are
`x,yFLAGS` with no comma before the flags — regex `^(-?\d+),(-?\d+)([ESF-]{3})$`.

Desktop run (hymn, 128 heads): PageCleaner compiled alone into `phase23/classes`
(per §29.2), `DesktopOcrExport phase23/hymn.png phase37/desktop-hymn-noocr72.musicxml`
with `testocr.file=phase23/empty-ocr.txt` — exit 0, 128 DIAG37 + 12 DIAG37P lines,
`.mxl` 44,237 B byte-identical to desktop69b — DIAG37 is print-only on desktop.
Wasm build full-out72: `build.sh` OK, TeaVM 0 problems, 3,058 classes, 28,700 methods,
`classes.wasm` 13,636,460 bytes. Wasm hymn no-OCR run: exit 0, main() 35,858 ms,
128 DIAG37 + 128 DIAG36 lines, MXL 44,105 B byte-identical to out71.
Note: the canonical build command's bare `java` was not on PATH in this shell — the
full JDK path `~/workspace/score-reader-spikes/repo/.work/jdk/jdk-25.0.5+8/bin/java`
was used throughout §32.

### 32.2 DIAG37 comparison (1.1x ellipse, hymn, 128 heads)

Comparator `teavm-fork/phase37/compare_diag37.py`, results in
`compare-diag37.txt` (12-head sample) and `compare-diag37-full.txt` (all 833 px).

Desktop paint totals: paintN=4,989 (Wasm 0 — paint is a no-op under TeaVM, as
expected); paintInEll=4,470; paintInBnd=4,852; paintOutBnd=137; paintStaff=654;
paintFringe=4,709 (94.4% of paint pixels are 8-adjacent to a glyph run);
paintGlyph=4,156 (83.3%); **paintNotGlyph=833 (16.7%)**; paintNotGlyphInEll=399
(47.9% of the 833); paintNotGlyphStaff=449 (53.9%); paintBorder=0 (snapshot window
big enough). Glyph: glyphN desktop 57,894 vs Wasm 57,998 (+104 — windows differ
slightly on the 24 heads whose glyph bounds differ by (−1,0)/(0,+1), §31);
glyphStep desktop 0 vs Wasm 4,181; ellipse-erased desktop 265 vs Wasm 620 (+355,
matches §31.5); ellipse outside-ellipse desktop 118 vs Wasm 0 (real JDK fill
rasterisation erases ~1 px of boundary pixels the strict `contains()` test does
not — second-order observation, contributes ~118 px to the residual floor).
Leftover foreAfterEllipse in the widened window: desktop 6,229 vs Wasm 6,647,
delta **+418** (vs +468 in the ellipse rect, §31 — same residual, wider window).

Full distribution of the 833 paint-not-glyph pixels (all heads, not the 12-head
sample): non-ellipse pixels (434) normalised radius min 1.04, median 1.14, p90 1.19,
max 1.20 — **all 434 within r < 1.20** (131 within r < 1.10, 431 within r < 1.20);
max distance outside glyph bounds dx=1, dy=2; per-head paintNotGlyph uniform
(7 px on 70 heads, 6 on 33, 5 on 16, 8 on 6, 4 on 2, 9 on 1 — no outliers); all
434 non-ellipse pixels are NOTEHEAD_BLACK (no shape concentration). DIAG37P flag
combos (full sample): ESF 221, --F 208, -S- 103, ES- 89, E-F 88, --- 87, -SF 36,
E-- 1; paint-not-glyph outside ellipse AND not staff-line: 295 of 833.

Arithmetic of the residual: desktop erased 5,254 px in-window (paintGlyph 4,156 +
paintNotGlyph 833 + ellipse 265); Wasm erased 4,801 (glyphStep 4,181 + ellipse 620);
shortfall 453 = 833 − 355 (ellipse extra recovery) − 25 (extra glyph erasure on
Wasm). Per-head rects overlap, so per-head sums double-count shared pixels; stage
totals are authoritative.

Interpretation: the paint footprint is essentially the glyph shape + ~1 px fringe
(94.4% fringe-adjacent, ≤1 px outside glyph bounds in x, ≤2 px in y), and every
sampled paint-not-glyph pixel outside the ellipse lies within 1.2x of the ellipse
(median 1.14). The footprint IS modellable as a slightly larger ellipse — the
1.2x factor is evidence-based (covers 830/833 = 99.6%), not fitted.

### 32.3 Fix (ROUND 36): ellipse enlargement 1.1x -> 1.32x

One-number change in the patched `PageCleaner.visit(HeadInter)` only
(`teavm/patched/make_patches.py`, ROUND 36): the ellipse w/h computation goes from
`bounds * enlargementRatio` to `bounds * enlargementRatio * 1.2`. The `paintSymbol`
call and the glyph runs are unchanged. A control run at 1.1x was produced by
temporarily reverting the factor (see §32.5 for the patch-hygiene note).

DIAG37 with the 1.32x ellipse (hymn, `compare-diag37-73.txt`):
paintNotGlyphInEll 818/819 (**99.9%**, was 399/833); Wasm ellipse-erased 1,994
(was 620); desktop ellipse-erased 1,230 (was 265); leftover foreAfterEllipse
delta **+69** (was +418). The single remaining non-ellipse paint pixel sits at
r = 1.00 (on the ellipse edge).

### 32.4 Verification — stage totals and .mxl (full-out73)

Build full-out73: 0 problems, 3,058 classes, 28,700 methods (same class count as
out72; `classes.wasm` not re-measured, same shape as out72's 13,636,460 bytes).
Runs: Wasm hymn no-OCR exit 0, main() 46,159 ms, MXL 44,105 B; Wasm Hallelujah
no-OCR exit 0, main() 166,269 ms, MXL 105,118 B; desktop hymn exit 0, 44,237 B;
desktop Hallelujah exit 0, 105,442 B. (One false start: the first Wasm hymn run
used `phase23/hymn-clean.gray` (2500x3527, luma conversion) and died at BINARY
with interline 267 — wrong input file, not a build failure. The correct input is
`teavm/hymn-satb.gray` (2480x3507, 8,697,360 bytes), as in out71/out72.)

Stage totals (DIAG35 fore px; A = after non-crossable eraseShapes, B = after
crossable eraseShapes, C = after eraseDistantRegions):

| page       | stage | desktop 1.1x | Wasm 1.1x | Δ 1.1x | desktop 1.32x | Wasm 1.32x | Δ 1.32x |
|------------|-------|-------------|-----------|--------|---------------|------------|---------|
| hymn       | A     | 51,369      | 51,822    | +453   | 50,457        | 50,494     | **+37** |
| hymn       | B     | 42,513      | 42,708    | +195   | 41,716        | 41,813     | **+97** |
| hymn       | C     | 41,178      | 41,373    | +195   | 40,381        | 40,478     | **+97** |
| Hallelujah | A     | 169,898     | 170,172   | +274   | 168,229       | 168,135    | **−94** |
| Hallelujah | B     | 155,361     | 155,681   | +320   | 153,963       | 154,131    | **+168**|
| Hallelujah | C     | 148,055     | 148,375   | +320   | 146,657       | 146,825    | **+168**|

The residual shrank 4–6x at stage A and ~2x at stages B/C, and its sign now flips
between stages/pages — it is at the level of the other second-order differences
(fill rasterisation ~118 px, glyph-bound windows ±104 px), not a systematic paint
shortfall.

.mxl byte-identity (the decisive check):
- Hymn: desktop 73 (44,237 B) byte-identical to all 1.1x desktop controls (69/69b/
  72/72b); Wasm 73 (44,105 B) byte-identical to Wasm 72/71/69. Wasm-vs-desktop
  deep diff **12** — unchanged from §31.
- Hallelujah: desktop 73 (105,442 B) **byte-identical** to the 1.1x desktop control
  (`desktop-hallelujah-noocr73-1p1.musicxml`); Wasm 73 (105,118 B) byte-identical
  to Wasm 71. Wasm-vs-desktop deep diff **8** — unchanged from §31 (2 filename,
  2 staff-distance ±1, 1 slur ±1, 2 ties in the §25.5 StackRhythm measures P4 m8,
  1 default-x ±1).

Desktop-neutrality of ROUND 36 is therefore proven on both pages: the 1.32x ellipse
changes nothing in either desktop .mxl relative to the 1.1x ellipse.

### 32.5 Correction to §30: ROUND 33 was NOT desktop-neutral on Hallelujah

The 1.1x desktop Hallelujah control (produced this round) vs the stock-desktop
control (`phase23/desktop-hallelujah-noocr.musicxml`, Nov 9, pre-ROUND-33,
`paintSymbol` working, no ellipse): **87 deep diffs** (mostly ±1 default-x on
notes/dynamics in part 5, plus a few structural changes in part 5 m9 — a rest
gaining time-modification+notations, notes losing time-modification). All 87 come
from ROUND 33, none from ROUND 36 (desktop 1.32x vs 1.1x is byte-identical, §32.4).
§30.4's desktop-neutrality claim was verified on the hymn only (byte-identical)
and does not hold on Hallelujah: the ROUND 33 ellipse changes the desktop skeleton
by −797 px at stage B on the hymn (and −1,669 px at stage A on Hallelujah), and on
Hallelujah that moves a few ±1 px positions and a small rhythm decision. The
Wasm-vs-desktop deep diff is unaffected (8 before and after), because Wasm and
desktop moved together. This does not reopen §30 — the ROUND 33 fix stands (it
fixed the slur residual, §30) — but the "desktop-neutral" characterisation is
corrected: ROUND 33 is desktop-neutral on the hymn, desktop-near-neutral (87 deep
diffs, no note-count change) on Hallelujah.

### 32.6 Patch-hygiene note (make_patches.py ROUND 36)

While producing the 1.1x control, an edit to `make_patches.py` landed on the
ROUND 33 replacement string instead of the ROUND 36 replacement string (the
`final double w/h` lines occur in five places in the file). The control run
nevertheless produced a true 1.1x build (stage totals prove it: Hallelujah A
169,898 = the §31 value), because the ROUND 36 `sub()` — which replaces only the
first occurrence — applied the (then 1.1x) ROUND 36 replacement to the product
ellipse. After the control run the factor was restored to its proper home:
ROUND 33 replacement back to 1.1x, ROUND 36 replacement back to `* 1.2`, verified
by re-running `make_patches.py` (exit 0; generated `PageCleaner.java` lines
603–604 carry `* 1.2` with the §32 comment at line 598) and recompiling
`PageCleaner` alone into `phase23/classes`. The generated file is identical in
content to the one that built full-out73. Lesson: when a patch line occurs in
multiple rounds, edit with the surrounding round-specific context (the §32 comment
for ROUND 36, the `g.fill` + `print(... §30)` tail for ROUND 33), never the bare
two lines.

### 32.7 Artefacts

- Build: `teavm-fork/full-out73/` (0 problems, 3,058 classes, 28,700 methods).
- Logs / `.mxl`: `teavm-fork/phase37/` — `build73-shims.log`, `full-build73.log`,
  `run-noocr-wasm73.log` + `wasm-hymn-noocr73.musicxml` (44,105 B, byte-identical
  to out72), `run-noocr-hallelujah73.log` + `wasm-hallelujah-noocr73.musicxml`
  (105,118 B, byte-identical to out71), `desktop-hymn-noocr73.log` +
  `desktop-hymn-noocr73.musicxml` (44,237 B), `desktop-hallelujah-noocr73.log` +
  `desktop-hallelujah-noocr73.musicxml` (105,442 B), 1.1x control
  `desktop-hallelujah-noocr73-1p1.log` + `desktop-hallelujah-noocr73-1p1.musicxml`
  (105,442 B, byte-identical to desktop73), DIAG37 artefacts `compare_diag37.py`,
  `compare-diag37.txt` (12-head sample), `compare-diag37-full.txt` (all 833 px),
  `compare-diag37-73.txt` (1.32x build), DIAG37 runs `desktop-hymn-noocr72.log` /
  `desktop-hymn-noocr72b.log` + `.musicxml` (44,237 B), `run-noocr-wasm72.log` +
  `wasm-hymn-noocr72.musicxml` (44,105 B).
- Fix: `teavm/patched/make_patches.py` ROUND 36 (one-number change in
  `PageCleaner.visit(HeadInter)`); DIAG37 diagnostic ROUND 35 in the same file.
- Next diagnostic named: none for this item — the head-erasure residual is closed
  to the noise floor. The next open items are the Lindenbaum HEADERS CME
  localisation (§23.8 — now deterministic on two pages, Lindenbaum + Snow p1),
  the StackRhythm divergence (§25.5), the HeadHeadRelation SIGraph symptom (§26.12),
  and the template catalog coverage cliff ({80,92,108} ± 8 — Snow p5 point size 140
  -> HEADS 0). Still open overall: BrowserOCR follow-up, photometric recovery,
  clean build, real-browser Chrome run, upstream filings (#272, #21244, §11, §19
  TColor, §27 hypot). CheerpJ 5 remains the only working option.

## §33 — HEADERS CME: genuine TeaVM `ArrayList.retainAll` defect, contained fix in the fork classlib (2026-11-10)

**Verdict: (a) DONE — the CME is fixed and verified gone on every page that
had it. Two NEW blockers surfaced behind it, both localised (§33.6): the
Lindenbaum export trap (null chord timeOffset in the wedge sort) and the
Hallelujah-p06 BEAMS `%f`-on-null failure. German lyrics are still untested
end to end — Lindenbaum produces no .mxl yet.**

### §33.1 Localisation (DIAG38/DIAG39, full-out74/75)

The CME was reproduced with full-out73 on Lindenbaum in 5.9 s (exit 2, no
.mxl; `phase38/run-lindenbaum73.log`). Key fact established first: the
executor is INLINE under TeaVM (shim `ThreadPoolExecutor` runs every task on
the submitting thread) — so this is NOT a true race; it is a single-threaded
concurrent modification during iteration, where a shim collection's iterator
is fail-fast while the JDK collection's iterator tolerates it.

DIAG38 (ROUND 37, phase brackets in `HeaderBuilder.processHeader()`):
desktop compiled alone into `phase23/classes`, all 7 phases complete on all 3
systems (42 lines), .mxl 189 notes vs the 190-note §22 control — the 1-note
difference is the known §20 luma-vs-maxRGB input residual; print-only on
desktop. Wasm full-out74 (0 problems, 3,058 classes): **CME localised to
system #1, phase `retrieveKeys`** (`KeyColumn.retrieveKeys`).

DIAG39 (ROUND 38, sub-phase brackets in `KeyColumn.retrieveKeys` +
DIAG39B in `KeyBuilder.process()`): desktop 126 DIAG39 lines, .mxl
reproduces 189 notes — print-only. Wasm full-out75 (0 problems, 3,058
classes): **CME localised further to `retrieveHiLoPeaks()` for staff #1**
(log: `DIAG39B staff=1 enter retrieveHiLoPeaks` then `DIAG39 CME
phase=process staff=1 sys=1`). `retrieveHiLoPeaks` =
`peakFinder.setQuorum(...)` + `peakFinder.findPeaks(...)`
(`HiLoPeakFinder`) + `Collections.sort(hiloPeaks, Range.byMain)`.

### §33.2 Root cause — the quorum branch of `HiLoPeakFinder.findPeaks`

`HiLoPeakFinder.java:248-260` (stock Audiveris, legal JDK code):

```java
if (quorum != null) {
    for (int i = 0; i < peaks.size(); i++) {
        final Range peak = peaks.get(i);
        if (function.getValue(peak.main) < quorum.yMin) {
            peaks.retainAll(peaks.subList(0, i));
        }
    }
}
```

`peaks.retainAll(peaks.subList(0, i))` — `retainAll` with a subList view of
the same list. On the JDK, `ArrayList.retainAll` uses `batchRemove` (raw
array access, no iterator), so no CME, and the list is truncated to its
first `i` elements. TeaVM's `TArrayList` does NOT override `retainAll`: it
inherits the iterator-based `TAbstractCollection.retainAll`
(`TAbstractCollection.java:123`), which iterates with one iterator while
`subList.contains()` uses a second iterator over the same list; the outer
iterator's `remove()` bumps `modCount`, so the inner subList iterator throws
`ConcurrentModificationException`. The JDK's own `AbstractCollection.retainAll`
is iterator-based too — the contract difference is specifically that
`ArrayList` overrides it. (For a `LinkedList` the JDK throws here as well,
so this is an `ArrayList` fidelity gap, not a general `Collection` one.)

This is a family, not one call site. Audiveris has NINE self-subList
`retainAll` sites, all on `ArrayList`s: `HiLoPeakFinder.java:257`,
`ScaleBuilder.java:834` (`blackPeaks`, SCALE step), `ClefBuilder.java:419`
(`parts`), `KeyBuilder.java:1231, 2073, 2369, 2376, 2378` (`peaks`), and
`KeyExtractor.java:422` (`parts`). Any of them can fire on the right input;
Lindenbaum staff #1 happened to hit the `HiLoPeakFinder` one first
(`retrieveHiLoPeaks n=11` on desktop DIAG39B, quorum branch taken).
`Range` does not override equals/hashCode (identity equality), so
`retainAll(subList(0, i))` keeps exactly the first `i` elements — the
fix's equivalence target.

### §33.3 Minimal repro (stock TeaVM 0.16.0, no fork patches, no Audiveris)

`phase38/retain-repro/src/repro/RetainRepro.java` (11-element list,
`retainAll(subList(0, 5))`, plus `removeAll` coverage — see
`phase38/retain-repro/ISSUE_RETAINALL_DRAFT.md`, NOT filed):

| run | result |
|---|---|
| JDK 25 | `after size=5 peaks=[p0, p1, p2, p3, p4]`, `RETAIN-REPRO OK (no exception)`; `removeAll` → `[x0, x2, x4, x5]`; self-subList `removeAll` → `[x4, x5]` |
| TeaVM 0.16.0 stock classlib (`out/`) | `CAUGHT java.util.ConcurrentModificationException: null` |
| TeaVM, fixed control `subList(5, size).clear()` (`out-fixed/`) | exit 0, JDK-identical output |

The repro was built exactly as the §27/fn272 repros (TeaVM `Spike wasm-gc`,
stock `lib/teavm-classlib-0.16.0.jar`, `run-repro.mjs` runner).

### §33.4 The fix — port OpenJDK `ArrayList.batchRemove` into `TArrayList`

`teavm-classlib-retainall.patch` (67 lines, `TArrayList.java` only, in the
fork source at `src/`): `retainAll` → `batchRemove(c, true)`,
`removeAll` → `batchRemove(c, false)` — exactly the JDK's call shape — with
`batchRemove` ported from OpenJDK `ArrayList` (index scan over the backing
array, `modCount` untouched until the end, so no iterator ever observes a
concurrent modification; `finally` block preserves the tail if `contains()`
throws). This fixes all nine Audiveris sites at once, with no Audiveris-side
change. Installed into `lib-fork/teavm-classlib-0.16.0.jar` by single-file
javac + in-place `jar uf` (method as §19/§27); rollback copy
`teavm-classlib-0.16.0-pre-retainall.jar` kept. The fixed repro under the
patched classlib (`out-retainfix2/`) prints the JDK-identical output on all
three checks, exit 0.

Catch recorded: the first attempt swapped the complements (`retainAll` →
`batchRemove(c, false)`), and the repro caught it immediately — `retainAll`
kept `[p5..p10]` instead of `[p0..p4]`. The inversion was fixed in the
source before any pipeline run; the patch file holds only the correct
version. Lesson, same as §13: never trust a port from memory — the repro's
output check is what caught it.

Why the classlib fix, not the one-line Audiveris fix
(`peaks.subList(i, peaks.size()).clear()`)? The Audiveris form is
semantically identical (verified: the fixed control prints the same result
on both JDK and TeaVM) and remains a valid alternative, but it would have
to be applied at nine sites to close the family, while the classlib fix is
one place, JDK-faithful, and also the correct upstream fix (draft issue
prepared, §33.8).

### §33.5 Verification — full-out76 (0 problems, 3,058 classes, 28,703 methods)

Canonical build; `lib-fork/teavm-classlib-0.16.0.jar` is the patched one.
No-OCR full runs (`run-fullout-noocr.mjs`). CME outcome on every page that
had it:

| page | full-out63 (before) | full-out76 (after) |
|---|---|---|
| Lindenbaum | exit 2 CME, ~5.9 s | HEADERS completes (`retrieveHiLoPeaks` n=12/n=11), reaches PAGE (HEADS 216, SIG 1050, SCORE 2/12, 56 s). No .mxl — new export trap, §33.6 |
| Snow p1 (private-test) | exit 2 CME, ~14 s, 3/3 runs | exit 0, PAGE, HEADS 278, SIG 1134, .mxl 42,424 B (score 2 only, §33.7), 115 notes vs desktop 116 |
| BWV 227 p01 | exit 2 CME, 18.2 s | exit 0, PAGE, .mxl (score 2 only) 30 notes vs desktop 345 — HEADS 0, catalog cliff, §33.7 |
| Hallelujah p06 | exit 2 CME, 7.7 s | exit 2, but NOT the CME — new BEAMS `%f`-on-null failure, §33.6 |
| Gute Nacht p01 | exit 2 CME, 8.7 s | exit 0, PAGE, HEADS 510, SIG 1775, **530 notes = desktop 530**, 52 measures, 2 parts |
| Hymn (regression) | — | exit 0, HEADS 128, SIG 491, **.mxl BYTE-IDENTICAL to the §22 control** (`wasm-hymn.musicxml`, 44,105 B) |
| Hallelujah p01 (regression, multi-page input) | cached ok under out63 | not re-run under out76 in this round (p06 was the CME page) |

No CME remains anywhere in the batch. The multi-page agent's recorded CME
results for these 7 pages (full-out63) are now stale; those pages need a
re-run under full-out76, which is the parent agent's call, not this round's
(the multi-page agent was still running when §33 finished — its files were
not touched, only its `.grey` inputs read).

### §33.6 Two new blockers, localised (not fixed in this round)

1. **Lindenbaum export trap — null chord timeOffset in the wedge sort.**
   After PAGE, `MxlWriter.build(score)` traps (`RuntimeError: dereferencing
   a null pointer`). DumpSeq on `full-out76/classes.wasm.teadbg` (hex→decimal
   done with python3, not by hand — the §13 lesson): innermost frame
   `Rational.compareTo`, called from the `WedgeIterators` sort comparator
   `w1.timeOffset.compareTo(w2.timeOffset)` (`MxlWriter.java`, `new
   WedgeIterators(measure)` ← `Collections.sort` ← `Arrays.sort` ←
   `Arrays.merge`). `timeOffset = chord.getTimeOffset()` is null for some
   wedge-attached chord under Wasm; desktop assigns it (desktop Lindenbaum
   exports fine, §22: 190 notes, 0 deep diffs). `timeOffset` is set during
   RHYTHMS (`MeasureRhythm`/`Slot.setTimeOffset`); a null means RHYTHMS
   never assigned that chord a slot time under Wasm — most plausibly a
   downstream symptom of the StackRhythm divergence (§25.5), not a new
   isolated writer bug. Lindenbaum is the first Wasm page with wedges
   (desktop: 3 wedges), which is why this surfaces here and not on
   hymn/Hallelujah. Next diagnostic: dump which wedge/chord has the null
   timeOffset on both sides and compare RHYTHMS time assignment for it.
   (Note: one DumpSeq frame in this stack, `Shape$<clinit>$lambda...compare`,
   was misattributed by the first hand-converted PC list — the corrected
   conversion puts no PC inside that sequence; the wedge-sort frames above
   are the ones whose PCs fall inside their sequences.)

2. **Hallelujah p06 BEAMS failure — `IllegalFormatConversionException:
   Can't format argument of null using f conversion` in an executor task**
   (`DIAG24 FAILED AT LATEST=BEAMS`, exit 2, main() returns, NO MXL).
   Method unidentified: the executor's FakeClass stack carries no names.
   Static analysis ruled OUT every direct BEAMS-path `String.format` `%f`
   call — `BeamsBuilder.java:592-593` (`coreRatio`/`beltRatio`),
   `BeamStructure.java:451` (`globalDistance`), `BlackHeadSizer.java:220`
   (`params.diameter`), `SpotsBuilder.java:268-270` (`beam`/`diameter`/
   `radius`), `ScaleBuilder.java:401` (`jitter`), `Arc.java:288`
   (`model.getDistance()`) — all take primitive `double`/`float` args,
   which cannot be null. The null must come from a `toString()` evaluated
   during logging (e.g. an inter `toString` formatting a nullable `Double`
   such as `getGrade()` — cf. `CurvesBuilder.java:1120`, which formats
   `getGrade()` with `%.3f`, though that site is in CURVES, not BEAMS), a
   library Formatter path, or a TeaVM `TFormatter` gap. Next diagnostic
   (DIAG41): catch-and-print the format string + args around the BEAMS
   logging sites, or bracket the candidate `toString` calls.

### §33.7 Side observations (recorded, not in scope for this round)

- **Multi-score export limitation (pre-existing since §22):** TeavmMain
  loops `for (Score score : book.getScores())` for both the SCORE print and
  the `MxlWriter` export, and `setMxlB64` is overwritten per score — the
  runner saves only the LAST score. Snow p1 (2 scores: 10 + 8 measures) and
  BWV 227 p01 (2 scores) therefore save an incomplete .mxl. The two SCORE /
  two MXL-len lines in those logs are this loop, not a double run. To fix in
  the clean build: export all scores (concatenate or one file per score).
- **BWV 227 p01 HEADS 0 is the template-catalog cliff, with a concrete
  case:** Scale is `interline(14,15,15)` vs hymn's `interline(21,21,22)`
  (point 92) — estimated calibrated point size ~65, below the catalog floor
  (catalog {80,92,108} ± 8 covers 72–116), so no templates exist and no
  heads are found. Desktop gets 345 notes on the same page. Widening the
  catalog or making the fallback real is the already-open item; this page
  is its cleanest demonstration.
- **Hymn is byte-identical; Gute Nacht is count-identical.** The classlib
  change has no observable effect on pages that never hit the quorum
  branch — as expected, since `batchRemove` is only reached by
  `retainAll`/`removeAll` calls.

### §33.8 Upstream

Genuine TeaVM defect, localised to a single small operation, minimal repro
built: `phase38/retain-repro/ISSUE_RETAINALL_DRAFT.md` (repro steps, JDK vs
TeaVM output, root cause, proposed fix = the `batchRemove` port). **NOT
filed** — Jonathan's decision (2026-11-09) is to file upstream only after
our own work is done. Candidate upstream items now: #272, #21244/#15448,
§11 Profiles.getName(), §19 TColor, §27 hypot, **§33 retainAll/removeAll**.

### §33.9 Artefacts

- `phase38/retain-repro/` — `src/repro/RetainRepro.java`,
  `RetainFixed.java`, `classes/`, `out/` (stock classlib, CME),
  `out-fixed/` (subList.clear control), `out-retainfix/` (first, inverted
  complement — superseded), `out-retainfix2/` (patched classlib, OK),
  `build-*.log`, `run-*.log`, `run-repro.mjs`, `ISSUE_RETAINALL_DRAFT.md`.
- `teavm-classlib-retainall.patch` (67 lines); rollback
  `lib-fork/teavm-classlib-0.16.0-pre-retainall.jar`; patched
  `lib-fork/teavm-classlib-0.16.0.jar` (current).
- `phase38/full-build76.log`, `full-build76-spike.log`,
  `run-lindenbaum73.log` (CME repro), `run-lindenbaum74.log` (DIAG38),
  `run-lindenbaum75.log` (DIAG39), `run-lindenbaum76.log` (PAGE, then wedge
  trap), `run-snow-p1-76.log`, `run-bwv227-p01-76.log`,
  `run-hallelujah-p06-76.log`, `run-gute-nacht-p01-76.log`,
  `run-hymn76.log`; produced `.mxl` in `phase38/`:
  `wasm-snow-p1-noocr76.musicxml` (42,424 B),
  `wasm-bwv227-p01-noocr76.musicxml` (16,643 B),
  `wasm-gute-nacht-p01-noocr76.musicxml` (205,107 B),
  `wasm-hymn-noocr76.musicxml` (44,105 B, byte-identical to §22 control).
  Builds `full-out74/` (DIAG38), `full-out75/` (DIAG39), `full-out76/`
  (current, retainAll fix + DIAG38/39 prints still in).
- Desktop references: `phase38/desktop-lindenbaum-noocr74/75.musicxml`
  (189 notes, luma input); multi-page desktop `.mxl` files (ZIP) for
  bwv227-p01 (345 notes), gute-nacht-p01 (530), hallelujah-p06.
- Next diagnostic named: the Lindenbaum wedge-null export trap (§33.6.1) —
  it is what still blocks German lyrics end to end — then the
  hallelujah-p06 BEAMS `%f` failure (§33.6.2, DIAG41). After those: the
  multi-score export limitation, the template-catalog cliff, StackRhythm
  (§25.5), HeadHeadRelation (§26.12), clean build (strip DIAG14/16/17/18/19/
  20/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39), real-browser
  Chrome run, upstream filings. CheerpJ 5 remains the only working option.

## §34 — Lindenbaum export trap: NOT a Wasm divergence — un-timed chords in "no correct rhythm" stacks; contained writer fix, German lyrics verified end to end (2026-11-10)

**Verdict: (a) DONE — contained fix applied and verified. Lindenbaum exports under Wasm for the first time (223 notes, 14 German lyrics); hymn/Hallelujah unchanged.**

### §34.1 DIAG40 localisation (full-out77) — the §33.6 claim is corrected

DIAG40/DIAG40B prints in `MxlWriter.WedgeIterators` (our own writer, same file both sides; desktop: compiled alone into `phase23/classes`; Wasm: full-out77, 0 problems, 3,058 classes).

- **Headline correction to §33.6: the null timeOffset is NOT Wasm-only.** Desktop has the IDENTICAL nulls in the IDENTICAL chords: measure #1P2 (stack #1, system #1), wedge DIMINUENDO RIGHT chord slot #18, Voice #2, bounds x=1277, same grades/bounds/durations on both sides (inter ids differ — allocation order — desktop #4232, Wasm #3979). Same for #3P2 (desktop #4253). Three null-offset chords per measure (Voice #2 slots 16/17/18, bounds x=1197/1237/1277, dur 1/16), plus Voice #4/#6 chords in stack #4 (DIAG40 nullOffset lines, desktop only — Wasm dies at #1P2 before reaching them).
- The sort DOES trap on desktop too: DIAG40B `sortOut` is MISSING for #1P2 and #3P2 on desktop (present for every other measure). Standalone TimSort repro (`phase40/sorttest-timsort/SortTest.java`, JDK 25) NPEs exactly as expected on `[1/12, 1/4, 7/16, null]` with the wedge comparator (`TimSort.countRunAndMakeAscending`).
- Desktop "exports fine" only because `processMeasure`'s catch swallows the NPE and removes the measure shell (`MxlWriter.java:760-762`) — P2 measures 1 and 3 are silently MISSING from the desktop `.mxl` (P2 has 10 measures, not 12; 189 notes). Log: `WARN teavm.MxlWriter -- Error visiting Measure{#1P2} / {#3P2}`, stack at `MxlWriter.java:622` (the `WedgeIterators` construction).
- Wasm dies because the same null dereference is an uncatchable Wasm trap (§27 pattern), so the whole run dies instead of dropping 2 measures. **The Wasm/desktop difference is catchability only, not data.**
- Wasm DIAG40 confirms identity before the trap: same 4 wedge events for #1P2 in the same order `[1/12, 1/4, 7/16, null]`, same wedge/chord grades and bounds; `sortIn` printed, `RuntimeError` immediately after, no `sortOut`. Wasm DIAG40 total 45 lines vs desktop 91 — Wasm dies at the first null measure, desktop continues past its two dropped measures.

### §34.2 Root cause upstream (RHYTHMS) — an Audiveris behaviour, not a Wasm defect

- The null chords are the trailing chords of Voice #2 in stacks S1 #1 and S1 #3, where `StackRhythm` logs "no correct rhythm" — IDENTICAL on both sides (same four stacks S1 #1, S1 #3, S2 #4, S2 #5 in both logs). Their slots never got a timeOffset, so `Slot.afterReload` leaves the chords un-timed (`timeOffset` stays null from `resetTiming`). Same family as the §25.5 StackRhythm divergence, but here identical on both sides. Fixing StackRhythm's failure itself remains the open §25.5 item; the writer fix below is the contained unblock.
- `getDuration()` does not need `timeOffset` (note type/dots/tuplet; null only for measure rests) and `getEndTime()` returns null safely when `timeOffset` is null — so un-timed chords are exportable once the writer stops dereferencing the null offset.

### §34.3 The fix (our MxlWriter only, `teavm/entry/src/teavm/MxlWriter.java`)

Three null guards, all in our own writer (no Audiveris patch, no make_patches.py ROUND — MxlWriter is entry code, compiled from `entry/src` by `build.sh` and into `phase23/classes` for the desktop harness):

1. **Wedge sort comparator — nulls last.** A null event sorts after every timed event.
2. **`WedgeIterators.push()` — a null event never fires on a timed push.** It waits for the final `push(null)` flush. (Found by re-running: the sort-only fix moved the trap to `push()` at `MxlWriter.java:2655` — the first timed push after the last timed event compared against the null event. Fixed in the same round; the sort-only intermediate build `full-out77`→ desktop `desktop-lindenbaum-noocr78.musicxml` still dropped both measures.)
3. **Voice loop — forward-insert only when `timeOffset != null`; `timeCounter` advanced by the chord duration only if non-null.** `wedgeIters.push(timeOffset)` was already null-safe (flushes on null).
- Effect: wedges attached to un-timed chords are emitted at the end of the measure (the `push(null)` flush), instead of losing the measure. The degradation is positional only (wedge stop lands at measure end rather than at its true — unknowable — time).
- NOT desktop-neutral in the strict sense: desktop output gains the 2 restored measures (it can no longer drop them). Verification is same-patched-writer both sides, identical output. Stock Audiveris drops these measures too (the same catch exists in `PartwiseBuilder`) — our writer is now more complete than stock, not less faithful.

### §34.4 Verification — full-out78 (0 problems, 3,058 classes, 28,703 methods)

- **Desktop (fixed writer): 0 "Error visiting"; P2 12/12 measures; 189 → 223 notes.** Structural diff vs pre-fix desktop: ONLY +P2 m1/m3 (17 pitched notes, 0 rests, 1 backup, 4 wedge elements each). 9 later P2 measures differ only in slur `number=` renumbering (same slur geometry — the running allocation shifts when two slur-bearing measures are restored) and the G/F clef pair moves from P2 m4 to P2 m1 (the writer re-emits the part's opening clefs at the first measure it actually emits — in the old file m4 was the first emitted measure after the gap).
- **Wasm full-out78: Lindenbaum `.mxl` 99,305 B, 223 notes, 24 measures, 11 wedge elements; per-measure note/wedge counts identical to the fixed desktop.** Deep diff vs fixed desktop (`phase40/compare-deep-lindenbaum78.txt`): **10** — 2 filename (Wasm hardcodes `/hymn-satb.png` as `<source>`, desktop uses the real PNG path — known) + 8 × ±1 `default-x`/`staff-distance`/slur-bezier (the §22 residual family); zero structural diffs.
- **No regression: hymn Wasm 44,105 B byte-identical to the §22 canonical `wasm-hymn.musicxml`; Hallelujah Wasm 105,118 B byte-identical to the out73 file (deep diff 8 unchanged).**

### §34.5 German lyrics end to end (bonus verification)

- deu OCR run (`run-fullout-ocr.mjs`, full-out78, `deu`): phase 1 exports the clean image; tesseract.js deu 218 rows (13 L / 45 W / 160 C); phase 2 `.mxl` 101,039 B, 223 notes, **14 lyrics**.
- Syllable sequence identical both sides: "Am Brun nen vor dem Tho re da steht ein Lin den baum; ich" (desktop deu control with the same prefed OCR text, `phase23/lindenbaum-ocr.txt`: 223 notes, 14 lyrics, same sequence). Deep diff 12 (`phase40/compare-deep-lindenbaum-ocr78.txt`): 2 filename + 2 credit font-size (the known §24 residual — Wasm infers 11/6 vs desktop 10/9) + 8 × ±1. Zero structural diffs.
- **German lyrics end to end: UNBLOCKED.** (Lyric recall vs ground truth not re-scored here — 14 lyrics is the page's first-system opening line only; the full-page recall question belongs to the BrowserOCR follow-up, not this round.)

### §34.6 Corrections to the record

- **§33.6.1 withdrawn:** "timeOffset is null for some wedge-attached chord under Wasm; desktop assigns it" is wrong — desktop has the identical nulls. The trap's Wasm-only aspect is catchability, not data.
- **§22's "Lindenbaum 190 notes, 0 deep diffs" was against a desktop `.mxl` that itself drops P2 m1/m3** (189 notes in our harness, 190 stock). The true desktop reference with the fix is 223 notes. GT for the page is 216 (open-music manifest) — 223 vs 216 is now a recall question about the notes, not a missing-measures question.
- The multi-page agent's full-out63 Lindenbaum result (CME) and its Wasm-vs-desktop counts are stale in the same way §33 noted for the CME pages; a re-run under full-out78 is the natural follow-up (not done here).

### §34.7 Artefacts

- `phase40/` — DIAG40 desktop logs (`desktop-lindenbaum-noocr77/77b.log` + `.musicxml`, pre-fix; `noocr78.log`, sort-only; `noocr78b.log`, full fix) and `.mxl` files; Wasm logs (`run-lindenbaum77.log`, trap; `run-lindenbaum78.log`, export; `run-hymn78.log`, `run-hallelujah78.log`); `compare-deep-lindenbaum78.txt`, `compare-deep-lindenbaum-ocr78.txt`; `sorttest-timsort/` (standalone TimSort NPE repro + README); `full-build77/78.log`, `full-build77/78-spike.log`.
- Produced `.mxl`: `wasm-lindenbaum-noocr78.musicxml` (99,305 B, 223 notes), `wasm-lindenbaum-ocr78.musicxml` (101,039 B, 223 notes, 14 lyrics), `desktop-lindenbaum-noocr78b.musicxml` (99,463 B), `desktop-lindenbaum-ocr78.musicxml` (101,195 B), `wasm-hymn-noocr78.musicxml` (44,105 B, byte-identical to §22 control), `wasm-hallelujah-noocr78.musicxml` (105,118 B, byte-identical to out73).
- Builds: `full-out77/` (DIAG40 diagnostic, trap reproduced), `full-out78/` (current, fix + DIAG40/40B prints still in — strip in the clean build with DIAG14/16/17/18/19/20/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40).
- Nothing pushed, filed, or merged; `jdlehman/score-reader` untouched. No TeaVM defect in this round — nothing to file upstream for §34 (the upstream list is unchanged: #272, #21244, §11, §19 TColor, §27 hypot, §33 retainAll).
- Next diagnostic named: the Hallelujah-p06 BEAMS `%f` failure (§33.6.2, DIAG41). After that: the multi-score export limitation, the template-catalog cliff, StackRhythm (§25.5), HeadHeadRelation (§26.12), clean build, real-browser Chrome run, upstream filings. CheerpJ 5 remains the only working option.

## §35 — Hallelujah-p06 `%f` failure: NOT BEAMS — LEDGERS `TFormatter` null-argument defect; contained fix, p06 exports (2026-11-10)

**Verdict: (a) DONE — contained fix applied and verified. The Hallelujah-p06
`IllegalFormatConversionException` is a genuine TeaVM defect in
`TFormatter`: it throws for a null argument to a numeric conversion where
the JDK formats `"null"`. Full-out80: p06 completes (exit 0, `.mxl`
produced); hymn/Hallelujah-p01/Lindenbaum byte-identical to out78. The p06
`.mxl` is rests-only for a separate, pre-existing reason — the template-
catalog cliff (resolution 140, §35.6) — not this fix.**

### 35.1 The §33.6.2 attribution was wrong — twice over

§33.6.2 called this a "BEAMS failure" and ruled out "every direct
BEAMS-path `String.format` `%f` call". Both halves are wrong:

1. **It is not BEAMS.** TeavmMain's `DIAG24 FAILED AT LATEST=` prints
   `SheetStub.getLatestStep()`, which reports the latest step **done**
   (`isDone(step)` — `SheetStub.java:749-756`), not the step running.
   Step order is `... HEADERS, BEAMS, LEDGERS, HEADS, ...`
   (`OmrStep.java:54-70`), so `LATEST=BEAMS` means the failure is in the
   **next** step, **LEDGERS**. The multi-page Hallelujah-p09 failure
   ("IllegalFormatConversionException, null `%f` argument, in BEAMS") is
   the same misattribution by message — same family, same LATEST artefact.
2. **The format call is not in the BEAMS path at all.** It is in
   `LedgersPostAnalysis.filter()` (LEDGERS doEpilog), the only site in the
   LEDGERS path where a null can reach a `%f` conversion.

Corroborating evidence for LEDGERS, visible before DIAG41: the 225
consecutive `DIAG14 getSource NO_STAFF` lines between system #3's BEAMS
prints (line 680) and the failure (line 906) are
`LedgersBuilder.ConvexityCheck.getValue()` (`LedgersBuilder.java:902-903`,
`getSource(NO_STAFF)` per ledger candidate per check) — LEDGERS doSystem
work, after BEAMS doSystem finished.

### 35.2 DIAG41 localisation (full-out79) — the null is min/maxDeltaBelowRatio

DIAG41 (ROUND 39 in `teavm/patched/make_patches.py`, same patched file
both sides, print-only): per-staff ledger census in `collect()`,
cardinalities + the six ratios before the format in `filter()`.

Wasm p06 (`phase41/run-p06-79.log`, exit 2, same failure):

```
DIAG41 collect staff#1 keys=[-1] above=6 below=0
DIAG41 collect staff#3 keys=[-1] above=3 below=0
DIAG41 collect staff#5 keys=[-1] above=8 below=0
DIAG41 collect staff#8 keys=[-1] above=1 below=0
DIAG41 collect staff#9 keys=[-1] above=11 below=0
DIAG41 collect staff#11 keys=[-1] above=2 below=0
DIAG41 collect staff#12 keys=[-1] above=8 below=0
(all other staves keys=[] above=0 below=0)
DIAG41 collect infos=39 cardAbove=39 cardBelow=0 cardHeight=39 cardWidth=29
DIAG41 filter cardAbove=39 cardBelow=0 cardHeight=39 minAbove=0.73065234022056 maxAbove=1.0518496968453708 minBelow=null maxBelow=null minHeight=0.037465810394649655 maxHeight=0.10325098914567923
DIAG24 FAILED AT LATEST=BEAMS
TEAVM FAILED: java.util.concurrent.ExecutionException: java.util.IllegalFormatConversionException: Can't format argument of null using f conversion
```

Mechanism (`LedgersPostAnalysis.java:230-272`): `filter()` declares six
boxed `Double`s, all initially null, and assigns each pair only if its
`Population` is non-empty (`popDeltaAbove.getCardinality() > 0`, etc.).
p06 has 39 ledgers, **all above staff (key −1), zero below** — so
`popDeltaBelow` is empty and `minDeltaBelowRatio`/`maxDeltaBelowRatio`
stay null. The `String.format("Filter minDeltaAboveRatio:%.2f ...",
minDeltaAboveRatio, ...)` then evaluates `%.2f` on a null `Double`.
The format argument is evaluated **eagerly** before `logger.debug` is
invoked, so log level cannot save it — and `filter()` also unboxes the
same ratios afterwards (`(info.key < 0 ? minDeltaAboveRatio :
minDeltaBelowRatio) * interline`), so the format is the first of two
null dereferences on this path. `Info.toString()` is not a candidate
(all its format args are primitives); `Population.toString()` is not
either (formats only when `n > 0`, primitive args).

### 35.3 Desktop comparison — identical data, different formatter

Desktop harness (`DesktopOcrExport phase41/hallelujah-p06.png`,
`testocr.file=phase23/empty-ocr.txt`, same patched file compiled alone
into `phase23/classes`, PNG regenerated from the same `.grey` bytes):
exit 0, `.mxl` 69,883 B, and the DIAG41 lines are **identical to Wasm
to the last digit** — `infos=39 cardAbove=39 cardBelow=0 cardHeight=39`,
same per-staff census, `minBelow=null maxBelow=null` — followed by
`DIAG41 filter formatted ok`. So the data is identical on both sides;
the divergence is the formatter, not the ledger detection.

JDK null semantics, measured on this VM's JDK 25 (`FmtNull.java`,
`/tmp/fmttest/`): a null argument formats as `"null"` for **every**
conversion — `%f`, `%e`, `%g`, `%a`, `%d`, `%x`, `%o`, `%s`, `%c`, `%h`;
`"false"` for `%b`. Precision truncates (`%.2f` → `"nu"`,
`%5.2f` → `"   nu"`), width pads. Nothing throws for null.

### 35.4 Root cause — `TFormatter` numeric formatters throw on null

`TFormatter.FormatWriter`
(`src/classlib/src/main/java/org/teavm/classlib/java/util/TFormatter.java`,
0.16.0 tag e87d452):

- `formatFloat` (line ~257): throws `IllegalFormatConversionException`
  for any argument that is not `Double`/`Float`/`BigDecimal` — including
  null.
- `formatDecimalInt` (line ~402): throws for any argument that is not an
  integral wrapper — including null.
- `formatRadixInt` (line ~475): same — including null.
- `formatChar` already has the null branch (`formatGivenString(upperCase,
  "null")`); `formatBoolean` (`"false"`), `formatHex` (`"null"`),
  `formatString` (`String.valueOf`) already handle null. Only the three
  numeric formatters are missing it. (`formatGivenString` already applies
  precision truncation + width padding + uppercasing, i.e. exactly the
  JDK's null rendering.)

Minimal repro (`phase41/format-repro/`, TeaVM-level, independent of
Audiveris — same pattern as §27 hypot / §33 retainAll): `FormatMain.java`
prints `String.format` results for 13 cases, including the exact six-
argument `LedgersPostAnalysis` format string. Built with `Spike wasm-gc`
(`jars.txt`: shims.jar + fork classlib + teavm libs + repro classes),
run with `run-repro2.mjs`:

| case | JDK 25 | TeaVM pre-fix | TeaVM post-fix |
|---|---|---|---|
| `%.2f`, null Double | `nu` | **throws** | `nu` |
| `%f`, null Double | `null` | **throws** | `null` |
| `%d`, null Integer | `null` | **throws** | `null` |
| `%x`, null Integer | `null` | **throws** | `null` |
| `%o`, null Integer | `null` | **throws** | `null` |
| `%5.2f`, null Double | `   nu` | **throws** | `   nu` |
| `%s`/`%c`/`%b`/`%h`, null | `null`/`null`/`false`/`null` | same | same |
| `%.2f`, 1.23456 / `%d`, 42 | `1.23` / `42` | same | same |
| 6-arg filter format (2 nulls) | formats, `nu` × 2 | **throws** | formats, `nu` × 2 |

Pre-fix repro (`out/`, 170 classes, 1,868 methods): 6 numeric-null cases
throw, the rest correct. Post-fix (`out-fixed/`): all 13 cases
JDK-exact.

### 35.5 The fix (fork classlib — genuine TeaVM defect)

`teavm-classlib-formatter.patch` (3 hunks, one per method): in
`formatFloat`, `formatDecimalInt`, and `formatRadixInt`, right after
reading the argument, return the JDK's `"null"` rendering through the
existing width/precision handling:

```java
if (arg == null) {
    formatGivenString(upperCase, "null");
    return;
}
```

Placed **after** the flag-verification calls in each method, so illegal
flag/precision combinations still throw exactly as before. Jar entry
replaced in place (`lib-fork/teavm-classlib-0.16.0.jar`; pre-fix jar kept
as `lib-fork/teavm-classlib-0.16.0-pre-formatter.jar`); single-file
`javac` + `jar uf`, same procedure as §19 TColor / §27 hypot / §33
retainAll. `teavm-classlib-0.16.0.jar` is the jar the canonical build
references (`teavm-main-jars-corepatch2.txt`), so full-out80 picks the
fix up with no build-script change.

Known limitation (not part of this fix): `TFormatter` does not dispatch
`%e`/`%E`/`%g`/`%G`/`%a`/`%A`/`%F` at all — they hit `default: throw new
UnknownFormatConversionException`. The JDK supports them; that is a
separate coverage gap, recorded in the issue draft, not the null defect
fixed here.

### 35.6 Verification — full-out80 (0 problems, 3,058 classes, 28,703 methods)

- **Hallelujah p06 no-OCR** (`phase41/run-p06-80.log`): exit 0,
  `DIAG41 filter formatted ok`, `main() returned in 43514 ms`,
  `.mxl` 24,841 B, 4 parts, 36 measures, 54 notes — all rests.
- **The rests-only output is the template-catalog cliff, not this fix:**
  Wasm requests resolution **140** (`TemplateFactory: Rebuilding
  NOTEHEAD_VOID template at resolution 140`, then `No template for
  NOTEHEAD_VOID at any resolution, giving up`), outside the pre-rendered
  catalog {80, 92, 108} ± 8 (72–116) — `STAVES 12 HEADS 0 CHECK 0`.
  Desktop (same input) finds 149 pitched notes / 203 total, 54 rests.
  The 54 rests match exactly (54 = 54); the pitched gap is entirely
  HEADS 0, and the 36-vs-40 measures and 0-vs-8 beams/slurs are its
  downstream (no heads → no beams/slurs attached). p06 joins p04/p05/p08
  (resolution 142) as a catalog-cliff page — the cliff is now the
  biggest Wasm gap and the named next item (§35.9).
- **No regression** (all byte-identical to out78): hymn 44,105 B
  (`phase41/run-hymn80.log`, exit 0); Hallelujah p01 105,118 B
  (`phase41/run-hallelujah80.log`, exit 0); Lindenbaum 99,305 B, 223
  notes (`phase41/run-lindenbaum80.log`, exit 0).
- **Desktop p06 reference** (harness, `phase41/desktop-hallelujah-p06-
  noocr79.musicxml`, 69,883 B): 203 notes, 149 pitched, 54 rests, 4
  parts, 40 measures, 8 beams, 8 slurs. (The multi-page stock-CLI
  `desktop/p06/p06.mxl` is 4,307 B with 0 notes — a different export
  path; the harness file is the like-for-like reference here.)
- One service restart mid-round killed the first full-out79 Wasm run
  (log ended mid-BEAMS at a DIAG31 line); the re-run completed cleanly
  and is the recorded one. The desktop compile of the single patched
  file survived the restart (class timestamp verified).

### 35.7 Corrections to the record

- **§33.6.2 withdrawn in full:** "Hallelujah p06 BEAMS failure" is
  wrong on both counts — the failure is in LEDGERS (doEpilog,
  `LedgersPostAnalysis.filter()`), and the `%f`-on-null is a genuine
  TeaVM `TFormatter` defect, not a BEAMS-path logging site. The static
  analysis ruling out BEAMS-path `%f` calls was correct but aimed at
  the wrong step.
- **DIAG24 caveat, general:** `FAILED AT LATEST=<step>` names the last
  step *completed*, so a failure it reports belongs to the *next* step
  in `OmrStep` order. Any earlier `LATEST=` attribution that was read
  as "failed in that step" should be re-checked against the step order
  (the §23.8 Lindenbaum CME attribution to HEADERS was confirmed by
  DIAG38/39 phase brackets inside HEADERS itself, so it stands).
- The multi-page agent's full-out63 Hallelujah p09 failure (same
  exception message) is the same family by message; whether it is the
  same `filter()` site needs a re-run under full-out80 (not done here).
  The multi-page CME results for the 7 pages are likewise stale after
  §33, and a full-out80 re-run is the natural follow-up.

### 35.8 Upstream

Genuine TeaVM defect, localised to a single small operation in three
methods, minimal repro built, fix is a 3-hunk classlib patch:
`phase41/format-repro/ISSUE_FORMATTER_DRAFT.md` (repro steps, JDK vs
TeaVM output table, root cause, proposed fix, known `%e`/`%g`/`%a`/`%F`
limitation, FormatterTest gap). **NOT filed** — Jonathan's decision
(2026-11-09) is to file upstream only after our own work is done.
Candidate upstream items now: #272, #21244/#15448, §11
Profiles.getName(), §19 TColor, §27 hypot, §33 retainAll/removeAll,
**§35 TFormatter null argument**. TeaVM's own `FormatterTest` does not
cover null arguments to numeric conversions — a regression test along
the repro's lines would cover this. Verified here by `javac` + in-place
`jar uf` (Gradle does not run in this VM); per `src/AGENTS.md` the
Gradle suite (`./gradlew :tests:test` with the `teavm.tests.wasm-gc`/
`js`/`c` and `teavm.tests.optimized` properties) must run on a machine
where Gradle works before submitting upstream.

### 35.9 Artefacts

- `phase41/` — DIAG41 logs (`run-p06-79.log`, trap reproduced;
  `run-p06-80.log`, p06 exports; `run-hymn80.log`, `run-hallelujah80.log`,
  `run-lindenbaum80.log`, regressions; `desktop-hallelujah-p06-noocr79.log`
  + `.musicxml`, desktop reference; `build79.log`,
  `full-build79-spike.log`, `build80.log`, `full-build80-spike.log`;
  `desktop-compile-diag41.log`; `hallelujah-p06.png`, regenerated from
  `p06.grey` with PIL); `format-repro/` (`FormatMain.java`, `classes/`,
  `jars.txt`, `out/` pre-fix, `out-fixed/` post-fix, `build.log`,
  `build-fixed.log`, `run-prefixed.log`, `run-fixed.log`,
  `ISSUE_FORMATTER_DRAFT.md`); `fmt-classes/` (compiled `TFormatter`
  classes); `fmt-compile.log`.
- `teavm-classlib-formatter.patch` (3 hunks); rollback
  `lib-fork/teavm-classlib-0.16.0-pre-formatter.jar`; patched
  `lib-fork/teavm-classlib-0.16.0.jar` (current).
- Produced `.mxl`: `wasm-hallelujah-p06-noocr80.musicxml` (24,841 B,
  rests-only — catalog cliff, §35.6), `wasm-hymn-noocr80.musicxml`
  (44,105 B, byte-identical to §22 control),
  `wasm-hallelujah-noocr80.musicxml` (105,118 B, byte-identical to
  out78), `wasm-lindenbaum-noocr80.musicxml` (99,305 B, byte-identical
  to out78).
- Builds: `full-out79/` (DIAG41 diagnostic, trap reproduced),
  `full-out80/` (current, formatter fix + DIAG41 prints still in —
  strip in the clean build with
  DIAG14/16/17/18/19/20/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/
  38/39/40/41).
- Nothing pushed, filed, or merged; `jdlehman/score-reader` untouched.
- Next diagnostic named: the template-catalog coverage cliff ({80, 92,
  108} ± 8 — p06 requests 140, p04/p05/p08 request 142, BWV 227
  requests ~65/128; 16/37 multi-page pages HEADS 0, now the biggest
  Wasm gap). After that: the multi-page re-run under full-out80 (CME
  pages + p06/p09), the multi-score export limitation, StackRhythm
  (§25.5), HeadHeadRelation (§26.12), clean build, real-browser Chrome
  run, upstream filings. CheerpJ 5 remains the only working option.

## §36 — Template-catalog coverage cliff: mapped, corrected, fixed by widening the catalog; variant B (MAX_DIFF 10, no 72) measured and rejected (2026-11-10)

### §36.0 Verdict: (a) contained fix applied and verified

The catalog is widened from {80, 92, 108} to {64, 72, 80, 92, 108} at the
same MAX_DIFF 8. Both HEADS-0 test pages recover with counts exactly
equal to desktop (Hallelujah p04: 231/184/47; BWV 227 p02: 338/297/41),
and hymn + Lindenbaum are byte-identical to their §22/§34 references
(no regression). One documented tradeoff: Hallelujah p01's deep-diff
metric goes 8 → 93 against the same desktop reference — counts,
beams, slurs and ties all identical, the extra diffs are ±1-tenth
position roundings plus one StackRhythm-family measure (§36.5). The
cheaper alternative — drop the 72 catalog and widen MAX_DIFF to 10
(variant B, full-out83) — was built, measured, and REJECTED: undersize
templates miscount in both directions (§36.6). Current build:
full-out82. Nothing pushed, filed, or merged; `jdlehman/score-reader`
untouched; the private Snow PDF stayed under `private-test/`.

### §36.1 The cliff map — and a correction to the numbers everyone quoted

The multi-page report's and §35's "requests resolution 128/140/142"
figures are NOT the catalog requests. They are
`TemplateFactory.Builder.processSymbol(ratio)` retry prints: when hole
detection fails on the blank stub-font glyph, the builder retries at a
larger ratio and logs "Rebuilding {shape} template at resolution
{larger*ps}" — so the FIRST retry print is 2× the catalog point size.
The true catalog requests, established by DIAG42 (§36.2):

| page | true catalog request | nearest old catalog | diff | old result |
|------|---------------------|--------------------|-----:|------------|
| hymn | 92 | 92 | 0 | works |
| Gute Nacht p02 | 92 | 92 | 0 | works |
| Hallelujah p01/p02/p03/p07 | 72 | 80 | 8 | works (boundary) |
| Lindenbaum | 92 | 92 | 0 | works |
| Hallelujah p04/p05/p08 | 71 | 80 | 9 | HEADS 0 |
| Hallelujah p06 | 70 | 80 | 10 | HEADS 0 |
| BWV 227 (all 19 HEADS-reaching pages) | 64 | 80 | 16 | HEADS 0 |
| Snow p5 (full 300 dpi) | 140 | 108 | 32 | HEADS 0 |

This also answers the multi-page run's open question — why the
calibrated size differs between pages with the SAME interline 16–17:
the calibrated size does not come from the interline, it comes from
the measured black-head width, which differs by 0.3 px between pages
(21.2 vs 20.9). That rounds to point size 72 vs 71, and 71 is exactly
one point outside the ±8 window around catalog 80. p01 squeaks in at
diff exactly 8; p04 misses by 1.

### §36.2 DIAG42 — how the requested resolution is computed

ROUND 42 (print-only, same patched files both sides) dumps three links
of the calibration chain, verified by reading the stock Audiveris
sources in `~/workspace/score-reader-spikes/repo/.work/audiveris/`:

1. `BlackHeadSizer.measureSingles` — finds single black noteheads,
   measures their mean width `w` (and height) over the core set.
2. `MusicFont.computePointSize(w)` — `v1 = rint(w*3.3)`; `w1` = text
   layout width at `v1`; `v2 = v1 ± rint(w*0.25)`; interpolated
   `v = rint(v1 + (v2-v1)*(w-w1)/(w2-w1))`. This is
   `musicFontScale.pointSize`.
3. `Staff.getHeadPointSize()` =
   `MusicFont.getHeadPointSize(scale, specificInterline)` —
   `rint((staffInterline / sheetInterline) * musicFontScale.pointSize)`
   when the sizer set a scale, else the fallback
   `getPointSize(rint(staffInterline * headRatio=1.0))` =
   `4 * staffInterline` (from `OmrFont.getPointSize`).

DIAG42 results (Wasm full-out81 vs desktop harness, PNGs regenerated
from the same `.grey` bytes with PIL — the §29.2-safe shape):

- Hallelujah p01 (working): Wasm cps width=21.219 v1=70 w1=20.651
  v2=75 w2=22.126 v=72; sizer singles=210 core=105 wMean=21.219
  wSd=0.416 hMean=17.324 hSd=1.156 mfsPoint=72; headps 17.0/17 → 72.
  Desktop identical (cps w1=20.65625 — 4th-decimal shim rounding only
  — v=72; sizer identical to the last digit). Desktop `.omr`:
  mean-width 21.2, point-size 72.
- Hallelujah p04 (failing): Wasm cps width=20.942 v1=69 w1=20.356
  v2=74 w2=21.831 v=71; sizer singles=171 core=86 wMean=20.942
  wSd=0.494 hMean=17.593 hSd=1.022 mfsPoint=71; headps 17.0/17 → 71.
  Desktop identical (cps v=71; sizer identical). Desktop `.omr`:
  mean-width 20.9, point-size 71. **The sizer and the interpolation are
  CORRECT on the failing page — the measured width is not 2×, and the
  interpolation does not diverge. The catalog request is 71, and
  |80−71| = 9 > MAX_DIFF 8 — it misses by ONE point.**
- BWV 227 p02 (failing): Wasm cps width=19.0 v1=63 w1=18.586 v2=68
  w2=20.061 v=64; sizer singles=202 core=101 wMean=19.0 wSd=0.0
  hMean=16.525 hSd=0.502 mfsPoint=64. Desktop `.omr`: mean-width 19,
  point-size 64. Catalog request 64, retry print 128; |108−64| = 44,
  miss is 8 below the old window floor 72.
- Gute Nacht p02 (working): Wasm cps width=27.083 v1=89 w1=26.256
  v2=96 w2=28.321 v=92; sizer singles=433 core=216 wMean=27.083
  wSd=0.277 hMean=23.306 hSd=0.462 mfsPoint=92; headps 21.0/21 → 92.
  Desktop `.omr`: mean-width 27.1, point-size 92.
- The FALLBACK headps lines (pre-sizer, harmless — they never touch
  the template catalog): PageCleaner (staffInterline 17.0 → 68, 11.39
  → 44) and `BlackHeadSizer.measureSingles`' own
  `getHeadFont(family, scale, 0)` (0.0 → 0). The fallback arithmetic
  (4 × staffInterline ≈ 68 for Hallelujah) was already ruled out
  before DIAG42.
- Snow p5: genuine request 140 (interline 30; rebuilds at 280/560/1120
  in `private-test/run-noocr-wasm63-snow-p5.log`, first retry 280 =
  2×140). The §30 4096-cap caveat STANDS: 140 × 4096/5100 ≈ 112 →
  catalog 108, diff 4.4 ≤ 8 → HIT at the app's cap.

### §36.3 Fix direction judged, with measurements

- (a) **Widen the catalog — CHOSEN.** Add 64 and 72. Cost per catalog
  measured in §17: ~260 KB source, ~0.64 MB Wasm. Precedent that a
  diff-8 template is fine: Hallelujah p01 uses the 80-template for a
  72 request (diff 8, 11% oversize) and matches desktop EXACTLY on
  counts on all 7 matching pages. With catalogs {64, 72, 80, 92, 108},
  coverage is [56..116] continuous (64±8, 72±8, 80±8, 92±8, 108±8)
  — it covers the entire 37-page multi-page set.
- (b) Make the fallback real — NOT viable in one round. There is no
  stock fallback that renders a template on the fly from the font in
  the headless path; the fallback would mean rendering Bravura glyphs
  under TeaVM — the stub-font problem Phase B exists to avoid. The
  pre-rendered approach already works; it just needs more entries.
- (c) Rescale the input image into the catalog window — a hack: it
  changes all scale-dependent pipeline behaviour and needs per-page
  validation. The app's 4096 cap already rescales Snow p5 into the
  window for free (§36.1).
- Snow p5 at 140 is NOT covered by (a) (needs a 140 catalog for
  [132,148]); it is a bad scan on which desktop itself crashes, and
  the app cap rescales it into the window — recorded as a possible
  future addition, not added in this round.

### §36.4 Fix applied (variant A)

- `phaseb/TemplateDump.java` run on desktop JDK (stock Audiveris
  jars): dumped catalogs 64 and 72 to
  `teavm-fork/phase42/templates-64-72.json` (257,081 chars, 9.8 s,
  exit 0) — 64: blackW 18.875, ratio 0.29492; 72: blackW 21.234,
  ratio 0.29492 (constant, matching existing catalogs 0.2950).
  Merged into `teavm-fork/phaseb/templates.json` (backup at
  `phase42/templates-before-64-72.json`); catalogs now
  [54, 64, 72, 80, 92, 108]; key-point totals 54: 6,008, 64: 9,066,
  72: 11,821, 80: 14,728, 92: 19,410, 108: 27,132.
- `phaseb/gen_prerendered.py`: WANT updated [80,92,108] →
  [64,72,80,92,108] (+ §36 docstring note). Regenerated
  `teavm/entry/src/teavm/PreRenderedTemplates.java`: 1,065,054 bytes
  (was 784 KB), 82,157 key points, RATIO=1.000000,
  `CATALOG_POINT_SIZES = {64, 72, 80, 92, 108}`.
- `phaseb/src/RoundTrip.java`: fixed a stale constant reference
  (`DESKTOP_PER_TEAVM_POINT` → `DESKTOP_PER_REQUESTED_POINT`; the
  §19 rename had left the source uncompilable against the current
  generated file — the compiled class in `phaseb/classes/` predated
  the rename). Recompiled RoundTrip + PreRenderedTemplates;
  **round-trip: 120/120 PASS, 0 failures** (5 catalogs × 24 shapes,
  field-identical to live native templates; fallbacks Leland/54,
  Bravura/10, Bravura/200 all null). Log: `phase42/roundtrip.log`.
- full-out82 built (build.sh + canonical Spike command): 3,058
  classes, 28,753 methods, classes.wasm 14,349,130 bytes (vs
  ~13.59 MB for out61/out63-era builds — the two added catalogs cost
  ~+0.76 MB Wasm). Logs: `phase42/build82.log`,
  `phase42/full-build82-spike.log`.

### §36.5 Verification — variant A (full-out82)

Runs via `phase42/run-verify82.sh` (all exit 0; desktop references:
DIAG42 harness `.musicxml` for Hallelujah p01/p04, multi-page desktop
for BWV p02, §22 canonical for hymn, out78 for Lindenbaum):

- **Hallelujah p04 (was HEADS 0):** requested 71 → catalog 72.
  REACH HEADS 30,297 ms, **STAVES 14 HEADS 435** (was 0),
  `.mxl` 83,978 B, **231 notes / 184 pitched / 47 rests / 4 parts —
  identical counts to desktop** (desktop 84,130 B, 231/184/47/4).
  Deep diff vs desktop: **52** — 42 attrib (±1 `default-x` /
  `relative-x`, the §22 residual family), 10 text (2 filename +
  system/staff-distance ±1 + 1 rest `display-step` B vs C), **zero
  child-count / missing / extra diffs**. Structurally identical.
- **BWV 227 p02 (was HEADS 0):** requested 64 → catalog 64.
  REACH HEADS 32,698 ms, **STAVES 15 HEADS 787** (was 0),
  `.mxl` 129,094 B, **338 notes / 297 pitched / 41 rests / 5 parts —
  identical counts to desktop** (multi-page desktop: 297 pitched /
  338 total). Deep diff writer-vs-writer (desktop harness
  `desktop-bwv227-p02-noocr81.musicxml`, 128,647 B, 338/297/41):
  **11** — 2 filename + 4 child-count (2 notes missing
  tie+accidental+stem+notations in P3 m6/m7, 2 measures missing
  backup/forward in P5/P7 m9) + 5 text. **Zero ±1 attrib diffs** —
  the exact-64 template lands positions exactly. (Against the stock
  CLI `.mxl` export the count is 15, the extra 4 being the known
  exporter-artifact encoding block — writer-vs-writer is the clean
  number.)
- **Hymn (no regression):** requested 92 → catalog 92, HEADS 306,
  `.mxl` 44,105 B, **byte-identical to the §22 canonical file**.
- **Hallelujah p01 (documented tradeoff):** requested 72 → catalog
  72 (was 80). HEADS 630, `.mxl` 105,254 B, counts **275 / 217 /
  58 rests / 13 beams / 22 slurs / 2 ties — identical to out80 and
  to desktop** (desktop ties 4, the known §25.5 difference).
  Deep diff vs the SAME desktop reference: **93, was 8 on out80**
  (reproduced: out80 vs this reference = 8). Of the listed diffs:
  51 attrib (nearly all ±1 `default-x`/`relative-x`), 3 text,
  6 child-count — 2 are the pre-existing P4 m8 tie diffs also present
  in out80, 4 are new in P5 m9 (two rests losing
  time-modification+notations, two pitched notes gaining/losing
  time-modification/stem/notations — one measure's tuplet resolution,
  the §25.5 StackRhythm family). **No musical content changed** —
  the metric worsened because the exact-72 template shifts head boxes
  by ~1 px vs the 80-template, flipping many ±1-tenth roundings.
  The counts, which are the ground truth for "does it work", are
  unchanged. A 70 catalog (p01 → 70, diff 2) is a possible future
  refinement if the metric matters; not run in this round.
- **Lindenbaum (no regression):** `.mxl` 99,305 B, **byte-identical
  to out78**.

### §36.6 Variant B measured and rejected

Hypothesis: drop the 72 catalog, widen MAX_DIFF to 10, let 70/71/72
fall back to the 80-template (p01's proven regime) and save one
catalog. Built as full-out83 (gen_prerendered.py WANT [64,80,92,108],
MAX_DIFF 10.0; generated 908,505 B, 70,336 key points; round-trip
**96/96 PASS**; 3,058 classes, 28,728 methods, classes.wasm
13,965,666 B). But the nearest-pick does NOT do what the hypothesis
assumed: 71 is nearer 64 (diff 7) than 80 (diff 9), and 72 ties
64/80 at diff 8 (64 wins the tie, first in array order). So variant B
tests UNDERSIZE templates, not the oversize regime — and undersize
fails:

- **Hallelujah p04 → 64-template (diff 7):** HEADS 488, `.mxl`
  84,909 B, **235 notes / 188 pitched** vs desktop 231/184 —
  **+4 extra pitched notes** (variant A: exact).
- **Hallelujah p01 → 64-template (diff 8):** HEADS 673, `.mxl`
  103,302 B, **266 notes / 210 pitched / 56 rests** vs desktop
  275/217/58 — **−7 pitched notes** (variant A: exact).
- **Hymn → 92 (unchanged):** 44,105 B, byte-identical to the §22
  canonical — variant B does not affect the 92 pages.

Conclusion: oversize and undersize are NOT symmetric. An 11%
oversize kernel (80 for 72) matches desktop exactly on counts; an
11% undersize kernel miscounts in both directions (+4 on p04, −7 on
p01). MAX_DIFF 10 is rejected. Sources were restored to variant A
(`gen_prerendered.py` WANT [64,72,80,92,108], MAX_DIFF 8.0;
`PreRenderedTemplates.java` back to the 1,065,054-byte variant-A
file, saved copy at `phase42/PreRenderedTemplates-82.java`);
full-out82 remains the current build. Variant-B artefacts kept for
the record in `phase42/` (`wasm-*-noocr83.musicxml`,
`run-*-83.log`, `roundtrip-83.log`, `gen-prerendered-83.log`).

### §36.7 Coverage now, and what is left of the cliff

- Catalogs {64, 72, 80, 92, 108} cover [56..116] continuous — every
  one of the 37 multi-page pages (requests 64–92) is inside the
  window. The 16 HEADS-0 pages are accounted for: 12 BWV 227 pages
  at 64 (exact), Hallelujah p04/p05/p08 at 71 (→72, diff 1), p06 at
  70 (→72, diff 2). BWV 227 p01 (~65) → 64 (diff 1), predicted hit,
  not yet run — the multi-page re-run will cover it.
- Snow p5 at 140 remains uncovered at full 300 dpi; at the app's
  4096 cap it rescales to ~112 → catalog 108, diff 4.4, HIT. A 140
  catalog (covering [132,148]) is a possible future addition for
  full-resolution scans.
- The catalog is a Phase B pre-rendered approximation of desktop's
  exact-size templates. The p01 evidence (§36.5) shows the
  approximation is good on counts but can flip ±1-tenth roundings;
  that is the residual cost of the approach, not a defect to chase
  page by page.

### §36.8 Artefacts, builds, next steps

- Artefacts in `teavm-fork/phase42/`: DIAG42 logs
  (`diag42-*.log`, desktop + Wasm cps/sizer/headps), desktop
  references (`desktop-hallelujah-p01-noocr81.musicxml` 105,450 B,
  `desktop-hallelujah-p04-noocr81.musicxml` 84,130 B,
  `desktop-bwv227-p02-noocr81.musicxml` 128,647 B +
  `desktop-bwv227-p02-noocr81.log`), template dumps
  (`templates-64-72.json`, `templates-before-64-72.json`),
  round-trip logs (`roundtrip.log` 120/120, `roundtrip-83.log`
  96/96), build logs (`build82.log`, `full-build82-spike.log`,
  `build83.log`, `full-build83-spike.log`), verification runs
  (`run-verify82.sh`, `run-verify83.sh`, `run-*-82.log`,
  `run-*-83.log`), produced `.mxl` (`wasm-*-noocr82.musicxml`,
  `wasm-*-noocr83.musicxml`), deep diffs
  (`compare-deep-hallelujah-p04-82.txt`,
  `compare-deep-hallelujah-p01-82.txt`,
  `compare-deep-hallelujah-p01-out80.txt`,
  `compare-deep-bwv227-p02-82.txt` vs stock CLI export,
  `compare-deep-bwv227-p02-82-ww.txt` writer-vs-writer),
  `PreRenderedTemplates-82.java` (variant-A generated source).
- Builds: `full-out81/` (DIAG42 diagnostic), `full-out82/`
  (current, widened catalog + DIAG42 prints still in), `full-out83/`
  (variant B, rejected — do not use).
- Next named: the multi-page re-run under full-out82 (the full-out63
  results are stale three ways now — CME pages fixed §33, p06/p09
  `%f` fixed §35, catalog cliff fixed §36). After that: multi-score
  export limitation, StackRhythm divergence (§25.5), HeadHeadRelation
  SIGraph symptom (§26.12), clean build (strip DIAG14/16/17/18/19/
  20/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42),
  real-browser Chrome run, upstream filings (#272, #21244, §11, §19
  TColor, §27 hypot, §33 retainAll, §35 TFormatter). CheerpJ 5
  remains the only working option.

## §37 — Multi-score export: NOT a runner bug — TeavmMain never set the app's indentations=false; contained fix + per-score export (2026-11-10)

### §37.0 Verdict: (a) contained fix applied and verified

The six BWV 227 pages that saved only the last score (920 of the 937-note
BWV shortfall in the full-out82 multi-page re-run) now export whole:
all six are single-score under full-out84, with six-page totals of
1,809 pitched / 2,039 notes vs desktop 1,808 / 2,039 (+1). The
"runner saves only the last score" (§33.7) was the proximate cause;
the root cause was one missing Audiveris constant in TeavmMain. The
export path is also hardened to emit one file per score, matching
desktop's `BOOK.mvt#.ext` behaviour, so a genuine multi-score book can
never silently drop a score again. No TeaVM defect in this round, so
nothing to file upstream for §37.

### §37.1 DIAG43 — the symptom as recorded vs what it actually was

The multi-page re-run recorded the six pages as "two-score page, last
score only" (e.g. p01: desktop 21 measures/part, Wasm 8) and §33.7
recorded the mechanism as "TeavmMain loops `for (Score score :
book.getScores())` ... `setMxlB64` is overwritten per score — the
runner saves only the LAST score". That is true but incomplete: it
never asked why the Wasm book had two scores when the desktop book had
one. DIAG43 asked it. The Wasm p01 log (full-out82) shows:

```
SCORE parts=4 measures=13
SCORE parts=5 measures=8
MXL len=84753 ... / MXL len=54100 ...
```

while the desktop p01 log (same page, app constants) shows one score:

```
Created scores: [{Score 1}]
```

5 parts, 21 measures/part, 345 notes. Same 3 systems, same 13 staves
on both sides. The split is a Wasm-side divergence in score creation,
not an export artefact.

### §37.2 The mechanism — indentation detection splits the book

Read from the stock Audiveris sources in
`~/workspace/score-reader-spikes/repo/.work/audiveris/`:

- `Book.createScores` (`Book.java:529`): a new `Score` is started
  whenever `pageRef.isMovementStart()`.
- `SystemManager.allocatePages` (`SystemManager.java:144`): a system
  whose `isIndented()` is true starts a new `PageRef` with
  `movementStart=true` — "We have a movement start ... Sheet middle
  => Score break".
- `SystemManager.checkIndentations` (`SystemManager.java:172`): runs
  only `if (sheet.getStub().getProcessingSwitches().getValue(
  ProcessingSwitch.indentations))` — i.e. only when the switch is true.
  It runs in the GRID/layout phase (`SystemManager.java:685`), before
  `allocatePages()`.

The Wasm p01 log has the smoking gun, twice:

```
INFO [org.audiveris.omr.sheet.SystemManager] Indentation detected for system #1
INFO [org.audiveris.omr.sheet.SystemManager] Indentation detected for system #3
```

System #1's indentation is harmless (first page of the sheet); system
#3's is the mid-sheet movement start that creates the second score
(13 + 8 = 21 measures). All six pages show the same pattern (p01 #1/#3,
p06 #3, p07 #3, p08 #3, p11 #2, p24 #2). The desktop p01 log has zero
"Indentation detected" lines — because the desktop harness runs with
`-constant org.audiveris.omr.sheet.ProcessingSwitches.indentations=false`
(`run_photo_spikes.py` `AUD_CONSTANTS`), and the shipped app passes the
same constant (`score-reader/app/reader.js:260`). **TeavmMain set none
of the four app constants** — no `indentations`, no
`LinesRetriever.maxSlopeDiff`, no `Main.sheetStepTimeOut`, no
`TesseractOCR.useOCR` (the last is effectively covered by the BrowserOCR
replacement of native Tesseract). The switch therefore defaulted to
true under Wasm, and the stock indentation feature fired.

### §37.3 DIAG43 control — desktop with the switch ON splits identically

Control: desktop Audiveris 5.11 on `bwv227/p01.png` with the same
`AUD_CONSTANTS` minus `indentations=false` (39.1 s, `/tmp/ctrl-p01-out/`).
Result:

```
Indentation detected for system #1
Indentation detected for system #3
Created scores: [{Score 1}, {Score 2}]
Score p01.mvt1 exported to /tmp/ctrl-p01-out/p01.mvt1.mxl
Score p01.mvt2 exported to /tmp/ctrl-p01-out/p01.mvt2.mxl
```

- `p01.mvt1.mxl`: 4 parts, 52 measures (13/part), 191 notes.
- `p01.mvt2.mxl`: 5 parts, 40 measures (8/part), 141 notes.

That is the Wasm split 1:1 (Wasm: parts=4 measures=13, MXL len=84753;
parts=5 measures=8, MXL len=54100; the saved Wasm .mxl was 111 pitched /
141 total — exactly mvt2). The detection is stock Audiveris behaviour,
identical on both sides; the only divergence was the switch value.

Control caveat, recorded honestly: the filter that removed the
indentations constant from the flat `AUD_CONSTANTS` list left a stray
`-constant` token (the value was removed, its flag was not), so the
invocation was `-constant -constant maxSlopeDiff=0.05` at that point.
The log shows no error from it, the two "Indentation detected" lines
and the two-score creation are the stock outcome, and the split depends
only on the indentations switch (maxSlopeDiff affects GRID line
retrieval, not indentation detection) — but the control was not a
byte-clean rerun of the harness invocation, only a switch-ON rerun.

### §37.4 Desktop export behaviour — fix shape (a)

`Book.export` (`Book.java:569`): "If we don't use opus and the book
contains a single score, it is exported as `BOOK.ext` ... If we don't
use opus and the book contains several scores, it is exported as several
`BOOK.mvt#.ext` files, where `#` stands for the movement number".
The control run confirms it (`p01.mvt1.mxl`, `p01.mvt2.mxl`). Fix shape
(a) — one .mxl per score — is therefore the desktop behaviour; shape
(b) (concatenate into a single file) would not match desktop and would
produce a file no MusicXML reader expects (two `<score-partwise>`
documents). The shipped app already offers `score.mxl` or per-movement
`.mxl`, so per-score files slot straight into it.

### §37.5 The fix — ROUND 43

Two parts, both in the spike tree (no Audiveris source changed):

1. **The switch (root cause).** `teavm/entry/src/teavm/TeavmMain.java`,
   right after the stub is created and the OCR language is set (and
   before `reachStep(HEADS)` — `checkIndentations` runs in GRID, so
   this is early enough):
   ```java
   stub.getProcessingSwitches().getParam(
           org.audiveris.omr.sheet.ProcessingSwitch.indentations).setSpecific(Boolean.FALSE);
   ```
   Same `Param.setSpecific` mechanism the OCR language uses on the line
   above it; `INDENTATIONS false` is printed so the log proves it took.
   This is the app's own constant, not a new behaviour: the shipped app
   and every desktop comparison in this investigation run with it off.

2. **The export path (hardening).** `TeavmMain` now accumulates one
   base64 string per score and publishes `__mxlB64List` (a JSON array;
   base64 has no JSON-special characters, so plain concatenation is
   safe) alongside `__mxlB64`, which now carries the FIRST score
   (movement 1) instead of the last — for old runners. `MXL count=N`
   is printed. New shared helper `teavm-fork/save-mxl.mjs`
   (`saveMxl(out, b64List)` + `readMxlList()`): one score writes exactly
   `out` (unchanged behaviour); N>1 writes `out` as `<stem>.mvt1<ext>`,
   `<stem>.mvt2<ext>`, ... — desktop's naming exactly. `readMxlList`
   prefers `__mxlB64List` and falls back to legacy `__mxlB64` (builds
   before full-out84 set only that, to the last score). Updated runners:
   `run-fullout-noocr.mjs`, `run-fullout-ocr.mjs` (phase-2 tail),
   `run-fullout-mxl.mjs`. `run-fullout.mjs` does not save .mxl and is
   untouched. Node unit test `phase43/save-mxl-test.mjs`: **13/13 PASS**
   (N=1 exact file, N=2 names + content round-trip + lyric count,
   empty/null list writes nothing, list-wins / legacy-fallback /
   neither-null).

### §37.6 Verification — full-out84

Build: `./build.sh` + canonical Spike command, 0 problems, 3,058
classes, 28,754 methods (+1, the new `@JSBody`), `classes.wasm`
14,354,417 B (+5,287 B vs out82). `phase43/build84.log`,
`phase43/full-build84-spike.log`.

| page | out82 (2 scores) | out84 | desktop |
|---|---|---|---|
| BWV 227 p01 | 111/141 (score 2 only) | **301/344, 5 parts × 21** | 301/345 |
| BWV 227 p06 | 82/91 (score 2 only) | **245/267, 5 parts × 13** | 245/267 |
| BWV 227 p07 | 125/127 (score 2 only) | **304/338** | 303/337 |
| BWV 227 p08 | 181/197 (score 2 only) | **321/366** | 321/366 |
| BWV 227 p11 | 198/219 (score 2 only) | **337/378** | 337/378 |
| BWV 227 p24 | 191/201 (score 2 only) | **301/346** | 301/346 |
| **six-page total** | | **1,809 / 2,039** | **1,808 / 2,039** |

All six pages: one `SCORE` line each, `MXL count=1`, zero
"Indentation detected" lines in any log. The 920-note shortfall is
gone: the six-page delta is **+1 pitched note** (p07 has one extra
pitched note; p01 is one rest short, 43 vs 44).

BWV p01 deep diff vs the desktop batch `.mxl`
(`phase43/compare-deep-bwv227-p01-84.txt`, full 162, `phase22/compare_deep.py`):
139 × ±1-tenth position roundings (the §36 family), 3 ×
filename/encoding (writer-vs-writer, known), 8 × child-count (mostly
extra/missing tie/slur/accidental notations, e.g. Wasm adds a tie +
notations on two P5 m3 notes, drops a slur on P5 m7/m9), 4 × text
(duration 18→16 in P4 m12; duration 4→2 + quarter→eighth in P6 m12;
rest display-step D vs C — the one missing rest), 8 × other attrib
(slur bezier values differing by >1). Zero structural diffs:
parts, measures/part, and pitched counts are identical. The rhythm
residuals are the known §25.5 StackRhythm family, not this fix.

No regression (all byte-identical to their references):
- Hymn no-OCR: 44,105 B, byte-identical to the §22 canonical
  (`wasm-hymn.musicxml`).
- Hallelujah p01 no-OCR: 105,254 B, byte-identical to the out82
  multi-page file. (Note: the §30 figure was 105,118 B; out82 already
  produced 105,254 B — the change predates this round and is the §36
  catalog tradeoff, not §37.)
- Lindenbaum no-OCR: 99,305 B, byte-identical to the out78 (§34)
  reference (223 notes).

Residual, recorded honestly: there is still no end-to-end N>1 Wasm
run — with `indentations=false` no multi-score book occurs anywhere
in the test set, so the `__mxlB64List` multi-file path is exercised
only by the Node unit test (13/13) and the N=1 live path (the list is
set and read on every run). A genuine multi-movement page with
indentations on would be needed to exercise it live, and the app never
produces one.

### §37.7 Open parity note — the other three app constants

TeavmMain still does not set the other three constants the shipped app
passes (`reader.js:257-263`): `LinesRetriever.maxSlopeDiff=0.05`,
`Main.sheetStepTimeOut=3600`, and `TesseractOCR.useOCR=false` (the last
is effectively covered: native Tesseract is replaced by BrowserOCR in
the Wasm build). No divergence from them has been observed on any
reference page (every desktop comparison in §§22-36 ran with
maxSlopeDiff=0.05 on desktop and the default under Wasm, and matched),
but they are a known parity gap. Deliberately NOT changed in this round:
`maxSlopeDiff` touches GRID line retrieval and could move results, so it
needs its own verification round; `sheetStepTimeOut` is a timeout only
(no step has come near it — longest single step observed is ~2 s, longest
page total ~124 s). Flagged for the clean build.

### §37.8 Artefacts

- `teavm/entry/src/teavm/TeavmMain.java` — ROUND 43 edits (switch +
  list export); `teavm-fork/save-mxl.mjs` (new); runners updated
  (`run-fullout-noocr.mjs`, `run-fullout-ocr.mjs`,
  `run-fullout-mxl.mjs`).
- `phase43/` — `save-mxl-test.mjs` (13/13) + `save-mxl-test-out/`,
  `build84.log`, `full-build84-spike.log`, verification runs
  (`run-bwv227-p01/p06/p07/p08/p11/p24-84.log`,
  `run-hymn84.log`, `run-hallelujah-p01-84.log`,
  `run-lindenbaum84.log`), produced `.mxl` files
  (`wasm-bwv227-p01/p06/p07/p08/p11/p24-noocr84.musicxml`,
  `wasm-hymn-noocr84.musicxml`,
  `wasm-hallelujah-p01-noocr84.musicxml`,
  `wasm-lindenbaum-noocr84.musicxml`), `compare-deep-bwv227-p01-84.txt`
  (full 162), `run-compare-full.py`, `desk-p01/` (desktop reference).
- Desktop control: `/tmp/ctrl-p01-out/` (`p01.mvt1.mxl`,
  `p01.mvt2.mxl`, log) — ephemeral, not in the spike tree.
- Builds: `full-out84/` (current, switch + list export + DIAG prints
  still in). `full-out82/` remains the last pre-§37 build.
- Next named: StackRhythm divergence (§25.5) is now the biggest
  remaining recognition gap (it accounts for the p01 rhythm residuals
  above and the Hallelujah p01 deep-diff growth); after that:
  HeadHeadRelation SIGraph symptom (§26.12), clean build (strip DIAG
  prints incl. DIAG43), real-browser Chrome run, upstream filings
  (#272, #21244, §11, §19 TColor, §27 hypot, §33 retainAll, §35
  TFormatter). Nothing to file for §37 (no TeaVM defect; the split is
  stock Audiveris behaviour, the export change is our code).

## §38 — StackRhythm divergence (DIAG44): localised to two upstream SIG differences; StackRhythm itself is identical — verdict (c) inconclusive, localised (2026-11-10)

### §38.0 Verdict

**(c) inconclusive, localised — no contained fix, no TeaVM defect.**
DIAG44 pins both remaining Hallelujah rhythm divergences to concrete
upstream SIG differences and proves StackRhythm/MeasureRhythm themselves
do not diverge, but the root cause of either upstream difference is not
identified, so there is nothing to fix and no defect to repro. Stop per
the task rule; the next diagnostic (DIAG45) is named in §38.7.

### §38.1 Re-establishment on full-out84 — the §25.5 picture has changed

New comparator `teavm-fork/phase44/compare_rhythm.py` (per-part/per-measure
pitch/duration/type/tie/tuplet comparison, ignoring positions/dynamics/
slurs/lyrics) on the full-out84 references:

- **Hallelujah p01: exactly 2 of 56 measures differ in rhythm** (deep diff
  still 93). (1) **P2 m9: tie pair missing on Wasm** — desktop has A/4
  eighth tie=start + A/4 eighth tie=stop on notes 1–2; Wasm has the same
  notes, no ties. Slur elements are 22 = 22 in every part; tie elements
  4 vs 2, the difference entirely in P2 (2 vs 0); P3 has 2 tie elements
  on both sides. (2) **P3 m10: tuplet assignment differs** — desktop
  R:6 plain eighth at note[2], E:2 16th tuplet at note[4], R:6 plain at
  note[7]; Wasm R:4 tuplet eighth at note[2], E:3 plain 16th at note[4],
  R:4 tuplet at note[7].
- **The §25.5 six-measure split is GONE.** "No correct rhythm" sets are
  now identical on both sides — Hallelujah p01: only S2 #8 on both sides;
  the old Wasm-only failures S2 #5 / S3 #9 no longer occur. What §25.5
  described as a StackRhythm divergence has collapsed to the two measures
  above.
- **Lindenbaum: 0 of 24 measures differ in rhythm** (deep diff 10: 2
  filename + 8 × ±1). Its four "no correct rhythm" stacks (S1 #1, S1 #3,
  S2 #4, S2 #5) are identical on both sides — no divergence to diagnose
  there.
- Measure→system map (from `<print new-system>` in the desktop .mxl):
  system 1 = m1–m6, system 2 = m7–m10, system 3 = m11–m14. So P2 m9 →
  global stack S2 #7; P3 m10 → global stack S2 #8 — the "no correct
  rhythm" stack on both sides. The P2 m9 tie divergence is in a stack
  that does NOT log "no correct rhythm" on either side; the P3 m10
  tuplet divergence is in the stack that fails on both sides yet still
  resolves differently (already noted in §25.5).

### §38.2 DIAG44 design and build (ROUND 44, full-out85)

Four print sites, all print-only, same patched files both sides
(`SlurInter.java`, `TupletsBuilder.java`, `StackRhythm.java`,
`MeasureRhythm.java` in `teavm/patched/make_patches.py`, ROUND 44):

- **DIAG44A** in `SlurInter.checkStaffTie` (LINKS doEpilog, runs for EVERY
  slur in every system): slur id, left/right head (id, step/octave, staff
  id, center), sameStaff, compatible, spaceClear, final tie value
  (components computed into locals first, preserving the original
  short-circuit semantics; `isSpaceClear` is null-safe; `getBounds()` /
  `getCenter()` are never called on the slur itself — null curve would
  trap, §28 lesson).
- **DIAG44B** in `TupletsBuilder`: candidate order per tuplet sign
  (`getChordsAround`), collector outcome at all three return points
  (`getEmbracedChords`), linked chord ids (`linkStackTuplets`).
  `ProcessingSwitch.implicitTuplets` defaults to **false**, so the
  MeasureRhythm `findImplicitTuplets` / `analyzeTimes` 3/2 paths are OFF
  — the P3 m10 tuplets are explicit `TupletInter` signs, linked by
  `TupletsBuilder` (called from `SymbolsLinker.java:320`, SYMBOLS step).
- **DIAG44C** in `StackRhythm.doProcess` (per-measure outcome) and
  `MeasureRhythm.finalCheck` (chords lacking voice/timeOffset — id, voice,
  timeOffset only, no `getDuration()`/`getBounds()` calls, to avoid trap
  risk).

Build **full-out85** (0 problems, 3,058 classes, 28,754 methods —
same counts as out84). Side-effect-free, verified both sides:
Wasm Hallelujah .mxl byte-identical to out84, Wasm Lindenbaum .mxl
byte-identical to out84; desktop Hallelujah .mxl deep diff 2 vs the
phase42 reference (input-path string only); desktop Lindenbaum .mxl
deep diff 0 vs the phase40 reference. DIAG44 line counts: Hallelujah
204 each side; Lindenbaum 116 each side.

### §38.3 Divergence A — the P2 m9 tie: the slur inter is absent from the Wasm SIG

`checkStaffTie` calls: **desktop 13, Wasm 12**. The one missing line is
exactly the P2 m9 tie:

- Desktop: `DIAG44 tie slur#… left=#… A4 staff#… @java.awt.Point[x=1273,y=1697] right=#… A4 staff#… @java.awt.Point[x=1340,y=1697] sameStaff=true compatible=true spaceClear=true tie=true`
- Wasm: no line for it. The other 12 tie lines match (modulo 1 px
  head-center jitter on three lines — 396→395, 474→473, 448→447 — the
  §18 family).

LinksStep calls `checkStaffTie` for EVERY SlurInter in every system at
LINKS doEpilog, so a missing line means the slur is **absent from the
Wasm SIG at LINKS time**. This is not a tie-classification difference —
the classification inputs are never computed because the slur is not
there (and the early tie flag in `ClumpPruner.java:195-203`, CURVES,
never runs for it either). The two A4 eighth heads exist on both sides
(same notes in the .mxl); only the slur connecting them is missing.

Upstream cause NOT localised: the slur is either never created in CURVES
(`SlursBuilder`) or pruned before LINKS. No DIAG44 print covers
`SlursBuilder`. Nothing in the .mxl counts distinguishes the two (slur
elements 22 = 22 in every part — the tie-slur is a tie, not a slur
notation, so its absence costs exactly the 2 tie elements).

### §38.4 Divergence B — the P3 m10 tuplet: Wasm's collector skips the 16th chord by the staff check

Tuplet sign at **(2067,1970)**, system 2, measure 10, staff 7 (tenor).
Desktop collector dump (from the `collector.dump()` INFO lines, present
in the desktop log only — see §38.4.4):

- Desktop: base **1/16**, embraces 2 chords —
  `HeadChordInter#6867 staff:7 dur:1/16` + `HeadChordInter#6869 staff:7
  dur:1/8` — total 3/16 = expectedTotal → OK.
- Wasm: base **1/8**, embraces 3 chords — `[9612, 6292, 9616]`
  (6292 ≡ 6869, the eighth head; 9612/9616 are rests) — total 3/8 →
  OK.

#### §38.4.1 Candidate order is identical

Candidate lists for this tuplet, position by position: desktop
`[6869, 6890, 6868, 6891, 6889, 6867, 10317, 10318, 6888, 6866, 6892,
6870, 10313, 10314, 6865, 6887, 6864, 6886]` (18 ids), Wasm `[6292,
6313, 6291, 6314, 6290, 6312, 9616, 9617, 6289, 6311, 6315, 6293, 9612,
9613, 6288, 6310, 6309, 6287]` (18 ids). The id→chord mapping is a
constant offset within each id class (68xx heads −577, 10xxx rests
−701 — allocation-order difference, §34 note); the relative order is
identical. The ByEuclidean sort (`GeoUtil.ptDistanceSq` on chord
bounds) does NOT diverge. The 16th chord (6312 ≡ 6867) is present in
Wasm's candidate list at position 6 — it is there, and never included.

#### §38.4.2 The skip is the staff check — proved by the collector's arithmetic

The `getEmbracedChords` loop has only two ways to skip a candidate:
`staff != targetStaff` (continue) or `include()` being a no-op because
the chord is already in the set (added as a beam sibling). The second
is excluded by the status machine:

- If 6312 had been added as a beam sibling of 6292, the base would
  have dropped to 1/16 and the total would have reached 3/16 at the
  first include (OK with [6292, 6312]) — or, if the sign were outside
  the abscissa range, OUTSIDE → Fail. Wasm's actual outcome is OK 3/8
  with three eighths, so 6312 was not a sibling.
- If 6312 had been included on its own iteration (position 6), the
  base would have dropped to 1/16 and the next rest (9616, 1/8) would
  have pushed the total to 5/16 > 3/16 → TOO_LONG → Fail. That did
  not happen either.

Therefore: **under Wasm, `6312.getTopStaff() != targetStaff` (staff 7),
while on desktop `6867.getTopStaff() == 7`.** The 16th chord's top staff
differs under Wasm.

#### §38.4.3 What is NOT proven

Why the top staff differs is unproven. Candidates, in no order:
(a) a 1 px head-center difference near a staff boundary (the §18
jitter family is exactly this magnitude, and the 16th is a ledger-line
note); (b) an extra head in the chord under Wasm, pulling its top
staff up a staff; (c) a `getTopStaff()` behaviour difference. DIAG44
prints no Wasm-side staff/duration data for that chord, so none of
these can be distinguished. No fix is justified on this evidence.

#### §38.4.4 A second tuplet with the same signature — benign

Tuplet @ **(550,1781)**, system 2, measure 7: desktop fails OUTSIDE at
total 3/8 vs 3/8 (base 1/8 — the eighth chords are included); Wasm
fails exhausted at total 1/2 vs 3/4 (base 1/4 — the eighth chords are
never included). Same signature as §38.4.2 (shortest chords skipped
on Wasm). But **both sides fail to link this tuplet** (no links either
side; the sign is removed on both), so the .mxl is unaffected —
compare_rhythm shows m7 identical. Benign path divergence, same
family, recorded not chased.

#### §38.4.5 `lookupLinks` runs ~3× per tuplet sign — identical both sides

86–87 Ok/Fail prints vs 28 Cand/Link lines per side. The pattern per
sign is Ok (first, operative collection), Fail, Fail (exhausted
re-runs), Ok (same collection again), Link. The re-runs come via
`TupletInter.searchLinks` (`TupletInter.java:280`) after relations
exist; the first Ok and the last Ok are identical per tuplet on each
side, and the pattern reproduces identically on both sides. It does
not affect any outcome. (The collector `dump()` INFO lines are present
in the desktop log only; the Wasm runner does not surface multi-line
logger.info messages — a harness gap for the next round, §38.7.)

### §38.5 DIAG44C — StackRhythm/MeasureRhythm do NOT diverge

- **Hallelujah:** 48 rhythm lines each side, identical. Exactly one
  `ok=false` on both: `MeasureStack#8 Measure{#8P1}` — the S2 #8
  stack. One `rhythmNoTime` line each side: `Measure{#8P1} chord
  Voice #2 timeOffset=null` — the §34 null-offset chord, identical
  (inter ids differ only: 6827 desktop / 6250 Wasm).
- **Lindenbaum:** "no correct rhythm" 4× on both sides (S1 #1, S1 #3,
  S2 #4, S2 #5); 4 `ok=false` on both; `rhythmNoTime` lines identical
  (#1P2 ×3, #3P2 ×3 — the §34 family). The only DIAG44 differences on
  Lindenbaum are two tuplet signs processed in swapped order (set
  iteration order differs — allocation-dependent HashSet order;
  outcomes identical) and 1 px center jitter (tuplet y 1799→1800,
  head centers ±1 px — §18 family). Tie decisions identical,
  including one `tie=true` on both sides.

Conclusion: the §25.5 framing is refined. **The rhythm step faithfully
processes different inputs; the divergence is upstream, in the SIG:**
a slur missing at LINKS (CURVES, §38.3) and a tuplet linked to
different chords (SYMBOLS, §38.4). StackRhythm itself is not a
divergence source on either page.

### §38.6 Ruled out

- TEXTS/OCR (no-OCR both sides throughout).
- MeasureRhythm/StackRhythm logic (§38.5 — identical outcomes,
  identical failure sets).
- Tuplet candidate order (§38.4.1 — identical position-by-position).
- Beam-sibling inclusion as the mechanism for divergence B (§38.4.2 —
  excluded by the collector's arithmetic).
- `implicitTuplets` (defaults false; the P3 m10 tuplets are explicit
  `TupletInter` signs).
- The (550,1781) tuplet as a .mxl cause (§38.4.4 — both sides fail it).
- A TeaVM defect localised to a single small operation — none found;
  no minimal repro exists. The divergences live in SIG contents
  (head staff assignment / slur existence), i.e. upstream of the
  decision code DIAG44 instruments, at the 1 px level where the two
  sides are already known to differ (§18 jitter, §20 4-pixel
  NO_STAFF residual).
- Head-center 1 px jitter as a *proven* cause — present, right
  magnitude, but the causal link to the staff flip is unproven.

### §38.7 Next diagnostic — DIAG45 (named, not started)

Two parts, both print-only, same patched files both sides:

- **DIAG45A — tuplet loop:** in `getEmbracedChords`, per candidate
  print chord id, isRest, topStaff id, head count + each head's staff
  and center y, `durationSansTuplet`, and the include/skip reason.
  Directly answers why 6312's top staff differs (staff-boundary
  head? extra head? `getTopStaff` behaviour?). Also route the
  collector `dump()` through `System.out` (single-line prints) so the
  Wasm side shows it — the logger.info dump is invisible under Wasm.
- **DIAG45B — slur creation:** in `SlursBuilder`, a trace of seed
  arcs / extension / weed decisions for arcs near (1273–1340, 1697)
  in system 2 (or a dump of every `SlurInter` created in CURVES per
  system with bounds). Directly answers whether the P2 m9 slur is
  never created or pruned before LINKS.

### §38.8 Artefacts

- `teavm/patched/make_patches.py` — ROUND 44 (DIAG44A/B/C).
- `teavm-fork/phase44/` — `compare_rhythm.py` (new), `build85.log`,
  `full-build85-spike.log`, `desktop-compile-diag44.log`,
  `run-hallelujah-p01-85.log`, `desktop-hallelujah-p01-noocr85.log`,
  `diag44-{desktop,wasm}-hallelujah.txt` + `-norm.txt`,
  `wasm-hallelujah-p01-noocr85.musicxml`,
  `desktop-hallelujah-p01-noocr85.musicxml`, `run-lindenbaum85.log`,
  `desktop-lindenbaum-noocr85.log`,
  `diag44-{desktop,wasm}-lindenbaum.txt`,
  `wasm-lindenbaum-noocr85.musicxml`,
  `desktop-lindenbaum-noocr85.musicxml`.
- Builds: `full-out85/` (current, diagnostic — DIAG44 prints in).
  `full-out84/` remains the last non-diagnostic build.
- Nothing to file for §38 (no TeaVM defect). Next named: DIAG45
  (§38.7); after that: HeadHeadRelation SIGraph symptom (§26.12),
  clean build (strip DIAG prints incl. DIAG44), real-browser Chrome
  run, upstream filings (#272, #21244, §11, §19 TColor, §27 hypot,
  §33 retainAll, §35 TFormatter).

## §39 — StackRhythm DIAG45: both divergences localised to 1px knife-edges in Audiveris's own thresholds; no contained fix, no TeaVM defect — verdict (c) inconclusive, localised (2026-11-10)

### §39.0 Verdict

(c) inconclusive, localised. DIAG45 (full-out86, ROUND 45) measures both
§38 divergences to their exact numeric inputs and refines the mechanism
of each — but neither yields a contained fix or a TeaVM defect, so this
round stops here per the task rule. The next diagnostic (DIAG46) is named
in §39.6.

- **Divergence A (P2 m9 tie): the purge gate's inputs are now measured
  exactly.** The tie-slur arc is created identically on both sides; it is
  `purgeStaffLines` in CURVES that kills it under Wasm. Desktop keeps
  candidates 270/271/272 at incidence **15.945°** (just above the 15°
  threshold); Wasm purges 264/265/266 at incidence **14.036°** (just
  below it). The two inputs differ by exactly 1 px each: staff-line Y
  1656.0 (desktop) vs 1657.0 (Wasm), and end-tangent dx 7 (desktop) vs 8
  (Wasm). No contained fix: moving the 15° threshold or the tangent
  length is an Audiveris behaviour change, not desktop-neutral; the root
  (why the line fit / arc points differ by 1 px) is upstream of the gate.
- **Divergence B (P3 m10 tuplet): the §38 mechanism is refined — the
  staff-7 16th is removed by `filterChordsOnAbscissa`, not by the staff
  check.** The staff check only ever sees the staff-8 16th (6312), which
  it correctly skips. The filter's only differing decision is the
  6902/6880 pair: desktop discards 6902 and keeps the staff-7 16th 6880;
  Wasm discards 6290 (≡ 6880) and keeps 6312 (≡ 6902). The ByEuclidean
  candidate order also swaps at positions 5/6. But the filter's numeric
  inputs (chord bounds/centers, vertical distances to the sign) were NOT
  measured in this round — DIAG45A shows only post-filter iteration — so
  the exact 1 px input that flips the filter is unproven. No contained
  fix: changing the filter's tie-break or the sort is an Audiveris
  behaviour change.
- **Correction to §38.4.1:** the candidate order is NOT identical
  position-by-position (positions 5/6 are swapped), and desktop inter
  ids shift between runs (the (2067,1970) tuplet is #10235 in §38,
  #10249 now — same input, byte-identical .mxl), so id-offset alignment
  is unreliable; content-based alignment (head positions, durations,
  staffs) is required. Wasm ids are deterministic (inline executor) and
  match §38 exactly (#9534).
- The benign (550,1781) tuplet confirms the same family a third way:
  `getTargetStaff` returns 6 on desktop, 7 under Wasm, because the
  first head-based candidate in the ByEuclidean order differs — again a
  ~1 px order flip at the top of the list. Both sides still fail to link
  it, so the .mxl is unaffected.
- No TeaVM defect was localised to a single small operation in this
  round. Both divergences are 1 px knife-edges in Audiveris's own
  thresholds (15° incidence, nearest-chord filtering), fed by the known
  §18 1 px jitter family in SIG geometry. Nothing to file for §39.

### §39.1 DIAG45 design and build (ROUND 45, full-out86)

Two print sites, all print-only, same patched files both sides
(`TupletsBuilder.java`, `SlursBuilder.java` in
`teavm/patched/make_patches.py`, ROUND 45):

- **DIAG45A** in `TupletsBuilder.getEmbracedChords` (SYMBOLS): target
  staff per tuplet sign (`getTargetStaff`); per-candidate
  `tupletCand2` — chord id, isRest, top staff, duration sans tuplet
  (null-safe), member list with each member's id/shape/staff id/center
  y (pure getters only); `tupletSkip` in the staff-check `continue`
  branch; `tupletDump` (status, base, expectedTotal, total, chord ids —
  accesses the nested `TupletCollector`'s private fields, legal from the
  enclosing class) at all three return points (isNotOk, isOk,
  exhausted). The collector `dump()` logger.info lines are invisible
  under Wasm, so the dump now also goes through `System.out`.
- **DIAG45B** in `SlursBuilder.purgeStaffLines` (CURVES): `diag45lineY`
  / `diag45toLine` hoisted out of the `!staff.isTablature()` block
  (the original `toLine` was block-scoped); `decision=keep-far` print
  inside the `|toLine| > maxStaffLineDy` gate; a `purge` values print
  after `Arc endPart = slur.getPartAt(end)` — id, end, lineY, toLine,
  maxDy, endPart shape (null-safe), tangent p1/p2, dx, dy,
  incidenceDeg, maxIncDeg. Tangent values are duplicated from below
  (pure getters, no side effects) with an empty-points guard
  (p1/p2 null → dx/dy/incidence NaN). Existing DIAG33
  PURGE-STAFFLINE prints already give the delete decisions; keep
  decisions (other than keep-far) are implied by a values print with no
  corresponding delete print.

Build **full-out86** (0 problems, 3,058 classes, 28,754 methods,
classes.wasm 14,372,166 B). Side-effect-free, verified both sides:
Wasm Hallelujah .mxl byte-identical to out85 (105,254 B); desktop
Hallelujah .mxl byte-identical to out85 (105,442 B); Wasm Lindenbaum
.mxl byte-identical to out78 (99,305 B). DIAG44 line counts unchanged:
204 each side. DIAG45 line counts: desktop 8,172, Wasm 7,286
(tupletTarget 86/87, tupletCand2 198/209, tupletSkip 10/18,
tupletDump 86/87, purge 7,792/6,885 — the per-site count differences
are the same call-count phenomenon as DIAG33's computeModel 228 vs
5,343, not new divergence).

Build incidents, recorded so the next round does not repeat them:

1. The first `build.sh` run failed at ROUND 45's third TupletsBuilder
   sub ("PATCH FAILED: not found" on the DIAG44-modified isNotOk
   block). Root cause: ROUND 45 used `copy_src` (pristine Audiveris
   source) for files an earlier round had already patched —
   TupletsBuilder (ROUND 44) and SlursBuilder (ROUND 29/30). The
   convention, visible in `read_out()` (make_patches.py:946) and used
   by every later round that builds on an earlier one, is to start from
   the previously-patched OUT file. Fixed: ROUND 45 now uses
   `read_out` for both files. **Any future round touching a file an
   earlier round patched must use `read_out`, not `copy_src`.**
2. `java` is not on PATH in a fresh shell in this VM; the JDK is at
   `repo/.work/jdk/jdk-25.0.5+8/bin` (build.sh sets `J` to it; the
   canonical Spike command needs the same prefix).

### §39.2 Divergence A — the P2 m9 tie: measured at the purge gate

The clump is the same one §28 mined from the DIAG33 logs (weed block
#433 desktop / #429 Wasm): five candidates, same grades both sides.
Desktop OUT [272, 271, 270, 273] (only 261 purged); Wasm OUT [267]
(255 purged the same way, plus 264/265/266). DIAG45B gives the exact
gate inputs (lineY from `staff.getClosestStaffLine(end).yAt(end.x)`,
maxDy = 3.4 both sides, maxIncidence = 15° both sides):

| id (desk/Wasm) | end | lineY | toLine | endPart | p1 | dx | dy | incidence | outcome |
|---|---|---|---|---|---|---|---|---|---|
| 261 / 255 | (1348,1656) | 1656.0 / 1657.0 | 0.0 / 1.0 | STAFF_ARC | (1341,1656) / (1340,1656) | 7 / 8 | 0 | 0.0° | purged (STAFF_ARC rule), both |
| 261 / 255 | (1290,1657) | 1656.0 / 1657.0 | -1.0 / 0.0 | STAFF_ARC | (1297,1656) / (1298,1656) | 7 / 8 | 1 | 8.13° / 7.13° | purged (STAFF_ARC rule), both |
| 272 / 266 | (1284,1658) | 1656.0 / 1657.0 | -2.0 / -1.0 | SHORT | (1291,1656) / (1292,1656) | 7 / 8 | 2 | **15.945°** / **14.036°** | desktop KEEP / Wasm PURGE (staff-line-incidence) |
| 271 / 265 | (1286,1658) | 1656.0 / 1657.0 | -2.0 / -1.0 | SHORT | (1293,1656) / (1294,1656) | 7 / 8 | 2 | **15.945°** / **14.036°** | desktop KEEP / Wasm PURGE |
| 270 / 264 | (1288,1658) | 1656.0 / 1657.0 | -2.0 / -1.0 | SHORT | (1295,1656) / (1296,1656) | 7 / 8 | 2 | **15.945°** / **14.036°** | desktop KEEP / Wasm PURGE |
| 273 / 267 | (1284,1653) | 1656.0 / 1657.0 | 3.0 / 4.0 | SHORT | (1287,1658) / — | 3 / — | 5 / — | 59.04° / — | desktop KEEP (incidence) / Wasm keep-far; same outcome |

Confirmed by the DIAG33 delete lines: desktop deletes only id=261
(STAFF_ARC, both ends); Wasm deletes id=255 (STAFF_ARC, both ends)
**plus** id=266, id=265, id=264, each
`reason=staff-line-incidence end=(1284|1286|1288,1658)`.

Mechanism, measured: the incidence is `atan(dy/dx)` over the last
`tangentLength` (≈ 0.5 interline ≈ 8 px) points of the curve end.
Desktop: `atan(2/7) = 15.945°` — just above the 15° threshold, so the
candidate survives. Wasm: `atan(2/8) = 14.036°` — just below it, so
`purgeStaffLines` deletes it. The two inputs differ by exactly 1 px
each: the staff-line Y (1656.0 vs 1657.0 — the fitted line itself
differs by a full pixel) and the tangent start point (p1 x 1291 vs
1292 — the arc's point list differs by 1 px at that end, the §28
1–4 px arc-length jitter family). Either 1 px difference alone flips
the gate: dy=2 over dx=7 keeps, over dx=8 purges.

No contained fix at this level. The gate is doing exactly what
Audiveris specifies; the inputs are 1 px off. Changing `maxIncidence`
(15°) or `tangentLength` would move the knife edge, not remove it,
and would change desktop results on other pages — not desktop-neutral.
The root (why the staff-line fit differs by 1 px, why the arc points
differ by 1 px) is upstream of `purgeStaffLines` — that is DIAG46A
(§39.6). The §28 conclusion stands: the slur residual is upstream of
SlursBuilder's decision logic, in skeleton/arc geometry; the residual
skeleton difference after §31/§32 (+37/+97 fore px under Wasm) is the
prime suspect for the line-fit shift.

### §39.3 Divergence B — the P3 m10 tuplet: the filter, not the staff check

The tuplet sign is at (2067,1970), system 2, measure 10, staff 7
(tenor). Operative (first) `getEmbracedChords` call on each side:

**Desktop — tuplet#10249, targetStaff=7:**

- chord#6882 rest=false topStaff=7 dur=1/8 members=[#2978:NOTEHEAD_BLACK:staff=7@y=1873] → included
- chord#6903 rest=false topStaff=8 dur=1/8 → SKIPPED (staff-mismatch)
- chord#6880 rest=false topStaff=7 dur=**1/16** members=[#2945:NOTEHEAD_BLACK:staff=7@y=1857] → included
- dump: `status=OK base=1/16 expectedTotal=3/16 total=3/16 chords=[6880, 6882]`

**Wasm — tuplet#9534, targetStaff=7:**

- chord#6292 rest=false topStaff=7 dur=1/8 members=[#3133:NOTEHEAD_BLACK:staff=7@y=1874] → included (≡ 6882, 1 px head-center jitter)
- chord#6313 rest=false topStaff=8 dur=1/8 → SKIPPED (staff-mismatch) (≡ 6903)
- chord#6312 rest=false topStaff=**8** dur=**1/16** members=[#3401:NOTEHEAD_BLACK:staff=**8**@y=2034] → SKIPPED (staff-mismatch)
- chord#9616 rest=true topStaff=7 dur=1/8 → included
- chord#6311 rest=false topStaff=8 dur=1/16 → SKIPPED (staff-mismatch)
- chord#6315 rest=false topStaff=8 dur=1/8 → SKIPPED (staff-mismatch)
- chord#9612 rest=true topStaff=7 dur=1/8 → included
- dump: `status=OK base=1/8 expectedTotal=3/8 total=3/8 chords=[9612, 6292, 9616]`

So §38's hypothesis is confirmed in outcome but refined in mechanism.
The 16th chord that desktop includes (6880, head @ y=1857, staff 7)
is NOT the chord Wasm skips at the staff check (6312, head @ y=2034,
staff 8) — they are different chords. Under Wasm, the counterpart of
6880 is chord#6290, and it never reaches the staff check at all: it is
removed by `filterChordsOnAbscissa` before the loop. Proof from the
iteration order: `getEmbracedChords` calls
`filterChordsOnAbscissa(tuplet, candidates)` first (mutating the list),
then iterates it, and DIAG45A prints every visited candidate. The
Wasm DIAG44 candidate list is
`[6292, 6313, 6291, 6314, 6290, 6312, 9616, 9617, 6289, 6311, 6315,
6293, 9612, 9613, 6288, 6310, 6309, 6287]`; the operative call visits
`[6292, 6313, 6312, 9616, 6311, 6315, 9612]` — 6291, 6314 and 6290,
which precede 6312 in the list, were removed by the filter. The
desktop DIAG44 list is
`[6882, 6903, 6881, 6904, 6902, 6880, 10331, 10332, 6901, 6879, 6905,
6883, 10327, 10328, 6878, 6900, 6877, 6899]`; the operative call visits
`[6882, 6903, 6880]` — 6881, 6904 and 6902, which precede 6880, were
removed by the filter on desktop. The filter's only differing decision
is the 6902/6880 pair: desktop discards 6902 and keeps 6880; Wasm
discards 6290 (≡ 6880) and keeps 6312 (≡ 6902).

The ByEuclidean candidate order also differs at exactly that pair.
With the consistent within-run id offsets (heads −590, rests −715,
verified on the other 16 positions), desktop positions 5/6 are
`[6902, 6880]` while Wasm positions 5/6 are `[6290, 6312]` —
i.e. `[≡6880, ≡6902]` — swapped. Two chords at nearly equal Euclidean
distance from the sign flip order on a ~1 px chord-center difference.

What is NOT proven: the filter's numeric inputs. `filterChordsOnAbscissa`
discards, for each horizontally-overlapping pair, the chord with the
higher vertical distance from the tuplet sign — but DIAG45A prints only
post-filter iteration, never the pair comparisons (chord bounds,
centers, vertical distances, which was discarded). The head positions
alone do not determine it: 6880's head is at y=1857 (113 px above the
sign) while 6902/6312's head is at y=2034 (64 px below it), so on head
distance alone 6902 is nearer — the filter must be comparing chord
bounds/centers (stems included), which can sit on either side of the
sign. The exact 1 px input that flips the filter is therefore
unmeasured; that is DIAG46B (§39.6).

No contained fix at this level. Changing the filter's tie-break, or
the ByEuclidean sort, is an Audiveris behaviour change — and the
"correct" choice here is unknowable from one page: desktop keeps 6880
by a 1 px margin just as Wasm keeps 6902 by a 1 px margin. The
divergence is a 1 px knife-edge in upstream chord geometry, same family
as divergence A.

**Correction to §38.4.1 (candidate order).** The §38 claim that the
candidate order is "identical position-by-position" is withdrawn:
positions 5/6 are swapped (above), and the desktop ids themselves
shift between runs — the (2067,1970) tuplet is #10235 in the §38
desktop log but #10249 in this run, with a completely different id
list, for the same input and a byte-identical .mxl. Desktop's parallel
executors make inter id allocation non-deterministic across runs (same
family as the §23.8/§33 HEADERS CME, which ran in a parallel executor
task on desktop). Wasm ids are deterministic (inline executor) and
match §38 exactly (#9534, same list). **Future id-based comparisons
must align by content (head positions, durations, staffs), never by id
offset.** The §38 conclusions that survive this correction: the
collector's arithmetic (§38.4.2 — the 16th is not added as a beam
sibling), the benign (550,1781) tuplet (§38.4.4), and StackRhythm
identity (§38.5).

### §39.4 The (550,1781) tuplet — same family, benign

- Desktop — tuplet#9868, targetStaff=**6**: first candidate is a
  quarter rest on staff 6, then eighth #6844 (staff 6, head @y=1722)
  → `status=OUTSIDE base=1/8 expectedTotal=3/8 total=3/8 chords=[6844,
  10309]` — Fail, sign outside the abscissa range.
- Wasm — tuplet#9152, targetStaff=**7**: the quarter rest (staff 6)
  is skipped (staff-mismatch, target is 7); two quarter notes on
  staff 7 are included (#6276, #6274, heads @y=1890) → `status=null
  base=1/4 expectedTotal=3/4 total=1/2 chords=[6274, 6276]` —
  exhausted, Fail.

`getTargetStaff` returns the staff of the first head-based chord
among the sorted candidates. Desktop's nearest head-based chord is
staff-6; Wasm's is staff-7 — the ByEuclidean order flips at the top
of the list, the same ~1 px knife-edge as §39.3's positions 5/6. Both
sides fail to link this tuplet, so the .mxl is unaffected (benign, as
§38.4.4 said). Recorded, not chased — but it shows the order flip is
not specific to one tuplet: it is a property of how close the
competing chords sit to the sign.

### §39.5 Ruled out

- TEXTS/OCR (no-OCR both sides throughout); StackRhythm/MeasureRhythm
  logic (§38.5 stands — 48 rhythm lines identical, only S2 #8 fails
  both sides); tuplet candidate generation (the DIAG44 lists agree in
  content modulo the §39.3 5/6 swap); beam-sibling inclusion as the
  mechanism for divergence B (§38.4.2 stands, and the DIAG45A member
  lists show single-head chords on both sides); `getTopStaff()`
  behaviour (the staff values are consistent with the member heads'
  staffs on both sides — 6312's head really is staff 8 @y=2034 under
  Wasm, 6880's really staff 7 @y=1857 on desktop; the difference is
  which head is in the chord, not the staff lookup); the §26 Area/fill
  path (not in either chain); the §25 grid gap (fixed in §26, structure
  identical); a TeaVM defect localised to a single small operation —
  none found in this round. Both divergences are 1 px knife-edges in
  Audiveris's own thresholds, fed by the §18 jitter family.
- Also ruled out by the side-effect-free checks: the DIAG45 prints
  themselves change nothing (both .mxl files byte-identical to out85 /
  out78 on all three reference pages).

### §39.6 Next diagnostic — DIAG46 (named, not started)

One print round, two sites, both aimed at the exact 1 px input that
flips each gate:

- **DIAG46A (purge gate):** in `SlursBuilder.purgeStaffLines`, dump
  the staff-line fit for the line at y≈1656/1657 near x=1284 — the
  fitted line's constituent points and the `yAt(end.x)` computation —
  on both sides, plus the arc point list around the tie-arc ends
  (1284–1348, 1653–1658). Goal: name the exact pixel(s) that move the
  fitted line Y by 1 px and the arc points by 1 px (skeleton pixel?
  line-fit rounding? the §30–§32 residual +37/+97 fore px?).
- **DIAG46B (tuplet filter):** in
  `TupletsBuilder.filterChordsOnAbscissa`, dump every overlapping pair
  comparison — both chords' bounds/centers, each vertical distance to
  the sign, which was discarded — for the 6902/6880 pair on both
  sides. Goal: name the exact 1 px input that flips the filter.

Only after DIAG46 can a contained fix be judged: if the 1 px input
traces to a specific shim/classlib behaviour (a rounding rule, a
geometry primitive), that is fixable; if it traces to accumulated
skeleton jitter with no single source, the fix is either a tolerance in
the Audiveris threshold (not desktop-neutral — needs Jonathan's call)
or acceptance of 2/56 rhythm-only measures differing on this page.

### §39.7 Artefacts

- `teavm/patched/make_patches.py` — ROUND 45 (DIAG45A/B); note the
  `read_out` correction (§39.1, incident 1).
- `teavm-fork/phase45/` — `phase45-build86.log`,
  `phase45-build86-spike.log`, `phase45-desktop-compile-diag45.log`,
  `run-noocr-wasm86.log` (Hallelujah, 15.5 MB),
  `desktop-hallelujah-noocr86.log` (125 MB),
  `run-noocr-wasm86-lindenbaum.log`,
  `wasm-hallelujah-noocr86.musicxml` (105,254 B),
  `desktop-hallelujah-noocr86.musicxml` (105,442 B),
  `wasm-lindenbaum-noocr86.musicxml` (99,305 B),
  `analyse_diag45.py`, `extracts/diag45-{wasm,desktop}.txt`
  (DIAG45 lines only: 7,286 / 8,172).
- Builds: `full-out86/` (current, diagnostic — DIAG44 + DIAG45 prints
  in). `full-out84/` remains the last non-diagnostic build.
- Nothing to file for §39 (no TeaVM defect). Next named: DIAG46
  (§39.6); after that: HeadHeadRelation SIGraph symptom (§26.12),
  clean build (strip DIAG prints incl. DIAG44/DIAG45), real-browser
  Chrome run, upstream filings (#272, #21244, §11, §19 TColor, §27
  hypot, §33 retainAll, §35 TFormatter).

## §40 — DIAG46 localisation + the `Math.rint` defect: Divergence A FIXED by a contained classlib patch; Divergence B is not rint — verdict (a) for A, (c) for B (2026-11-10)

### §40.0 Verdict

**(a) for Divergence A (P2 m9 tie): contained fix, applied and verified.**
DIAG46 localised both 1 px gate inputs to one specific classlib behaviour:
`TMath.rint` is `return round(a);` — round half *away* from zero, where the
JDK rounds half to *even*. The staff-line fit does not differ at all
(`yAtDbl` = 1656.5 both sides); the 1 px line-Y difference is
`rint(1656.5)` (1656.0 JDK / 1657.0 TeaVM), and the tangent dx 7 vs 8 is not
an arc difference either — the arc point lists are identical; it is
`tangentLength = rint(0.5 × 17) = rint(8.5)` (8 JDK / 9 TeaVM). The fix is a
2-hunk `TMath` patch (proper `rint`, plus `round` corrected for negative
halves, same defect family). Minimal repro: 30/30 cases match the JDK
post-fix (13 mismatched pre-fix). Full-out88 re-run: the tie slur's gate
inputs now match desktop exactly (lineY 1656.0, dx 7, incidence 15.945°) and
the slur survives purge; Hallelujah deep diff 93 → 89, Lindenbaum 10 → 2
(filename artefacts only), hymn 12 → 2 (filename artefacts only). No
regression on either control page — both are now at desktop parity on real
diffs.

**(c) for Divergence B (P3 m10 tuplet): inconclusive, localised, NOT fixed by
this patch.** DIAG46 did name the exact flipping pixel — the chord-bounds
right edge (desktop 1987 vs Wasm 1985, from widths 23 vs 21) — but the
rint fix changed neither the bounds (still 21 wide under full-out88) nor the
filter outcome (still a 89 = 89 tie, still discards the staff-7 16th), so
the bounds-width difference is *not* rint-driven. Its source is still
unproven. Next diagnostic named: **DIAG47 — chord member-bounds dump**
(head bounds vs stem bounds for the 6902/6880 pair). If DIAG47 also finds
accumulated jitter with no single source, the §39 options for B stand (an
Audiveris threshold tolerance — not desktop-neutral, needs Jonathan's call —
or accepting 1/56 rhythm-only measures differing on this page).

### §40.1 DIAG46A — staff-line fit dump + arc point list (full-out87)

Two print sites in `SlursBuilder.purgeStaffLines` (ROUND 46): `DIAG46 lineFit`
— staff-line bounds, thickness, `yAtDbl` at the arc end and at x = 1284/1290/
1300/1340/1348, `defPts` (the line's defining points); `DIAG46 arcPts` — the
full arc point list for the end being purged.

- **Line fit: identical.** Both sides: lineBounds `Rectangle[237, 1656,
  2064x1]`, thickness 1.014215418261345, `yAtDbl` = 1656.5 at every sampled x.
  `defPts=[]` on both sides — the StaffLine was simplified (endpoints only),
  so the fit is flat 1656.5 and does *not* differ. The 1 px line-Y difference
  (1656.0 vs 1657.0) is purely `Math.rint(1656.5)`: JDK half-to-even →
  1656.0; TeaVM half-away → 1657.0.
- **Arc points: identical.** For every shared end, the point lists match
  exactly, including the tie arc 272 ≡ 266 (n = 65, starting (1284,1658),
  through (1291,1656), (1292,1656), … (1348,1656)). So the tangent dx 7 vs 8
  from DIAG45B is *not* an arc difference. `getSidePoints(reverse,
  tangentLength)` takes the first `tangentLength` points; with identical
  lists, p1 = points[7] on desktop vs points[8] under Wasm means
  `tangentLength` itself differs by 1: 8 vs 9. `tangentLength =
  scale.toPixels(0.5 fraction) = (int) Math.rint(0.5 × interline)`;
  interline is 17 (median; `Scale{ interline(16,17,17) ... }`), so this is
  `rint(8.5)` — 8 on the JDK, 9 under TeaVM. Both Divergence A inputs are
  the same single defect.

### §40.2 DIAG46B — filterChordsOnAbscissa pair dump (full-out87)

One print site in `TupletsBuilder.filterChordsOnAbscissa` (ROUND 46):
`DIAG46 filterPair` — for each pair the sign point, both chords' ids, bounds,
centres, vertical distances, overlap, and which was discarded. The decisive
pair, sign (2067,1970):

- Desktop: `ch1=#6814 b1=[1965,2025,23x68] c1=(1976,2059) d1=89 ch2=#6792
  b2=[1965,1848,22x67] c2=(1976,1881) d2=89 overlap=22 discard=#6814`.
- Wasm: `ch1=#6290 b1=[1966,1848,21x67] c1=(1976,1881) d1=89 ch2=#6312
  b2=[1965,2025,21x68] c2=(1975,2059) d2=89 overlap=20 discard=#6290`.

**The pair is a tie (d1 = d2 = 89) on both sides** — the outcome depends
only on which chord is ch1, i.e. on the ByEuclidean order. The order flip is
fully explained by the chord-bounds width, verified by hand against
`GeoUtil.ptDistanceSq` (minimum distance to the four rectangle edges, with
x2 = x + width − 1): desktop #6814's right edge is 1987, so the closest
point on its top edge to (2067,1970) is (1987,2025): dx 80, dy 55 →
dSq 9425 < 9697, so 6814 sorts first. Wasm #6312's right edge is 1985 →
(1985,2025): dx 82, dy 55 → dSq 9749 > 9697, so it sorts second. The other
pair's dSq is 9697 on both sides (bottom edge (1986,1914): dx 81, dy 56).
**The exact flipping pixel is the chord-bounds right edge (1987 vs 1985)** —
a 2 px width difference (23 vs 21). Systematic, not random: every head-chord
bound in the dump is 1–2 px narrower on Wasm (widths 21 vs 22/23, heights 66
vs 67 sometimes, x +1 sometimes) while rests are byte-identical
(`[2154,1867,19x32]` both sides). Centres follow the widths by integer
division (23-wide rect at x=1965 centres at 1976; 21-wide at 1975), so the
centre difference is a consequence, not a second input. What sets the width
— head glyph bounds vs stem bounds — was *not* measured by DIAG46; that is
DIAG47 (§40.6).

Correction to §39.5: the filter's numeric inputs are now measured, and the
flip is a tie-break on equal distances, not a distance difference. The
§38.4.1 correction stands (candidate order is not identical
position-by-position; compare by content, never by id offset).

### §40.3 The defect — `TMath.rint` and `round` (fork classlib)

`teavm-fork/src/classlib/src/main/java/org/teavm/classlib/java/lang/TMath.java`:

```java
public static double rint(double a) {
    return round(a);
}
public static int round(float a) {
    return (int) (a + signum(a) * 0.5f);
}
public static long round(double a) {
    return (long) (a + signum(a) * 0.5);
}
```

Three distinct non-conformances, all "halves away from zero where the JDK
does something else":

1. `rint` rounds halves away from zero; the JDK rounds half to even.
   `rint(8.5)` = 9.0 (JDK 8.0), `rint(1656.5)` = 1657.0 (JDK 1656.0),
   `rint(0.5)` = 1.0 (JDK 0.0), `rint(-0.5)` = −1.0 (JDK −0.0).
2. `rint` destroys NaN/Infinity: they pass through `round`'s `(long)` cast,
   so `rint(NaN)` = 0.0 (JDK NaN), `rint(+Inf)` = 9.223372036854776E18
   (`Long.MAX_VALUE` as a double; JDK +Infinity).
3. `round(double)`/`round(float)` are wrong for negative halves: the JDK
   defines them as `floor(a + 0.5)` / `floor(a + 0.5f)`, so `round(-8.5)` =
   −8 (TeaVM −9), `round(-9.5)` = −9 (TeaVM −10), same for the float
   versions. Positive halves already agreed.

### §40.4 Minimal repro — `phase47/rint-repro/` (TeaVM-level, no Audiveris)

`RintMain.java` prints 30 cases (`rint` halves both signs, non-halves,
NaN/±Inf/±0.0, `round` double/float) with the JDK value beside each, and an
OK/MISMATCH verdict. JDK reference (`jdk-reference.log`, JDK 25): all 30 OK.
Pre-fix TeaVM (`out/`, `run-prefixed.log`): 13 mismatches — 9 `rint` (8.5,
1656.5, 0.5, 2.5, −8.5, −0.5, NaN, +Inf, −Inf) and 4 `round` (the negative
halves). Post-fix (`out-fixed/`, `run-fixed2.log`): **all 30 byte-identical
to the JDK reference, 0 mismatches** — including the printed `−0.0` for
`rint(-0.5)`, which needed one extra line in the fix (the `f + 1.0` tie path
yields +0.0; the sign of zero is preserved explicitly). Runner
`run-repro2.mjs`, `jars.txt` mirrors the §35 format-repro.

### §40.5 The fix — applied to the fork classlib

`teavm-classlib-rint.patch` (2 hunks, `TMath.java` only; verified to apply
cleanly to pristine TeaVM 0.16.0 with `patch --dry-run`):

```java
public static double rint(double a) {
    // JDK: the closest integer; ties go to the even integer (round half
    // to even). TeaVM previously delegated to round(), i.e. half away
    // from zero, and additionally destroyed NaN/Infinity (they pass
    // through a (long) cast, becoming 0 / +-Long.MAX_VALUE).
    if (Double.isNaN(a) || Double.isInfinite(a) || a == 0.0) {
        return a;
    }
    double f = floor(a);
    double diff = a - f;
    if (diff < 0.5) {
        return f;
    }
    if (diff > 0.5) {
        return f + 1.0;
    }
    // Tie: return the even neighbour. (Preserve the sign of zero:
    // rint(-0.5) is -0.0 on the JDK.)
    double r = (f % 2.0 == 0.0) ? f : f + 1.0;
    return (r == 0.0) ? (a < 0.0 ? -0.0 : 0.0) : r;
}

public static int round(float a) {
    // JDK: (int) floor(a + 0.5f). TeaVM previously rounded halves away
    // from zero, so round(-8.5f) was -9 instead of -8.
    return (int) floor(a + 0.5f);
}

public static long round(double a) {
    // JDK: (long) floor(a + 0.5). TeaVM previously rounded halves away
    // from zero, so round(-8.5) was -9 instead of -8.
    return (long) floor(a + 0.5);
}
```

`floor` is the existing native import (`teavmMath.floor`); `%` on doubles is
native `f64.rem`, exact for integer-valued operands. Applied the §27
procedure: `javac -cp <classlib.jar>:<teavm>/lib/*` (`phase47/rint-classes/`,
`rint-compile.log`), `jar uf` into
`lib-fork/teavm-classlib-0.16.0.jar` (verified by `javap`), rollback kept as
`lib-fork/teavm-classlib-0.16.0-pre-rint.jar`. The fork `src/` git diff for
`TMath.java` also contains the §27 hypot hunk — the patch file holds the
rint/round hunks only (hypot lives in `teavm-classlib-hypot.patch`).

Test gap (for the upstream filing): TeaVM's own `MathTest` has no `rint`
coverage at all, and `roundWorks` tests only non-half values (1.3, 1.8, −1.3,
−1.8) — which is why this survived. A regression test along the repro's
lines (half values both signs, NaN, ±Infinity, ±0.0) would cover it.

### §40.6 Full verification — full-out88 (ROUND 46 sources + rint-fixed classlib)

No Audiveris source change in this round, so no new `make_patches.py` ROUND:
`./build.sh` re-ran ROUND 46 as-is and the Spike build used the patched
classlib jar (already on the program classpath via
`teavm-main-jars-corepatch2.txt`). Build **full-out88** (0 problems, 3,058
classes, 28,753 methods — one fewer than out87, `round(double)` no longer
called from `rint`; `classes.wasm` 14,382,190 B). DIAG46 prints still in.

**Hallelujah p01 no-OCR** (`run-noocr-wasm88.log`, 84.3 s; .mxl 105,434 B vs
desktop 105,442 B, was 105,254 B):

- Divergence A FIXED at the gate. DIAG45 line 30186: `purge id=269
  end=(1284,1658) lineY=1656.0 toLine=-2.0 ... p1=(1291,1656) p2=(1284,1658)
  dx=7.0 dy=2.0 incidenceDeg=15.945395900922856` — both inputs now match
  desktop exactly, and there is no `PURGE-STAFFLINE id=269
  reason=staff-line-incidence` delete for this arc. DIAG46 lineFit (30187)
  still shows `yAtDbl` 1656.5 — the inputs are unchanged; only the rounding
  of them changed.
- Element counts: notes 275 = 275, pitched 217 = 217, rests 58 = 58, slurs
  22 = 22, ties 4 = 4, measures 56 = 56. `time-modification` 39 vs 38 —
  the one extra is the P3 tuplet (below).
- Deep diff vs desktop (`compare-deep-hallelujah-p01-88.txt`): **89, was
  93** (2 are the input-filename artefacts in both). Path-level comparison
  against the out82 list (accounting for the out82 file's swapped ref/writer
  roles): 3 paths gone — the two P2 m9 tie child-count diffs
  (`part[4]/measure[8]/note[2]` and `note[3]`, the tie + notations now
  present on Wasm) and a staff-distance rounding (`part[4]/measure[0]`,
  104 vs 103, now matching); 3 new ±1 `default-x` diffs in part[5]
  (measure[10] notes 5, 6; measure[12] note[0]) — .5 boundaries moved by
  the fix, losing three accidental matches; the rest of the ±1-tenth family
  is unchanged in substance. The unlisted tail shrank by 4 (93 → 89 total).
- Divergence B UNCHANGED. DIAG46 filterPair (log line 160271): `ch1=#6346
  b1=[1966,1848,21x67] d1=89 ch2=#6368 b2=[1965,2025,21x68] d2=89
  discard=#6346` — still a tie, still discards the staff-7 16th. The bounds
  are still 21 wide: no `rint` site with a `.5` input feeds these bounds.
  `part[5]/measure[9]` still differs structurally (Wasm links the rest into
  the tuplet, desktop links notes 5, 7). Hallelujah p01 is now 1 of 56
  measures differing rhythm-only (was 2).

**Lindenbaum no-OCR** (`run-lindenbaum-wasm88.log`, 59.1 s; .mxl 99,305 B,
223 notes): deep diff vs the FIXED desktop
(`phase40/desktop-lindenbaum-noocr78b.musicxml`, 223 notes) is **2 — both
filename artefacts, zero real diffs** (was 10 at out78: 2 filename + 8 × ±1
`default-x`/staff-distance/slur-bezier). Note: comparing against the
unfixed `desktop-lindenbaum-noocr78.musicxml` (189 notes, the §34 trap)
gives a spurious part measure-count diff — the §34 desktop trap, not a rint
effect.

**Hymn no-OCR** (`run-hymn-wasm88.log`, 36.1 s; .mxl 44,105 B, 128 notes,
0 slurs): deep diff vs desktop (phase35 = phase37, byte-identical) is **2 —
both filename artefacts, zero real diffs** (was 12 at out78). Not
byte-identical to Wasm78 — five ±1 `default-x` values moved (62→63, 144→145,
137→138, 52→53, 93→94) *onto* the desktop values; the old bytes were the
wrong-rounding bytes. No regression.

### §40.7 Divergence B — next diagnostic DIAG47 (named, not started)

Dump, for the 6902/6880 filter pair, each chord's member bounds: head bounds
and stem bounds separately (which member's bounds differ, and by how much).
Candidates to discriminate: head glyph bounds from the skeleton (Wasm
skeleton is fatter, not thinner, §30–32 — so a narrower chord bound points at
the stem: stem x/section range) vs a `rint` site with a non-`.5` input (ruled
out for the width itself by out88 — the fix moved nothing) vs integer line
fitting on the skeleton (accumulated jitter). If DIAG47 also finds no single
source, the §39 options for B stand unchanged.

### §40.8 Upstream

Genuine TeaVM defect, localised to a single small operation in three methods,
minimal repro built, fix is a 2-hunk classlib patch:
`phase47/rint-repro/ISSUE_RINT_DRAFT.md` (repro steps, JDK vs TeaVM output
table, root cause, proposed fix, MathTest gap). **NOT filed** — Jonathan's
decision (2026-11-09) is to file upstream only after our own work is done.
Candidate upstream items now: #272, #21244/#15448, §11 Profiles.getName(),
§19 TColor, §27 hypot, §33 retainAll, **§35 TFormatter null argument, §40
`rint`/`round`**. Verified here by `javac` + in-place `jar uf` (Gradle does
not run in this VM); per `src/AGENTS.md` the Gradle suite
(`./gradlew :tests:test` with the `teavm.tests.wasm-gc`/`js`/`c` and
`teavm.tests.optimized` properties) must run on a machine where Gradle works
before submitting upstream.

### §40.9 Artefacts

- `phase47/rint-repro/` — `RintMain.java`, `classes/`, `jars.txt`,
  `jdk-reference.log` (JDK 25, 30/30 OK), `build.log`, `run-prefixed.log`
  (pre-fix: 13 mismatches), `build-fixed.log`, `run-fixed.log`,
  `build-fixed2.log`, `run-fixed2.log` (post-fix: 30/30, byte-identical to
  the JDK reference apart from the `LOAD OK` / `main() returned` framing
  lines), `ISSUE_RINT_DRAFT.md`.
- `phase47/rint-classes/` (`TMath.class`), `rint-compile.log`;
  `teavm-classlib-rint.patch` (2 hunks, applies cleanly to pristine
  0.16.0); `lib-fork/teavm-classlib-0.16.0.jar` (TMath entry replaced),
  `lib-fork/teavm-classlib-0.16.0-pre-rint.jar` (rollback).
- `phase47/` — `full-build88-spike.log`, `build88.log`,
  `run-noocr-wasm88.log` (Hallelujah), `run-lindenbaum-wasm88.log`,
  `run-hymn-wasm88.log`, `wasm-hallelujah-noocr88.musicxml` (105,434 B),
  `wasm-lindenbaum-noocr88.musicxml` (99,305 B),
  `wasm-hymn-noocr88.musicxml` (44,105 B),
  `compare-deep-hallelujah-p01-88.txt` (89),
  `compare-deep-lindenbaum-88.txt` (2),
  `compare-deep-hymn-88.txt` (2).
- `phase46/` — DIAG46 artefacts from the pre-compaction session
  (`run-noocr-wasm87.log`, `desktop-hallelujah-noocr87.log`,
  `extracts/diag46-{wasm,desktop}.txt`, `analyse_diag46.py`); the DIAG46
  values quoted in §40.1/§40.2 are from those logs, re-confirmed in the
  out88 run.
- Builds: `full-out88/` (current, diagnostic — DIAG44 + DIAG45 + DIAG46
  prints in, rint-fixed classlib). `full-out84/` remains the last
  non-diagnostic build. Next named: DIAG47 (chord member-bounds dump for
  the 6902/6880 pair); after that: HeadHeadRelation SIGraph symptom
  (§26.12), clean build (strip DIAG prints incl. DIAG44/45/46),
  real-browser Chrome run, upstream filings (#272, #21244, §11, §19 TColor,
  §27 hypot, §33 retainAll, §35 TFormatter, §40 rint/round).

## §41 — DIAG47: Divergence B never existed — the desktop harness was running a stale `PreRenderedTemplates` (ps80 for a 72 request); contained harness fix, all three control pages now at zero real diffs — verdict (a) (2026-11-10)

### §41.0 Verdict

**(a) contained fix applied and verified — but the fix is in the comparison
harness, not in Wasm and not in TeaVM. Divergence B (P3 m10 tuplet) never
existed as a Wasm divergence.** The 1–2 px chord-bounds difference DIAG46B
measured was the desktop harness building heads from the wrong template: the
harness's compiled `teavm.PreRenderedTemplates` was the §19 version
(catalogs {80, 92, 108}), so a 72 request mapped to the ps80 template
(11% oversize), while Wasm (full-out89, current §36 class) correctly mapped
72 → 72. After recompiling the current class into the harness, every DIAG47
member bound is byte-identical on both sides and the Hallelujah deep diff is
**89 → 2 (both filename artefacts — zero real diffs)**. The P3 m10 tuplet
measure matches exactly. Hymn and Lindenbaum re-confirmed at 2 (filename
only), byte-identical desktop references to §35/§34 — no regression. **All
three control pages are now at zero real diffs; Hallelujah is 0 of 56
measures differing.** No Wasm rebuild was needed in this round; nothing in
the classlib, shims, or Audiveris patches changed. No TeaVM defect, no
repro, nothing to file for this item.

### §41.1 DIAG47 results (full-out89, ROUND 47)

The dump itself (18 chords in the first full-list call, both sides) confirmed
the §40 headline and exonerated the stem: **head bounds differ on 14/14
head chords; stem x/width identical per chord** (stems differ only
vertically, Wasm stems start 2 px higher with the same bottom/tail — a
knock-on of the head box, not a cause); **rests byte-identical** (4/4).
Desktop heads 22–23 px wide, 18–19 tall; Wasm uniformly 21×18. Pair chords:
desktop #6896 cb=[1965,2025,23x68], head #3185 [1965,2025,23x18], stem #5873
[1965,2041,3x53], tail=(1966,2093); Wasm #6368 cb=[1965,2025,21x68], head
#3428 [1965,2025,21x18], stem #5497 [1965,2039,3x55], tail=(1966,2093).
Upper pair: desktop #6874 head #2945 [1965,1848,22x18]; Wasm #6346 head
#3097 [1966,1848,21x18]. Chord left/right edges are set by the heads on
both sides in every case (headsL == cbL, headsR == cbR).

### §41.2 Why head bounds are template-size, not ink-size — the mechanism

Read from stock Audiveris source (not assumed):

1. `NoteHeadsBuilder.createInter` builds the HeadInter from
   `template.getSlimBoundsAt(loc.x, loc.y, anchor)` — the template's slim
   bounds placed at the match location. Width is template-fixed.
2. `HeadInter.retrieveGlyph(template, image)` — called for every head right
   after creation (both the seed-based and abscissa-based paths) — then
   **overwrites the bounds**: `bounds = glyph.getBounds()`, with the comment
   "Use glyph bounds as inter bounds".
3. The glyph is built from `Template.getForegroundPixels(tplBox, image)`,
   which keeps only the template's d==0 key points where the image pixel is
   foreground (`image.get(nx, ny) == 0`). So the final head bounds are the
   extents of the template's key points that coincide with image ink.
4. Consequence: a *smaller* template's key points all sit inside the real
   ink (real heads here are ~22–23 px wide), so every key point finds ink
   and the bounds come out uniformly template-size (Wasm ps72: 21×18). A
   *larger* template's outermost key-point columns sit at the ink edge, so
   whether they are kept varies head by head with 1 px ink jitter (desktop
   ps80: 22–23 wide, 18–19 tall). The 22-vs-23 variation on desktop is
   exactly this edge effect — it is not a second template and not a
   rounding difference.

So the head-bounds difference reduces to: **which template did each side
use for the same request?**

### §41.3 The two sides used different templates for request 72

The one-line proof, from the run logs:

- Wasm full-out89: `PreRenderedTemplates: requested 72 maps to desktop
  catalog 72` (current §36 class).
- Desktop harness, phase48 run: `PreRenderedTemplates: requested 72 maps to
  desktop catalog 80` (stale §19 class).

Root cause of the staleness (timestamps, verified): `phase23/classes/teavm/
PreRenderedTemplates.class` is dated **2026-11-10 04:27** — the §29.2
fresh-classes build — while `teavm/entry/src/teavm/PreRenderedTemplates.java`
was regenerated **2026-11-10 08:36** by §36 (catalogs {64, 72, 80, 92, 108})
and never recompiled into `phase23/classes`. The §29.2 rule ("compile only
changed diagnostic files") was followed for diagnostic files, but the §36
entry-source regeneration did not trigger a harness recompile. The patched
`TemplateFactory` (ROUND 12) in the harness therefore substituted the
stale lookup, and the harness desktop — which is only a valid reference
when its compiled classes match the current sources — silently ran with an
11%-oversize template on every request-72 page.

Note the desktop harness is *supposed* to use the pre-rendered lookup (it
runs the same patched code as Wasm, minus the TeaVM-functional classes);
the substitution is harmless when the data matches what stock builds at
the requested size. Stock desktop builds the template from real Bravura
at exactly 72 — slim [3,3,21,18] per `phaseb/templates.json` — i.e. the
ps72 template Wasm uses. The stale ps80 substitution was the only
deviation.

### §41.4 Fix applied (harness only)

Recompiled the current `teavm/entry/src/teavm/PreRenderedTemplates.java`
into `phase23/classes` (javac, exit 0, classpath `phase23/classes` +
program jars; no other file touched). The stale class is kept as
`phase48/PreRenderedTemplates-stale-19.class` (plus `$1`). No Wasm rebuild
(full-out89 already uses the current class), no source change, no classlib
change.

### §41.5 Verification

- **Hallelujah p01** — new desktop run (89b, exit 0): `requested 72 maps
  to desktop catalog 72`. DIAG47 (analyser fixed — see §41.6): **head
  bounds differ 0/18, stem bounds differ 0/18**; every chord, head, stem,
  and tail byte-identical; filter calls 4 vs 4 (was 3 vs 4 — the stale
  desktop even took a different call path). Deep diff new desktop
  (105,578 B) vs Wasm out89 (105,434 B): **2 — both filename artefacts
  (`/identification/source`, `/miscellaneous-field`), zero real diffs.**
  P3 m10: 9 notes, durations `['6','6','4','3','3','6','4','4','6']`
  identical both sides. Counts identical: 4 parts, 56 measures,
  28 tuplets, 4 ties, 13 beams, 22 slurs.
- **Hymn** — desktop 89b **byte-identical to the §35 desktop**
  (md5 9b058b42…); deep diff vs Wasm out88: **2 (filename only)** — §40
  stands, no regression.
- **Lindenbaum** — desktop 89b **byte-identical to the §34 desktop**;
  deep diff vs Wasm out88: **2 (filename only)** — §40 stands, no
  regression.

### §41.6 Corrections to the record

- **§40's Divergence B is WITHDRAWN as a Wasm divergence.** The "filter
  pair is a 89 = 89 tie decided by chord-bounds width (23 vs 21 → right
  edge 1987 vs 1985)" was measured against the stale harness: the
  23-wide desktop chords were built from the wrong (ps80) template.
  With the correct template both sides are 21 wide, the filter inputs
  are identical, and the tuplet agrees. There is no bounds-width source
  left to find — the rint fix did not change the bounds because the
  bounds were never a Wasm behaviour; they were the harness's template.
- **§40's "deep diff 93 → 89" is superseded**: against the correct
  desktop reference the Hallelujah deep diff is **2 (filename only)**.
  The rint fix's real contribution was Divergence A (tie gate inputs now
  match desktop exactly, slur survives purge) — that stands, verified by
  DIAG46A gate inputs, not by the diff count. The "3 new ±1 default-x
  diffs where .5 boundaries moved" were also measured against the wrong
  reference and are withdrawn.
- **§36.4's "8 → 93" explained, not a regression.** Under out80 both
  sides used ps80 (Wasm: nearest catalog to 72 in {80, 92, 108};
  harness: stale class also 80) → diff 8. §36 widened only the Wasm side
  to ps72; the harness stayed ps80 → diff 93. The two sides diverged
  because only one of them got the §36 update.
- **§39's framing** ("filter pair is a tie decided by chord-bounds
  width") — same withdrawal as §40's. The §39 options (Audiveris
  threshold tolerance vs accepting 1/56 rhythm-only measures differing)
  are moot for this item: there is no remaining measure differing.
- **Contamination scope**: only request-72 pages (Hallelujah
  p01/p02/p03/p07). Every other request either hit the same catalog in
  both versions (80/92/108) or fell back to the stock Builder with real
  Bravura when the stale lookup returned null (64, 70/71, 140) — which
  is stock-correct. The multi-page full-out82 results are unaffected
  (stock batch desktop, not the harness).
- **Analyser bug, fixed in passing**: `phase48/analyse_diag47.py`
  hardcoded the old log paths and ignored argv — the first two
  "analyses" of the 89b log actually re-read the stale 89 log. Fixed to
  accept argv paths (defaults preserved). Lesson: the DIAG47 headline
  numbers in §41.1 were re-verified against the raw lines after the fix.

### §41.7 Durable procedure (new lesson)

**Whenever an entry source the desktop harness compiles
(`teavm/entry/src/*.java`) is regenerated, recompile it into
`phase23/classes` in the same round.** The harness is only a valid
desktop reference when its compiled classes match the current sources;
a stale class fails silently (the run still completes, exit 0, plausible
numbers). Cheap tripwire for every future desktop run: the
`PreRenderedTemplates: requested N maps to desktop catalog M` line in
the desktop log must match the Wasm log's mapping for the same request —
if they differ, stop and rebuild the harness before believing any diff.

### §41.8 Status and next

- **Hallelujah p01, Lindenbaum, hymn: all at deep diff 2 (filename
  artefacts only) — zero real diffs on all three control pages.**
  Hallelujah is now **0 of 56 measures** differing. The §38/§39
  StackRhythm divergences are both resolved: A by the §40 rint fix, B as
  a harness artefact (this section).
- No remaining known Wasm-vs-desktop divergence on the three control
  pages. Current build is **full-out89** (diagnostic, DIAG44/45/46/47
  prints in, rint-fixed classlib); **full-out84** remains the last
  non-diagnostic build.
- Still open (unchanged): HeadHeadRelation SIGraph symptom (§26.12),
  clean build (strip DIAG prints incl. DIAG44–47), real-browser Chrome
  run, upstream filings (#272, #21244, §11, §19 TColor, §27 hypot,
  §33 retainAll, §35 TFormatter, §40 rint/round), BrowserOCR follow-up,
  photometric recovery.
- Next named: **HeadHeadRelation** (§26.12) — the remaining open
  Wasm-vs-desktop item (insertSupport's getDeclaredConstructor().
  newInstance() throws NoSuchMethodException under TeaVM; candidate
  contained fix: ReflectionPolicy entry for the support classes).
- Artefacts: `phase48/` — `desktop-hallelujah-noocr89b.{log,musicxml}`
  (105,578 B), `desktop-hymn-noocr89b.{log,musicxml}`,
  `desktop-lindenbaum-noocr89b.{log,musicxml}`,
  `PreRenderedTemplates-stale-19.class` (+ `$1`), `analyse_diag47.py`
  (argv paths fixed); `phase47/compare-deep-*.txt` are the superseded
  §40 references (Hallelujah 89, Lindenbaum 2, hymn 2).


## §42 — DIAG48: HeadHeadRelation SIGraph symptom FIXED by ReflectionPolicy entries for the support-class constructors — verdict (a) (2026-11-10)

### §42.0 Verdict

**(a) contained fix applied and verified.** DIAG48 named the failing
support class — all 149 failures on Hallelujah p01 are
`HeadHeadRelation` — and the fix is two ReflectionPolicy entries for
the no-arg constructors of the two Support subclasses instantiated
through `SIGraph.insertSupport` (`HeadHeadRelation`,
`BeamBeamRelation`). Full-out91: **149 → 0 `Could not instantiate`
ERROR lines**, and the `.mxl` is byte-identical to out89/out88 on all
three control pages (deep diff 2 each, filename artefacts only — zero
real diffs). The §26.12 open question is answered for these pages:
**the missing supports change no downstream result.** No TeaVM defect
in this round (same treatment as §12 — the policy mechanism is
TeaVM's designed opt-in reflection), so nothing to file upstream for
§42.

### §42.1 Symptom re-established (full-out89)

Hallelujah p01 no-OCR (`phase48/run-noocr-wasm89.log`): **149 `ERROR
[org.audiveris.omr.sig.SIGraph] Could not instantiate javaClass@1524325284
java.lang.NoSuchMethodException` lines**, all one class id, lines
3308–3456 — between REACH HEADS (line 1132) and the ReductionStep end
(line 3457), i.e. during STEMS/CHORDS/REDUCTION, consistent with
§26.12/§26.14. Hymn: 0 lines (unchanged). The count is run-dependent
(58 in the out61 OCR run, 94 in the DIAG29 runs, 149 now — it grows
with how far the run gets and how many systems complete reduction),
and so is the class id; neither is a stable fingerprint. Snow p2's
945 lines (§private-test) were not re-run this round — same
class-level mechanism, see §42.6.

### §42.2 Correction to §26.12: the "only call site" claim was wrong

§26.12 identified the class as `HeadHeadRelation` from the claim that
`SigReducer.java:326` is the only `insertSupport` call site. There
are **three** call sites (stock source, verified):

- `SigReducer.java:326` — `sig.insertSupport(head, sameDur,
  HeadHeadRelation.class)` (REDUCTION step, same-duration head sets)
- `ChordsBuilder.java:484` — `sig.insertSupport(otherHead, rightHead,
  HeadHeadRelation.class)` (CHORDS step, mirror migration when a
  supporting head must move to the right mirror head)
- `BeamGroupInter.java:158` — `sig.insertSupport(member, beam,
  BeamBeamRelation.class)` (beam-group mutual support)

Both classes extend `Support` and have explicit public no-arg
constructors (`HeadHeadRelation.java:48`,
`BeamBeamRelation.java:53`). The §26.12 identification was right in
outcome (DIAG48 proves it) but the reasoning was wrong — the class
could equally have been `BeamBeamRelation`, and only a named print
settles it. The ERROR log prints the class opaquely as
`javaClass@<id>` under TeaVM (slf4j `{}` calls `Class.toString()`),
so the log alone can never identify the class.

### §42.3 DIAG48 localisation (full-out90, ROUND 48)

ROUND 48 (`make_patches.py`): `SIGraph.java` was never patched
before, so `copy_src` is correct here (per §39.1, `read_out` is only
for files an earlier round already patched). One print in
`insertSupport`'s catch, printing `supportClass.getName()`:

```
DIAG48 insertSupport FAIL class=org.audiveris.omr.sig.relation.HeadHeadRelation ex=java.lang.NoSuchMethodException
```

Full-out90 (0 problems, 3,058 classes, 28,753 methods — identical
counts to out89): **149/149 DIAG48 lines are HeadHeadRelation**,
0 BeamBeamRelation. `Class.getName()` works under TeaVM — the
opacity is only in `Class.toString()`. DIAG48 is print-only:
out90 `.mxl` md5 `126771ec…` = out89, and the desktop control
(§42.4) is byte-identical to the 89b desktop.

### §42.4 Root cause: reflection-policy gap (same family as §10/§11/§12)

`insertSupport` (SIGraph.java:971) does
`supportClass.getDeclaredConstructor().newInstance()`. TeaVM
generates reflection metadata only for members a ReflectionPolicy
declares accessible; with no policy entry for these constructors,
`getDeclaredConstructor()` throws `NoSuchMethodException`, the catch
logs the ERROR and returns null, and the support is silently missing.
This is the same defect family as the §10 ConstantSet fields stall
and the §12 FilamentFactory `(int)` constructors — and the same
treatment: a contained fix in our policy, not a TeaVM code change.
The policy mechanism is TeaVM's designed opt-in reflection
(`SimpleReflectionPolicy`, discovered via ServiceLoader on the
program classpath; compile-time only, not in the wasm), so there is
nothing to file upstream for §42 — same as §12, which was also
fixed by policy and never filed.

### §42.5 Fix applied (policy only)

`teavm/policy/src/teavm/TeavmReflectionPolicy.java` — two entries,
following the §12 `reflectableMethods(named("<init>"))` pattern
(constructors are IntrospectMethods named `"<init>"`):

```java
selectClass("org.audiveris.omr.sig.relation.HeadHeadRelation")
        .reflectableMethods(named("<init>"));
selectClass("org.audiveris.omr.sig.relation.BeamBeamRelation")
        .reflectableMethods(named("<init>"));
```

Both Support subclasses instantiated through `insertSupport` are
listed: `HeadHeadRelation` (proven failing) and `BeamBeamRelation`
(same path, never observed failing in these runs, same defect
class) — the §12 precedent (both filament classes listed though
only one had failed first). No Audiveris source change, no classlib
change, no shim change. `build.sh` recompiles the policy into
`policy-classes/` (on the program classpath via
`teavm-main-jars-corepatch2.txt`).

### §42.6 Verification — full-out91 (ROUND 48 sources + policy fix)

Build **full-out91** (0 problems, **3,060 classes** (+2 — the two
relation classes now compiled in with their constructors as
reflectable), 28,757 methods (+4), `classes.wasm` 14,392,214 B).
Build outputs were captured in the session transcript (no separate
build log file was saved this round).

- **Hallelujah p01 no-OCR** (`phase49/run-noocr-wasm91.log`,
  82.9 s): `DIAG48: 0`, `Could not instantiate: 0` (was 149/149).
  `.mxl` 105,434 B, md5 `126771ec…` — **byte-identical to out89
  and out90**. Deep diff vs desktop 91: **2, both filename
  artefacts** (`/identification/source`,
  `/miscellaneous-field`) — zero real diffs.
  REACH lines identical to out90 (HEADS 218, SYMBOLS SIG 1509,
  LINKS 1261, PAGE 1256, CHECK 685409). SIG vertex counts do not
  move — expected: supports are graph *edges*, not vertices, so
  creating 149 of them cannot change a vertex count. The 0 DIAG48
  lines are the proof the instantiations succeeded (the same 149
  calls that threw in out90 now return; `addEdge` after them
  runs without trapping, exit 0).
- **Hymn no-OCR** (`phase49/run-noocr-wasm91-hymn.log`, 35.2 s):
  44,105 B, md5 `75637092…` — **byte-identical to out88**.
  DIAG48: 0, `Could not instantiate: 0`. Deep diff vs desktop
  89b: **2 (filename only)**.
- **Lindenbaum no-OCR**
  (`phase49/run-noocr-wasm91-lindenbaum.log`, 57.3 s): 99,305 B,
  md5 `dbd546ba…` — **byte-identical to out88**. DIAG48: 0,
  `Could not instantiate: 0`. Deep diff vs desktop 89b: **2
  (filename only)**.
- **Desktop control** — patched `SIGraph.java` compiled alone
  into `phase23/classes` (per §29.2), `DesktopOcrExport
  phase23/hallelujah.png phase49/desktop-hallelujah-noocr91.musicxml`
  with `testocr.file=phase23/empty-ocr.txt`: exit 0, **0 DIAG48
  lines**, `.mxl` 105,578 B, md5 `9d9028dd…` — **byte-identical
  to the 89b desktop**. DIAG48 is print-only on desktop too.
- **Downstream effect — answered:** the 149 missing supports
  change **no** downstream result on Hallelujah p01 (byte-identical
  `.mxl`: same counts, ties, slurs, beams). That settles §26.12's
  open question for this page — with the caveat that it does not
  prove supports never matter: they feed chord reduction, and on
  this page the reduction outcome is identical either way. Snow
  p2's 945 missing supports were not re-run (same class-level
  mechanism; the policy fix is page-independent), so the
  downstream-effect answer for a bad scan is still open — but the
  symptom itself is fixed at the class level, not per page.

Note on md5s: the hymn/Lindenbaum md5s moved between out84 and
out88 (`d9cc20ab…` → `75637092…` hymn; `ecbbcc84…` →
`dbd546ba…` Lindenbaum) — that is the **§40 rint fix**, already
recorded; out91 matches out88 exactly on both pages, so the
policy fix moved nothing.

### §42.7 Notes and possible future items (not started)

- `TremoloInter.java:576` uses the same reflective pattern
  (`relationClass.getDeclaredConstructor().newInstance()`) in the
  headless path (tremolo relations). No observed failure in any
  run so far; if a `Could not instantiate` line ever names a
  tremolo relation class, the fix is the same one-line policy
  entry. `ChordListMenu.java:881` and `RelationVector.java:203`
  use the same call but are UI-only, out of scope.
- No new upstream filing from this round (§42.4). The deferred
  upstream list is unchanged: #272, #21244/#15448, §11
  Profiles.getName(), §19 TColor, §27 hypot, §33 retainAll, §35
  TFormatter, §40 rint/round.

### §42.8 Files

- `teavm/patched/make_patches.py` ROUND 48 (DIAG48 in
  `SIGraph.java`, `copy_src` — file never patched before).
- `teavm/policy/src/teavm/TeavmReflectionPolicy.java` (§42
  entries, HeadHeadRelation + BeamBeamRelation).
- `teavm-fork/phase49/` — `run-noocr-wasm90.log` (DIAG48
  diagnostic, 149 HeadHeadRelation), `run-noocr-wasm91.log`
  (Hallelujah, 0/0), `run-noocr-wasm91-hymn.log`,
  `run-noocr-wasm91-lindenbaum.log`,
  `desktop-hallelujah-noocr91.{log,musicxml}` (byte-identical to
  89b desktop), `wasm-hallelujah-noocr90.musicxml`,
  `wasm-hallelujah-noocr91.musicxml` (both md5 `126771ec…`),
  `wasm-hymn-noocr91.musicxml` (= out88),
  `wasm-lindenbaum-noocr91.musicxml` (= out88),
  `compare-deep-hallelujah-p01-91.txt`,
  `compare-deep-hymn-91.txt`, `compare-deep-lindenbaum-91.txt`
  (all 2, filename only). No separate build log file was saved this
  round; the build.sh + Spike outputs (0 problems, 3,060 classes,
  28,757 methods) are in the session transcript.
- Builds: **full-out91** (current, diagnostic, DIAG44–48 prints
  in, rint-fixed classlib + §42 policy); full-out90 (DIAG48
  diagnostic, pre-fix); full-out84 remains the last
  non-diagnostic build.
- Nothing pushed, filed, or merged; `jdlehman/score-reader`
  untouched; `open-music/` and the zip untouched; no lyric
  recall re-scored.

### §42.9 Status and next

- **HeadHeadRelation SIGraph symptom: FIXED.** No remaining known
  Wasm-vs-desktop divergence on the three control pages — all at
  deep diff 2 (filename artefacts only).
- Still open (unchanged): BrowserOCR follow-up, photometric
  recovery, clean build (strip DIAG prints incl. DIAG44–48),
  real-browser Chrome run, upstream filings (deferred per
  Jonathan's 2026-11-09 decision).
- Next named: **clean build** — strip the DIAG prints
  (DIAG14/16/17/18/19/20/22/23/24/25/26/27/28/29/30/31/32 and
  successors through DIAG48) and produce a non-diagnostic build
  to replace full-out84 as the current build; then the
  real-browser Chrome run. The DIAG48 print itself should go in
  the clean build (it only fires on failure, but it is diagnostic
  code in a shipped path).

## §43 — Clean build: DIAG14–DIAG48 stripped; full-out92 verified byte-identical — verdict (a) (2026-11-10)

### §43.0 Verdict

**(a) Clean build verified.** full-out92 is the new current non-diagnostic build, replacing full-out84. All three control pages produce .mxl **byte-identical** to full-out91; deep diffs 2 (filename only) on all three. The catalog fix (§36) and the retainAll fix (§33) both survive the strip. The desktop control (stripped sources recompiled into the harness) is byte-identical to the 89b desktop. No DIAG print remains in the shipped path.

### §43.1 What was stripped

**Patched sources — `teavm/patched/strip_diag.py`, wired in as ROUND 49** at the end of `teavm/patched/make_patches.py` (after the prune step, so it runs on the freshly generated tree every build). A future diagnostic ROUND must be inserted BEFORE the ROUND 49 call, or its prints will be stripped too. Two tiers:

- *Tier 1 — generic print removal (all files):* every `System.out.print/println/printf` statement whose text contains `"DIAG<digit>`, plus the StringBuilder-println statements in TupletsBuilder/SlursBuilder (`println(sb.toString())`, `println(d46sb/d47sb/d46ab.toString())`), whose label lives in the builder, not the call. The scanner is string/char/comment aware — it skips matches inside comments (this caught the already-commented-out prints in `Constant.java`/`ConstantSet.java`, which the first version of the scanner choked on; §43.3).
- *Tier 2 — targeted scaffolding removal (9 files):* helper methods, fields, counting blocks and accounting statements that exist ONLY to feed the DIAG prints — `PageCleaner` DIAG36/37 helpers + `visit(HeadInter)` accounting + DIAG37 classification block; `Skeleton` diag34/35 helpers + call sites + DIAG35-REGION try/catch; `HeaderBuilder`/`KeyColumn` diag38/39Phase decl + assignments; `TupletsBuilder` DIAG44B/45A braced blocks + both `if (diag46)` blocks + decl; `SlursBuilder` DIAG45B/46A blocks; `StemScaler` diag31Segs + diag31t0; `LedgersPostAnalysis` DIAG41 census block; `BeamsBuilder` diag29/diag29small maps + merge ifs. Each removal asserts its expected count — if a future ROUND changes DIAG code, the strip fails loudly instead of silently leaving dead code or silently removing live code.

Totals (identical in dry-run and in the real build): **32 files changed, 161 print statements removed by tier 1, 48 targeted removals.** Post-strip verification (in the script, runs on every build): 0 `System.out.println("DIAG` lines, 0 DIAG strings and 0 `diagNN` identifiers in code (comments excluded — see §43.2).

**Entry sources (direct edits, not regenerated):**
- `TeavmMain.java`: DIAG14 print, DIAG24 print (kept `throw t;`), DIAG17 head dump, DIAG18 SIG dump, DIAG19 fingerprint loop, DIAG20 header-range loop, DIAG20b SIGP dump, DIAG22 row-fingerprint block, DIAG23 zero-positions block. All removed blocks declared only their own locals.
- `MxlWriter.java`: DIAG40 measure/wedge/nullOffset prints, diag40b construction + `println(diag40b)`, DIAG40B sortOut print. The §34 nulls-last sort comparator and `push()` null-event handling are untouched (verified by assertion in the strip script).
- `TeavmMainDiag.java`: deleted outright — standalone diagnostic copy of TeavmMain, referenced nowhere. Its class was also removed from `phase23/classes`.

**Not stripped, deliberately:**
- Operational prints in TeavmMain (IMAGE, GREY BYTES, OCR LANG, INDENTATIONS false, REACH, STAVES/HEADS/CHECK, SCORE, MXL len=/count=, TEAVM DONE/FAILED) — progress reporting the runner reads.
- Stock Audiveris prints (Table/Template printf dumps, MetronomeInter main() test code, Main/CLI output, WellKnowns error print, Sheet.dumpSystemInfos) — never called in the pipeline path.
- DIAG mentions inside `//` comments — documentation of why a fix exists (e.g. the §30 comment in `PageCleaner.visit`, the §34 comment in MxlWriter's sort comparator, the §37 (DIAG43) comment in TeavmMain).
- `PreRenderedTemplates`' "requested N maps to desktop catalog M" line (not a DIAG print): one line per catalog pair, same character as the other operational progress lines. The §41 tripwire it served is done.
- `diag45lineY`/`diag45toLine` in SlursBuilder: the DIAG45B print block is gone, but the two variables are read by the REAL purge-gate test (`abs(diag45toLine) > params.maxStaffLineDy`) — they stay. Recorded in `strip_diag.py`'s `KEPT_IDENTS` allowlist.
- The desktop harness (`phase23/src`) keeps its own DIAG prints — it is a diagnostic harness, not the build.

### §43.2 Build

- `build.sh` exit 0 (`phase50/build92.log`): ROUND 49 strip ran inside make_patches.py with the same counts as the dry run (32 files, 161 prints, 48 targeted). `patched/classes OK: 368 classes`.
- Spike build exit 0, **0 problems** (`phase50/spike92.log`): **3,055 classes, 28,726 methods**, classes.wasm 14,235,288 B (full-out91: 3,060 classes, 28,757 methods — see §43.5 for the delta).

### §43.3 Incidents during the strip (all caught before anything shipped)

Three near-misses, all caught by the strip's own verification or by the byte-identical checks — recorded so the next round doesn't repeat them:

1. **MxlWriter wrong-loop match.** The first MxlWriter strip matched `for (Inter inter : sig.inters(WedgeInter.class))` by regex and removed the REAL events-building loop (lines 2571–2580), not the DIAG40 dump loop — the pattern occurs twice in the file. The script failed its own verification (`diag40b` still referenced: `println(diag40b)` contains neither `"DIAG` nor the builder pattern) before writing, so the file was untouched. Redone with anchor-based enclosing-block removal (find the DIAG40 println, remove the `for` whose brace range contains it), plus explicit assertions that the events-building loop, the §34 comparator, and `push()` survive. Lesson: never remove a loop by a bare `for`-line regex when the same `for` shape occurs twice in the file — anchor on content inside the block.
2. **TupletsBuilder has TWO `if (diag46)` blocks.** The `boolean diag46` declaration gates two blocks (filterList/member dump at ~256 and the pair comparison at ~322). Removing the decl + first block left the second referencing a deleted variable. Fixed: remove all `if (diag46)` blocks (asserted 2), then the declaration.
3. **Desktop-control harness overwrite (OcrUtil).** The first desktop control run failed at TEXTS with `UnsatisfiedLinkError: BrowserOCR.readOcrText()` (a native `@JSBody` method). Cause: my recompile of the 31 changed patched sources into `phase23/classes` overwrote the harness's own desktop `OcrUtil` (phase23/src routes OCR through TestOcr; patched/src OcrUtil calls `BrowserOCR.recognize()` → the native method). `OcrUtil` is on the §29.2 excluded list (TeaVM-functional classes whose phase23/classes copy is NOT the patched one) — the only one of the 31 in that list. Fixed by recompiling `phase23/src/.../OcrUtil.java` back into `phase23/classes`; the control then passed byte-identically. Lesson: when recompiling patched sources into phase23/classes, NEVER include a file from the §29.2 excluded list (WellKnowns, ConstantManager, LogUtil, StepMonitoring, LoadStep, OmrExecutors, SheetStub, ConstantSet, BookManager, AliasPatterns, UriUtil, OmrFont, Book, OcrUtil) — the harness's own variant wins there. (UriUtil was already excluded from the recompile because it has no class in phase23/classes.)
4. **Desktop DEBUG-log NPE noise (pre-existing, non-fatal).** The desktop control log carries 2,599 `NullPointerException: TreeMap.get() is null` lines from `StemBuilder.getTotalLength` ← `StemBuilder.toString`, thrown while Logback formats a `logger.debug` call in `StemBuilder.retrieveAllItems` (STEMS step). They are logged, not fatal — the run continued past STEMS to TEXTS and completed. Pre-existing desktop behaviour (a `toString()` that NPEs when a debug line formats a StemBuilder in that state), unrelated to the strip; the 89b reference was produced by the same harness. Recorded only.

### §43.4 Verification (full-out92, no-OCR unless noted)

| Page | out92 | out91 reference | Deep diff vs desktop 89b |
|---|---|---|---|
| Hymn | 44,105 B, md5 `75637092…` | byte-identical | **2** (filename only) |
| Hallelujah p01 | 105,434 B, md5 `126771ec…` | byte-identical | **2** (filename only) |
| Lindenbaum | 99,305 B, md5 `dbd546ba…` | byte-identical | **2** (filename only) |

- **Catalog fix survives (§36):** BWV 227 p02 — 338 notes / 297 pitched / 41 rests, counts exactly equal to desktop (338/297/41) and to the wasm82 run. HEADS 787 in the run log (was HEADS 0 under full-out63).
- **retainAll fix survives (§33):** Gute Nacht p01 (multi-page preparation, the actual CME page from the full-out63 run) — 530 notes / 509 pitched / 21 rests, counts exactly equal to the wasm82 run; total 530 = desktop 530 (desktop splits 510 pitched / 20 rests vs Wasm 509 / 21 — the same 1-note pitched/rest difference already present in the full-out82 multi-page results, i.e. pre-existing, not a strip effect). HEADERS completes, no CME, exit 0.
- **Note on the two Gute Nacht inputs:** `phase23/lieder-gute-nacht.gray` (bars 1–12, GT 223 notes per the manifest) and the multi-page `p01.grey` (full first page, 530 notes) are DIFFERENT pages of the same song — same byte size, different bytes. The out92 run on the phase23 file gives 223 pitched = its ground truth; the "530" figure belongs to the multi-page file. Both check out.
- **Desktop control:** the 31 changed patched sources + `MxlWriter.java` + `TeavmMain.java` recompiled into `phase23/classes` (javac exit 0; TeavmMain needed `lib/teavm-jso-0.16.0.jar` on the classpath for the `@JSBody` annotation). Hallelujah desktop run exit 0, `.mxl` 105,578 B, md5 `9d9028dd…` — **byte-identical to the 89b desktop**. The strip is print-only on the desktop side too. (After the OcrUtil incident in §43.3, the desktop `OcrUtil` was recompiled from `phase23/src`.)
- No lyric recall re-scored (per task). `open-music/` and the zip untouched. `jdlehman/score-reader` untouched; nothing pushed, filed, or merged.

### §43.5 The 3,055 vs 3,060 class delta

full-out92 compiles 5 fewer classes and 31 fewer methods than full-out91. The teadbg string diff shows exactly what left: the removed DIAG helper methods (`diag31Segs`, `diag34Dump`, `diag35Band`, `diag35DumpImg`, `diag35Erased`, `diag36Corner/Count/Height/Pixels/Width`, `diag37InEllipse/InGlyphRun/Snap`, `setDiag36Img`) and the lambdas that existed only inside DIAG dumps (`PageCleaner$visit$lambda$…`, `TeavmMain$run$lambda$…`, `BeamsStep$doEpilog$lambda$…`). This is dead-code elimination of classes/methods reachable only from the removed diagnostics — the expected shape of a clean build, and the byte-identical .mxl files on all three control pages plus the byte-identical desktop control prove nothing live went with them.

### §43.6 Status and next

- **Current build: full-out92** (non-diagnostic; replaces full-out84). full-out91 kept as the last diagnostic build. The DIAG prints are gone from the shipped path; to diagnose again, add a new ROUND before ROUND 49 in make_patches.py (and update `strip_diag.py` if the new DIAG code adds scaffolding — the strip fails loudly on a mismatch).
- Still open (unchanged): BrowserOCR follow-up, photometric recovery, **real-browser Chrome run** (next named item — everything so far is Node v24.22.1; needs Jonathan's machine, no Chrome in this VM), upstream filings (deferred per Jonathan's 2026-11-09 decision: #272, #21244/#15448, §11 Profiles.getName(), §19 TColor, §27 hypot, §33 retainAll, §35 TFormatter, §40 rint/round).
- Artefacts: `teavm-fork/phase50/` (build92.log, spike92.log, strip-dryrun.log, desktop-compile92.log, all six Wasm run logs + .mxl files, desktop Hallelujah log + .mxl). Strip script: `teavm/patched/strip_diag.py`; ROUND 49 call at the end of `teavm/patched/make_patches.py`.

## §44 — Full-out92 validation fix round (2026-11-10)

Fix-round items from `open-music/FULLOUT92_RESULTS.md` (Part 1 divergences
1–4), one diagnostic round each, in order. Each subsection is one item;
§44.1 is Mozart Kyrie p20 (divergence 1). Current build after §44.1:
**full-out94** (0 problems, 3,055 classes, 28,726 methods) — supersedes
full-out92 as the current clean build. DIAG49 (this item's diagnostic) is
stripped; no DIAG print remains in the shipped path.

### §44.1 Mozart Kyrie p20 export trap — null fifths on a KEY_CANCEL key; contained writer fix, page exports (2026-11-10)

**Verdict: (a) DONE — contained fix applied and verified. Mozart Kyrie p20
exports under Wasm for the first time (165,102 B, 435 notes / 408 pitched,
12 parts × 5 measures). Hymn / Hallelujah p01 / Lindenbaum byte-identical
to full-out92; desktop Mozart byte-identical to the pre-fix desktop.**

#### §44.1.1 Localisation — DumpSeq + DIAG49

Trap stack in the full-out92 validation log
(`open-music/wasm92/mozart-kyrie-p20/wasm/mozart-kyrie-p20.log`), PCs
converted hex→decimal with Python (the §12.9 lesson — hand conversion
produced wrong addresses once already):

| frame | PC (hex → dec) | method (DumpSeq containment on `full-out92/classes.wasm.teadbg`) |
|---|---|---|
| [5268] innermost | 0x2f0679 → 3081849 | `teavm.MxlWriter.processKey` [3081070..3084019) |
| [24242] | 0x8c6a85 → 9202309 | `teavm.MxlWriter.processKeys` [9201813..9202767) |
| [5263] | 0x2ed74c → 3069772 | `teavm.MxlWriter.processMeasure` [3064744..3077776) |
| [5258] | 0x2ebb7f → 3062655 | `teavm.MxlWriter.processPart` [3061839..3062924) |
| [24207] | 0x8c3698 → 9189016 | `teavm.MxlWriter.processSystem` [9188075..9190137) |
| [24196] | 0x8c2c94 → 9186452 | `teavm.MxlWriter.processLogicalPart` [9185718..9186543) |
| [24167] | 0x8c11fc → 9179644 | `teavm.MxlWriter.processStub` [9176808..9179823) |
| [24091] | 0x8bb0ed → 9154797 | `teavm.MxlWriter.processPartList` [9153509..9154900) |
| [23919] | 0x8b1c26 → 9116710 | `teavm.MxlWriter.processScore` [9111788..9118778) |
| [22537] | 0x626386 → 6448006 | `teavm.MxlWriter.build` [6447807..6448052) |

A perfectly coherent chain, all in our own writer — no Audiveris frame,
no shim frame. The trap site is the same function family as the old
full-out63 export traps (`wasm-function[5266]`), now `[5268]`.

DIAG49 (prints in `MxlWriter.processKeys` / `processKey`, entry code —
not a make_patches.py ROUND, since MxlWriter lives in `entry/src` and
strip_diag.py ROUND 49 only strips patched sources; removed by hand
afterwards, verified by grep) names the call. Diagnostic build
full-out93 (0 problems, 3,055 classes, 28,726 methods) reproduces the
trap at the identical function indices ([5268]…[22537], PCs shifted
slightly by the added prints). Last prints before the trap:

```
DIAG49 key measure=Measure{#3P11} global=true key=KeyInter#21401{(0.796/0.796) staff:11 KEY_SHARP_1 pitch:-1.9 fifths:1} fifths=1 cancel=false staff={Staff id=11 left:337 right:3928}
DIAG49 key done measure=Measure{#3P11} key=KeyInter#21401{...}
DIAG49 keys measure=Measure{#4P11}
DIAG49 key measure=Measure{#4P11} global=true key=KeyInter#21403{(0.799/0.799) staff:11 KEY_CANCEL pitch:-2.2 fifths:null} fifths=null cancel=true staff={Staff id=11 left:337 right:3928}
RuntimeError: dereferencing a null pointer   (no "DIAG49 key done")
```

**Trapping call, named: `MxlWriter.processKey`, `int fifths =
keySignature.getFifths();` — auto-unboxing a null `Integer` for the
KEY_CANCEL key in measure #4P11 (staff 11).** The DIAG49 print itself
reads `getFifths()` boxed (no unbox) and survives; the staff is
non-null, and `global=true` means the non-global staff path is not even
reached — the unboxing is the first and only null dereference on the
failing path. `hasSameKeys()` (called before, in `processKeys`) is
null-safe here (its `prevFifths != null` guard).

The identical key exists on **all three sides** (ids differ —
allocation order only; staff, grade, pitch, fifths agree exactly):

| side | key | staff | grade | pitch | fifths |
|---|---|---|---|---|---|
| Wasm full-out93 | KeyInter#21403 | 11 | 0.799 | −2.2 | null (KEY_CANCEL) |
| Desktop harness (DIAG49 writer) | KeyInter#21179 | 11 | 0.799 | −2.2 | null (KEY_CANCEL) |
| Stock batch desktop | KeyInter#21577 / #21565 | 11 | 0.799 | −2.2 | null (KEY_CANCEL) |

Desktop "Key built" lines agree exactly too (2 keys: staff-11
KEY_SHARP_1 fifths 1, then the KEY_CANCEL fifths null, same grades both
sides). The Wasm DIAG49 key-entry lines are a subset of the desktop's
(2 vs 7 — Wasm dies at #4P11; the measure-visit order is identical up
to the trap). The one asymmetry in the DIAG49 record is the five
measure-1 FROZEN header keys (see §44.1.6).

#### §44.1.2 Root cause — the null is Audiveris data, the trap is catchability (§34 family)

`KeyInter.getFifths()` (`KeyInter.java:349`) returns the `Integer fifths`
field as-is for cancel keys: the recompute branch is guarded by
`if ((fifths == null) && !isCancel())`, so a cancel built by
`KeyInter.createAdded(staff, alters)` (`KeyInter.java:766`, `new
KeyInter(null, (Integer) null)`) keeps `fifths == null` — despite the
javadoc promising 0 for a KEY_CANCEL. Stock `PartwiseBuilder.processKey`
does `key.setFifths(new BigInteger("" + keySignature.getFifths()))` —
`"" + null` is `"null"`, so it throws `NumberFormatException: For input
string: "null"`, caught by processKey's own `catch (Exception ex)`,
logged as `Error visiting KeyInter#21577 ...`, and the key is skipped
(the measure is otherwise exported; the stock `.mxl` carries 0
`<cancel>` elements). Our writer's `int fifths = ...` unboxes the same
null to an NPE — catchable on the JVM (the desktop harness logs the
same `Error visiting KeyInter#21179` warn and continues), but an
**uncatchable Wasm trap** under TeaVM WasmGC. The Wasm/desktop
difference is catchability only, not data — the exact §34 pattern
(null timeOffset), one file over.

#### §44.1.3 Cause vs consequence — the 12-parts/5-measures structure is NOT the trap's cause, and NOT a Wasm divergence

The report's open question was whether the structure (Wasm 12 parts,
5 measures/part vs desktop 6 parts, 15–17 measures/part) causes the
trap. It does not, and it is not a Wasm divergence at all. Evidence
chain, each link measured:

1. **The desktop harness reproduces the Wasm structure exactly.**
   `DesktopOcrExport` on the PNG regenerated from the same `.grey`
   bytes (PIL mode `L`, `phase51/mozart-kyrie-p20.png`), same patched
   classes as Wasm: `Systems: #1[1..12]`, `12 parts along 1 system`,
   5 measures/part, the same `BarsRetriever: No startColumn found for
   multi-staff System#1` warning and the same `MeasureFixer: No target
   duration for measures local IDs [1..5]`. Its `.mxl` is 12 parts × 5
   measures, 434 notes / 407 pitched. SCALE is identical on all sides
   (`interline(21,23,25) line(2,4,6) beam(12)`), raw clusters identical
   (`12 of sizes [5]`), slope identical (0.00175).
2. **Input is exonerated.** Stock batch Audiveris run on that same
   regenerated grey PNG (`phase51/desktop-stock-grey/`) splits into 3
   systems / 6 parts × 17 measures, 448 notes / 391 pitched — identical
   to the RGB-input batch run. The grey preparation (PIL `convert("L")`
   vs Audiveris max-RGB-to-gray) does not cause the merge.
3. **The merge is Jonathan's own repo patch.** `PeakGraph.java` is in
   make_patches.py ROUND 3 COPY_ASIS (copied as-is from the repo's
   0001-score-reader.patch). The repo's working tree adds
   `PeakGraph.joinByLeftLines` (127 added lines, `git diff`):
   consecutive staves with no connecting bar line are joined into one
   system when a thin vertical line left of their start crosses the
   gap. On this page it fires twice — `Staves #6 and #7 joined by a
   line on their left at x:336` and `Staves #7 and #8 joined ... at
   x:336` — merging all 12 staves into one system, hence 12 parts and
   only 5 measures (the single system's measures; the startColumn /
   MeasureFixer warnings follow from the merged system). The desktop
   batch log instead carries `ClustersRetriever: Pairing clusters
   CC5833 & CC6034` (absent from both harness and Wasm logs) and no
   join lines. Whether the x:336 line is a genuine system-joining line
   or a false positive of `joinByLeftLines` on this page is a
   score-reader-patch question for Jonathan's agent, not a TeaVM
   question — Wasm faithfully reproduces the patched desktop behaviour
   here.
4. **The trap is independent of the structure.** The null-fifths cancel
   key exists in the stock SIG too (same staff/grade/pitch), and stock
   trips on it in its own export — the trap would fire under Wasm even
   with correct 3-system grouping. Structure and trap are two separate
   items: the structure is a repo-patch effect (open item, §44.1.6d);
   the trap is a writer catchability gap (fixed here).

#### §44.1.4 The fix (our MxlWriter only, `teavm/entry/src/teavm/MxlWriter.java`)

One null guard in `processKey`, before the unboxing:

```java
Integer fifthsObj = keySignature.getFifths();
if (fifthsObj == null) {
    logger.warn("Skipping {} with null fifths in {}", keySignature, current.page);
    return;
}
int fifths = fifthsObj.intValue();
```

Skipping emits no `<key>` element for the cancel — exactly stock's
observable output (no `<cancel>` in any of the three reference files).
No guessed fifths is emitted: the cancelled value is the null
information itself, and deriving it from the NATURAL members would be
new semantics, not a minimal guard. The guard must sit *before* the
unboxing, not in the existing `catch (Exception)` — under WasmGC the
trap is uncatchable. Desktop-neutrality, verified by output, not
asserted: on the JVM the old path caught the NPE in the same method and
skipped the same key, so the `.mxl` is unchanged (see §44.1.5); only
the log line changes (`Skipping ... with null fifths` instead of
`Error visiting ... NullPointerException`). No other null site is
guarded — `getStaff()` is non-null on every key observed on both sides,
and no null-staff key exists in this SIG; speculative guards were not
added.

#### §44.1.5 Verification — full-out94 (0 problems, 3,055 classes, 28,726 methods)

- **Mozart Wasm** (`phase51/run-mozart94.log`, 550.7 s wall): exit 0,
  `MXL len=165102 exportMs=294 totalMs=549956`, `TEAVM DONE`,
  `.musicxml` 165,102 B, **12 parts × 5 measures, 435 notes / 408
  pitched**. The guard fires exactly once in the log
  (`Skipping KeyInter#21403 ... KEY_CANCEL ... fifths:null`). Tripwire
  holds: `PreRenderedTemplates: requested 78 maps to desktop catalog
  80`, same as full-out92. 0 DIAG49 lines in the shipped run.
- **Wasm vs harness desktop** (like-for-like reference,
  `phase51/desktop-mozart-noocr93.musicxml`, 434 notes / 407 pitched):
  per-part counts identical except P4 (+1 note / +1 pitched under
  Wasm: 76/73 vs 75/72); all other 11 parts identical. Deep diff
  (`phase51/compare-deep-mozart94.txt`): **25** — 2 filename (known
  §22 `/hymn-satb.png` artefact) + 5 missing measure-1 `<key>` elements
  (see §44.1.6a) + the P4 extra note and its rhythm knock-ons + 5
  pitch-`<alter>` diffs + slur/notations wobbles + 1 `default-x`
  (261 vs 258, §22 ±-tenths family).
- **Wasm vs stock batch** (6 parts × 17 measures, 448 / 391): the
  structural gap remains and is the §44.1.3 repo-patch effect, not a
  Wasm gap — the like-for-like comparator is the harness desktop, which
  Wasm matches to 25 deep diffs.
- **No regression — Wasm controls byte-identical to full-out92
  (phase50):** hymn 44,105 B md5 `75637092…`, Hallelujah p01 105,434 B
  md5 `126771ec…`, Lindenbaum 99,305 B md5 `dbd546ba…`.
- **No regression — desktop control byte-identical:** the harness
  Mozart run with the fixed writer
  (`phase51/desktop-mozart-noocr94.musicxml`, 165,658 B) is
  **byte-identical** (md5 `54514a01…`) to the DIAG-writer desktop file
  — the fix changes no desktop output. (The guard fires once there
  too, KeyInter#21173, same key — id differs by allocation order
  across runs.)
- **Incident during verification (own error, caught):** the first
  hymn/Hallelujah control runs used `phase23/hymn-clean.gray` /
  `hallelujah-clean.gray` (2500×3527, 8,817,500 B) — different files
  from the §43 control inputs — and failed fast with `Sheet ignored`
  (interline 267, same shape as the Beethoven typeset rejection).
  Re-ran with the correct §43 inputs (`teavm/hymn-satb.gray`,
  `phase23/hallelujah-satb.gray`, 2480×3507/3509); those are the
  recorded byte-identical runs. The `-clean` files are not §43
  controls.

#### §44.1.6 Residuals — named, not started

(a) **Five missing measure-1 header keys (Wasm-only, small).** The
desktop writer emits `<key><fifths>-1</fifths></key>` in measure 1 of
P1, P2, P5, P11, P12; Wasm emits none of them (its measure-1 `keys`
sets are empty — DIAG49 shows `hasKeys()` false for those measures,
while the desktop's `KeyInter#467/#469/#475/#485/#488` are FROZEN
header keys, frozen by `StaffHeader.freeze()` at HEADERS). The P11 m3
KEY_SHARP_1 (fifths 1) IS present on both sides, so this is specific
to the frozen header keys' measure assignment, not to keys in general.
Consequences visible in the deep diff: 5 of the pitch-`<alter>` diffs
(notes whose B-flat spelling depends on the missing initial key) are
downstream of this, not independent. **Next diagnostic DIAG50 (named,
not started):** dump, per staff, the header KeyInter's abscissa vs
measure 1's abscissa range on both sides (harness vs Wasm) — prime
hypothesis is a 1-px boundary effect in the measure assignment
(consistent with the known §18/§20 sub-pixel jitter), possibly via
the merged system's missing startColumn; the header keys exist in the
SIG on both sides (same 2 "Key built" lines), so the gap is in
assignment, not detection.
(b) **P4 +1 note under Wasm.** One extra note (+ backup + forward) in
P4 measure 2, plus a dot/backup-duration wobble in P4 measure 5
(backup 84 vs 87; one note gains a `<dot>`). Pre-existing pipeline
difference, not a fix artefact (P4 is exported before the trap site
at P11 m4). Root cause unknown — one extra head vs a chord split
needs a SIG-level comparison (DIAG18-style), not started here.
(c) **Slur/notations wobbles:** one extra slur in P5 m3 notations,
one slur `number` 1 vs 2 (same geometry), two notes gaining/losing a
notations element, one fermata+slur vs fermata-only. Same small-SIG
family as (b); not chased.
(d) **The `joinByLeftLines` merge itself.** Whether the x:336 line
should join staves 6–7–8 on this page (and hence whether 12×5 or 6×17
is the *right* structure) is a score-reader-patch question — the
patched desktop and Wasm agree with each other, and stock disagrees
with both. If the join is judged a false positive, the fix belongs in
Jonathan's repo patch, not in the TeaVM spike.
(e) No TeaVM defect in this round — nothing to file upstream for
§44.1 (the upstream list is unchanged). No lyric recall re-scored
(no-OCR runs both sides, per task). `open-music/` was read-only;
`choral-test-set.zip` not repacked; `jdlehman/score-reader` untouched
(only `git diff` read); nothing pushed, filed, or merged.

#### §44.1.7 Artefacts

- `teavm-fork/phase51/` — DIAG49 build + runs (`build93.log`,
  `spike93.log`, `run-mozart93.log` trap reproduced,
  `MxlWriter.java.pre-diag49` + pre-DIAG `MxlWriter*.class` backups);
  fixed build + runs (`build94.log`, `spike94.log`,
  `run-mozart94.log`, `wasm-mozart-noocr94.musicxml` 165,102 B);
  controls (`run-hymn-94.log`, `run-hallelujah-94.log`,
  `run-lindenbaum-94.log` + three `.musicxml` files, byte-identical
  to out92); desktop (`desktop-mozart-noocr93.log` + `.musicxml`
  DIAG writer, `desktop-mozart-noocr94.log` + `.musicxml` fixed writer
  byte-identical, `mozart-kyrie-p20.png` regenerated from the `.grey`
  bytes); stock control (`desktop-stock-grey/` + `.log`, 6×17);
  `compare-deep-mozart94.txt` (25 diffs).
- Builds: `full-out93/` (diagnostic, DIAG49 in — kept as the
  diagnostic artefact), `full-out94/` (**current clean build**,
  DIAG49 stripped, fix in; 0 problems, 3,055 classes, 28,726 methods).
  `phase23/classes/teavm/MxlWriter*.class` now holds the fixed writer
  (compiled alone from `entry/src`, per §29.2 — no other harness file
  touched), so the desktop harness matches `entry/src`.
- Fix location: `teavm/entry/src/teavm/MxlWriter.java`,
  `processKey` (null-fifths guard + `§44.1` comment). No
  make_patches.py ROUND was needed (MxlWriter is entry code, not a
  patched Audiveris file).

### §44.2 Schumann Widmung — Wasm −122 pitched; root is the missing key signature, localised to KeyBuilder — verdict (c), inconclusive with named next diagnostic (2026-11-10)

#### §44.2.0 Verdict

**(c) Inconclusive — but localised to one method.** The −122 pitched notes are
not a head-detection loss at all. The full causal chain is measured down to
the staff header: on Wasm the key signature (−4 flats) is never found, so the
header stops after the clef, the time-signature ROI opens inside the
key-signature flats, the header time build fails, the SYMBOLS-step fallback
reads the time as 3/4 instead of 3/2, the rhythm step caps every voice at
3/4, and 128 chords are left without a timeOffset and dropped by the writer
(desktop: 6). What is **not** measured — and therefore not fixed — is the
mechanism *inside* `KeyBuilder` that makes the key vanish on Wasm: whether
its projection peaks differ or its peak-pattern logic diverges. That is the
named next diagnostic (DIAG51, §44.2.6). No fix was applied, no TeaVM defect
was localised to a single small operation, no repro was built, nothing was
filed. `full-out94` remains the current clean build; the tree was restored
and re-verified byte-identical (§44.2.7).

#### §44.2.1 Symptom

Schumann Widmung (`lieder-schumann-widmung`, GT 322 notes), no-OCR both
sides, `prep92` input:

| | Desktop | Wasm |
|---|---|---|
| Notes / pitched | 299 / 291 | 175 / 169 |
| Per part (notes / pitched) | P1 54/49, P2 245/242 | P1 25/21, P2 150/148 |
| Time signature in output | `<beats>3</beats><beat-type>2</beat-type>` (3/2) | `<beat-type>4</beat-type>` (3/4) |
| `<key>` elements | 2 × `<fifths>-4</fifths>` | **0** |
| `<alter>` elements | 207 × −1 | 19 × −1 |
| Wasm `.musicxml` md5 | — | `a398a44f9b07deb3a83acddcfddd1c93` |
| Desktop `.mxl` md5 | `3d452d3ec54b0f52f576418f4d7437f6` | — |

The loss is uniform across all bars in both parts (voice 4–7 → 1–4 per bar;
piano 17–28 → 10–18 per bar), not one measure. All 169 Wasm notes match GT
on step+octave (169/169), so the task brief read it as recall loss with
precision intact. **Correction to that reading:** the match was step+octave
only. Comparing full pitch (step+alter+octave) on the 169 shared notes,
**107 have the wrong alter on Wasm** (desktop −1, Wasm 0). The missing key
signature corrupts the exported pitches of most surviving notes as well as
the count. Original log pointers: "no correct rhythm" 1 stack (desktop
batch) vs 11 (Wasm); "No timeOffset" 3 lines vs 95; "too long" 0 vs 66.

#### §44.2.2 Step census (DIAG50, full-out95) — the head-loss hypothesis is refuted

Entry-side step prints (HEADS counts, SIG counts, per-system/per-staff
heads, bounds checksum) in `TeavmMain.java` / `DesktopOcrExport.java`,
same patched files both sides; prints side-effect-free (`.mxl`
byte-identical to the full-out94 baselines on both sides).

| Step | Desktop heads (SIG) | Wasm heads (SIG) |
|---|---|---|
| HEADS | 637 (1007), check 2052454 | 696 (997), check 2151180 |
| STEMS | 637 (1298) | 696 (1312) |
| REDUCTION | 286 (902), check 917643 | 286 (833), check 917643 |
| CUE_BEAMS / TEXTS / MEASURES | 286 | 286 |
| CHORDS | 297 (1249), check 962742 | 297 (1180), check 962742 |
| CURVES | 297 (1306) | 297 (1237) |
| SYMBOLS | 297 (1555) | 297 (1543) |
| LINKS / RHYTHMS / PAGE | 297 (1399) | 297 (1340) |

Per-system/per-staff head counts are identical from REDUCTION onward (e.g.
sys1 59 [7,24,28], sys2 81→84 [13,42→45,26]). **Conclusion: the head sets
converge at REDUCTION — the 59 extra Wasm heads at HEADS are all pruned,
and the surviving heads are identical (same bounds checksum). The "heads
lost between HEADS and SYMBOLS" suggestion in the task brief is refuted;
the loss is downstream, in RHYTHMS.** (The 59 extra Wasm heads at HEADS —
template matching producing more head candidates under Wasm — are pruned
identically and are not the loss; not chased.)

#### §44.2.3 Rhythm census (DIAG50, same builds) — the loss is 128 un-timed chords

Same 299 chords both sides (8 rests). Desktop: `noTime=6,
noTimeHeads=6`. Wasm: `noTime=128, noTimeHeads=128`. **128 − 6 = 122 =
exactly the pitched gap (291 − 169).** Content-aligned per-chord diff
(`phase52/compare_diag50.py`, aligned by measure + sorted head centers,
never by id per §39.3): 287 shared chord keys, 0 only-desktop, 0
only-Wasm; field diffs **dur 0, staff 0, rest 0, heads 0**; only voice
(246) and off (117) differ. **Rhythm inputs are identical; only its
outputs differ.**

Voice excess: Wasm voices carry `excess:1/4` (mostly); desktop has no
excess voices. Concrete example, `Measure{#1P2}` (3/2 = 12 eighths):
desktop `Voice{#1}` holds 12 eighth-note chords summing to exactly 3/2.
Wasm `Voice{#1 excess:1/4}` holds only the first 8 (summing to 1), the
last 4 split into `Voice{#2}` with `off=null`. A voice summing to 1 being
"excess 1/4" implies the expected measure duration under Wasm is **3/4,
not 3/2**. Same pattern in `Measure{#6P2}` (desktop's one failing stack:
6 no-time chords there; Wasm fails it the same way plus all others).

#### §44.2.4 The time-signature decision (ROUND 50, full-out96)

`TimeColumn.checkConsistency` prints (DIAG50, `TimeColumn.java`):

- Desktop, system 1: WHOLE eval `TIME_THREE_FOUR` (~0.91–0.96 raw,
  grade ~0.73–0.76), NUM eval `TIME_THREE` (~0.9995), DEN eval
  `TIME_TWO` (~0.9998). `timeGrades system=1 grades={3/2=0.9522919166850515,
  3/4=0.7520103803175632}`, chosen 3/2. Only system 1 has a time column
  (the time sig appears only in the first system's header).
- Wasm, system 1: **zero `DIAG50 timeEval` lines**, but `timeGrades
  system=1 grades={3/4=0.7453268590078621}`, chosen 3/4. The 3/2
  candidate never exists in the grades map.

Selection builds `Map<TimeValue, AbstractTimeInter[]>` via
`getValueVectors()` (wholes from `builder.wholes`; pairs from
`builder.nums` × `TimeTopBottomRelation` edges), mean grade per value,
picks best with strict `>` over a `HashMap` iteration. The desktop margin
is wide (0.95 vs 0.75), so this is **not** a tie/order flip — the 3/2 pair
is absent on Wasm.

#### §44.2.5 The header time range (DIAG50b/c, full-out97/98) — localised to the key signature

Entry-level prints in `HeaderTimeBuilder.findCandidates` /
`WholeAdapter` / `HalfAdapter` / `browseProjection`:

- Desktop, system 1, staff 1/2/3: `timeFind ... hasStart=true width=35
  minWidth=21`; each half 1 trial, 1 glyph: WHOLE `[433,250,35,81]`
  `TIME_THREE_FOUR(0.90974)`; NUM `[434,250,33,38]` `TIME_THREE(0.99957)`;
  DEN `[433,293,35,38]` `TIME_TWO(0.99979)`.
- Wasm, system 1, staff 1: `timeFind ... width=61 minWidth=21` — the
  range starts ~x=331 (key-signature area, not the time sig). WHOLE:
  parts `[180, 224, 225, 183, 184]`, trials=2, glyphs at
  `Rectangle[331, 250, 39x55]` with top evals `DYNAMICS_SF(0.25604)` and
  `BOW_UP(0.12980)` — junk, no time shape. NUM: parts
  `[228, 224, 225, 229]`, glyph `[331, 250, 39x38]`, evals=0, top=none.
  DEN: parts `[231, 232, 233]`, trials=0 (no evaluation at all). Same
  shape on staff 4/7/10 (first staff of systems 2/3/4): WHOLE tops
  `FLAG_1_DOWN` / `FLAG_1`, NUM evals 0 or `DYNAMICS_F`, DEN trials=0.

ROI + spaces print (`browseProjection`):

| | Desktop staff 1 | Wasm staff 1 |
|---|---|---|
| roi / browseStart | `x=411, w=84`, 411 | `x=309, w=84`, 309 |
| spaces | `[Space(412-433), Space(467-494)]` | `[Space(309-330), Space(334-336), Space(348-351), Space(355-361), Space(369-373), Space(376-383), Space(390-392)]` |
| range | `[433, 467]`, width 35 | `[330, 391]`, width 61 |

`browseStart` comes from `staff.getHeaderStop()` (the end of clef +
key processing). **On Wasm the header stops 102 px too early, right
after the clef, before the key signature** — so the time ROI opens inside
the flats, the spaces are fragments between flat symbols, and the range
covers the key signature instead of the time signature.

Two corollaries, both measured:

- `timeFind` fired only for the first staff of each system on Wasm
  (staff 1, 4, 7, 10), while desktop fired for staff 1, 2, 3 (system 1).
  Consistent with `retrieveTime` returning −1 after the first staff's
  `filterCandidates()` fails (the loop exits before staves 2–3).
- The Wasm 3/4 comes from the **SYMBOLS-step fallback**, not the header
  path: the header path produced no whole inter (zero `timeEval` lines)
  and no header time, yet `timeGrades {3/4}` printed — the only other
  `checkConsistency` caller is the `BasicTimeColumn` built by
  `InterFactory.handleTimes` from the SYMBOLS-step whole classification
  (`TIME_THREE_FOUR`) of the real time-sig glyph. (Inferred from the
  call sites, not directly printed; see §44.2.6 for the confirmation
  print.)

**Root (measured): the key signature is not found on Wasm.**
`KeyBuilder` on desktop (DEBUG): `Staff#1 hilos: [(331,331,333),
(352,353,354), (374,374,375), (395,395,397), (440,440,443),
(456,456,459), (522,523,525)]` — peaks at x≈331/352/374/395 are the four
flats, ~21 px apart — `peak dxs:[21.0, 21.5, 21.5] mean:21.25
maxPeakDx:32 cutOver:28.09`, then `TREBLE 0.75 0.74 0.75 0.75 key:0.973`.
On Wasm there is no key at all (0 `<key>` elements, 19 vs 207 alters),
so `headerStop` never advances past the clef.

Causal chain, complete: **KeyBuilder finds no key on Wasm → headerStop
= 309 (clef end) instead of 411 (key end) → time ROI opens at 309 inside
the flats → header time range is junk (width 61) → no header time inter
→ SYMBOLS fallback reads 3/4 → rhythm caps voices at 3/4 → 128 chords
un-timed (vs 6) → writer drops them (−122 pitched) and 107/169 surviving
notes lose their flats.**

#### §44.2.6 What was ruled out, and the next diagnostic

Ruled out in this round: head loss between HEADS and SYMBOLS (§44.2.2);
template matching / classifier grades / stem-beam linking as the loss
mechanism; a specific shape or staff; rhythm inputs differing (§44.2.3);
a tie/order flip in `TimeColumn.checkConsistency` (§44.2.4); the header
time classifier itself (it was never called on the right glyphs,
§44.2.5).

**Next diagnostic (DIAG51, not started — one print round):** `KeyBuilder`
hilos/peaks/grades on both sides — print the projection peak list
(`hilos`), the `peak dxs` / `cutOver` computation, and the key-grade
decision per staff, same DIAG-round pattern (prints in `KeyBuilder.java`
via a new ROUND before ROUND 49; entry-side prints not needed). That
distinguishes the two remaining hypotheses: (i) the NO_STAFF projection
in the header area differs on Wasm (staff-line removal / source pixels),
so the flat peaks are absent or shifted; (ii) the peaks are the same but
the peak-pattern logic (dx means, `cutOver`, grade thresholds) diverges
under TeaVM. Also confirm the §44.2.5 fallback inference with one print
identifying the column class in `timeGrades` (header vs basic). Stop
rule from the task applies: if DIAG51 localises to a single small TeaVM
operation, build a minimal repro (do not file); if it localises to a
contained desktop-neutral fix, apply it with the §44.2 verification
(Widmung recovered to ~291 pitched + the three control pages
byte-identical); otherwise report (c) again with the next step named.

#### §44.2.7 Close-out: tree restored, full-out94 still the current clean build

No fix ships from this round (verdict (c)), so no new clean build was
cut. Close-out verified:

- Entry sources restored by hand from the pre-DIAG50 backups
  (`phase52/TeavmMain.java.pre-diag50`,
  `DesktopOcrExport.java.pre-diag50`); `phase23/classes` restored
  (`HeaderTimeBuilder`/`TimeColumn` recompiled alone from the stripped
  `patched/src`, per §29.2; `DesktopOcrExport`/`TeavmMain` class files
  restored from the `.pre-diag50` backups — note: `TeavmMain.java` does
  not compile against the harness classpath alone, it needs the TeaVM
  `jso` jar, so the class backup is the right restore).
- Default build (no `TEAVM_KEEP_DIAG`) → `full-out99`: **0 problems,
  3,055 classes, 28,726 methods — exactly full-out94**. Strip removed
  171 prints / 34 files (161 + 10 DIAG50 prints, 32 + 2 files), so ROUND
  50's prints are stripped by the default build. Wasm Widmung on
  full-out99 is byte-identical to the out94 output (md5 `a398a44f…`,
  0 DIAG50 lines); desktop Widmung on the restored harness is
  byte-identical to the out94 `.mxl` (md5 `3d452d3e…`, 0 DIAG50 lines).
  `full-out99` is kept as the re-verification artefact; **full-out94
  remains the named current clean build**.
- `make_patches.py` ROUND 50 stays in the file (stripped by the default
  build, like ROUNDs 44–48); the `TEAVM_KEEP_DIAG` mechanism added this
  round stays in `strip_diag.py` (env var `TEAVM_KEEP_DIAG=<n>` makes
  tier-1 stripping skip that DIAG number's prints; default strips
  everything as before — a general facility, documented in the
  strip_diag.py docstring).
- One incident during close-out: the runtime restarted while the
  desktop noocr99 verification run was in flight (log written, no
  `.musicxml` produced); the run was re-executed from the verified
  restored state and passed.
- `open-music/` was read-only; `choral-test-set.zip` not repacked;
  `jdlehman/score-reader` untouched; nothing pushed, filed, or merged.
  No lyric recall re-scored (no-OCR runs both sides, per task).

#### §44.2.8 Artefacts

- `teavm-fork/phase52/` — backups (`TeavmMain.java.pre-diag50`,
  `DesktopOcrExport.java.pre-diag50`, `TeavmMain.class.pre-diag50`,
  `DesktopOcrExport.class.pre-diag50`); baselines
  (`run-widmung94.log`, `wasm-widmung-noocr94.musicxml`,
  `desktop-widmung-noocr94.log`, `desktop-widmung-noocr94.musicxml`,
  `widmung.png` regenerated from the `.grey` via PIL mode `L`); DIAG50
  (`build95.log`, `spike95.log`, `run-widmung95.log`,
  `wasm-widmung-noocr95.musicxml`, `desktop-widmung-noocr95.log`,
  `desktop-widmung-noocr95.musicxml`, `desktop-compile-diag50.log`,
  `count_notes.py`, `compare_diag50.py`); ROUND 50 (`build96.log`,
  `spike96.log`, `run-widmung96.log`, `wasm-widmung-noocr96.musicxml`,
  `desktop-widmung-noocr96.log`, `desktop-widmung-noocr96.musicxml`,
  `desktop-compile-diag50b.log`); DIAG50b (`build97.log`, `spike97.log`,
  `run-widmung97.log`, `wasm-widmung-noocr97.musicxml`,
  `desktop-widmung-noocr97.log`, `desktop-widmung-noocr97.musicxml`,
  `desktop-compile-diag50c.log`); DIAG50c (`build98.log`, `spike98.log`,
  `run-widmung98.log`, `wasm-widmung-noocr98.musicxml`,
  `desktop-widmung-noocr98.log`, `desktop-widmung-noocr98.musicxml`,
  `desktop-compile-diag50d.log`); clean re-verification (`build99.log`,
  `spike99.log`, `run-widmung99.log`, `wasm-widmung-noocr99.musicxml`,
  `desktop-widmung-noocr99.log`, `desktop-widmung-noocr99.musicxml`,
  `desktop-compile-restore.log`, `desktop-compile-restore2.log`).
- Builds: `full-out95/` (DIAG50 entry), `full-out96/` (ROUND 50),
  `full-out97/` (DIAG50b; 0 problems, 3,056 classes, 28,732 methods),
  `full-out98/` (DIAG50c; 0 problems, 3,056 classes, 28,732 methods),
  `full-out99/` (default build, DIAG50 stripped; 0 problems, 3,055
  classes, 28,726 methods — equals full-out94).
- Fix location: none (no fix). Diagnostic locations:
  `teavm/patched/make_patches.py` ROUND 50 (`HeaderTimeBuilder.java` +
  `TimeColumn.java` via `copy_src`; DIAG50b/c via `read_out`),
  `teavm/entry/src/teavm/TeavmMain.java` and
  `teavm-fork/phase23/src/teavm/DesktopOcrExport.java` (DIAG50 entry
  prints, hand-added/hand-removed), `teavm/patched/strip_diag.py`
  (`TEAVM_KEEP_DIAG`).

### §44.3 Brahms Wiegenlied — Wasm numbers the pickup measure 1 instead of 0; root is the missing flat key signature, same family as Widmung — verdict (c), inconclusive with named next diagnostic (2026-11-10)

#### §44.3.0 Verdict

**(c) Inconclusive — but the causal chain is measured end to end, and the
extra note is the same root cause through a second path.** The pickup
decision itself is localised exactly: `MeasureFixer.isPickup` needs a
negative stack termination, which needs an expected duration, which needs
a time signature — and on Wasm there is no time signature at all, because
the header time ROI opens 81 px too early, inside the key-signature
flats, because the key signature (−3 flats) is never found. The writer
is exonerated: it renders the stack's id / implicit flag, and the
harness desktop (same writer, same patched classes) numbers the pickup
0. The extra G4 is a phantom `NOTEHEAD_VOID` head at (520,337) — the
dead centre of the time-signature "4" digit, which on desktop is claimed
as a `TIME_FOUR` inter and on Wasm is left unclaimed and template-matched
as a head, with the unclaimed A-flat flat linking as its accidental. No
contained fix exists at this level: a MeasureFixer pickup heuristic
without a time signature would be new semantics, a writer renumber would
contradict the model, and suppressing the phantom head needs the time
inter to claim the glyph — all three lead back to the missing key. The
remaining unknown is the mechanism *inside* `KeyBuilder` that makes flat
keys vanish under Wasm — that is DIAG51, already named in §44.2.6 for
Widmung, and this round shows it is the same diagnostic for Wiegenlied
(and six further flat-key pages, §44.3.6). No fix was applied, no TeaVM
defect was localised to a single small operation, no repro was built,
nothing was filed. `full-out94` remains the current clean build; the
tree was restored and re-verified byte-identical (§44.3.9).

**DIAG-number collision, recorded.** §44.1 named a future "DIAG50"
(header-key measure assignment); §44.2 then used DIAG50 for its own
time-signature census and named DIAG51 next (KeyBuilder). This round
uses **DIAG52** — fresh; DIAG51 stays reserved for the Widmung KeyBuilder
follow-up named in §44.2.6. Do not reuse DIAG50 or DIAG51 for a new
diagnostic. This round also *reused* DIAG26 (MeasureFixer decision
inputs) and DIAG50 (time grades + header time ROI) via
`TEAVM_KEEP_DIAG=26,50,52` rather than re-printing them — the strip
keeps any `"DIAG<n>` print whose number is listed.

#### §44.3.1 Symptom (re-established on the harness desktop)

Brahms Wiegenlied (`lieder-brahms-wiegenlied`, GT 155 notes), no-OCR
both sides, `prep92` input. The harness desktop (same `MxlWriter`,
same patched classes as Wasm, JVM) reproduces the stock batch desktop
exactly where it matters — so the comparator is like-for-like, and the
divergence is in the pipeline data, not the writer:

| | Desktop harness (full-out94) | Wasm (full-out92) |
|---|---|---|
| Notes / pitched | 165 / 155 | 166 / 156 |
| Measures / part | 0–11, m0 `implicit="yes"` | 1–12, no implicit |
| `<key>` elements | 2 × `<fifths>-3</fifths>` | **0** |
| `<time>` elements | 3/4 in m0 | **0** |
| `<divisions>` | 6 | 6 |
| P1 m0/m1 | m0: one B4 eighth rest | m1: G♭4 half + B4 eighth rest |
| Wasm `.musicxml` md5 | — | `dffd4b23…` |
| Desktop `.musicxml` md5 | `7da31f88…` | — |

Content alignment (shifted by one bar): every Wasm bar N+1 equals
desktop bar N, except the extra G♭4 in Wasm P1 m1. The desktop batch
`.mxl` (74,284 B unzipped) agrees with the harness desktop on
numbering, key, time, and the pickup contents. The Wasm log carries
`MeasureFixer: No target duration for measures local IDs [1..12]` on
both systems; the desktop log has no such warning (its `TimeColumn`
grades `{3/4=0.9365}`, chosen 3/4).

**The writer is exonerated.** `MxlWriter.processMeasure` numbers the
measure `stack.getScoreId(current.pageMeasureIdOffset)` and emits
`implicit="yes"` iff `stack.isImplicit()` — and `isImplicit()` is true
iff `MeasureFixer` set the stack `PICKUP`. The numbering divergence is
entirely in the stack state `MeasureFixer` assigns, not in the writer.
A writer-side renumber would contradict the model and stock output,
not fix it.

#### §44.3.2 DIAG52 design and build (ROUND 52, full-out100)

Two print sites, all print-only, same patched files both sides:

- **MeasureFixer.java** (ROUND 52 in `make_patches.py`, `read_out` —
  ROUND 22/DIAG26 patched it first, per §39.1): per stack, the
  pickup-decision inputs (`DIAG52 stack`: system index-in-page,
  first-stack flag, expected / actual duration, termination) and the
  result after the branch chain (`DIAG52 decision`: assigned id,
  implicit flag). DIAG26's own prints (left/right, multi-rest count,
  actual duration, isEmpty, assigned id) were kept alive with the same
  build flag instead of being re-printed.
- **MxlWriter.java** (entry code, hand-added/hand-removed, DIAG49
  pattern): per measure, key/time presence at export (`DIAG52
  measure`: scoreId, implicit, hasKeys, time inter); per note, head
  position at export (`DIAG52 note`: part, measure scoreId, staff
  index-in-part, step/octave, head centre, chord duration, shape) —
  pure getters already used by the render path (`note.getCenter()`,
  `chord.getDuration()`, `stepOf(note.getStep())`).
- **DIAG50 reused** (`TEAVM_KEEP_DIAG=26,50,52`): `TimeColumn`
  grades/choice + `HeaderTimeBuilder` timeFind / timeSpaces /
  timeEvalCall / timeTrials — no new prints in those files.

Build **full-out100** (0 problems, 3,055 classes, 28,726 methods —
exactly full-out94; diagnostic prints change no counts). Strip in
that build removed 157 prints (the kept DIAG26/50/52 prints account
for the difference from the clean 161). Side-effect-free, verified
both sides: Wasm Wiegenlied byte-identical to the validation output
(md5 `dffd4b23…`); desktop Wiegenlied byte-identical to the full-out94
harness baseline (md5 `7da31f88…`). Desktop DIAG files were compiled
alone into `phase23/classes` (MeasureFixer, TimeColumn,
HeaderTimeBuilder from `patched/src`; MxlWriter from `entry/src`).

#### §44.3.3 The pickup decision — measured in MeasureFixer

`MeasureFixer.isPickup(stack)` is first system + first stack +
`stackTermination < 0`, where the termination is the voices'
actual-minus-expected duration (null if the voices disagree or the
expected duration is missing — `getStackTermination` returns null
unless all non-null voice terminations agree). DIAG52 + DIAG26, stack
1 (the first stack, left 332 right 627, identical geometry both
sides):

| | Desktop | Wasm |
|---|---|---|
| expected duration | 3/4 | **null** |
| actual duration | 1/8 | **5/8** |
| stackTermination | −5/8 | **null** |
| branch / assigned id | pickup / **id 0, implicit=true** | normal / **id 1, implicit=false** |

All other 11 stacks are identical on both sides (expected 3/4,
actual 3/4, term 0, ids 1–11 on desktop / 2–12 on Wasm — the +1 shift
propagating from stack 1). One stack-5 curiosity is the same both
sides (term null on desktop and Wasm — a pre-existing one-stack voice
inconsistency, not part of this divergence).

So the numbering break is exactly one missing input: **expected=null
on Wasm, because there is no time signature**. With term null,
`isPickup` is false however short the stack is, the branch falls
through to "normal", and the first stack takes id 1. The `actual`
difference (5/8 vs 1/8) is the phantom half note (§44.3.5) — and it
is *not* what breaks the pickup: had the time signature existed,
5/8 − 3/4 = −1/8 < 0 would still be a pickup. The numbering and the
extra note are two independent consequences of the same missing key.

#### §44.3.4 Why there is no time signature — the Widmung shape, on this page

DIAG50, system 1, staff 1:

| | Desktop | Wasm |
|---|---|---|
| browseStart / roi x | 483 | **402** (81 px early) |
| spaces | `[Space(484-505), Space(539-566)]` | `[Space(402-424), Space(428-429), Space(441-445), Space(449-455), Space(463-466), Space(471-473), Space(475-476), Space(484-485)]` |
| range width | 35 | **61** |
| WHOLE glyph / top eval | `[505,276,34x82]` TIME_THREE_FOUR (0.99151) | `[446,276,39x66]` FLAG_1 (0.80176); `[425,276,39x55]` FLAG_1_DOWN (0.52378) |
| NUM / DEN | TIME_THREE (0.99940) / TIME_FOUR (0.87930), 1 trial each | NUM evals 0, DEN trials 0 |
| grades / choice | `{3/4=0.9365}`, chosen 3/4 | **no `timeGrades` / `timeChoice` lines at all** |

The desktop header stops at 483 — exactly the right edge of the key
signature (desktop SIG: the three flats span x 425–484, key bounds
`[425,244,59x98]`). On Wasm the header stops at 402, right after the
clef and *before* the key, so the time ROI opens inside the flats; its
spaces are fragments between flat symbols, the evaluated glyphs are
flat shapes read as flags, and no header time inter is ever built.
System 2 shows the same 82 px shortfall (browseStart 130 vs 212).
Unlike Widmung, there is no SYMBOLS-step fallback time here either —
zero `timeGrades` lines on Wasm — so `MeasureFixer` sees no expected
duration on any stack. The causal chain is complete: **key not found
→ headerStop 402 instead of 483 → time ROI inside the flats → no
header time → no time signature → expected=null → termination null →
not a pickup → measure 1.**

#### §44.3.5 The extra G♭4 — same root, second path

DIAG52 note dump, first measure:

| | Desktop (meas 0) | Wasm (meas 1) |
|---|---|---|
| P1 notes | B4 eighth rest, centre (581,319) | **G4 half, centre (520,337), `NOTEHEAD_VOID`, dur 1/2** + B4 eighth rest (581,319) |
| P2 notes | G4 (582,627), B♭4 (582,606), D3 rest (581,822) | identical centres |

The phantom head's centre (520,337) is the dead centre of the desktop
time-signature "4" digit (desktop SIG: DEN `TIME_FOUR` bounds
`[505,319,34x39]`, glyph 158; staff-1 line spacing puts G4, the 2nd
line, at y=337). Desktop SIG evidence (stock batch `.omr`,
`sheet#1/sheet#1.xml`): **267 heads, none with centre within 40 px of
(520,337)**; the only `NOTEHEAD_VOID` on the whole page is at
(2035,1030), system 2. On desktop the "4" is claimed as a time inter
(frozen, grade 0.703/0.879); on Wasm it is never claimed, and template
matching reads a void head in the digit's counter. Its duration (1/2)
is exactly the stack-1 actual-duration excess (5/8 vs 1/8, §44.3.3).
Its flat accidental is consistent with the unclaimed A-flat flat
(desktop SIG bounds `[467,287,18x55]`: right edge 485, 21 px left of
the head's left edge, vertical span 287–342 containing the head centre
y=337) linking as the head's accidental — geometric inference, not a
printed link. **Verdict on the extra note: same cause (missing key),
different downstream path** — it is not a separate head-detection
divergence, and it does not cause the numbering shift.

#### §44.3.6 The pattern is bigger than this page — flat keys never survive under Wasm

All 19 Part 1 pages with a desktop `.mxl` + Wasm `.musicxml` pair in
`wasm92/` (fifths values are the distinct `<fifths>` sets):

| Desktop key | Pages | Wasm key |
|---|---|---|
| flat (−1/−2/−3/−4) | BWV 397 (−1), Fauré Agnus (−1), Fauré Sanctus (−2,−3), Wiegenlied (−3), Après un rêve (−3), Erlkönig (−2), Widmung (−4), Wolf (−3) — **8 pages** | **lost on all 8** |
| sharp (+1/+2/+3) | BWV 248-33 (+1), BWV 269 (+1), BWV 303 (+2), divisi-ii (+1), divisi-vi (+1), Monat Mai (+3), Mendelssohn (+1,+3) — **7 pages** | kept on all 7 |
| none | BWV 248-05, BWV 371 — 2 pages | agrees on both |

**8/8 flat-key pages lose the key under Wasm; 7/7 sharp-key pages
keep it.** The KeyBuilder divergence is flat-specific, not a general
key failure — and the four pages that emit measure 0 on both sides
(BWV 248-05, 269, 303, Monat Mai) are all non-flat, which is why the
pickup numbering only breaks on flat-key pages. (The `<beats>` column
is not cited here: the scorer regex required adjacent `<beats>` /
`<beat-type>` tags and both writers put them on separate lines.)

Narrowing for DIAG51, from data already in hand (not new KeyBuilder
work): the Wasm header projection *does* see the flat ink — the
DIAG50 timeSpaces are the white gaps *between* the flat glyphs — so
the binary image in the header area is intact on Wasm. The divergence
is in `KeyBuilder`'s own projection peaks or its peak-pattern logic
(dx means, `cutOver`, grade thresholds), not in the pixels it reads.

#### §44.3.7 Ruled out, and why there is no contained fix

Ruled out in this round: the writer (renders stack state faithfully,
§44.3.1); a measure-geometry difference (stack left/right identical,
§44.3.3); a tie/order flip in time selection (no grades exist on
Wasm at all, §44.3.4); head loss or a separate head-detection
divergence for the extra note (it is the unclaimed "4" digit,
§44.3.5); a general key failure (sharp keys survive, §44.3.6).

No contained fix:

- **MeasureFixer pickup heuristic without a time signature** (e.g.
  "first stack shorter than the following stacks is a pickup"): new
  Audiveris semantics, not a contained fix — it would mis-number any
  page whose first measure is genuinely short for another reason, and
  it papers over the missing time signature rather than restoring it.
- **Writer-side renumbering** (emit 0 for the first measure when the
  stack is not flagged pickup): contradicts the model stock uses, and
  would diverge from the harness desktop on every non-pickup page.
- **Suppressing the phantom head**: the head is a genuine template
  match on unclaimed glyph pixels; the principled suppression is the
  time inter claiming the glyph — which is the missing key/time again.
- **KeyBuilder fix**: the mechanism inside `KeyBuilder` is unmeasured
  — that is DIAG51, not this round.

#### §44.3.8 Next diagnostic — DIAG51 (named, not started; shared with Widmung)

`KeyBuilder` hilos / peaks / grades on both sides, per §44.2.6: print
the projection peak list (`hilos`), the `peak dxs` / `cutOver`
computation, and the key-grade decision per staff. That distinguishes
the two remaining hypotheses: (i) the `KeyBuilder` projection in the
header area differs on Wasm (staff-line removal / source pixels), so
the flat peaks are absent or shifted; (ii) the peaks are the same but
the peak-pattern logic diverges under TeaVM. The §44.3.6 narrowing
(the header projection already sees the flat ink) leans toward (ii)
but does not prove it. One DIAG51 round answers Widmung *and*
Wiegenlied *and* the six other flat-key pages, since the mechanism is
now shown to be shared and flat-specific. Stop rule from the task
applies: if DIAG51 localises to a single small TeaVM operation, build
a minimal repro (do not file); if it localises to a contained
desktop-neutral fix, apply it with the §44.2 verification (Widmung
recovered to ~291 pitched + Wiegenlied pickup numbered 0 with bars
aligned vs desktop/GT + the three control pages byte-identical);
otherwise report (c) again with the next step named.

#### §44.3.9 Close-out: tree restored, full-out94 still the current clean build

No fix ships from this round (verdict (c)), so no new clean build was
cut. Close-out verified:

- Entry source restored by hand from the pre-DIAG52 backup
  (`phase53/MxlWriter.java.pre-diag52`); 0 DIAG52 lines remain in
  `entry/src/teavm/MxlWriter.java`.
- Default build (no `TEAVM_KEEP_DIAG`) → `full-out101`: **0 problems,
  3,055 classes, 28,726 methods — exactly full-out94**. Strip removed
  173 prints (161 + 10 DIAG50 + 2 DIAG52). The four DIAG files were
  recompiled into `phase23/classes` from the stripped sources; the
  restored `MeasureFixer.class` carries 0 DIAG52 strings.
- Wasm Wiegenlied on full-out101 byte-identical to the validation
  output (md5 `dffd4b23…`, 0 DIAG lines); Wasm hymn control
  byte-identical to full-out94 (44,105 B, md5 `75637092…`, 0 DIAG
  lines); desktop Wiegenlied on the restored harness byte-identical
  to the full-out94 harness file (md5 `7da31f88…`, 0 DIAG lines).
  `full-out101` is kept as the re-verification artefact;
  **full-out94 remains the named current clean build**.
- `make_patches.py` ROUND 52 stays in the file (stripped by the
  default build, like ROUNDs 44–48 and 50); `TEAVM_KEEP_DIAG`
  unchanged (comma-separated keep list, §44.2.7).
- One incident during the diagnostic compile (own error, caught):
  the first desktop `javac` used `$J/javac` where `J` was the `java`
  binary path, so the shell tried to execute `.../bin/java/javac`
  (exit 126, nothing compiled). Fixed by using the `javac` binary
  path directly; no state was touched.
- The desktop harness runs in this round needed
  `-Dtestocr.file=phase23/empty-ocr.txt` — without it `TestOcr`
  fails at TEXTS (NPE on the null property) and the run dies before
  export. The desktop logs also carry the pre-existing
  `StemBuilder.toString` DEBUG NPE noise (§43.3(4)); non-fatal,
  unrelated.
- `open-music/` was read-only; `choral-test-set.zip` not repacked;
  `jdlehman/score-reader` untouched (only `git diff` read for the
  repo source, and the stock `.omr` SIG read); nothing pushed, filed,
  or merged. No lyric recall re-scored (no-OCR runs both sides, per
  task). BWV p14, Widmung DIAG51, and items 5–8 from the report were
  not touched.

#### §44.3.10 Artefacts

- `teavm-fork/phase53/` — backups (`MxlWriter.java.pre-diag52`,
  `make_patches.py.pre-diag52`); inputs (`wiegenlied.png`
  regenerated from the `.grey` via PIL mode `L`); baselines
  (`desktop-wiegenlied-noocr94.log` + `.musicxml`,
  md5 `7da31f88…`); DIAG52 (`build100.log`, `spike100.log`,
  `run-wiegenlied100.log`, `wasm-wiegenlied-noocr100.musicxml`,
  `desktop-wiegenlied-noocr100.log`,
  `desktop-wiegenlied-noocr100.musicxml`,
  `desktop-compile-diag52.log`); clean re-verification (`build101.log`,
  `spike101.log`, `run-wiegenlied101.log`,
  `wasm-wiegenlied-noocr101.musicxml`, `run-hymn-101.log`,
  `wasm-hymn-noocr101.musicxml`,
  `desktop-wiegenlied-noocr101.log`,
  `desktop-wiegenlied-noocr101.musicxml`,
  `desktop-compile-restore.log`).
- Builds: `full-out100/` (diagnostic, DIAG26/50/52 kept; 0 problems,
  3,055 classes, 28,726 methods), `full-out101/` (default build,
  DIAG52 stripped; 0 problems, 3,055 classes, 28,726 methods —
  equals full-out94).
- Fix location: none (no fix). Diagnostic locations:
  `teavm/patched/make_patches.py` ROUND 52 (`MeasureFixer.java` via
  `read_out`; DIAG26/DIAG50 kept via `TEAVM_KEEP_DIAG=26,50,52`),
  `teavm/entry/src/teavm/MxlWriter.java` (DIAG52 measure/note prints,
  hand-added/hand-removed).

### §44.4 BWV 227 p14 new +2 — a §40 × §42 interaction: the rint fix creates the extra head candidates, the §42 supports let them survive; p13's +1 flip is the same cause — verdict (c), inconclusive with named next diagnostic (2026-11-10)

#### §44.4.0 Verdict

**(c) Inconclusive — but the attribution is complete and the mechanism is
localised to two stages.** The p14 +2 and the p13 +1 flip are the same
cause: **neither the §40 rint fix nor the §42 policy entries alone moves
either page — both together do.** The 2×2 toggle (below) proves it on
both pages, with byte-identical outputs. The rint fix changes the
HEADS-stage head-candidate set (template matching lands on the other
side of a .5 boundary for these heads); the §42 HeadHeadRelation
supports then let the extra candidates survive REDUCTION/CHORDS and
land in chords. Desktop has both correct rint *and* working supports
yet produces 365/321 — so the remaining difference must be upstream of
rint: some value Wasm feeds into a rounding call differs by an epsilon
from the JVM's, and the corrected rounding then flips the other way.
That upstream float divergence is **not localised** — no single small
TeaVM operation is named, no minimal repro exists, and neither
candidate "fix" is containable (reverting rint re-breaks §40
Divergence A; reverting the policy restores the §42 149 ERRORs). No
fix was applied, nothing was filed. `full-out94` remains the current
clean build; the tree was restored and re-verified byte-identical
(§44.4.7). The +2 are **not** two correct notes desktop misses
(§44.4.2).

#### §44.4.1 The extra notes, identified (no new run needed)

Per-part/per-measure multiset diff of the produced `.musicxml` files
(`phase54/compare_p13p14.py`, `dump_measure.py`) — desktop vs out92
and out82 vs out92 agree exactly; the *only* count differences on
either page are these:

**BWV p14, P1 measure 4** (desktop/out82: D5 q, C♯5 q, D5 q, rest q —
voice sums to 4/4; out92: D5 q, **C5 half + E5 half (chord tone)**,
C5 q, D5 q, rest q — voice sums to **6.0 vs 4**, validity 35/45 →
34/45). Net +2 pitched: the half-note chord is the whole +2, plus a
pitch change on the following quarter (C♯5 → C5, same caesura
`default-x=273`, same slur-stop geometry). The other apparent diffs
(P2 m5–6, P4 m1–2) are tie start/stop markings only, present in
out82 already — not part of this divergence.

**BWV p13, P2 measure 4**: out92 adds one **G5 quarter chord tone**
attached to the final A4 onset (desktop already carries two G5 chord
tones at the earlier G4 onset; out92 carries those two *plus* this
third). P1 m5 is a pitch swap, not a count change (out82's surplus
G5 chord tone becomes out92's surplus D5 chord tone at the F♯4
onset; desktop has neither). Net +1 pitched vs desktop (+2 vs out82,
which was missing two of desktop's G5 chord tones there).

#### §44.4.2 The +2 are a regression, not correct notes desktop misses

- **Rhythmically impossible as written.** The p14 half chord makes
  voice 1 sum to 6.0 beats in a 4/4 measure (scorer bad-measure list:
  `P1 m4 v1: 6.0 vs 4`, new under out92; desktop has no such entry)
  and drops page validity 35/45 → 34/45. A correct reading cannot
  overflow its voice.
- **GT has no half note in bar 4 on any part.** Pooled GT bar 4
  (all six parts): quarters/eighths only. The C5+E5 *half* chord
  cannot be GT-correct at that duration; the E5 does add +1 exact
  hit (GT bar 4 has E5 ×2, desktop recovers 0, out92 recovers 1),
  but at the wrong duration inside an overflowing voice — a real
  head given a wrong duration/grouping, not a correct note. The
  extra C5 scores nothing (GT bar-4 C5 ×0). Pitch-class is flat
  (205 both sides).
- **p13's extra G5 scores nothing.** Exact-pitch 189 and
  pitch-class 230 are identical on desktop and out92 (per-bar: bar 4
  28 = 28, bar 5 29 = 29); GT bar 4 has no G5 at all, and desktop
  already carries two surplus G5 chord tones at that onset.
  The (a)-second-branch verdict (correct notes, no fix needed) is
  therefore excluded on both pages.

#### §44.4.3 Step census — the divergence is already present at HEADS

Out82 vs out92 logs, same prepared pages, same catalog
(`requested 68 maps to catalog 64` p14, `65 → 64` p13, both sides;
SCALE identical: `interline(14,15,15)`):

| Page | out82 HEADS cands (CHECK) | out92 HEADS cands (CHECK) | out82 SYMBOLS heads (SIG, CHECK) | out92 SYMBOLS heads (SIG, CHECK) |
|---|---|---|---|---|
| p14 | 967 (2784176) | **983 (2852036)** | 365 (2085, 1067560) | **367 (2089, 1071250)** |
| p13 | 1551 (4709451) | **1532 (4636655)** | 321 (1759, 960445) | **323 (1760, 964484)** |

Two things follow. First, the candidate set changes at HEADS —
*before* any `insertSupport` call (REDUCTION/CHORDS) — so a
HEADS-stage change is implicated; of the §40/§42 set only the rint
fix can act there (§37 is export-only, §43 strip is prints-only).
Second, the candidate *count* moves in opposite directions
(+16 p14, −19 p13) while survivors move the same way (+2 both) —
the candidate set changes composition, not just size, so the
HEADS delta alone does not prove the surviving +2 are
rint-created; the toggles (§44.4.4) are what settle it. `Could not
instantiate` lines: out82 169 (p14) / 694 (p13), out92 0 / 0 —
the §42 symptom is gone under out92 on both pages, as expected.

#### §44.4.4 The 2×2 toggle — rint × policy interaction, both pages

Two toggle builds from the current (full-out94) tree, no Audiveris
source change in either:

- **Toggle 1 — rint reverted, policy kept (full-out102).** Spike
  with `phase54/teavm-main-jars-rintrevert.txt` (copy of
  `teavm-main-jars-corepatch2.txt` with only the classlib line
  swapped to `lib-fork/teavm-classlib-0.16.0-pre-rint.jar`). The
  jar was verified genuine by `javap`: its `TMath.rint` is the old
  `return round(a)` (`invokestatic round:(D)J; l2d`), while the
  current jar has the §40 fixed form (`Double.isNaN/isInfinite`
  guards, floor/tie logic). Build: 3,055 classes, 28,727 methods
  (+1 vs out94 — `round(double)` called from `rint` again).
- **Toggle 2 — rint kept, policy reverted (full-out103).** The two
  §42 `selectClass` entries in
  `teavm/policy/src/teavm/TeavmReflectionPolicy.java` commented out
  (backup `phase54/TeavmReflectionPolicy.java.pre-toggle2`),
  `build.sh` re-run (BUILD OK), Spike with the normal jars file.
  Build: 3,053 classes (−2), 28,722 methods (−4) — exactly the
  inverse of §42.6's +2/+4, so the revert took effect at compile
  level.

Pitched-note results (desktop / out82 in parentheses):

| Build | rint | policy | p14 pitched | p13 pitched |
|---|---|---|---|---|
| full-out94 (= out92) | fixed | on | **367** (365 / 365) | **322** (321 / 320) |
| full-out102 (toggle 1) | **reverted** | on | 365 | 320 |
| full-out103 (toggle 2) | fixed | **off** | 365 | 321 |
| full-out82 | reverted | off | 365 | 320 |
| Desktop | — | — | 365 | 321 |

Both toggles reproduce an out82-equivalent output *byte-identically*:
out102 p14 md5 `fbd3b9ec…` = out82 p14 file, out102 p13 md5
`088dcb03…` = out82 p13 file; step censuses identical too (out102
p14 HEADS 967 / SYMBOLS 365/2085/1067560; p13 HEADS 1551 /
SYMBOLS 321/1759/960445 — the out82 values exactly). Toggle 2 does
*not* reproduce out82 byte-wise (p14 CHECK 1067519 vs out82
1067560; p13 SYMBOLS 322 vs 321, PAGE 321) — the rint fix still
changes the head set — but the *counts* land exactly on desktop
(365, 321) on both pages.

**Reading:** on p14 the +2 needs **both** changes; either alone
leaves 365. On p13 the rint fix alone *repairs* the page to desktop
parity (320 → 321), and adding the policy overshoots it (→ 322).
So p13's +1 flip is the same cause as p14's +2 — the interaction —
with the single-toggle behaviour differing per page. §42 is **not**
exonerated by toggle 1 alone (it is necessary for the +2); it is
exonerated as a *sole* cause by toggle 2 (rint alone does not
produce the +2 on p14, and on p13 rint alone is a fix). Likewise
§40 is not the sole cause either: with the policy off, the fixed
rint gives desktop counts on both pages.

**Mechanism (localised to two stages, not to one operation).**
(1) The rint fix moves template matching across .5 boundaries for
these heads: the HEADS candidate set changes on both pages
(§44.4.3). Desktop has the *same* correct rint semantics yet
produces different candidates — so the values Wasm feeds into the
rounding calls must differ by an epsilon from the JVM's: an
upstream float divergence, not a rint defect (rint itself is
30/30 vs the JDK, §40.4). (2) The §42 supports then decide the
extra candidates' fate: same-duration heads support each other
(`SigReducer.java:326`, mutual support within a duration set, vs
exclusion across durations) and mirror-migrate
(`ChordsBuilder.java:484` — a supporting head moves to the right
mirror head in divisi). With supports working, the flipped heads
survive REDUCTION/CHORDS and are grouped into chords (the C5+E5
half chord, the third G5 chord tone); with supports missing they
are pruned or never grouped, so the counts stay at desktop. Under
out82 the old (wrong) rint accidentally compensated: the flipped
candidates never arose, so the missing supports did not matter on
these pages.

#### §44.4.5 Ruled out, and why there is no contained fix

Ruled out: the §42 policy entries as sole cause (toggle 2: rint
alone, policy off, gives desktop counts — but the +2 needs the
policy too, so it is a co-cause, not exonerated outright; see the
2×2 table, not a single toggle); the rint fix as sole cause
(toggle 1 alone does not produce the +2 without the policy, and
toggle 2 shows fixed rint without policy is desktop-exact);
a template-catalog difference (identical `requested → catalog`
lines both sides); a SCALE difference (identical interline/slope);
a writer/export difference (§37 acts after PAGE; the divergence
is already in SYMBOLS heads); the "two correct notes" reading
(§44.4.2); a head-detection loss (this is a head *gain* that
survives reduction).

No contained fix:

- **Revert rint** — re-breaks §40 Divergence A (the P2 m9 tie
  slur gate, Hallelujah deep diff 89 → 93, Lindenbaum 10 → 2).
  It would trade two pages' +2/+1 for the control pages'
  regressions. Not desktop-neutral.
- **Revert the policy** — restores the §42 symptom (149 `Could
  not instantiate` ERRORs on Hallelujah p01, 162/684 on these
  pages) and the §42 fix is a correct reflection-policy
  completion, not a workaround. Not a fix.
- **A targeted threshold tweak** in `SigReducer`/chord grouping
  to prune these two heads would be Audiveris-semantics surgery
  tuned to two pages, with no principled boundary to aim at —
  the heads are supported same-duration heads, exactly the case
  the supports exist for. Not contained, not desktop-neutral by
  construction.
- **The remaining fix lives upstream of rint** — finding which
  computed value differs by an epsilon between JVM and Wasm.
  That is the next diagnostic, not this round.

#### §44.4.6 Next diagnostic — DIAG53 (named, not started; fresh number)

DIAG51 stays reserved for the Widmung/Wiegenlied KeyBuilder
follow-up; DIAG52 was used by §44.3; **DIAG53 is fresh** (no
DIAG53 print exists anywhere in the tree — checked before naming).
Two halves, one round:

1. **Name the flipped heads.** Head dump at end of HEADS (and
   again at SYMBOLS) on both sides — per-head centre, shape,
   grade — diffed by centre, never by id (§39.3). Entry-side
   prints in `TeavmMain.java` / `DesktopOcrExport.java`
   (DIAG50 pattern), same patched files both sides. This says
   exactly which heads the rint fix creates/destroys on p13/p14
   and whether they are the C5/E5/G5 heads.
2. **Print the rounding inputs for those heads.** Grep the
   `Math.rint` / `Math.round` call sites on the head-grading path
   (template matching / seed tally / `HeadInter` grading — enumerate
   when the round starts) and print each call's input value around
   the flipped heads on both sides. That distinguishes the two
   remaining hypotheses: (i) a rint input is exactly .5 on one side
   and epsilon-off on the other (upstream float divergence — then
   DIAG54 hunts the upstream operation that computes that value);
   (ii) identical rint inputs with different rint results (a
   remaining TeaVM rounding defect — then build the minimal repro,
   do not file).

Open question not answered by this round (not started): which
change fixed BWV p17 (−14 → identical) and p23 (−2 → identical)?
The 2×2 predicts they are one of the two changes or the same
interaction — re-running p17/p23 under full-out102 and
full-out103 would say which, in one round. Do not conflate with
the p13/p14 result: on p13/p14 the interaction is proven; on
p17/p23 it is only a hypothesis.

#### §44.4.7 Close-out: tree restored, full-out94 still the current clean build

No fix ships from this round (verdict (c)), so no new clean build
was cut. Close-out verified:

- Policy source restored by hand from the pre-toggle backup
  (`phase54/TeavmReflectionPolicy.java.pre-toggle2`); `diff`
  against the backup is empty. No `make_patches.py` ROUND was
  added (no DIAG prints, no Audiveris source change in this
  round); `make_patches.py`, the classlib jars, and the entry
  sources are untouched (mtimes pre-date this round).
- Default build after restore → `full-out104`: **0-problem build,
  3,055 classes, 28,726 methods — exactly full-out94**.
- Wasm BWV p14 on full-out104 byte-identical to the validation
  output (md5 `c446203a…`, SYMBOLS 367/2089/1071250 — the +2
  back, as expected with the tree restored); Wasm hymn control
  byte-identical to full-out94 (44,105 B, md5 `75637092…`).
  0 DIAG lines in both logs. `full-out104` is kept as the
  re-verification artefact; **full-out94 remains the named current
  clean build**. `full-out102` (rint-revert toggle) and
  `full-out103` (policy-revert toggle) are kept as the diagnostic
  artefacts — neither is a candidate clean build.
- Incidents during the runs (own errors, caught, no state
  affected): two `exec` calls reported exit 1 from a trailing
  `grep -c` with zero matches (0 `Could not instantiate` / 0 DIAG
  lines) — the page runs themselves exited 0 with `TEAVM DONE`
  in every case.
- `open-music/` was read-only; `choral-test-set.zip` not
  repacked; `jdlehman/score-reader` untouched (only `git diff`
  read for the repo source, and the stock `.omr` SIG read);
  nothing pushed, filed, or merged. No lyric recall re-scored
  (no-OCR runs both sides, per task). Widmung/Wiegenlied DIAG51
  and items 5–8 from the report were not touched.

#### §44.4.8 Artefacts

- `teavm-fork/phase54/` — comparators (`compare_p13p14.py` +
  `.txt`, `dump_measure.py` + `.txt`, `exact_by_bar.py` + `.txt`,
  `score_file.py`); baselines (`run-bwv227-p14-94.log`,
  `run-bwv227-p13-94.log`, `wasm-bwv227-p14-noocr94.musicxml`,
  `wasm-bwv227-p13-noocr94.musicxml` — both md5-identical to the
  out92 validation files); toggle 1 (`teavm-main-jars-rintrevert.txt`,
  `spike102.log`, `run-bwv227-p14-102.log`,
  `run-bwv227-p13-102.log`, `wasm-bwv227-p14-noocr102.musicxml`,
  `wasm-bwv227-p13-noocr102.musicxml` — both md5-identical to the
  out82 files); toggle 2 (`TeavmReflectionPolicy.java.pre-toggle2`,
  `build103.log`, `spike103.log`, `run-bwv227-p14-103.log`,
  `run-bwv227-p13-103.log`, `wasm-bwv227-p14-noocr103.musicxml`,
  `wasm-bwv227-p13-noocr103.musicxml`); clean re-verification
  (`build104.log`, `spike104.log`, `run-bwv227-p14-104.log`,
  `run-hymn-104.log`, `wasm-bwv227-p14-noocr104.musicxml`,
  `wasm-hymn-noocr104.musicxml`).
- Builds: `full-out102/` (toggle 1, rint reverted, policy kept;
  3,055 classes, 28,727 methods), `full-out103/` (toggle 2, rint
  kept, policy reverted; 3,053 classes, 28,722 methods),
  `full-out104/` (default build after restore; 3,055 classes,
  28,726 methods — equals full-out94).
- Fix location: none (no fix). Toggle locations:
  `teavm-main-jars-rintrevert.txt` (classlib swap only, Spike
  classpath) and `teavm/policy/src/teavm/TeavmReflectionPolicy.java`
  (two §42 entries commented out for toggle 2, restored after).

## §45 — DIAG51: flat-key loss FIXED — missing Bravura LINE_CODE metrics in the shim table; contained shim-data fix, all 8 flat-key pages recovered — verdict (a) (2026-11-10)

### §45.0 Verdict

**(a) Contained fix applied and verified.** Root cause: the §19
`BravuraMetrics` table lacked codepoint 0xe010
(`BravuraSymbols.LINE_CODE`), so the shim `TextLayout` fell back to
stub bounds (height = font size) and
`AbstractPitchedInter.populatePitchOffsets` computed lineHeight =
200.0 instead of 6.40625, collapsing pitchHeight 25.0 → 0.80 and
inflating every pitch offset ~31×; flat alters' measured pitches
shifted +15.97, so `checkWithClefs` graded 0 and no key was ever
created. Sharp keys use only `massPitch` (no area offset), which is
why they survived. Fix: dump 0xe010's real desktop metrics and
regenerate the table (157 → 158 codepoints). No Audiveris code
changed; no TeaVM defect; no repro needed; nothing filed. New current
clean build: **full-out110** (0 problems, 3,055 classes, 28,726
methods). DIAG51's own prints then caught a second, self-inflicted
bug (§45.5): the browse print NPE'd on empty hilos — fixed in ROUND
56, print-only.

### §45.1 Root cause, measured (DIAG51c recap + the table gap)

DIAG51c (full-out107) had already localised the flip to
`getAreaPitchOffset(FLAT)`: desktop 1.0559375, Wasm 33.0 (exactly).
Both `pitchPositionOf` values were bit-identical and
`flatMassPitchOffset` = 0.65 on both sides; the divergence was the
offset formula `(−rect.getY() − rect.getHeight()/2) / pitchHeight`
with `pitchHeight = (staffHeight − lineHeight)/8` — desktop
staffHeight 206.40625, **lineHeight 6.40625**, pitchHeight 25.0;
Wasm staffHeight 206.3988, **lineHeight 200.0** (= the font size),
pitchHeight 0.79985. The FLAT rect itself was essentially identical
(y ≈ −87.80, h ≈ 122.80). Exact mix shift: (33.0 − 1.0559375)/2 =
+15.97203125.

`lineHeight` comes from
`font.layout(BravuraSymbols.LINE_CODE).getBounds().getHeight()`
(`LINE_CODE` = 0xe010). The shim `TextLayout.getBounds()` composes
real bounds only when the font is Bravura AND every codepoint is in
`BravuraMetrics`; otherwise it returns the stub
`Rectangle2D(0, −ascent, advance, ascent+descent)` with height =
font size (0.8 + 0.2). 0xe010 was absent from the table; 0xe01a
(`STAFF_CODE`) was present — hence `staffHeight` correct and
`lineHeight` wrong.

Audit of all 169 codes in `BravuraSymbols.java` against the table:
the only live gap is 0xe010. The other 11 missing codes (0xe527,
0xe528, 0xe529, 0xe531, 0xe532, 0xe533, 0xe537, 0xe538, 0xe53b, 0xe53c,
0xe53d) are dynamics shapes whose case lines are commented out in
`BravuraSymbols.java` — never laid out.

### §45.2 Fix

- `teavm-fork/phase55/LineCodeDump.java` — minimal desktop dumper
  (JDK 25 + stock jars, `-Djava.awt.headless=true`), mirroring
  `SymbolMetricsDump`'s per-codepoint loop at sizes 40/84/168.
- Dumped 0xe010 (`linecode-dump.out`): size 84 adv
  42.00006103515625, bounds (0.0, −43.34375, 42.0, 2.6875); unit adv
  0.500000726609003, x 0.0, y −0.5159970238095238, w 0.5, h
  0.031994047619047616; maxLinErr 3.72e-5 (inside the §19 5.02e-4
  envelope).
- Sanity: at size 200 the unit height gives 6.3988 vs desktop's
  directly measured 6.40625 (0.0074 px, size non-linearity inside the
  documented envelope); pitchHeight becomes 25.0000, FLAT offset
  1.0558 vs desktop 1.0559375 (Δ 0.00013, against the ±1.5/2.0
  key-grade gate — negligible).
- Merged into `teavm-fork/phase-font/symbol-metrics.json`
  (`counts.codepoints` 157 → 158; original kept as
  `symbol-metrics.json.bak157`), regenerated via
  `gen_symbol_metrics.py` (its docstring updated 157 → 158).
  `BravuraMetrics.java` now carries 57360 in CPS (sorted, between
  57348 and 57370); `PreRenderedSymbolMetrics.java` byte-identical
  (shapes unchanged).
- No Audiveris source changed. No classlib/core change. The fix is
  data in the shim table, the same mechanism as §19.

### §45.3 Verification (diagnostic build full-out108, TEAVM_KEEP_DIAG=51)

- Build: `build108.log`, Spike 0 problems, 3,055 classes, 28,726
  methods.
- DIAG51 pitchScale on Wasm: staffHeight=206.39880952380955
  lineHeight=6.398809523809518 pitchHeight=25.000000000000004; FLAT
  offset=1.0558035714285712.
- **Widmung:** 2× `<fifths>-4</fifths>` (was 0), 207 alters (was 19,
  desktop 207), 291 pitched (was 169, desktop 291), 299 note
  elements = desktop. `.musicxml` 129,619 B vs desktop 129,611 B;
  deep diff vs harness desktop: source-path (known filename
  artefact) + 1 extra wedge stop + 2 slur bezier coords ±1 px. The
  wedge stop was already present in Wasm at full-out92/94 (7 vs
  desktop 6 in all three builds) — a pre-existing Wasm/desktop
  wobble, unchanged by the fix.
- **Wiegenlied:** 2× `<fifths>-3</fifths>`, time 2, 155 pitched (was
  156 with the phantom G♭4), 165 note elements = desktop,
  `implicit="yes"` ×2 (pickup m0 restored). Deep diff vs desktop:
  source-path + 10 slur bezier hunks ±1–2 px + 1 extra tie (A♭4
  m9→m10). The tie IS in the ground truth (GT `score.xml` ties A♭4
  m9→m10) — Wasm matches GT, the harness desktop misses it.
- **Controls on full-out108 byte-identical to full-out94:** hymn
  `75637092…` (44,105 B), Hallelujah SATB `126771ec…` (105,434 B),
  Lindenbaum `dbd546ba…` (99,305 B). (First Hallelujah run used the
  wrong input — prep92 IMSLP p1, 258,209 B, kept as
  `wasm-hallelujah-noocr108.musicxml` — re-ran with the correct
  phase23 SATB input for the control comparison.)

### §45.4 Spot-check: the other six flat-key pages (full-out108, then 109)

Desktop comparators are the stock batch desktop `.mxl` files from the
full-out92 tree (`open-music/wasm92/<page>/desktop/`); Wasm92
numbers are the broken-build baselines.

| page | key | fifths Wasm / desktop | pitch Wasm / desktop | note |
|---|---|---|---|---|
| BWV 397 (−1) | −1 ×4 | 4 / 4 | 209 / 209 | exact |
| Après un rêve (−3) | −3 ×2 | 2 / 2 | 308 / 308 | exact, time 2 |
| Erlkönig (−2) | −2 ×2 | 2 / 2 | 165 / 159 | +6, identical to wasm92 — pre-existing |
| Wolf Verborgenheit (−3) | −3 ×2 | 2 / 2 | 301 / 298 | +3, identical to wasm92 — pre-existing |
| Fauré Agnus (−1) | −1 ×15 | 15 / 15 | 95 / 96 | −1, identical to wasm92 — pre-existing; crashed on 108, see §45.5 |
| Fauré Sanctus (−2/−3) | exact desktop sequence ×12 | 12 / 12 | 178 / 182 | −4, identical to wasm92 — pre-existing; crashed on 108, see §45.5 |

Sanctus fifths sequence on Wasm109 is exactly the desktop sequence:
[−3,−3,−3,−2,−3,−3,−2,−3,−3,−3,−3,−2]. The key is recovered on all
six; the pitched gaps that remain are all identical to the full-out92
Wasm numbers, i.e. pre-existing Wasm/desktop divergences the key fix
did not move.

### §45.5 Self-inflicted crash: DIAG51 browse print NPE on empty hilos (ROUND 56)

- Both Fauré organ pages (23 staves, 1 system) died on Wasm
  full-out108 with `RuntimeError: dereferencing a null pointer`
  immediately after `DIAG51 hilos staff=1 inHeader=true []`.
- Cause: my own DIAG51 browse print (ROUND 53) calls
  `range.getStart()` unconditionally.
  `StaffHeader.Range.getStart()` auto-unboxes the nullable `Integer
  start`, which is null when no peaks were found (`setStart` only
  runs inside peak processing: `KeyBuilder` lines 1432/1435/1877/
  2440). Stock code never calls `getStart()` on an unpopulated
  range, so this is purely a diagnostic-print bug — not the metrics
  fix, not a TeaVM defect.
- Proof: the desktop harness (same patched files) died identically
  — `NullPointerException: Cannot invoke
  "java.lang.Integer.intValue()" because "this.start" is null` at
  `StaffHeader.java:237` via `KeyBuilder.java:2247`
  (`desktop-agnus-noocr108.log`).
- Fix (ROUND 56 in `make_patches.py`, before the ROUND 49 strip):
  both range prints (browse + refine) now use
  `(range.hasStart() ? range.getStart() : -1)`. Print-only,
  desktop-neutral. `KeyBuilder` was patched by ROUND 53, so
  `read_out`, not `copy_src` (per §39.1).
- Re-verified: Wasm full-out109 Agnus exit 0 (`range=-1-595` for
  staff 1), Sanctus exit 0; desktop harness recompiled with the
  fixed `KeyBuilder` (javac into `phase23/classes`, exit 0,
  `desktop-compile-diag51d.log`) — desktop Agnus exit 0,
  `range=-1-595`, pitch 95, fifths 15.

### §45.6 Clean build full-out110 + final verification

- Build: `./build.sh` (no `TEAVM_KEEP_DIAG`), Spike 0 problems,
  3,055 classes, 28,726 methods. Strip verified: 0 live DIAG51
  prints remain (KeyBuilder 30, AbstractPitchedInter 2, AlterInter
  2 removed).
- Widmung clean = diagnostic: md5 `eec969c9…` (129,619 B).
  Wiegenlied clean = diagnostic: md5 `9a1eb42f…` (72,470 B). The
  prints are print-only — stripping changes nothing.
- Controls byte-identical to full-out94: hymn `75637092…` (44,105
  B), Hallelujah SATB `126771ec…` (105,434 B), Lindenbaum
  `dbd546ba…` (99,305 B).
- **full-out110 is the new current clean build.** The only delta
  from full-out94 is the `BravuraMetrics` data (one codepoint) plus
  the §44.1 writer guard already in full-out94.

### §45.7 Residuals (not regressions, not blocking)

- Erlkönig +6 pitched vs desktop, Wolf +3, Sanctus −4, Agnus −1
  (harness; stock batch desktop is 96 vs harness 95 on Agnus) — all
  identical to the full-out92 Wasm numbers; pre-existing
  Wasm/desktop divergences, unchanged by this fix.
- Widmung +1 wedge stop vs harness desktop (present since
  full-out92) and ±1 px slur bezier wobbles (documented §19 family);
  Wiegenlied +1 tie vs harness desktop where Wasm matches GT.
- Still open (unchanged): DIAG53 (BWV p14 +2), real-browser Chrome
  run, upstream filings (deferred), BrowserOCR follow-up,
  photometric recovery, multi-file export N>1, unexercised writer
  paths, Lindenbaum batch-vs-harness gap, Beethoven typeset p165,
  StackRhythm wobbles, Beethoven p229 wall time.

### §45.8 Artefacts

- `teavm-fork/phase55/` — `LineCodeDump.java` + `classes/`,
  `linecode-dump.out` / `.err`, `build108/109/110.log`,
  `spike108/109/110.log`, `run-widmung108.log`,
  `run-wiegenlied108.log`, `run-hymn108.log`,
  `run-hallelujah108.log` (wrong-input IMSLP p1 run),
  `run-hallelujah-satb108.log`, `run-lindenbaum108.log`,
  `run-widmung-110.log`, `run-wiegenlied-110.log`,
  `run-hymn-110.log`, `run-hallelujah-satb-110.log`,
  `run-lindenbaum-110.log`, `verify110.sh` + `verify110.log`,
  `spotcheck6.sh` + `spotcheck6.log`, `run-spot-*-108/109.log`,
  `spot-*-108/109.musicxml`, `wasm-*-noocr108/110.musicxml`,
  `agnus.png` (PIL mode `L` from the prep92 grey),
  `desktop-agnus-noocr108.log` (crash repro),
  `desktop-agnus-noocr109.log` (fixed),
  `desktop-agnus-noocr109.musicxml`,
  `desktop-compile-diag51d.log`.
- `teavm-fork/phase-font/symbol-metrics.json` (158 codepoints) +
  `symbol-metrics.json.bak157`;
  `teavm/shims/src/java/awt/font/BravuraMetrics.java`
  (regenerated); `gen_symbol_metrics.py` docstring 157 → 158.
- `teavm/patched/make_patches.py` ROUND 56.
- Builds: `full-out108/` (diagnostic, DIAG51 kept), `full-out109/`
  (diagnostic + ROUND 56), `full-out110/` (clean, current).

## §46 — Fix round on the full-out110 validation findings (2026-11-11)

Six items, sequential, shared build tree. Validation context:
`open-music/FULLOUT110_ADDITIONS_RESULTS.md` (22 pages, desktop Audiveris
5.11 vs Wasm full-out110, no-OCR first + hymnal OCR bridge). Current clean
build remains **full-out110** (0 problems, 3,055 classes, 28,726 methods);
**full-out111** is the diagnostic build of this round (DIAG54 kept, ROUND 57).
No contained fix landed in this round, so no clean build beyond full-out111
is warranted. DIAG54 used (item 1); next fresh DIAG is **DIAG55**.

### §46.1 Hymnal Wasm −28 notes / 2 bars — verdict (c) inconclusive, localised; reframed by the item-2 experiment

Desktop 125/126 notes, 12 measures/part; Wasm 97/98, 10 measures/part.
Per-part loss P1 (odd staves) −8, P2 (even staves) −20; per-system S1 −10,
S2 −10, S3 −8.

**DIAG54 (ROUND 57, `teavm/patched/make_patches.py`, before the ROUND 49
strip):** three print-only sites — `HeadsStep.doEpilog` (per-staff HeadInter
counts + bounds checksums at HEADS-END; `copy_src`, pristine),
`SymbolsStep.doEpilog` override (same at SYMBOLS-END; `read_out`, R2 copy
list, unmodified by any ROUND), `MeasuresBuilder` column loop (every barline
column: deskewed x, groupCount, staffCount, per-staff groups; `copy_src`,
pristine). Diagnostic build **full-out111** (0 problems, 3,055 classes,
28,728 methods; `phase56/build111.log`, `phase56/spike111.log`).

**Results (all in `teavm-fork/phase56/`):**
- HEADS-END **identical both sides**: sys1 `{1=80, 2=89}` check
  `{71871, 87195}`; sys2 `{3=89, 4=72}` check `{97483, 85914}`; sys3
  `{5=113, 6=129}` check `{145904, 179959}`; total 572. Tripwire matches:
  `requested 57 maps to desktop catalog 64` both sides.
- Wasm SYMBOLS-END: sys1 `{1=13, 2=11}`, sys2 `{3=16, 4=16}`, sys3
  `{5=22, 6=19}` = 97. Desktop final (`.omr`): 15/21/20/22/24/23 = 125.
  Per-staff gaps: s1 −2, s2 −10, s3 −4, s4 −6, s5 −2, s6 −4. Loss is
  inside STEMS..SYMBOLS; post-SYMBOLS steps create no heads, so desktop
  SYMBOLS-END ≥125.
- Barlines: Wasm COLUMN dump shows S2 x=878.88 groups=1 (s3 only —
  staff-4 barline at ~876 **absent** from SIG, not mis-grouped) and S3
  x=340.49 groups=1 (s6 only — staff-5 barline at ~337 absent). Desktop
  `.omr` has both barlines. All other columns complete (groups=2). The 2
  deletions explain 13→11 raw measures, not the −28.
- Weak pointers (not proof): GRID spurious clusters destroyed 4 (desktop)
  vs 2 (Wasm); ReductionStep stem free-length median 32 px / 2.7 interlines
  (desktop) vs 33 / 2.8 (Wasm).
- Wasm `.mxl` byte-identical full-out110 vs full-out111 (md5
  `56c5941c661ba048b84cb652109fe427`, 38,762 B) — DIAG54 print-only on the
  Wasm side.

**Ruled out:** HEADS template matching; clef recognition (identical "no
recognized header clef" warnings on staves 2/3/5/6 both sides, identical
`.mxl` clefs); missing time signature as the note-loss cause (both sides
warn "No target duration for measures", same assumed 4/4); barline grouping
as the cause of note loss (S1 loses 12 notes with intact barlines).

**Reframe from the item-2 stock-template experiment (same round):** the
desktop harness with STOCK `TemplateFactory` on the hymnal page gives
HEADS-END **584** (sys1 `{87, 82}`, sys2 `{82, 73}`, sys3 `{124, 136}`),
vs 572 pre-rendered, with a different per-staff split — the template
catalog DOES move the hymnal head population. The −28 is now most plausibly
template-driven (request 57 → catalog 64, a 12% oversize template), the
same mechanism proven on p13 (§46.2, ±24 heads). The exact template-vs-
TeaVM split is **unmeasured**: the desktop stock SYMBOLS-END is blocked by
the harness TEXTS crash (see below).

**Blocker — desktop harness TEXTS crash on the hymnal page
(template-independent):** `ArrayIndexOutOfBoundsException: Coordinate out
of bounds!` in `SheetScanner.getCleanImage` → `BufferedImage.getRGB` (via
`TextsCleaner.eraseInters`), after HEADS-END printed, before SYMBOLS/
MEASURES — so no desktop SYMBOLS-END/COLUMN reference exists yet, with
either template variant (`phase56/desktop-hymnal-noocr111.log`,
`phase56/desktop-hymnal-stocktemplate.log`, both exit 1).
`TestOcr.isAvailable()` always returns true, so TEXTS cannot be skipped
via property. Batch skips TEXTS (no crash); Wasm's BrowserOCR path does
not hit it. Hymn control on the same `phase23/classes`: exit 0, `.mxl`
md5 `9b058b42b4b0f22814cc428b6990a110` (known-good §41 value), all DIAG54
lines present — the crash is hymnal-page-specific, not a harness/DIAG54
regression. (The StemBuilder `TreeMap.get` NPEs in the hymn log are
pre-existing Audiveris DEBUG-log formatting noise, non-fatal.)

**Next diagnostic DIAG55:** same per-staff print at end of REDUCTION,
MEASURES, CHORDS, CURVES (bracket the flip inside STEMS..SYMBOLS) +
barline presence at end of GRID; plus identification of the
out-of-bounds inter in the TEXTS crash to unblock the stock reference.

### §46.2 Cantique p13/p01 desktop measure merging — verdict: Wasm is right; the desktop harness is the authoritative comparator

**Deep diff (`phase56/cantique_deepdiff.py`):** key-aware exact scorer (GT
pitches carry no key-signature accidentals; Db major fifths=−5 applies
flats to B,E,A,D,G; per-bar exact = per-page exact, so no bar
misalignment). GT p13: 160 notes / 8 bars; p01: 216 / 12 bars.
- p13: desktop batch `.mxl` 124 pitched, key-aware exact 120; Wasm 158
  pitched, exact 154. **Wasm's +34 are GT-correct** (154−120=34).
- p01: desktop 149, exact 134; Wasm 158, exact 143. **Wasm's +9 are
  GT-correct** (dropped m3's 8 notes + m1's 1).

**Decomposition (desktop `.omr` model vs `.mxl`, resolving head-chord→head
via `<containment>` relations):**
- p13: desktop pipeline log says 8 raw measures [4+4]; `.omr` model has 8
  measure-slots/part (1–4, 5, 6, 7, 7C), all 134 SIG heads placed in
  measures. Desktop `.mxl` has 7 measures/part, 124 notes. Desktop SIG
  has 24 fewer heads than Wasm (134 vs 158), concentrated in system 2
  (voices bars 5/7/8: desktop SIG sys2 voice heads = 8 = bar 6 only;
  organ sys2 34 vs Wasm 45). The stock pipeline loses 10 more heads
  between SIG (134) and `.mxl` (124), all in the two "no correct rhythm"
  stacks (#2P5 m2: model 12 → `.mxl` 4; #6P5 m6: model 8 → 6).
- p01: SIGs agree (desktop 215 vs Wasm 216 heads); desktop model places
  all 215. Both sides fail rhythm on all 12 stacks (identical
  StackRhythm behaviour, §25.5 family); the stock exporter drops measure
  3 wholesale (model 17 notes → 0; Wasm exports 8) and 1 more in m1.

**Decisive harness experiments (same build, `phase56/`):**
- Desktop harness (DesktopOcrExport + MxlWriter, pre-rendered templates)
  on p13: **158 notes, per-part/per-measure counts identical to Wasm**;
  HEADS-END 360 = Wasm's `STAVES 12 HEADS 360`; SYMBOLS-END 158 (sys1
  {1=5,2=5,3=6,4=5,5=40,6=32}=93; sys2 {7=5,8=5,9=5,10=5,11=29,12=16}=65);
  tripwire `requested 84 maps to desktop catalog 80` both sides; deep diff
  vs Wasm `.musicxml`: tag counts identical, only source-path artefact
  (Wasm hardcodes `/hymn-satb.png`) + ±1 px dynamics `default-y` / ±4 px
  `relative-x` wobbles. 0 "no correct rhythm" stacks (Wasm log: 0).
- Same harness on p01: **158 notes, 12 measures, per-measure counts
  identical to Wasm** (incl. m3=8); HEADS-END total 517 = Wasm's
  `STAVES 12 HEADS 517`. Tripwire `requested 83 maps to desktop catalog 80`.
- **Root cause — the template (proven by controlled experiment):**
  harness with **stock** `TemplateFactory` (pristine, compiled into
  `phase23/classes`) gives HEADS-END 321, SYMBOLS-END 134 (sys1
  {5,5,6,5,41,30}=92; sys2 {2,2,2,2,26,8}=42), and exports **124 notes
  with per-measure counts identical to the batch `.mxl`** (2 "no correct
  rhythm" stacks, #2 and #6 — matching the batch log). Batch rerun into
  `/tmp/batch-p13-rerun` reproduced 124 exactly (deterministic, not a
  flake). So: pre-rendered catalog templates (request 84 → catalog 80, 5%
  undersize) find more heads than exact-size stock templates on p13; on
  the hymnal page the direction reverses (request 57 → catalog 64, 12%
  oversize; batch 125 vs harness/Wasm 97). The harness and Wasm agree
  partly because they share the same template approximation.

**Verdict:** Wasm is right on measure counts (8/12 = GT) and on the extra
notes (GT-correct). **Authoritative comparator for the pipeline is the
desktop harness (DesktopOcrExport + MxlWriter), NOT the desktop batch
`.mxl`** — the stock JAXB ScoreExporter drops the 7C courtesy measure
(p13) and rhythm-failed measure 3 (p01) and notes from rhythm-failed
stacks, and the batch pipeline builds exact-size templates where
harness/Wasm use the §36 pre-rendered catalog. For `.mxl`-level
comparison, use the desktop harness (same MxlWriter both sides); the batch
`.mxl` conflates pipeline behaviour with exporter behaviour and with
template differences. Caveat to record: the harness shares Wasm's
pre-rendered-template approximation, so harness==Wasm does not by itself
prove the pipeline matches stock desktop — and the approximation is
GT-favourable here (p13 key-aware exact 154 vs 120), so "fixing" the
catalog toward exact sizes would make Wasm *worse* vs GT on this page.
No catalog change in this round.

**⚠️ State — restored:** `phase23/classes/org/audiveris/omr/image/TemplateFactory.class`
held the **stock** version during the experiment; the patched (ROUND-12)
`.class` was backed up at `phase56/TemplateFactory-patched.class` and
**restored** (recompiled from `teavm/patched/src/.../TemplateFactory.java`;
md5 `7cf8f9d0140f6c42e3b45b78ffc5ca2c` matches the backup). The p01 harness
run after the restore (exit 0, 158 notes) re-verifies the harness.
Related logs: `phase56/desktop-compile-stocktemplate.log`,
`phase56/desktop-cantique-p13-stocktemplate.log`,
`phase56/desktop-cantique-p13-stocktemplate.musicxml`,
`phase56/desktop-cantique-p13-noocr111.{log,musicxml}`,
`phase56/desktop-cantique-p01-noocr111.{log,musicxml}`,
`phase56/desktop-hymnal-stocktemplate.log` (TEXTS crash, no `.musicxml` produced),
`phase56/desktop-restore-template.log`, `phase56/cantique-p13.png`,
`phase56/cantique-p01.png`, `phase56/hymnal.png`.

### §46.3 Writer-path coverage as a WRITER test — verdict: verified, no fix needed (writer correct; the gap is pipeline-side)

Grace/harmony/drums/measure-repeat emit nothing on EITHER side across the
whole validation set (verified by grep over all `wasm92`/`wasm110`/
`multi-page` `.mxl`/`.musicxml`; the one `measure-repeat` hit was a false
positive — the string in the drum file's `<source>` path, not an element),
and octave-shift `stop` is missing on both sides (`down` found on both).
Route taken: synthetic Score → `MxlWriter.build` at unit level.

**`WriterPathTest.java`** (`teavm-fork/phase23/src/teavm/`, harness-only —
NOT part of the Wasm build): runs the desktop pipeline on the hymn PNG to
PAGE, then mutates the in-memory Score/SIG with one instance of each
unexercised path, and verifies `MxlWriter.build` emits the elements.
Mutations are test-only (reflection on the protected `AbstractInter.shape`
field; synthetic inters linked into the SIG; a subclass exposing the
protected `OctaveShiftInter` geometry ctor). All 7 checks **PASS** on the
first run (`phase56/writerpath-test.{log,musicxml}`, compile
`phase56/writerpath-compile.log`):
- `<grace>` ×1 — first head of system-1 chord 1 → `NOTEHEAD_BLACK_SMALL`
  (`isSmallHead()` true).
- `<harmony>` ×1 — `ChordNameInter` (C major: root-step C, kind major)
  linked to chord 2 via `ChordNameRelation`.
- `<unpitched>` ×40 — first-measure clef → `PERCUSSION_CLEF`, so
  `Part.isDrumPart()` is true for the whole part.
- `<measure-repeat type="start" slashes="1">` ×1 (measure 3) and
  `<measure-repeat type="stop">` ×1 (measure 4) — `MeasureRepeatInter`
  (`REPEAT_ONE_BAR`) in the measure of a mid-system chord; the writer
  copies the preceding measure's content into the repeat measure.
- `<octave-shift type="down" number="1" size="8">` ×1 and
  `<octave-shift type="stop" number="1" size="8">` ×1 — 8va ALTA line from
  chord 3 (LEFT) to chord 6 (RIGHT) with no extensions; `stop` is emitted
  exactly when `os.getExtension(RIGHT) == null`.
- Output parses as well-formed XML (`score-partwise`).

**Interpretation:** `MxlWriter` handles all five paths correctly when the
model contains them. The validation gap is **pipeline-side**: Audiveris
never produces small-head grace chords, `ChordNameInter`,
percussion-clef drum parts, or `MeasureRepeatInter` on those pages (the
Ständchen grace notes are recovered as ordinary notes; the Jeanie chord
symbols never become `ChordNameInter`; the drum page's part is never
flagged as percussion). Octave-shift `stop` specifically requires an OS
inter with no RIGHT extension; on real pages (Verborgenheit) the line
extends past the last chord, so no `stop` is emitted — pipeline behaviour,
not a writer bug. Verification is at the desktop level on shared
`MxlWriter` source; these paths contain no TeaVM-sensitive operations
(no reflection, no native calls — model reads + XML building).

### §46.4 Cantique validity — verdict: diagnostics only, concluded — Audiveris behaviour identical on both sides

Low validity is the StackRhythm family (§25.5), not a Wasm divergence.
"No correct rhythm" stacks, desktop batch vs Wasm (existing logs):
p01 12 = 12 (all 12 stacks fail both sides); p02 1 = 1; p03–p10 0 = 0;
p11 1 (#1) vs 0; p12 2 (#3, #6) vs 1 (#3 — same stack fails both sides,
#6 desktop-only); p13 2 (#2, #6) vs 0. Identical on 10/13 pages; the 3
differing pages are the template-effect pages (§46.2). Validity rates:
p01 24/98 vs 24/101 (24% both); p05 7/54 both; p13 20/39 (51%) vs 33/57
(58%) — the gap follows the note-count gap, not a separate rhythm
divergence. Organ triplets (349 `<Tuplet>` elements in the source) are
hard for Audiveris on both sides. No fix in this round per the task; the
divergence question is settled — improving Audiveris rhythm itself is out
of scope. (Analysis record: `phase56/ITEM456_NOTES.md`.)

### §46.5 Orchestral latency/memory — verdict: profile only, no optimisation

36-part Beethoven 9 finale page, 2480×7319 px, 1 system, 36 staves, 2,089
head candidates, SIG 4,261. Wasm wall 791.2 s vs desktop 91.0 s, peak RSS
~1,079 MB. Per-step times from the existing Wasm log
(`open-music/wasm110/orchestral-beethoven9-finale/wasm/*.log`):

| span | Wasm | share |
|---|---|---|
| LOAD..HEADS | 128,493 ms | 16% |
| STEMS..SYMBOLS | 656,768 ms | **83%** |
| LINKS | 1,466 ms | |
| RHYTHMS | 1,350 ms | |
| PAGE | 14 ms | |
| export | 1,172 ms | |
| total main_ms | 790,280 ms | |

Desktop same page (batch-log StepMonitoring timestamps): LOAD..HEADS-start
23.5 s; HEADS..TEXTS 42.7 s; CURVES 6.5 s; SYMBOLS 6.0 s; LINKS 0.6 s;
RHYTHMS+PAGE ~4.1 s; pipeline ~84 s. Wasm/desktop ratios: HEADS family
×1.9; STEMS..SYMBOLS span ×52; LINKS ×2.4. The TeaVM penalty concentrates
in the graph-heavy SYMBOLS span, not the pixel-heavy HEADS span.
Template exact here (requested 92 → catalog 92), so the template is not a
factor on this page.

Scaling (Wasm SYMBOLS-span vs SIG size; Cantique pages have 4 systems,
orchestral has 1 system of 36 staves): p05 SIG 619 → 12.8 s; p01 SIG
1,199 → 23.9 s; p13 SIG 1,014 → 22.2 s; hymnal SIG 589 → 38.6 s (outlier —
not a pure function of SIG size); orchestral SIG 4,261 → 656.8 s
(154 ms/inter vs ~21 ms/inter on Cantique). Per staff: p01 2.0 s/staff vs
orchestral 18.2 s/staff (×9.2 for ×3 staves — roughly quadratic in
single-system graph size). No OOM; the run completed.
**Next step if pursued (no optimisation this round):** split the SYMBOLS
span with per-substep timing (STEMS/REDUCTION/MEASURES/CHORDS/CURVES/
SYMBOLS) to name the exact substep before any optimisation. (Analysis
record: `phase56/ITEM456_NOTES.md`.)

### §46.6 Hymnal OCR recall (62.5%, 233/373 stanza words) — verdict: diagnostics only, localised to lyric attachment

Misses are whole verse lines not picked up as text — localised to the
**lyric-to-note attachment (x-slot mapping)**, not OCR capture and not
TEXTS line classification. Evidence (OCR text
`teavm-fork/phase23/hymnal289-ocr.txt`, 2,463 rows: 81 L, 456 W, 1,927 C;
GT `open-music/hymnal/hymnal-am1874-p213-lyrics.json`, 11 stanzas × 6
lines = 66 lines, 373 stanza words; output
`open-music/wasm110/hymnal-am1874-p213/wasm-ocr/hymnal-am1874-p213-ocr.musicxml`,
256 lyric elements on 18 of 98 notes):
- **OCR stage: not the drop point.** Tesseract captured ALL 66 verse lines
  (OCR lines 14–79; 380 verse words vs 373 GT words, with normal misreads:
  'Otispring' for 'offspring', 'llc', 'ﬁrst', ligature/curly-quote
  confusions). OCR lines 0–13 are the title/epigraph plus the music
  staves misread as text fragments (lines 2–10); those contribute lyric
  junk ('J', 'l', 'PART', 'II.').
- **TEXTS classification: not the main drop point.** The words DO become
  lyrics (256 elements, words from all 66 lines present). No stanza or
  line is dropped wholesale at classification.
- **Attachment: the drop point.** Multiset difference OCR verse words
  (380) vs lyric elements (256): 128 words dropped. **64/128 (50%) are
  the first or last word of their verse line** — x outside the note slots
  of system 3 (before the first note / after the last note / in
  inter-note gaps). Drops spread across all 11 stanzas and both columns;
  no stanza wholly dropped (apparent whole-line drops on OCR lines 63 /
  75 / 76 are a greedy-matching artefact of repeated words like 'Praise
  and honour to the').
- **Attachment shape:** all lyrics land on P2 (system-3 lower part),
  measures 8–10, 18 notes, up to 24 lyrics per note, in vertical column
  slices — each note takes all verse words whose x falls in its slot,
  across all 66 lines. The verse text sits below the last system;
  Audiveris attaches by x-proximity to that system's notes only. That is
  the shape of this page (verses printed as text below the tune, not
  underlaid), interacting with stock Audiveris TEXTS/LyricsBuilder
  behaviour. No desktop OCR comparison exists (no Tesseract in this VM),
  so this is a Wasm-only number — but the mechanism is stock Audiveris,
  identical code on desktop.
- **Next diagnostic if pursued:** instrument LyricsBuilder to log
  per-word attach/drop decisions (x-range vs system), or run the same
  page through desktop Tesseract + Audiveris TEXTS once Tesseract is
  available, to confirm identical attachment. No behaviour change in this
  round. (Analysis record: `phase56/ITEM456_NOTES.md`.)

### §46.7 Artefacts and build state

- `teavm-fork/phase56/` — `build111.log`, `spike111.log`
  (full-out111 diagnostic build), `cantique_deepdiff.py`,
  `desktop-cantique-p13-noocr111.{log,musicxml}`,
  `desktop-cantique-p01-noocr111.{log,musicxml}`,
  `desktop-cantique-p13-stocktemplate.{log,musicxml}`,
  `desktop-compile-stocktemplate.log`, `desktop-restore-template.log`,
  `TemplateFactory-patched.class` (backup of the ROUND-12 patched
  `.class`; restored to `phase23/classes`, md5-verified),
  `desktop-hymnal-noocr111.log` (TEXTS crash),
  `desktop-hymnal-stocktemplate.{log,musicxml}` (TEXTS crash),
  `hymnal.png`, `cantique-p01.png`, `cantique-p13.png` (PIL mode `L`
  from the prep110 grey), `writerpath-compile.log`,
  `writerpath-test.{log,musicxml}`, `ITEM456_NOTES.md`.
- `teavm-fork/phase23/src/teavm/WriterPathTest.java` (+ compiled
  `.class` in `phase23/classes`) — harness-only test, not in the Wasm build.
- `teavm/patched/make_patches.py` ROUND 57 (DIAG54, print-only).
- Builds: `full-out111/` (diagnostic, DIAG54 kept); `full-out110/`
  (clean, current — unchanged). No clean build beyond full-out111.
- Still open (unchanged): DIAG53 (BWV p14 +2), DIAG55 (hymnal flip
  bracket + TEXTS-crash inter), real-browser Chrome run, upstream
  filings (deferred), BrowserOCR follow-up, photometric recovery,
  multi-file export N>1, Lindenbaum batch-vs-harness gap, Beethoven
  typeset p165, StackRhythm wobbles, Beethoven p229 wall time (profiled
  §46.5, not optimised). CheerpJ 5 remains the only working option.

## §47 — DIAG55: hymnal −28 split MEASURED — 22 template + 6 gray, 0 Wasm-side; TEXTS crash solved (DIAG24 dead block); contained fix + clean build full-out113 (2026-11-11)

**Verdict: (a) localised + contained fix applied.** The hymnal −28 is fully
split, and there is no Wasm-side loss left: Wasm equals the pre-rendered
desktop harness at every measured step, with identical checksums. The fix
in this round is the removal of the ROUND 20 DIAG24 dead block that caused
the harness TEXTS crash (harness-only artefact, stock-restoring). Clean
build **full-out113** verified byte-identical and is the new current clean
build; **full-out112** is the diagnostic build of this round (DIAG54+55
kept, ROUND 58). DIAG55 is this round's number (verified fresh: no DIAG55
print existed before it); next fresh DIAG is **DIAG56**.

### §47.1 The measured split (pitched notes; heads in brackets)

| Stage | Batch (max-RGB gray, stock tpl, stock exporter) | Harness stock (PIL-L gray, stock tpl) | Harness pre-rendered (PIL-L gray) | Wasm full-out112 (PIL-L gray) |
|---|---|---|---|---|
| HEADS-END | unmeasured (no DIAG in batch) | 584 | 572 | 572 |
| REDUCTION-END | — | 118 | 97 | 97 |
| MEASURES-END | — | 118 | 97 | 97 |
| CHORDS-END | — | 119 (+1 s1) | 97 | 97 |
| CURVES-END | — | 119 | 97 | 97 |
| SYMBOLS-END | — (≈126 final SIG, see below) | 119 | 97 | 97 |
| Export | **125 pitched / 126 notes, 12 meas/part** | BLOCKED (LINKS NPE, §47.5) | 97 / 98, 10 meas/part | 97 / 98, 10 meas/part |
| Final SIG heads (`.omr`) | **126** (35 NOTEHEAD_BLACK + 91 NOTEHEAD_VOID) | — | — | — |

Per-staff HEADS→REDUCTION (the flip lives inside STEMS, both worlds):
pre-rendered {80,89,89,72,113,129}=572 → {13,11,16,16,22,19}=97 (losses
−67/−78/−73/−56/−91/−110); stock {87,82,82,73,124,136}=584 →
{16,20,18,21,20,23}=118 (losses −71/−62/−64/−52/−104/−113). StemsStep +
SigReducer discard ~81% of head candidates on this page on both sides;
the template moves how many survive (+21 stock at REDUCTION).

**Split: 125 − 97 = 28 = 22 + 6.**
- **22 template-driven:** stock SYMBOLS-END 119 vs pre-rendered 97 —
  same PIL-L gray, same harness, only the TemplateFactory differs
  (request 57 → catalog 64, 12% oversize). Measures 13 vs 11 likewise.
- **6 gray-conversion-driven:** batch 125 pitched vs stock-harness 119
  heads — same stock templates, same harness code path family; the
  difference is the input gray. The batch input PNG is RGB; Audiveris
  converts it with max-RGB ("Converting max RGB to gray", batch log),
  while the prep grey (hence the harness PNG, the Wasm grey, and the
  harness input) is PIL-L luma. The two grays differ on **all 2,338,180
  pixels (max 22 levels)**. GRID already diverges on the gray alone:
  spurious clusters destroyed **4 (batch) vs 2 (harness-stock,
  harness-pre-rendered, Wasm)** — same templates in the stock pair, so
  not template-driven. Corroboration: the ReductionStep stem free-length
  median follows the gray, not the template — batch 32 px / 2.7
  interlines = harness-stock 32 / 2.7, while harness-pre-rendered and
  Wasm are both 33 / 2.8.
- **0 Wasm-side:** Wasm == pre-rendered harness at HEADS (572, identical
  per-staff checksums), REDUCTION, MEASURES, CHORDS, CURVES, SYMBOLS
  (97, identical checksums throughout), GRID-END barlines (identical
  x/staff lists), and the COLUMN dump to full float precision (S2
  x=878.8752905097153, S3 x=340.4904514293648 on both sides). Tripwire
  `requested 57 maps to desktop catalog 64` matches on both sides.
- Head-level arithmetic: batch final SIG 126 heads vs Wasm 97 = 29
  heads = 22 template + 7 gray (the 7th gray head is the batch's one
  unpitched note: 126 notes vs 125 pitched). The stock-harness pitched
  count is unmeasured (export blocked, §47.5), so the gray share is
  stated pitched as ≥6, heads as 7.

### §47.2 Barlines — template-driven, not a Wasm loss

DIAG55 GRID-END (BarlineInter per system, x → staff list) is **identical
on all four runs** (desktop pre-rendered, desktop stock, Wasm 112;
batch has no DIAG print but its 13 raw measures agree with stock):
sys1 `{73=[2], 74=[1], 395=[2], 396=[1], 644=[2], 645=[1], 652=[2],
653=[1], 902=[1, 2], 1097=[1, 2], 1105=[1, 2]}`,
sys2 `{75=[3, 4], 348=[4], 349=[3], 607=[3], 608=[4], 615=[3], 617=[4],
877=[4], 878=[3], 1097=[3, 4], 1105=[3, 4]}`,
sys3 `{74=[5, 6], 338=[5], 339=[6], 577=[5], 578=[6], 585=[5], 586=[6],
844=[5, 6], 999=[5], 1000=[6], 1007=[5], 1008=[6], 1098=[5, 6],
1106=[5, 6]}`. The two "missing" barlines (S2 x≈877 staff-4, S3
x≈338 staff-5) are present at GRID on every side. They disappear
between GRID and MEASURES in the pre-rendered world on BOTH desktop
harness and Wasm (DIAG54 COLUMN groups=1 at S2 x=878.88 s3-only and S3
x=340.49 s6-only, identical both sides), while the stock world keeps
groups=2 at both columns (S2 x=878.48 s3+s4, S3 x=339.89 s5+s6) and
13 raw measures [4, 4, 5] = batch (pre-rendered: 11 [4, 3, 4]). So
the 13→11 measure regrouping is a template effect, not a Wasm loss.
Note the GRID pattern: most barlines appear as adjacent ±1 px
per-staff pairs (e.g. 877[4]/878[3]) — one physical barline detected
per staff — which is why a per-staff loss at MEASURES reads as a
"missing barline" in the COLUMN dump.

### §47.3 TEXTS crash — solved: no inter, it was the DIAG24 dead block

§46's open item ("identification of the out-of-bounds inter") is
closed by inspection: there is no inter. The crash is
`SheetScanner.getCleanImage:143`, i.e. the ROUND 20 DIAG24 block
(§23 trap 4) calling `img.getRGB(xx, yy)` over the hard-coded ROI
x 1854..1929, y 574..609. The hymnal page is 1196 px wide, so x=1854
is out of bounds on the first pixel. §46's "(via
TextsCleaner.eraseInters)" attribution was wrong — eraseInters is
line 130; line 143 is the DIAG24 getRGB. The block computes bx/ix
that nothing reads (dead code); it survived the §43 strip because
tier 1 only removes `System.out` prints. It is the ONLY
patched-vs-repo diff in `SheetScanner.java`, so removing it restores
the repo-original `getCleanImage` exactly. **Fix (ROUND 58,
`read_out` per §39.1): the block is removed.** The desktop harness
now passes TEXTS on the hymnal, exit 0, both template variants.
Harness-only artefact: the block exists only in patched sources
(stock Audiveris has no such code, so the batch never crashed), and
Wasm never surfaced it (the full-out110 run completed with the block
present). The first ROUND 58 build attempt failed loudly on a
truncated anchor (the block also contains a `DIAG24 cleanCheck`
println my first anchor missed — the earlier diff view had been
truncated at 60 lines); the anchor was corrected to the full block
and the build passed.

### §47.4 DIAG55 method (ROUND 58, `teavm/patched/make_patches.py`)

Inserted after ROUND 57, before the ROUND 49 strip; diagnostic build
run with `TEAVM_KEEP_DIAG=54,55` so DIAG54 prints survive alongside
DIAG55. Six sites, print-only apart from §47.3:
- `SheetScanner` (read_out): DIAG24 block removal (§47.3).
- `GridStep.doit` end (read_out, R2 displayUI no-op only): DIAG55
  GRID-END barline print (BarlineInter per system, TreeMap x →
  staff list, sorted by x).
- `ReductionStep.doEpilog` end (copy_src, pristine): DIAG55
  REDUCTION-END per-staff HeadInter counts+checks (DIAG54 shape).
- `MeasuresStep.doEpilog` end (copy_src, pristine): DIAG55
  MEASURES-END.
- `ChordsStep` (copy_src, pristine): new `doEpilog` override (class
  has none) with DIAG55 CHORDS-END.
- `CurvesStep.doit` end (copy_src, pristine): DIAG55 CURVES-END.
All prints use fully-qualified names (no import edits). Build:
`phase57/build112.log` (BUILD OK, patched/classes 394 — was 368,
+26 from the 4 new step files and their inner classes); Spike
`phase57/spike112.log` (0 problems, 3,055 classes, 28,730 methods;
full-out111 was 28,728 — +2 is the new ChordsStep doEpilog + one
synthetic). Desktop harness: the 6 changed files compiled alone into
`phase23/classes` (`phase57/desktop-compile-diag55.log`, javac exit
0; none on the §29.2 excluded list). Stock-template experiment:
patched `TemplateFactory.class` backed up to
`phase57/TemplateFactory-patched112.class`, stock repo
`TemplateFactory.java` compiled in (md5 f8e8674e…), run, then the
patched class restored (md5 7cf8f9d0140f6c42e3b45b78ffc5ca2c =
`phase56/TemplateFactory-patched.class`), and the hymn control
re-run after the restore (exit 0, `.mxl` md5 9b058b42… = known-good
§41 value).

### §47.5 Residuals and notes (not regressions)

- **Stock-harness LINKS NPE (new, stock Audiveris, not a TeaVM
  defect):** the stock-template harness run exits 1 in LINKS
  doEpilog — `SlurInter.isSpaceClear:754` ← `checkStaffTie:447` ←
  `LinksStep.doEpilog:112`: `Part.getMeasureAt(Point2D)` returns null
  for a slur point, i.e. a slur falls outside all measures in the
  stock-template SIG. The batch does not hit it (different SIG via
  the gray) and Wasm does not hit it (pre-rendered SIG completes
  LINKS). It blocks the stock-harness export, which is why the stock
  pitched count is unmeasured (§47.1). No fix in this round — it is a
  stock-Audiveris robustness gap (getMeasureAt-null), out of scope
  for the TeaVM fork; candidate for the deferred upstream list, as an
  Audiveris issue, not a TeaVM issue. It does not affect the split:
  the split is measured at SYMBOLS-END, before LINKS.
- **+1 head at CHORDS, stock world only:** REDUCTION 118 → CHORDS
  119 (staff 1, check 13394 → 13945); pre-rendered is flat 97 → 97.
  One HeadInter appears between REDUCTION and CHORDS in the stock
  world. Not pursued to the inter level — it moves the template
  share from 21 (at REDUCTION) to 22 (at SYMBOLS) and changes
  nothing else.
- **Lindenbaum batch-vs-harness gap (§46 open item):** the hymnal
  residual shows batch-vs-harness gaps can come from the gray
  conversion alone (max-RGB vs PIL-L). Before treating the
  Lindenbaum gap as a pipeline divergence, check whether its batch
  and harness inputs differ the same way.
- **Strip note for a future round:** the DIAG24 block survived the
  §43 strip because it contains no println — only a `println` was
  stripped from it in clean builds, leaving the crashing loops.
  A future strip pass could flag leftover `// DIAG<digit>` comment
  blocks whose code has no live use; not done here.

### §47.6 Fix applied — clean build full-out113

The §47 round's code change is the DIAG24 dead-block removal
(stock-restoring, output-neutral by construction). Verification:
- Hymnal Wasm full-out112: `.mxl` md5
  `56c5941c661ba048b84cb652109fe427` (38,762 B) — **byte-identical to
  full-out110/111**.
- Controls on full-out112 (no-OCR): hymn `75637092…` (44,105 B),
  Hallelujah SATB `126771ec…` (105,434 B), Lindenbaum `dbd546ba…`
  (99,305 B) — all byte-identical to the full-out110 known-good
  values.
- Desktop hymn control on the new `phase23/classes`: exit 0,
  `.mxl` md5 `9b058b42…` — known-good §41 value.
- **Clean build full-out113** (`./build.sh` with no
  `TEAVM_KEEP_DIAG`; `phase57/build113.log`, strip verified: 0 live
  DIAG printlns in patched/src, DIAG24 block gone; Spike
  `phase57/spike113.log`, 0 problems, 3,055 classes, 28,730
  methods): hymnal + all three controls **byte-identical to
  full-out112** (hymnal `56c5941c…`, hymn `75637092…`, Hallelujah
  `126771ec…`, Lindenbaum `dbd546ba…`).
- **full-out113 is the new current clean build.** full-out112
  remains the diagnostic build of this round (DIAG54+55 kept);
  full-out110 is superseded (its Wasm output is byte-identical to
  full-out113 on all four verified pages; the only code delta is
  the DIAG24 removal).

### §47.7 Artefacts and build state

- `teavm-fork/phase57/` — `build112.log`, `spike112.log`,
  `build113.log`, `spike113.log`, `desktop-compile-diag55.log`,
  `desktop-hymnal-noocr112.{log,musicxml}` (pre-rendered harness,
  exit 0, 97 pitched / 98 notes, 38,643 B),
  `desktop-hymnal-stocktemplate112.log` (stock harness, LINKS NPE,
  no `.musicxml`; DIAG55 lines through SYMBOLS-END),
  `desktop-compile-stocktemplate112.log`,
  `TemplateFactory-patched112.class` (backup of the patched
  `.class`; restored to `phase23/classes`, md5-verified),
  `desktop-hymn-noocr112.{log,musicxml}` (control, md5 `9b058b42…`),
  `run-hymnal-noocr112.log`, `wasm-hymnal-noocr112.musicxml` (md5
  `56c5941c…`), `run-hymn-112.log`,
  `wasm-hymn-noocr112.musicxml`, `run-hallelujah-satb-112.log`,
  `wasm-hallelujah-satb-noocr112.musicxml`,
  `run-lindenbaum-112.log`, `wasm-lindenbaum-noocr112.musicxml`,
  `run-hymnal-noocr113.log`, `wasm-hymnal-noocr113.musicxml`,
  `run-hymn-113.log`, `wasm-hymn-noocr113.musicxml`,
  `run-hallelujah-satb-113.log`,
  `wasm-hallelujah-satb-noocr113.musicxml`,
  `run-lindenbaum-113.log`, `wasm-lindenbaum-noocr113.musicxml`.
- `teavm/patched/make_patches.py` ROUND 58 (DIAG55 + DIAG24 removal).
- Builds: **full-out113** (clean, current); **full-out112**
  (diagnostic, DIAG54+55 kept); full-out110 superseded (output-identical
  on all verified pages); full-out111 diagnostic-only (DIAG54).
- Still open (unchanged except DIAG55 now done): DIAG53 (BWV p14 +2),
  real-browser Chrome run, upstream filings (deferred; plus the
  §47.5 LinksStep getMeasureAt-null stock robustness note as an
  Audiveris candidate, not TeaVM), BrowserOCR follow-up, photometric
  recovery, multi-file export N>1, Lindenbaum batch-vs-harness gap
  (re-examine via the gray-conversion lens, §47.5), Beethoven
  typeset p165, StackRhythm wobbles, Beethoven p229 wall time
  (profiled §46.5, not optimised). CheerpJ 5 remains the only working
  option.
