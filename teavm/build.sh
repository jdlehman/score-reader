#!/usr/bin/env bash
# Build shims.jar, patched Audiveris classes, and the TeavmMain entry classes.
# Usage: ./build.sh   (re-runs make_patches.py first, so patched/src is fresh)
set -e
cd "$(dirname "$0")"
J=~/workspace/score-reader-spikes/repo/.work/jdk/jdk-25.0.5+8/bin
CP_PROG=$(paste -sd: program-jars.txt)
CP_PROG="$CP_PROG:$PWD/lib/jzlib-1.1.3.jar"   # jzlib was missing from repo .work/lib

python3 patched/make_patches.py

# 0. regenerate the AWT/Swing stub sources (idempotent)
python3 shims/gen_awt.py > /dev/null
python3 shims/gen_awt2.py > /dev/null
python3 shims/gen_swing2.py > /dev/null
python3 shims/gen_swing3.py > /dev/null

# 1. shims (three passes: java.base shims first, then java.desktop shims,
#    then java.xml shims, each against the earlier passes' classes;
#    a single pass fails with 83 errors)
rm -rf shims/classes && mkdir -p shims/classes
"$J/javac" --patch-module java.base=shims/src -d shims/classes \
    $(find shims/src/java/lang shims/src/java/util shims/src/java/text shims/src/java/io shims/src/java/nio shims/src/java/security shims/src/java/net shims/src/org -name '*.java' ! -path '*/w3c/*')
"$J/javac" --patch-module java.desktop=shims/src -cp shims/classes -d shims/classes \
    $(find shims/src/java/awt shims/src/java/applet shims/src/java/beans shims/src/javax/imageio shims/src/javax/swing -name '*.java' ! -path '*/datatransfer/*')
# 2b. java.datatransfer lives in its own module, not java.desktop
"$J/javac" --patch-module java.datatransfer=shims/src -cp shims/classes -d shims/classes \
    $(find shims/src/java/awt/datatransfer -name '*.java')
"$J/javac" --patch-module java.xml=shims/src -cp shims/classes -d shims/classes \
    $(find shims/src/javax/xml shims/src/org/w3c/dom -name '*.java')
"$J/jar" --create --file shims.jar -C shims/classes .
echo "shims.jar OK: $(ls -la shims.jar | awk '{print $5}') bytes"

# 1b. ASM rewrites (see tools/RewriteJars.java):
#   - PhantomReference super(referent) -> super() inside shims.jar
#     (TeaVM's TReference has only a no-arg ctor)
#   - ij Color.<lowercase> field refs -> TColor equivalents (lib-patched/)
#   - jgrapht SupplierUtil.canAccess check skipped (lib-patched/)
mkdir -p tools/classes lib-patched
"$J/javac" -cp "lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" -d tools/classes tools/RewriteJars.java
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" RewriteJars phantom shims.jar
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" RewriteJars ij ~/workspace/score-reader-spikes/repo/.work/lib/ij-1.54p.jar lib-patched/ij-1.54p-teavm.jar
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" RewriteJars jgrapht ~/workspace/score-reader-spikes/repo/.work/lib/jgrapht-core-1.5.2.jar lib-patched/jgrapht-core-1.5.2-teavm.jar
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar:$HOME/workspace/score-reader-spikes/repo/.work/lib/bsaf-1.9.2.jar" RewriteJars bsaf ~/workspace/score-reader-spikes/repo/.work/lib/bsaf-1.9.2.jar lib-patched/bsaf-1.9.2-teavm.jar
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" RewriteJars jaxb ~/workspace/score-reader-spikes/repo/.work/lib/jaxb-api-2.3.1.jar lib-patched/jaxb-api-2.3.1-teavm.jar
"$J/java" -cp "tools/classes:lib/asm-9.10.1.jar:lib/asm-tree-9.10.1.jar" RewriteJars colorfields ~/workspace/score-reader-spikes/repo/.work/lib/jgoodies-forms-1.9.0.jar lib-patched/jgoodies-forms-1.9.0-teavm.jar

# 2. patched Audiveris sources + entry (compiled together: patched LoadStep
#    references teavm.TeavmImageHolder, entry references patched classes)
rm -rf patched/classes && mkdir -p patched/classes
"$J/javac" -d patched/classes \
    -cp "$CP_PROG:$PWD/shims.jar:$PWD/lib/teavm-jso-0.16.0.jar" \
    $(find patched/src entry/src -name '*.java')
echo "patched/classes OK: $(find patched/classes -name '*.class' | wc -l) classes"
echo BUILD OK

# 3. reflection policy (compile-time only, DIAG10): TeaVM generates field-reflection
#    metadata only for members a ReflectionPolicy declares accessible; without it,
#    Class.getDeclaredFields() returns [] and ConstantSet.initMap() builds an empty map.
#    Compiled into policy-classes/ (with META-INF/services) and added to the program
#    classpath in teavm-fork/teavm-main-jars-corepatch.txt.
rm -rf policy-classes && mkdir -p policy-classes
"$J/javac" -cp "lib/teavm-extension-spi-0.16.0.jar:lib/teavm-extension-apis-0.16.0.jar" -d policy-classes \
    $(find policy/src -name '*.java')
cp -r policy/src/META-INF policy-classes/
echo "policy-classes OK: $(find policy-classes -name '*.class' | wc -l) classes"
