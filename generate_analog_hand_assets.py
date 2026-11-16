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
# ==============================================================================
# 4. SUPER-THIN HAIRLINE / WIRE HANDS (Pure straight profile, no diamond pip)
# ==============================================================================
# --- Hairline Hour Hand ---
needle_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnh = ImageDraw.Draw(needle_hr_frame)
nh_left = [(0, 22), (-1.2, 22), (-1.2, -112), (0, -115)]
nh_right = [(0, 22), (1.2, 22), (1.2, -112), (0, -115)]
dnh.polygon(poly(nh_left), fill=(210, 222, 236, 255))
dnh.polygon(poly(nh_right), fill=(128, 140, 158, 255))
nh_cut = [(-0.5, -16), (0.5, -16), (0.5, -108), (-0.5, -108)]
dnh.polygon(poly(nh_cut), fill=(0, 0, 0, 0))
nh_out = [(-1.2, 22), (1.2, 22), (1.2, -112), (0, -115), (-1.2, -112)]
dnh.line(poly(nh_out + [nh_out[0]]), fill=(24, 28, 36, 255), width=int(1.0 * S))

needle_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnh_l = ImageDraw.Draw(needle_hr_lume)
dnh_l.polygon(poly(nh_cut), fill=(255, 255, 255, 255))

needle_hr_frame_sh = add_drop_shadow(needle_hr_frame, needle_hr_lume, dx=2.2, dy=3.2, blur=2.4, opacity=0.62)
save_drawable(needle_hr_frame_sh, W, H, "hand_needle_hr_frame.png")
save_drawable(needle_hr_lume, W, H, "hand_needle_hr_lume.png")

