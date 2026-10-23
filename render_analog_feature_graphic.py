#!/usr/bin/env python3
r"""
Generates the complete Google Play Store asset suite for the Analog watch face variant (v4.8):
1. 10 round transparent analog dials in recreated_album_screenshots/ (recreated_analog_01..10)
2. 10 RGB analog dials on black in play_store_screenshots/ (play_rgb_analog_01..10)
3. 4 hero analog screenshots in play_store_screenshots/ (play_screenshot_analog_1..4)
4. 4 default 512x512 analog icons in recreated_album_screenshots/ (default_512_analog_*)
5. Master 8-watch composite: play_store_screenshots/G-Shark-Main-Analog.png (3022x1476 RGB)
6. Official Play Store Feature Graphic: play_store_screenshots/G-Shark-Feature-Graphic-Analog-1024x500.png (1024x500 RGB)
7. Copies to Downloads for immediate access.
"""

import os
import shutil
from PIL import Image

from render_fresh_playstore_assets import (
    ALBUM_DIR,
    DOWNLOADS_DIR,
    PLAY_DIR,
    compose_8_watches,
    render_dial,
    save_default_512_icons,
)

# 10 Curated Analog Configurations matching the 10-dial album structure and 8-watch showcase
ANALOG_CONFIGS = [
    # 01: Casino G-Shark — Tactical Spec-Ops (Volt Lime + Sword Theme Hands) [Case 1]
    {
        "id": "01_casino_gshark",
        "title": "Tactical Spec-Ops",
        "bg_texture": 0,       # Classic LCD
        "theme_color": 0,      # Volt Lime #BAFA08
        "logo_color": 0,       # Volt Lime #BAFA08
        "sec_color": 1,        # Volt Lime
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date 18/10/2026
        "sub_dial_mode": 0,    # 8-Segment Battery Gauge
        "tick_style": 0,       # Classic
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 1,     # Sword Theme Hands
        "top_logo": 0,         # CASINO
        "bottom_logo": 0,      # G-SHARK
        "date_str": "18/10/2026",
        "pod1_val": "100%",
        "pod2_val": "6342",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "15:22",
    },
    # 02: Critical G-Spot — Industrial Spec (Industrial Black & Silver + Precision Needle White Hands)
    {
        "id": "02_critical_gspot",
        "title": "Industrial Spec",
        "bg_texture": 17,      # Industrial Black & Silver
        "theme_color": 1,      # Bright Lime Green #39FF14
        "logo_color": 1,       # Bright Lime Green
        "sec_color": 2,        # Bright Lime Green
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sun 18/10
        "sub_dial_mode": 5,    # Dual Time SFO
        "tick_style": 6,       # Bold Tactical Wedges
        "seconds_dot": 1,      # White dot
        "analog_hands": 7,     # Precision Needle White Hands
        "top_logo": 2,         # CRITICAL
        "bottom_logo": 1,      # G-SPOT
        "date_str": "Sun 18/10",
        "pod1_val": "88%",
        "pod2_val": "7155",
        "pod3_val": ("07:22", "NYC"),
        "pod4_val": "18°",
    },
    # 03: Curious G-Snack — Arctic Recon (Urban Camo + Baton White Hands) [Case 2]
    {
        "id": "03_curious_gsnack",
        "title": "Arctic Recon",
        "bg_texture": 3,       # Urban / Arctic Camo
        "theme_color": 2,      # Shark Blue #0EDBFF
        "logo_color": 2,       # Shark Blue
        "sec_color": 3,        # Shark Blue
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sun 18/10
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 2,       # Bold Batons
        "seconds_dot": 2,      # Theme dot (Cyan)
        "analog_hands": 4,     # Baton White Hands
        "top_logo": 4,         # CURIOUS
        "bottom_logo": 2,      # G-SNACK
        "date_str": "Sun 18/10",
        "pod1_val": "94%",
        "pod2_val": "8420",
        "pod3_val": ("15:30", "SFO"),
        "pod4_val": "16°",
    },
    # 04: Creative G-Squawk — Woodland Commando (Woodland Camo + Needle Theme Hands) [Case 5]
    {
        "id": "04_creative_gsquawk",
        "title": "Woodland Commando",
        "bg_texture": 2,       # Woodland Camo
        "theme_color": 3,      # Tactical Orange #FF660A
        "logo_color": 3,       # Tactical Orange
        "sec_color": 4,        # Tactical Orange
        "time_color": 0,       # White
        "screen_texture": 4,   # Solar Moiré Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sun 18/10
        "sub_dial_mode": 15,   # Dual Time LON
        "tick_style": 2,       # Bold Batons
        "seconds_dot": 1,      # White dot
        "analog_hands": 6,     # Needle Theme Hands
        "top_logo": 5,         # CREATIVE
        "bottom_logo": 4,      # G-SQUAWK
        "date_str": "Sun 18/10",
        "pod1_val": "92%",
        "pod2_val": "7890",
        "pod3_val": ("10:11", "LON"),
        "pod4_val": "17°",
    },
    # 05: Cautious G-Snooze — Carbon Crimson (Carbon Fiber + Sword White Hands) [Case 6]
    {
        "id": "05_cautious_gsnooze",
        "title": "Carbon Crimson",
        "bg_texture": 6,       # Carbon Fiber Weave
        "theme_color": 4,      # Crimson Red #FF1E38
        "logo_color": 4,       # Crimson Red
        "sec_color": 5,        # Crimson Red
        "time_color": 0,       # White
        "screen_texture": 3,   # Solar Moiré Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date
        "sub_dial_mode": 8,    # Dual Time NYC
        "tick_style": 3,       # Chrono Fine Scale
        "seconds_dot": 1,      # White dot
        "analog_hands": 2,     # Sword White Hands
        "top_logo": 6,         # CAUTIOUS
        "bottom_logo": 3,      # G-SNOOZE
        "date_str": "18/10/2026",
        "pod1_val": "85%",
        "pod2_val": "11250",
        "pod3_val": ("06:12", "NYC"),
        "pod4_val": "14°",
    },
    # 06: Cheerful G-Sloth — Deep Blue Diver (Industrial Cyan + Baton Theme Hands) [Case 4]
    {
        "id": "06_cheerful_gsloth",
        "title": "Deep Blue Diver",
        "bg_texture": 10,      # Industrial Cyan
        "theme_color": 2,      # Shark Blue #0EDBFF
        "logo_color": 2,       # Shark Blue
        "sec_color": 3,        # Shark Blue
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 0,  # Next Event
        "sub_dial_mode": 5,    # Dual Time SFO
        "tick_style": 5,       # Theme Accent
        "seconds_dot": 1,      # White dot
        "analog_hands": 3,     # Baton Theme Hands
        "top_logo": 7,         # CHEERFUL
        "bottom_logo": 5,      # G-SLOTH
        "date_str": None,
        "pod1_val": "72%",
        "pod2_val": "9340",
        "pod3_val": ("19:13", "TYO"),
        "pod4_val": "21°",
    },
    # 07: Charming G-Spot — Inverted Executive (Tactical Mesh + Chisel White Hands + Deep Violet) [Case 3]
    {
        "id": "07_charming_gspot",
        "title": "Inverted Executive",
        "bg_texture": 9,       # Tactical Raised Mesh
        "theme_color": 8,      # Deep Violet #B040FF
        "logo_color": 6,       # Stealth White #FFFFFF
        "sec_color": 18,       # Black digits
        "time_color": 2,       # Positive Inverted LCD
        "screen_texture": 0,   # Clean
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 2,  # Sun 10/18
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 1,       # 12-Hour Indices
        "seconds_dot": 6,      # Theme Triangle
        "analog_hands": 9,     # Chisel White Hands
        "top_logo": 3,         # CHARMING
        "bottom_logo": 1,      # G-SPOT
        "date_str": "Sun 10/18",
        "pod1_val": "100%",
        "pod2_val": "5410",
        "pod3_val": ("15:30", "PAR"),
        "pod4_val": "19°",
    },
    # 08: Curious G-Snack — Urban Neon (Urban / Arctic Camo + Hot Pink Chisel Hands)
    {
        "id": "08_casino_gsnack",
        "title": "Urban Neon",
        "bg_texture": 3,       # Urban / Arctic Camo
        "theme_color": 9,      # Hot Pink #F514C8
        "logo_color": 6,       # White
        "sec_color": 10,       # Hot Pink
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date 18/10/2026
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 5,       # Theme Accent
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 8,     # Chisel Theme Hands
        "top_logo": 4,         # CURIOUS
        "bottom_logo": 2,      # G-SNACK
        "date_str": "18/10/2026",
        "pod1_val": "78%",
        "pod2_val": "6820",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "17°",
    },
    # 09: Casino G-Squawk — Desert Ranger (Desert Camo + Chisel Theme Hands) [Case 7]
    {
        "id": "09_casino_gsquawk",
        "title": "Desert Ranger",
        "bg_texture": 4,       # Desert Camo
        "theme_color": 5,      # Amber Gold #FFC400
        "logo_color": 5,       # Amber Gold
        "sec_color": 6,        # Amber Gold
        "time_color": 0,       # White
        "screen_texture": 4,   # Solar Moiré Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 4,       # Numeric 05-60
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 8,     # Chisel Theme Hands
        "top_logo": 0,         # CASINO
        "bottom_logo": 4,      # G-SQUAWK
        "date_str": "18/10/2026",
        "pod1_val": "82%",
        "pod2_val": "12180",
        "pod3_val": ("20:16", "SYD"),
        "pod4_val": "22°",
    },
    # 10: Casino G-Snooze — Zebra Ghost (Subtle Zebra Camo + Ghost Theme Hands) [Case 8]
    {
        "id": "10_casino_gsnooze",
        "title": "Zebra Ghost",
        "bg_texture": 5,       # Subtle Zebra Camo
        "theme_color": 0,      # Cyber Lime #BAFA08
        "logo_color": 0,       # Cyber Lime
        "sec_color": 1,        # Cyber Lime
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date
        "sub_dial_mode": 0,    # 8-Segment Battery Gauge
        "tick_style": 0,       # Classic
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 5,     # Ghost Theme Hands
        "top_logo": 0,         # CASINO
        "bottom_logo": 0,      # G-SHARK
        "date_str": "18/10/2026",
        "pod1_val": "85%",
        "pod2_val": "9680",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "18°",
    },
]


