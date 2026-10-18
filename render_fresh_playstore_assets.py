#!/usr/bin/env python3
"""
Renders fresh, pixel-perfect Play Store screenshots and promo graphics for v4.7:
1. 10 round transparent dials in recreated_album_screenshots/ (recreated_01..10)
2. 10 RGB dials on black in play_store_screenshots/ (play_rgb_01..10)
3. 4 hero screenshots in play_store_screenshots/ (play_screenshot_1..4)
4. High-res 8-watch composite in play_store_screenshots/G-Shark-Main.png (3022x1476)
5. Google Play feature graphic in play_store_screenshots/G-Shark-Feature-Graphic-1024x500.png (1024x500)
"""

import os
from PIL import Image, ImageDraw
from psd_tools import PSDImage

import generate_setting_icons as gsi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PSD_PATH = r"C:\Users\bonst\Photoshop\casino-feature.psd"
PLAY_DIR = os.path.join(BASE_DIR, "play_store_screenshots")
ALBUM_DIR = os.path.join(BASE_DIR, "recreated_album_screenshots")
os.makedirs(PLAY_DIR, exist_ok=True)
os.makedirs(ALBUM_DIR, exist_ok=True)

# Generate smooth circular alpha mask for 466x466 dial
def create_circle_mask(size=466):
    mask = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2 - 1, size * 2 - 1), fill=255)
    return mask.resize((size, size), Image.Resampling.LANCZOS)

DIAL_MASK = create_circle_mask(466)

