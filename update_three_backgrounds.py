import os, math, random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")
EXPORT_DIR = os.path.join(BASE_DIR, "exported_backgrounds_for_photoshop")

cx, cy = 225, 225
scx, scy = 352, 323
r_outer = 38.0 * 1.3   # 49.4px
r_inner = 30.5 * 1.3   # 39.65px
gap_dist = 9.6
r_cut = r_outer + gap_dist  # 59.0px

scale = 2
w, h = 450 * scale, 450 * scale
CORNER_RADIUS = 12
r_c2 = CORNER_RADIUS * scale
scx_2, scy_2 = scx * scale, scy * scale
r_cut_2 = r_cut * scale

def make_curved_chamber_mask(W, H, x1, y1, x2, y2, r_corner, scx_2=None, scy_2=None, r_cut_2=0, fillet_r=16):
    cx_r = (x1 + x2) / 2.0
    cy_r = (y1 + y2) / 2.0
    hx = (x2 - x1) / 2.0 - r_corner
    hy = (y2 - y1) / 2.0 - r_corner
    k = float(fillet_r)
    has_cut = (r_cut_2 > 0 and scx_2 is not None)

    m_u8 = bytearray(W * H)
    b_u8 = bytearray(W * H)

    ix1 = max(0, int(x1 - 6))
    ix2 = min(W, int(x2 + 6))
    iy1 = max(0, int(y1 - 6))
    iy2 = min(H, int(y2 + 6))

    for y in range(iy1, iy2):
        dy0 = abs(y - cy_r) - hy
        dy = dy0 if dy0 > 0.0 else 0.0
        dy_sq = dy * dy
        if has_cut:
            dy_sc_sq = (y - scy_2) ** 2
        row_off = y * W
        for x in range(ix1, ix2):
            dx0 = abs(x - cx_r) - hx
            dx = dx0 if dx0 > 0.0 else 0.0
            m_xy = dx0 if dx0 > dy0 else dy0
            sdf_rect = math.sqrt(dx * dx + dy_sq) + (m_xy if m_xy < 0.0 else 0.0) - r_corner
            if not has_cut:
                sdf_c = sdf_rect
            else:
                dist_sc = math.sqrt((x - scx_2) ** 2 + dy_sc_sq)
                sdf_excl = r_cut_2 - dist_sc
                u = sdf_rect + k
                if u < 0.0: u = 0.0
                v = sdf_excl + k
                if v < 0.0: v = 0.0
                mx = sdf_rect if sdf_rect > sdf_excl else sdf_excl
                mn = mx if mx < -k else -k
                sdf_c = mn + math.sqrt(u * u + v * v)

            a = 0.5 - sdf_c / 1.2
            if a > 0.0:
                m_u8[row_off + x] = 255 if a >= 1.0 else int(a * 255.0)
            ba = 1.0 - abs(sdf_c + 1.0) / 1.1
            if ba > 0.0:
                b_u8[row_off + x] = 255 if ba >= 1.0 else int(ba * 255.0)

    return Image.frombytes("L", (W, H), bytes(m_u8)), Image.frombytes("L", (W, H), bytes(b_u8))

QUAD_PODS = [(72, 138), (152, 218), (232, 298), (312, 378)]
QUAD_Y1, QUAD_Y2 = 90, 168

chamber_specs_2x = []
for x1_q, x2_q in QUAD_PODS:
    m_img, b_img = make_curved_chamber_mask(w, h, x1_q*scale, QUAD_Y1*scale, x2_q*scale, QUAD_Y2*scale, r_c2, None, None, 0)
    chamber_specs_2x.append(("quad", m_img, b_img))

m_main, b_main = make_curved_chamber_mask(w, h, 70*scale, 178*scale, 380*scale, 284*scale, r_c2, scx_2, scy_2, r_cut_2, fillet_r=16)
chamber_specs_2x.append(("main", m_main, b_main))

m_slot5, b_slot5 = make_curved_chamber_mask(w, h, 70*scale, 302*scale, 305*scale, 358*scale, r_c2, scx_2, scy_2, r_cut_2, fillet_r=16)
chamber_specs_2x.append(("slot5", m_slot5, b_slot5))