# --- Hairline Minute Hand ---
needle_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnm = ImageDraw.Draw(needle_mn_frame)
nm_left = [(0, 28), (-0.95, 28), (-0.95, -168), (0, -171)]
nm_right = [(0, 28), (0.95, 28), (0.95, -168), (0, -171)]
dnm.polygon(poly(nm_left), fill=(210, 222, 236, 255))
dnm.polygon(poly(nm_right), fill=(128, 140, 158, 255))
nm_cut = [(-0.4, -18), (0.4, -18), (0.4, -164), (-0.4, -164)]
dnm.polygon(poly(nm_cut), fill=(0, 0, 0, 0))
nm_out = [(-0.95, 28), (0.95, 28), (0.95, -168), (0, -171), (-0.95, -168)]
dnm.line(poly(nm_out + [nm_out[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))

needle_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dnm_l = ImageDraw.Draw(needle_mn_lume)
dnm_l.polygon(poly(nm_cut), fill=(255, 255, 255, 255))

needle_mn_frame_sh = add_drop_shadow(needle_mn_frame, needle_mn_lume, dx=2.5, dy=3.8, blur=2.8, opacity=0.65)
save_drawable(needle_mn_frame_sh, W, H, "hand_needle_mn_frame.png")
save_drawable(needle_mn_lume, W, H, "hand_needle_mn_lume.png")

# ==============================================================================
# 5. TACTICAL CHISEL RECTANGLE HANDS (Wide parallel rectangles with pointed ends)
# ==============================================================================
# --- Chisel Hour Hand ---
chisel_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dch = ImageDraw.Draw(chisel_hr_frame)
ch_left = [(0, 22), (-2.5, 22), (-2.5, 14), (-5.0, 0), (-5.0, -92), (0, -114)]
ch_right = [(0, 22), (2.5, 22), (2.5, 14), (5.0, 0), (5.0, -92), (0, -114)]
dch.polygon(poly(ch_left), fill=(218, 228, 240, 255))
dch.polygon(poly(ch_right), fill=(125, 138, 155, 255))
ch_lume_cut_hr = [(-3.0, -14), (3.0, -14), (3.0, -90), (0, -107), (-3.0, -90)]
dch.polygon(poly(ch_lume_cut_hr), fill=(0, 0, 0, 0))
ch_out_hr = [(-2.5, 22), (2.5, 22), (2.5, 14), (5.0, 0), (5.0, -92), (0, -114), (-5.0, -92), (-5.0, 0), (-2.5, 14)]
dch.line(poly(ch_out_hr + [ch_out_hr[0]]), fill=(20, 24, 32, 255), width=int(1.2 * S))
dch.line(poly(ch_lume_cut_hr + [ch_lume_cut_hr[0]]), fill=(20, 24, 32, 255), width=int(1.0 * S))

chisel_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dch_l = ImageDraw.Draw(chisel_hr_lume)
dch_l.polygon(poly(ch_lume_cut_hr), fill=(255, 255, 255, 255))

chisel_hr_frame_sh = add_drop_shadow(chisel_hr_frame, chisel_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(chisel_hr_frame_sh, W, H, "hand_chisel_hr_frame.png")
save_drawable(chisel_hr_lume, W, H, "hand_chisel_hr_lume.png")

# --- Chisel Minute Hand ---
chisel_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dcm = ImageDraw.Draw(chisel_mn_frame)
cm_left = [(0, 28), (-2.0, 28), (-2.0, 18), (-4.0, 0), (-4.0, -148), (0, -170)]
cm_right = [(0, 28), (2.0, 28), (2.0, 18), (4.0, 0), (4.0, -148), (0, -170)]
dcm.polygon(poly(cm_left), fill=(218, 228, 240, 255))
dcm.polygon(poly(cm_right), fill=(125, 138, 155, 255))
cm_lume_cut_mn = [(-2.4, -16), (2.4, -16), (2.4, -146), (0, -164), (-2.4, -146)]
dcm.polygon(poly(cm_lume_cut_mn), fill=(0, 0, 0, 0))
cm_out_mn = [(-2.0, 28), (2.0, 28), (2.0, 18), (4.0, 0), (4.0, -148), (0, -170), (-4.0, -148), (-4.0, 0), (-2.0, 18)]
dcm.line(poly(cm_out_mn + [cm_out_mn[0]]), fill=(20, 24, 32, 255), width=int(1.2 * S))
dcm.line(poly(cm_lume_cut_mn + [cm_lume_cut_mn[0]]), fill=(20, 24, 32, 255), width=int(1.0 * S))

chisel_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dcm_l = ImageDraw.Draw(chisel_mn_lume)
dcm_l.polygon(poly(cm_lume_cut_mn), fill=(255, 255, 255, 255))

chisel_mn_frame_sh = add_drop_shadow(chisel_mn_frame, chisel_mn_lume, dx=3.0, dy=4.2, blur=3.2, opacity=0.68)
save_drawable(chisel_mn_frame_sh, W, H, "hand_chisel_mn_frame.png")
save_drawable(chisel_mn_lume, W, H, "hand_chisel_mn_lume.png")

# ==============================================================================
# 5B. LONG CENTER-PIVOT HANDS (Longer reach, square ends, uniform minute thickness)
# ==============================================================================
# --- Long Hour Hand (y=0 to -128, square tip, same thickness as minute hand) ---
long_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dlh = ImageDraw.Draw(long_hr_frame)
lh_left = [(0, 0), (-4.6, 0), (-5.2, -22), (-4.0, -128), (0, -128)]
lh_right = [(0, 0), (4.6, 0), (5.2, -22), (4.0, -128), (0, -128)]
dlh.polygon(poly(lh_left), fill=(215, 225, 238, 255))
dlh.polygon(poly(lh_right), fill=(125, 138, 156, 255))
lh_lume_pts = [(-2.4, -20), (2.4, -20), (2.0, -122), (-2.0, -122)]
dlh.polygon(poly(lh_lume_pts), fill=(0, 0, 0, 0))
lh_out = [(-4.6, 0), (4.6, 0), (5.2, -22), (4.0, -128), (-4.0, -128), (-5.2, -22)]
dlh.line(poly(lh_out + [lh_out[0]]), fill=(20, 24, 32, 255), width=int(1.1 * S))
dlh.line(poly(lh_lume_pts + [lh_lume_pts[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))

long_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(long_hr_lume).polygon(poly(lh_lume_pts), fill=(255, 255, 255, 255))

long_hr_frame_sh = add_drop_shadow(long_hr_frame, long_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(long_hr_frame_sh, W, H, "hand_long_hr_frame.png")
save_drawable(long_hr_lume, W, H, "hand_long_hr_lume.png")

# --- Long Minute Hand (y=0 to -188, square tip) ---
long_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dlm = ImageDraw.Draw(long_mn_frame)
lm_left = [(0, 0), (-4.6, 0), (-5.2, -22), (-4.0, -188), (0, -188)]
lm_right = [(0, 0), (4.6, 0), (5.2, -22), (4.0, -188), (0, -188)]
dlm.polygon(poly(lm_left), fill=(215, 225, 238, 255))
dlm.polygon(poly(lm_right), fill=(125, 138, 156, 255))
lm_lume_pts = [(-2.4, -20), (2.4, -20), (2.0, -182), (-2.0, -182)]
dlm.polygon(poly(lm_lume_pts), fill=(0, 0, 0, 0))
lm_out = [(-4.6, 0), (4.6, 0), (5.2, -22), (4.0, -188), (-4.0, -188), (-5.2, -22)]
dlm.line(poly(lm_out + [lm_out[0]]), fill=(20, 24, 32, 255), width=int(1.1 * S))
dlm.line(poly(lm_lume_pts + [lm_lume_pts[0]]), fill=(24, 28, 36, 255), width=int(0.9 * S))

long_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(long_mn_lume).polygon(poly(lm_lume_pts), fill=(255, 255, 255, 255))

long_mn_frame_sh = add_drop_shadow(long_mn_frame, long_mn_lume, dx=3.0, dy=4.2, blur=3.2, opacity=0.68)
save_drawable(long_mn_frame_sh, W, H, "hand_long_mn_frame.png")
save_drawable(long_mn_lume, W, H, "hand_long_mn_lume.png")

# ==============================================================================
# 5C. BOLD DIVER HANDS (Wider Hour Hand + Narrower Minute Hand, rounded ends)
# ==============================================================================
def rounded_cap_pts(yc, rx, ry, start_deg, end_deg, steps=16):
    pts = []
    for k in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * (k / steps))
        pts.append((rx * math.cos(a), yc + ry * math.sin(a)))
    return pts

# --- Wide Rounded Hour Hand ---
diver_hr_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ddh = ImageDraw.Draw(diver_hr_frame)
# Top cap centered at y=-104.5 (radius 11.5 -> tip at -116), bottom cap centered at y=14.5 (radius 7.5 -> tail at +22)
hr_top_l = rounded_cap_pts(-104.5, 11.5, 11.5, 270, 180, 12)   # (0,-116) -> (-11.5,-104.5)
hr_bot_l = rounded_cap_pts(14.5, 7.5, 7.5, 180, 90, 10)       # (-7.5,14.5) -> (0,22)
hr_top_r = rounded_cap_pts(-104.5, 11.5, 11.5, 270, 360, 12)  # (0,-116) -> (11.5,-104.5)
hr_bot_r = rounded_cap_pts(14.5, 7.5, 7.5, 0, 90, 10)         # (7.5,14.5) -> (0,22)

dh_left = [(0, 22)] + list(reversed(hr_bot_l)) + [(-11.5, -14)] + list(reversed(hr_top_l)) + [(0, -116)]
dh_right = [(0, -116)] + hr_top_r + [(11.5, -14)] + hr_bot_r + [(0, 22)]
ddh.polygon(poly(dh_left), fill=(215, 226, 240, 255))
ddh.polygon(poly(dh_right), fill=(122, 136, 155, 255))

dh_lume_top = rounded_cap_pts(-100.0, 6.8, 6.8, 180, 360, 16)
dh_lume_bot = rounded_cap_pts(-20.0, 6.8, 6.8, 0, 180, 16)
dh_lume_pts = dh_lume_top + dh_lume_bot
ddh.polygon(poly(dh_lume_pts), fill=(0, 0, 0, 0))

dh_out = hr_bot_r + list(reversed(hr_bot_l)) + [(-11.5, -14)] + list(reversed(hr_top_l)) + hr_top_r + [(11.5, -14)]
ddh.line(poly(dh_out + [dh_out[0]]), fill=(20, 24, 32, 255), width=int(1.2 * S))
ddh.line(poly(dh_lume_pts + [dh_lume_pts[0]]), fill=(24, 28, 36, 255), width=int(1.0 * S))

diver_hr_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(diver_hr_lume).polygon(poly(dh_lume_pts), fill=(255, 255, 255, 255))

diver_hr_frame_sh = add_drop_shadow(diver_hr_frame, diver_hr_lume, dx=2.5, dy=3.5, blur=2.8, opacity=0.65)
save_drawable(diver_hr_frame_sh, W, H, "hand_diver_hr_frame.png")
save_drawable(diver_hr_lume, W, H, "hand_diver_hr_lume.png")

# --- Narrower Rounded Minute Hand ---
diver_mn_frame = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ddm = ImageDraw.Draw(diver_mn_frame)
# Top cap centered at y=-170 (radius 1.8 -> tip at -171.8), bottom cap centered at y=23.8 (radius 2.2 -> tail at +26)
mn_top_l = rounded_cap_pts(-170.0, 1.8, 1.8, 270, 180, 10)
mn_bot_l = rounded_cap_pts(23.8, 2.2, 2.2, 180, 90, 10)
mn_top_r = rounded_cap_pts(-170.0, 1.8, 1.8, 270, 360, 10)
mn_bot_r = rounded_cap_pts(23.8, 2.2, 2.2, 0, 90, 10)

dm_left = [(0, 26)] + list(reversed(mn_bot_l)) + [(-2.4, -14)] + list(reversed(mn_top_l)) + [(0, -171.8)]
dm_right = [(0, -171.8)] + mn_top_r + [(2.4, -14)] + mn_bot_r + [(0, 26)]
ddm.polygon(poly(dm_left), fill=(215, 226, 240, 255))
ddm.polygon(poly(dm_right), fill=(122, 136, 155, 255))

dm_lume_pts = rounded_cap_pts(-165.0, 0.9, 0.9, 180, 360, 10) + rounded_cap_pts(-18.0, 1.0, 1.0, 0, 180, 10)
ddm.polygon(poly(dm_lume_pts), fill=(0, 0, 0, 0))
dm_out = mn_bot_r + list(reversed(mn_bot_l)) + [(-2.4, -14)] + list(reversed(mn_top_l)) + mn_top_r + [(2.4, -14)]
ddm.line(poly(dm_out + [dm_out[0]]), fill=(20, 24, 32, 255), width=int(1.0 * S))

diver_mn_lume = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
ImageDraw.Draw(diver_mn_lume).polygon(poly(dm_lume_pts), fill=(255, 255, 255, 255))

diver_mn_frame_sh = add_drop_shadow(diver_mn_frame, diver_mn_lume, dx=2.8, dy=3.8, blur=2.8, opacity=0.65)
save_drawable(diver_mn_frame_sh, W, H, "hand_diver_mn_frame.png")
save_drawable(diver_mn_lume, W, H, "hand_diver_mn_lume.png")

# ==============================================================================
# 5D. HOLLOW THEME HANDS (Theme-colored frame, completely transparent middle)
# ==============================================================================
# --- Hollow Hour Hand ---
hollow_hr = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dhh = ImageDraw.Draw(hollow_hr)
hh_outer = [(-5.5, 20), (5.5, 20), (8.2, -14), (8.2, -84), (0, -114), (-8.2, -84), (-8.2, -14)]
hh_inner = [(-4.8, -18), (4.8, -18), (4.8, -81), (0, -104), (-4.8, -81)]
dhh.polygon(poly(hh_outer), fill=(255, 255, 255, 255))
dhh.polygon(poly(hh_inner), fill=(0, 0, 0, 0))

hollow_hr_sh = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
hh_a = hollow_hr.split()[3].point(lambda p: int(p * 0.65))
hh_sh_mask = Image.new("L", (W2, H2), 0)
hh_sh_mask.paste(hh_a, (int(2.5 * S), int(3.5 * S)))
hh_sh_mask = hh_sh_mask.filter(ImageFilter.GaussianBlur(2.6 * S))
hollow_hr_sh.putalpha(hh_sh_mask)
save_drawable(hollow_hr_sh, W, H, "hand_hollow_hr_sh.png")
save_drawable(hollow_hr, W, H, "hand_hollow_hr.png")

# --- Hollow Minute Hand ---
hollow_mn = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
dhm = ImageDraw.Draw(hollow_mn)
hm_outer = [(-4.4, 26), (4.4, 26), (6.2, -16), (5.8, -140), (0, -170), (-5.8, -140), (-6.2, -16)]
hm_inner = [(-3.2, -20), (3.2, -20), (3.0, -137), (0, -160), (-3.0, -137)]
dhm.polygon(poly(hm_outer), fill=(255, 255, 255, 255))
dhm.polygon(poly(hm_inner), fill=(0, 0, 0, 0))

hollow_mn_sh = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
hm_a = hollow_mn.split()[3].point(lambda p: int(p * 0.68))
hm_sh_mask = Image.new("L", (W2, H2), 0)
hm_sh_mask.paste(hm_a, (int(3.0 * S), int(4.2 * S)))
hm_sh_mask = hm_sh_mask.filter(ImageFilter.GaussianBlur(3.0 * S))
hollow_mn_sh.putalpha(hm_sh_mask)
save_drawable(hollow_mn_sh, W, H, "hand_hollow_mn_sh.png")
save_drawable(hollow_mn, W, H, "hand_hollow_mn.png")

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