# 10 Curated Configurations representing the best of Casino G-Shark v4.7
CONFIGS = [
    # 01: Casino G-Shark (Volt Lime Default, Battery Gauge, Hex Dark)
    {
        "id": "01_casino_gshark",
        "bg_texture": 0,       # Classic LCD
        "theme_color": 0,      # Volt Lime #BAFA08
        "logo_color": 0,       # Volt Lime #BAFA08
        "sec_color": 1,        # Volt Lime
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date
        "sub_dial_mode": 0,    # 8-Segment Battery Gauge
        "tick_style": 0,       # Classic
        "seconds_dot": 0,
        "analog_hands": 0,
        "top_logo": 0,         # CASINO
        "bottom_logo": 0,      # G-SHARK
        "time_str": "10:08",
        "sec_str": "42",
        "date_str": "18/10/2026",
        "pod1_val": "100%",
        "pod2_val": "6342",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "15:22",
    },
    # 02: Critical G-Spot (Bright Lime Green, Dual-Time SFO, Hex Light)
    {
        "id": "02_critical_gspot",
        "bg_texture": 0,       # Classic LCD
        "theme_color": 1,      # Bright Lime Green #39FF14
        "logo_color": 1,       # Bright Lime Green
        "sec_color": 2,        # Bright Lime Green
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sat 18/10
        "sub_dial_mode": 5,    # Dual Time SFO
        "tick_style": 0,       # Classic
        "seconds_dot": 1,      # White dot
        "analog_hands": 0,
        "top_logo": 2,         # CRITICAL
        "bottom_logo": 1,      # G-SPOT
        "time_str": "10:09",
        "sec_str": "06",
        "date_str": "Sun 18/10",
        "pod1_val": "88%",
        "pod2_val": "7155",
        "pod3_val": ("07:22", "NYC"),
        "pod4_val": "18°",
    },
    # 03: Curious G-Snack (Stealth Matte Black + Shark Blue, Dual-Time SFO)
    {
        "id": "03_curious_gsnack",
        "bg_texture": 1,       # Matte Black
        "theme_color": 2,      # Shark Blue #0EDBFF
        "logo_color": 2,       # Shark Blue
        "sec_color": 3,        # Shark Blue
        "time_color": 0,       # White
        "screen_texture": 1,   # Hex Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sat 18/10
        "sub_dial_mode": 5,    # Dual Time SFO
        "tick_style": 2,       # Bold Batons
        "seconds_dot": 2,      # Theme dot (Cyan)
        "analog_hands": 0,
        "top_logo": 4,         # CURIOUS
        "bottom_logo": 2,      # G-SNACK
        "time_str": "10:10",
        "sec_str": "19",
        "date_str": "Sun 18/10",
        "pod1_val": "94%",
        "pod2_val": "8420",
        "pod3_val": ("15:30", "SFO"),
        "pod4_val": "16°",
    },
    # 04: Creative G-Squawk (Woodland Camo + Tactical Orange, Solar Moiré)
    {
        "id": "04_creative_gsquawk",
        "bg_texture": 2,       # Woodland Camo (Refreshed GitHub palette)
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
        "analog_hands": 0,
        "top_logo": 5,         # CREATIVE
        "bottom_logo": 4,      # G-SQUAWK
        "time_str": "10:11",
        "sec_str": "41",
        "date_str": "Sun 18/10",
        "pod1_val": "92%",
        "pod2_val": "7890",
        "pod3_val": ("10:11", "LON"),
        "pod4_val": "17°",
    },
    # 05: Cautious G-Snooze (Matte Black + Crimson Red, Solar Moiré Light)
    {
        "id": "05_cautious_gsnooze",
        "bg_texture": 1,       # Matte Black
        "theme_color": 4,      # Crimson Red #FF1E38
        "logo_color": 4,       # Crimson Red
        "sec_color": 5,        # Crimson Red
        "time_color": 0,       # White
        "screen_texture": 3,   # Solar Moiré Light
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 3,  # Sat 18/10
        "sub_dial_mode": 8,    # Dual Time NYC
        "tick_style": 3,       # Chrono Fine Scale
        "seconds_dot": 1,      # White dot
        "analog_hands": 0,
        "top_logo": 6,         # CAUTIOUS
        "bottom_logo": 3,      # G-SNOOZE
        "time_str": "10:12",
        "sec_str": "48",
        "date_str": "Sun 18/10",
        "pod1_val": "85%",
        "pod2_val": "11250",
        "pod3_val": ("06:12", "NYC"),
        "pod4_val": "14°",
    },
    # 06: Cheerful G-Sloth (Tactical Mesh + Next Event Calendar + Titanium Silver)
    {
        "id": "06_cheerful_gsloth",
        "bg_texture": 9,       # Tactical Raised Mesh
        "theme_color": 15,     # Titanium Silver #CED8E2
        "logo_color": 6,       # Stealth White #FFFFFF
        "sec_color": 0,        # Match clock
        "time_color": 0,       # White
        "screen_texture": 0,   # Clean
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 0,  # Next Event: 15:00 Coffee / Conf Room B
        "sub_dial_mode": 0,    # 8-Segment Battery Gauge
        "tick_style": 0,       # Classic
        "seconds_dot": 1,      # White dot
        "analog_hands": 0,
        "top_logo": 7,         # CHEERFUL
        "bottom_logo": 5,      # G-SLOTH
        "time_str": "10:13",
        "sec_str": "43",
        "date_str": None,      # Uses bottom_bay_mode=0
        "pod1_val": "72%",
        "pod2_val": "9340",
        "pod3_val": ("19:13", "TYO"),
        "pod4_val": "21°",
    },
    # 07: Charming G-Spot (Positive Inverted LCD + Deep Violet Seconds Wheel)
    {
        "id": "07_charming_gspot",
        "bg_texture": 9,       # Tactical Raised Mesh
        "theme_color": 8,      # Deep Violet #B040FF
        "logo_color": 6,       # Stealth White #FFFFFF
        "sec_color": 18,       # Black digits
        "time_color": 2,       # Positive Inverted LCD (Black digits on Light screen)
        "screen_texture": 0,   # Clean
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 2,  # Sat 10/18
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 1,       # 12-Hour Indices
        "seconds_dot": 5,      # Triangle white
        "analog_hands": 0,
        "top_logo": 3,         # CHARMING
        "bottom_logo": 1,      # G-SPOT
        "time_str": "10:14",
        "sec_str": "01",
        "date_str": "Sun 10/18",
        "pod1_val": "100%",
        "pod2_val": "5410",
        "pod3_val": ("15:30", "PAR"),
        "pod4_val": "19°",
    },
    # 08: Curious G-Snack (Urban / Arctic Camo + Hot Pink)
    {
        "id": "08_casino_gsnack",
        "bg_texture": 3,       # Urban / Arctic Camo (Refreshed GitHub palette)
        "theme_color": 9,      # Hot Pink #F514C8
        "logo_color": 6,       # White
        "sec_color": 9,        # Hot Pink
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date 18/10/2026
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 5,       # Theme Accent
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 0,
        "top_logo": 4,         # CURIOUS
        "bottom_logo": 2,      # G-SNACK
        "time_str": "10:15",
        "sec_str": "06",
        "date_str": "18/10/2026",
        "pod1_val": "78%",
        "pod2_val": "6820",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "17°",
    },
    # 09: Casino G-Squawk (Desert Camo + Tactical Orange / Amber Gold)
    {
        "id": "09_casino_gsquawk",
        "bg_texture": 4,       # Desert Camo (Refreshed GitHub palette)
        "theme_color": 3,      # Tactical Orange
        "logo_color": 6,       # White
        "sec_color": 4,        # Tactical Orange
        "time_color": 0,       # White
        "screen_texture": 4,   # Solar Moiré Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date 18/10/2026
        "sub_dial_mode": 1,    # 12-Segment Seconds Wheel
        "tick_style": 4,       # Numeric 05-60
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 0,
        "top_logo": 0,         # CASINO
        "bottom_logo": 4,      # G-SQUAWK
        "time_str": "10:16",
        "sec_str": "22",
        "date_str": "18/10/2026",
        "pod1_val": "82%",
        "pod2_val": "12180",
        "pod3_val": ("20:16", "SYD"),
        "pod4_val": "22°",
    },
    # 10: Casino G-Snooze (Subtle Zebra Camo + Cyber Lime + Analog Chisel Hands)
    {
        "id": "10_casino_gsnooze",
        "bg_texture": 5,       # Subtle Zebra Camo (Refreshed GitHub palette)
        "theme_color": 0,      # Cyber Lime #BAFA08
        "logo_color": 0,       # Cyber Lime
        "sec_color": 1,        # Cyber Lime
        "time_color": 0,       # White
        "screen_texture": 2,   # Hex Dark
        "quad_style": 0,
        "bottom_style": 0,
        "bottom_bay_mode": 4,  # Date 18/10/2026
        "sub_dial_mode": 0,    # 8-Segment Battery Gauge
        "tick_style": 0,       # Classic
        "seconds_dot": 2,      # Theme dot
        "analog_hands": 8,     # Chisel Theme Hands!
        "top_logo": 0,         # CASINO
        "bottom_logo": 3,      # G-SNOOZE
        "time_str": "10:09",
        "sec_str": "35",
        "date_str": "18/10/2026",
        "pod1_val": "85%",
        "pod2_val": "9680",
        "pod3_val": ("15:30", "DUB"),
        "pod4_val": "18°",
    },
]

