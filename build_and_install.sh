#!/usr/bin/env bash
set -euo pipefail

SDK_DIR="${ANDROID_HOME:-$HOME/Android/Sdk}"
BUILD_TOOLS="$SDK_DIR/build-tools/36.0.0"
AAPT2="$BUILD_TOOLS/aapt2"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"
ANDROID_JAR="$SDK_DIR/platforms/android-37.0/android.jar"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYSTORE="${KEYSTORE:-$PROJECT_DIR/gshark-release.keystore}"
KEY_ALIAS="${KEY_ALIAS:-gshark_release}"
KEY_PASS="${KEY_PASS:-gsharkrelease}"
if [[ ! -f "$KEYSTORE" ]]; then
  KEYSTORE="$HOME/.android/debug.keystore"
  KEY_ALIAS="androiddebugkey"
  KEY_PASS="android"
fi
BUNDLETOOL_JAR="${BUNDLETOOL_JAR:-$HOME/.local/share/bundletool/bundletool-all.jar}"
BUILD_DIR="$PROJECT_DIR/build"

mkdir -p "$BUILD_DIR"

echo "0. Generating Pixel Watch variant (watchface_pixel.xml with bgBorder defaultValue=0 and natural 1..16 UserConfigurations order)..."
python3 - "$PROJECT_DIR/app/src/main/res/raw/watchface.xml" "$PROJECT_DIR/app/src/main/res/raw/watchface_pixel.xml" <<'PYEOF'
import re, sys

src_path, dst_path = sys.argv[1], sys.argv[2]
with open(src_path, "r", encoding="utf-8") as f:
    xml = f.read()

# 1. Set bgBorder defaultValue="0" (Bordered) on Pixel Watches
xml = xml.replace(
    '<ListConfiguration id="bgBorder" displayName="bg_border_label" defaultValue="1" icon="ic_cfg_bgborder_1">',
    '<ListConfiguration id="bgBorder" displayName="bg_border_label" defaultValue="0" icon="ic_cfg_bgborder_0">',
)

# 1b. Prioritize Google Clock NextAlarmProviderService over Oppo AlarmProviderService on Pixel Watches
xml = xml.replace(
    'primaryProvider="com.heytap.wearable.clock/com.heytap.wearable.alarm.complication.AlarmProviderService"\n                primaryProviderType="SHORT_TEXT"\n                secondaryProvider="com.google.android.deskclock/com.google.android.deskclock.complications.NextAlarmProviderService"',
    'primaryProvider="com.google.android.deskclock/com.google.android.deskclock.complications.NextAlarmProviderService"\n                primaryProviderType="SHORT_TEXT"\n                secondaryProvider="com.heytap.wearable.clock/com.heytap.wearable.alarm.complication.AlarmProviderService"',
)

# 2. Place UserConfigurations in natural 1..16 order for Pixel Watch EditorPagesState.kt
uc_match = re.search(r"(<UserConfigurations>\s*)(.*?)(\s*</UserConfigurations>)", xml, re.DOTALL)
if uc_match:
    block_pattern = re.compile(
        r"(?:<!--[^>]*-->\s*)*<(?:ListConfiguration|ColorConfiguration|BooleanConfiguration)\b[^>]*>.*?</(?:ListConfiguration|ColorConfiguration|BooleanConfiguration)>",
        re.DOTALL,
    )
    blocks = block_pattern.findall(uc_match.group(2))
    desired_order = [
        "bgTexture", "bgBorder", "themeColor", "logoColor", "secColor",
        "timeColor", "screenTexture", "quadStyle", "bottomStyle", "bottomBayMode",
        "subDialMode", "tickStyle", "secondsDot", "analogHands", "topLogo", "bottomLogo",
    ]
    by_id = {}
    for b in blocks:
        m = re.search(r'\bid="([^"]+)"', b)
        if m:
            by_id[m.group(1)] = b
    if all(k in by_id for k in desired_order):
        reordered = "\n\n        ".join(by_id[k] for k in desired_order)
        xml = xml[:uc_match.start()] + uc_match.group(1) + reordered + uc_match.group(3) + xml[uc_match.end():]

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(xml)
PYEOF

