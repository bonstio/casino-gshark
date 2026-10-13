import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

OUTPUT_DIR = 'app/src/main/res/drawable'
EXPORT_DIR = 'exported_backgrounds_for_photoshop'
BRAIN_DIR = r'C:\Users\bonst\.gemini\antigravity\brain\d3a6c7d4-5613-437a-a72c-e90fec512f25'

cx, cy = 225, 225
scx, scy = 352, 323
r_outer = 38.0 * 1.3   # 49.4px (30% larger)
r_inner = 30.5 * 1.3   # 39.65px (30% larger)
gap_dist = 9.6
r_cut = r_outer + gap_dist  # 59.0px concentric cutout radius

def make_curved_chamber_mask(W, H, x1, y1, x2, y2, r_corner, scx_2=None, scy_2=None, r_cut_2=0, fillet_r=16):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx_r = (x1 + x2) / 2.0
    cy_r = (y1 + y2) / 2.0
    hx = (x2 - x1) / 2.0 - r_corner
    hy = (y2 - y1) / 2.0 - r_corner
    dx = np.maximum(np.abs(xx - cx_r) - hx, 0.0)
    dy = np.maximum(np.abs(yy - cy_r) - hy, 0.0)
    sdf_rect = np.sqrt(dx*dx + dy*dy) + np.minimum(np.maximum(np.abs(xx - cx_r) - hx, np.abs(yy - cy_r) - hy), 0.0) - r_corner

    if r_cut_2 <= 0 or scx_2 is None:
        sdf_combined = sdf_rect
    else:
        dist_sc = np.sqrt((xx - scx_2)**2 + (yy - scy_2)**2)
        sdf_excl = r_cut_2 - dist_sc
        k = float(fillet_r)
        u = np.maximum(sdf_rect + k, 0.0)
        v = np.maximum(sdf_excl + k, 0.0)
        sdf_combined = np.minimum(np.maximum(sdf_rect, sdf_excl), -k) + np.sqrt(u*u + v*v)

    alpha = np.clip(0.5 - sdf_combined / 1.2, 0.0, 1.0)
    return (alpha * 255.0).astype(np.uint8), sdf_combined

# Precompute 2x chamber masks & directional inner shadows once for all 8 backgrounds + textures
scale = 2
w, h = 450 * scale, 450 * scale
CORNER_RADIUS = 12
r_c2 = CORNER_RADIUS * scale
scx_2, scy_2 = scx * scale, scy * scale
r_cut_2 = r_cut * scale

QUAD_PODS = [(72, 138), (152, 218), (232, 298), (312, 378)]
QUAD_Y1, QUAD_Y2 = 90, 168

chamber_specs_2x = []
for x1_q, x2_q in QUAD_PODS:
    m_u8, sdf_q = make_curved_chamber_mask(w, h, x1_q*scale, QUAD_Y1*scale, x2_q*scale, QUAD_Y2*scale, r_c2, None, None, 0)
    chamber_specs_2x.append(('quad', m_u8, sdf_q))

# Main Clock Chamber (x=70..380, y=178..284, lower-right corner curves around sub-dial)
m_main_u8, sdf_main = make_curved_chamber_mask(w, h, 70*scale, 178*scale, 380*scale, 284*scale, r_c2, scx_2, scy_2, r_cut_2, fillet_r=16)
chamber_specs_2x.append(('main', m_main_u8, sdf_main))

# Lower Slot 5 Complication Chamber (Option B: x=70..305, y=302..358, right edge curves concentrically around sub-dial)
m_slot5_u8, sdf_slot5 = make_curved_chamber_mask(w, h, 70*scale, 302*scale, 305*scale, 358*scale, r_c2, scx_2, scy_2, r_cut_2, fillet_r=16)
chamber_specs_2x.append(('slot5', m_slot5_u8, sdf_slot5))

def draw_bezel_and_track(draw, cx, cy, bezel_fill=(18, 22, 28, 255), gloss=False):
    # Solid #000000 circumference ring in the tick-mark track section (outside 26..424)
    draw.ellipse((0, 0, 450, 450), fill=(0, 0, 0, 255))
    if gloss:
        draw.ellipse((26, 26, 424, 424), fill=bezel_fill, outline=(65, 78, 95, 255), width=1)
        draw.ellipse((38, 38, 412, 412), outline=(85, 100, 120, 255), width=1)
    else:
        draw.ellipse((26, 26, 424, 424), fill=bezel_fill, outline=(26, 32, 40, 255), width=1)
        draw.ellipse((38, 38, 412, 412), outline=(36, 44, 54, 255), width=1)

def draw_chambers_and_subdial(img, base_rgb, gloss=False):
    ch_rgb = (max(0, base_rgb[0]-8), max(0, base_rgb[1]-8), max(0, base_rgb[2]-8))
    outline_col = (75, 90, 110, 255) if gloss else (48, 58, 72, 255)

    hi_chambers = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for kind, m_u8, sdf_c in chamber_specs_2x:
        fill_op = 0.94 if kind == 'quad' else 1.0
        fill_layer = np.zeros((h, w, 4), dtype=np.uint8)
        fill_layer[:, :, 0] = ch_rgb[0]
        fill_layer[:, :, 1] = ch_rgb[1]
        fill_layer[:, :, 2] = ch_rgb[2]
        fill_layer[:, :, 3] = (m_u8.astype(float) * fill_op).clip(0, 255).astype(np.uint8)
        hi_chambers.alpha_composite(Image.fromarray(fill_layer))

        border_a = np.clip(1.0 - np.abs(sdf_c + 1.0) / 1.1, 0.0, 1.0)
        b_layer = np.zeros((h, w, 4), dtype=np.uint8)
        b_layer[:, :, 0] = outline_col[0]
        b_layer[:, :, 1] = outline_col[1]
        b_layer[:, :, 2] = outline_col[2]
        b_layer[:, :, 3] = (border_a * 255.0).clip(0, 255).astype(np.uint8)
        hi_chambers.alpha_composite(Image.fromarray(b_layer))

    img.alpha_composite(hi_chambers.resize((450, 450), Image.Resampling.LANCZOS))

    # 4. Circular GA-100 Sub-Dial Housing at 2x supersampling (scx=352, scy=323, r_outer=49.4, r_inner=39.65)
    hi = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dhi = ImageDraw.Draw(hi)
    cx2, cy2 = int(round(scx * scale)), int(round(scy * scale))
    ro2 = int(round(r_outer * scale))
    ri2 = int(round(r_inner * scale))

    # Subtle outer drop shadow under the metallic bezel ring
    sh_ring = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh_ring).ellipse((cx2-ro2-2, cy2-ro2+2, cx2+ro2+2, cy2+ro2+6), fill=(0, 0, 0, 115))
    sh_ring = sh_ring.filter(ImageFilter.GaussianBlur(3.5))
    hi.alpha_composite(sh_ring)

    # Outer metallic bezel flange
    flange_fill = (42, 50, 62, 255) if gloss else (34, 41, 50, 255)
    flange_out = (105, 122, 145, 255) if gloss else (82, 95, 112, 255)
    dhi.ellipse((cx2-ro2, cy2-ro2, cx2+ro2, cy2+ro2), fill=flange_fill, outline=flange_out, width=2)
    dhi.ellipse((cx2-ro2+3, cy2-ro2+3, cx2+ro2-3, cy2+ro2-3), outline=(56, 66, 80, 255), width=2)

    # 4 Screws at 45, 135, 225, 315 degrees on the bezel ring (scaled 1.3x)
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

    # Recessed inner sub-dial chamber
    dhi.ellipse((cx2-ri2, cy2-ri2, cx2+ri2, cy2+ri2), fill=(*ch_rgb, 255), outline=outline_col, width=2)

    img.alpha_composite(hi.resize((450, 450), Image.Resampling.LANCZOS))

