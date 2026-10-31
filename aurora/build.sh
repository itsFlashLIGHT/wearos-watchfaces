#!/bin/zsh
# Regenerate assets + watchface.xml, validate against WFF v2, build the APK.
# Usage: ./build.sh              -> release APK in dist/
#        ./build.sh install      -> build and install on the connected watch (adb)
#        FORCE_SCENE=rain_day ./build.sh install   -> pin one background (debugging)
set -e
cd "${0:A:h}"
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home}

PY=python3
[[ -x ../.venv/bin/python ]] && PY=../.venv/bin/python
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
$PY tools/gen_watchface.py

VALIDATOR=tools/bin/wff-validator.jar
if [[ -f $VALIDATOR ]]; then
  "$JAVA_HOME/bin/java" -jar $VALIDATOR 2 watchface/src/main/res/raw/watchface.xml
else
  echo "! $VALIDATOR not found - skipping WFF validation (see README)"
fi

./gradlew -q --console=plain assembleRelease
VERSION=$(grep -m1 versionName watchface/build.gradle.kts | sed -E 's/.*"(.*)".*/\1/')
mkdir -p dist
APK=dist/Aurora-$VERSION.apk
cp watchface/build/outputs/apk/release/watchface-release.apk "$APK"
echo "APK: $APK"

if [[ "$1" == "install" ]]; then
  # The watch may be listed several times (IP + mDNS); pick the first online one.
  SERIAL=${ANDROID_SERIAL:-$(adb devices | awk 'NR > 1 && $2 == "device" { print $1; exit }')}
  [[ -z "$SERIAL" ]] && { echo "No watch connected (adb devices)"; exit 1; }
  adb -s "$SERIAL" install -r "$APK"
fi
