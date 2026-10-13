$ErrorActionPreference = "Stop"

$aapt2 = "C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\aapt2.exe"
$zipalign = "C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\zipalign.exe"
$apksigner = "C:\Users\bonst\AppData\Local\Android\Sdk\build-tools\35.0.0\apksigner.bat"
$androidJar = "C:\Users\bonst\AppData\Local\Android\Sdk\platforms\android-34\android.jar"
$keystore = "C:\Users\bonst\.android\debug.keystore"
$projectDir = "C:\Users\bonst\.gemini\antigravity\scratch\gshark-watchface"
$buildDir = "$projectDir\build"

if (!(Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}

Write-Host "1. Compiling resources with AAPT2..."
& $aapt2 compile --dir "$projectDir\app\src\main\res" -o "$buildDir\resources.zip"

Write-Host "2. Linking APK with AndroidManifest..."
& $aapt2 link -I $androidJar --manifest "$projectDir\app\src\main\AndroidManifest.xml" -o "$buildDir\unaligned.apk" "$buildDir\resources.zip"

Write-Host "3. Aligning APK with zipalign..."
& $zipalign -f -p 4 "$buildDir\unaligned.apk" "$buildDir\aligned.apk"

Write-Host "4. Signing APK with apksigner..."
& $apksigner sign --ks $keystore --ks-pass pass:android --key-pass pass:android --out "$buildDir\gshark-watchface.apk" "$buildDir\aligned.apk"

Write-Host "5. Installing APK to OnePlus Watch 2..."
$watchDevice = (adb devices -l | Select-String "OWWE251" | ForEach-Object { ($_ -split '\s+')[0] }) | Select-Object -First 1
if (-not $watchDevice) {
    $watchDevice = "10.10.10.148:41747"
}
Write-Host "Targeting watch device: $watchDevice"
adb -s $watchDevice install -r "$buildDir\gshark-watchface.apk"

Write-Host "6. Done!"