def draw_dial_labels(draw, gloss=False):
    dial_font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 9)
    col = (130, 145, 165, 255) if gloss else (105, 118, 136, 255)
    # START placed on right bezel between quad complications and clock chamber
    draw.text((386, 168), 'START', font=dial_font, fill=col)

# ----------------- SHADOW LAYER (Curved SDF Chambers + 30% Larger Circular Sub-Dial) -----------------
shadow_layer_hi = Image.new('RGBA', (w, h), (0, 0, 0, 0))
dx = -4 * scale
dy = 5 * scale
blur_radius = 5 * scale / 2.0
alpha_val = int(255 * 0.58)

for kind, m_u8, sdf_c in chamber_specs_2x:
    mask = Image.fromarray(m_u8)
    inv_mask = Image.fromarray(255 - m_u8)

    shifted_inv = Image.new('L', (w, h), 255)
    shifted_inv.paste(inv_mask, (dx, dy))
    blurred_inv = shifted_inv.filter(ImageFilter.GaussianBlur(blur_radius))

    arr_mask = m_u8.astype(float) / 255.0
    arr_inv = np.array(blurred_inv).astype(float) / 255.0
    final_alpha = (arr_mask * arr_inv * alpha_val).clip(0, 255).astype(np.uint8)

    box_arr = np.zeros((h, w, 4), dtype=np.uint8)
    box_arr[:, :, 3] = final_alpha
    shadow_layer_hi.alpha_composite(Image.fromarray(box_arr))

# Add Circular Sub-Dial Inner Shadow (cx=352, cy=323, r_inner=39.65)
c_mask = Image.new('L', (w, h), 0)
ImageDraw.Draw(c_mask).ellipse((int(round((scx-r_inner)*scale)), int(round((scy-r_inner)*scale)), int(round((scx+r_inner)*scale)), int(round((scy+r_inner)*scale))), fill=255)
c_inv = Image.new('L', (w, h), 255)
ImageDraw.Draw(c_inv).ellipse((int(round((scx-r_inner)*scale)), int(round((scy-r_inner)*scale)), int(round((scx+r_inner)*scale)), int(round((scy+r_inner)*scale))), fill=0)
c_shift = Image.new('L', (w, h), 255)
c_shift.paste(c_inv, (-3 * scale, 4 * scale))
c_blur = c_shift.filter(ImageFilter.GaussianBlur(4.5 * scale / 2.0))
c_arr_mask = np.array(c_mask).astype(float) / 255.0
c_arr_inv = np.array(c_blur).astype(float) / 255.0
c_final_alpha = (c_arr_mask * c_arr_inv * int(255 * 0.56)).clip(0, 255).astype(np.uint8)
c_box_arr = np.zeros((h, w, 4), dtype=np.uint8)
c_box_arr[:, :, 3] = c_final_alpha
shadow_layer_hi.alpha_composite(Image.fromarray(c_box_arr))

user_shadow = shadow_layer_hi.resize((450, 450), Image.Resampling.LANCZOS)

def save_all_places(img, filename):
    p1 = os.path.join(OUTPUT_DIR, filename)
    p2 = os.path.join(EXPORT_DIR, filename)
    p3 = os.path.join(BRAIN_DIR, filename)
    img.save(p1)
    img.save(p2)
    img.save(p3)
    print(f'Saved: {filename}')

# 1. Classic LCD
img0 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
d0 = ImageDraw.Draw(img0)
draw_bezel_and_track(d0, cx, cy, (18, 22, 28, 255), False)
d0.ellipse((39, 39, 411, 411), fill=(30, 37, 43, 255))
grid0 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
gd0 = ImageDraw.Draw(grid0)
for y in range(40, 410, 3):
    dy_v = abs(y - cy)
    if dy_v < 184:
        hw = math.sqrt(184**2 - dy_v**2)
        gd0.line([(cx - hw + 4, y), (cx + hw - 4, y)], fill=(255, 255, 255, 16), width=1)
img0.alpha_composite(grid0)
draw_chambers_and_subdial(img0, (30, 37, 43), False)
draw_dial_labels(d0, False)
img0.alpha_composite(user_shadow)
save_all_places(img0, 'bg_lcd_real.png')