# Extract exact 'START' text overlay from existing bg_lcd_real.png
orig_real = Image.open(os.path.join(OUTPUT_DIR, "bg_lcd_real.png")).convert("RGBA")
start_overlay = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
# Reconstruct background of bg_lcd_real.png in x=384..418, y=166..180 without text
ref_real = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
d_ref = ImageDraw.Draw(ref_real)
d_ref.ellipse((0, 0, 450, 450), fill=(0, 0, 0, 255))
d_ref.ellipse((26, 26, 424, 424), fill=(18, 22, 28, 255), outline=(26, 32, 40, 255), width=1)
d_ref.ellipse((38, 38, 412, 412), outline=(36, 44, 54, 255), width=1)
d_ref.ellipse((39, 39, 411, 411), fill=(30, 37, 43, 255))
grid_ref = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
gd_ref = ImageDraw.Draw(grid_ref)
for y in range(40, 410, 3):
    dy_v = abs(y - cy)
    if dy_v < 184:
        hw = math.sqrt(184**2 - dy_v**2)
        gd_ref.line([(cx - hw + 4, y), (cx + hw - 4, y)], fill=(255, 255, 255, 16), width=1)
ref_real.alpha_composite(grid_ref)

for y in range(166, 180):
    for x in range(384, 420):
        pr, pg, pb, _ = orig_real.getpixel((x, y))
        br, bg, bb, _ = ref_real.getpixel((x, y))
        if pr > br and (105 - br) > 0:
            alpha_f = (pr - br) / float(105 - br)
            a_u8 = min(255, max(0, int(round(alpha_f * 255.0))))
            if a_u8 > 0:
                start_overlay.putpixel((x, y), (105, 118, 136, a_u8))

def draw_bezel_and_track(draw, bezel_fill=(18, 22, 28, 255)):
    draw.ellipse((0, 0, 450, 450), fill=(0, 0, 0, 255))
    draw.ellipse((26, 26, 424, 424), fill=bezel_fill, outline=(26, 32, 40, 255), width=1)
    draw.ellipse((38, 38, 412, 412), outline=(36, 44, 54, 255), width=1)

def draw_chambers_and_subdial(img, base_rgb):
    ch_rgb = (max(0, base_rgb[0]-8), max(0, base_rgb[1]-8), max(0, base_rgb[2]-8))
    outline_col = (48, 58, 72, 255)

    hi_chambers = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for kind, m_img, b_img in chamber_specs_2x:
        if kind == "quad":
            m_scaled = m_img.point(lambda p: int(round(p * 0.94)))
        else:
            m_scaled = m_img
        fill_layer = Image.new("RGBA", (w, h), (*ch_rgb, 0))
        fill_layer.putalpha(m_scaled)
        hi_chambers.alpha_composite(fill_layer)

        b_layer = Image.new("RGBA", (w, h), (*outline_col[:3], 0))
        b_layer.putalpha(b_img)
        hi_chambers.alpha_composite(b_layer)

    img.alpha_composite(hi_chambers.resize((450, 450), Image.Resampling.LANCZOS))

    hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dhi = ImageDraw.Draw(hi)
    cx2, cy2 = int(round(scx * scale)), int(round(scy * scale))
    ro2 = int(round(r_outer * scale))
    ri2 = int(round(r_inner * scale))

    sh_ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh_ring).ellipse((cx2-ro2-2, cy2-ro2+2, cx2+ro2+2, cy2+ro2+6), fill=(0, 0, 0, 115))
    sh_ring = sh_ring.filter(ImageFilter.GaussianBlur(3.5))
    hi.alpha_composite(sh_ring)

    flange_fill = (34, 41, 50, 255)
    flange_out = (82, 95, 112, 255)
    dhi.ellipse((cx2-ro2, cy2-ro2, cx2+ro2, cy2+ro2), fill=flange_fill, outline=flange_out, width=2)
    dhi.ellipse((cx2-ro2+3, cy2-ro2+3, cx2+ro2-3, cy2+ro2-3), outline=(56, 66, 80, 255), width=2)

    r_screw_pos = (r_inner + r_outer) / 2.0 * scale
    r_screw = 2.9 * 1.3 * scale
    for deg in (45, 135, 225, 315):
        rad = math.radians(deg)
        sx = cx2 + r_screw_pos * math.cos(rad)
        sy = cy2 + r_screw_pos * math.sin(rad)
        dhi.ellipse((sx-r_screw, sy-r_screw, sx+r_screw, sy+r_screw), fill=(78, 90, 108, 255), outline=(20, 24, 30, 255), width=1)
        slot_ang = rad + math.pi/4
        dx_s = (r_screw - 1.8) * math.cos(slot_ang)
        dy_s = (r_screw - 1.8) * math.sin(slot_ang)
        dhi.line([(sx-dx_s, sy-dy_s), (sx+dx_s, sy+dy_s)], fill=(24, 28, 34, 255), width=2)

    dhi.ellipse((cx2-ri2, cy2-ri2, cx2+ri2, cy2+ri2), fill=(*ch_rgb, 255), outline=outline_col, width=2)
    img.alpha_composite(hi.resize((450, 450), Image.Resampling.LANCZOS))

