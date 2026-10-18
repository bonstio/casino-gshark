import os
import shutil
import subprocess
import sys
import zipfile

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
RES_DIR = os.path.join(PROJECT_DIR, "app", "src", "main", "res")
MANIFEST = os.path.join(PROJECT_DIR, "app", "src", "main", "AndroidManifest.xml")

AAPT2 = r"C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\aapt2.exe"
ZIPALIGN = r"C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\zipalign.exe"
APKSIGNER = r"C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\apksigner.bat"
ANDROID_JAR = r"C:\Users\bonst\AppData\Local\Android\Sdk\platforms\android-34\android.jar"
KEYSTORE = os.path.join(PROJECT_DIR, "gshark-release.keystore")
KEY_ALIAS = "gshark_release"
KEY_PASS = "gsharkrelease"
BUNDLETOOL_JAR = r"C:\Users\bonst\AppData\Local\Programs\WatchFaceStudioBeta\tools\common\tools\bundletool-all-1.13.2.jar"
JARSIGNER = r"C:\Program Files\Java\jdk-18.0.1.1\bin\jarsigner.exe"

os.makedirs(BUILD_DIR, exist_ok=True)

print("=== 1. Compiling resources with AAPT2 ===")
res_zip = os.path.join(BUILD_DIR, "resources.zip")
subprocess.run([AAPT2, "compile", "--dir", RES_DIR, "-o", res_zip], check=True)

print("=== 2. Linking APK with AAPT2 ===")
unaligned_apk = os.path.join(BUILD_DIR, "unaligned.apk")
if os.path.exists(unaligned_apk):
    os.remove(unaligned_apk)
subprocess.run([AAPT2, "link", "-I", ANDROID_JAR, "--manifest", MANIFEST, "-o", unaligned_apk, res_zip], check=True)

print("=== 3. Zipaligning APK ===")
aligned_apk = os.path.join(BUILD_DIR, "aligned.apk")
if os.path.exists(aligned_apk):
    os.remove(aligned_apk)
subprocess.run([ZIPALIGN, "-f", "-p", "4", unaligned_apk, aligned_apk], check=True)

print("=== 4. Signing APK with apksigner ===")
release_apk_v = os.path.join(BUILD_DIR, "gshark-watchface-v4.7.apk")
release_apk = os.path.join(BUILD_DIR, "gshark-watchface.apk")
for p in [release_apk_v, release_apk, release_apk_v + ".idsig", release_apk + ".idsig"]:
    if os.path.exists(p):
        os.remove(p)

subprocess.run([
    APKSIGNER, "sign",
    "--ks", KEYSTORE,
    "--ks-key-alias", KEY_ALIAS,
    "--ks-pass", f"pass:{KEY_PASS}",
    "--key-pass", f"pass:{KEY_PASS}",
    "--out", release_apk_v,
    aligned_apk
], check=True)

shutil.copyfile(release_apk_v, release_apk)
if os.path.exists(release_apk_v + ".idsig"):
    shutil.copyfile(release_apk_v + ".idsig", release_apk + ".idsig")
print(f"Release APK built: {release_apk_v}")

print("=== 5. Linking proto APK for AAB ===")
proto_apk = os.path.join(BUILD_DIR, "proto.apk")
if os.path.exists(proto_apk):
    os.remove(proto_apk)
subprocess.run([AAPT2, "link", "--proto-format", "-I", ANDROID_JAR, "--manifest", MANIFEST, "-o", proto_apk, res_zip], check=True)

print("=== 6. Assembling base module zip for AAB ===")
base_module_dir = os.path.join(BUILD_DIR, "base_module")
if os.path.exists(base_module_dir):
    shutil.rmtree(base_module_dir)
os.makedirs(base_module_dir, exist_ok=True)

with zipfile.ZipFile(proto_apk, "r") as z:
    z.extractall(base_module_dir)

manifest_src = os.path.join(base_module_dir, "AndroidManifest.xml")
manifest_dst_dir = os.path.join(base_module_dir, "manifest")
os.makedirs(manifest_dst_dir, exist_ok=True)
manifest_dst = os.path.join(manifest_dst_dir, "AndroidManifest.xml")
os.rename(manifest_src, manifest_dst)

base_zip = os.path.join(BUILD_DIR, "base.zip")
if os.path.exists(base_zip):
    os.remove(base_zip)

with zipfile.ZipFile(base_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(base_module_dir):
        for file in files:
            full_path = os.path.join(root, file)
            arcname = os.path.relpath(full_path, base_module_dir)
            z.write(full_path, arcname)

print("=== 7. Building bundle with bundletool ===")
release_aab_v = os.path.join(BUILD_DIR, "gshark-watchface-v4.7.aab")
release_aab = os.path.join(BUILD_DIR, "gshark-watchface.aab")
for p in [release_aab_v, release_aab]:
    if os.path.exists(p):
        os.remove(p)

subprocess.run([
    "java", "-jar", BUNDLETOOL_JAR,
    "build-bundle",
    f"--modules={base_zip}",
    f"--output={release_aab_v}"
], check=True)

print("=== 8. Signing AAB with jarsigner ===")
subprocess.run([
    JARSIGNER,
    "-keystore", KEYSTORE,
    "-storepass", KEY_PASS,
    "-keypass", KEY_PASS,
    "-sigalg", "SHA256withRSA",
    "-digestalg", "SHA-256",
    release_aab_v,
    KEY_ALIAS
], check=True)

print("=== 9. Validating AAB with bundletool ===")
subprocess.run([
    "java", "-jar", BUNDLETOOL_JAR,
    "validate",
    f"--bundle={release_aab_v}"
], check=True)

shutil.copyfile(release_aab_v, release_aab)
print(f"Release AAB built: {release_aab_v}")

print("=== 10. Cleaning up intermediate build files ===")
for p in [unaligned_apk, aligned_apk, proto_apk, base_zip]:
    if os.path.exists(p):
        os.remove(p)
if os.path.exists(base_module_dir):
    shutil.rmtree(base_module_dir)

print("\nSUCCESS! Release artifacts ready in build/:")
print(f"  APK: {release_apk_v} ({os.path.getsize(release_apk_v):,} bytes)")
print(f"  AAB: {release_aab_v} ({os.path.getsize(release_aab_v):,} bytes)")