# 2. Matte Black (Solid #000000 circumference ring in the tick-mark track section)
img1 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
d1 = ImageDraw.Draw(img1)
d1.ellipse((0, 0, 450, 450), fill=(0, 0, 0, 255))
d1.ellipse((26, 26, 424, 424), fill=(10, 11, 13, 255), outline=(26, 32, 40, 255), width=1)
d1.ellipse((38, 38, 412, 412), outline=(36, 44, 54, 255), width=1)
d1.ellipse((39, 39, 411, 411), fill=(14, 16, 19, 255))
grid1 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
gd1 = ImageDraw.Draw(grid1)
for y in range(40, 410, 4):
    dy_v = abs(y - cy)
    if dy_v < 184:
        hw = math.sqrt(184**2 - dy_v**2)
        gd1.line([(cx - hw + 4, y), (cx + hw - 4, y)], fill=(255, 255, 255, 8), width=1)
img1.alpha_composite(grid1)
draw_chambers_and_subdial(img1, (14, 16, 19), False)
draw_dial_labels(d1, False)
img1.alpha_composite(user_shadow)
save_all_places(img1, 'bg_lcd_matte_black.png')

# 3. Woodland Camo
img2 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
d2 = ImageDraw.Draw(img2)
draw_bezel_and_track(d2, cx, cy, (32, 38, 28, 255), False)
d2.ellipse((39, 39, 411, 411), fill=(38, 48, 34, 255))
camo_layer = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
cdraw = ImageDraw.Draw(camo_layer)
random.seed(42)
camo_colors = [
    (24, 30, 20, 180),
    (52, 65, 42, 160),
    (68, 75, 54, 150),
    (44, 54, 46, 140),
]
for _ in range(55):
    bx = random.randint(45, 405)
    by = random.randint(45, 405)
    if (bx - cx)**2 + (by - cy)**2 < 178**2:
        rad_x = random.randint(18, 52)
        rad_y = random.randint(14, 42)
        col = random.choice(camo_colors)
        cdraw.ellipse((bx - rad_x, by - rad_y, bx + rad_x, by + rad_y), fill=col)
img2.alpha_composite(camo_layer)
draw_chambers_and_subdial(img2, (34, 44, 32), False)
draw_dial_labels(d2, False)
img2.alpha_composite(user_shadow)
save_all_places(img2, 'bg_lcd_camo.png')

# 4. Urban Arctic Camo
img_camo_urban = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
du = ImageDraw.Draw(img_camo_urban)
draw_bezel_and_track(du, cx, cy, (20, 23, 28, 255), False)
du.ellipse((39, 39, 411, 411), fill=(24, 27, 32, 255))
camo_urban_layer = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
cdraw_u = ImageDraw.Draw(camo_urban_layer)
random.seed(99)
urban_camo_colors = [
    (15, 18, 22, 170),
    (45, 52, 62, 150),
    (75, 84, 96, 130),
    (110, 120, 135, 110),
]
for _ in range(50):
    bx = random.randint(45, 405)
    by = random.randint(45, 405)
    if (bx - cx)**2 + (by - cy)**2 < 178**2:
        rad_x = random.randint(16, 44)
        rad_y = random.randint(12, 36)
        col = random.choice(urban_camo_colors)
        cdraw_u.ellipse((bx - rad_x, by - rad_y, bx + rad_x, by + rad_y), fill=col)
img_camo_urban.alpha_composite(camo_urban_layer)
draw_chambers_and_subdial(img_camo_urban, (24, 27, 32), False)
draw_dial_labels(du, False)
img_camo_urban.alpha_composite(user_shadow)
save_all_places(img_camo_urban, 'bg_lcd_camo_urban.png')