# Build directional inner shadow layer (user_shadow)
shadow_layer_hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
dx = -4 * scale
dy = 5 * scale
blur_radius = 5 * scale / 2.0
alpha_val = int(255 * 0.58)

for kind, m_img, _ in chamber_specs_2x:
    inv_mask = m_img.point(lambda p: 255 - p)
    shifted_inv = Image.new("L", (w, h), 255)
    shifted_inv.paste(inv_mask, (dx, dy))
    blurred_inv = shifted_inv.filter(ImageFilter.GaussianBlur(blur_radius))

    m_bytes = m_img.tobytes()
    b_bytes = blurred_inv.tobytes()
    sh_bytes = bytearray(w * h)
    for i in range(w * h):
        mv = m_bytes[i]
        if mv:
            bv = b_bytes[i]
            if bv:
                sh_bytes[i] = (mv * bv * alpha_val) // (255 * 255)
    sh_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh_img.putalpha(Image.frombytes("L", (w, h), bytes(sh_bytes)))
    shadow_layer_hi.alpha_composite(sh_img)

c_mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(c_mask).ellipse((int(round((scx-r_inner)*scale)), int(round((scy-r_inner)*scale)), int(round((scx+r_inner)*scale)), int(round((scy+r_inner)*scale))), fill=255)
c_inv = Image.new("L", (w, h), 255)
ImageDraw.Draw(c_inv).ellipse((int(round((scx-r_inner)*scale)), int(round((scy-r_inner)*scale)), int(round((scx+r_inner)*scale)), int(round((scy+r_inner)*scale))), fill=0)
c_shift = Image.new("L", (w, h), 255)
c_shift.paste(c_inv, (-3 * scale, 4 * scale))
c_blur = c_shift.filter(ImageFilter.GaussianBlur(4.5 * scale / 2.0))
cm_bytes = c_mask.tobytes()
cb_bytes = c_blur.tobytes()
c_alpha_val = int(255 * 0.56)
csh_bytes = bytearray(w * h)
for i in range(w * h):
    mv = cm_bytes[i]
    if mv:
        bv = cb_bytes[i]
        if bv:
            csh_bytes[i] = (mv * bv * c_alpha_val) // (255 * 255)
csh_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
csh_img.putalpha(Image.frombytes("L", (w, h), bytes(csh_bytes)))
shadow_layer_hi.alpha_composite(csh_img)

user_shadow = shadow_layer_hi.resize((450, 450), Image.Resampling.LANCZOS)

def save_all_places(img, filename):
    for d in (OUTPUT_DIR, EXPORT_DIR, BASE_DIR):
        if os.path.isdir(d):
            img.save(os.path.join(d, filename))
    print(f"Saved: {filename}")

# ==============================================================================
# 1. MATTE BLACK WITH VERY DARK GREY OFF-CENTER RADIAL GRADIENT
# ==============================================================================
img_matte = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
d_matte = ImageDraw.Draw(img_matte)
draw_bezel_and_track(d_matte, (12, 13, 15, 255))

# Off-center radial gradient inside dial plate (39..411)
# Focal center in upper-left quadrant at (142, 130)
gx, gy = 142.0, 130.0
max_d = 265.0
# Peak color at focal center: neutral very dark grey (40, 41, 43) -> fading to deep matte black (8, 9, 10)
r_peak, g_peak, b_peak = 40.0, 41.0, 43.0
r_edge, g_edge, b_edge = 8.0, 9.0, 10.0

