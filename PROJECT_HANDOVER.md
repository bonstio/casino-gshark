# G-Shock GA-100 "GShark" Wear OS Watch Face — Project Handover & Architecture

> **Purpose:** Master reference documentation for continuing development, design iteration, and deployment of the G-Shock GA-100 tactical watchface across different development environments or AI assistant sessions.

---

## 1. Project Overview & Target Platform

- **App Name:** `GShark Watchface`
- **Package ID:** `com.gshark.watchface`
- **Target OS:** Wear OS 4+ / Wear OS 5+ (Android 13 / 14 / 15 API 33+)
- **Standard:** **Watch Face Format (WFF) Version 1** (`res/raw/watchface.xml`) — Pure declarative, battery-efficient, Android-runtime-independent watchface standard.
- **Physical Verification Device:** OnePlus Watch 2 (`H621133000052E960019`), 466×466 px round AMOLED display.
- **Virtual Coordinate Canvas:** 450×450 normalized square Wear OS canvas with circular clip mask (`cx=225, cy=225, r=225`).

---

## 2. Repository Layout & Artifact Hierarchy

```text
gshark-watchface/
├── app/
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml          # Declares Watch Face service & WFF raw resource
│           └── res/
│               ├── drawable/                # Generated 450x450 backgrounds, split textures, sub-dial assets
│               ├── font/
│               │   └── digital7.ttf         # High-precision authentic 7-segment digital LCD font
│               ├── raw/
│               │   └── watchface.xml        # Master declarative Watch Face Format layout & logic
│               └── values/
│                   ├── colors.xml           # Color palette definitions
│                   └── strings.xml          # Configuration menus, labels, and setting options
├── apply_user_shadows.py                    # Procedural generator for backgrounds, shadows, and textures
├── build_and_install.ps1                    # Fast standalone AAPT2 + zipalign + apksigner build script
├── build/
│   └── gshark-watchface.apk                 # Signed, ready-to-run release APK
└── exported_backgrounds_for_photoshop/     # Clean base assets for external graphics editors
```

---

## 3. Display Architecture & Geometry

### 3.1. Canvas & Chambers Coordinate Reference (450×450 Canvas)

| Chamber / Component | X Range | Y Range | Dimensions (W×H) | Visual Description / Alignment |
| :--- | :--- | :--- | :--- | :--- |
| **Outer Bezel & Track** | `0 .. 450` | `0 .. 450` | `450×450` | Outer tick ring (`r=210..220`), dial track, and bezel flange |
| **Upper Quad Pod 1** | `72 .. 138` | `90 .. 168` | `66×78` (cx=105) | Slot 1: Battery / Weather (`SHORT_TEXT`, `SMALL_IMAGE`) |
| **Upper Quad Pod 2** | `152 .. 218` | `90 .. 168` | `66×78` (cx=185) | Slot 2: Steps / Heart Rate (`SHORT_TEXT`, `SMALL_IMAGE`) |
| **Upper Quad Pod 3** | `232 .. 298` | `90 .. 168` | `66×78` (cx=265) | Slot 3: Date / Calendar (`SHORT_TEXT`, `SMALL_IMAGE`) |
| **Upper Quad Pod 4** | `312 .. 378` | `90 .. 168` | `66×78` (cx=345) | Slot 4: Sunrise / World Clock (`SHORT_TEXT`, `SMALL_IMAGE`) |
| **Main Clock Chamber** | `70 .. 380` | `178 .. 284` | `310×106` | Lower-right corner curved concentrically around sub-dial |
| **Time Readout (HH:mm)** | `82 .. 321` | `151 .. 277` | `239×126` | Anchored top-right at `(321, 195)`, `size="120"`, `digital7.ttf` |
| **Seconds Readout (ss)** | `332 .. 374` | `206 .. 248` | `42×42` | Moved down 20px, left 2px, 20% larger (`size="43"`) |
| **Sub-Dial Housing** | `302 .. 402` | `273 .. 373` | `100×100` (scx=352, scy=323) | 30% larger GA-100 housing (`r_outer=49.4, r_inner=39.65`) |
| **Lower Complication (Slot 5)** | `70 .. 305` | `302 .. 358` | `235×56` | Right edge curves concentrically around sub-dial at `gap_dist=9.6` |

### 3.2. Sub-Dial Concentric Cutout Geometry (Option B)

Both the **Main Clock Chamber** lower-right corner and the **Lower Slot 5 Complication** right edge curve smoothly around the Sub-Dial at an exact distance of `gap_dist = 9.6px`:
$$\text{Cutout Radius } r_{\text{cut}} = r_{\text{outer}} + \text{gap\_dist} = 49.4 + 9.6 = 59.0\,\text{px}$$
- **SDF Filleting:** Smooth rounded transition fillets (`fillet_r = 16px` at 2x supersampling) ensure organic G-Shock molded resin aesthetics rather than hard geometric intersections.

---

## 4. Sub-Dial Dual Modes (`SubDialBattery` vs `SubDialAnalogDualTime`)

The circular Sub-Dial operates in two distinct, user-configurable modes controlled in `watchface.xml`:

1. **8-Segment Battery Gauge Mode (`SubDialBattery`):**
   - 8 individual pie wedges (`subdial_seg_1.png` .. `subdial_seg_8.png`, `45°` arc each, `3.5°` gap).
   - Tints dynamically with `[CONFIGURATION.themeColor.0]`.
   - Ghost background (`subdial_seg_ghost.png`) with dimmed segments for depleted charge.
   - Central battery hub cap (`subdial_batt_hub.png`) with crisp molded battery outline.

