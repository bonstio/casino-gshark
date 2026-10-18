#!/usr/bin/env python3
r"""
Generates the second Google Play feature graphic highlighting Analog watch face modes:
1. Master composite: play_store_screenshots/G-Shark-Main-Analog.png (3022x1476 RGB)
2. Official Play Store graphic: play_store_screenshots/G-Shark-Feature-Graphic-Analog-1024x500.png (1024x500 RGB)
3. Copies to C:\Users\bonst\Downloads\ for immediate access.
"""

import os
from PIL import Image, ImageDraw
from psd_tools import PSDImage

import generate_setting_icons as gsi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PSD_PATH = r"C:\Users\bonst\Photoshop\casino-feature.psd"
PLAY_DIR = os.path.join(BASE_DIR, "play_store_screenshots")
DOWNLOADS_DIR = r"C:\Users\bonst\Downloads"

def create_circle_mask(size=466):
    mask = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2 - 1, size * 2 - 1), fill=255)
    return mask.resize((size, size), Image.Resampling.LANCZOS)

DIAL_MASK = create_circle_mask(466)

ANALOG_CASES = [
    # Case 1: Tactical Spec-Ops (Volt Lime + Sword Theme Hands)
    {
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
    # Case 2: Arctic Recon (Urban Camo + Baton White Hands)
    {
        "title": "Arctic Recon",
        "bg_texture": 3,       # Urban / Arctic Camo
        "theme_color": 2,      # Shark Blue #0EDBFF
        "logo_color": 2,       # Shark Blue
        "sec_color": 3,        # Shark Blue
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sat 18/10
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
    # Case 3: Inverted Executive (Tactical Mesh + Chisel White Hands + Deep Violet)
    {
        "title": "Inverted Executive",
        "bg_texture": 9,       # Tactical Raised Mesh
        "theme_color": 8,      # Deep Violet #B040FF
        "logo_color": 6,       # Stealth White #FFFFFF
        "sec_color": 18,       # Black digits
        "time_color": 2,       # Positive Inverted LCD
        "screen_texture": 0,   # Clean
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 2,  # Sat 10/18
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
    # Case 4: Deep Blue Diver (Industrial Cyan + Baton Theme Hands)
    {
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
    # Case 5: Woodland Commando (Woodland Camo + Needle Theme Hands)
    {
        "title": "Woodland Commando",
        "bg_texture": 2,       # Woodland Camo
        "theme_color": 3,      # Tactical Orange #FF660A
        "logo_color": 3,       # Tactical Orange
        "sec_color": 4,        # Tactical Orange
        "time_color": 0,       # White
        "screen_texture": 4,   # Solar Moiré Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sat 18/10
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
    # Case 6: Carbon Crimson (Carbon Fiber + Sword White Hands)
    {
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
    # Case 7: Desert Ranger (Desert Camo + Chisel Theme Hands)
    {
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
    # Case 8: Zebra Ghost (Subtle Zebra Camo + Ghost Theme Hands)
    {
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

def render_analog_dial(cfg):
    dial_450 = gsi.render_watchface(
        bg_texture=cfg["bg_texture"],
        bg_border=0,
        theme_color=cfg["theme_color"],
        logo_color=cfg["logo_color"],
        sec_color=cfg["sec_color"],
        time_color=cfg["time_color"],
        screen_texture=cfg["screen_texture"],
        quad_style=cfg["quad_style"],
        bottom_style=cfg["bottom_style"],
        bottom_bay_mode=cfg["bottom_bay_mode"],
        sub_dial_mode=cfg["sub_dial_mode"],
        tick_style=cfg["tick_style"],
        seconds_dot=cfg["seconds_dot"],
        analog_hands=cfg["analog_hands"],
        top_logo=cfg["top_logo"],
        bottom_logo=cfg["bottom_logo"],
        date_str=cfg.get("date_str"),
        pod1_val=cfg.get("pod1_val", "100%"),
        pod2_val=cfg.get("pod2_val", "5328"),
        pod3_val=cfg.get("pod3_val", ("15:30", "DUB")),
        pod4_val=cfg.get("pod4_val", "15:22"),
    )
    dial_466 = dial_450.resize((466, 466), Image.Resampling.LANCZOS)
    dial_rgba = Image.new("RGBA", (466, 466), (0, 0, 0, 0))
    dial_rgba.paste(dial_466, (0, 0), DIAL_MASK)
    return dial_rgba

def main():
    print("=== 1. Rendering 8 Distinct Analog Dials ===")
    dials_402 = []
    for i, cfg in enumerate(ANALOG_CASES):
        dial = render_analog_dial(cfg)
        d_402 = dial.resize((402, 402), Image.Resampling.LANCZOS)
        dials_402.append(d_402)
        print(f"  [Case {i+1}] {cfg['title']} (hands={cfg['analog_hands']})")

    print("\n=== 2. Composing 8-Watch Analog Master Graphic (3022x1476) ===")
    psd = PSDImage.open(PSD_PATH)
    W, H = psd.size
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    
    # Base background layer
    l0 = psd[0]
    comp.alpha_composite(l0.topil(), (l0.bbox[0], l0.bbox[1]))
    
    group = psd[1]
    for idx, watch_group in enumerate(reversed(group)):
        c0 = watch_group[0]  # dial slot
        c1 = watch_group[1]  # bezel & glare overlay
        
        comp.alpha_composite(dials_402[idx], (c0.bbox[0], c0.bbox[1]))
        
        img1 = c1.topil()
        if img1:
            comp.alpha_composite(img1, (c1.bbox[0], c1.bbox[1]))

    main_rgb = comp.convert("RGB")
    main_path = os.path.join(PLAY_DIR, "G-Shark-Main-Analog.png")
    main_rgb.save(main_path, optimize=True)
    print(f"  Saved {main_path}")

    print("\n=== 3. Downsampling to Google Play Feature Graphic (1024x500) ===")
    feat_img = main_rgb.resize((1024, 500), Image.Resampling.LANCZOS)
    feat_path = os.path.join(PLAY_DIR, "G-Shark-Feature-Graphic-Analog-1024x500.png")
    feat_img.save(feat_path, optimize=True)
    print(f"  Saved {feat_path}")

    # Copy to Downloads
    dl_path = os.path.join(DOWNLOADS_DIR, "G-Shark-Feature-Graphic-Analog-1024x500.png")
    feat_img.save(dl_path, optimize=True)
    print(f"  Copied to Downloads -> {dl_path}")

    print("\n[SUCCESS] Analog feature graphic generated successfully!")

if __name__ == "__main__":
    main()