rng_mb = random.Random(101)
matte_bytes = bytearray(450 * 450 * 4)
for y in range(39, 412):
    dy_c = y - cy
    for x in range(39, 412):
        dx_c = x - cx
        if dx_c*dx_c + dy_c*dy_c <= 186.5**2:
            dist = math.hypot(x - gx, y - gy)
            t = min(1.0, dist / max_d) ** 1.15
            # Smooth falloff with subtle matte micro-grain dither
            n = rng_mb.gauss(0.0, 0.5)
            rv = int(min(255, max(0, round(r_peak + (r_edge - r_peak) * t + n))))
            gv = int(min(255, max(0, round(g_peak + (g_edge - g_peak) * t + n))))
            bv = int(min(255, max(0, round(b_peak + (b_edge - b_peak) * t + n))))
            idx = (y * 450 + x) * 4
            matte_bytes[idx] = rv
            matte_bytes[idx+1] = gv
            matte_bytes[idx+2] = bv
            matte_bytes[idx+3] = 255

dial_mask = Image.new("L", (450, 450), 0)
ImageDraw.Draw(dial_mask).ellipse((39, 39, 411, 411), fill=255)
matte_surf = Image.frombytes("RGBA", (450, 450), bytes(matte_bytes))
img_matte.paste(matte_surf, (0, 0), dial_mask)

draw_chambers_and_subdial(img_matte, (14, 15, 17))
img_matte.alpha_composite(start_overlay)
img_matte.alpha_composite(user_shadow)
save_all_places(img_matte, "bg_lcd_matte_black.png")

