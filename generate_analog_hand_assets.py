import os, math
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")

# Hand canvas: 60x450 in 450x450 watchface space (placed at x=195, y=0, pivotX=0.5, pivotY=0.5 -> pivot at 225, 225)
W, H = 60, 450
S = 4  # 4x supersampling (240x1800)
W2, H2 = W * S, H * S
cx, cy = W2 // 2, H2 // 2  # (120, 900)

def pt(x, y):
    return (cx + x * S, cy + y * S)

def poly(pts):
    return [pt(x, y) for (x, y) in pts]

def add_drop_shadow(frame_img, lume_img=None, dx=2.5, dy=3.5, blur=2.8, opacity=0.65):
    # Combine alpha of frame + lume to cast a unified drop shadow behind the hand
    comb = frame_img.copy()
    if lume_img is not None:
        comb.alpha_composite(lume_img)
    alpha = comb.split()[3]
    sh = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    sh_a = alpha.point(lambda p: int(p * opacity))
    sh_shifted = Image.new("L", (W2, H2), 0)
    sh_shifted.paste(sh_a, (int(dx * S), int(dy * S)))
    sh_shifted = sh_shifted.filter(ImageFilter.GaussianBlur(blur * S))
    sh.putalpha(sh_shifted)
    sh.alpha_composite(frame_img)
    return sh

def save_drawable(img_hi, w_out, h_out, name):
    out = img_hi.resize((w_out, h_out), Image.Resampling.LANCZOS)
    out.save(os.path.join(OUTPUT_DIR, name))
    print(f"Saved {name} ({w_out}x{h_out})")

# ==============================================================================
# 1. SKELETON SWORD HANDS (Matches mock_analog_cyberlime & mock_analog_skeleton_spread)
# ==============================================================================
left_facet = (205, 216, 230, 255)
right_facet = (125, 138, 156, 255)

# --- Sword Hour Hand ---
sword_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dh = ImageDraw.Draw(sword_hr_frame)
hr_left = [(0, 22), (-6.5, 22), (-9.0, -14), (-9.0, -80), (0, -112)]
hr_right = [(0, 22), (6.5, 22), (9.0, -14), (9.0, -80), (0, -112)]
dh.polygon(poly(hr_left), fill=left_facet)
dh.polygon(poly(hr_right), fill=right_facet)

hr_base_l = [(0, 22), (-6.5, 22), (-7.8, -14), (0, -14)]
hr_base_r = [(0, 22), (6.5, 22), (7.8, -14), (0, -14)]
dh.polygon(poly(hr_base_l), fill=(58, 66, 78, 255))
dh.polygon(poly(hr_base_r), fill=(36, 42, 52, 255))

# Cutout skeleton window (-18 to -66)
hr_cut = [(-4.4, -18), (4.4, -18), (4.4, -66), (-4.4, -66)]
dh.polygon(poly(hr_cut), fill=(0, 0, 0, 0))

# Cut out lume tip area (-70 to -105) from frame so frame + lume don't double-composite
hr_lume_pts = [(-5.4, -70), (5.4, -70), (5.4, -80), (0, -105), (-5.4, -80)]
dh.polygon(poly(hr_lume_pts), fill=(0, 0, 0, 0))

hr_outline = [(-6.5, 22), (6.5, 22), (9.0, -14), (9.0, -80), (0, -112), (-9.0, -80), (-9.0, -14)]
dh.line(poly(hr_outline + [hr_outline[0]]), fill=(22, 26, 32, 255), width=int(1.2 * S))
dh.line(poly(hr_cut + [hr_cut[0]]), fill=(28, 34, 42, 255), width=int(1.1 * S))

sword_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(sword_hr_lume).polygon(poly(hr_lume_pts), fill=(255, 255, 255, 255))

