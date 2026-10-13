#!/usr/bin/env python3
"""Generates high-resolution and watch-ready CASINO-style alternate logos."""

import os
import math
from PIL import Image, ImageDraw, ImageFont

SCRATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
EXPORT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/exported_logo"
DRAWABLE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/app/src/main/res/drawable"

CASINO_REF_PATH = os.path.join(SCRATCH_DIR, "casino_fixed_highres.png")
ALPHABET_4X_PATH = os.path.join(SCRATCH_DIR, "michroma_heavy_4x.png")


def load_glyph_library():
    """Returns a dict mapping 'A'..'Z' to 100px-tall RGBA glyph images."""
    glyphs = {}

    # 1. Load exact reference glyphs from casino_fixed_highres.png (717x100)
    ref = Image.open(CASINO_REF_PATH).convert("RGBA")
    ref_slices = {
        "C": (0, 116),
        "A": (126, 262),
        "S": (273, 386),
        "I": (404, 432),
        "N": (452, 576),
        "O": (593, 717),
    }
    for ch, (x0, x1) in ref_slices.items():
        glyphs[ch] = ref.crop((x0, 0, x1, 100))

    # 2. Extract remaining glyphs from michroma_heavy_4x.png (4 cols x 7 rows, 1000x520 cells)
    sheet = Image.open(ALPHABET_4X_PATH).convert("RGBA")
    CELL_W = 1000
    CELL_H = 520
    COLS = 4
    scale_x = 116.0 / 446.0

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    round_top = {"C", "G", "O", "Q", "S"}
    round_bot = {"C", "G", "J", "O", "Q", "S", "U"}

    for idx, ch in enumerate(letters):
        if ch in glyphs:
            continue
        col = idx % COLS
        row = idx // COLS
        cell = sheet.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
        alpha = cell.split()[3]
        bbox = alpha.getbbox()
        x0, y0, x1, y1 = bbox
        # Clip any sharp miter spikes on M, A, V, W that protrude beyond flat cap-height (y=66..439)
        if ch not in round_top and y0 < 66:
            y0 = 66
        if ch not in round_bot and y1 > 439:
            y1 = 439
        w4 = x1 - x0
        w1 = int(round(w4 * scale_x))
        if ch == "M":
            w1 = 148

        y_top_1 = 0 if ch in round_top else 1
        y_bot_1 = 97 if ch in round_bot else 95
        h1 = y_bot_1 - y_top_1

        cropped = cell.crop((x0, y0, x1, y1))
        resized = cropped.resize((w1, h1), Image.Resampling.LANCZOS)

        # Boost alpha slightly so edge sharpness matches casino_fixed_highres.png
        r, g, b, a = resized.split()
        a = a.point(lambda p: min(255, int(p * 1.08)) if p > 12 else 0)
        resized = Image.merge("RGBA", (Image.new("L", (w1, h1), 255),
                                       Image.new("L", (w1, h1), 255),
                                       Image.new("L", (w1, h1), 255), a))

        canvas = Image.new("RGBA", (w1, 100), (0, 0, 0, 0))
        canvas.paste(resized, (0, y_top_1))
        glyphs[ch] = canvas

    return glyphs


