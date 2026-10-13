import os, math, random, colorsys
from PIL import Image, ImageDraw, ImageFilter

# Import shared geometry & helpers from generate_industrial_gradient_mocks
import generate_industrial_gradient_mocks as base

OUTPUT_DIR = base.OUTPUT_DIR
ARTIFACT_DIR = base.ARTIFACT_DIR
W_m, H_m = base.W_m, base.H_m
pitch_a = base.pitch_a
ndotl_tile = base.ndotl_tile
AO_tile = base.AO_tile
spec_tile = base.spec_tile
brush_rows = base.brush_rows
dial_mask = base.dial_mask
edge_sh = base.edge_sh
start_overlay = base.start_overlay
user_shadow = base.user_shadow

# Precompute the 2x (900x900 -> 450x450) stationary 3D Micro-Knurl + Brushed Metal alpha/glint layer
# Inside dial_mask (r=206, 19..431):
#   mult(x,y) = (0.54 + 0.72 * nd) * ao + b_streak  in [0.22, 1.30]
#   With M_MAX = 1.34, darkness factor f = mult / M_MAX in [0.16, 0.97]
#   So alpha_dark = 1.0 - f in [0.03, 0.84], plus subtle 3D facet specular glint on pyramid crests.
M_MAX = 1.34

diff_mult_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
spec_facet_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    for px in range(pitch_a):
        nd = ndotl_tile[py][px]
        ao = AO_tile[py][px]
        diff_mult_tile[py][px] = (0.54 + 0.72 * nd) * ao
        spec_facet_tile[py][px] = 14.0 * spec_tile[py][px] * ao

knurl_bytes_2x = bytearray(W_m * H_m * 4)
for y in range(36, 864):
    py = y % pitch_a
    dm_row = diff_mult_tile[py]
    sp_row = spec_facet_tile[py]
    b_streak = brush_rows[y]
    dy_c = y - 450.0
    row_off = y * W_m * 4
    for x in range(36, 864):
        dx_c = x - 450.0
        if dx_c*dx_c + dy_c*dy_c <= 414.0**2:
            px = x % pitch_a
            mult = max(0.15, min(M_MAX, dm_row[px] + b_streak))
            a_dark = 1.0 - (mult / M_MAX)
            sp = sp_row[px]  # 0..14
            # Combine darken (0,0,0, a_dark) and subtle facet glint (255,255,255, sp/255)
            a_sp = sp / 255.0
            a_out = a_dark + a_sp * (1.0 - a_dark)
            if a_out > 0.001:
                c_val = int(min(255, max(0, round((255.0 * a_sp) / a_out))))
                a_u8 = int(min(255, max(0, round(a_out * 255.0))))
                idx = row_off + x * 4
                knurl_bytes_2x[idx] = c_val
                knurl_bytes_2x[idx+1] = c_val
                knurl_bytes_2x[idx+2] = c_val
                knurl_bytes_2x[idx+3] = a_u8

knurl_1x = Image.frombytes("RGBA", (W_m, H_m), bytes(knurl_bytes_2x)).resize((450, 450), Image.Resampling.LANCZOS)
knurl_clipped = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
knurl_clipped.paste(knurl_1x, (0, 0), dial_mask)
knurl_clipped.alpha_composite(edge_sh)

# Precompute inverse dial_mask (opaque outside r=206, transparent inside r=206)
inv_dial_mask = dial_mask.point(lambda p: 255 - p)

