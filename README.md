# 🦈 CASINO G-SHARK 200M — Wear OS Watch Face

A rugged, tactical digital watch face inspired by the **Casio G-SQUAD GBD-200** Memory-in-Pixel (MIP) display, reimagined for **round smartwatches** (Samsung Galaxy Watch 4 / 5 / 6 / 7 / Ultra, Google Pixel Watch 1 / 2 / 3, and all Wear OS 4+ devices).

Branded with custom **CASINO** and **G-SHARK** tactical markings.

---

## 🧭 Project Architecture & Samsung Watch Face Studio (.wfs)

### 1. What is the `.wfs` format?
Samsung Watch Face Studio (WFS) uses `.wfs` files as project containers (internally a zipped bundle containing `project.json` and assets). 
However, **Watch Face Format (WFF)** is the open, declarative XML engine created jointly by Google and Samsung for all modern Wear OS 4+ devices. 

* When Watch Face Studio exports or builds an APK/AAB, it outputs this exact declarative **WFF XML** format.
* Google Play requires all modern Wear OS watch faces to use the **Watch Face Format (WFF)** with `hasCode="false"`.

### 2. Features Included in this Watch Face
- **Tactical Armor Bezel**: Industrial textured bezel with 4 titanium corner screws, "CASINO" 12 o'clock branding, "G-SHARK" 6 o'clock accent, and etched button navigation labels (`ADJUST`, `MODE`, `START`, `RESET`).
- **GBD-200 Sub-panel Layout**: Inverted high-contrast MIP LCD layout with crisp geometric partition grids.
- **Top Header Status**: Day of week (`[DAY_OF_WEEK_S]`), date (`[MONTH].[DAY]`), `WR 20BAR`, `BLUETOOTH`, and battery readout (`[BATTERY_PERCENT]%`).
- **Battery Arc Gauge**: Top curved arc showing real-time battery percentage dynamically.
- **Giant Time Module**: Ultra-bold high-contrast digital hours and minutes (`HH:mm`), with a right-aligned recessed seconds box (`ss`), mode badge, and 24H indicator.
- **Lower Fitness Module**: Step count readout (`[STEP_COUNT]`), `GOAL 10,000` status, and an animated step progress arc.
- **Complication Slot**: Customizable bottom slot supporting short text complications (heart rate, weather, world clock, etc.).
- **Ambient Mode (Always-On Display)**: Energy-conserving AOD layout with pure black background, decorative screws hidden, seconds stopped, and low pixel ratio (<15% OPR) to prevent OLED burn-in.
- **User Color Palettes**:
  - `0`: Stealth Monochrome White
  - `1`: Volt Lime (Signature G-Squad neon)
  - `2`: Ocean Shark Cyan
  - `3`: Tactical Orange

---

## 🛠️ How to Build & Install via Android Studio / Gradle

### Requirements
- Android Studio Hedgehog (2023.1.1) or newer
- Android SDK 34 or 35
- Wear OS 4+ device or emulator (Galaxy Watch 4+, Pixel Watch)

### Build Command
Run from this directory:
```bash
./gradlew assembleDebug
```
The installable APK will be output to:
`app/build/outputs/apk/debug/app-debug.apk`

### Install to your Watch over Wi-Fi / ADB:
1. On your watch, go to **Settings > Developer options > Wireless debugging**.
2. Note the IP address and port (e.g. `192.168.1.150:5555`).
3. In your terminal:
   ```bash
   adb connect 192.168.1.150:5555
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```
4. Long-press the watch screen, tap **Add watch face**, and select **CASINO G-SHARK 200M**!

---

## 🎨 How to Replicate in Samsung Watch Face Studio (GUI)

If you prefer editing visually inside **Samsung Watch Face Studio**:
1. Open **Watch Face Studio** and create a new project with **450 x 450** resolution.
2. **Bezel Layer**:
   - Add a circular shape at (0, 0, 450, 450) with color `#131518`.
   - Add Text: `C A S I N O` at top (y=16) and `G - S H A R K` at bottom (y=414).
3. **Digital Clock**:
   - Add Component > **Digital Clock**. Set time format to `HH:mm`, font size `98`, bold, color `#FFFFFF`.
   - Add a secondary Digital Clock at (312, 156) for seconds with format `ss`, color set to your accent color (e.g. Lime `#D2F800`).
4. **Header Cards**:
   - Add Text with tag `[DAY_OF_WEEK_S]` on top left.
   - Add Text with tag `[MONTH].[DAY]` on top right.
   - Add Text with tag `BAT [BATT_PER]%` in top center.
5. **Step Counter**:
   - Add Text with tag `[SC]` (or `[STEP_COUNT]`) in the lower card.
   - Add a circular Progress Bar linked to `[SC_PER]` (Step count percent).
6. **Save as `.wfs`**:
   - Click **File > Save** to save your `.wfs` project.
   - Click **Run on Device** or **Build** to generate the signed APK.