# 5. Carbon Fiber
img_carbon = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
dc = ImageDraw.Draw(img_carbon)
draw_bezel_and_track(dc, cx, cy, (16, 18, 22, 255), False)
dc.ellipse((39, 39, 411, 411), fill=(18, 20, 24, 255))
carbon_layer = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
cdraw_cf = ImageDraw.Draw(carbon_layer)
bw = 6
for y in range(40, 410, bw):
    for x in range(40, 410, bw):
        if (x + bw//2 - cx)**2 + (y + bw//2 - cy)**2 < 182**2:
            bx = x // bw
            by = y // bw
            twill = (bx + by) % 4
            if twill in (0, 1):
                for sy in range(bw):
                    shade = int(22 + 18 * math.sin((sy / bw) * math.pi))
                    cdraw_cf.line([(x, y + sy), (x + bw - 1, y + sy)], fill=(shade, shade + 2, shade + 4, 180), width=1)
            else:
                for sx in range(bw):
                    shade = int(14 + 14 * math.sin((sx / bw) * math.pi))
                    cdraw_cf.line([(x + sx, y), (x + sx, y + bw - 1)], fill=(shade, shade + 2, shade + 4, 180), width=1)
img_carbon.alpha_composite(carbon_layer)
draw_chambers_and_subdial(img_carbon, (20, 22, 26), False)
draw_dial_labels(dc, False)
img_carbon.alpha_composite(user_shadow)
save_all_places(img_carbon, 'bg_lcd_carbon_fiber.png')

# 6. Gloss Black
img3 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
d3 = ImageDraw.Draw(img3)
draw_bezel_and_track(d3, cx, cy, (6, 8, 10, 255), True)
d3.ellipse((39, 39, 411, 411), fill=(10, 12, 15, 255))
gloss_img = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
gldraw = ImageDraw.Draw(gloss_img)
for r in range(45, 405, 2):
    dy_v = abs(r - cy)
    if dy_v < 184:
        hw = math.sqrt(184**2 - dy_v**2)
        if r < 200:
            gldraw.line([(cx - hw + 10, r), (cx, r)], fill=(255, 255, 255, int(18 * (1 - r/200))), width=1)
img3.alpha_composite(gloss_img)
draw_chambers_and_subdial(img3, (12, 14, 18), True)
draw_dial_labels(d3, True)
img3.alpha_composite(user_shadow)
save_all_places(img3, 'bg_lcd_gloss_black.png')

# 7. Grid
img4 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
d4 = ImageDraw.Draw(img4)
draw_bezel_and_track(d4, cx, cy, (20, 24, 30, 255), False)
d4.ellipse((39, 39, 411, 411), fill=(33, 41, 47, 255))
grid4 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
gd4 = ImageDraw.Draw(grid4)
for y in range(39, 411, 6):
    dy_v = abs(y - cy)
    if dy_v < 184:
        hw = math.sqrt(184**2 - dy_v**2)
        gd4.line([(cx - hw + 4, y), (cx + hw - 4, y)], fill=(255, 255, 255, 28), width=1)
for x in range(39, 411, 6):
    dx_v = abs(x - cx)
    if dx_v < 184:
        hh = math.sqrt(184**2 - dx_v**2)
        gd4.line([(x, cy - hh + 4), (x, cy + hh - 4)], fill=(255, 255, 255, 28), width=1)
img4.alpha_composite(grid4)
draw_chambers_and_subdial(img4, (26, 33, 38), False)
draw_dial_labels(d4, False)
img4.alpha_composite(user_shadow)
save_all_places(img4, 'bg_lcd_grid.png')

# 8. Tactical Raised Mesh (Mock A: Photo-Realistic 3D Normal-Mapped Molded Micro-Waffle)
img_mesh = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
dm = ImageDraw.Draw(img_mesh)
draw_bezel_and_track(dm, cx, cy, (18, 22, 27, 255), False)

H_m, W_m = 900, 900
yy_m, xx_m = np.mgrid[0:H_m, 0:W_m].astype(float)
pitch_a = 9.0  # 4.5px pitch at 450x450
u_a = ((xx_m % pitch_a) / pitch_a) * 2.0 - 1.0
v_a = ((yy_m % pitch_a) / pitch_a) * 2.0 - 1.0
dist_cheb = np.maximum(np.abs(u_a), np.abs(v_a))
Z_a = 0.5 * (1.0 - np.tanh(6.5 * (dist_cheb - 0.74)))
dist_eucl = np.sqrt(u_a**2 + v_a**2)
Z_a *= np.clip(1.0 - 0.15 * np.maximum(0.0, dist_eucl - 0.85), 0.0, 1.0)
AO_a = 0.42 + 0.58 * (Z_a ** 0.7)

rng_m = np.random.default_rng(42)
Z_rough = Z_a + rng_m.normal(0.0, 0.025, (H_m, W_m))
dZdy, dZdx = np.gradient(Z_rough)
slope_scale = 2.6
nx_m = -slope_scale * dZdx
ny_m = -slope_scale * dZdy
nz_m = np.ones_like(Z_rough)
norm_m = np.sqrt(nx_m*nx_m + ny_m*ny_m + nz_m*nz_m)
nx_m /= norm_m
ny_m /= norm_m
nz_m /= norm_m

lx_m, ly_m, lz_m = -0.48, -0.62, 0.62
l_len_m = math.sqrt(lx_m*lx_m + ly_m*ly_m + lz_m*lz_m)
lx_m, ly_m, lz_m = lx_m/l_len_m, ly_m/l_len_m, lz_m/l_len_m
ndotl_m = np.clip(nx_m*lx_m + ny_m*ly_m + nz_m*lz_m, 0.0, 1.0)

hx_m, hy_m, hz_m = lx_m, ly_m, lz_m + 1.0
h_len_m = math.sqrt(hx_m*hx_m + hy_m*hy_m + hz_m*hz_m)
hx_m, hy_m, hz_m = hx_m/h_len_m, hy_m/h_len_m, hz_m/h_len_m
spec_m = np.power(np.clip(nx_m*hx_m + ny_m*hy_m + nz_m*hz_m, 0.0, 1.0), 18.0)

macro_light = np.clip(1.0 - 0.18 * ((xx_m - W_m*0.35)/(W_m*0.7))**2 - 0.18 * ((yy_m - H_m*0.32)/(H_m*0.7))**2, 0.72, 1.05)
fine_noise = rng_m.normal(0.0, 1.0, (H_m, W_m))
out_m = np.zeros((H_m, W_m, 4), dtype=np.uint8)
for c_idx, base_c in enumerate((26, 31, 37)):
    ch_val = (base_c * (0.55 + 0.65 * ndotl_m) + 15.0 * (ndotl_m - 0.5)) * AO_a * macro_light + 20.0 * spec_m * AO_a + fine_noise
    out_m[:, :, c_idx] = np.clip(ch_val, 0, 255).astype(np.uint8)
out_m[:, :, 3] = 255
surf_a = Image.fromarray(out_m).resize((450, 450), Image.Resampling.LANCZOS)

dial_mask = Image.new('L', (450, 450), 0)
ImageDraw.Draw(dial_mask).ellipse((39, 39, 411, 411), fill=255)
mesh_clipped = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
mesh_clipped.paste(surf_a, (0, 0), dial_mask)

# Subtle radial inner bezel recess shadow around r=186 (39..411)
bezel_sh = Image.new('L', (450, 450), 255)
ImageDraw.Draw(bezel_sh).ellipse((42, 42, 408, 408), fill=0)
bezel_sh = bezel_sh.filter(ImageFilter.GaussianBlur(4.0))
b_arr = np.array(bezel_sh).astype(float) / 255.0
m_arr = np.array(dial_mask).astype(float) / 255.0
edge_sh = np.zeros((450, 450, 4), dtype=np.uint8)
edge_sh[:, :, 3] = (b_arr * m_arr * 150).clip(0, 255).astype(np.uint8)
mesh_clipped.alpha_composite(Image.fromarray(edge_sh))

img_mesh.alpha_composite(mesh_clipped)
draw_chambers_and_subdial(img_mesh, (22, 26, 32), False)
draw_dial_labels(dm, False)
img_mesh.alpha_composite(user_shadow)
save_all_places(img_mesh, 'bg_lcd_tactical_mesh.png')

print('All 8 background images generated with shortened Slot 5 and GA-100 Sub-Dial!')

# ----------------- GENERATE 30% LARGER SUB-DIAL ASSETS (100x100 at 2x = 200x200) -----------------
S = 100
S2 = S * 2
cx_s, cy_s = S, S
r_pie = int(round(27.5 * 1.3 * 2))
r_cut_hub = int(round(13.5 * 1.3 * 2))

# 1. Individual 8 Pie Wedge PNGs (White #FFFFFF so tintColor=[CONFIGURATION.themeColor.0] works!)
wedges_all = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
d_all = ImageDraw.Draw(wedges_all)

for i in range(8):
    w_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
    dw = ImageDraw.Draw(w_img)
    a_start = -90 + i * 45 + 3.5
    a_end = -90 + (i + 1) * 45 - 3.5
    dw.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=(255, 255, 255, 255))
    # Cut out center hub
    dw.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=(0, 0, 0, 0))
    
    d_all.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=(255, 255, 255, 255))
    
    w_small = w_img.resize((S, S), Image.Resampling.LANCZOS)
    w_small.save(os.path.join(OUTPUT_DIR, f'subdial_seg_{i+1}.png'))

