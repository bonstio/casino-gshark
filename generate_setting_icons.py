#!/usr/bin/env python3
"""Generates zoomed-in 96x96 configuration option icons for all 16 watch face settings."""

import datetime
import math
import os
import zoneinfo
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRAWABLE_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")
FONT_DIR = os.path.join(BASE_DIR, "app/src/main/res/font")
BUILD_DIR = os.path.join(BASE_DIR, "build")
os.makedirs(BUILD_DIR, exist_ok=True)

ICON_SIZE = 96

# Fonts
DIGITAL7_PATH = os.path.join(FONT_DIR, "digital7.ttf")
ROB_BOLD_PATH = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf"
if not os.path.exists(ROB_BOLD_PATH):
    ROB_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf" if os.path.exists("C:/Windows/Fonts/arialbd.ttf") else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ROB_REG_PATH = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf"
if not os.path.exists(ROB_REG_PATH):
    ROB_REG_PATH = "C:/Windows/Fonts/arial.ttf" if os.path.exists("C:/Windows/Fonts/arial.ttf") else ROB_BOLD_PATH

# Cache loaded RGBA drawables
_IMAGE_CACHE = {}


def load_drawable(name):
    if name not in _IMAGE_CACHE:
        path = os.path.join(DRAWABLE_DIR, f"{name}.png")
        _IMAGE_CACHE[name] = Image.open(path).convert("RGBA")
    return _IMAGE_CACHE[name].copy()


def hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def tint_image(img, rgb, alpha_scale=1.0):
    r, g, b, a = img.split()
    if alpha_scale != 1.0:
        a = a.point(lambda p: min(255, max(0, int(round(p * alpha_scale)))))
    return Image.merge(
        "RGBA",
        (
            r.point(lambda p: (p * rgb[0]) // 255),
            g.point(lambda p: (p * rgb[1]) // 255),
            b.point(lambda p: (p * rgb[2]) // 255),
            a,
        ),
    )


def solid_tint_alpha(img, rgb, alpha_scale=1.0):
    _, _, _, a = img.split()
    if alpha_scale != 1.0:
        a = a.point(lambda p: min(255, max(0, int(round(p * alpha_scale)))))
    return Image.merge(
        "RGBA",
        (
            Image.new("L", img.size, rgb[0]),
            Image.new("L", img.size, rgb[1]),
            Image.new("L", img.size, rgb[2]),
            a,
        ),
    )


BG_TEXTURES = [
    "bg_lcd_real",
    "bg_lcd_matte_black",
    "bg_lcd_camo",
    "bg_lcd_camo_urban",
    "bg_lcd_camo_desert",
    "bg_lcd_camo_zebra",
    "bg_lcd_carbon_fiber",
    "bg_lcd_gloss_black",
    "bg_lcd_grid",
    "bg_lcd_tactical_mesh",
    "bg_lcd_ind_cyan",
    "bg_lcd_ind_lime",
    "bg_lcd_ind_blue",
    "bg_lcd_ind_red",
    "bg_lcd_ind_orange",
    "bg_lcd_ind_magenta",
    "bg_lcd_ind_silver",
    "bg_lcd_ind_black_silver",
]

THEME_COLORS = [
    "#BAFA08",  # 0: Cyber Lime
    "#39FF14",  # 1: Bright Lime Green
    "#0EDBFF",  # 2: Shark Blue
    "#FF660A",  # 3: Tactical Orange
    "#FF1E38",  # 4: Crimson Red
    "#FFC400",  # 5: Amber Gold
    "#FFFFFF",  # 6: Stealth White
    "#147EFF",  # 7: Vibrant Blue
    "#B040FF",  # 8: Deep Violet
    "#F514C8",  # 9: Hot Pink
    "#D2B48C",  # 10: Coyote Tan
    "#9A8A62",  # 11: Earth Khaki
    "#A76D43",  # 12: Mocha Brown
    "#94A3B8",  # 13: Steel Grey
    "#64748B",  # 14: Slate Charcoal
    "#CED8E2",  # 15: Titanium Silver
]

SEC_COLORS = {
    0: None,        # Same as clock
    1: "#BAFA08",
    2: "#39FF14",
    3: "#0EDBFF",
    4: "#FF660A",
    5: "#FF1E38",
    6: "#FFC400",
    7: "#FFFFFF",
    8: "#147EFF",
    9: "#B040FF",
    10: "#F514C8",
    11: "#D2B48C",
    12: "#9A8A62",
    13: "#A76D43",
    14: "#94A3B8",
    15: "#64748B",
    16: "#CED8E2",
    17: "#D4D4D4",  # Soft White
    18: "#0A0D10",  # Black
}

TOP_LOGOS = [
    "logo_casino",
    "logo_calypso",
    "logo_critical",
    "logo_charming",
    "logo_curious",
    "logo_creative",
    "logo_cautious",
    "logo_cheerful",
    None,
]

BOTTOM_LOGOS = [
    "logo_gshark",
    "logo_gspot",
    "logo_gsnack",
    "logo_gsnooze",
    "logo_gsquawk",
    "logo_gsloth",
    None,
]

SUBDIAL_TIMEZONES = {
    2: ("PPG", "Pacific/Pago_Pago"),
    3: ("HNL", "Pacific/Honolulu"),
    4: ("ANC", "America/Anchorage"),
    5: ("SFO", "America/Los_Angeles"),
    6: ("DEN", "America/Denver"),
    7: ("CHI", "America/Chicago"),
    8: ("NYC", "America/New_York"),
    9: ("SCL", "America/Santiago"),
    10: ("YYT", "America/St_Johns"),
    11: ("GRU", "America/Sao_Paulo"),
    12: ("FEN", "America/Noronha"),
    13: ("PDL", "Atlantic/Azores"),
    14: ("UTC", "UTC"),
    15: ("LON", "Europe/London"),
    16: ("PAR", "Europe/Paris"),
    17: ("CAI", "Europe/Athens"),
    18: ("IST", "Europe/Istanbul"),
    19: ("THR", "Asia/Tehran"),
    20: ("DXB", "Asia/Dubai"),
    21: ("KBL", "Asia/Kabul"),
    22: ("KHI", "Asia/Karachi"),
    23: ("DEL", "Asia/Kolkata"),
    24: ("KTM", "Asia/Kathmandu"),
    25: ("DAC", "Asia/Dhaka"),
    26: ("RGN", "Asia/Yangon"),
    27: ("BKK", "Asia/Bangkok"),
    28: ("HKG", "Asia/Hong_Kong"),
    29: ("TYO", "Asia/Tokyo"),
    30: ("ADL", "Australia/Adelaide"),
    31: ("SYD", "Australia/Sydney"),
    32: ("NOU", "Pacific/Noumea"),
    33: ("AKL", "Pacific/Auckland"),
    34: ("APW", "Pacific/Apia"),
    35: ("CXI", "Pacific/Kiritimati"),
}


def draw_centered_text(canvas, box, text, font_path, size, color_rgb, alpha=255):
    x, y, w, h = box
    font = ImageFont.truetype(font_path, size)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (w - tw) / 2.0 - bbox[0]
    ty = y + (h - th) / 2.0 - bbox[1]
    d.text((tx, ty), text, font=font, fill=(*color_rgb, alpha))
    canvas.alpha_composite(layer)


def draw_start_text(canvas, box, text, font_path, size, color_rgb, alpha=255):
    x, y, w, h = box
    font = ImageFont.truetype(font_path, size)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), text, font=font)
    th = bbox[3] - bbox[1]
    tx = x
    ty = y + (h - th) / 2.0 - bbox[1]
    d.text((tx, ty), text, font=font, fill=(*color_rgb, alpha))
    canvas.alpha_composite(layer)


def render_watchface(
    bg_texture=0,
    bg_border=0,
    theme_color=0,
    logo_color=0,
    sec_color=0,
    time_color=0,
    screen_texture=0,
    quad_style=0,
    bottom_style=0,
    bottom_bay_mode=4,
    sub_dial_mode=0,
    tick_style=0,
    seconds_dot=0,
    analog_hands=0,
    top_logo=0,
    bottom_logo=0,
):
    canvas = Image.new("RGBA", (450, 450), (0, 0, 0, 255))
    theme_rgb = hex_to_rgb(THEME_COLORS[theme_color])
    logo_rgb = hex_to_rgb(THEME_COLORS[logo_color])

    # 1. Background texture
    canvas.alpha_composite(load_drawable(BG_TEXTURES[bg_texture]))

    # 2. Border
    if bg_border == 0:
        canvas.alpha_composite(load_drawable("bg_border_classic"))

    # 3. Outer Bezel Ticks
    if tick_style == 0:
        canvas.alpha_composite(load_drawable("ticks_0_classic"))
    elif tick_style == 1:
        canvas.alpha_composite(load_drawable("ticks_1_hours"))
    elif tick_style == 2:
        canvas.alpha_composite(load_drawable("ticks_2_batons"))
    elif tick_style == 3:
        canvas.alpha_composite(load_drawable("ticks_3_chrono"))
    elif tick_style == 4:
        canvas.alpha_composite(load_drawable("ticks_4_numeric"))
    elif tick_style == 5:
        canvas.alpha_composite(load_drawable("ticks_5_theme_minor"))
        canvas.alpha_composite(solid_tint_alpha(load_drawable("ticks_5_theme_major"), theme_rgb))
    elif tick_style == 6:
        canvas.alpha_composite(load_drawable("ticks_6_wedge"))
    # tick_style 7 is None (no ticks rendered)

    # 4. Top Logo
    if top_logo < 8 and TOP_LOGOS[top_logo] is not None:
        logo_name = TOP_LOGOS[top_logo]
        outline_name = f"{logo_name}_outline"
        if top_logo == 0:
            canvas.alpha_composite(load_drawable(outline_name).resize((180, 35), Image.Resampling.LANCZOS), (135, 36))
            lw, lh = int(round(170 * 0.9)), int(round(25 * 0.9))
            l_img = solid_tint_alpha(load_drawable(logo_name).resize((lw, lh), Image.Resampling.LANCZOS), (255, 255, 255))
            canvas.alpha_composite(l_img, (140 + (170 - lw) // 2, 41 + (25 - lh)))
        else:
            canvas.alpha_composite(load_drawable(outline_name).resize((198, 35), Image.Resampling.LANCZOS), (126, 36))
            lw, lh = int(round(188 * 0.9)), int(round(25 * 0.9))
            l_img = solid_tint_alpha(load_drawable(logo_name).resize((lw, lh), Image.Resampling.LANCZOS), (255, 255, 255))
            canvas.alpha_composite(l_img, (131 + (188 - lw) // 2, 41 + (25 - lh)))

    # 5. Bottom Logo
    if bottom_logo < 6 and BOTTOM_LOGOS[bottom_logo] is not None:
        b_name = BOTTOM_LOGOS[bottom_logo]
        b_outline = f"{b_name}_outline"
        canvas.alpha_composite(load_drawable(b_outline).resize((228, 53), Image.Resampling.LANCZOS), (111, 368))
        b_img = solid_tint_alpha(load_drawable(b_name).resize((220, 45), Image.Resampling.LANCZOS), logo_rgb)
        canvas.alpha_composite(b_img, (115, 372))

    # 6. Quad Complication Overlays (x=70, y=90, w=310, h=78)
    tex_suffixes = {1: "hex_light", 2: "hex_dark", 3: "moire_light", 4: "moire_dark"}
    if quad_style == 0:
        if time_color == 2:
            if screen_texture == 0:
                canvas.alpha_composite(load_drawable("tex_quad_invert_default"), (70, 90))
            else:
                canvas.alpha_composite(load_drawable(f"tex_quad_invert_{tex_suffixes[screen_texture]}"), (70, 90))
        elif screen_texture in tex_suffixes:
            canvas.alpha_composite(load_drawable(f"tex_quad_{tex_suffixes[screen_texture]}"), (70, 90))

    # 7. Bottom Complication Overlays (x=70, y=302, w=310, h=56)
    if bottom_style == 0:
        if time_color == 2:
            if screen_texture == 0:
                canvas.alpha_composite(load_drawable("tex_bottom_invert_default"), (70, 302))
            else:
                canvas.alpha_composite(load_drawable(f"tex_bottom_invert_{tex_suffixes[screen_texture]}"), (70, 302))
        elif screen_texture in tex_suffixes:
            canvas.alpha_composite(load_drawable(f"tex_bottom_{tex_suffixes[screen_texture]}"), (70, 302))

    # 8. Center Digital Time Panel (when analog_hands == 0)
    if analog_hands == 0:
        canvas.alpha_composite(load_drawable(f"center_chamber_{bg_texture}"), (68, 164))
        if time_color == 2:
            if screen_texture == 0:
                canvas.alpha_composite(load_drawable("tex_invert_default"), (70, 178))
            else:
                canvas.alpha_composite(load_drawable(f"tex_invert_{tex_suffixes[screen_texture]}"), (70, 178))
        elif screen_texture in tex_suffixes:
            canvas.alpha_composite(load_drawable(f"tex_screen_{tex_suffixes[screen_texture]}"), (70, 178))

        # Wear OS flank logo
        canvas.alpha_composite(load_drawable("logo_wear_os_outline").resize((34, 28), Image.Resampling.LANCZOS), (34, 211))
        canvas.alpha_composite(load_drawable("logo_wear_os").resize((26, 20), Image.Resampling.LANCZOS), (38, 215))

        # Digital time HH:MM ("18:30")
        if time_color == 2:
            main_rgb = (10, 13, 16)
            ghost_rgb = (10, 13, 16)
            ghost_alpha = 28
        elif time_color == 1:
            main_rgb = (212, 212, 212)
            ghost_rgb = (255, 255, 255)
            ghost_alpha = 36
        else:
            main_rgb = (255, 255, 255)
            ghost_rgb = (255, 255, 255)
            ghost_alpha = 36

        draw_centered_text(canvas, (82, 165, 110, 108), "88", DIGITAL7_PATH, 120, ghost_rgb, ghost_alpha)
        draw_centered_text(canvas, (211, 165, 110, 108), "88", DIGITAL7_PATH, 120, ghost_rgb, ghost_alpha)
        draw_centered_text(canvas, (82, 165, 110, 108), "18", DIGITAL7_PATH, 120, main_rgb, 255)
        draw_centered_text(canvas, (194, 165, 15, 108), ":", DIGITAL7_PATH, 120, main_rgb, 255)
        draw_centered_text(canvas, (211, 165, 110, 108), "30", DIGITAL7_PATH, 120, main_rgb, 255)

        # Alarm indicator at (336, 188, 34, 16)
        alarm_rgb = main_rgb
        alarm_ic = solid_tint_alpha(load_drawable("ic_alarm_indicator").resize((34, 16), Image.Resampling.LANCZOS), alarm_rgb)
        canvas.alpha_composite(alarm_ic, (336, 188))

        # Seconds at (330, 206, 42, 42)
        if sec_color == 0:
            sec_rgb = main_rgb
            sec_ghost_alpha = 28 if time_color == 2 else 36
        else:
            sec_rgb = hex_to_rgb(SEC_COLORS[sec_color])
            sec_ghost_alpha = 28 if sec_color == 18 else (36 if sec_color in (7, 17) else 43)
        draw_centered_text(canvas, (330, 210, 42, 38), "88", DIGITAL7_PATH, 43, sec_rgb, sec_ghost_alpha)
        draw_centered_text(canvas, (330, 210, 42, 38), "04", DIGITAL7_PATH, 43, sec_rgb, 255)

    # 9. Top 4 Quad Complication Pods (x=72, 152, 232, 312; y=90, w=66, h=78)
    quad_black_mode = (time_color == 2 and quad_style == 0)
    quad_fg = (212, 212, 212) if time_color == 1 else ((10, 13, 16) if quad_black_mode else (255, 255, 255))
    quad_ov = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    qd = ImageDraw.Draw(quad_ov)
    # Pod 1 (center 105): Battery 100%
    qd.rounded_rectangle((91, 107, 115, 121), radius=2, outline=(*quad_fg, 255), width=2)
    qd.rectangle((115, 111, 118, 117), fill=(*quad_fg, 255))
    qd.rectangle((94, 110, 110, 118), fill=(*quad_fg, 255))
    draw_centered_text(quad_ov, (72, 134, 66, 20), "100%", ROB_BOLD_PATH, 16, quad_fg, 255)
    # Pod 2 (center 185): Steps 5328
    prev = load_drawable("preview").resize((450, 450), Image.Resampling.LANCZOS)
    shoe_crop = prev.crop((167, 98, 203, 134))
    shoe_ic = Image.new("RGBA", shoe_crop.size, (0, 0, 0, 0))
    for py in range(shoe_crop.height):
        for px in range(shoe_crop.width):
            r_p, g_p, b_p, _ = shoe_crop.getpixel((px, py))
            lum = max(r_p, g_p, b_p)
            if lum > 45:
                a_p = min(255, int(round((lum - 35) / 220.0 * 255.0)))
                shoe_ic.putpixel((px, py), (*quad_fg, a_p))
    quad_ov.alpha_composite(shoe_ic, (167, 98))
    draw_centered_text(quad_ov, (152, 134, 66, 20), "5328", ROB_BOLD_PATH, 16, quad_fg, 255)
    # Pod 3 (center 265): World Clock 15:30 DUB
    qd.ellipse((251, 100, 279, 128), outline=(*quad_fg, 255), width=2)
    qd.ellipse((258, 100, 272, 128), outline=(*quad_fg, 255), width=2)
    qd.line([(251, 114), (279, 114)], fill=(*quad_fg, 255), width=2)
    draw_centered_text(quad_ov, (232, 132, 66, 20), "15:30", ROB_BOLD_PATH, 16, quad_fg, 255)
    draw_centered_text(quad_ov, (232, 149, 66, 14), "DUB", ROB_BOLD_PATH, 10, quad_fg, 255)
    # Pod 4 (center 345): Alarm / Sunset 15:22
    qd.ellipse((331, 102, 359, 130), outline=(*quad_fg, 255), width=2)
    qd.line([(345, 116), (345, 108)], fill=(*quad_fg, 255), width=2)
    qd.line([(345, 116), (352, 120)], fill=(*quad_fg, 255), width=2)
    draw_centered_text(quad_ov, (312, 134, 66, 20), "15:22", ROB_BOLD_PATH, 16, quad_fg, 255)
    canvas.alpha_composite(quad_ov)

    # 10. Bottom Bay (x=70, y=302, w=226, h=56)
    bot_black_mode = (time_color == 2 and bottom_style == 0)
    bot_fg = (212, 212, 212) if time_color == 1 else ((10, 13, 16) if bot_black_mode else (255, 255, 255))
    cal_ic = solid_tint_alpha(load_drawable("ic_calendar_date").resize((32, 32), Image.Resampling.LANCZOS), bot_fg)

    if bottom_bay_mode == 0:
        # Complication / Next Event mode
        canvas.alpha_composite(cal_ic, (70 + 12, 302 + 12))
        draw_start_text(canvas, (70 + 52, 302 + 6, 166, 24), "15:00 Coffee", ROB_BOLD_PATH, 17, bot_fg, 255)
        draw_start_text(canvas, (70 + 52, 302 + 29, 166, 18), "Conf Room B", ROB_REG_PATH, 12, bot_fg, 210)
    elif bottom_bay_mode == 1:
        canvas.alpha_composite(cal_ic, (70 + 54, 302 + 13))
        draw_start_text(canvas, (70 + 92, 302 + 10, 126, 38), "Jan 31", ROB_REG_PATH, 25, bot_fg, 255)
    elif bottom_bay_mode == 2:
        canvas.alpha_composite(cal_ic, (70 + 33, 302 + 13))
        draw_start_text(canvas, (70 + 71, 302 + 10, 148, 38), "Sat 01/31", ROB_REG_PATH, 25, bot_fg, 255)
    elif bottom_bay_mode == 3:
        canvas.alpha_composite(cal_ic, (70 + 33, 302 + 13))
        draw_start_text(canvas, (70 + 71, 302 + 10, 148, 38), "Sat 31/01", ROB_REG_PATH, 25, bot_fg, 255)
    elif bottom_bay_mode == 4:
        canvas.alpha_composite(cal_ic, (70 + 23, 302 + 13))
        draw_start_text(canvas, (70 + 61, 302 + 10, 158, 38), "31/01/2026", ROB_REG_PATH, 25, bot_fg, 255)

    # 11. Sub-Dial (x=302, y=273, w=100, h=100)
    sub_group = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    if sub_dial_mode == 0:
        # 8-Segment Battery Gauge
        sub_group.alpha_composite(solid_tint_alpha(load_drawable("subdial_seg_ghost"), theme_rgb, 43 / 255.0))
        for seg_i in range(1, 8):
            sub_group.alpha_composite(solid_tint_alpha(load_drawable(f"subdial_seg_{seg_i}"), theme_rgb))
        sub_group.alpha_composite(load_drawable("subdial_batt_radial_shade"))
        sub_group.alpha_composite(load_drawable("subdial_batt_hub"))
    elif sub_dial_mode == 1:
        # 12-Segment Seconds Gauge (show segments 00..07 lit = 40 seconds)
        sub_group.alpha_composite(solid_tint_alpha(load_drawable("subdial_sec_ghost"), theme_rgb, 43 / 255.0))
        for seg_i in range(8):
            sub_group.alpha_composite(solid_tint_alpha(load_drawable(f"subdial_sec_{seg_i:02d}"), theme_rgb))
        sub_group.alpha_composite(load_drawable("subdial_sec_radial_shade"))
        sub_group.alpha_composite(load_drawable("subdial_sec_hub"))
    else:
        # Analog Dual-Timezone Clock (2..35)
        if bottom_style == 0:
            if time_color == 2:
                if screen_texture == 0:
                    sub_group.alpha_composite(load_drawable("tex_subdial_invert_default"))
                else:
                    sub_group.alpha_composite(load_drawable(f"tex_subdial_invert_{tex_suffixes[screen_texture]}"))
            elif screen_texture in tex_suffixes:
                sub_group.alpha_composite(load_drawable(f"tex_subdial_{tex_suffixes[screen_texture]}"))

        if bot_black_mode:
            sub_group.alpha_composite(load_drawable("subdial_analog_ticks_black"))
            city_col = (10, 13, 16)
        else:
            sub_group.alpha_composite(load_drawable("subdial_analog_ticks"))
            city_col = (196, 210, 228)

        city_code, tz_name = SUBDIAL_TIMEZONES[sub_dial_mode]
        draw_centered_text(sub_group, (0, 58, 100, 20), city_code, ROB_BOLD_PATH, 13, city_col, 255)

        # Compute timezone hour & minute angles for a fixed reference UTC time (2026-01-31 10:25 UTC)
        utc_dt = datetime.datetime(2026, 1, 31, 10, 25, 0, tzinfo=datetime.timezone.utc)
        loc_dt = utc_dt.astimezone(zoneinfo.ZoneInfo(tz_name))
        hr_angle = ((loc_dt.hour % 12) + loc_dt.minute / 60.0) * 30.0
        mn_angle = loc_dt.minute * 6.0

        hr_hand = solid_tint_alpha(load_drawable("subdial_hand_hour"), theme_rgb)
        hr_rot = hr_hand.rotate(-hr_angle, resample=Image.Resampling.BICUBIC, center=(50, 50))
        sub_group.alpha_composite(hr_rot)

        mn_hand = load_drawable("subdial_hand_min")
        if bot_black_mode:
            mn_hand = solid_tint_alpha(mn_hand, (10, 13, 16))
        mn_rot = mn_hand.rotate(-mn_angle, resample=Image.Resampling.BICUBIC, center=(50, 50))
        sub_group.alpha_composite(mn_rot)

        sub_group.alpha_composite(load_drawable("subdial_analog_cap"))

    canvas.alpha_composite(sub_group, (302, 273))

    # 12. Rotating Seconds Hand Orbit Indicator (at 5-second mark = 30 degrees)
    if seconds_dot > 0:
        dot_map = {
            1: ("sec_dot_white", None),
            2: ("sec_dot_theme", theme_rgb),
            3: ("sec_square_white", None),
            4: ("sec_square_theme", theme_rgb),
            5: ("sec_triangle_white", None),
            6: ("sec_triangle_theme", theme_rgb),
        }
        res_name, d_tint = dot_map[seconds_dot]
        d_img = load_drawable(res_name).resize((20, 225), Image.Resampling.LANCZOS)
        if d_tint is not None:
            d_img = tint_image(d_img, d_tint)
        sec_layer = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
        sec_layer.alpha_composite(d_img, (215, 0))
        sec_rot = sec_layer.rotate(-30.0, resample=Image.Resampling.BICUBIC, center=(225, 225))
        canvas.alpha_composite(sec_rot)

    # 13. Main Analog Hands (when analog_hands > 0, placed at 10:09 -> hr=304.5, mn=54.0)
    if analog_hands > 0:
        hr_deg, mn_deg = 304.5, 54.0

        def render_hand_pair(frame_hr, lume_hr, frame_mn, lume_mn, lume_rgb):
            hands_layer = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
            for fr_name, lu_name, ang in [(frame_hr, lume_hr, hr_deg), (frame_mn, lume_mn, mn_deg)]:
                single = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
                if fr_name is not None:
                    fr = load_drawable(fr_name).resize((60, 450), Image.Resampling.LANCZOS)
                    single.alpha_composite(fr, (195, 0))
                lu = load_drawable(lu_name).resize((60, 450), Image.Resampling.LANCZOS)
                lu_t = tint_image(lu, lume_rgb)
                single.alpha_composite(lu_t, (195, 0))
                rot = single.rotate(-ang, resample=Image.Resampling.BICUBIC, center=(225, 225))
                hands_layer.alpha_composite(rot)
            r_h, g_h, b_h, a_h = hands_layer.split()
            a_h = a_h.point(lambda p: (p * 242) // 255)
            return Image.merge("RGBA", (r_h, g_h, b_h, a_h))

        if analog_hands == 1:
            canvas.alpha_composite(
                render_hand_pair("hand_sword_hr_frame", "hand_sword_hr_lume", "hand_sword_mn_frame", "hand_sword_mn_lume", theme_rgb)
            )
            ring_rgb = theme_rgb
        elif analog_hands == 2:
            canvas.alpha_composite(
                render_hand_pair("hand_sword_hr_frame", "hand_sword_hr_lume", "hand_sword_mn_frame", "hand_sword_mn_lume", (255, 255, 255))
            )
            ring_rgb = (255, 255, 255)
        elif analog_hands == 3:
            canvas.alpha_composite(
                render_hand_pair("hand_baton_hr_frame", "hand_baton_hr_lume", "hand_baton_mn_frame", "hand_baton_mn_lume", theme_rgb)
            )
            ring_rgb = theme_rgb
        elif analog_hands == 4:
            canvas.alpha_composite(
                render_hand_pair("hand_baton_hr_frame", "hand_baton_hr_lume", "hand_baton_mn_frame", "hand_baton_mn_lume", (255, 255, 255))
            )
            ring_rgb = (255, 255, 255)
        elif analog_hands == 5:
            canvas.alpha_composite(
                render_hand_pair(None, "hand_ghost_hr", None, "hand_ghost_mn", theme_rgb)
            )
            ring_rgb = theme_rgb
        elif analog_hands == 6:
            canvas.alpha_composite(
                render_hand_pair("hand_needle_hr_frame", "hand_needle_hr_lume", "hand_needle_mn_frame", "hand_needle_mn_lume", theme_rgb)
            )
            ring_rgb = theme_rgb
        elif analog_hands == 7:
            canvas.alpha_composite(
                render_hand_pair("hand_needle_hr_frame", "hand_needle_hr_lume", "hand_needle_mn_frame", "hand_needle_mn_lume", (255, 255, 255))
            )
            ring_rgb = (255, 255, 255)
        elif analog_hands == 8:
            canvas.alpha_composite(
                render_hand_pair("hand_chisel_hr_frame", "hand_chisel_hr_lume", "hand_chisel_mn_frame", "hand_chisel_mn_lume", theme_rgb)
            )
            ring_rgb = theme_rgb
        elif analog_hands == 9:
            canvas.alpha_composite(
                render_hand_pair("hand_chisel_hr_frame", "hand_chisel_hr_lume", "hand_chisel_mn_frame", "hand_chisel_mn_lume", (255, 255, 255))
            )
            ring_rgb = (255, 255, 255)

        p_base = load_drawable("main_pinion_base").resize((40, 40), Image.Resampling.LANCZOS)
        p_ring = solid_tint_alpha(load_drawable("main_pinion_ring").resize((40, 40), Image.Resampling.LANCZOS), ring_rgb)
        canvas.alpha_composite(p_base, (205, 205))
        canvas.alpha_composite(p_ring, (205, 205))

    return canvas


def make_circular_icon(full_img, crop_box, size=ICON_SIZE):
    """Crops crop_box from full_img, resizes to size x size, and applies a crisp circular bezel mask."""
    raw_crop = full_img.crop(crop_box)
    bg_crop = Image.new("RGBA", raw_crop.size, (0, 0, 0, 255))
    bg_crop.alpha_composite(raw_crop)
    cropped = bg_crop.resize((size, size), Image.Resampling.LANCZOS)

    # Supersampled 4x circular mask & thin metallic bezel ring
    k = 4
    s4 = size * k
    mask4 = Image.new("L", (s4, s4), 0)
    ImageDraw.Draw(mask4).ellipse((2 * k, 2 * k, s4 - 2 * k - 1, s4 - 2 * k - 1), fill=255)
    mask = mask4.resize((size, size), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(cropped, (0, 0), mask)

    # Subtle 1.5px dark metallic frame so the circular icon has a clean edge on any card background
    ring4 = Image.new("RGBA", (s4, s4), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring4)
    rd.ellipse((2 * k, 2 * k, s4 - 2 * k - 1, s4 - 2 * k - 1), outline=(92, 106, 124, 210), width=int(1.5 * k))
    out.alpha_composite(ring4.resize((size, size), Image.Resampling.LANCZOS))
    return out


def generate_all_icons():
    generated = {}  # (setting_id, option_id) -> icon_resource_name

    def save_icon(setting_id, opt_id, wf_img, crop_box):
        res_name = f"ic_cfg_{setting_id.lower()}_{opt_id}"
        icon_img = make_circular_icon(wf_img, crop_box)
        icon_path = os.path.join(DRAWABLE_DIR, f"{res_name}.png")
        icon_img.save(icon_path, optimize=True)
        generated[(setting_id, str(opt_id))] = (res_name, icon_img)

    # 1. bgTexture (18 options: 0..17) - Top-left bezel & textured plate
    crop_bg_tex = (28, 28, 178, 178)
    for i in range(18):
        wf = render_watchface(bg_texture=i, bg_border=0)
        save_icon("bgTexture", i, wf, crop_bg_tex)

    # 2. bgBorder (2 options: 0..1) - Top-left outer bezel rim over high-contrast Industrial Cyan
    crop_bg_border = (8, 8, 148, 148)
    for i in range(2):
        wf = render_watchface(bg_texture=10, bg_border=i)
        save_icon("bgBorder", i, wf, crop_bg_border)

    # 3. themeColor (16 options: 0..15) - GA-100 circular sub-dial with theme-tinted battery segments
    crop_theme_color = (298, 269, 406, 377)
    for i in range(16):
        wf = render_watchface(theme_color=i, sub_dial_mode=0)
        save_icon("themeColor", i, wf, crop_theme_color)

    # 4. logoColor (16 options: 0..15) - Bottom G-SHARK wordmark logo
    crop_logo_color = (105, 275, 345, 515)
    for i in range(16):
        wf = render_watchface(logo_color=i, bottom_logo=0)
        save_icon("logoColor", i, wf, crop_logo_color)

    # 5. secColor (19 options: 0..18) - Digital seconds readout "04" in right LCD chamber
    crop_sec_color = (298, 172, 402, 276)
    for i in range(19):
        # For option 18 (Black), show on inverted light LCD (time_color=2) so black digits are crisp
        tc = 2 if i == 18 else 0
        wf = render_watchface(sec_color=i, time_color=tc)
        save_icon("secColor", i, wf, crop_sec_color)

    # 6. timeColor (3 options: 0..2) - Center digital clock digits "18:30"
    crop_time_color = (80, 110, 320, 350)
    for i in range(3):
        wf = render_watchface(time_color=i)
        save_icon("timeColor", i, wf, crop_time_color)

    # 7. screenTexture (5 options: 0..4) - Center LCD chamber texture behind digits
    crop_screen_tex = (80, 110, 320, 350)
    for i in range(5):
        wf = render_watchface(screen_texture=i, time_color=0)
        save_icon("screenTexture", i, wf, crop_screen_tex)

    # 8. quadStyle (2 options: 0..1) - Top complication pods (Match LCD Screen vs Classic Dark, shown with time_color=2)
    crop_quad_style = (145, 60, 305, 220)
    for i in range(2):
        wf = render_watchface(quad_style=i, time_color=2)
        save_icon("quadStyle", i, wf, crop_quad_style)

    # 9. bottomStyle (2 options: 0..1) - Bottom bay (Match LCD Screen vs Classic Dark, shown with time_color=2)
    crop_bottom_style = (105, 245, 265, 405)
    for i in range(2):
        wf = render_watchface(bottom_style=i, time_color=2)
        save_icon("bottomStyle", i, wf, crop_bottom_style)

    # 10. bottomBayMode (5 options: 0..4) - Bottom rectangular bay content (Next Event vs 4 Date formats)
    crop_bottom_bay = (93, 240, 273, 420)
    for i in range(5):
        wf = render_watchface(bottom_bay_mode=i)
        save_icon("bottomBayMode", i, wf, crop_bottom_bay)

    # 11. subDialMode (36 options: 0..35) - GA-100 circular sub-dial (Battery, Seconds, 34 World Timezones)
    crop_subdial = (298, 269, 406, 377)
    for i in range(36):
        wf = render_watchface(sub_dial_mode=i)
        save_icon("subDialMode", i, wf, crop_subdial)

    # 12. tickStyle (8 options: 0..7) - Top-right outer bezel tick arc
    crop_tick_style = (275, 15, 425, 165)
    for i in range(8):
        wf = render_watchface(tick_style=i)
        save_icon("tickStyle", i, wf, crop_tick_style)

    # 13. secondsDot (7 options: 0..6) - Outer bezel at 5-second mark (30 degrees, center ~(333, 45))
    crop_sec_dot = (283, 0, 383, 100)
    for i in range(7):
        wf = render_watchface(seconds_dot=i)
        save_icon("secondsDot", i, wf, crop_sec_dot)

    # 14. analogHands (10 options: 0..9) - Center analog hands & 3D pinion cap
    crop_analog_hands = (125, 115, 325, 315)
    for i in range(10):
        wf = render_watchface(analog_hands=i)
        save_icon("analogHands", i, wf, crop_analog_hands)

    # 15. topLogo (9 options: 0..8) - Top bezel wordmark logo
    crop_top_logo = (115, -55, 335, 165)
    for i in range(9):
        wf = render_watchface(top_logo=i)
        save_icon("topLogo", i, wf, crop_top_logo)

    # 16. bottomLogo (7 options: 0..6) - Bottom bezel wordmark logo
    crop_bottom_logo = (105, 275, 345, 515)
    for i in range(7):
        wf = render_watchface(bottom_logo=i)
        save_icon("bottomLogo", i, wf, crop_bottom_logo)

    return generated


def build_contact_sheet(generated):
    settings_order = [
        ("bgTexture", 18),
        ("bgBorder", 2),
        ("themeColor", 16),
        ("logoColor", 16),
        ("secColor", 19),
        ("timeColor", 3),
        ("screenTexture", 5),
        ("quadStyle", 2),
        ("bottomStyle", 2),
        ("bottomBayMode", 5),
        ("subDialMode", 36),
        ("tickStyle", 7),
        ("secondsDot", 7),
        ("analogHands", 10),
        ("topLogo", 9),
        ("bottomLogo", 7),
    ]
    cols = 12
    cell_w, cell_h = 108, 116
    rows = 0
    for _, count in settings_order:
        rows += math.ceil(count / cols)

    sheet_w = 180 + cols * cell_w + 20
    sheet_h = rows * cell_h + 40
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (18, 22, 28, 255))
    d = ImageDraw.Draw(sheet)
    font_lbl = ImageFont.truetype(ROB_BOLD_PATH, 15)
    font_sub = ImageFont.truetype(ROB_REG_PATH, 11)

    cur_row = 0
    for s_id, count in settings_order:
        d.text((16, cur_row * cell_h + 48), f"{s_id} ({count})", font=font_lbl, fill=(230, 236, 245, 255))
        for opt_i in range(count):
            r_idx = cur_row + (opt_i // cols)
            c_idx = opt_i % cols
            x = 180 + c_idx * cell_w
            y = 16 + r_idx * cell_h
            res_name, ic_img = generated[(s_id, str(opt_i))]
            sheet.alpha_composite(ic_img, (x, y))
            d.text((x + 36, y + 98), f"#{opt_i}", font=font_sub, fill=(160, 172, 188, 255))
        cur_row += math.ceil(count / cols)

    sheet_path = os.path.join(BUILD_DIR, "setting_icons_contact_sheet.png")
    sheet.save(sheet_path)
    print(f"Generated {len(generated)} icons and saved contact sheet to {sheet_path}")


if __name__ == "__main__":
    gen = generate_all_icons()
    build_contact_sheet(gen)
