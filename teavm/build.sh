#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build Audiveris for the browser with TeaVM (WebAssembly GC) into .work/teavm/out/classes.wasm.
#   teavm/build.sh   (needs .work/ from ./setup.sh, and .work/patched.jar from ./build.sh)
# TEAVM_STRICT=0 builds without TeaVM's null and bounds checks (smaller and a little faster, but a
# null dereference then kills the whole run instead of being an exception Audiveris can catch).
set -e
cd "$(dirname "$0")/.."
J=$(ls -d .work/jdk/*/Contents/Home/bin .work/jdk/*/bin 2>/dev/null | head -1) # macOS or Linux
L=.work/teavm-lib # TeaVM's jars and the source of the classes teavm/fork/ fixes (setup.sh)
W=${TEAVM_WORK:-.work/teavm} # everything built here (TEAVM_WORK to build elsewhere)
ASM="$L/asm-9.10.1.jar:$L/asm-tree-9.10.1.jar"
TEAVM_JARS="$L/teavm-interop-0.16.0.jar:$L/teavm-jso-0.16.0.jar:$L/teavm-jso-apis-0.16.0.jar:$L/teavm-jso-impl-0.16.0.jar:$L/teavm-metaprogramming-api-0.16.0.jar:$L/teavm-metaprogramming-impl-0.16.0.jar:$L/teavm-platform-0.16.0.jar"
[ -f .work/patched.jar ] || { echo "run ./build.sh first: TeaVM's build uses its .work/patched.jar" >&2; exit 1; }
rm -rf $W && mkdir -p $W
jc() { "$J/javac" -nowarn "$@" > $W/javac.log 2>&1 || { cat $W/javac.log >&2; exit 1; }; }