sword_hr_frame_sh = add_drop_shadow(sword_hr_frame, sword_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(sword_hr_frame_sh, W, H, "hand_sword_hr_frame.png")
save_drawable(sword_hr_lume, W, H, "hand_sword_hr_lume.png")

# --- Sword Minute Hand ---
sword_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dm = ImageDraw.Draw(sword_mn_frame)
mn_left = [(0, 28), (-5.2, 28), (-7.2, -16), (-6.6, -130), (0, -168)]
mn_right = [(0, 28), (5.2, 28), (7.2, -16), (6.6, -130), (0, -168)]
dm.polygon(poly(mn_left), fill=left_facet)
dm.polygon(poly(mn_right), fill=right_facet)

mn_base_l = [(0, 28), (-5.2, 28), (-6.2, -16), (0, -16)]
mn_base_r = [(0, 28), (5.2, 28), (6.2, -16), (0, -16)]
dm.polygon(poly(mn_base_l), fill=(58, 66, 78, 255))
dm.polygon(poly(mn_base_r), fill=(36, 42, 52, 255))

mn_cut = [(-3.3, -20), (3.3, -20), (3.0, -100), (-3.0, -100)]
dm.polygon(poly(mn_cut), fill=(0, 0, 0, 0))

mn_lume_pts = [(-4.0, -104), (4.0, -104), (3.8, -130), (0, -161), (-3.8, -130)]
dm.polygon(poly(mn_lume_pts), fill=(0, 0, 0, 0))

mn_outline = [(-5.2, 28), (5.2, 28), (7.2, -16), (6.6, -130), (0, -168), (-6.6, -130), (-7.2, -16)]
dm.line(poly(mn_outline + [mn_outline[0]]), fill=(22, 26, 32, 255), width=int(1.2 * S))
dm.line(poly(mn_cut + [mn_cut[0]]), fill=(28, 34, 42, 255), width=int(1.1 * S))

sword_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(sword_mn_lume).polygon(poly(mn_lume_pts), fill=(255, 255, 255, 255))

sword_mn_frame_sh = add_drop_shadow(sword_mn_frame, sword_mn_lume, dx=3.0, dy=4.2, blur=3.2, opacity=0.68)
save_drawable(sword_mn_frame_sh, W, H, "hand_sword_mn_frame.png")
save_drawable(sword_mn_lume, W, H, "hand_sword_mn_lume.png")

# ==============================================================================
# 2. TACTICAL BATON HANDS (GA-2100 "CasiOak" Style)
# ==============================================================================
# --- Baton Hour Hand ---
baton_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dbh = ImageDraw.Draw(baton_hr_frame)
b_hr_l = [(0, 20), (-5.5, 20), (-6.8, -16), (-5.8, -94), (0, -108)]
b_hr_r = [(0, 20), (5.5, 20), (6.8, -16), (5.8, -94), (0, -108)]
dbh.polygon(poly(b_hr_l), fill=(185, 198, 214, 255))
dbh.polygon(poly(b_hr_r), fill=(110, 122, 138, 255))
dbh.polygon(poly([(-5.5, 20), (5.5, 20), (6.2, -22), (-6.2, -22)]), fill=(40, 46, 56, 255))
b_hr_lume_pts = [(-2.6, -28), (2.6, -28), (2.4, -92), (0, -101), (-2.4, -92)]
dbh.polygon(poly(b_hr_lume_pts), fill=(0, 0, 0, 0))
b_hr_out = [(-5.5, 20), (5.5, 20), (6.8, -16), (5.8, -94), (0, -108), (-5.8, -94), (-6.8, -16)]
dbh.line(poly(b_hr_out + [b_hr_out[0]]), fill=(20, 24, 30, 255), width=int(1.1 * S))

baton_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(baton_hr_lume).polygon(poly(b_hr_lume_pts), fill=(255, 255, 255, 255))
baton_hr_frame_sh = add_drop_shadow(baton_hr_frame, baton_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(baton_hr_frame_sh, W, H, "hand_baton_hr_frame.png")
save_drawable(baton_hr_lume, W, H, "hand_baton_hr_lume.png")

# --- Baton Minute Hand ---
baton_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dbm = ImageDraw.Draw(baton_mn_frame)
b_mn_l = [(0, 26), (-4.5, 26), (-5.6, -18), (-4.6, -148), (0, -164)]
b_mn_r = [(0, 26), (4.5, 26), (5.6, -18), (4.6, -148), (0, -164)]
dbm.polygon(poly(b_mn_l), fill=(185, 198, 214, 255))
dbm.polygon(poly(b_mn_r), fill=(110, 122, 138, 255))
dbm.polygon(poly([(-4.5, 26), (4.5, 26), (5.2, -24), (-5.2, -24)]), fill=(40, 46, 56, 255))
b_mn_lume_pts = [(-2.1, -30), (2.1, -30), (1.9, -145), (0, -156), (-1.9, -145)]
dbm.polygon(poly(b_mn_lume_pts), fill=(0, 0, 0, 0))
b_mn_out = [(-4.5, 26), (4.5, 26), (5.6, -18), (4.6, -148), (0, -164), (-4.6, -148), (-5.6, -18)]
dbm.line(poly(b_mn_out + [b_mn_out[0]]), fill=(20, 24, 30, 255), width=int(1.1 * S))

baton_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(baton_mn_lume).polygon(poly(b_mn_lume_pts), fill=(255, 255, 255, 255))
baton_mn_frame_sh = add_drop_shadow(baton_mn_frame, baton_mn_lume, dx=3.0, dy=4.2, blur=3.2, opacity=0.68)
save_drawable(baton_mn_frame_sh, W, H, "hand_baton_mn_frame.png")
save_drawable(baton_mn_lume, W, H, "hand_baton_mn_lume.png")

# ==============================================================================
# 3. STEALTH OUTLINE HANDS (Hollow Theme-Tinted Skeleton)
# ==============================================================================
ghost_hr = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dgh = ImageDraw.Draw(ghost_hr)
dgh.line(poly(hr_outline + [hr_outline[0]]), fill=(255, 255, 255, 255), width=int(2.2 * S))
dgh.polygon(poly([(-4.5, -80), (4.5, -80), (0, -104)]), fill=(255, 255, 255, 255))
save_drawable(ghost_hr, W, H, "hand_ghost_hr.png")

ghost_mn = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dgm = ImageDraw.Draw(ghost_mn)
dgm.line(poly(mn_outline + [mn_outline[0]]), fill=(255, 255, 255, 255), width=int(2.0 * S))
dgm.polygon(poly([(-3.5, -132), (3.5, -132), (0, -158)]), fill=(255, 255, 255, 255))
save_drawable(ghost_mn, W, H, "hand_ghost_mn.png")

# ==============================================================================
# 4. ULTRA-THIN NEEDLE HANDS
# ==============================================================================
# --- Needle Hour Hand ---
needle_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnh = ImageDraw.Draw(needle_hr_frame)
nh_left = [(0, 22), (-2.0, 22), (-2.4, 12), (-1.8, 0), (-1.2, -112), (0, -115)]
nh_right = [(0, 22), (2.0, 22), (2.4, 12), (1.8, 0), (1.2, -112), (0, -115)]
dnh.polygon(poly(nh_left), fill=(210, 222, 236, 255))
dnh.polygon(poly(nh_right), fill=(128, 140, 158, 255))
nh_pip_cut = [(0, -91), (-2.2, -85), (0, -79), (2.2, -85)]
dnh.polygon(poly(nh_pip_cut), fill=(0, 0, 0, 0))
dnh.polygon(poly([(-0.6, -18), (0.6, -18), (0.6, -77), (-0.6, -77)]), fill=(0, 0, 0, 0))
dnh.polygon(poly([(-0.5, -93), (0.5, -93), (0.5, -106), (-0.5, -106)]), fill=(0, 0, 0, 0))
nh_out = [(-2.0, 22), (2.0, 22), (2.4, 12), (1.8, 0), (1.2, -112), (0, -115), (-1.2, -112), (-1.8, 0), (-2.4, 12)]
dnh.line(poly(nh_out + [nh_out[0]]), fill=(24, 28, 36, 255), width=int(1.0 * S))
dnh.line(poly(nh_pip_cut + [nh_pip_cut[0]]), fill=(24, 28, 36, 255), width=int(0.8 * S))

needle_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnh_l = ImageDraw.Draw(needle_hr_lume)
dnh_l.polygon(poly(nh_pip_cut), fill=(255, 255, 255, 255))
dnh_l.polygon(poly([(-0.6, -18), (0.6, -18), (0.6, -77), (-0.6, -77)]), fill=(255, 255, 255, 255))
dnh_l.polygon(poly([(-0.5, -93), (0.5, -93), (0.5, -106), (-0.5, -106)]), fill=(255, 255, 255, 255))

needle_hr_frame_sh = add_drop_shadow(needle_hr_frame, needle_hr_lume, dx=2.2, dy=3.2, blur=2.4, opacity=0.62)
save_drawable(needle_hr_frame_sh, W, H, "hand_needle_hr_frame.png")
save_drawable(needle_hr_lume, W, H, "hand_needle_hr_lume.png")

# --- Needle Minute Hand ---
needle_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnm = ImageDraw.Draw(needle_mn_frame)
nm_left = [(0, 28), (-1.8, 28), (-2.2, 16), (-1.5, 0), (-1.0, -168), (0, -171)]
nm_right = [(0, 28), (1.8, 28), (2.2, 16), (1.5, 0), (1.0, -168), (0, -171)]
dnm.polygon(poly(nm_left), fill=(210, 222, 236, 255))
dnm.polygon(poly(nm_right), fill=(128, 140, 158, 255))
nm_pip_cut = [(0, -141), (-1.8, -135), (0, -129), (1.8, -135)]
dnm.polygon(poly(nm_pip_cut), fill=(0, 0, 0, 0))
dnm.polygon(poly([(-0.5, -20), (0.5, -20), (0.5, -127), (-0.5, -127)]), fill=(0, 0, 0, 0))
dnm.polygon(poly([(-0.4, -143), (0.4, -143), (0.4, -162), (-0.4, -162)]), fill=(0, 0, 0, 0))
nm_out = [(-1.8, 28), (1.8, 28), (2.2, 16), (1.5, 0), (1.0, -168), (0, -171), (-1.0, -168), (-1.5, 0), (-2.2, 16)]
dnm.line(poly(nm_out + [nm_out[0]]), fill=(24, 28, 36, 255), width=int(1.0 * S))
dnm.line(poly(nm_pip_cut + [nm_pip_cut[0]]), fill=(24, 28, 36, 255), width=int(0.8 * S))

needle_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnm_l = ImageDraw.Draw(needle_mn_lume)
dnm_l.polygon(poly(nm_pip_cut), fill=(255, 255, 255, 255))
dnm_l.polygon(poly([(-0.5, -20), (0.5, -20), (0.5, -127), (-0.5, -127)]), fill=(255, 255, 255, 255))
dnm_l.polygon(poly([(-0.4, -143), (0.4, -143), (0.4, -162), (-0.4, -162)]), fill=(255, 255, 255, 255))

needle_mn_frame_sh = add_drop_shadow(needle_mn_frame, needle_mn_lume, dx=2.5, dy=3.8, blur=2.8, opacity=0.65)
save_drawable(needle_mn_frame_sh, W, H, "hand_needle_mn_frame.png")
save_drawable(needle_mn_lume, W, H, "hand_needle_mn_lume.png")

# ==============================================================================
# 5. SLIM AVIATOR ARROW HANDS
# ==============================================================================
# --- Arrow Hour Hand ---
arrow_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dah = ImageDraw.Draw(arrow_hr_frame)
ah_left = [(0, 22), (-2.8, 22), (-3.2, 14), (-2.2, 0), (-2.0, -80), (-6.2, -80), (0, -114)]
ah_right = [(0, 22), (2.8, 22), (3.2, 14), (2.2, 0), (2.0, -80), (6.2, -80), (0, -114)]
dah.polygon(poly(ah_left), fill=(210, 222, 236, 255))
dah.polygon(poly(ah_right), fill=(128, 140, 158, 255))
ah_tri_cut = [(-3.8, -83), (3.8, -83), (0, -107)]
dah.polygon(poly(ah_tri_cut), fill=(0, 0, 0, 0))
ah_stem_cut = [(-1.1, -16), (1.1, -16), (1.1, -74), (-1.1, -74)]
dah.polygon(poly(ah_stem_cut), fill=(0, 0, 0, 0))
ah_out = [(-2.8, 22), (2.8, 22), (3.2, 14), (2.2, 0), (2.0, -80), (6.2, -80), (0, -114), (-6.2, -80), (-2.0, -80), (-2.2, 0), (-3.2, 14)]
dah.line(poly(ah_out + [ah_out[0]]), fill=(24, 28, 36, 255), width=int(1.1 * S))
dah.line(poly(ah_tri_cut + [ah_tri_cut[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))
dah.line(poly(ah_stem_cut + [ah_stem_cut[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))

arrow_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dah_l = ImageDraw.Draw(arrow_hr_lume)
dah_l.polygon(poly(ah_tri_cut), fill=(255, 255, 255, 255))
dah_l.polygon(poly(ah_stem_cut), fill=(255, 255, 255, 255))

arrow_hr_frame_sh = add_drop_shadow(arrow_hr_frame, arrow_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(arrow_hr_frame_sh, W, H, "hand_arrow_hr_frame.png")
save_drawable(arrow_hr_lume, W, H, "hand_arrow_hr_lume.png")

# --- Arrow Minute Hand ---
arrow_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dam = ImageDraw.Draw(arrow_mn_frame)
am_left = [(0, 28), (-2.2, 28), (-2.6, 18), (-1.7, 0), (-1.5, -132), (-5.2, -132), (0, -168)]
am_right = [(0, 28), (2.2, 28), (2.6, 18), (1.7, 0), (1.5, -132), (5.2, -132), (0, -168)]
dam.polygon(poly(am_left), fill=(210, 222, 236, 255))
dam.polygon(poly(am_right), fill=(128, 140, 158, 255))
am_tri_cut = [(-3.2, -135), (3.2, -135), (0, -161)]
dam.polygon(poly(am_tri_cut), fill=(0, 0, 0, 0))
am_stem_cut = [(-0.9, -18), (0.9, -18), (0.9, -125), (-0.9, -125)]
dam.polygon(poly(am_stem_cut), fill=(0, 0, 0, 0))
am_out = [(-2.2, 28), (2.2, 28), (2.6, 18), (1.7, 0), (1.5, -132), (5.2, -132), (0, -168), (-5.2, -132), (-1.5, -132), (-1.7, 0), (-2.6, 18)]
dam.line(poly(am_out + [am_out[0]]), fill=(24, 28, 36, 255), width=int(1.1 * S))
dam.line(poly(am_tri_cut + [am_tri_cut[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))
dam.line(poly(am_stem_cut + [am_stem_cut[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))

arrow_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dam_l = ImageDraw.Draw(arrow_mn_lume)
dam_l.polygon(poly(am_tri_cut), fill=(255, 255, 255, 255))
dam_l.polygon(poly(am_stem_cut), fill=(255, 255, 255, 255))

arrow_mn_frame_sh = add_drop_shadow(arrow_mn_frame, arrow_mn_lume, dx=3.0, dy=4.2, blur=3.2, opacity=0.68)
save_drawable(arrow_mn_frame_sh, W, H, "hand_arrow_mn_frame.png")
save_drawable(arrow_mn_lume, W, H, "hand_arrow_mn_lume.png")

# ==============================================================================
# 6. CENTER PINION CAP (40x40 at x=205, y=205)
#    Split into untinted base + tintable accent ring
# ==============================================================================
PW, PH = 40, 40
PW2, PH2 = PW * S, PH * S
pcx, pcy = PW2 // 2, PH2 // 2

pin_base = Image.new("RGBA", (PW2, PH2), (0, 0, 0, 0))
dp = ImageDraw.Draw(pin_base)
r1 = int(12.5 * S)
dp.ellipse((pcx-r1, pcy-r1, pcx+r1, pcy+r1), fill=(42, 49, 58, 255), outline=(165, 180, 198, 255), width=int(1.5 * S))
r1_in = int(11.0 * S)
dp.arc((pcx-r1_in, pcy-r1_in, pcx+r1_in, pcy+r1_in), start=190, end=350, fill=(220, 232, 245, 220), width=int(1.2 * S))
r2 = int(8.0 * S)
dp.ellipse((pcx-r2, pcy-r2, pcx+r2, pcy+r2), fill=(18, 22, 28, 255))
r3 = int(3.2 * S)
dp.ellipse((pcx-r3, pcy-r3, pcx+r3, pcy+r3), fill=(215, 225, 238, 255), outline=(30, 36, 44, 255), width=max(1, int(0.8 * S)))

# Add pinion drop shadow
p_alpha = pin_base.split()[3]
p_sh = Image.new("RGBA", (PW2, PH2), (0, 0, 0, 0))
p_sh_a = p_alpha.point(lambda p: int(p * 0.72))
p_sh_shift = Image.new("L", (PW2, PH2), 0)
p_sh_shift.paste(p_sh_a, (int(1.5 * S), int(2.5 * S)))
p_sh_shift = p_sh_shift.filter(ImageFilter.GaussianBlur(2.2 * S))
p_sh.putalpha(p_sh_shift)
p_sh.alpha_composite(pin_base)
save_drawable(p_sh, PW, PH, "main_pinion_base.png")

pin_ring = Image.new("RGBA", (PW2, PH2), (0, 0, 0, 0))
ImageDraw.Draw(pin_ring).ellipse((pcx-r2, pcy-r2, pcx+r2, pcy+r2), outline=(255, 255, 255, 255), width=int(1.6 * S))
save_drawable(pin_ring, PW, PH, "main_pinion_ring.png")