def main():
    print("=== 1. Generating 10 Fresh 466x466 Analog Dials ===")
    rendered_dials = {}

    for i, cfg in enumerate(ANALOG_CONFIGS):
        dial_rgba = render_dial(cfg)
        rendered_dials[cfg["id"]] = dial_rgba

        recreated_path = os.path.join(ALBUM_DIR, f"recreated_analog_{cfg['id']}.png")
        dial_rgba.save(recreated_path, optimize=True)

        bg_black = Image.new("RGBA", (466, 466), (0, 0, 0, 255))
        dial_rgb = Image.alpha_composite(bg_black, dial_rgba).convert("RGB")
        play_rgb_path = os.path.join(PLAY_DIR, f"play_rgb_analog_{cfg['id']}.png")
        dial_rgb.save(play_rgb_path, optimize=True)
        print(f"  [#{i+1:02d}] {cfg['title']} -> {recreated_path} and {play_rgb_path}")

    print("\n=== 2. Updating Analog Hero Screenshots (play_screenshot_analog_1..4) ===")
    hero_map = [
        (1, "01_casino_gshark"),
        (2, "03_curious_gsnack"),
        (3, "04_creative_gsquawk"),
        (4, "07_charming_gspot"),
    ]
    for hero_num, cfg_id in hero_map:
        dial_rgba = rendered_dials[cfg_id]
        bg_black = Image.new("RGBA", (466, 466), (0, 0, 0, 255))
        dial_rgb = Image.alpha_composite(bg_black, dial_rgba).convert("RGB")
        hero_path = os.path.join(
            PLAY_DIR, f"play_screenshot_analog_{hero_num}_{cfg_id.split('_', 1)[1]}.png"
        )
        dial_rgb.save(hero_path, optimize=True)
        print(f"  Analog Hero #{hero_num} -> {hero_path}")

    print("\n=== 3. Updating Default 512x512 Analog Icons ===")
    save_default_512_icons(ANALOG_CONFIGS[0], prefix="default_512_analog")

    print("\n=== 4. Composing 8-Watch Analog Master Graphic (G-Shark-Main-Analog.png 3022x1476) ===")
    # Preserve the 8 curated analog showcase positions:
    case_configs = [
        ANALOG_CONFIGS[0],  # Case 1: Tactical Spec-Ops (01_casino_gshark)
        ANALOG_CONFIGS[2],  # Case 2: Arctic Recon (03_curious_gsnack)
        ANALOG_CONFIGS[6],  # Case 3: Inverted Executive (07_charming_gspot)
        ANALOG_CONFIGS[5],  # Case 4: Deep Blue Diver (06_cheerful_gsloth)
        ANALOG_CONFIGS[3],  # Case 5: Woodland Commando (04_creative_gsquawk)
        ANALOG_CONFIGS[4],  # Case 6: Carbon Crimson (05_cautious_gsnooze)
        ANALOG_CONFIGS[8],  # Case 7: Desert Ranger (09_casino_gsquawk)
        ANALOG_CONFIGS[9],  # Case 8: Zebra Ghost (10_casino_gsnooze)
    ]
    dials_402 = [
        rendered_dials[cfg["id"]].resize((402, 402), Image.Resampling.LANCZOS)
        for cfg in case_configs
    ]
    main_rgb = compose_8_watches(dials_402)
    main_path = os.path.join(PLAY_DIR, "G-Shark-Main-Analog.png")
    main_rgb.save(main_path, optimize=True)
    print(f"  Saved {main_path}")

    print("\n=== 5. Downsampling to Google Play Analog Feature Graphic (1024x500) ===")
    feat_img = main_rgb.resize((1024, 500), Image.Resampling.LANCZOS)
    feat_path = os.path.join(PLAY_DIR, "G-Shark-Feature-Graphic-Analog-1024x500.png")
    feat_img.save(feat_path, optimize=True)
    print(f"  Saved {feat_path}")

    if os.path.exists(DOWNLOADS_DIR):
        shutil.copy2(main_path, os.path.join(DOWNLOADS_DIR, "G-Shark-Main-Analog.png"))
        shutil.copy2(
            feat_path,
            os.path.join(DOWNLOADS_DIR, "G-Shark-Feature-Graphic-Analog-1024x500.png"),
        )
        print(f"  Copied G-Shark-Main-Analog.png and G-Shark-Feature-Graphic-Analog-1024x500.png to {DOWNLOADS_DIR}")

    print("\n[SUCCESS] All Analog Play Store assets updated successfully for v4.8!")


if __name__ == "__main__":
    main()
