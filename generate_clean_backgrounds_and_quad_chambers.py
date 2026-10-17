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

            dist_tr = abs(sdf_c - 1.6)
            if dist_tr < 1.3:
                m_trench[idx] = int((1.0 - dist_tr / 1.3) * 255.0)

            if sdf_c >= -2.4 and sdf_c <= 1.4:
                ldot = nx * (-light_dir_x) + ny * (-light_dir_y)
                profile = math.exp(-((sdf_c + 0.5) / 1.05) ** 2)
                if ldot > 0.0:
                    m_bev_lit[idx] = int(min(255.0, (ldot ** 1.1) * profile * 255.0))
                else:
                    m_bev_sh[idx] = int(min(255.0, ((-ldot) ** 0.95) * profile * 255.0))

    return (
        Image.frombytes("L", (W, H), bytes(m_in)),
        Image.frombytes("L", (W, H), bytes(m_trench)),
        Image.frombytes("L", (W, H), bytes(m_bev_lit)),
        Image.frombytes("L", (W, H), bytes(m_bev_sh)),
    )

QUAD_PODS = [(72, 138), (152, 218), (232, 298), (312, 378)]
QUAD_Y1, QUAD_Y2 = 90, 168

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

# 1. Slot 5 Pod (Bottom Date Bay) - baked into bg_lcd_*.png
slot5_in, slot5_trench, slot5_bev_lit, slot5_bev_sh = compute_chamber_masks_and_bevels(
    70 * scale, 302 * scale, 305 * scale, 358 * scale, r_c2, has_cut=True
)
slot5_shadow_2x = build_dual_stage_shadow_layer(slot5_in)
slot5_trench_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
slot5_trench_layer.putalpha(slot5_trench.point(lambda p: (p * 115) // 255))

# 2. Quad Pods (Top 4) - saved into quad_chamber_0..16.png for digital mode only!
quad_in = Image.new("L", (W, H), 0)
quad_trench = Image.new("L", (W, H), 0)
quad_bev_lit = Image.new("L", (W, H), 0)
quad_bev_sh = Image.new("L", (W, H), 0)

for x1_q, x2_q in QUAD_PODS:
    m_in, m_tr, m_bl, m_bs = compute_chamber_masks_and_bevels(
        x1_q * scale, QUAD_Y1 * scale, x2_q * scale, QUAD_Y2 * scale, r_c2, False
    )
    quad_in = ImageChops.lighter(quad_in, m_in)
    quad_trench = ImageChops.lighter(quad_trench, m_tr)
    quad_bev_lit = ImageChops.lighter(quad_bev_lit, m_bl)
    quad_bev_sh = ImageChops.lighter(quad_bev_sh, m_bs)

quad_shadow_2x = build_dual_stage_shadow_layer(quad_in)
quad_trench_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
quad_trench_layer.putalpha(quad_trench.point(lambda p: (p * 115) // 255))

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

AR_SLOT5_STD = make_ar_layer_for_mask(slot5_in, 0.45)
AR_SLOT5_GLOSS = make_ar_layer_for_mask(slot5_in, 0.75)
AR_QUAD_STD = make_ar_layer_for_mask(quad_in, 0.45)
AR_QUAD_GLOSS = make_ar_layer_for_mask(quad_in, 0.75)

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
    print(f"Saved clean full-bleed: {filename}")

def save_quad_chamber_3d(idx, floor_rgb, bev_lit_rgb, bev_sh_rgb=(4, 6, 9), honeycomb_gain=0.18, gloss_ar=False):
    hi_quad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hi_quad.alpha_composite(quad_trench_layer)

    floor_layer = Image.new("RGBA", (W, H), (*floor_rgb, 0))
    floor_layer.putalpha(quad_in)
    hi_quad.alpha_composite(floor_layer)

    if honeycomb_gain > 0.0:
        hc_layer = Image.new("RGBA", (W, H), (190, 215, 240, 0))
        hc_alpha = ImageChops.multiply(quad_in, hc_900_L.point(lambda p: min(255, int(p * honeycomb_gain))))
        hc_layer.putalpha(hc_alpha)
        hi_quad.alpha_composite(hc_layer)

    sh_rim = Image.new("RGBA", (W, H), (*bev_sh_rgb, 0))
    sh_rim.putalpha(quad_bev_sh.point(lambda p: min(255, int(p * 0.95))))
    hi_quad.alpha_composite(sh_rim)

    lit_rim = Image.new("RGBA", (W, H), (*bev_lit_rgb, 0))
    lit_rim.putalpha(quad_bev_lit.point(lambda p: min(255, int(p * 0.95))))
    hi_quad.alpha_composite(lit_rim)

    hi_quad.alpha_composite(quad_shadow_2x)
    hi_quad.alpha_composite(AR_QUAD_GLOSS if gloss_ar else AR_QUAD_STD)

    canvas_1x = hi_quad.resize((450, 450), Image.Resampling.BOX)
    out_name = f"quad_chamber_{idx}.png"
    canvas_1x.save(os.path.join(OUTPUT_DIR, out_name))
    print(f"Saved quad chamber overlay: {out_name}")

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

    # 1. Outer seam trench around slot 5
    img_2x.alpha_composite(slot5_trench_layer)

    # 2. Recessed cavity floor for slot 5
    floor_layer = Image.new("RGBA", (W, H), (*floor_rgb, 0))
    floor_layer.putalpha(slot5_in)
    img_2x.alpha_composite(floor_layer)

    # 3. Subtle default honeycomb wafer inside slot 5
    if honeycomb_gain > 0.0:
        hc_layer = Image.new("RGBA", (W, H), (190, 215, 240, 0))
        hc_alpha = ImageChops.multiply(slot5_in, hc_900_L.point(lambda p: min(255, int(p * honeycomb_gain))))
        hc_layer.putalpha(hc_alpha)
        img_2x.alpha_composite(hc_layer)

    # 4. 3D directional chamfered window bevels for slot 5
    sh_rim = Image.new("RGBA", (W, H), (*bev_sh_rgb, 0))
    sh_rim.putalpha(slot5_bev_sh.point(lambda p: min(255, int(p * 0.95))))
    img_2x.alpha_composite(sh_rim)

    lit_rim = Image.new("RGBA", (W, H), (*bev_lit_rgb, 0))
    lit_rim.putalpha(slot5_bev_lit.point(lambda p: min(255, int(p * 0.95))))
    img_2x.alpha_composite(lit_rim)

    # 5. Dual-stage recessed cavity shadow + subtle sapphire AR reflection inside slot 5
    img_2x.alpha_composite(slot5_shadow_2x)
    img_2x.alpha_composite(AR_SLOT5_GLOSS if gloss_ar else AR_SLOT5_STD)

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
                            slot_profile = max(0.0, min(1.0, (1.1 * scale - s_dist) / 0.7)) * max(0.0, min(1.0, (r_screw - 0.4 * scale - s_len) / 0.7))
                            s_sh = 1.0 - 0.88 * slot_profile
                            rv = (rv * 0.82 + 55.0 * dome) * s_sh
                            gv = (gv * 0.82 + 62.0 * dome) * s_sh
                            bv = (bv * 0.82 + 75.0 * dome) * s_sh
                        break

                alpha_edge = 1.0
                if r > ro2 - 0.8:
                    alpha_edge = max(0.0, min(1.0, (ro2 + 0.8 - r) / 1.6))
                elif r < ri2 + 0.8:
                    alpha_edge = max(0.0, min(1.0, (r - (ri2 - 0.8)) / 1.6))

                patch_bytes[idx]   = int(max(0, min(255, rv)))
                patch_bytes[idx+1] = int(max(0, min(255, gv)))
                patch_bytes[idx+2] = int(max(0, min(255, bv)))
                patch_bytes[idx+3] = int(alpha_edge * 255.0)

            elif r < ri2 - 0.8:
                u_ar = (dx * 0.72 + dy * 0.69) / float(P)
                sh_sub_ar = math.exp(-((u_ar - 0.05) / 0.16) ** 2) * 44.0 * ar_sheen_gain
                r_in_sh = math.hypot(dx + 2.0, dy + 2.5) / ri2
                sub_ao = max(0.35, min(1.0, 0.68 + 0.32 * (1.0 - (r / ri2))))

                rv = well_rgb[0] * sub_ao + sh_sub_ar * 0.68
                gv = well_rgb[1] * sub_ao + sh_sub_ar * 0.89
                bv = well_rgb[2] * sub_ao + sh_sub_ar * 1.00
                patch_bytes[idx]   = int(max(0, min(255, rv)))
                patch_bytes[idx+1] = int(max(0, min(255, gv)))
                patch_bytes[idx+2] = int(max(0, min(255, bv)))
                patch_bytes[idx+3] = 255

    sub_patch_2x = Image.frombytes("RGBA", (P, P), bytes(patch_bytes))
    img_2x.alpha_composite(sub_patch_2x, (int(scx2 - pcx), int(scy2 - pcy)))

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
# 0. CLASSIC LCD (bg_lcd_real.png)
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
save_quad_chamber_3d(0, floor_rgb=(10, 14, 18), bev_lit_rgb=(150, 172, 198), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.22)

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
save_quad_chamber_3d(1, floor_rgb=(9, 10, 12), bev_lit_rgb=(124, 138, 156), bev_sh_rgb=(2, 3, 5), honeycomb_gain=0.16)

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
    all_blobs = []
    for _ in range(count_inner):
        rad_dist = rng.uniform(0.0, 160.0 * scale)
        th = rng.uniform(0.0, 2.0 * math.pi)
        bx = cx2 + rad_dist * math.cos(th)
        by = cy2 + rad_dist * math.sin(th)
        rx = rng.uniform(*rx_range) * scale
        ry = rng.uniform(*ry_range) * scale
        rot = rng.uniform(0.0, 180.0)
        c_idx = rng.randint(0, len(camo_palette) - 1)
        all_blobs.append((bx, by, rx, ry, rot, camo_palette[c_idx]))

    for _ in range(count_outer):
        rad_dist = rng.uniform(160.0 * scale, 215.0 * scale)
        th = rng.uniform(0.0, 2.0 * math.pi)
        bx = cx2 + rad_dist * math.cos(th)
        by = cy2 + rad_dist * math.sin(th)
        rx = rng.uniform(*rx_range) * 1.08 * scale
        ry = rng.uniform(*ry_range) * 1.08 * scale
        rot = rng.uniform(0.0, 180.0)
        c_idx = rng.randint(0, len(camo_palette) - 1)
        all_blobs.append((bx, by, rx, ry, rot, camo_palette[c_idx]))

    for bx, by, rx, ry, rot, col in all_blobs:
        patch = Image.new("RGBA", (int(rx * 2.6), int(ry * 2.6)), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(patch)
        pdraw.ellipse((0, 0, patch.width, patch.height), fill=(*col, 255))
        patch_rot = patch.rotate(rot, expand=True, resample=Image.Resampling.BICUBIC)
        camo_layer.paste(patch_rot, (int(bx - patch_rot.width // 2), int(by - patch_rot.height // 2)), patch_rot)

        hpatch = Image.new("L", patch.size, 0)
        ImageDraw.Draw(hpatch).ellipse((0, 0, hpatch.width, hpatch.height), fill=190)
        hpatch_rot = hpatch.rotate(rot, expand=True, resample=Image.Resampling.BICUBIC)
        height_layer.paste(hpatch_rot, (int(bx - hpatch_rot.width // 2), int(by - hpatch_rot.height // 2)), hpatch_rot)

    camo_layer = camo_layer.filter(ImageFilter.GaussianBlur(1.4 * scale))
    height_layer = height_layer.filter(ImageFilter.GaussianBlur(1.8 * scale))

    base_img.alpha_composite(camo_layer)
    b_arr = np.array(base_img, dtype=float)
    h_arr = np.array(height_layer, dtype=float) / 255.0

    gy_c, gx_c = np.gradient(h_arr)
    lx, ly = -light_dir_x, -light_dir_y
    ldot = gx_c * lx + gy_c * ly
    shade = 1.0 + ldot * 2.4
    shade = np.clip(shade, 0.72, 1.35)[:, :, np.newaxis]
    b_arr[:, :, :3] = np.clip(b_arr[:, :, :3] * shade, 0, 255)

    res = Image.fromarray(b_arr.astype(np.uint8))
    r_c, g_c, b_c, a_c = res.split()
    r_b = bytearray(r_c.tobytes())
    g_b = bytearray(g_c.tobytes())
    b_b = bytearray(b_c.tobytes())
    a_b = bytearray(a_c.tobytes())
    for i in range(W * H):
        if inside_disc[i]:
            vg = vig_map[i]
            r_b[i] = int(r_b[i] * vg)
            g_b[i] = int(g_b[i] * vg)
            b_b[i] = int(b_b[i] * vg)
        else:
            a_b[i] = 0
    return Image.merge("RGBA", (
        Image.frombytes("L", (W, H), bytes(r_b)),
        Image.frombytes("L", (W, H), bytes(g_b)),
        Image.frombytes("L", (W, H), bytes(b_b)),
        Image.frombytes("L", (W, H), bytes(a_b)),
    ))

import numpy as np

# 2. WOODLAND CAMO (bg_lcd_camo.png)
src_camo_path = os.path.join(EXPORT_DIR, "source_camo_woodland.png")
if not os.path.exists(src_camo_path):
    alt_path = "C:/Users/bonst/.gemini/antigravity/brain/d3a6c7d4-5613-437a-a72c-e90fec512f25/.user_uploaded/media_1792233428021_086ed444.png"
    if os.path.exists(alt_path):
        raw_crop = Image.open(alt_path).crop((0, 0, 948, 948))
        raw_crop.save(src_camo_path)

camo_src = Image.open(src_camo_path).convert("RGB")
w_src, h_src = camo_src.size
zoom_factor = 1.8
cw, ch = w_src / zoom_factor, h_src / zoom_factor
x1 = (w_src - cw) / 2.0
y1 = (h_src - ch) / 2.0
camo_cropped = camo_src.crop((int(round(x1)), int(round(y1)), int(round(x1 + cw)), int(round(y1 + ch))))
camo_resized = camo_cropped.resize((W, H), Image.Resampling.LANCZOS)
arr_camo = np.array(camo_resized, dtype=float)
vig_camo = np.array(vig_map).reshape((H, W))
disc_camo = np.array(inside_disc).reshape((H, W))

arr_camo_vig = np.clip(arr_camo * vig_camo[:, :, np.newaxis], 0, 255).astype(np.uint8)
alpha_camo = (disc_camo * 255).astype(np.uint8)
img_02 = Image.fromarray(np.dstack([arr_camo_vig, alpha_camo]))

apply_pods_and_subdial_housing_2x(
    img_02,
    floor_rgb=(17, 23, 16),
    bev_lit_rgb=(148, 166, 142),
    bev_sh_rgb=(4, 6, 4),
    honeycomb_gain=0.18,
    sub_base_f=(36.0, 42.0, 34.0),
    sub_spec_f=(160.0, 175.0, 155.0),
    well_rgb=(16.0, 22.0, 15.0),
)
save_bg_from_2x(img_02, "bg_lcd_camo.png")
save_quad_chamber_3d(2, floor_rgb=(17, 23, 16), bev_lit_rgb=(148, 166, 142), bev_sh_rgb=(4, 6, 4), honeycomb_gain=0.18)

# 3. URBAN / ARCTIC CAMO (bg_lcd_camo_urban.png)
src_arctic_path = os.path.join(EXPORT_DIR, "source_camo_arctic.png")
if not os.path.exists(src_arctic_path):
    alt_arctic_path = "C:/Users/bonst/.gemini/antigravity/brain/d3a6c7d4-5613-437a-a72c-e90fec512f25/.user_uploaded/media_1792236990592_a7ef715c.png"
    if os.path.exists(alt_arctic_path):
        raw_crop = Image.open(alt_arctic_path).crop((0, 0, 1024, 1024))
        raw_crop.save(src_arctic_path)

camo_arctic_src = Image.open(src_arctic_path).convert("RGB")
w_src, h_src = camo_arctic_src.size
zoom_factor = 1.8
cw, ch = w_src / zoom_factor, h_src / zoom_factor
x1 = (w_src - cw) / 2.0
y1 = (h_src - ch) / 2.0
camo_arctic_cropped = camo_arctic_src.crop((int(round(x1)), int(round(y1)), int(round(x1 + cw)), int(round(y1 + ch))))
camo_arctic_resized = camo_arctic_cropped.resize((W, H), Image.Resampling.LANCZOS)
arr_arctic = np.array(camo_arctic_resized, dtype=float)
vig_arctic = np.array(vig_map).reshape((H, W))
disc_arctic = np.array(inside_disc).reshape((H, W))

arr_arctic_vig = np.clip(arr_arctic * vig_arctic[:, :, np.newaxis], 0, 255).astype(np.uint8)
alpha_arctic = (disc_arctic * 255).astype(np.uint8)
img_03 = Image.fromarray(np.dstack([arr_arctic_vig, alpha_arctic]))

apply_pods_and_subdial_housing_2x(
    img_03,
    floor_rgb=(16, 18, 22),
    bev_lit_rgb=(175, 185, 200),
    bev_sh_rgb=(3, 4, 6),
    honeycomb_gain=0.18,
    sub_base_f=(38.0, 42.0, 48.0),
    sub_spec_f=(175.0, 188.0, 205.0),
    well_rgb=(15.0, 17.0, 21.0),
)
save_bg_from_2x(img_03, "bg_lcd_camo_urban.png")
save_quad_chamber_3d(3, floor_rgb=(16, 18, 22), bev_lit_rgb=(175, 185, 200), bev_sh_rgb=(3, 4, 6), honeycomb_gain=0.18)

# Generate ic_cfg_bgtexture_3.png icon via generate_setting_icons
try:
    import generate_setting_icons as gsi
    if os.path.exists("C:/Windows/Fonts/arialbd.ttf"):
        gsi.ROB_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"
        gsi.ROB_REG_PATH = "C:/Windows/Fonts/arial.ttf"
    crop_bg_tex = (28, 28, 178, 178)
    wf3 = gsi.render_watchface(bg_texture=3, bg_border=0)
    icon_img3 = gsi.make_circular_icon(wf3, crop_bg_tex)
    icon_img3.save(os.path.join(OUTPUT_DIR, "ic_cfg_bgtexture_3.png"), optimize=True)
    print("Saved updated ic_cfg_bgtexture_3.png via gsi!")
except Exception as e:
    print("Icon update error:", e)

# 4. DESERT CAMO (bg_lcd_camo_desert.png)
camo_desert = [(68, 54, 40), (124, 102, 78), (170, 146, 116), (208, 186, 154)]
img_04 = build_3d_camo_plate((148, 126, 98), camo_desert, seed_val=88, count_inner=22, count_outer=26, rx_range=(20, 48), ry_range=(14, 32))
apply_pods_and_subdial_housing_2x(
    img_04,
    floor_rgb=(21, 17, 12),
    bev_lit_rgb=(185, 165, 138),
    bev_sh_rgb=(6, 5, 3),
    honeycomb_gain=0.18,
    sub_base_f=(48.0, 42.0, 32.0),
    sub_spec_f=(195.0, 180.0, 155.0),
    well_rgb=(20.0, 16.0, 11.0),
)
save_bg_from_2x(img_04, "bg_lcd_camo_desert.png")
save_quad_chamber_3d(4, floor_rgb=(21, 17, 12), bev_lit_rgb=(185, 165, 138), bev_sh_rgb=(6, 5, 3), honeycomb_gain=0.18)

# 5. ZEBRA CAMO (bg_lcd_camo_zebra.png)
camo_zebra = [(18, 20, 24), (45, 48, 54), (160, 165, 175), (215, 220, 228)]
img_05 = build_3d_camo_plate((88, 92, 102), camo_zebra, seed_val=19, count_inner=28, count_outer=32, rx_range=(12, 34), ry_range=(24, 60))
apply_pods_and_subdial_housing_2x(
    img_05,
    floor_rgb=(12, 15, 20),
    bev_lit_rgb=(155, 170, 192),
    bev_sh_rgb=(3, 4, 6),
    honeycomb_gain=0.18,
    sub_base_f=(34.0, 38.0, 46.0),
    sub_spec_f=(165.0, 180.0, 205.0),
    well_rgb=(12.0, 15.0, 20.0),
)
save_bg_from_2x(img_05, "bg_lcd_camo_zebra.png")
save_quad_chamber_3d(5, floor_rgb=(12, 15, 20), bev_lit_rgb=(155, 170, 192), bev_sh_rgb=(3, 4, 6), honeycomb_gain=0.18)

# 6. CARBON FIBER (bg_lcd_carbon_fiber.png)
pitch_cf = 12 * scale
twill = bytearray(pitch_cf * pitch_cf)
for ty in range(pitch_cf):
    for tx in range(pitch_cf):
        v = math.sin((tx + ty) / float(pitch_cf) * 2.0 * math.pi) * 0.5 + 0.5
        v2 = math.cos((tx - ty) / float(pitch_cf) * 2.0 * math.pi) * 0.5 + 0.5
        twill[ty * pitch_cf + tx] = int((0.6 * v + 0.4 * v2) * 255.0)

cf_bytes = bytearray(W * H * 4)
for y in range(H):
    row_off = y * W
    py = (y % pitch_cf) * pitch_cf
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            px = x % pitch_cf
            cf_val = twill[py + px] / 255.0
            con = conical_map[i]
            t = t_rad_map[i]
            base = 18.0 + 16.0 * cf_val + 14.0 * con - 8.0 * t
            vg = vig_map[i]
            rv = (base * 0.95) * vg
            gv = (base * 1.00) * vg
            bv = (base * 1.12) * vg
            idx = i * 4
            cf_bytes[idx]   = int(max(0, min(255, rv)))
            cf_bytes[idx+1] = int(max(0, min(255, gv)))
            cf_bytes[idx+2] = int(max(0, min(255, bv)))
            cf_bytes[idx+3] = 255

img_06 = Image.frombytes("RGBA", (W, H), bytes(cf_bytes))
apply_pods_and_subdial_housing_2x(
    img_06,
    floor_rgb=(13, 16, 21),
    bev_lit_rgb=(145, 162, 185),
    bev_sh_rgb=(3, 5, 8),
    honeycomb_gain=0.18,
    sub_base_f=(32.0, 36.0, 44.0),
    sub_spec_f=(160.0, 175.0, 198.0),
    well_rgb=(12.0, 15.0, 20.0),
)
save_bg_from_2x(img_06, "bg_lcd_carbon_fiber.png")
save_quad_chamber_3d(6, floor_rgb=(13, 16, 21), bev_lit_rgb=(145, 162, 185), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.18)

# 7. GLOSS PIANO BLACK (bg_lcd_gloss_black.png)
gp_bytes = bytearray(W * H * 4)
for y in range(H):
    row_off = y * W
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            con = conical_map[i]
            t = t_rad_map[i]
            base = 6.0 + 8.0 * (con ** 3.0) + 4.0 * (1.0 - t)
            idx = i * 4
            gp_bytes[idx]   = int(base * 0.9)
            gp_bytes[idx+1] = int(base * 0.95)
            gp_bytes[idx+2] = int(base * 1.1)
            gp_bytes[idx+3] = 255
img_07 = Image.frombytes("RGBA", (W, H), bytes(gp_bytes))
apply_pods_and_subdial_housing_2x(
    img_07,
    floor_rgb=(7, 9, 12),
    bev_lit_rgb=(165, 185, 215),
    bev_sh_rgb=(2, 3, 5),
    honeycomb_gain=0.12,
    sub_base_f=(22.0, 26.0, 32.0),
    sub_spec_f=(185.0, 205.0, 235.0),
    well_rgb=(6.0, 8.0, 11.0),
    gloss_ar=True,
)
save_bg_from_2x(img_07, "bg_lcd_gloss_black.png")
save_quad_chamber_3d(7, floor_rgb=(7, 9, 12), bev_lit_rgb=(165, 185, 215), bev_sh_rgb=(2, 3, 5), honeycomb_gain=0.12, gloss_ar=True)

# 8. CYBER GRID (bg_lcd_grid.png)
grid_bytes = bytearray(W * H * 4)
grid_pitch = 16 * scale
for y in range(H):
    row_off = y * W
    is_gy = (y % grid_pitch < 2)
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            is_gx = (x % grid_pitch < 2)
            con = conical_map[i]
            line_val = 14.0 if (is_gx or is_gy) else 0.0
            base = 18.0 + 16.0 * con + line_val
            vg = vig_map[i]
            idx = i * 4
            grid_bytes[idx]   = int(base * 0.85 * vg)
            grid_bytes[idx+1] = int(base * 1.05 * vg)
            grid_bytes[idx+2] = int(base * 1.25 * vg)
            grid_bytes[idx+3] = 255
img_08 = Image.frombytes("RGBA", (W, H), bytes(grid_bytes))
apply_pods_and_subdial_housing_2x(
    img_08,
    floor_rgb=(15, 20, 24),
    bev_lit_rgb=(138, 168, 196),
    bev_sh_rgb=(3, 5, 8),
    honeycomb_gain=0.20,
    sub_base_f=(30.0, 38.0, 46.0),
    sub_spec_f=(155.0, 185.0, 215.0),
    well_rgb=(14.0, 19.0, 23.0),
)
save_bg_from_2x(img_08, "bg_lcd_grid.png")
save_quad_chamber_3d(8, floor_rgb=(15, 20, 24), bev_lit_rgb=(138, 168, 196), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.20)

# 9. TACTICAL MESH (bg_lcd_tactical_mesh.png)
mesh_bytes = bytearray(W * H * 4)
m_pitch = 8 * scale
for y in range(H):
    row_off = y * W
    my = y % m_pitch
    for x in range(W):
        i = row_off + x
        if inside_disc[i]:
            mx = x % m_pitch
            d_hole = math.hypot(mx - m_pitch/2.0, my - m_pitch/2.0)
            hole_factor = max(0.0, min(1.0, (d_hole - 1.8 * scale) / 1.2))
            con = conical_map[i]
            base = (14.0 + 18.0 * con) * (0.4 + 0.6 * hole_factor)
            vg = vig_map[i]
            idx = i * 4
            mesh_bytes[idx]   = int(base * 0.92 * vg)
            mesh_bytes[idx+1] = int(base * 0.98 * vg)
            mesh_bytes[idx+2] = int(base * 1.08 * vg)
            mesh_bytes[idx+3] = 255
img_09 = Image.frombytes("RGBA", (W, H), bytes(mesh_bytes))
apply_pods_and_subdial_housing_2x(
    img_09,
    floor_rgb=(13, 17, 22),
    bev_lit_rgb=(142, 160, 184),
    bev_sh_rgb=(3, 5, 8),
    honeycomb_gain=0.18,
    sub_base_f=(28.0, 34.0, 42.0),
    sub_spec_f=(150.0, 172.0, 198.0),
    well_rgb=(12.0, 16.0, 21.0),
)
save_bg_from_2x(img_09, "bg_lcd_tactical_mesh.png")
save_quad_chamber_3d(9, floor_rgb=(13, 17, 22), bev_lit_rgb=(142, 160, 184), bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.18)

# ==============================================================================
# 10..16. INDUSTRIAL SERIES
# ==============================================================================
pitch_a = 12 * scale
diff_mult_tile = [[1.0] * pitch_a for _ in range(pitch_a)]
spec_add_tile = [[0.0] * pitch_a for _ in range(pitch_a)]
spec_tile = [[0.0] * pitch_a for _ in range(pitch_a)]

for py in range(pitch_a):
    for px in range(pitch_a):
        dx_t = (px - pitch_a / 2.0) / (pitch_a / 2.0)
        dy_t = (py - pitch_a / 2.0) / (pitch_a / 2.0)
        dist_t = math.hypot(dx_t, dy_t)
        ao = min(1.0, dist_t * 1.2)
        diff_mult_tile[py][px] = 0.82 + 0.28 * ao
        spec_add_tile[py][px] = 42.0 * ao

ind_lut_idx = bytearray(W * H)
ind_mult_map = [0.0] * (W * H)
ind_sp_map = [0.0] * (W * H)

gx_ind, gy_ind = 276.0, 248.0
max_rad_ind = 600.0
dir_x_ind, dir_y_ind = 0.68, 0.733
rng_br = random.Random(77)
brush_rows = [rng_br.gauss(0.0, 0.04) for _ in range(H)]

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
    save_quad_chamber_3d(idx_bg, floor_rgb=floor_rgb, bev_lit_rgb=bev_lit_rgb, bev_sh_rgb=(3, 5, 8), honeycomb_gain=0.22)

# ==============================================================================
# GENERATE QUAD ARC OVERLAY & FACE PLATES (DARK, INVERT, & TEXTURES)
# ==============================================================================
centers = [(101, 231), (161, 118), (289, 118), (349, 231)]
r_outer_c = 39.0
r_inner_c = 31.5

# 1. Bezel overlay with transparent window
hi_dials = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d_hi = ImageDraw.Draw(hi_dials)

sh_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d_sh = ImageDraw.Draw(sh_layer)
for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ro2_d = int(r_outer_c * scale)
    d_sh.ellipse((c2x - ro2_d - 4, c2y - ro2_d + 4, c2x + ro2_d + 4, c2y + ro2_d + 10), fill=(0, 0, 0, 160))
sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(3.5 * scale))
hi_dials.alpha_composite(sh_layer)

flange_fill = (34, 41, 50, 255)
flange_out = (82, 95, 112, 255)
inner_bevel = (56, 66, 80, 255)

for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ro2_d = int(r_outer_c * scale)
    ri2_d = int(r_inner_c * scale)

    # Outer ring
    d_hi.ellipse((c2x - ro2_d, c2y - ro2_d, c2x + ro2_d, c2y + ro2_d), fill=flange_fill, outline=flange_out, width=2*scale)
    d_hi.ellipse((c2x - ro2_d + 3*scale, c2y - ro2_d + 3*scale, c2x + ro2_d - 3*scale, c2y + ro2_d - 3*scale), outline=inner_bevel, width=1*scale)

    # Clear window
    d_hi.ellipse((c2x - ri2_d, c2y - ri2_d, c2x + ri2_d, c2y + ri2_d), fill=(0, 0, 0, 0))

    # Inner shadow & highlight on the inner rim
    d_hi.arc((c2x - ri2_d, c2y - ri2_d, c2x + ri2_d, c2y + ri2_d), start=180, end=360, fill=(0, 0, 0, 240), width=2*scale)
    d_hi.arc((c2x - ri2_d, c2y - ri2_d, c2x + ri2_d, c2y + ri2_d), start=0, end=180, fill=(65, 78, 95, 140), width=1*scale)

    # 4 screws on bezel
    r_screw_pos = (r_inner_c + r_outer_c) / 2.0 * scale
    r_screw = 2.2 * scale
    for deg in (45, 135, 225, 315):
        s_rad = math.radians(deg)
        sx = c2x + r_screw_pos * math.cos(s_rad)
        sy = c2y + r_screw_pos * math.sin(s_rad)
        d_hi.ellipse((sx - r_screw, sy - r_screw, sx + r_screw, sy + r_screw), fill=(20, 25, 32, 255), outline=(95, 112, 135, 255), width=1)

dials_450 = hi_dials.resize((450, 450), Image.Resampling.LANCZOS)
dials_450.save(os.path.join(OUTPUT_DIR, "quad_arc_overlay.png"))
print("Saved windowed quad_arc_overlay.png")

# 2. Quad Arc Face Dark
face_dark_hi = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d_dark = ImageDraw.Draw(face_dark_hi)
for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ri2_d = int(r_inner_c * scale) + 2
    d_dark.ellipse((c2x - ri2_d, c2y - ri2_d, c2x + ri2_d, c2y + ri2_d), fill=(12, 15, 20, 255))
face_dark_450 = face_dark_hi.resize((450, 450), Image.Resampling.LANCZOS)
face_dark_450.save(os.path.join(OUTPUT_DIR, "quad_arc_face_dark.png"))
print("Saved quad_arc_face_dark.png")

# 3. Quad Arc Invert Default
face_inv_hi = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d_inv = ImageDraw.Draw(face_inv_hi)
for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ri2_d = int(r_inner_c * scale) + 2
    d_inv.ellipse((c2x - ri2_d, c2y - ri2_d, c2x + ri2_d, c2y + ri2_d), fill=(16, 18, 22, 255))

inv_arr = np.zeros((H, W, 4), dtype=np.uint8)
Y_g, X_g = np.ogrid[:H, :W]
for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ri2_d = int(r_inner_c * scale) + 2
    dist_sq = (X_g - c2x)**2 + (Y_g - c2y)**2
    mask = dist_sq <= ri2_d**2
    inv_arr[mask, 0] = 242
    inv_arr[mask, 1] = 246
    inv_arr[mask, 2] = 250
    inv_arr[mask, 3] = 210

scan_rows = (Y_g % (3 * scale) < scale).squeeze()
inv_arr[scan_rows, :, :3] = (inv_arr[scan_rows, :, :3] * 0.92).astype(np.uint8)
face_inv_hi.alpha_composite(Image.fromarray(inv_arr))

sh_inv_hi = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d_sh_inv = ImageDraw.Draw(sh_inv_hi)
for cx_d, cy_d in centers:
    c2x, c2y = int(cx_d * scale), int(cy_d * scale)
    ri2_d = int(r_inner_c * scale)
    for r_step in range(int(10 * scale)):
        alpha_step = int(140 * (1.0 - r_step / (10 * scale))**1.5)
        d_sh_inv.arc((c2x - ri2_d + r_step, c2y - ri2_d + r_step, c2x + ri2_d - r_step, c2y + ri2_d - r_step),
                     start=180, end=360, fill=(14, 18, 24, alpha_step), width=scale)

face_inv_hi.alpha_composite(sh_inv_hi)
face_inv_450 = face_inv_hi.resize((450, 450), Image.Resampling.LANCZOS)
face_inv_450.save(os.path.join(OUTPUT_DIR, "tex_arc_invert_default.png"))
print("Saved tex_arc_invert_default.png")

# 4. Textures
tex_configs = [
    ('tex_screen_hex_light.png',   'tex_arc_hex_light.png',   'tex_arc_invert_hex_light.png',   True,  0.14, 0.00, 1.00),
    ('tex_screen_hex_dark.png',    'tex_arc_hex_dark.png',    'tex_arc_invert_hex_dark.png',    False, 0.22, 0.07, 0.78),
    ('tex_screen_moire_light.png', 'tex_arc_moire_light.png', 'tex_arc_invert_moire_light.png', True,  0.15, 0.00, 1.00),
    ('tex_screen_moire_dark.png',  'tex_arc_moire_dark.png',  'tex_arc_invert_moire_dark.png',  True,  0.30, 0.08, 0.65),
]

arc_mask_450 = np.zeros((450, 450), dtype=float)
Y450, X450 = np.ogrid[:450, :450]
for cx_d, cy_d in centers:
    dist_sq = (X450 - cx_d)**2 + (Y450 - cy_d)**2
    m = np.clip((r_inner_c + 0.5 - np.sqrt(dist_sq)), 0.0, 1.0)
    arc_mask_450 = np.maximum(arc_mask_450, m)

for src_name, dark_out_name, inv_out_name, inv_polarity, contrast_str, base_dark, dark_scale in tex_configs:
    src_file = os.path.join(OUTPUT_DIR, src_name)
    if not os.path.exists(src_file):
        continue
    raw_tex = Image.open(src_file).convert('RGBA')
    raw_arr = np.array(raw_tex).astype(float)
    tw, th = raw_tex.size

    tiled_v = np.zeros((450, 450), dtype=float)
    tiled_a = np.zeros((450, 450), dtype=float)
    for y in range(450):
        for x in range(450):
            tiled_v[y, x] = raw_arr[y % th, x % tw, 0] / 255.0
            tiled_a[y, x] = raw_arr[y % th, x % tw, 3] / 255.0

    dark_pure_op = tiled_a * tiled_v * dark_scale * arc_mask_450
    dark_arr = np.zeros((450, 450, 4), dtype=np.uint8)
    dark_arr[:, :, 0] = 255
    dark_arr[:, :, 1] = 255
    dark_arr[:, :, 2] = 255
    dark_arr[:, :, 3] = (dark_pure_op * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(dark_arr).save(os.path.join(OUTPUT_DIR, dark_out_name))

    valid_v = raw_arr[:, :, 0]
    v_min, v_max = np.percentile(valid_v, 2), np.percentile(valid_v, 98)
    pat_norm = np.clip((tiled_v - v_min/255.0) / max(0.01, (v_max - v_min)/255.0), 0.0, 1.0)
    pattern_darkness = (1.0 - pat_norm) if inv_polarity else pat_norm
    pat_dark_alpha = (base_dark + pattern_darkness * contrast_str) * arc_mask_450

    inv_t_arr = np.zeros((450, 450, 4), dtype=np.uint8)
    inv_t_arr[:, :, 0] = 14
    inv_t_arr[:, :, 1] = 18
    inv_t_arr[:, :, 2] = 24
    inv_t_arr[:, :, 3] = (pat_dark_alpha * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(inv_t_arr).save(os.path.join(OUTPUT_DIR, inv_out_name))

print(f"All 17 clean full-bleed backgrounds, quad_chambers, and quad arc assets generated in {time.time() - t0:.1f}s!")