d_all.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=(0, 0, 0, 0))
wedges_all.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_seg_ghost.png'))

# 2. Center Hub Cap + Crisp Larger Battery Icon (subdial_batt_hub.png)
hub_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dh = ImageDraw.Draw(hub_img)
r_hub = int(round(12.2 * 1.3 * 2))
dh.ellipse((cx_s - r_hub, cy_s - r_hub, cx_s + r_hub, cy_s + r_hub), fill=(30, 36, 44, 255), outline=(105, 120, 140, 255), width=2)
bx1, by1 = cx_s - int(round(15 * 1.3)), cy_s - int(round(9 * 1.3))
bx2, by2 = cx_s + int(round(11 * 1.3)), cy_s + int(round(9 * 1.3))
dh.rounded_rectangle((bx1, by1, bx2, by2), radius=5, fill=(255, 255, 255, 255))
dh.rounded_rectangle((bx2 + 3, cy_s - int(round(5 * 1.3)), bx2 + 8, cy_s + int(round(5 * 1.3))), radius=2, fill=(255, 255, 255, 255))
hub_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_batt_hub.png'))

# 3. Analog Dual-Time Ticks (subdial_analog_ticks.png for dark bg, subdial_analog_ticks_black.png for positive LCD bg)
ticks_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dt = ImageDraw.Draw(ticks_img)
ticks_blk_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dt_blk = ImageDraw.Draw(ticks_blk_img)
for i in range(12):
    ang = i * (2 * math.pi / 12) - math.pi/2
    is_maj = (i % 3 == 0)
    r1 = (r_inner - 1.5 * 1.3) * 2
    tick_len = (5.0 if i == 6 else (7.5 if is_maj else 4.5)) * 1.3
    r2 = (r_inner - tick_len) * 2
    x1, y1 = cx_s + r1 * math.cos(ang), cy_s + r1 * math.sin(ang)
    x2, y2 = cx_s + r2 * math.cos(ang), cy_s + r2 * math.sin(ang)
    col = (220, 230, 242, 255) if is_maj else (110, 125, 145, 255)
    col_blk = (10, 13, 16, 255) if is_maj else (65, 75, 90, 235)
    dt.line([(x1, y1), (x2, y2)], fill=col, width=4 if is_maj else 2)
    dt_blk.line([(x1, y1), (x2, y2)], fill=col_blk, width=4 if is_maj else 2)

ticks_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_analog_ticks.png'))
ticks_blk_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_analog_ticks_black.png'))

# 4. Analog Hour Hand (Pointing UP to 12 o'clock at angle=0, pure white #FFFFFF so tintColor works!)
hr_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dhr = ImageDraw.Draw(hr_img)
dhr.rounded_rectangle((cx_s - 5, cy_s - 40, cx_s + 5, cy_s + 10), radius=4, fill=(255, 255, 255, 255))
hr_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_hand_hour.png'))

# 5. Analog Minute Hand (Pointing UP to 12 o'clock at angle=0, pure white #FFFFFF)
mn_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dmn = ImageDraw.Draw(mn_img)
dmn.rounded_rectangle((cx_s - 4, cy_s - 60, cx_s + 4, cy_s + 12), radius=3, fill=(255, 255, 255, 255))
mn_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_hand_min.png'))

# 6. Analog Center Pivot Cap (subdial_analog_cap.png)
cap_img = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
dcap = ImageDraw.Draw(cap_img)
dcap.ellipse((cx_s - 12, cy_s - 12, cx_s + 12, cy_s + 12), fill=(45, 54, 66, 255), outline=(190, 205, 225, 255), width=2)
dcap.ellipse((cx_s - 4, cy_s - 4, cx_s + 4, cy_s + 4), fill=(255, 255, 255, 255))
cap_img.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'subdial_analog_cap.png'))

# 7. Apply Consistent Inner Shadow & 1px Border Mask to All 6 LCD Chambers + Circular Sub-Dial
# Unified bounding box: x=70..380 (w=310), y=90..358 (h=268)
BETA_DRAWABLE_DIR = r'C:\Users\bonst\.gemini\antigravity\scratch\gshark-watchface-checkpoint-BETA\app\src\main\res\drawable'
lcd_shadow_all = user_shadow.crop((70, 90, 380, 358))  # 310x268

# Build exact 1px-inset interior mask from 2x SDFs so curved corners match 100%
inner_hi_arr = np.zeros((h, w), dtype=float)
for kind, m_u8, sdf_c in chamber_specs_2x:
    in_a = np.clip(0.5 - (sdf_c + 2.0) / 1.2, 0.0, 1.0)
    inner_hi_arr = np.maximum(inner_hi_arr, in_a)

inner_450 = Image.fromarray((inner_hi_arr * 255.0).clip(0, 255).astype(np.uint8)).resize((450, 450), Image.Resampling.LANCZOS)
inner_mask = inner_450.crop((70, 90, 380, 358))  # 310x268

inner_mask_arr = np.array(inner_mask).astype(float) / 255.0
sh_arr = np.array(lcd_shadow_all)
sh_alpha = (sh_arr[:, :, 3].astype(float) / 255.0) * inner_mask_arr

sh_overlay = np.zeros((268, 310, 4), dtype=np.uint8)
sh_overlay[:, :, 3] = (sh_alpha * 255.0).clip(0, 255).astype(np.uint8)
sh_overlay_img = Image.fromarray(sh_overlay)

# Sub-Dial circular 1px-inset interior mask & shadow (100x100 at x=302, y=273)
yy_s2, xx_s2 = np.mgrid[0:S2, 0:S2].astype(float)
dist_s2 = np.sqrt((xx_s2 - cx_s)**2 + (yy_s2 - cy_s)**2)
sdf_sub_in = dist_s2 - (r_inner - 1.0) * 2.0
sub_in_hi = (np.clip(0.5 - sdf_sub_in / 1.2, 0.0, 1.0) * 255.0).astype(np.uint8)
sub_inner_mask = Image.fromarray(sub_in_hi).resize((S, S), Image.Resampling.LANCZOS)
sub_inner_mask_arr = np.array(sub_inner_mask).astype(float) / 255.0