# 1. TeaVM's own bugs, fixed (teavm/fork/, see FORK_FIX.md): those classes of its release, patched and
# compiled to go before the release's jars
mkdir -p $W/fork-src
grep -h '^+++ b/' teavm/fork/*.patch | sed 's|^+++ b/[a-z]*/src/main/java/||' | sort -u | while read -r f; do
  case $f in */classlib/*) jar=teavm-classlib ;; *) jar=teavm-core ;; esac
  unzip -q -o -d $W/fork-src "$L/$jar-0.16.0-sources.jar" "$f"
done
for p in teavm/fork/*.patch; do patch -s -p5 -d $W/fork-src < "$p"; done
jc --release 17 -cp "$L/teavm-classlib-0.16.0.jar:$L/*" -d $W/fork-classlib $(find $W/fork-src -path '*/classlib/*' -name '*.java')
jc --release 17 -cp "$L/*" -d $W/fork-core $(find $W/fork-src -path '*/backend/*' -name '*.java')

# 2. Audiveris's source (ours applied) with the TeaVM patches
TEAVM_PATCHED_SRC=$W/patched-src PYTHONDONTWRITEBYTECODE=1 python3 teavm/patched/make_patches.py > /dev/null

# 3. the JDK classes TeaVM's class library lacks or gets wrong: AWT, Swing and XML stubs and shims,
# compiled in passes, each against the ones before (one pass fails)
for g in gen_awt gen_awt2 gen_swing2 gen_swing3; do python3 teavm/shims/$g.py > /dev/null; done
S=teavm/shims/src
mkdir -p $W/shims
jc --patch-module java.base=$S -d $W/shims \
  $(find $S/java/lang $S/java/util $S/java/text $S/java/io $S/java/nio $S/java/security $S/java/net $S/org -name '*.java' ! -path '*/w3c/*')
jc --patch-module java.desktop=$S -cp $W/shims -d $W/shims \
  $(find $S/java/awt $S/java/applet $S/java/beans $S/javax/imageio $S/javax/swing -name '*.java' ! -path '*/datatransfer/*')
jc --patch-module java.datatransfer=$S -cp $W/shims -d $W/shims $(find $S/java/awt/datatransfer -name '*.java')
jc --patch-module java.xml=$S -cp $W/shims -d $W/shims $(find $S/javax/xml $S/org/w3c/dom -name '*.java')
"$J/jar" --create --file $W/shims.jar -C $W/shims .

# 4. bytecode rewrites TeaVM needs (teavm/tools/RewriteJars.java): in the shims, and in five of the
# release's jars
mkdir -p $W/tools $W/lib-patched
jc -cp "$ASM" -d $W/tools teavm/tools/RewriteJars.java
R="$J/java -cp $W/tools:$ASM RewriteJars"
$R phantom $W/shims.jar
$R ij .work/lib/ij-1.54p.jar $W/lib-patched/ij-1.54p-teavm.jar
$R jgrapht .work/lib/jgrapht-core-1.5.2.jar $W/lib-patched/jgrapht-core-1.5.2-teavm.jar
"$J/java" -cp "$W/tools:$ASM:.work/lib/bsaf-1.9.2.jar" RewriteJars bsaf .work/lib/bsaf-1.9.2.jar $W/lib-patched/bsaf-1.9.2-teavm.jar
$R jaxb .work/lib/jaxb-api-2.3.1.jar $W/lib-patched/jaxb-api-2.3.1-teavm.jar
$R colorfields .work/lib/jgoodies-forms-1.9.0.jar $W/lib-patched/jgoodies-forms-1.9.0-teavm.jar

# 5. the release's jars, in the page's order, and jzlib (which the desktop gets from its JDK)
PROG=$(tr ':' '\n' < .work/classpath.txt | sed 's|^/app/||')
PROG="$PROG
$L/jzlib-1.1.3.jar"

# 6. the patched Audiveris classes and the entry (together: each refers to the other)
mkdir -p $W/classes
jc -proc:none -d $W/classes -cp "$(echo "$PROG" | paste -sd: -):$W/shims.jar:$L/teavm-jso-0.16.0.jar" \
  $(find $W/patched-src teavm/entry/src -name '*.java')

# 7. the reflection TeaVM must keep (teavm/policy/): only for the compiler
mkdir -p $W/policy
jc -cp "$L/teavm-extension-spi-0.16.0.jar:$L/teavm-extension-apis-0.16.0.jar" -d $W/policy $(find teavm/policy/src -name '*.java')
cp -R teavm/policy/src/META-INF $W/policy/

# 8. compile to WebAssembly. What the program is made of, first found first: the shims, TeaVM (fixed
# classes first), the TeaVM-patched Audiveris classes, then ours (.work/patched.jar: a change to
# Audiveris in patches/ reaches the browser build without being copied here), the rewritten jars,
# and the release's jars.
{
  echo $W/shims.jar; echo $W/policy
  echo $W/fork-classlib; echo $L/teavm-classlib-0.16.0.jar; echo $W/fork-core; echo $L/teavm-core-0.16.0.jar
  echo "$TEAVM_JARS" | tr ':' '\n'
  echo $W/classes; echo .work/patched.jar
  ls $W/lib-patched/*.jar
  echo "$PROG"
} > $W/classpath.txt
mkdir -p $W/compiler
jc -cp "$L/*" -d $W/compiler teavm/Spike.java
STRICT=-Dteavm.strict=true; [ "$TEAVM_STRICT" = 0 ] && STRICT=
"$J/java" -Xmx4g $STRICT -cp "$W/fork-core:$L/*:$W/compiler" Spike wasm-gc $W/out teavm.TeavmMain @$W/classpath.txt > $W/compile.log 2>&1 || true
if grep -q '^PROBLEM' $W/compile.log || [ ! -f $W/out/classes.wasm ]; then
  grep '^PROBLEM' $W/compile.log | head -20 >&2; echo "TeaVM failed: $W/compile.log" >&2; exit 1
fi
cp teavm/runtime.mjs $W/out/

# 9. the note-head templates, drawn by desktop Audiveris (ours) from its fonts, a file a font and
# point size: the page fetches the one a page needs (teavm/entry/src/teavm/PreRenderedTemplates.java).
# From the smallest heads Audiveris reads (staff lines 11 pixels apart) to the biggest in a page of
# 4096 pixels; Leland for the second whole-note match (NOTES.md).
mkdir -p $W/dump
jc -proc:none -cp ".work/patched.jar:.work/lib/*" -d $W/dump teavm/generate/TemplateDump.java
"$J/java" -Djava.awt.headless=true -cp ".work/patched.jar:.work/lib/*:$W/dump" TemplateDump $W/out/templates 32 200 Bravura Leland > $W/dump/log.txt 2>&1 \
  || { tail -20 $W/dump/log.txt >&2; exit 1; }
echo "teavm: $(du -h $W/out/classes.wasm | cut -f1) $(grep -o 'Classes compiled: [0-9]*' $W/compile.log), $(ls $W/out/templates | wc -l | tr -d ' ') template files"
