import os, math, random, colorsys, time
from PIL import Image, ImageDraw, ImageFilter, ImageChops

t0 = time.time()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")
EXPORT_DIR = os.path.join(BASE_DIR, "exported_backgrounds_for_photoshop")

cx, cy = 225.0, 225.0
scx, scy = 352.0, 323.0
r_outer = 38.0 * 1.3   # 49.4px
r_inner = 30.5 * 1.3   # 39.65px
gap_dist = 9.6
r_cut = r_outer + gap_dist  # 59.0px

scale = 2
W, H = 450 * scale, 450 * scale
cx2, cy2 = cx * scale, cy * scale
scx2, scy2 = scx * scale, scy * scale
ro2, ri2, rcut2 = r_outer * scale, r_inner * scale, r_cut * scale
r_c2 = 12.0 * scale

light_dir_x, light_dir_y = -0.60, -0.80  # Light source at ~10:30 upper-left

def compute_chamber_masks_and_bevels(x1, y1, x2, y2, r_corner, has_cut=False, fillet_r=32.0):
    cx_r = (x1 + x2) / 2.0
    cy_r = (y1 + y2) / 2.0
    hx = (x2 - x1) / 2.0 - r_corner
    hy = (y2 - y1) / 2.0 - r_corner
    k = float(fillet_r)

    m_in = bytearray(W * H)
    m_trench = bytearray(W * H)
    m_bev_lit = bytearray(W * H)
    m_bev_sh = bytearray(W * H)

    ix1 = max(0, int(x1 - 14))
    ix2 = min(W, int(x2 + 14))
    iy1 = max(0, int(y1 - 14))
    iy2 = min(H, int(y2 + 14))

    for y in range(iy1, iy2):
        dy_r = y - cy_r
        dy0 = abs(dy_r) - hy
        dy = dy0 if dy0 > 0.0 else 0.0
        dy_sq = dy * dy
        if has_cut:
            dy_sc = y - scy2
            dy_sc_sq = dy_sc * dy_sc
        row_off = y * W
        for x in range(ix1, ix2):
            dx_r = x - cx_r
            dx0 = abs(dx_r) - hx
            dx = dx0 if dx0 > 0.0 else 0.0
            m_xy = dx0 if dx0 > dy0 else dy0
            d_corner = math.sqrt(dx * dx + dy_sq)
            sdf_rect = d_corner + (m_xy if m_xy < 0.0 else 0.0) - r_corner

            if d_corner > 1e-4:
                gx_r = (dx / d_corner) * (1.0 if dx_r >= 0 else -1.0)
                gy_r = (dy / d_corner) * (1.0 if dy_r >= 0 else -1.0)
            else:
                if dx0 > dy0:
                    gx_r = 1.0 if dx_r >= 0 else -1.0
                    gy_r = 0.0
                else:
                    gx_r = 0.0
                    gy_r = 1.0 if dy_r >= 0 else -1.0

            if not has_cut:
                sdf_c = sdf_rect
                nx, ny = gx_r, gy_r
            else:
                dx_sc = x - scx2
                dist_sc = math.sqrt(dx_sc * dx_sc + dy_sc_sq)
                sdf_excl = rcut2 - dist_sc
                u = sdf_rect + k
                if u < 0.0: u = 0.0
                v = sdf_excl + k
                if v < 0.0: v = 0.0
                mx = sdf_rect if sdf_rect > sdf_excl else sdf_excl
                mn = mx if mx < -k else -k
                uv_len = math.sqrt(u * u + v * v)
                sdf_c = mn + uv_len
                if dist_sc > 1e-4:
                    gx_e = -dx_sc / dist_sc
                    gy_e = -dy_sc / dist_sc
                else:
                    gx_e, gy_e = 0.0, 0.0
                if uv_len > 1e-4:
                    nx = (u * gx_r + v * gx_e) / uv_len
                    ny = (u * gy_r + v * gy_e) / uv_len
                elif sdf_rect > sdf_excl:
                    nx, ny = gx_r, gy_r
                else:
                    nx, ny = gx_e, gy_e

            idx = row_off + x
            a_in = 0.5 - sdf_c / 1.4
            if a_in > 0.0:
                m_in[idx] = 255 if a_in >= 1.0 else int(a_in * 255.0)

            if -0.5 < sdf_c < 4.5:
                tr = math.exp(-((sdf_c - 1.6) / 1.6) ** 2)
                m_trench[idx] = int(min(255.0, tr * 255.0))

            if -4.5 < sdf_c < 2.0:
                rim_w = math.exp(-((sdf_c + 1.2) / 1.8) ** 2)
                illum = nx * (-light_dir_x) + ny * (-light_dir_y)
                if illum >= 0.0:
                    lit = (illum ** 1.15) * rim_w
                    m_bev_lit[idx] = int(min(255.0, lit * 255.0))
                else:
                    sh = ((-illum) ** 1.1) * rim_w
                    m_bev_sh[idx] = int(min(255.0, sh * 255.0))

    return (
        Image.frombytes("L", (W, H), bytes(m_in)),
        Image.frombytes("L", (W, H), bytes(m_trench)),
        Image.frombytes("L", (W, H), bytes(m_bev_lit)),
        Image.frombytes("L", (W, H), bytes(m_bev_sh)),
    )

print("Precomputing 2x 3D chamber masks & bevel normals (pods vs center chamber)...")
QUAD_PODS = [(72, 138), (152, 218), (232, 298), (312, 378)]
QUAD_Y1, QUAD_Y2 = 90, 168

# 1. Pods (ONLY bottom slot5 pod baked into bg_lcd_*.png; quad pods are separate in quad_chamber_*.png for digital mode only!)
pods_in = Image.new("L", (W, H), 0)
pods_trench = Image.new("L", (W, H), 0)
pods_bev_lit = Image.new("L", (W, H), 0)
pods_bev_sh = Image.new("L", (W, H), 0)

pod_specs = [(70 * scale, 302 * scale, 305 * scale, 358 * scale, True)]

for x1, y1, x2, y2, has_cut in pod_specs:
    m_in, m_tr, m_bl, m_bs = compute_chamber_masks_and_bevels(x1, y1, x2, y2, r_c2, has_cut=has_cut)
    pods_in = ImageChops.lighter(pods_in, m_in)
    pods_trench = ImageChops.lighter(pods_trench, m_tr)
    pods_bev_lit = ImageChops.lighter(pods_bev_lit, m_bl)
    pods_bev_sh = ImageChops.lighter(pods_bev_sh, m_bs)

# 2. Main center time chamber baked into center_chamber_0..16.png
main_in, main_trench, main_bev_lit, main_bev_sh = compute_chamber_masks_and_bevels(
    70 * scale, 178 * scale, 380 * scale, 284 * scale, r_c2, has_cut=True
)

