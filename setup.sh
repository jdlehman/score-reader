#!/bin/sh
# Make .work/, which ./build.sh needs: Audiveris 5.11.0's source with our patch applied, the jars
# of its release, their class path, and a Temurin JDK 25.
#   ./setup.sh   (on macOS or Linux; needs git and curl, and dpkg-deb on Linux)
# Each part is skipped if it is already there.
set -e
cd "$(dirname "$0")"
V=5.11.0
mkdir -p .work

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
      curl -fsSL -o "$tmp/a.dmg" "$release/Audiveris-$V-macosx-$(uname -m | sed 's/aarch64/arm64/').dmg"
      # the image shows Audiveris's licence (the AGPL) and asks to agree before it opens
      yes | PAGER=cat hdiutil attach -nobrowse -readonly -mountpoint "$tmp/mnt" "$tmp/a.dmg" > /dev/null
      app="$tmp/mnt/Audiveris.app/Contents/app"
      ;;
    Linux)
      curl -fsSL -o "$tmp/a.deb" "$release/Audiveris-$V-ubuntu24.04-x86_64.deb"
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