def render_dial(cfg):
    # Render 450x450 master canvas
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
        time_str=cfg.get("time_str", "10:08"),
        sec_str=cfg.get("sec_str", "42"),
        date_str=cfg.get("date_str"),
        pod1_val=cfg.get("pod1_val", "100%"),
        pod2_val=cfg.get("pod2_val", "5328"),
        pod3_val=cfg.get("pod3_val", ("15:30", "DUB")),
        pod4_val=cfg.get("pod4_val", "15:22"),
    )
    # Scale to 466x466
    dial_466 = dial_450.resize((466, 466), Image.Resampling.LANCZOS)
    
    # Apply anti-aliased circular alpha mask
    dial_rgba = Image.new("RGBA", (466, 466), (0, 0, 0, 0))
    dial_rgba.paste(dial_466, (0, 0), DIAL_MASK)
    return dial_rgba

def main():
    print("=== 1. Generating 10 Fresh 466x466 Dials ===")
    rendered_dials = {}
    
    for i, cfg in enumerate(CONFIGS):
        dial_rgba = render_dial(cfg)
        rendered_dials[cfg["id"]] = dial_rgba
        
        # Save transparent round dial in recreated_album_screenshots/
        recreated_path = os.path.join(ALBUM_DIR, f"recreated_{cfg['id']}.png")
        dial_rgba.save(recreated_path, optimize=True)
        
        # Save RGB dial on black background in play_store_screenshots/
        bg_black = Image.new("RGBA", (466, 466), (0, 0, 0, 255))
        dial_rgb = Image.alpha_composite(bg_black, dial_rgba).convert("RGB")
        play_rgb_path = os.path.join(PLAY_DIR, f"play_rgb_{cfg['id']}.png")
        dial_rgb.save(play_rgb_path, optimize=True)
        print(f"  [#{i+1:02d}] Saved {cfg['id']} -> {recreated_path} and {play_rgb_path}")

    print("\n=== 2. Updating Hero Screenshots (play_screenshot_1..4) ===")
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
        hero_path = os.path.join(PLAY_DIR, f"play_screenshot_{hero_num}_{cfg_id.split('_', 1)[1]}.png")
        dial_rgb.save(hero_path, optimize=True)
        print(f"  Hero #{hero_num} -> {hero_path}")

    print("\n=== 3. Composing 8-Watch Graphic (G-Shark-Main.png 3022x1476) ===")
    psd = PSDImage.open(PSD_PATH)
    W, H = psd.size
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    
    # Base background layer
    l0 = psd[0]
    comp.alpha_composite(l0.topil(), (l0.bbox[0], l0.bbox[1]))
    
    # 8 watch positions mapped to curated configs:
    # Top Row: 4 vibrant themes on dark plates (Volt Lime, Cyan, Violet, Silver)
    # Bottom Row: 4 authentic camouflage patterns (Woodland, Urban/Arctic, Desert, Subtle Zebra)
    case_configs = [
        CONFIGS[0],  # Case 1: 01_casino_gshark (Volt Lime Default, Battery Gauge)
        CONFIGS[2],  # Case 2: 03_curious_gsnack (Shark Blue / Cyan)
        CONFIGS[6],  # Case 3: 07_charming_gspot (Positive Inverted LCD + Deep Violet)
        CONFIGS[5],  # Case 4: 06_cheerful_gsloth (Tactical Mesh + Titanium Silver)
        CONFIGS[3],  # Case 5: 04_creative_gsquawk (Woodland Camo + Tactical Orange)
        CONFIGS[7],  # Case 6: 08_casino_gsnack (Urban / Arctic Camo + Hot Pink)
        CONFIGS[8],  # Case 7: 09_casino_gsquawk (Desert Camo + Amber Gold)
        CONFIGS[9],  # Case 8: 10_casino_gsnooze (Subtle Zebra Camo + Cyber Lime + Chisel Hands)
    ]
    
    group = psd[1]
    for idx, watch_group in enumerate(reversed(group)):
        c0 = watch_group[0]  # dial slot
        c1 = watch_group[1]  # bezel hardware & glass glare
        
        cfg = case_configs[idx]
        dial_rgba = rendered_dials[cfg["id"]]
        dial_402 = dial_rgba.resize((402, 402), Image.Resampling.LANCZOS)
        
        comp.alpha_composite(dial_402, (c0.bbox[0], c0.bbox[1]))
        
        img1 = c1.topil()
        if img1:
            comp.alpha_composite(img1, (c1.bbox[0], c1.bbox[1]))
            
    main_rgb = comp.convert("RGB")
    main_path = os.path.join(PLAY_DIR, "G-Shark-Main.png")
    main_rgb.save(main_path, optimize=True)
    print(f"  Saved main composite ({main_rgb.size[0]}x{main_rgb.size[1]} RGB) -> {main_path}")

    print("\n=== 4. Generating Feature Graphic (1024x500) ===")
    feat_img = main_rgb.resize((1024, 500), Image.Resampling.LANCZOS)
    feat_path = os.path.join(PLAY_DIR, "G-Shark-Feature-Graphic-1024x500.png")
    feat_img.save(feat_path, optimize=True)
    print(f"  Saved feature graphic ({feat_img.size[0]}x{feat_img.size[1]} RGB) -> {feat_path}")
    
    print("\n[SUCCESS] All Play Store assets updated successfully for v4.7!")

if __name__ == "__main__":
    main()
