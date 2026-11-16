#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Fetch TrOMR's browser runner files into .work/tromr/ (build.sh copies them to dist/tromr/):
# the CrispEmbed WebAssembly build (MIT, from crispstrobe/CrispEmbed's deployed site) and the
# TrOMR model (Apache-2.0, from Hugging Face, pinned to a commit). Nothing is committed to the
# repo: the model is 32 MB, and the site serves its own copies at read time — no request to
# anyone else's server happens during a read.
#   teavm/tromr-fetch.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p .work/tromr

# The model is pinned to a Hugging Face commit, not the moving main branch: a new upload must
# not silently change what the site reads.
MODEL_COMMIT=f7912e2c68d5d89c9ff2546bbbcc736268822af0

# sha256 <file>: print the hex digest, on Linux (sha256sum) or macOS (shasum)
sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

# fetch <url> <sha256> <dest>: keep what is already there when it matches, otherwise download
# to a temporary file and only move it into place once the checksum matches.
fetch() {
  url=$1; want=$2; dest=$3
  if [ -f "$dest" ] && [ "$(sha256 "$dest")" = "$want" ]; then
    echo "tromr: $(basename "$dest") already there"
    return
  fi
  tmp="$dest.tmp"
  curl -fsSL "$url" -o "$tmp"
  got=$(sha256 "$tmp")
  if [ "$got" != "$want" ]; then
    echo "tromr: checksum mismatch for $(basename "$dest"): got $got, want $want" >&2
    rm -f "$tmp"
    exit 1
  fi
  mv "$tmp" "$dest"
  echo "tromr: fetched $(basename "$dest")"
}

fetch https://crispstrobe.github.io/CrispEmbed/crispembed_ocr.js \
  957158169d342d892bcefc6081423f4afd3d393ffbeed65cfedd925526f532cb .work/tromr/crispembed_ocr.js
fetch https://crispstrobe.github.io/CrispEmbed/crispembed_ocr.wasm \
  59501fcd4746b106e329a9002fde7a6154d9b6f93761b97f43ff57235265f1c3 .work/tromr/crispembed_ocr.wasm
fetch "https://huggingface.co/cstr/tromr-GGUF/resolve/$MODEL_COMMIT/tromr-q8_0.gguf" \
  dcefa3654290c2d0fd170cab75404b478b28ad926566c45c57dbd5bb299c105e .work/tromr/tromr-q8_0.gguf
