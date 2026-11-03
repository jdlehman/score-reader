#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Make .work/, which ./build.sh needs: Audiveris 5.11.0's source with our patch applied, the jars
# of its release, their class path, a Temurin JDK 25, and the source of the copyleft libraries.
#   ./setup.sh   (on macOS or Linux; needs git and curl, and dpkg-deb on Linux)
# Each part is skipped if it is already there.
set -e
cd "$(dirname "$0")"
V=5.11.0
mkdir -p .work

# the SHA-256 of each release file used, as GitHub lists them: what the site serves is built from these
sha256() { (sha256sum "$1" 2>/dev/null || shasum -a 256 "$1") | cut -d' ' -f1; }
check() {
  [ "$(sha256 "$1")" = "$2" ] || { echo "$1: not the file released (SHA-256 differs)" >&2; exit 1; }
}

# 1. the source, for the classes we change (patches/; the files have CRLF line ends)
if [ ! -d .work/audiveris ]; then
  git -c core.autocrlf=false -c advice.detachedHead=false clone -q --depth 1 -b $V https://github.com/Audiveris/audiveris .work/audiveris
  git -C .work/audiveris apply --whitespace=nowarn "$PWD/patches/0001-score-reader.patch"
  echo "source: Audiveris $V, patched"
fi

# 2. the release's jars (the same in every installer; there is no plain zip of them)
if [ ! -d .work/lib ]; then
  tmp=$(mktemp -d)
  release=https://github.com/Audiveris/audiveris/releases/download/$V
  case $(uname) in
    Darwin)
      arch=$(uname -m | sed 's/aarch64/arm64/')
      curl -fsSL -o "$tmp/a.dmg" "$release/Audiveris-$V-macosx-$arch.dmg"
      case $arch in
        arm64) check "$tmp/a.dmg" 17491af8b6d40153b031dd1f0815e37213f0999ef23f10586af46706e59b2eb6 ;;
        *) check "$tmp/a.dmg" 11794424c6f1698617836a77d2c5818c46405a3fe7388281c623c4e383fa33cb ;;
      esac
      # the image shows Audiveris's licence (the AGPL) and asks to agree before it opens
      yes | PAGER=cat hdiutil attach -nobrowse -readonly -mountpoint "$tmp/mnt" "$tmp/a.dmg" > /dev/null
      app="$tmp/mnt/Audiveris.app/Contents/app"
      ;;
    Linux)
      curl -fsSL -o "$tmp/a.deb" "$release/Audiveris-$V-ubuntu24.04-x86_64.deb"
      check "$tmp/a.deb" f20113aaa33b3149ec8d6a09b2a7963360e65fafd92d69389987a85bbc3ec7a3
      dpkg-deb -x "$tmp/a.deb" "$tmp/deb"
      app=$(dirname "$(find "$tmp/deb" -name audiveris.jar | head -1)")
      ;;
  esac
  mkdir -p .work/lib
  cp "$app"/*.jar .work/lib/
  [ -d "$tmp/mnt" ] && hdiutil detach -quiet "$tmp/mnt"
  rm -rf "$tmp"
  echo "jars: $(ls .work/lib | wc -l | tr -d ' ') from the $V release"
fi

# 3. the class path, as the page names the jars: in name order (a few classes are in two jars, and
# this is the order that was tested), leaving out the native code for OCR, which can't run here
ls .work/lib/*.jar | grep -Ev -- '-(macosx|linux|windows)-' | LC_ALL=C sort | sed 's|^|/app/|' | paste -sd: - | tr -d '\n' > .work/classpath.txt

# 4. a JDK 25, to compile our classes and run the jar rewriter
if [ ! -d .work/jdk ]; then
  case $(uname) in Darwin) os=mac ;; Linux) os=linux ;; esac
  case $(uname -m) in arm64 | aarch64) arch=aarch64 ;; *) arch=x64 ;; esac
  mkdir -p .work/jdk
  curl -fsSL "https://api.adoptium.net/v3/binary/latest/25/ga/$os/$arch/jdk/hotspot/normal/eclipse" | tar xz -C .work/jdk
  echo "jdk: $(ls .work/jdk)"
fi

# 5. the source of the libraries under copyleft licences (AGPL, LGPL, CDDL, EPL), which the site
# serves next to their jars (in source/), as Maven Central publishes it. The rest are permissive.
if [ ! -d .work/sources ]; then
  mkdir -p .work/sources.tmp
  for p in \
    com/itextpdf/itextpdf/5.5.13.2/itextpdf-5.5.13.2 \
    org/jfree/jfreechart/1.5.6/jfreechart-1.5.6 \
    org/jdesktop/bsaf/bsaf/1.9.2/bsaf-1.9.2 \
    org/audiveris/proxymusic/4.0.3/proxymusic-4.0.3 \
    ch/qos/logback/logback-classic/1.4.14/logback-classic-1.4.14 \
    ch/qos/logback/logback-core/1.4.14/logback-core-1.4.14 \
    org/jgrapht/jgrapht-core/1.5.2/jgrapht-core-1.5.2 \
    com/sun/xml/bind/jaxb-impl/2.3.1/jaxb-impl-2.3.1 \
    com/sun/xml/bind/jaxb-core/2.3.0.1/jaxb-core-2.3.0.1 \
    javax/xml/bind/jaxb-api/2.3.1/jaxb-api-2.3.1 \
    javax/activation/javax.activation-api/1.2.0/javax.activation-api-1.2.0
  do
    curl -fsSL -o ".work/sources.tmp/$(basename $p)-sources.jar" "https://repo1.maven.org/maven2/$p-sources.jar"
  done
  mv .work/sources.tmp .work/sources
  echo "sources: $(ls .work/sources | wc -l | tr -d ' ') libraries"
fi