2. **34-Timezone Analog Dual-Time Mode (`SubDialAnalogDualTime`):**
   - 12-hour dual-time analog clock with continuous hour and minute hands (`subdial_hand_hour.png`, `subdial_hand_min.png`).
   - Analog ticks (`subdial_analog_ticks.png` in dark mode, `subdial_analog_ticks_black.png` in positive LCD mode).
   - 34 selectable international timezones (UTC, LON, PAR, NYC, LAX, TYO, HKG, DXB, etc.) with timezone city code badge text.
   - Central pivot cap (`subdial_analog_cap.png`).

---

## 5. Procedural Asset Generation Pipeline (`apply_user_shadows.py`)

All visual textures, backgrounds, shadows, and sub-dial components are procedurally synthesized using NumPy, SciPy, and Pillow in `apply_user_shadows.py`:

1. **Normal-Mapped 3D Micro-Waffle Surface (`bg_lcd_tactical_mesh.png`):**
   - Generates heightmap $Z(x, y)$ using Chebyshev distance metric across 4.5px pitch grid.
   - Computes analytical surface normal gradients:
     $$\mathbf{N} = \frac{(-\text{scale} \cdot \frac{\partial Z}{\partial x}, -\text{scale} \cdot \frac{\partial Z}{\partial y}, 1)}{\|\mathbf{N}\|}$$
   - Evaluates Blinn-Phong specular highlight and directional diffuse shading with ambient occlusion ($AO$).

2. **Directional Inner Shadows:**
   - Light source positioned at the upper-right ($\Delta x = -4, \Delta y = +5$).
   - Blurs an inverted SDF chamber mask to generate realistic recessed depth along the top and right chamber walls.

3. **Decoupled Main vs Complication Textures:**
   - Textures are partitioned so that the Main Clock chamber (`310×106` at `y=178`) and the Complication chambers (`310×268` at `y=90`, masking rows 78..212) can be styled independently.
   - Circular `100×100` sub-dial textures (`tex_subdial_*`) match the active screen texture when the sub-dial is set to an analog clock.

---

## 6. User Configuration Options (Rationalized Order)

Configured in `res/values/strings.xml` and exposed in the Wear OS companion app and on-watch customize screen:

1. **`bgStyle` (Main Background):** 8 Tactical finishes:
   - `0`: Classic LCD (Subtle scanline grid)
   - `1`: Matte Black (Stealth blackout)
   - `2`: Woodland Camo (Tactical green/brown/black splotches)
   - `3`: Urban Arctic Camo (High-contrast grey/slate/white geometric camouflage)
   - `4`: Carbon Fiber (2x2 twill weave)
   - `5`: Gloss Black (Top-lit reflective sheen)
   - `6`: Tactical Grid (Cross-hatch grid lines)
   - `7`: Tactical Raised Mesh (Photo-realistic normal-mapped molded waffle)

2. **`timeColor` (Time Display / LCD Polarity):**
   - `0`: Dark LCD (Bright white digits on dark background)
   - `1`: Positive LCD (Black tactical digits on inverted silver/white LCD overlay)

3. **`quadStyle` (Complications & Sub-Dial):**
   - `0`: Follow Main Screen (Inherits screen texture and LCD polarity)
   - `1`: Classic Dark (Keeps complications and sub-dial in classic dark styling with white text)

4. **`bezelTrack` (Outer Bezel Track):**
   - `0`: Classic Minute Track (Default 60-tick track)
   - `1`: 12-Hour Indices Only (Minimalist hour batons)
   - `2`: Bold Tactical Batons (Heavy lume batons + double 12-o'clock)
   - `3`: Chronograph Fine Scale (180-tick 1/3-second track)
   - `4`: Numeric 05-60 Track (Numerals at 5-minute intervals)
   - `5`: Theme Accent Ticks (Dynamic tinting with `themeColor`)
   - `6`: None / Stealth

5. **`themeColor` (Theme Color):**
   - Tactical Amber, Crimson Red, Olive Drab, Navy Blue, Stealth Gray, Cyber Teal, Neon Lime, Pure White, Sunset Orange, Desert Tan.

---

## 7. Fast Build & Deployment Toolchain (`build_and_install.ps1`)

To iterate rapidly without Gradle build overhead:

```powershell
# 1. Regenerate procedural assets if geometry or textures changed:
python apply_user_shadows.py

# 2. Build, align, sign, and install directly to connected watch:
.\build_and_install.ps1
```

The script automatically:
1. Calls Android SDK `aapt2 compile` on `app/src/main/res/`.
2. Calls `aapt2 link` with `AndroidManifest.xml` targeting `android-34`.
3. Calls `zipalign -p -f -v 4`.
4. Calls `apksigner` with `debug.keystore`.
5. Calls `adb install -r -d` targeting the connected Wear OS device.

---

## 8. Current State & Recent Changes Completed

- **Quad Complications:**
  - Narrowed to `66px` wide and increased to `78px` tall (`x=72, 152, 232, 312`, `y=90..168`).
  - Shifted all internal contents down `2px` (`y=6→8`, `y=44→46`, `y=60→62`, `y=14→16`).
  - Verified exact horizontal centering across all 4 pods.
- **Sub-Dial:**
  - Enlarged 30% (`r_outer=49.4, r_inner=39.65`, `100×100` centered at `352, 323`).
  - Implemented Option B concentric cutouts on Main Time container and Lower Slot 5.
- **Clock Layout:**
  - `HH:mm` shifted right `11px`, increased height `4px` (`size="120"` anchored top-right at `321, 195`).
  - `Seconds` moved down `20px`, left `2px`, 20% larger (`size="43"` at `332, 206`).
- **Texture Splitting & Inversion Calibration:**
  - Distinct Honeycomb Light / Dark and Solar Moiré Light / Dark contrast curves.
  - Complication textures decoupled from Main Clock texture.