# Optical kerning table (in 100px-tall high-res pixel units; represents bbox-to-bbox gap)
# Reference gaps in CASINO:
#   C-A: 10, A-S: 11, S-I: 18, I-N: 20, N-O: 17
KERNING_GAPS = {
    # Original CASINO reference pairs
    ("C", "A"): 10,
    ("A", "S"): 11,
    ("S", "I"): 18,
    ("I", "N"): 20,
    ("N", "O"): 17,

    # CALYPSO pairs
    ("A", "L"): 13,
    ("L", "Y"): -22,  # Y top-left overhang over L bottom horizontal bar
    ("Y", "P"): 3,    # P vertical stem tucked into Y right open space
    ("P", "S"): 13,
    ("S", "O"): 15,

    # CRITICAL pairs
    ("C", "R"): 17,
    ("R", "I"): 18,
    ("I", "T"): 11,
    ("T", "I"): 11,
    ("I", "C"): 17,

    # CHARMING pairs
    ("C", "H"): 17,
    ("H", "A"): 12,
    ("A", "R"): 12,
    ("R", "M"): 17,
    ("M", "I"): 19,
    ("N", "G"): 17,

    # CURIOUS pairs
    ("C", "U"): 17,
    ("U", "R"): 18,
    ("I", "O"): 17,
    ("O", "U"): 16,
    ("U", "S"): 16,

    # CREATIVE pairs
    ("R", "E"): 18,
    ("E", "A"): 10,
    ("A", "T"): -8,   # A bottom-right diagonal tucks under T top-left crossbar
    ("I", "V"): 10,
    ("V", "E"): 10,

    # CAUTIOUS pairs
    ("A", "U"): 11,
    ("U", "T"): 9,
    ("T", "I"): 11,

    # CHEERFUL pairs
    ("H", "E"): 20,
    ("E", "E"): 18,
    ("E", "R"): 18,
    ("R", "F"): 18,
    ("F", "U"): 10,
    ("U", "L"): 18,
}


def get_pair_gap(c1, c2):
    if (c1, c2) in KERNING_GAPS:
        return KERNING_GAPS[(c1, c2)]
    # Fallback optical rules if any new words are rendered
    round_right = {"C", "G", "O", "Q", "S", "D", "P", "R", "B"}
    round_left = {"C", "G", "O", "Q", "S", "J"}
    diag_Set = {"A", "V", "W", "Y", "X"}
    if c1 in diag_Set or c2 in diag_Set:
        return 12
    if c1 in round_right and c2 in round_left:
        return 15
    if c1 in round_right or c2 in round_left:
        return 17
    return 20


def render_word_highres(word, glyphs):
    """Renders a word at 100px height matching casino_fixed_highres.png."""
    word = word.upper()
    positions = []
    cur_x = 0
    for i, ch in enumerate(word):
        g = glyphs[ch]
        if i > 0:
            gap = get_pair_gap(word[i - 1], ch)
            cur_x += gap
        positions.append((cur_x, g))
        cur_x += g.width

    total_w = cur_x
    out = Image.new("RGBA", (total_w, 100), (0, 0, 0, 0))
    for x, g in positions:
        out.alpha_composite(g, (x, 0))
    return out


def make_thin_black_outline_4x_sdf(alpha_1x, pad=5, scale_factor=0.9, pivot=(0.5, 1.0), box_origin_1x=(126, 36), orig_origin_1x=(131, 41), radius_px=1.25):
    """
    Given a 1x alpha image `alpha_1x` (188x25), places it into a padded canvas at 4x resolution
    accounting for WatchFace Format's scaleX=0.9, scaleY=0.9 around pivot=(0.5, 1.0),
    computes an exact Euclidean distance field out to `radius_px`, and downsamples to 1x
    to produce a razor-sharp anti-aliased thin black outline RGBA image (198x35).
    """
    S = 4
    w0, h0 = alpha_1x.size
    W1 = w0 + 2 * pad
    H1 = h0 + 2 * pad
    W4, H4 = W1 * S, H1 * S

    canvas_4x = Image.new("L", (W4, H4), 0)
    if scale_factor != 1.0 and pivot is not None:
        sw4 = int(round(w0 * scale_factor * S))
        sh4 = int(round(h0 * scale_factor * S))
        scaled_a = alpha_1x.resize((sw4, sh4), Image.Resampling.LANCZOS)
        px_wf = orig_origin_1x[0] + pivot[0] * w0
        py_wf = orig_origin_1x[1] + pivot[1] * h0
        x_tl_wf = px_wf - pivot[0] * (w0 * scale_factor)
        y_tl_wf = py_wf - pivot[1] * (h0 * scale_factor)
        ox4 = int(round((x_tl_wf - box_origin_1x[0]) * S))
        oy4 = int(round((y_tl_wf - box_origin_1x[1]) * S))
        canvas_4x.paste(scaled_a, (ox4, oy4))
    else:
        scaled_a = alpha_1x.resize((w0 * S, h0 * S), Image.Resampling.LANCZOS)
        canvas_4x.paste(scaled_a, (pad * S, pad * S))

    R4 = radius_px * S
    R_int = int(math.ceil(R4 + 1.0))
    src_bytes = canvas_4x.tobytes()
    out_bytes = bytearray(W4 * H4)

    offsets = []
    for dy in range(-R_int, R_int + 1):
        for dx in range(-R_int, R_int + 1):
            d1x = math.hypot(dx, dy) / float(S)
            if d1x <= radius_px + 0.35:
                cov = max(0.0, min(1.0, (radius_px + 0.25 - d1x) / 0.5))
                if cov > 0.0:
                    offsets.append((dx, dy, int(round(cov * 255.0))))

    for y in range(R_int, H4 - R_int):
        row_off = y * W4
        for x in range(R_int, W4 - R_int):
            sv = src_bytes[row_off + x]
            if sv > 32:
                for dx, dy, w_cov in offsets:
                    val = (sv * w_cov) // 255
                    idx = (y + dy) * W4 + (x + dx)
                    if val > out_bytes[idx]:
                        out_bytes[idx] = val

    dilated_4x = Image.frombytes("L", (W4, H4), bytes(out_bytes))
    dilated_1x = dilated_4x.resize((W1, H1), Image.Resampling.LANCZOS)

    rgba = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    rgba.putalpha(dilated_1x)
    return rgba


