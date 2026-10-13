import os, math
from PIL import Image, ImageFilter

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/app/src/main/res/drawable"
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

def make_thin_black_outline(alpha_1x, pad, scale_factor=1.0, pivot=None, box_origin_1x=(0, 0), orig_origin_1x=(0, 0), radius_px=1.25):
    """
    Given a 1x alpha image `alpha_1x` (or scaled by `scale_factor` around `pivot`),
    places it into a padded canvas at 4x resolution, computes an exact Euclidean
    distance field out to `radius_px`, and downsamples to 1x to produce a razor-sharp
    anti-aliased thin black outline RGBA image.
    """
    S = 4
    w0, h0 = alpha_1x.size
    W1 = w0 + 2 * pad
    H1 = h0 + 2 * pad
    W4, H4 = W1 * S, H1 * S

    canvas_4x = Image.new("L", (W4, H4), 0)
    if scale_factor != 1.0 and pivot is not None:
        # Compute exact scaled size and position in 4x coordinates
        sw4 = int(round(w0 * scale_factor * S))
        sh4 = int(round(h0 * scale_factor * S))
        scaled_a = alpha_1x.resize((sw4, sh4), Image.Resampling.LANCZOS)
        # Pivot in 1xwatchface coordinates:
        px_wf = orig_origin_1x[0] + pivot[0] * w0
        py_wf = orig_origin_1x[1] + pivot[1] * h0
        # Top-left of scaled image in 1x watchface coordinates:
        x_tl_wf = px_wf - pivot[0] * (w0 * scale_factor)
        y_tl_wf = py_wf - pivot[1] * (h0 * scale_factor)
        # Convert to 4x padded canvas coordinates (where box_origin_1x is (0,0))
        ox4 = int(round((x_tl_wf - box_origin_1x[0]) * S))
        oy4 = int(round((y_tl_wf - box_origin_1x[1]) * S))
        canvas_4x.paste(scaled_a, (ox4, oy4))
    else:
        scaled_a = alpha_1x.resize((w0 * S, h0 * S), Image.Resampling.LANCZOS)
        canvas_4x.paste(scaled_a, (pad * S, pad * S))

    # Fast exact 2D Euclidean distance dilation at 4x using disk kernel offsets
    R4 = radius_px * S
    R_int = int(math.ceil(R4 + 1.0))
    src_bytes = canvas_4x.tobytes()
    out_bytes = bytearray(W4 * H4)

    # Precompute circular kernel offsets and their Euclidean distance in 1x pixels
    offsets = []
    for dy in range(-R_int, R_int + 1):
        for dx in range(-R_int, R_int + 1):
            d1x = math.hypot(dx, dy) / float(S)
            if d1x <= radius_px + 0.35:
                # Smooth anti-aliased falloff at radius_px
                cov = max(0.0, min(1.0, (radius_px + 0.25 - d1x) / 0.5))
                if cov > 0.0:
                    offsets.append((dx, dy, int(round(cov * 255.0))))

    # Gather all foreground seed pixels (src > 32)
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

# 1. CASINO logo outline:
#    CasinoLogo is at x=140, y=41, w=170, h=25, pivotX=0.5, pivotY=1.0, scaleX=0.9, scaleY=0.9
#    We pad by 5px on each side -> box at x=135, y=36, w=180, h=35
casino_im = Image.open(os.path.join(OUTPUT_DIR, "logo_casino.png")).convert("RGBA")
casino_outline = make_thin_black_outline(
    casino_im.split()[3],
    pad=5,
    scale_factor=0.9,
    pivot=(0.5, 1.0),
    box_origin_1x=(135, 36),
    orig_origin_1x=(140, 41),
    radius_px=1.25
)
casino_outline.save(os.path.join(OUTPUT_DIR, "logo_casino_outline.png"))

# 2. G-SHARK logo outline:
#    GSharkLogo is at x=115, y=372, w=220, h=45 (scale 1.0)
#    We pad by 4px on each side -> box at x=111, y=368, w=228, h=53
gshark_im = Image.open(os.path.join(OUTPUT_DIR, "logo_gshark.png")).convert("RGBA")
gshark_outline = make_thin_black_outline(
    gshark_im.split()[3],
    pad=4,
    scale_factor=1.0,
    pivot=None,
    radius_px=1.25
)
gshark_outline.save(os.path.join(OUTPUT_DIR, "logo_gshark_outline.png"))

# 3. WEAR OS logo outline:
#    WearOsLogo is rendered at x=38, y=215, w=26, h=20
#    Since logo_wear_os.png has max alpha 178, normalize its alpha to 0..255 at 26x20 so the black outline is full strength
wear_im = Image.open(os.path.join(OUTPUT_DIR, "logo_wear_os.png")).convert("RGBA").resize((26, 20), Image.Resampling.LANCZOS)
wear_a = wear_im.split()[3].point(lambda p: min(255, int(round(p * 255.0 / 178.0))))
wear_outline = make_thin_black_outline(
    wear_a,
    pad=4,
    scale_factor=1.0,
    pivot=None,
    radius_px=1.25
)
wear_outline.save(os.path.join(OUTPUT_DIR, "logo_wear_os_outline.png"))

print("Generated logo_casino_outline.png (180x35), logo_gshark_outline.png (228x53), and logo_wear_os_outline.png (34x28)!")