sub_shadow_crop = user_shadow.crop((302, 273, 402, 373))  # 100x100
sub_sh_alpha = (np.array(sub_shadow_crop)[:, :, 3].astype(float) / 255.0) * sub_inner_mask_arr
sub_sh_overlay = np.zeros((S, S, 4), dtype=np.uint8)
sub_sh_overlay[:, :, 3] = (sub_sh_alpha * 255.0).clip(0, 255).astype(np.uint8)
sub_sh_overlay_img = Image.fromarray(sub_sh_overlay)

def build_full_268_tex_array(raw_106_arr):
    """Maps a 106x310 raw texture array across all 3 chamber rows (268x310)."""
    full_arr = np.zeros((268, 310, 4), dtype=float)
    # Row 1: Quad pods (y=0..78, 78px tall) sampled from unclipped interior rows 14..92
    full_arr[0:78, :, :] = raw_106_arr[14:92, :, :]
    # Row 2: Main clock (y=88..194, 106px tall) uses full 0..106
    full_arr[88:194, :, :] = raw_106_arr[0:106, :, :]
    # Row 3: Slot 5 (y=212..268, 56px tall) sampled from unclipped interior rows 25..81
    full_arr[212:268, :, :] = raw_106_arr[25:81, :, :]
    return full_arr

def save_split_main_and_comp_textures(full_268_img, main_filename, comp_filename):
    """
    Saves:
      1) main_filename (310x106 at x=70, y=178): ONLY the Main Clock chamber (rows 88..194)
      2) comp_filename (310x78 at x=70, y=90): ONLY the Upper 4 Quad Pods (rows 0..78)
      3) bottom_filename (310x56 at x=70, y=302): ONLY the Lower Slot 5 chamber (rows 212..268)
    """
    main_crop = full_268_img.crop((0, 88, 310, 194))  # 310x106
    main_crop.save(os.path.join(OUTPUT_DIR, main_filename))

    top_crop = full_268_img.crop((0, 0, 310, 78))  # 310x78
    top_crop.save(os.path.join(OUTPUT_DIR, comp_filename))

    bot_filename = comp_filename.replace('tex_quad_', 'tex_bottom_')
    bot_crop = full_268_img.crop((0, 212, 310, 268))  # 310x56
    bot_crop.save(os.path.join(OUTPUT_DIR, bot_filename))
    full_268_img.save(os.path.join(BRAIN_DIR, main_filename))

for tex_name in ['tex_screen_hex_light.png', 'tex_screen_hex_dark.png', 'tex_screen_moire_light.png', 'tex_screen_moire_dark.png']:
    src_path = os.path.join(BETA_DRAWABLE_DIR, tex_name)
    if os.path.exists(src_path):
        raw_tex = Image.open(src_path).convert('RGBA')
        t_arr_106 = np.array(raw_tex).astype(float)
        t_arr = build_full_268_tex_array(t_arr_106)
        v_norm = t_arr[:, :, 0] / 255.0
        a_norm = t_arr[:, :, 3] / 255.0
        # Subdue Honeycomb Dark slightly when text is white (0.78), and Solar Moire Dark (0.65)
        if tex_name == 'tex_screen_moire_dark.png':
            scale_factor = 0.65
        elif tex_name == 'tex_screen_hex_dark.png':
            scale_factor = 0.78
        else:
            scale_factor = 1.0
        pure_opacity = a_norm * v_norm * scale_factor * inner_mask_arr * (1.0 - sh_alpha * 0.85)

        out_arr = np.zeros((268, 310, 4), dtype=np.uint8)
        out_arr[:, :, 0] = 255
        out_arr[:, :, 1] = 255
        out_arr[:, :, 2] = 255
        out_arr[:, :, 3] = (pure_opacity * 255.0).clip(0, 255).astype(np.uint8)
        masked_tex = Image.fromarray(out_arr)

        final_tex = Image.alpha_composite(masked_tex, sh_overlay_img)
        quad_name = tex_name.replace('tex_screen_', 'tex_quad_')
        save_split_main_and_comp_textures(final_tex, tex_name, quad_name)

        # Also generate 100x100 circular Sub-Dial texture (sampled from clean interior 3:103, 105:205)
        sub_t_arr = t_arr_106[3:103, 105:205, :]
        sub_v_norm = sub_t_arr[:, :, 0] / 255.0
        sub_a_norm = sub_t_arr[:, :, 3] / 255.0
        sub_pure_op = sub_a_norm * sub_v_norm * scale_factor * sub_inner_mask_arr * (1.0 - sub_sh_alpha * 0.85)
        sub_out = np.zeros((S, S, 4), dtype=np.uint8)
        sub_out[:, :, 0] = 255
        sub_out[:, :, 1] = 255
        sub_out[:, :, 2] = 255
        sub_out[:, :, 3] = (sub_pure_op * 255.0).clip(0, 255).astype(np.uint8)
        sub_final = Image.alpha_composite(Image.fromarray(sub_out), sub_sh_overlay_img)
        sub_name = tex_name.replace('tex_screen_', 'tex_subdial_')
        sub_final.save(os.path.join(OUTPUT_DIR, sub_name))
        print(f'Saved main (310x106), comp (310x268), & subdial (100x100) textures: {tex_name}, {quad_name}, {sub_name}')

# 7B. Generate Inverted (Positive LCD: 82% White Overlay + Inner Shadow + Distinct Texture Matrix) Overlays
inv_base_arr = np.zeros((268, 310, 4), dtype=np.uint8)
inv_base_arr[:, :, 0] = 242
inv_base_arr[:, :, 1] = 246
inv_base_arr[:, :, 2] = 250
inv_base_arr[:, :, 3] = (inner_mask_arr * 210.0).clip(0, 255).astype(np.uint8)
invert_base = Image.fromarray(inv_base_arr)