def main():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(DRAWABLE_DIR, exist_ok=True)
    glyphs = load_glyph_library()

    # Verify CASINO exact reproduction
    casino_test = render_word_highres("CASINO", glyphs)
    print(f"CASINO test size: {casino_test.size} (reference is 717x100)")

    words = [
        "CALYPSO",
        "CRITICAL",
        "CHARMING",
        "CURIOUS",
        "CREATIVE",
        "CAUTIOUS",
        "CHEERFUL",
    ]

    rendered_highres = {"CASINO": Image.open(CASINO_REF_PATH).convert("RGBA")}
    MAX_WATCH_W = 187  # At most 10% longer than the original 170px CASINO logo (170 * 1.10 = 187px)
    SLOT_W = 188       # Even width so x = 225 - 94 = 131 centers cleanly at x=225
    SLOT_H = 25

    for word in words:
        hr = render_word_highres(word, glyphs)
        rendered_highres[word] = hr
        slug = word.lower()

        # 1. Save high-res 4x (height=100px) to exported_logo/ and artifact dir
        export_hr_path = os.path.join(EXPORT_DIR, f"logo_{slug}_highres_4x_white.png")
        artifact_hr_path = os.path.join(ARTIFACT_DIR, f"logo_{slug}_highres_4x.png")
        hr.save(export_hr_path)
        hr.save(artifact_hr_path)

        # 2. Save 1x proportional height (height=25px, exact 1/4 scale of CASINO)
        w_1x_prop = int(round(hr.width * (170.0 / 717.0)))
        img_1x_height = hr.resize((w_1x_prop, 25), Image.Resampling.LANCZOS)
        export_1x_h_path = os.path.join(EXPORT_DIR, f"logo_{slug}_1x_match_height.png")
        img_1x_height.save(export_1x_h_path)

        # 3. Scale down so width is at most MAX_WATCH_W (187px, +10% of 170px), preserving aspect ratio
        target_w = min(w_1x_prop, MAX_WATCH_W)
        scale_down = target_w / float(w_1x_prop)
        target_h = max(1, int(round(25.0 * scale_down)))
        scaled_logo = hr.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Boost alpha slightly after LANCZOS downsampling so 1x strokes stay crisp white like logo_casino.png
        r, g, b, a = scaled_logo.split()
        a = a.point(lambda p: min(255, int(round(p * 1.12))) if p > 8 else 0)
        scaled_logo = Image.merge("RGBA", (
            Image.new("L", (target_w, target_h), 255),
            Image.new("L", (target_w, target_h), 255),
            Image.new("L", (target_w, target_h), 255),
            a
        ))

        # Place centered horizontally and bottom-aligned (or vertically centered near bottom baseline) in 188x25 slot
        # Using bottom-ish vertical centering so the visual centerline aligns with CASINO
        canvas_slot = Image.new("RGBA", (SLOT_W, SLOT_H), (0, 0, 0, 0))
        paste_x = (SLOT_W - target_w) // 2
        paste_y = (SLOT_H - target_h) // 2
        canvas_slot.paste(scaled_logo, (paste_x, paste_y))

        # Save to app/src/main/res/drawable/logo_<slug>.png and exported_logo/
        drawable_logo_path = os.path.join(DRAWABLE_DIR, f"logo_{slug}.png")
        canvas_slot.save(drawable_logo_path)
        canvas_slot.save(os.path.join(EXPORT_DIR, f"logo_{slug}_watch_188x25.png"))

        # Generate exact matching 4x SDF black outline (198x35 at x=126, y=36 for logo at x=131, y=41 with scale=0.9, pivot=(0.5, 1.0))
        outline_slot = make_thin_black_outline_4x_sdf(
            canvas_slot.split()[3],
            pad=5,
            scale_factor=0.9,
            pivot=(0.5, 1.0),
            box_origin_1x=(126, 36),
            orig_origin_1x=(131, 41),
            radius_px=1.25
        )
        drawable_outline_path = os.path.join(DRAWABLE_DIR, f"logo_{slug}_outline.png")
        outline_slot.save(drawable_outline_path)
        outline_slot.save(os.path.join(EXPORT_DIR, f"logo_{slug}_outline_198x35.png"))

        print(f"{word:10s}: 4x={hr.width:4d}x100 | 1x_unscaled={w_1x_prop:3d}x25 | watch_scaled={target_w:3d}x{target_h:2d} (in {SLOT_W}x{SLOT_H} drawable, +{ (target_w/170.0 - 1)*100:.1f}% vs CASINO)")

    # Build a crisp high-resolution visual showcase card in ARTIFACT_DIR
    all_words = ["CASINO"] + words
    card_w = 1400
    row_h = 155
    header_h = 90
    card_h = header_h + len(all_words) * row_h + 40
    card = Image.new("RGBA", (card_w, card_h), (14, 17, 22, 255))
    draw = ImageDraw.Draw(card)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((40, 28), "G-SHARK WORDMARK COLLECTION — MICROGRAMMA BOLD EXTENDED (4x MASTER)", fill=(230, 235, 245, 255), font=font_title)
    draw.line([(40, 72), (card_w - 40, 72)], fill=(45, 52, 65, 255), width=2)

    for idx, w in enumerate(all_words):
        y_top = header_h + idx * row_h
        is_ref = (w == "CASINO")
        box_bg = (24, 30, 40, 255) if is_ref else (20, 24, 32, 255)
        border_col = (70, 130, 200, 255) if is_ref else (42, 48, 60, 255)
        draw.rounded_rectangle([40, y_top, card_w - 40, y_top + row_h - 16], radius=10, fill=box_bg, outline=border_col, width=2)

        hr_img = rendered_highres[w]
        tag = "REFERENCE (ORIGINAL)" if is_ref else f"ALTERNATE #{idx}"
        tag_col = (100, 180, 255, 255) if is_ref else (150, 165, 185, 255)
        draw.text((64, y_top + 22), w, fill=(255, 255, 255, 255), font=font_label)
        draw.text((64, y_top + 48), tag, fill=tag_col, font=font_sub)
        draw.text((64, y_top + 70), f"{hr_img.width} × {hr_img.height} px", fill=(115, 125, 145, 255), font=font_sub)

        # Paste the 100px-tall wordmark at 1:1 scale on the right side (centered vertically in the row)
        logo_x = 290
        logo_y = y_top + (row_h - 16 - 100) // 2
        # Subtle cap-height guide lines behind the logo
        draw.line([(logo_x - 15, logo_y + 1), (card_w - 65, logo_y + 1)], fill=(35, 45, 58, 255), width=1)
        draw.line([(logo_x - 15, logo_y + 95), (card_w - 65, logo_y + 95)], fill=(35, 45, 58, 255), width=1)

        card.alpha_composite(hr_img, (logo_x, logo_y))

    showcase_path = os.path.join(ARTIFACT_DIR, "casino_alternate_logos_showcase.png")
    card.save(showcase_path)
    print(f"\nSaved showcase card to {showcase_path}")


if __name__ == "__main__":
    main()
