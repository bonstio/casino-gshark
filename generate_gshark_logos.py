#!/usr/bin/env python3
"""Processes the user-attached G-SHARK alternate logos into 220x45 watch drawables and 228x53 4x SDF outlines."""

import math
import os
from PIL import Image, ImageDraw, ImageFont

ATTACHED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
EXPORT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/exported_logo"
DRAWABLE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/app/src/main/res/drawable"


def make_thin_black_outline(alpha_1x, pad=4, radius_px=1.25):
    """
    Exact 4x Euclidean distance field outline generator from generate_logo_outlines.py.
    Given a 220x45 1x alpha image, returns a 228x53 RGBA black outline image.
    """
    S = 4
    w0, h0 = alpha_1x.size
    W1 = w0 + 2 * pad
    H1 = h0 + 2 * pad
    W4, H4 = W1 * S, H1 * S

    canvas_4x = Image.new("L", (W4, H4), 0)
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

    # The 5 attached user logos (at most 220x45, same as existing logo_gshark.png)
    items = [
        ("G-SPOT", "gspot", "gspot.png"),
        ("G-SNACK", "gsnack", "gsnack.png"),
        ("G-SNOOZE", "gsnooze", "gsnooze.png"),
        ("G-SQUAWK", "gsquawk", "gsquawk.png"),
        ("G-SLOTH", "gsloth", "gsloth.png"),
    ]

    MAX_W, MAX_H = 220, 45

    orig_1x = Image.open(os.path.join(DRAWABLE_DIR, "logo_gshark.png")).convert("RGBA")
    rendered_1x = {"G-SHARK": orig_1x}
    rendered_src = {"G-SHARK": Image.open(os.path.dirname(os.path.abspath(__file__)) + "/cleaned_user_gshark.png").convert("RGBA")}

    for label, slug, fname in items:
        src_path = os.path.join(ATTACHED_DIR, fname)
        src = Image.open(src_path).convert("RGBA")
        # Crop to exact non-zero alpha bbox first
        bbox = src.split()[3].getbbox()
        src = src.crop(bbox)
        sw, sh = src.size

        # Scale down proportionally so width <= 220 and height <= 45
        scale = min(MAX_W / float(sw), MAX_H / float(sh))
        tw = max(1, int(round(sw * scale)))
        th = max(1, int(round(sh * scale)))
        assert tw <= MAX_W and th <= MAX_H

        resized = src.resize((tw, th), Image.Resampling.LANCZOS)
        r, g, b, a = resized.split()
        # Ensure pure white RGB channels and crisp alpha
        a = a.point(lambda p: min(255, int(round(p * 1.06))) if p > 8 else 0)
        white_1x = Image.merge("RGBA", (
            Image.new("L", (tw, th), 255),
            Image.new("L", (tw, th), 255),
            Image.new("L", (tw, th), 255),
            a,
        ))

        # Place centered horizontally and bottom-aligned (or centered vertically) in 220x45 canvas
        # Note: in logo_gshark.png (220x45), the bottom of the arc touches y=45 and top touches y=0.
        # Bottom-aligning at y = 45 - th keeps the lower bezel curve at the exact same radius/baseline!
        slot_1x = Image.new("RGBA", (MAX_W, MAX_H), (0, 0, 0, 0))
        px = (MAX_W - tw) // 2
        py = MAX_H - th
        slot_1x.paste(white_1x, (px, py))

        # Generate 228x53 4x SDF black outline
        outline_1x = make_thin_black_outline(slot_1x.split()[3], pad=4, radius_px=1.25)

        # Save to drawable/ and exported_logo/
        slot_1x.save(os.path.join(DRAWABLE_DIR, f"logo_{slug}.png"))
        outline_1x.save(os.path.join(DRAWABLE_DIR, f"logo_{slug}_outline.png"))

        slot_1x.save(os.path.join(EXPORT_DIR, f"logo_{slug}_1x_220x45.png"))
        outline_1x.save(os.path.join(EXPORT_DIR, f"logo_{slug}_outline_228x53.png"))
        src.save(os.path.join(EXPORT_DIR, f"logo_{slug}_attached_master.png"))

        rendered_1x[label] = slot_1x
        rendered_src[label] = src
        print(f"{label:10s}: src={sw:3d}x{sh:3d}px -> 1x_scaled={tw:3d}x{th:2d}px in 220x45 slot (+outline 228x53)")

    # Build a dark-backed visual showcase comparison card in ARTIFACT_DIR
    all_labels = ["G-SHARK"] + [it[0] for it in items]
    card_w = 1100
    row_h = 140
    header_h = 90
    card_h = header_h + len(all_labels) * row_h + 30
    card = Image.new("RGBA", (card_w, card_h), (14, 17, 22, 255))
    draw = ImageDraw.Draw(card)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((40, 26), "BOTTOM BEZEL LOGOS — ATTACHED ASSETS (SCALED TO <= 220×45 AT 1x)", fill=(230, 235, 245, 255), font=font_title)
    draw.line([(40, 68), (card_w - 40, 68)], fill=(45, 52, 65, 255), width=2)

    logo_x = 360
    disp_w, disp_h = 660, 135  # 3x display of the 220x45 watch slot so 1x sizing proportions are shown 1:1

    for idx, label in enumerate(all_labels):
        y_top = header_h + idx * row_h
        is_ref = (label == "G-SHARK")
        box_bg = (24, 30, 40, 255) if is_ref else (20, 24, 32, 255)
        border_col = (186, 250, 8, 200) if is_ref else (42, 48, 60, 255)
        draw.rounded_rectangle([40, y_top, card_w - 40, y_top + row_h - 14], radius=10, fill=box_bg, outline=border_col, width=2)

        s1 = rendered_1x[label]
        bb1 = s1.split()[3].getbbox()
        w1 = bb1[2] - bb1[0]
        h1 = bb1[3] - bb1[1]

        draw.text((64, y_top + 22), label, fill=(255, 255, 255, 255), font=font_label)
        draw.text((64, y_top + 48), "DEFAULT" if is_ref else f"OPTION #{idx}", fill=(186, 250, 8, 255) if is_ref else (100, 195, 255, 255), font=font_sub)
        draw.text((64, y_top + 72), f"1x watch size: {w1} × {h1} px (max 220×45)", fill=(150, 160, 180, 255), font=font_sub)

        # Draw 220px width boundaries (at 2.5x = 550px wide)
        S_DISP = 2.5
        slot_disp_w = int(MAX_W * S_DISP)
        slot_disp_h = int(MAX_H * S_DISP)
        draw.line([(logo_x, y_top + 8), (logo_x, y_top + row_h - 22)], fill=(65, 80, 100, 180), width=1)
        draw.line([(logo_x + slot_disp_w, y_top + 8), (logo_x + slot_disp_w, y_top + row_h - 22)], fill=(65, 80, 100, 180), width=1)

        # Render from high-res source at exact 2.5x of 1x size for crisp showcase display
        src_im = rendered_src[label]
        disp_tw = max(1, int(round(w1 * S_DISP)))
        disp_th = max(1, int(round(h1 * S_DISP)))
        disp_im = src_im.resize((disp_tw, disp_th), Image.Resampling.LANCZOS)
        r, g, b, a = disp_im.split()
        tinted = Image.merge("RGBA", (
            Image.new("L", disp_im.size, 186),
            Image.new("L", disp_im.size, 250),
            Image.new("L", disp_im.size, 8),
            a,
        ))
        px_d = logo_x + (slot_disp_w - disp_tw) // 2
        py_d = y_top + (row_h - 14 - slot_disp_h) // 2 + (slot_disp_h - disp_th)
        card.alpha_composite(tinted, (px_d, py_d))

    showcase_path = os.path.join(ARTIFACT_DIR, "gshark_attached_logos_showcase.png")
    card.save(showcase_path)
    print(f"\nSaved showcase card to {showcase_path}")


if __name__ == "__main__":
    main()