def build_dual_stage_shadow_layer(mask_in_L):
    inv_in = mask_in_L.point(lambda p: 255 - p)
    sh1 = Image.new("L", (W, H), 255)
    sh1.paste(inv_in, (int(3.5 * scale), int(4.5 * scale)))
    sh1 = sh1.filter(ImageFilter.GaussianBlur(2.4 * scale))

    sh2 = Image.new("L", (W, H), 255)
    sh2.paste(inv_in, (int(-3.5 * scale), int(5.5 * scale)))
    sh2 = sh2.filter(ImageFilter.GaussianBlur(5.0 * scale))

    sh_ao = inv_in.filter(ImageFilter.GaussianBlur(2.0 * scale))

    in_b = mask_in_L.tobytes()
    s1_b = sh1.tobytes()
    s2_b = sh2.tobytes()
    ao_b = sh_ao.tobytes()

    sh_bytes = bytearray(W * H)
    for i in range(W * H):
        mv = in_b[i]
        if mv:
            v1 = (s1_b[i] * 175 + s2_b[i] * 115 + ao_b[i] * 70) // 255
            sh_bytes[i] = min(230, (mv * v1) // 255)
    sh_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh_layer.putalpha(Image.frombytes("L", (W, H), bytes(sh_bytes)))
    return sh_layer

pods_shadow_2x = build_dual_stage_shadow_layer(pods_in)
main_shadow_2x = build_dual_stage_shadow_layer(main_in)

pods_trench_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pods_trench_layer.putalpha(pods_trench.point(lambda p: (p * 115) // 255))

main_trench_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
main_trench_layer.putalpha(main_trench.point(lambda p: (p * 115) // 255))

# Faint default honeycomb wafer overlay at 900x900
tex_scr = Image.open(os.path.join(OUTPUT_DIR, "tex_screen_hex_light.png")).convert("RGBA")
tex_bot = Image.open(os.path.join(OUTPUT_DIR, "tex_bottom_hex_light.png")).convert("RGBA")
tex_quad = Image.open(os.path.join(OUTPUT_DIR, "tex_quad_hex_light.png")).convert("RGBA")
hc_450 = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
hc_450.alpha_composite(tex_quad, (70, 90))
hc_450.alpha_composite(tex_scr, (70, 178))
hc_450.alpha_composite(tex_bot, (70, 302))
hc_900_L = hc_450.resize((W, H), Image.Resampling.LANCZOS).split()[3]

def make_ar_layer_for_mask(mask_in_L, ar_gain=0.45):
    in_b = mask_in_L.tobytes()
    ar_bytes = bytearray(W * H * 4)
    for y in range(70 * scale, 365 * scale):
        row_off = y * W
        for x in range(68 * scale, 405 * scale):
            i = row_off + x
            mv = in_b[i]
            if mv:
                u = (x * 0.72 + y * 0.69) / float(W)
                sh1 = math.exp(-((u - 0.55) / 0.08) ** 2) * 36.0 * ar_gain
                sh2 = math.exp(-((u - 0.67) / 0.03) ** 2) * 24.0 * ar_gain
                a_val = int(min(255.0, (sh1 + sh2) * (mv / 255.0)))
                if a_val > 0:
                    idx = i * 4
                    ar_bytes[idx] = 175
                    ar_bytes[idx+1] = 228
                    ar_bytes[idx+2] = 255
                    ar_bytes[idx+3] = a_val
    return Image.frombytes("RGBA", (W, H), bytes(ar_bytes))

AR_PODS_STD = make_ar_layer_for_mask(pods_in, 0.45)
AR_PODS_GLOSS = make_ar_layer_for_mask(pods_in, 0.75)
AR_MAIN_STD = make_ar_layer_for_mask(main_in, 0.45)
AR_MAIN_GLOSS = make_ar_layer_for_mask(main_in, 0.75)

# Load 'START' text overlay (pure alpha-only 2x resize so no black fringe is introduced)
start_cache_path = os.path.join(BASE_DIR, "start_overlay_cache.png")
start_1x = Image.open(start_cache_path).convert("RGBA")
start_a_2x = start_1x.split()[3].resize((W, H), Image.Resampling.BILINEAR)
start_std_2x = Image.new("RGBA", (W, H), (105, 118, 136, 0))
start_std_2x.putalpha(start_a_2x)
start_bright_2x = Image.new("RGBA", (W, H), (130, 145, 165, 0))
start_bright_2x.putalpha(start_a_2x)

# ==============================================================================
# GENERATE ENHANCED BEZEL BORDER OVERLAY (bg_border_classic.png: EXACT 22..428)
# ==============================================================================
print("Generating enhanced bg_border_classic.png (exact 22..428 / r=203.0px circumference)...")
R_BORDER_2X = 203.0 * scale  # 406.0px at 2x (exact 22..428 in 450x450 space)

border_bytes = bytearray(W * H * 4)
for y in range(H):
    dy_c = y - cy2
    dy_s = y - scy2
    row_off = y * W * 4
    for x in range(W):
        dx_c = x - cx2
        r_c = math.hypot(dx_c, dy_c)
        if r_c > 452.0:
            continue
        dx_s = x - scx2
        r_s = math.hypot(dx_s, dy_s)
        # Punch out the sub-dial flange so the sub-dial sits cleanly on top
        if r_s <= ro2 - 0.5:
            continue

        idx = row_off + x * 4
        if r_c >= R_BORDER_2X - 0.6:
            # Outer black bezel region (outside 22..428)
            # 3D directional chamfer strictly on the bezel rim (r_c in 406.0 .. 409.5) so opening circumference is unchanged
            ldot = (dx_c * (-light_dir_x) + dy_c * (-light_dir_y)) / max(r_c, 1.0)
            rim_w = math.exp(-((r_c - (R_BORDER_2X + 1.2)) / 1.35) ** 2)
            if ldot < 0.0:
                lit = ((-ldot) ** 1.1) * rim_w
                rv = 36.0 * rim_w + 92.0 * lit
                gv = 44.0 * rim_w + 108.0 * lit
                bv = 54.0 * rim_w + 128.0 * lit
            else:
                sh = (1.0 - 0.45 * ldot) * rim_w
                rv = 34.0 * sh
                gv = 42.0 * sh
                bv = 52.0 * sh

            edge_a = 1.0
            if r_c < R_BORDER_2X + 0.6:
                edge_a = max(0.0, min(1.0, (r_c - (R_BORDER_2X - 0.6)) / 1.2))

            border_bytes[idx]   = int(max(0, min(255, rv)))
            border_bytes[idx+1] = int(max(0, min(255, gv)))
            border_bytes[idx+2] = int(max(0, min(255, bv)))
            border_bytes[idx+3] = int(edge_a * 255.0)
        elif r_c > R_BORDER_2X - 9.0 and r_s > ro2 + 3.0:
            # Subtle inner bezel recess shadow inside (22..428)
            ldot = (dx_c * (-light_dir_x) + dy_c * (-light_dir_y)) / max(r_c, 1.0)
            dist_in = R_BORDER_2X - r_c
            sh_falloff = max(0.0, min(1.0, (9.0 - dist_in) / 9.0)) ** 1.7
            dir_boost = 1.0 + 0.35 * ldot
            sh_alpha = int(min(155.0, sh_falloff * 125.0 * dir_boost))
            border_bytes[idx+3] = sh_alpha

border_classic_2x = Image.frombytes("RGBA", (W, H), bytes(border_bytes))
border_classic_1x = border_classic_2x.resize((450, 450), Image.Resampling.BOX)
border_classic_1x.save(os.path.join(OUTPUT_DIR, "bg_border_classic.png"))
print("Saved: bg_border_classic.png")

# ==============================================================================
# HELPERS FOR PODS, SUB-DIAL HOUSING & CENTER CHAMBER OVERLAY
# ==============================================================================
def apply_pods_and_subdial_housing_2x(
    img_2x,
    floor_rgb,
    bev_lit_rgb,
    bev_sh_rgb=(4, 6, 9),
    honeycomb_gain=0.18,
    sub_base_f=(36.0, 42.0, 52.0),
    sub_spec_f=(168.0, 186.0, 210.0),
    well_rgb=None,
    gloss_ar=False,
):
    if well_rgb is None:
        well_rgb = floor_rgb

    # 1. Outer seam trench around the 4 quad pods + bottom pod
    img_2x.alpha_composite(pods_trench_layer)

    # 2. Recessed cavity floor
    floor_layer = Image.new("RGBA", (W, H), (*floor_rgb, 0))
    floor_layer.putalpha(pods_in)
    img_2x.alpha_composite(floor_layer)

    # 3. Subtle default honeycomb wafer inside pods
    if honeycomb_gain > 0.0:
        hc_layer = Image.new("RGBA", (W, H), (190, 215, 240, 0))
        hc_alpha = ImageChops.multiply(pods_in, hc_900_L.point(lambda p: min(255, int(p * honeycomb_gain))))
        hc_layer.putalpha(hc_alpha)
        img_2x.alpha_composite(hc_layer)

    # 4. 3D directional chamfered window bevels
    sh_rim = Image.new("RGBA", (W, H), (*bev_sh_rgb, 0))
    sh_rim.putalpha(pods_bev_sh.point(lambda p: min(255, int(p * 0.95))))
    img_2x.alpha_composite(sh_rim)

    lit_rim = Image.new("RGBA", (W, H), (*bev_lit_rgb, 0))
    lit_rim.putalpha(pods_bev_lit.point(lambda p: min(255, int(p * 0.95))))
    img_2x.alpha_composite(lit_rim)

    # 5. Dual-stage recessed cavity shadow + subtle sapphire AR reflection inside pods
    img_2x.alpha_composite(pods_shadow_2x)
    img_2x.alpha_composite(AR_PODS_GLOSS if gloss_ar else AR_PODS_STD)

    # 6. 3D CNC-turned conical sub-dial flange + 4 recessed domed screws + cavity well (no static segments baked!)
    P = 240
    pcx, pcy = 120.0, 120.0
    patch_bytes = bytearray(P * P * 4)
    ar_sheen_gain = 0.85 if gloss_ar else 0.45

    r_screw_pos = (ri2 + ro2) / 2.0
    r_screw = 2.9 * 1.3 * scale
    screw_centers = []
    for deg in (45, 135, 225, 315):
        rad = math.radians(deg)
        screw_centers.append((pcx + r_screw_pos * math.cos(rad), pcy + r_screw_pos * math.sin(rad), rad + math.pi / 4.0))

    for py in range(P):
        dy = py - pcy
        for px in range(P):
            dx = px - pcx
            r = math.hypot(dx, dy)
            idx = (py * P + px) * 4

            if r > ro2 - 0.8:
                r_sh = math.hypot(dx - 3.5, dy - 5.5)
                if r_sh < ro2 + 11.0:
                    sh_a = max(0.0, min(1.0, (ro2 + 11.0 - r_sh) / 11.0)) ** 1.6
                    if r > ro2 + 0.6:
                        patch_bytes[idx+3] = int(sh_a * 175.0)
                        continue

            if r >= ri2 - 0.8 and r <= ro2 + 0.8:
                ang = math.atan2(dy, dx)
                conical = (0.5 + 0.5 * math.cos(2.0 * (ang + 2.35))) ** 2.2
                lathe = 0.96 + 0.04 * math.sin(r * 3.14159)
                ldot = (dx * (-light_dir_x) + dy * (-light_dir_y)) / max(r, 1.0)
                outer_bev = math.exp(-((r - ro2 + 1.8) / 1.8) ** 2) * (-ldot * 48.0)
                inner_bev = math.exp(-((r - ri2 - 1.8) / 1.8) ** 2) * (ldot * 58.0)

                rv = (sub_base_f[0] + (sub_spec_f[0] - sub_base_f[0]) * conical * 0.74) * lathe + outer_bev + inner_bev
                gv = (sub_base_f[1] + (sub_spec_f[1] - sub_base_f[1]) * conical * 0.74) * lathe + outer_bev + inner_bev
                bv = (sub_base_f[2] + (sub_spec_f[2] - sub_base_f[2]) * conical * 0.74) * lathe + outer_bev + inner_bev

                for sx, sy, slot_ang in screw_centers:
                    dxs, dys = px - sx, py - sy
                    rs = math.hypot(dxs, dys)
                    if rs < r_screw + 2.2:
                        if rs >= r_screw:
                            sock = (r_screw + 2.2 - rs) / 2.2
                            rv *= (1.0 - 0.65 * sock)
                            gv *= (1.0 - 0.65 * sock)
                            bv *= (1.0 - 0.65 * sock)
                        else:
                            dome = max(0.18, min(1.32, 0.72 - 0.52 * (dxs * (-light_dir_x) + dys * (-light_dir_y)) / r_screw))
                            s_dist = abs(dxs * (-math.sin(slot_ang)) + dys * math.cos(slot_ang))
                            s_len = abs(dxs * math.cos(slot_ang) + dys * math.sin(slot_ang))
                            in_slot = max(0.0, min(1.0, 1.6 - s_dist)) * max(0.0, min(1.0, r_screw - 1.8 - s_len))
                            mult = dome * (1.0 - 0.80 * in_slot)
                            rv, gv, bv = 80.0 * mult, 90.0 * mult, 104.0 * mult

                edge_a = 1.0
                if r > ro2 - 0.6:
                    edge_a = max(0.0, min(1.0, ro2 + 0.6 - r))
                patch_bytes[idx]   = int(max(0, min(255, rv)))
                patch_bytes[idx+1] = int(max(0, min(255, gv)))
                patch_bytes[idx+2] = int(max(0, min(255, bv)))
                patch_bytes[idx+3] = int(edge_a * 255.0)
                continue

            if r < ri2:
                rv, gv, bv = float(well_rgb[0]), float(well_rgb[1]), float(well_rgb[2])
                if ar_sheen_gain > 0.0:
                    u_s = (dx * 0.72 + dy * 0.69) / float(ri2)
                    sh_s = math.exp(-((u_s + 0.18) / 0.28) ** 2) * 0.16 * ar_sheen_gain
                    rv += 175.0 * sh_s
                    gv += 228.0 * sh_s
                    bv += 255.0 * sh_s

                r_cav_sh = math.hypot(dx - 6.0, dy - 8.0)
                if r_cav_sh > ri2 - 9.0:
                    cav_s = max(0.0, min(1.0, (r_cav_sh - (ri2 - 9.0)) / 12.0)) * 0.62
                    rv *= (1.0 - cav_s)
                    gv *= (1.0 - cav_s)
                    bv *= (1.0 - cav_s)

                patch_bytes[idx]   = int(max(0, min(255, rv)))
                patch_bytes[idx+1] = int(max(0, min(255, gv)))
                patch_bytes[idx+2] = int(max(0, min(255, bv)))
                patch_bytes[idx+3] = 255

    patch_img = Image.frombytes("RGBA", (P, P), bytes(patch_bytes))
    img_2x.alpha_composite(patch_img, (int(scx2 - pcx), int(scy2 - pcy)))

# Full-bleed circular mask (0, 0, 450, 450)
full_bleed_mask_1x = Image.new("L", (450, 450), 0)
ImageDraw.Draw(full_bleed_mask_1x).ellipse((0, 0, 450, 450), fill=255)

def save_bg_from_2x(img_2x, filename):
    img_1x = img_2x.resize((450, 450), Image.Resampling.BOX)
    r, g, b, _ = img_1x.split()
    out_1x = Image.merge("RGBA", (r, g, b, full_bleed_mask_1x))
    for d in (OUTPUT_DIR, EXPORT_DIR):
        if os.path.isdir(d):
            out_1x.save(os.path.join(d, filename))
    print(f"Saved full-bleed: {filename}")

def save_center_chamber_3d(idx, floor_rgb, bev_lit_rgb, bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.18, bright_start=False, gloss_ar=False):
    hi_main = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hi_main.alpha_composite(main_trench_layer)

    floor_layer = Image.new("RGBA", (W, H), (*floor_rgb, 0))
    floor_layer.putalpha(main_in)
    hi_main.alpha_composite(floor_layer)

    if honeycomb_gain > 0.0:
        hc_layer = Image.new("RGBA", (W, H), (190, 215, 240, 0))
        hc_alpha = ImageChops.multiply(main_in, hc_900_L.point(lambda p: min(255, int(p * honeycomb_gain))))
        hc_layer.putalpha(hc_alpha)
        hi_main.alpha_composite(hc_layer)

    sh_rim = Image.new("RGBA", (W, H), (*bev_sh_rgb, 0))
    sh_rim.putalpha(main_bev_sh.point(lambda p: min(255, int(p * 0.95))))
    hi_main.alpha_composite(sh_rim)

    lit_rim = Image.new("RGBA", (W, H), (*bev_lit_rgb, 0))
    lit_rim.putalpha(main_bev_lit.point(lambda p: min(255, int(p * 0.95))))
    hi_main.alpha_composite(lit_rim)

    hi_main.alpha_composite(start_bright_2x if bright_start else start_std_2x)
    hi_main.alpha_composite(main_shadow_2x)
    hi_main.alpha_composite(AR_MAIN_GLOSS if gloss_ar else AR_MAIN_STD)

    canvas_1x = hi_main.resize((450, 450), Image.Resampling.BOX)
    cropped = canvas_1x.crop((68, 164, 422, 286))
    out_name = f"center_chamber_{idx}.png"
    cropped.save(os.path.join(OUTPUT_DIR, out_name))
    print(f"Saved center chamber overlay: {out_name}")

# ==============================================================================
# PRECOMPUTE SHARED 900x900 LIGHTING, SUNBURST & 3D WAFFLE MESH TABLES
# ==============================================================================
print("Precomputing 900x900 spatial lighting & 3D mesh tables...")
vig_map = [1.0] * (W * H)
conical_map = [0.0] * (W * H)
t_rad_map = [0.0] * (W * H)
inside_disc = bytearray(W * H)

gx1, gy1 = 138.0 * scale, 122.0 * scale
max_d1 = 335.0 * scale

rng2 = random.Random(108)
n_ang = 720
ang_lut = [rng2.gauss(0.0, 1.0) for _ in range(n_ang)]
ang_lut_s = [0.25 * ang_lut[(i-1)%n_ang] + 0.5 * ang_lut[i] + 0.25 * ang_lut[(i+1)%n_ang] for i in range(n_ang)]
h_streaks = [rng2.gauss(0.0, 1.25) for _ in range(H)]
sb_map = [0.0] * (W * H)

for y in range(H):
    dy_c = y - cy2
    dy_f = y - gy1
    row_off = y * W
    for x in range(W):
        dx_c = x - cx2
        r_c = math.hypot(dx_c, dy_c)
        if r_c <= 452.0:
            i = row_off + x
            inside_disc[i] = 1
            ang = math.atan2(dy_c, dx_c)
            conical_map[i] = (0.5 + 0.5 * math.cos(2.0 * (ang + 2.30))) ** 2.4
            t_rad_map[i] = min(1.0, math.hypot(x - gx1, dy_f) / max_d1)
            a_idx = int(((ang + math.pi) / (2.0 * math.pi)) * (n_ang - 1)) % n_ang
            sb_map[i] = ang_lut_s[a_idx]
            if r_c > 436.0:
                vig_map[i] = max(0.62, 1.0 - 0.34 * (((r_c - 436.0) / 16.0) ** 1.5))

def build_gunmetal_plate(base_rgb=(15.0, 19.0, 24.0), span_rgb=(36.0, 43.0, 52.0), sunburst_str=3.4, rib_str=1.8):
    plate_bytes = bytearray(W * H * 4)
    for y in range(H):
        hs = h_streaks[y]
        rib_v = math.sin((y % 6) / 6.0 * (2.0 * math.pi)) * rib_str if rib_str > 0.0 else 0.0
        row_off = y * W
        for x in range(W):
            i = row_off + x
            if inside_disc[i]:
                t = t_rad_map[i]
                con = conical_map[i]
                blend = 0.52 * (1.0 - t) + 0.48 * con
                sb = sb_map[i] * sunburst_str
                r_att = rib_v * (1.1 - 0.4 * t)
                vg = vig_map[i]
                rv = (base_rgb[0] + span_rgb[0] * blend + sb + hs + r_att) * vg
                gv = (base_rgb[1] + span_rgb[1] * blend + sb + hs + r_att) * vg
                bv = (base_rgb[2] + span_rgb[2] * blend + sb + hs + r_att) * vg
                idx = i * 4
                plate_bytes[idx]   = int(max(0, min(255, rv)))
                plate_bytes[idx+1] = int(max(0, min(255, gv)))
                plate_bytes[idx+2] = int(max(0, min(255, bv)))
                plate_bytes[idx+3] = 255
    return Image.frombytes("RGBA", (W, H), bytes(plate_bytes))

# ==============================================================================
# 0. CLASSIC LCD (bg_lcd_real.png) - Full Bleed
# ==============================================================================
img_00 = build_gunmetal_plate(base_rgb=(15.0, 19.0, 24.0), span_rgb=(36.0, 43.0, 52.0), sunburst_str=3.4, rib_str=1.8)
apply_pods_and_subdial_housing_2x(
    img_00,
    floor_rgb=(10, 14, 18),
    bev_lit_rgb=(150, 172, 198),
    bev_sh_rgb=(3, 5, 8),
    honeycomb_gain=0.22,
    sub_base_f=(32.0, 38.0, 47.0),
    sub_spec_f=(164.0, 182.0, 206.0),
    well_rgb=(10.0, 14.0, 18.0),
)
save_bg_from_2x(img_00, "bg_lcd_real.png")
save_center_chamber_3d(0, floor_rgb=(10, 14, 18), bev_lit_rgb=(150, 172, 198), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.22, bright_start=False)

# ==============================================================================
# 1. MATTE BLACK STEALTH (bg_lcd_matte_black.png)
# ==============================================================================
rng_mb = random.Random(101)
mb_bytes = bytearray(W * H * 4)
gx_mb, gy_mb = 142.0 * scale, 130.0 * scale
max_d_mb = 275.0 * scale
for y in range(H):
    dy_mb = y - gy_mb
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            t = (min(1.0, math.hypot(x - gx_mb, dy_mb) / max_d_mb)) ** 1.15
            con = conical_map[i]
            n = rng_mb.gauss(0.0, 0.85)
            rv = (44.0 + (8.0 - 44.0) * t + 5.5 * con + n) * vig_map[i]
            gv = (45.0 + (9.0 - 45.0) * t + 6.0 * con + n) * vig_map[i]
            bv = (48.0 + (10.5 - 48.0) * t + 7.0 * con + n) * vig_map[i]
            idx = i * 4
            mb_bytes[idx]   = int(max(0, min(255, rv)))
            mb_bytes[idx+1] = int(max(0, min(255, gv)))
            mb_bytes[idx+2] = int(max(0, min(255, bv)))
            mb_bytes[idx+3] = 255
img_01 = Image.frombytes("RGBA", (W, H), bytes(mb_bytes))
apply_pods_and_subdial_housing_2x(
    img_01,
    floor_rgb=(9, 10, 12),
    bev_lit_rgb=(124, 138, 156),
    bev_sh_rgb=(2, 3, 5),
    honeycomb_gain=0.16,
    sub_base_f=(25.0, 29.0, 35.0),
    sub_spec_f=(142.0, 158.0, 178.0),
    well_rgb=(9.0, 11.0, 14.0),
)
save_bg_from_2x(img_01, "bg_lcd_matte_black.png")
save_center_chamber_3d(1, floor_rgb=(9, 10, 12), bev_lit_rgb=(124, 138, 156), bev_sh_rgb=(2, 3, 5), honeycomb_gain=0.16, bright_start=False)

# ==============================================================================
# HELPER FOR 3D EMBOSSED TACTICAL CAMO PLATES (2: Woodland, 3: Urban, 4: Desert)
# ==============================================================================
def build_3d_camo_plate(base_col, camo_palette, seed_val, count_inner, count_outer, rx_range, ry_range):
    base_img = Image.new("RGBA", (W, H), (*base_col, 255))
    camo_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    height_layer = Image.new("L", (W, H), 64)
    cdraw = ImageDraw.Draw(camo_layer)
    hdraw = ImageDraw.Draw(height_layer)

    rng = random.Random(seed_val)
    for k in range(count_inner):
        bx = rng.randint(45, 405)
        by = rng.randint(45, 405)
        if (bx - cx)**2 + (by - cy)**2 < 178**2:
            rad_x = rng.randint(*rx_range)
            rad_y = rng.randint(*ry_range)
            col = rng.choice(camo_palette)
            box = ((bx - rad_x)*scale, (by - rad_y)*scale, (bx + rad_x)*scale, (by + rad_y)*scale)
            cdraw.ellipse(box, fill=col)
            h_val = 90 + (k % 4) * 38
            hdraw.ellipse(box, fill=h_val)
    for k in range(count_outer):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(158, 224)
        bx = int(round(cx + rr * math.cos(ang)))
        by = int(round(cy + rr * math.sin(ang)))
        rad_x = rng.randint(*rx_range)
        rad_y = rng.randint(*ry_range)
        col = rng.choice(camo_palette)
        box = ((bx - rad_x)*scale, (by - rad_y)*scale, (bx + rad_x)*scale, (by + rad_y)*scale)
        cdraw.ellipse(box, fill=col)
        h_val = 90 + (k % 4) * 38
        hdraw.ellipse(box, fill=h_val)

    base_img.alpha_composite(camo_layer)

    h_blur = height_layer.filter(ImageFilter.GaussianBlur(1.6))
    h_tl = Image.new("L", (W, H), 64)
    h_tl.paste(h_blur, (2, 2))
    h_br = Image.new("L", (W, H), 64)
    h_br.paste(h_blur, (-2, -2))
    tl_bytes = h_tl.tobytes()
    br_bytes = h_br.tobytes()
    src_bytes = base_img.tobytes()

    out_bytes = bytearray(W * H * 4)
    rng_g = random.Random(seed_val + 500)
    for i in range(W * H):
        if inside_disc[i]:
            idx = i * 4
            r0, g0, b0 = src_bytes[idx], src_bytes[idx+1], src_bytes[idx+2]
            emboss = (int(tl_bytes[i]) - int(br_bytes[i])) * 0.22
            t_r = t_rad_map[i]
            con = conical_map[i]
            macro = (1.16 - 0.30 * t_r) + 0.08 * con
            grain = rng_g.gauss(0.0, 0.9)
            vg = vig_map[i]
            out_bytes[idx]   = int(max(0, min(255, (r0 * macro + emboss + grain) * vg)))
            out_bytes[idx+1] = int(max(0, min(255, (g0 * macro + emboss + grain) * vg)))
            out_bytes[idx+2] = int(max(0, min(255, (b0 * macro + emboss + grain) * vg)))
            out_bytes[idx+3] = 255
    return Image.frombytes("RGBA", (W, H), bytes(out_bytes))

# ==============================================================================
# 2. WOODLAND CAMO (bg_lcd_camo.png)
# ==============================================================================
img_02 = build_3d_camo_plate(
    base_col=(38, 48, 34),
    camo_palette=[(24, 30, 20, 190), (52, 65, 42, 170), (68, 75, 54, 160), (44, 54, 46, 150)],
    seed_val=42, count_inner=55, count_outer=95, rx_range=(18, 52), ry_range=(14, 42)
)
apply_pods_and_subdial_housing_2x(
    img_02,
    floor_rgb=(17, 23, 16),
    bev_lit_rgb=(134, 158, 124),
    bev_sh_rgb=(4, 7, 4),
    honeycomb_gain=0.18,
    sub_base_f=(34.0, 42.0, 33.0),
    sub_spec_f=(154.0, 174.0, 146.0),
    well_rgb=(14.0, 19.0, 13.0),
)
save_bg_from_2x(img_02, "bg_lcd_camo.png")
save_center_chamber_3d(2, floor_rgb=(17, 23, 16), bev_lit_rgb=(134, 158, 124), bev_sh_rgb=(4, 7, 4), honeycomb_gain=0.18, bright_start=False)

# ==============================================================================
# 3. URBAN ARCTIC CAMO (bg_lcd_camo_urban.png)
# ==============================================================================
img_03 = build_3d_camo_plate(
    base_col=(24, 27, 32),
    camo_palette=[(15, 18, 22, 180), (45, 52, 62, 160), (75, 84, 96, 140), (110, 120, 135, 120)],
    seed_val=99, count_inner=50, count_outer=90, rx_range=(16, 44), ry_range=(12, 36)
)
apply_pods_and_subdial_housing_2x(
    img_03,
    floor_rgb=(13, 16, 21),
    bev_lit_rgb=(152, 174, 200),
    bev_sh_rgb=(4, 6, 9),
    honeycomb_gain=0.18,
    sub_base_f=(36.0, 42.0, 52.0),
    sub_spec_f=(170.0, 188.0, 212.0),
    well_rgb=(13.0, 16.0, 21.0),
)
save_bg_from_2x(img_03, "bg_lcd_camo_urban.png")
save_center_chamber_3d(3, floor_rgb=(13, 16, 21), bev_lit_rgb=(152, 174, 200), bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.18, bright_start=False)

# ==============================================================================
# 4. DESERT CAMO (bg_lcd_camo_desert.png)
# ==============================================================================
img_04 = build_3d_camo_plate(
    base_col=(52, 43, 32),
    camo_palette=[(30, 24, 17, 195), (78, 65, 47, 180), (104, 88, 64, 165), (64, 53, 39, 170)],
    seed_val=77, count_inner=60, count_outer=95, rx_range=(18, 50), ry_range=(13, 40)
)
apply_pods_and_subdial_housing_2x(
    img_04,
    floor_rgb=(21, 17, 12),
    bev_lit_rgb=(172, 152, 124),
    bev_sh_rgb=(7, 5, 3),
    honeycomb_gain=0.18,
    sub_base_f=(44.0, 38.0, 30.0),
    sub_spec_f=(178.0, 160.0, 134.0),
    well_rgb=(18.0, 15.0, 11.0),
)
save_bg_from_2x(img_04, "bg_lcd_camo_desert.png")
save_center_chamber_3d(4, floor_rgb=(21, 17, 12), bev_lit_rgb=(172, 152, 124), bev_sh_rgb=(7, 5, 3), honeycomb_gain=0.18, bright_start=False)

# ==============================================================================
# 5. SUBTLE ZEBRA CAMO (bg_lcd_camo_zebra.png)
# ==============================================================================
z_bytes = bytearray(W * H * 4)
ang_z = math.radians(-28.0)
ca_z, sa_z = math.cos(ang_z), math.sin(ang_z)
for y in range(H):
    dy = y - 450.0
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            dx = x - 450.0
            u = dx * ca_z - dy * sa_z
            v = dx * sa_z + dy * ca_z
            w1 = 26.0 * math.sin(v * 0.014 + 0.7 * math.cos(u * 0.011))
            w2 = 14.0 * math.cos(v * 0.029 - u * 0.009 + 1.2)
            fork = 1.35 * math.sin(v * 0.018 - 0.5) * math.cos((u + w1) * 0.045)
            phase = (u + w1 + w2) * 0.095 + fork
            val = math.sin(phase) + 0.28 * math.cos(2.0 * phase + 0.6 * math.sin(v * 0.022))
            t = max(0.0, min(1.0, 0.5 + (val - 0.06) * 3.2))
            ridge = math.cos(phase) * 3.6
            macro = (1.14 - 0.26 * t_rad_map[i]) + 0.14 * conical_map[i]
            vg = vig_map[i]
            idx = i * 4
            z_bytes[idx]   = int(max(0, min(255, ((15.0 + 27.0 * t) * macro + ridge) * vg)))
            z_bytes[idx+1] = int(max(0, min(255, ((18.0 + 31.0 * t) * macro + ridge * 1.1) * vg)))
            z_bytes[idx+2] = int(max(0, min(255, ((22.0 + 36.0 * t) * macro + ridge * 1.25) * vg)))
            z_bytes[idx+3] = 255
img_05 = Image.frombytes("RGBA", (W, H), bytes(z_bytes))
apply_pods_and_subdial_housing_2x(
    img_05,
    floor_rgb=(12, 15, 20),
    bev_lit_rgb=(148, 170, 196),
    bev_sh_rgb=(4, 6, 9),
    honeycomb_gain=0.20,
    sub_base_f=(34.0, 40.0, 50.0),
    sub_spec_f=(166.0, 184.0, 208.0),
    well_rgb=(12.0, 15.0, 20.0),
)
save_bg_from_2x(img_05, "bg_lcd_camo_zebra.png")
save_center_chamber_3d(5, floor_rgb=(12, 15, 20), bev_lit_rgb=(148, 170, 196), bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.20, bright_start=False)

# ==============================================================================
# 6. CARBON FIBER (bg_lcd_carbon_fiber.png)
# ==============================================================================
cf_bytes = bytearray(W * H * 4)
bw = 12
cf_tile = [[(0.0, 0.0)] * bw for _ in range(bw * 4)]
for twill in range(4):
    for py in range(bw):
        for px in range(bw):
            if twill in (0, 1):
                u_s = (py + 0.5) / bw
                v_s = (px + 0.5) / bw
                cyl = math.sin(u_s * math.pi)
                fil = 0.94 + 0.06 * math.sin(u_s * 6.0 * math.pi)
                gap_ao = 0.72 + 0.28 * math.sin(v_s * math.pi) ** 0.4
                shade = (26.0 + 42.0 * (cyl ** 1.15)) * fil * gap_ao
                spec_f = (cyl ** 6.0) * 14.0
            else:
                u_s = (px + 0.5) / bw
                v_s = (py + 0.5) / bw
                cyl = math.sin(u_s * math.pi)
                fil = 0.94 + 0.06 * math.sin(u_s * 6.0 * math.pi)
                gap_ao = 0.72 + 0.28 * math.sin(v_s * math.pi) ** 0.4
                shade = (14.0 + 24.0 * (cyl ** 1.15)) * fil * gap_ao
                spec_f = (cyl ** 6.0) * 8.0
            cf_tile[twill * bw + py][px] = (shade, spec_f)

for y in range(H):
    by_idx = y // bw
    py = y % bw
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            bx_idx = x // bw
            px = x % bw
            twill = (bx_idx + by_idx) % 4
            shade, spec_f = cf_tile[twill * bw + py][px]
            t_r = t_rad_map[i]
            con = conical_map[i]
            macro = (1.15 - 0.32 * t_r) + 0.16 * con
            clearcoat = max(0.0, (1.0 - t_r * 1.35)) ** 2.2 * 12.0
            vg = vig_map[i]
            rv = (shade * macro + spec_f + clearcoat * 0.85) * vg
            gv = ((shade + 3.5) * macro + spec_f * 1.05 + clearcoat * 0.95) * vg
            bv = ((shade + 7.5) * macro + spec_f * 1.15 + clearcoat * 1.10) * vg
            idx = i * 4
            cf_bytes[idx]   = int(max(0, min(255, rv)))
            cf_bytes[idx+1] = int(max(0, min(255, gv)))
            cf_bytes[idx+2] = int(max(0, min(255, bv)))
            cf_bytes[idx+3] = 255
img_06 = Image.frombytes("RGBA", (W, H), bytes(cf_bytes))
apply_pods_and_subdial_housing_2x(
    img_06,
    floor_rgb=(12, 15, 19),
    bev_lit_rgb=(152, 174, 200),
    bev_sh_rgb=(3, 5, 8),
    honeycomb_gain=0.22,
    sub_base_f=(34.0, 40.0, 49.0),
    sub_spec_f=(168.0, 186.0, 210.0),
    well_rgb=(12.0, 15.0, 19.0),
)
save_bg_from_2x(img_06, "bg_lcd_carbon_fiber.png")
save_center_chamber_3d(6, floor_rgb=(12, 15, 19), bev_lit_rgb=(152, 174, 200), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.22, bright_start=False)

# ==============================================================================
# 7. GLOSS BLACK CERAMIC (bg_lcd_gloss_black.png)
# ==============================================================================
gb_bytes = bytearray(W * H * 4)
for y in range(H):
    dy_c = y - cy2
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            dx_c = x - cx2
            r_c = math.hypot(dx_c, dy_c)
            t_r = t_rad_map[i]
            con = conical_map[i]
            u_diag = (dx_c * 0.65 + dy_c * 0.76) / 450.0
            softbox = 0.0
            if u_diag < -0.05:
                arc_band = math.exp(-((r_c - 345.0) / 52.0) ** 2) * max(0.0, min(1.0, (-u_diag - 0.05) * 2.2))
                dome_sheen = max(0.0, (-u_diag - 0.05)) ** 1.6 * 0.45
                softbox = (arc_band * 26.0 + dome_sheen * 24.0)
            vg = vig_map[i]
            rv = (7.0 + 8.0 * (1.0 - t_r) + 6.0 * (con ** 2.0) + softbox * 0.88) * vg
            gv = (9.0 + 10.0 * (1.0 - t_r) + 7.5 * (con ** 2.0) + softbox * 0.96) * vg
            bv = (12.0 + 13.0 * (1.0 - t_r) + 9.5 * (con ** 2.0) + softbox * 1.08) * vg
            idx = i * 4
            gb_bytes[idx]   = int(max(0, min(255, rv)))
            gb_bytes[idx+1] = int(max(0, min(255, gv)))
            gb_bytes[idx+2] = int(max(0, min(255, bv)))
            gb_bytes[idx+3] = 255
img_07 = Image.frombytes("RGBA", (W, H), bytes(gb_bytes))
apply_pods_and_subdial_housing_2x(
    img_07,
    floor_rgb=(7, 9, 12),
    bev_lit_rgb=(184, 206, 232),
    bev_sh_rgb=(2, 3, 5),
    honeycomb_gain=0.28,
    sub_base_f=(32.0, 38.0, 48.0),
    sub_spec_f=(195.0, 212.0, 235.0),
    well_rgb=(7.0, 9.0, 12.0),
    gloss_ar=True,
)
save_bg_from_2x(img_07, "bg_lcd_gloss_black.png")
save_center_chamber_3d(7, floor_rgb=(7, 9, 12), bev_lit_rgb=(184, 206, 232), bev_sh_rgb=(2, 3, 5), honeycomb_gain=0.28, bright_start=True, gloss_ar=True)

# ==============================================================================
# 8. MICRO-GRID CARBON (bg_lcd_grid.png)
# ==============================================================================
gr_bytes = bytearray(W * H * 4)
g_pitch = 12
grid_cell = [[0.0] * g_pitch for _ in range(g_pitch)]
for py in range(g_pitch):
    for px in range(g_pitch):
        dx_g = abs(px - 6)
        dy_g = abs(py - 6)
        if dx_g == 0 or dy_g == 0:
            grid_cell[py][px] = 18.0
        elif px == 7 or py == 7:
            grid_cell[py][px] = 8.5
        elif px == 5 or py == 5:
            grid_cell[py][px] = -6.5
        else:
            u_c = (px - 6) / 6.0
            v_c = (py - 6) / 6.0
            grid_cell[py][px] = 2.0 * (1.0 - 0.3 * (u_c*u_c + v_c*v_c))

for y in range(H):
    py = y % g_pitch
    g_row = grid_cell[py]
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            px = x % g_pitch
            g_mod = g_row[px]
            t_r = t_rad_map[i]
            con = conical_map[i]
            macro = (1.16 - 0.30 * t_rad_map[i]) + 0.18 * con
            vg = vig_map[i]
            rv = (30.0 * macro + g_mod * 0.90) * vg
            gv = (38.0 * macro + g_mod * 1.00) * vg
            bv = (44.0 * macro + g_mod * 1.12) * vg
            idx = i * 4
            gr_bytes[idx]   = int(max(0, min(255, rv)))
            gr_bytes[idx+1] = int(max(0, min(255, gv)))
            gr_bytes[idx+2] = int(max(0, min(255, bv)))
            gr_bytes[idx+3] = 255
img_08 = Image.frombytes("RGBA", (W, H), bytes(gr_bytes))
apply_pods_and_subdial_housing_2x(
    img_08,
    floor_rgb=(15, 20, 24),
    bev_lit_rgb=(150, 174, 198),
    bev_sh_rgb=(4, 6, 9),
    honeycomb_gain=0.22,
    sub_base_f=(35.0, 42.0, 50.0),
    sub_spec_f=(168.0, 186.0, 210.0),
    well_rgb=(14.0, 19.0, 23.0),
)
save_bg_from_2x(img_08, "bg_lcd_grid.png")
save_center_chamber_3d(8, floor_rgb=(15, 20, 24), bev_lit_rgb=(150, 174, 198), bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.22, bright_start=False)

# ==============================================================================
# PRECOMPUTE 3D MICRO-WAFFLE MESH TILES (for 9: Tactical Mesh + 10..16: Industrial)
# ==============================================================================
pitch_a = 9
Z_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
AO_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    v_a = (py / float(pitch_a)) * 2.0 - 1.0
    for px in range(pitch_a):
        u_a = (px / float(pitch_a)) * 2.0 - 1.0
        dist_cheb = max(abs(u_a), abs(v_a))
        z = 0.5 * (1.0 - math.tanh(6.5 * (dist_cheb - 0.74)))
        dist_eucl = math.hypot(u_a, v_a)
        if dist_eucl > 0.85:
            z *= max(0.0, min(1.0, 1.0 - 0.15 * (dist_eucl - 0.85)))
        Z_tile[py][px] = z
        AO_tile[py][px] = 0.44 + 0.56 * (z ** 0.7)

lx_m, ly_m, lz_m = -0.48, -0.62, 0.62
l_len_m = math.sqrt(lx_m*lx_m + ly_m*ly_m + lz_m*lz_m)
lx_m, ly_m, lz_m = lx_m/l_len_m, ly_m/l_len_m, lz_m/l_len_m

hx_m, hy_m, hz_m = lx_m, ly_m, lz_m + 1.0
h_len_m = math.sqrt(hx_m*hx_m + hy_m*hy_m + hz_m*hz_m)
hx_m, hy_m, hz_m = hx_m/h_len_m, hy_m/h_len_m, hz_m/h_len_m

slope_scale = 2.95
ndotl_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
spec_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    py_prev = (py - 1) % pitch_a
    py_next = (py + 1) % pitch_a
    for px in range(pitch_a):
        px_prev = (px - 1) % pitch_a
        px_next = (px + 1) % pitch_a
        dZdx = 0.5 * (Z_tile[py][px_next] - Z_tile[py][px_prev])
        dZdy = 0.5 * (Z_tile[py_next][px] - Z_tile[py_prev][px])
        nx = -slope_scale * dZdx
        ny = -slope_scale * dZdy
        nz = 1.0
        n_len = math.sqrt(nx*nx + ny*ny + nz*nz)
        nx, ny, nz = nx/n_len, ny/n_len, nz/n_len
        nd = max(0.0, min(1.0, nx*lx_m + ny*ly_m + nz*lz_m))
        nh = max(0.0, min(1.0, nx*hx_m + ny*hy_m + nz*hz_m))
        ndotl_tile[py][px] = nd
        spec_tile[py][px] = nh ** 15.0

# ==============================================================================
# 9. TACTICAL RAISED MESH (bg_lcd_tactical_mesh.png)
# ==============================================================================
base_r, base_g, base_b = 46.0, 53.0, 62.0
tile_r = [[0.0]*pitch_a for _ in range(pitch_a)]
tile_g = [[0.0]*pitch_a for _ in range(pitch_a)]
tile_b = [[0.0]*pitch_a for _ in range(pitch_a)]
spec_term_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    for px in range(pitch_a):
        nd = ndotl_tile[py][px]
        ao = AO_tile[py][px]
        sp = 36.0 * (spec_tile[py][px] ** (17.0/15.0)) * ao
        spec_term_tile[py][px] = sp
        diff_mult = 0.55 + 0.72 * nd
        diff_add = 24.0 * (nd - 0.5)
        tile_r[py][px] = (base_r * diff_mult + diff_add) * ao
        tile_g[py][px] = (base_g * diff_mult + diff_add) * ao
        tile_b[py][px] = (base_b * diff_mult + diff_add) * ao

rng_m = random.Random(42)
mesh_bytes = bytearray(W * H * 4)
for y in range(H):
    py = y % pitch_a
    tr_row = tile_r[py]
    tg_row = tile_g[py]
    tb_row = tile_b[py]
    sp_row = spec_term_tile[py]
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            px = x % pitch_a
            macro_light = (1.08 - 0.24 * t_rad_map[i]) + 0.14 * conical_map[i]
            fn = rng_m.gauss(0.0, 1.2)
            sp = sp_row[px] * (1.12 - 0.35 * t_rad_map[i]) + fn
            vg = vig_map[i]
            idx = i * 4
            mesh_bytes[idx]   = int(max(0, min(255, (tr_row[px] * macro_light + sp * 0.92) * vg)))
            mesh_bytes[idx+1] = int(max(0, min(255, (tg_row[px] * macro_light + sp * 0.96) * vg)))
            mesh_bytes[idx+2] = int(max(0, min(255, (tb_row[px] * macro_light + sp * 1.05) * vg)))
            mesh_bytes[idx+3] = 255
img_09 = Image.frombytes("RGBA", (W, H), bytes(mesh_bytes))
apply_pods_and_subdial_housing_2x(
    img_09,
    floor_rgb=(13, 17, 22),
    bev_lit_rgb=(154, 176, 202),
    bev_sh_rgb=(4, 6, 9),
    honeycomb_gain=0.22,
    sub_base_f=(36.0, 42.0, 52.0),
    sub_spec_f=(170.0, 188.0, 212.0),
    well_rgb=(13.0, 17.0, 22.0),
)
save_bg_from_2x(img_09, "bg_lcd_tactical_mesh.png")
save_center_chamber_3d(9, floor_rgb=(13, 17, 22), bev_lit_rgb=(154, 176, 202), bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.22, bright_start=False)

# ==============================================================================
# 10..16. THE 7 INDUSTRIAL TEXTURED GRADIENT BACKGROUNDS
# ==============================================================================
rng_brush = random.Random(303)
brush_rows = [rng_brush.gauss(0.0, 0.025) for _ in range(H)]

diff_mult_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
spec_add_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    for px in range(pitch_a):
        nd = ndotl_tile[py][px]
        ao = AO_tile[py][px]
        diff_mult_tile[py][px] = (0.52 + 0.76 * nd) * ao
        spec_add_tile[py][px] = 42.0 * spec_tile[py][px] * ao

ind_lut_idx = bytearray(W * H)
ind_mult_map = [0.0] * (W * H)
ind_sp_map = [0.0] * (W * H)

gx_ind, gy_ind = 276.0, 248.0
max_rad_ind = 600.0
dir_x_ind, dir_y_ind = 0.68, 0.733

for y in range(H):
    py = y % pitch_a
    dm_row = diff_mult_tile[py]
    sp_row = spec_add_tile[py]
    b_streak = brush_rows[y]
    dy_f = y - gy_ind
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            px = x % pitch_a
            dx_f = x - gx_ind
            r_dist = math.hypot(dx_f, dy_f) / max_rad_ind
            lin_proj = max(0.0, (dx_f * dir_x_ind + dy_f * dir_y_ind) / max_rad_ind)
            t = max(0.0, min(1.0, 0.72 * r_dist + 0.28 * lin_proj))
            ind_lut_idx[i] = int(round(t * 255.0))
            con = conical_map[i]
            ind_mult_map[i] = (dm_row[px] + b_streak + 0.14 * con) * vig_map[i]
            ind_sp_map[i] = (sp_row[px] * (1.20 - 0.55 * t) + 8.0 * (con ** 2.2)) * vig_map[i]

ind_specs = [
    (10, "bg_lcd_ind_cyan.png",    183.0, 0.80, 0.58, 199.0, 0.90, 0.14, (7, 16, 22),  (92, 184, 220),  (28.0, 44.0, 54.0), (145.0, 195.0, 220.0), (0.85, 0.96, 1.0)),
    (11, "bg_lcd_ind_lime.png",     69.0, 0.84, 0.54,  87.0, 0.88, 0.13, (12, 17, 8),  (148, 190, 82),  (36.0, 44.0, 26.0), (170.0, 195.0, 130.0), (0.90, 1.0, 0.82)),
    (12, "bg_lcd_ind_blue.png",    207.0, 0.84, 0.62, 225.0, 0.92, 0.14, (7, 12, 24),  (98, 152, 230),  (28.0, 38.0, 58.0), (150.0, 182.0, 228.0), (0.85, 0.94, 1.0)),
    (13, "bg_lcd_ind_red.png",     358.0, 0.84, 0.58, 340.0, 0.92, 0.14, (20, 7, 10),  (212, 88, 104),  (48.0, 28.0, 32.0), (205.0, 145.0, 155.0), (1.0, 0.86, 0.88)),
    (14, "bg_lcd_ind_orange.png",   28.0, 0.86, 0.60,  11.0, 0.92, 0.14, (21, 11, 6),  (220, 128, 66),  (50.0, 34.0, 24.0), (212.0, 165.0, 125.0), (1.0, 0.92, 0.82)),
    (15, "bg_lcd_ind_magenta.png", 320.0, 0.84, 0.56, 296.0, 0.92, 0.14, (19, 7, 19),  (204, 92, 194),  (46.0, 28.0, 46.0), (198.0, 145.0, 196.0), (0.98, 0.86, 1.0)),
    (16, "bg_lcd_ind_silver.png",  200.0, 0.08, 0.60, 218.0, 0.22, 0.15, (13, 16, 20), (168, 186, 210), (38.0, 44.0, 52.0), (182.0, 198.0, 218.0), (0.95, 0.98, 1.0)),
    (17, "bg_lcd_ind_black_silver.png",  0.0, 0.00, 0.85,   0.0, 0.00, 0.08, (9, 10, 12),  (210, 222, 238), (32.0, 36.0, 42.0), (220.0, 230.0, 245.0), (1.0, 1.0, 1.0)),
]

for idx_bg, fname, hl, sl, vl, hd, sd, vd, floor_rgb, bev_lit_rgb, sub_base_f, sub_spec_f, sp_tint in ind_specs:
    lut_rgb = []
    for k in range(256):
        t = k / 255.0
        t_hue = t ** 0.95
        t_val = t ** 1.05
        h_deg = hl + (hd - hl) * t_hue
        s_val = sl + (sd - sl) * t
        v_val = vl + (vd - vl) * t_val
        r_f, g_f, b_f = colorsys.hsv_to_rgb((h_deg % 360.0) / 360.0, s_val, v_val)
        lut_rgb.append((r_f * 255.0, g_f * 255.0, b_f * 255.0))

    sr_t, sg_t, sb_t = sp_tint
    surf_bytes = bytearray(W * H * 4)
    for i in range(W * H):
        if inside_disc[i]:
            br, bg_c, bb = lut_rgb[ind_lut_idx[i]]
            mult = ind_mult_map[i]
            sp = ind_sp_map[i]
            idx = i * 4
            surf_bytes[idx]   = int(max(0, min(255, br * mult + sp * sr_t)))
            surf_bytes[idx+1] = int(max(0, min(255, bg_c * mult + sp * sg_t)))
            surf_bytes[idx+2] = int(max(0, min(255, bb * mult + sp * sb_t)))
            surf_bytes[idx+3] = 255

    img_ind = Image.frombytes("RGBA", (W, H), bytes(surf_bytes))
    apply_pods_and_subdial_housing_2x(
        img_ind,
        floor_rgb=floor_rgb,
        bev_lit_rgb=bev_lit_rgb,
        bev_sh_rgb=(3, 5, 8),
        honeycomb_gain=0.22,
        sub_base_f=sub_base_f,
        sub_spec_f=sub_spec_f,
        well_rgb=floor_rgb,
    )
    save_bg_from_2x(img_ind, fname)
    save_center_chamber_3d(idx_bg, floor_rgb=floor_rgb, bev_lit_rgb=bev_lit_rgb, bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.22, bright_start=True)

print(f"All 17 full-bleed backgrounds, 17 center_chamber overlays, and bg_border_classic generated in {time.time() - t0:.1f}s!")
