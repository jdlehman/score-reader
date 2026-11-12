#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Build @jdlehman/score-view into one ES module, app/score-view.js, which is committed here. It
# draws the score after a read and makes the note edits. The package is MIT and lives in the
# midi_studio repository, where Sectional uses it too: change it there, commit, and run this again.
# Don't edit app/score-view.js. Its first lines say which midi_studio commit it was built from.
#   ./update-score-view.sh [path to midi_studio]   (default: ../midi_studio, with npm ci done)
set -e
cd "$(dirname "$0")"
MS=${1:-../midi_studio}
PKG="$MS/packages/score-view"
[ -f "$PKG/src/index.ts" ] || { echo "No packages/score-view in $MS" >&2; exit 1; }
if [ -n "$(git -C "$MS" status --porcelain -- packages/score-view)" ]; then
  echo "packages/score-view has changes that aren't committed: commit them first, so the file can say where it came from." >&2
  exit 1
fi
COMMIT=$(git -C "$MS" rev-parse --short HEAD)
TMP=$(mktemp -d)
"$MS/node_modules/.bin/rolldown" "$PKG/src/index.ts" --format esm --platform browser --file "$TMP/score-view.js" --log-level warn
{
  printf '// @jdlehman/score-view %s, built from midi_studio commit %s (packages/score-view) by\n' "$(sed -n 's/.*"version": "\(.*\)".*/\1/p' "$PKG/package.json")" "$COMMIT"
  printf "// Score Reader's update-score-view.sh. Change it there, not here. Its licence:\n//\n"
  sed 's|^|// |; s| *$||' "$PKG/LICENSE"
  echo
  cat "$TMP/score-view.js"
} > app/score-view.js
rm -rf "$TMP"
echo "app/score-view.js: $(wc -c < app/score-view.js | tr -d ' ') bytes, from midi_studio $COMMIT"