echo "1. Compiling resources with AAPT2..."
"$AAPT2" compile --dir "$PROJECT_DIR/app/src/main/res" -o "$BUILD_DIR/resources.zip"

echo "2. Linking APK with AndroidManifest..."
"$AAPT2" link -I "$ANDROID_JAR" --manifest "$PROJECT_DIR/app/src/main/AndroidManifest.xml" -o "$BUILD_DIR/unaligned.apk" "$BUILD_DIR/resources.zip"

echo "3. Aligning APK with zipalign..."
"$ZIPALIGN" -f -p 4 "$BUILD_DIR/unaligned.apk" "$BUILD_DIR/aligned.apk"

echo "4. Signing APK with apksigner..."
"$APKSIGNER" sign --ks "$KEYSTORE" --ks-key-alias "$KEY_ALIAS" --ks-pass "pass:$KEY_PASS" --key-pass "pass:$KEY_PASS" --out "$BUILD_DIR/gshark-watchface.apk" "$BUILD_DIR/aligned.apk"

if [[ -f "$BUNDLETOOL_JAR" ]]; then
  echo "5. Building and signing AAB with bundletool and jarsigner..."
  rm -rf "$BUILD_DIR/base_module" "$BUILD_DIR/proto.apk" "$BUILD_DIR/base.zip" "$BUILD_DIR/gshark-watchface.aab"
  "$AAPT2" link --proto-format -I "$ANDROID_JAR" --manifest "$PROJECT_DIR/app/src/main/AndroidManifest.xml" -o "$BUILD_DIR/proto.apk" "$BUILD_DIR/resources.zip"
  mkdir -p "$BUILD_DIR/base_module/manifest"
  unzip -q "$BUILD_DIR/proto.apk" -d "$BUILD_DIR/base_module"
  mv "$BUILD_DIR/base_module/AndroidManifest.xml" "$BUILD_DIR/base_module/manifest/AndroidManifest.xml"
  (cd "$BUILD_DIR/base_module" && zip -q -r "$BUILD_DIR/base.zip" .)
  java -jar "$BUNDLETOOL_JAR" build-bundle --modules="$BUILD_DIR/base.zip" --output="$BUILD_DIR/gshark-watchface.aab"
  jarsigner -keystore "$KEYSTORE" -storepass "$KEY_PASS" -keypass "$KEY_PASS" -sigalg SHA256withRSA -digestalg SHA-256 "$BUILD_DIR/gshark-watchface.aab" "$KEY_ALIAS" >/dev/null
  java -jar "$BUNDLETOOL_JAR" validate --bundle="$BUILD_DIR/gshark-watchface.aab"
fi

rm -rf "$BUILD_DIR/unaligned.apk" "$BUILD_DIR/aligned.apk" "$BUILD_DIR/proto.apk" "$BUILD_DIR/base.zip" "$BUILD_DIR/base_module" "$BUILD_DIR/resources.zip"

if [[ "${1:-}" == "--build-only" ]]; then
  echo "6. Build complete (--build-only): $BUILD_DIR/gshark-watchface.apk & $BUILD_DIR/gshark-watchface.aab"
  exit 0
fi

WATCH_DEVICE="${1:-${ANDROID_SERIAL:-5C161WRDTL3624}}"
echo "6. Installing APK to $WATCH_DEVICE..."
if ! adb -s "$WATCH_DEVICE" install -r -d "$BUILD_DIR/gshark-watchface.apk"; then
  echo "Signature mismatch detected; uninstalling previous build and reinstalling..."
  adb -s "$WATCH_DEVICE" uninstall net.bonstio.watchface.gshark || true
  adb -s "$WATCH_DEVICE" install "$BUILD_DIR/gshark-watchface.apk"
fi

echo "7. Done!"