# ==============================================================================
# 2. LIGHTER CARBON FIBRE WEAVE
# ==============================================================================
img_carbon = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
dc = ImageDraw.Draw(img_carbon)
draw_bezel_and_track(dc, (20, 23, 28, 255))
dc.ellipse((39, 39, 411, 411), fill=(24, 27, 32, 255))
carbon_layer = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
cdraw_cf = ImageDraw.Draw(carbon_layer)
bw = 6
for y in range(40, 410, bw):
    for x in range(40, 410, bw):
        if (x + bw//2 - cx)**2 + (y + bw//2 - cy)**2 < 185**2:
            bx = x // bw
            by = y // bw
            twill = (bx + by) % 4
            if twill in (0, 1):
                for sy in range(bw):
                    # Lifted from (22 + 18*sin) to (34 + 34*sin) so weave highlights reach ~68
                    shade = int(34 + 34 * math.sin(((sy + 0.5) / bw) * math.pi))
                    cdraw_cf.line([(x, y + sy), (x + bw - 1, y + sy)], fill=(shade, shade + 4, shade + 8, 230), width=1)
            else:
                for sx in range(bw):
                    # Lifted from (14 + 14*sin) to (18 + 20*sin) so orthogonal strands reach ~38
                    shade = int(18 + 20 * math.sin(((sx + 0.5) / bw) * math.pi))
                    cdraw_cf.line([(x + sx, y), (x + sx, y + bw - 1)], fill=(shade, shade + 2, shade + 5, 220), width=1)

carbon_clipped = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
carbon_clipped.paste(carbon_layer, (0, 0), dial_mask)
img_carbon.alpha_composite(carbon_clipped)
draw_chambers_and_subdial(img_carbon, (22, 25, 30))
img_carbon.alpha_composite(start_overlay)
img_carbon.alpha_composite(user_shadow)
save_all_places(img_carbon, "bg_lcd_carbon_fiber.png")

# ==============================================================================
# 3. LIGHTER TACTICAL RAISED MESH (3D Normal-Mapped Micro-Waffle)
# ==============================================================================
img_mesh = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
dm = ImageDraw.Draw(img_mesh)
draw_bezel_and_track(dm, (20, 24, 30, 255))

H_m, W_m = 900, 900
pitch_a = 9  # exact integer 9px pitch at 900x900 (4.5px at 450x450)

# Precompute 9x9 periodic heightfield Z_a and AO_a
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
        AO_tile[py][px] = 0.48 + 0.52 * (z ** 0.7)

# Precompute 9x9 periodic normal map & lighting terms (ndotl, spec)
lx_m, ly_m, lz_m = -0.48, -0.62, 0.62
l_len_m = math.sqrt(lx_m*lx_m + ly_m*ly_m + lz_m*lz_m)
lx_m, ly_m, lz_m = lx_m/l_len_m, ly_m/l_len_m, lz_m/l_len_m

hx_m, hy_m, hz_m = lx_m, ly_m, lz_m + 1.0
h_len_m = math.sqrt(hx_m*hx_m + hy_m*hy_m + hz_m*hz_m)
hx_m, hy_m, hz_m = hx_m/h_len_m, hy_m/h_len_m, hz_m/h_len_m

slope_scale = 2.6
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
        spec_tile[py][px] = nh ** 18.0

# Lifted base color from (26, 31, 37) to (46, 53, 62) with stronger diffuse & specular highlights
base_r, base_g, base_b = 46.0, 53.0, 62.0
tile_r = [[0.0]*pitch_a for _ in range(pitch_a)]
tile_g = [[0.0]*pitch_a for _ in range(pitch_a)]
tile_b = [[0.0]*pitch_a for _ in range(pitch_a)]
spec_term_tile = [[0.0]*pitch_a for _ in range(pitch_a)]
for py in range(pitch_a):
    for px in range(pitch_a):
        nd = ndotl_tile[py][px]
        ao = AO_tile[py][px]
        sp = 30.0 * spec_tile[py][px] * ao
        spec_term_tile[py][px] = sp
        diff_mult = 0.58 + 0.68 * nd
        diff_add = 22.0 * (nd - 0.5)
        tile_r[py][px] = (base_r * diff_mult + diff_add) * ao
        tile_g[py][px] = (base_g * diff_mult + diff_add) * ao
        tile_b[py][px] = (base_b * diff_mult + diff_add) * ao

rng_m = random.Random(42)
mesh_bytes = bytearray(W_m * H_m * 4)
# Only compute inside dial circle (78..822) for speed
for y in range(76, 824):
    py = y % pitch_a
    tr_row = tile_r[py]
    tg_row = tile_g[py]
    tb_row = tile_b[py]
    sp_row = spec_term_tile[py]
    ml_y = 0.16 * ((y - H_m*0.32)/(H_m*0.7))**2
    row_off = y * W_m * 4
    for x in range(76, 824):
        px = x % pitch_a
        macro_light = max(0.78, min(1.06, 1.02 - 0.16 * ((x - W_m*0.35)/(W_m*0.7))**2 - ml_y))
        fn = rng_m.gauss(0.0, 1.4)
        sp = sp_row[px] + fn
        rv = int(min(255, max(0, round(tr_row[px] * macro_light + sp))))
        gv = int(min(255, max(0, round(tg_row[px] * macro_light + sp))))
        bv = int(min(255, max(0, round(tb_row[px] * macro_light + sp))))
        idx = row_off + x * 4
        mesh_bytes[idx] = rv
        mesh_bytes[idx+1] = gv
        mesh_bytes[idx+2] = bv
        mesh_bytes[idx+3] = 255

surf_a = Image.frombytes("RGBA", (W_m, H_m), bytes(mesh_bytes)).resize((450, 450), Image.Resampling.LANCZOS)
mesh_clipped = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
mesh_clipped.paste(surf_a, (0, 0), dial_mask)

# Subtle radial inner bezel recess shadow around r=186 (39..411)
bezel_sh = Image.new("L", (450, 450), 255)
ImageDraw.Draw(bezel_sh).ellipse((42, 42, 408, 408), fill=0)
bezel_sh = bezel_sh.filter(ImageFilter.GaussianBlur(4.0))
b_bytes = bezel_sh.tobytes()
m_bytes = dial_mask.tobytes()
edge_bytes = bytearray(450 * 450)
for i in range(450 * 450):
    if m_bytes[i] and b_bytes[i]:
        edge_bytes[i] = (b_bytes[i] * m_bytes[i] * 130) // (255 * 255)
edge_sh = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
edge_sh.putalpha(Image.frombytes("L", (450, 450), bytes(edge_bytes)))
mesh_clipped.alpha_composite(edge_sh)

img_mesh.alpha_composite(mesh_clipped)
draw_chambers_and_subdial(img_mesh, (22, 26, 32))
img_mesh.alpha_composite(start_overlay)
img_mesh.alpha_composite(user_shadow)
save_all_places(img_mesh, "bg_lcd_tactical_mesh.png")

# ==============================================================================
# 4. DESERT CAMO (bg_lcd_camo_desert.png)
# ==============================================================================
img_desert = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
dd = ImageDraw.Draw(img_desert)
draw_bezel_and_track(dd, (36, 30, 22, 255))
dd.ellipse((39, 39, 411, 411), fill=(52, 43, 32, 255))

desert_layer = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
ddraw = ImageDraw.Draw(desert_layer)
rng_d = random.Random(77)
desert_colors = [
    (30, 24, 17, 190),   # Deep Espresso / Mud Brown
    (78, 65, 47, 175),   # Coyote Tan
    (104, 88, 64, 160),  # Desert Sand / Khaki
    (64, 53, 39, 165),   # Warm Dune Olive-Buff
]
for _ in range(60):
    bx = rng_d.randint(45, 405)
    by = rng_d.randint(45, 405)
    if (bx - cx)**2 + (by - cy)**2 < 178**2:
        rad_x = rng_d.randint(18, 50)
        rad_y = rng_d.randint(13, 40)
        col = rng_d.choice(desert_colors)
        ddraw.ellipse((bx - rad_x, by - rad_y, bx + rad_x, by + rad_y), fill=col)

desert_clipped = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
desert_clipped.paste(desert_layer, (0, 0), dial_mask)
img_desert.alpha_composite(desert_clipped)
draw_chambers_and_subdial(img_desert, (34, 28, 21))
img_desert.alpha_composite(start_overlay)
img_desert.alpha_composite(user_shadow)
save_all_places(img_desert, "bg_lcd_camo_desert.png")

# ==============================================================================
# 5. SUBTLE ZEBRA CAMO (bg_lcd_camo_zebra.png)
# ==============================================================================
img_zebra = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
dz = ImageDraw.Draw(img_zebra)
draw_bezel_and_track(dz, (18, 21, 26, 255))

# Generate 2x supersampled organic bifurcating zebra stripes inside dial circle
zebra_hi = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
z_bytes = bytearray(900 * 900 * 4)
ang_z = math.radians(-28.0)
ca_z, sa_z = math.cos(ang_z), math.sin(ang_z)

# Subtle dark charcoal base (17, 20, 24) with stealthy slate-grey zebra stripes (38, 43, 50)
for y in range(76, 824):
    dy = (y - 450.0)
    row_off = y * 900 * 4
    for x in range(76, 824):
        dx = (x - 450.0)
        if dx*dx + dy*dy <= 374.0**2:
            # Rotated coordinates
            u = dx * ca_z - dy * sa_z
            v = dx * sa_z + dy * ca_z
            # Multi-scale organic warp creating natural zebra stripe forks (Y-bifurcations) and V-chevrons
            w1 = 26.0 * math.sin(v * 0.014 + 0.7 * math.cos(u * 0.011))
            w2 = 14.0 * math.cos(v * 0.029 - u * 0.009 + 1.2)
            # Bifurcation phase modulation (causes stripes to split and merge like real zebra coat)
            fork = 1.35 * math.sin(v * 0.018 - 0.5) * math.cos((u + w1) * 0.045)
            phase = (u + w1 + w2) * 0.095 + fork
            val = math.sin(phase) + 0.28 * math.cos(2.0 * phase + 0.6 * math.sin(v * 0.022))
            # Smooth anti-aliased threshold around val > 0.08 for tapering zebra bands
            t = max(0.0, min(1.0, 0.5 + (val - 0.06) * 3.2))
            # Subtle radial shading so outer edge is slightly deeper
            vig = max(0.78, 1.0 - 0.16 * (dx*dx + dy*dy) / (374.0**2))
            r_v = int(round((16.0 + 25.0 * t) * vig))
            g_v = int(round((19.0 + 28.0 * t) * vig))
            b_v = int(round((23.0 + 33.0 * t) * vig))
            idx = row_off + x * 4
            z_bytes[idx] = r_v
            z_bytes[idx+1] = g_v
            z_bytes[idx+2] = b_v
            z_bytes[idx+3] = 255

zebra_surf = Image.frombytes("RGBA", (900, 900), bytes(z_bytes)).resize((450, 450), Image.Resampling.LANCZOS)
zebra_clipped = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
zebra_clipped.paste(zebra_surf, (0, 0), dial_mask)
img_zebra.alpha_composite(zebra_clipped)
draw_chambers_and_subdial(img_zebra, (20, 23, 28))
img_zebra.alpha_composite(start_overlay)
img_zebra.alpha_composite(user_shadow)
save_all_places(img_zebra, "bg_lcd_camo_zebra.png")
