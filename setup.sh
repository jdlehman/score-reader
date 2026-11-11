#!/bin/sh
# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# Make .work/, which ./build.sh and teavm/build.sh need: Audiveris 5.11.0's source with our patch applied, the jars
# of its release, their class path, a Temurin JDK 25, the source of the copyleft libraries, and
# TeaVM (for the browser build, teavm/build.sh).
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

# 6. TeaVM 0.16.0, which builds Audiveris for the browser (teavm/build.sh): its jars and the libraries
# its compiler uses, and the source of the classes teavm/fork/ fixes. With each file's SHA-256: the
# browser build is made from these.
if [ ! -d .work/teavm-lib ]; then
  mkdir -p .work/teavm-lib.tmp
  set -- \
    org/ow2/asm/asm/9.10.1/asm-9.10.1 ed825d10ab1399c8c0cb669e688cf0c8c82629b4c8399b58352b68e92ca10fcb \
    org/ow2/asm/asm-analysis/9.10.1/asm-analysis-9.10.1 dede75a21306b65974ecd8f87114ff6970f09fb794157a4ca09ab25c888c2bfc \
    org/ow2/asm/asm-commons/9.10.1/asm-commons-9.10.1 6d0abefb7cbf972ea16edb37ec14835372505063a45f976ab7ea889ed9497895 \
    org/ow2/asm/asm-tree/9.10.1/asm-tree-9.10.1 3dfb0d5b6a106cd40b5b250e39935fbf2f927f4477546a5369a3ac609cf0506b \
    org/ow2/asm/asm-util/9.10.1/asm-util-9.10.1 1bb99d091fba2597dc6d51193e9bbcf0d8447e7ed96bd8f0198b18152f09655c \
    com/carrotsearch/hppc/0.10.0/hppc-0.10.0 edc83b336476a2b06f7c17d09b17e98bb07678daf968c9825cc14275bdf20a26 \
    joda-time/joda-time/2.12.2/joda-time-2.12.2 8d4d807adc8e92a83913d9ccd61e634b4907c78d88f3016d06b3b3d2b4795a02 \
    com/jcraft/jzlib/1.1.3/jzlib-1.1.3 89b1360f407381bf61fde411019d8cbd009ebb10cff715f3669017a031027560 \
    org/mozilla/rhino/1.9.1/rhino-1.9.1 12dbb224cea124a5d32968722e8eb161c967bf15f3c9a795d1b05592b1147975 \
    org/teavm/teavm-classlib/0.16.0/teavm-classlib-0.16.0 329fd2a9cfb3afb453070cb97c12adb5c0ee7b0d943b357188d7dbf9c6bf3dd5 \
    org/teavm/teavm-core/0.16.0/teavm-core-0.16.0 c94539912c1b951fa741aecfcb6b4acad75c2e2360dc8859b1edd0c44175608a \
    org/teavm/teavm-extension-apis/0.16.0/teavm-extension-apis-0.16.0 9e867f3760b1c8d86cdb18ec70e429c23fd933021c8c3bb0cc0b727eac3202c0 \
    org/teavm/teavm-extension-spi/0.16.0/teavm-extension-spi-0.16.0 e280bbc31e8d26de2915954990e260871462c146418c7b901249502a1994dde5 \
    org/teavm/teavm-extension-spi-util/0.16.0/teavm-extension-spi-util-0.16.0 d94e8d4478c4186d18b657cb67654851d38b9f51d372dc7e7e54e0f3a24347c9 \
    org/teavm/teavm-interop/0.16.0/teavm-interop-0.16.0 5c8511d71ae6f6d2ca913130393b64a959303e521727b2d9c1a9b1e14519216f \
    org/teavm/teavm-jso/0.16.0/teavm-jso-0.16.0 58b337b93924106bf819c45890c7c231a0c740145afe77795f1e0f099f621d71 \
    org/teavm/teavm-jso-apis/0.16.0/teavm-jso-apis-0.16.0 32d28e39957a41404f53a14c2447d980c7b5074a92414d0972014f448a46fcb2 \
    org/teavm/teavm-jso-impl/0.16.0/teavm-jso-impl-0.16.0 12688d04e7d2d73036adacd72b74fd8fb44f10283004075fbe68706ccb223b75 \
    org/teavm/teavm-metaprogramming-api/0.16.0/teavm-metaprogramming-api-0.16.0 00f053ad35ff78312e48eebbf4e1c6cf5f7a1e759b2432ba0b60d6f111bb3bdd \
    org/teavm/teavm-metaprogramming-impl/0.16.0/teavm-metaprogramming-impl-0.16.0 616d30aa28f7b0180a61c2289b11c77bf84c715bd79f255e1e42400edb5b6d70 \
    org/teavm/teavm-platform/0.16.0/teavm-platform-0.16.0 999d369ab15aa83c17987d048ba59560759169891de7e13a5a1c2bd93dd060a8 \
    org/teavm/teavm-relocated-libs-asm/0.16.0/teavm-relocated-libs-asm-0.16.0 59deba713805038fb9ceb76f002e3ae0e9660ec9815875917f08e0a235b7b1a2 \
    org/teavm/teavm-relocated-libs-asm-analysis/0.16.0/teavm-relocated-libs-asm-analysis-0.16.0 8ce092f26dc44cffbfd6a23067b0ae43e32f9ddb29efd6e4eed93095a454b04a \
    org/teavm/teavm-relocated-libs-asm-commons/0.16.0/teavm-relocated-libs-asm-commons-0.16.0 b877abd3af4f9ae2650aa0cb3577fcbdd66a9a1a1181d545d5f1f20070ea5924 \
    org/teavm/teavm-relocated-libs-asm-tree/0.16.0/teavm-relocated-libs-asm-tree-0.16.0 e0bd21e6734b1f060c0553c66fe20292f49d146858aec1f1ecfe21f6417885f6 \
    org/teavm/teavm-relocated-libs-asm-util/0.16.0/teavm-relocated-libs-asm-util-0.16.0 c69ce1813eaa66643361b70b3f07c13ca924185280c237c832774a2f85eaf431 \
    org/teavm/teavm-relocated-libs-hppc/0.16.0/teavm-relocated-libs-hppc-0.16.0 7b82fedf747e0bf5d7a50acece86a8a684901e469165a3c5621c653128df4cd6 \
    org/teavm/teavm-relocated-libs-rhino/0.16.0/teavm-relocated-libs-rhino-0.16.0 ea776a11f0233ba9e3fd12faf81cca2101b42443d0d22084e2627898fd7ee76e \
    org/teavm/teavm-tooling/0.16.0/teavm-tooling-0.16.0 8335feb227d299bf51ba3862e84eb3a2723ff2e9840a885a7537f6454d44ee31 \
    org/teavm/teavm-classlib/0.16.0/teavm-classlib-0.16.0-sources da6f83c1436c87a9ad683b6143aaa9c172b08c3974c9a7d5741a479d0d60092e \
    org/teavm/teavm-core/0.16.0/teavm-core-0.16.0-sources 687cabf23e0d17a15be30fbc070809c2931714340aca224120fe31579f95519b \
    end
  while [ "$1" != end ]; do
    f=".work/teavm-lib.tmp/$(basename "$1").jar"
    curl -fsSL -o "$f" "https://repo1.maven.org/maven2/$1.jar"
    check "$f" "$2"
    shift 2
  done
  mv .work/teavm-lib.tmp .work/teavm-lib
  echo "teavm: $(ls .work/teavm-lib | wc -l | tr -d ' ') jars"
fi
