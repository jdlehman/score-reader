#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build the deblur pre-step for the browser with TeaVM (WebAssembly GC) into
# .work/teavm/deblur-out/classes.wasm (teavm/deblur/src/teavm/Deblur.java).
#   teavm/deblur-build.sh   (needs .work/ from ./setup.sh; run by teavm/build.sh)
# The module is small (about 19 KB) and separate from the Audiveris build: it only needs TeaVM's
# release jars, not the fork fixes or Audiveris, and it changes rarely. TEAVM_STRICT=0 builds
# without TeaVM's null and bounds checks, as in teavm/build.sh.
set -e
cd "$(dirname "$0")/.."
J=$(ls -d .work/jdk/*/Contents/Home/bin .work/jdk/*/bin 2>/dev/null | head -1) # macOS or Linux
L=.work/teavm-lib # TeaVM's jars (setup.sh)
W=${TEAVM_WORK:-.work/teavm} # everything built here (TEAVM_WORK to build elsewhere)
TEAVM_JARS="$L/teavm-interop-0.16.0.jar:$L/teavm-jso-0.16.0.jar:$L/teavm-jso-apis-0.16.0.jar:$L/teavm-jso-impl-0.16.0.jar:$L/teavm-metaprogramming-api-0.16.0.jar:$L/teavm-metaprogramming-impl-0.16.0.jar:$L/teavm-platform-0.16.0.jar"
jc() { "$J/javac" -nowarn "$@" > $W/deblur-javac.log 2>&1 || { cat $W/deblur-javac.log >&2; exit 1; }; }

mkdir -p $W/deblur-classes
jc -proc:none -d $W/deblur-classes -cp "$L/teavm-jso-0.16.0.jar" \
  teavm/deblur/src/teavm/Deblur.java

mkdir -p $W/deblur-compiler
jc -cp "$L/*" -d $W/deblur-compiler teavm/Spike.java

mkdir -p $W/deblur-out
STRICT=-Dteavm.strict=true; [ "$TEAVM_STRICT" = 0 ] && STRICT=
"$J/java" -Xmx4g $STRICT -cp "$L/*:$W/deblur-compiler" Spike wasm-gc $W/deblur-out teavm.Deblur \
  $W/deblur-classes $L/teavm-classlib-0.16.0.jar $L/teavm-core-0.16.0.jar $(echo "$TEAVM_JARS" | tr ':' ' ') \
  > $W/deblur-compile.log 2>&1 || true
if grep -q '^PROBLEM' $W/deblur-compile.log || [ ! -f $W/deblur-out/classes.wasm ]; then
  grep '^PROBLEM' $W/deblur-compile.log | head -20 >&2; echo "TeaVM deblur failed: $W/deblur-compile.log" >&2; exit 1
fi
echo "deblur: $(du -h $W/deblur-out/classes.wasm | cut -f1) $(grep -o 'Classes compiled: [0-9]*' $W/deblur-compile.log)"
