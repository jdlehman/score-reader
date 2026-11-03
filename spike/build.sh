#!/bin/sh
# Score reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build the browser classpath: Audiveris with our patches, its jars rewritten to use FastMath.
#   spike/build.sh   (needs .work/ as ./setup.sh makes it)
set -e
cd "$(dirname "$0")/.."
J=$(ls -d .work/jdk/*/Contents/Home/bin .work/jdk/*/bin 2>/dev/null | head -1) # macOS or Linux
SRC=.work/audiveris/app/src/main/java/org/audiveris/omr

# 1. our changed Audiveris classes, compiled against the Audiveris jars
rm -rf .work/classes && mkdir -p .work/classes
"$J/javac" -nowarn -proc:none -cp ".work/lib/*" -d .work/classes \
  $SRC/sheet/Book.java $SRC/sheet/Sheet.java $SRC/sheet/Picture.java $SRC/CLI.java $SRC/Main.java $SRC/ScoreReaderHook.java \
  $SRC/image/MorphoProcessor.java $SRC/image/FlatMorphology.java 2>&1 | grep -v '^Note:' || true
"$J/jar" cf .work/patched.jar -C .work/classes .

# 2. FastMath and the rewriter
rm -rf .work/fastclasses && mkdir -p .work/fastclasses
"$J/javac" -d .work/fastclasses java/org/scorereader/FastMath.java java/org/scorereader/Rewrite.java

# 3. every jar rewritten to call FastMath, patched classes first
rm -rf .work/fast
(echo .work/patched.jar; tr ':' '\n' < .work/classpath.txt | sed 's|^/app/||') \
  | xargs "$J/java" -cp .work/fastclasses org.scorereader.Rewrite .work/fast
"$J/jar" cf .work/fast/scorereader.jar -C .work/fastclasses org/scorereader/FastMath.class
(printf '/app/.work/fast/patched.jar:/app/.work/fast/scorereader.jar:'; sed 's|/app/.work/lib/|/app/.work/fast/|g' .work/classpath.txt) > .work/classpath-fast.txt
echo built