sub_inv_base_arr = np.zeros((S, S, 4), dtype=np.uint8)
sub_inv_base_arr[:, :, 0] = 242
sub_inv_base_arr[:, :, 1] = 246
sub_inv_base_arr[:, :, 2] = 250
sub_inv_base_arr[:, :, 3] = (sub_inner_mask_arr * 210.0).clip(0, 255).astype(np.uint8)
sub_invert_base = Image.fromarray(sub_inv_base_arr)

# Default inverted overlay (82% white + subtle horizontal positive-LCD scanlines + directional inner shadow)
scan_arr = np.zeros((268, 310), dtype=float)
scan_arr[1::3, :] = 0.08
pat_def_alpha = scan_arr * inner_mask_arr
sh_def_alpha = sh_alpha * 0.88
comb_def_alpha = np.clip(1.0 - (1.0 - pat_def_alpha) * (1.0 - sh_def_alpha), 0.0, 1.0)

sh_inv_arr = np.zeros((268, 310, 4), dtype=np.uint8)
sh_inv_arr[:, :, 0] = 14
sh_inv_arr[:, :, 1] = 18
sh_inv_arr[:, :, 2] = 24
sh_inv_arr[:, :, 3] = (comb_def_alpha * 255.0).clip(0, 255).astype(np.uint8)
inv_default = Image.alpha_composite(invert_base, Image.fromarray(sh_inv_arr))
save_split_main_and_comp_textures(inv_default, 'tex_invert_default.png', 'tex_quad_invert_default.png')

# Subdial default inverted overlay
sub_scan_arr = np.zeros((S, S), dtype=float)
sub_scan_arr[1::3, :] = 0.08
sub_pat_def = sub_scan_arr * sub_inner_mask_arr
sub_sh_def = sub_sh_alpha * 0.88
sub_comb_def = np.clip(1.0 - (1.0 - sub_pat_def) * (1.0 - sub_sh_def), 0.0, 1.0)
sub_def_arr = np.zeros((S, S, 4), dtype=np.uint8)
sub_def_arr[:, :, 0] = 14
sub_def_arr[:, :, 1] = 18
sub_def_arr[:, :, 2] = 24
sub_def_arr[:, :, 3] = (sub_comb_def * 255.0).clip(0, 255).astype(np.uint8)
sub_inv_def = Image.alpha_composite(sub_invert_base, Image.fromarray(sub_def_arr))
sub_inv_def.save(os.path.join(OUTPUT_DIR, 'tex_subdial_invert_default.png'))
print('Saved split inverted default overlays (main, comp, subdial)')

for tex_name, inv_name, invert_polarity, contrast_strength, base_dark in [
    # Exaggerate light vs dark differences in Black LCD mode while subduing Honeycomb slightly:
    ('tex_screen_hex_light.png',   'tex_invert_hex_light.png',   True,  0.14, 0.00),
    ('tex_screen_hex_dark.png',    'tex_invert_hex_dark.png',    False, 0.22, 0.07),
    ('tex_screen_moire_light.png', 'tex_invert_moire_light.png', True,  0.15, 0.00),
    ('tex_screen_moire_dark.png',  'tex_invert_moire_dark.png',  True,  0.30, 0.08),
]:
    src_path = os.path.join(BETA_DRAWABLE_DIR, tex_name)
    raw_tex = Image.open(src_path).convert('RGBA')
    t_arr_106 = np.array(raw_tex).astype(float)
    v_vals_106 = t_arr_106[:, :, 0]
    valid_v = v_vals_106[20:86, 10:300]
    v_min, v_max = np.percentile(valid_v, 2), np.percentile(valid_v, 98)

    t_arr = build_full_268_tex_array(t_arr_106)
    v_vals = t_arr[:, :, 0]
    pat_norm = np.clip((v_vals - v_min) / max(1.0, (v_max - v_min)), 0.0, 1.0)

    pattern_darkness = (1.0 - pat_norm) if invert_polarity else pat_norm
    pat_dark_alpha = (base_dark + pattern_darkness * contrast_strength) * inner_mask_arr
    sh_dark_alpha = sh_alpha * 0.88
    comb_alpha = np.clip(1.0 - (1.0 - pat_dark_alpha) * (1.0 - sh_dark_alpha), 0.0, 1.0)

    tex_dark = np.zeros((268, 310, 4), dtype=np.uint8)
    tex_dark[:, :, 0] = 14
    tex_dark[:, :, 1] = 18
    tex_dark[:, :, 2] = 24
    tex_dark[:, :, 3] = (comb_alpha * 255.0).clip(0, 255).astype(np.uint8)
    inv_comp = Image.alpha_composite(invert_base, Image.fromarray(tex_dark))
    quad_inv_name = inv_name.replace('tex_invert_', 'tex_quad_invert_')
    save_split_main_and_comp_textures(inv_comp, inv_name, quad_inv_name)

    # Also generate 100x100 circular Sub-Dial inverted texture
    sub_v_vals = t_arr_106[3:103, 105:205, 0]
    sub_pat_norm = np.clip((sub_v_vals - v_min) / max(1.0, (v_max - v_min)), 0.0, 1.0)
    sub_pat_dark = (1.0 - sub_pat_norm) if invert_polarity else sub_pat_norm
    sub_pat_alpha = (base_dark + sub_pat_dark * contrast_strength) * sub_inner_mask_arr
    sub_sh_d_alpha = sub_sh_alpha * 0.88
    sub_comb_a = np.clip(1.0 - (1.0 - sub_pat_alpha) * (1.0 - sub_sh_d_alpha), 0.0, 1.0)
    sub_tex_d = np.zeros((S, S, 4), dtype=np.uint8)
    sub_tex_d[:, :, 0] = 14
    sub_tex_d[:, :, 1] = 18
    sub_tex_d[:, :, 2] = 24
    sub_tex_d[:, :, 3] = (sub_comb_a * 255.0).clip(0, 255).astype(np.uint8)
    sub_inv_comp = Image.alpha_composite(sub_invert_base, Image.fromarray(sub_tex_d))
    sub_inv_name = inv_name.replace('tex_invert_', 'tex_subdial_invert_')
    sub_inv_comp.save(os.path.join(OUTPUT_DIR, sub_inv_name))
    print(f'Saved split inverted overlays: {inv_name}, {quad_inv_name}, {sub_inv_name}')