def generate_gyro_pair(
    name_slug,
    h_light_deg, s_light, v_light,
    h_dark_deg,  s_dark,  v_dark,
    ch_rgb, outline_col, bezel_fill,
    spec_tint=(0.85, 0.95, 1.0)
):
    """
    Produces:
      1. bg_ind_grad_<name_slug>.png: Full 450x450 rotatable/translating off-center radial + linear
         hue-shifted gradient disc (boosted by M_MAX + focal specular glow so it shines through the knurl).
      2. bg_ind_frame_<name_slug>.png: Static 450x450 top layer containing the outer bezel ring (outside r=206),
         stationary 3D micro-knurl waffle grid + brushed streaks + inner bezel shadow (inside r=206),
         and opaque recessed LCD chambers + 3D sub-dial + START + directional inner shadows.
    """
    # 1. Generate full 450x450 gradient plate (at 1x directly since it is a smooth gradient!)
    gx, gy = 138.0, 124.0
    max_rad = 300.0
    dir_x, dir_y = 0.68, 0.733
    sr_t, sg_t, sb_t = spec_tint

    lut_rgb = []
    for k in range(256):
        t = k / 255.0
        t_hue = t ** 0.95
        t_val = t ** 1.05
        h_deg = h_light_deg + (h_dark_deg - h_light_deg) * t_hue
        s_val = s_light + (s_dark - s_light) * t
        v_val = v_light + (v_dark - v_light) * t_val
        r_f, g_f, b_f = colorsys.hsv_to_rgb((h_deg % 360.0) / 360.0, s_val, v_val)
        # Boost by M_MAX and add the warm/cool off-center specular glow near t=0
        sp_glow = 18.0 * ((1.0 - t) ** 1.8)
        br = min(255, max(0, int(round(r_f * 255.0 * M_MAX + sp_glow * sr_t))))
        bg_c = min(255, max(0, int(round(g_f * 255.0 * M_MAX + sp_glow * sg_t))))
        bb = min(255, max(0, int(round(b_f * 255.0 * M_MAX + sp_glow * sb_t))))
        lut_rgb.append((br, bg_c, bb))

    grad_bytes = bytearray(450 * 450 * 4)
    for y in range(12, 438):
        dy_f = y - gy
        dy_c = y - 225.0
        row_off = y * 450 * 4
        for x in range(12, 438):
            dx_c = x - 225.0
            if dx_c*dx_c + dy_c*dy_c <= 212.0**2:
                dx_f = x - gx
                r_dist = math.hypot(dx_f, dy_f) / max_rad
                lin_proj = max(0.0, (dx_f * dir_x + dy_f * dir_y) / max_rad)
                t = max(0.0, min(1.0, 0.72 * r_dist + 0.28 * lin_proj))
                br, bg_c, bb = lut_rgb[int(round(t * 255.0))]
                idx = row_off + x * 4
                grad_bytes[idx] = br
                grad_bytes[idx+1] = bg_c
                grad_bytes[idx+2] = bb
                grad_bytes[idx+3] = 255

    grad_img = Image.frombytes("RGBA", (450, 450), bytes(grad_bytes))
    grad_img.save(os.path.join(OUTPUT_DIR, f"bg_ind_grad_{name_slug}.png"))

    # 2. Generate static top frame + stationary knurl overlay
    bezel_full = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    base.draw_bezel_and_track(ImageDraw.Draw(bezel_full), bezel_fill)
    # Punch out the r=206 dial aperture so the rotating gradient shows through
    frame_img = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    frame_img.paste(bezel_full, (0, 0), inv_dial_mask)

    # Composite the stationary 3D micro-knurl + brushed metal + bezel recess shadow over the aperture
    frame_img.alpha_composite(knurl_clipped)

    # Composite the opaque recessed LCD chambers, sub-dial, START text, and inner shadows
    base.draw_chambers_and_subdial(frame_img, ch_rgb, outline_col)
    frame_img.alpha_composite(start_overlay)
    frame_img.alpha_composite(user_shadow)

    frame_img.save(os.path.join(OUTPUT_DIR, f"bg_ind_frame_{name_slug}.png"))
    return grad_img, frame_img

THEMES = [
    ("cyan",    183.0, 0.80, 0.58, 199.0, 0.90, 0.14, (8, 19, 26),  (38, 76, 94, 255),  (14, 22, 28, 255), (0.85, 0.95, 1.0)),
    ("lime",    69.0,  0.84, 0.54, 87.0,  0.88, 0.13, (14, 20, 9),  (66, 84, 34, 255),  (18, 22, 14, 255), (0.85, 0.95, 1.0)),
    ("blue",    207.0, 0.84, 0.62, 225.0, 0.92, 0.14, (8, 14, 28),  (42, 66, 110, 255), (14, 18, 28, 255), (0.85, 0.95, 1.0)),
    ("red",     358.0, 0.84, 0.58, 340.0, 0.92, 0.14, (24, 8, 11),  (98, 36, 44, 255),  (26, 12, 14, 255), (1.0, 0.86, 0.88)),
    ("orange",  28.0,  0.86, 0.60, 11.0,  0.92, 0.14, (25, 13, 7),  (104, 56, 26, 255), (26, 16, 11, 255), (1.0, 0.92, 0.82)),
    ("magenta", 320.0, 0.84, 0.56, 296.0, 0.92, 0.14, (22, 8, 22),  (92, 36, 86, 255),  (24, 12, 24, 255), (0.98, 0.86, 1.0)),
    ("silver",  200.0, 0.08, 0.60, 218.0, 0.22, 0.15, (16, 19, 23), (74, 82, 94, 255),  (20, 23, 28, 255), (0.95, 0.98, 1.0)),
]

for slug, hl, sl, vl, hd, sd, vd, ch, out_c, bez_c, sp_t in THEMES:
    g_im, f_im = generate_gyro_pair(slug, hl, sl, vl, hd, sd, vd, ch, out_c, bez_c, sp_t)
    if slug == "cyan":
        # Save a test composite rotated by +95 deg so we can verify the gyro effect visually
        rot_g = g_im.rotate(95, resample=Image.Resampling.BICUBIC)
        comp = rot_g.copy()
        comp.alpha_composite(f_im)
        comp.alpha_composite(base.build_foreground_overlay((0, 229, 255), (0, 229, 255)))
        comp.save(os.path.join(ARTIFACT_DIR, "test_gyro_cyan_rotated.png"))

print("Generated all 7 bg_ind_grad_* and bg_ind_frame_* gyro layer pairs!")