# 8. Generate Outer Bezel Checkmark / Tick-Mark Overlays (Options 0..5, plus Option 6 = None)
# Option 0: Classic Minute Track (Default — 100% identical to original baked-in ticks)
t0 = Image.new('RGBA', (450, 450), (0, 0, 0, 0))
dt0 = ImageDraw.Draw(t0)
for i in range(60):
    angle = i * (2 * math.pi / 60)
    is_major = (i % 5 == 0)
    r_out = 220
    r_in = 210 if is_major else 214
    x1 = cx + r_out * math.cos(angle)
    y1 = cy + r_out * math.sin(angle)
    x2 = cx + r_in * math.cos(angle)
    y2 = cy + r_in * math.sin(angle)
    color = (175, 185, 200, 255) if is_major else (70, 80, 95, 200)
    width = 2 if is_major else 1
    dt0.line([(x1, y1), (x2, y2)], fill=color, width=width)
t0.save(os.path.join(OUTPUT_DIR, 'ticks_0_classic.png'))

# Option 1: 12-Hour Indices Only (Minimalist 12 major markers, no minor minute ticks)
t1 = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt1 = ImageDraw.Draw(t1)
for i in range(0, 60, 5):
    angle = i * (2 * math.pi / 60)
    r_out, r_in = 220 * 2, 209 * 2
    x1, y1 = 450 + r_out * math.cos(angle), 450 + r_out * math.sin(angle)
    x2, y2 = 450 + r_in * math.cos(angle), 450 + r_in * math.sin(angle)
    dt1.line([(x1, y1), (x2, y2)], fill=(200, 212, 230, 255), width=4)
t1.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_1_hours.png'))

# Option 2: Bold Tactical Batons (Heavy G-Shock lume batons + double 12-o'clock marker + minute dots)
t2 = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt2 = ImageDraw.Draw(t2)
for i in range(60):
    angle = i * (2 * math.pi / 60) - math.pi / 2
    if i == 0:
        # Double 12 o'clock tactical baton
        for da in (-0.016, 0.016):
            a = angle + da
            x1, y1 = 450 + 440 * math.cos(a), 450 + 440 * math.sin(a)
            x2, y2 = 450 + 416 * math.cos(a), 450 + 416 * math.sin(a)
            dt2.line([(x1, y1), (x2, y2)], fill=(230, 240, 252, 255), width=6)
    elif i % 5 == 0:
        x1, y1 = 450 + 440 * math.cos(angle), 450 + 440 * math.sin(angle)
        x2, y2 = 450 + 417 * math.cos(angle), 450 + 417 * math.sin(angle)
        dt2.line([(x1, y1), (x2, y2)], fill=(215, 226, 242, 255), width=8)
    else:
        px, py = 450 + 431 * math.cos(angle), 450 + 431 * math.sin(angle)
        dt2.ellipse((px - 2.5, py - 2.5, px + 2.5, py + 2.5), fill=(85, 98, 115, 220))
t2.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_2_batons.png'))

# Option 3: Chronograph Fine Scale (180-tick 1/3-second telemetry track)
t3 = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt3 = ImageDraw.Draw(t3)
for i in range(180):
    angle = i * (2 * math.pi / 180)
    r_out = 442
    if i % 15 == 0:
        r_in, col, w_line = 418, (215, 226, 242, 255), 4
    elif i % 3 == 0:
        r_in, col, w_line = 425, (120, 135, 155, 230), 3
    else:
        r_in, col, w_line = 432, (68, 78, 94, 190), 2
    x1, y1 = 450 + r_out * math.cos(angle), 450 + r_out * math.sin(angle)
    x2, y2 = 450 + r_in * math.cos(angle), 450 + r_in * math.sin(angle)
    dt3.line([(x1, y1), (x2, y2)], fill=col, width=w_line)
t3.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_3_chrono.png'))

# Option 4: Numeric 05-60 Track (05..60 numerals at 5-minute intervals + intermediate ticks)
t4 = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt4 = ImageDraw.Draw(t4)
f_num = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 18)
for i in range(60):
    angle = i * (2 * math.pi / 60) - math.pi / 2
    if i % 5 == 0:
        num_str = '60' if i == 0 else f'{i:02d}'
        tx = 450 + 429 * math.cos(angle)
        ty = 450 + 429 * math.sin(angle)
        bbox = dt4.textbbox((0, 0), num_str, font=f_num)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        dt4.text((tx - tw / 2 - bbox[0], ty - th / 2 - bbox[1]), num_str, font=f_num, fill=(195, 208, 226, 255))
    else:
        x1, y1 = 450 + 440 * math.cos(angle), 450 + 440 * math.sin(angle)
        x2, y2 = 450 + 428 * math.cos(angle), 450 + 428 * math.sin(angle)
        dt4.line([(x1, y1), (x2, y2)], fill=(75, 86, 102, 210), width=2)
t4.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_4_numeric.png'))

# Option 5: Theme Accent Ticks (Minor ticks in grey + Major 5-minute ticks in #FFFFFF for dynamic themeColor tinting)
t5_min = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt5_min = ImageDraw.Draw(t5_min)
t5_maj = Image.new('RGBA', (900, 900), (0, 0, 0, 0))
dt5_maj = ImageDraw.Draw(t5_maj)
for i in range(60):
    angle = i * (2 * math.pi / 60)
    if i % 5 == 0:
        x1, y1 = 450 + 440 * math.cos(angle), 450 + 440 * math.sin(angle)
        x2, y2 = 450 + 418 * math.cos(angle), 450 + 418 * math.sin(angle)
        dt5_maj.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 255), width=5)
    else:
        x1, y1 = 450 + 440 * math.cos(angle), 450 + 440 * math.sin(angle)
        x2, y2 = 450 + 428 * math.cos(angle), 450 + 428 * math.sin(angle)
        dt5_min.line([(x1, y1), (x2, y2)], fill=(75, 86, 102, 210), width=2)
t5_min.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_5_theme_minor.png'))
t5_maj.resize((450, 450), Image.Resampling.LANCZOS).save(os.path.join(OUTPUT_DIR, 'ticks_5_theme_major.png'))

print('All sub-dial, screen texture, and 6 checkmark style assets generated successfully!')
