import os, math
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")

# 100x100 sub-dial coordinate space, rendered at 4x supersampling (400x400) for razor-sharp edges
S = 100
K = 4
SK = S * K  # 400
cx_s, cy_s = SK // 2, SK // 2  # 200, 200

# Sub-dial inner chamber radius is r_inner = 39.65px (158.6px at 4x), with outline width=2 at 2x (1px at 1x).
# Previously r_pie was 35.75px (leaving a ~3.9px gap).
# Pulling segments closer to the bounding circle: r_pie = 37.85px (leaving ~1px clean clearance inside the inner border)
r_pie_1x = 37.85
r_cut_1x = 17.10  # Center hub cap outer radius is 15.86px, leaving ~1.2px clean gap around hub

r_pie = int(round(r_pie_1x * K))      # 151 px at 4x
r_cut_hub = int(round(r_cut_1x * K))  # 68 px at 4x

# Build subtle monochrome radial gradient field (400x400 grayscale L)
# Combines:
# 1) Radial convex/bevel profile across the ring [r_cut_hub .. r_pie]:
#    Slightly darker near the inner hub (v ~ 212), rising smoothly to 255 in the upper-mid band,
#    and subtly shading down to ~200 right at the outer rim near the bounding circle.
# 2) Subtle off-center upper-left to lower-right directional sheen (+/- 5%) for 3D realism.
grad_bytes = bytearray(SK * SK)
lx, ly = -0.6, -0.8  # upper-left light direction
for y in range(SK):
    dy = y - cy_s
    row_off = y * SK
    for x in range(SK):
        dx = x - cx_s
        r = math.hypot(dx, dy)
        if r_cut_hub - 4 <= r <= r_pie + 4:
            # Normalized radial position u in [0, 1] from inner cutout to outer edge
            u = max(0.0, min(1.0, (r - r_cut_hub) / float(r_pie - r_cut_hub)))
            # Smooth domed radial profile peaking at u = 0.55:
            # u=0.0 -> 0.85, u=0.55 -> 1.00, u=1.0 -> 0.78
            if u <= 0.55:
                t = u / 0.55
                rad_shade = 0.85 + 0.15 * math.sin(t * (math.pi / 2.0))
            else:
                t = (u - 0.55) / 0.45
                rad_shade = 1.00 - 0.22 * (t ** 1.6)

            # Subtle directional gradient across the sub-dial (+/- 0.04)
            dir_dot = (dx * lx + dy * ly) / float(r_pie)
            shade = max(0.72, min(1.0, rad_shade + 0.04 * dir_dot))
            grad_bytes[row_off + x] = int(round(shade * 255.0))

grad_L = Image.frombytes("L", (SK, SK), bytes(grad_bytes))
grad_rgba = Image.merge("RGBA", (grad_L, grad_L, grad_L, Image.new("L", (SK, SK), 255)))

mask_all = Image.new("L", (SK, SK), 0)
d_all = ImageDraw.Draw(mask_all)

for i in range(8):
    m_seg = Image.new("L", (SK, SK), 0)
    dw = ImageDraw.Draw(m_seg)
    a_start = -90 + i * 45 + 3.0
    a_end = -90 + (i + 1) * 45 - 3.0
    dw.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=255)
    dw.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=0)

    d_all.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=255)

    w_img = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
    w_img.paste(grad_rgba, (0, 0), m_seg)
    w_small = w_img.resize((S, S), Image.Resampling.LANCZOS)
    w_small.save(os.path.join(OUTPUT_DIR, f"subdial_seg_{i+1}.png"))
    w_small.save(os.path.join(BASE_DIR, f"subdial_seg_{i+1}.png"))

d_all.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=0)
wedges_all = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
wedges_all.paste(grad_rgba, (0, 0), mask_all)
ghost_small = wedges_all.resize((S, S), Image.Resampling.LANCZOS)
ghost_small.save(os.path.join(OUTPUT_DIR, "subdial_seg_ghost.png"))
ghost_small.save(os.path.join(BASE_DIR, "subdial_seg_ghost.png"))
print("Saved enlarged battery segments with subtle monochrome radial gradient!")

# Also generate subdial_batt_radial_shade.png:
# Because WFF <PartImage tintColor="..."> uses SRC_IN (replacing RGB with solid tintColor),
# we composite a dedicated monochrome radial shading overlay image on top of the segments!
shade_rgba = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
s_bytes = bytearray(SK * SK * 4)
m_all_bytes = mask_all.tobytes()

for y in range(SK):
    dy = y - cy_s
    row_off = y * SK
    for x in range(SK):
        m_val = m_all_bytes[row_off + x]
        if m_val > 0:
            dx = x - cx_s
            r = math.hypot(dx, dy)
            u = max(0.0, min(1.0, (r - r_cut_hub) / float(r_pie - r_cut_hub)))
            # Radial profile:
            # Darken slightly toward the outer rim (u -> 1.0) and inner hub (u -> 0.0),
            # with a subtle bright crest around u = 0.42, plus off-center directional light
            dir_dot = (dx * lx + dy * ly) / float(r_pie)  # -1 (bottom-right) to +1 (top-left)
            # Signed brightness delta in [-0.34, +0.12]
            if u < 0.42:
                t = (0.42 - u) / 0.42
                rad_delta = 0.06 - 0.24 * (t ** 1.4)
            else:
                t = (u - 0.42) / 0.58
                rad_delta = 0.06 - 0.36 * (t ** 1.5)

            delta = rad_delta + 0.07 * dir_dot
            idx = (row_off + x) * 4
            if delta >= 0.0:
                # Subtle white highlight
                a_out = min(255, int(round(delta * 255.0 * (m_val / 255.0))))
                s_bytes[idx] = 255
                s_bytes[idx+1] = 255
                s_bytes[idx+2] = 255
                s_bytes[idx+3] = a_out
            else:
                # Subtle black shading toward inner & outer circumference
                a_out = min(255, int(round((-delta) * 255.0 * (m_val / 255.0))))
                s_bytes[idx] = 0
                s_bytes[idx+1] = 0
                s_bytes[idx+2] = 0
                s_bytes[idx+3] = a_out

shade_hi = Image.frombytes("RGBA", (SK, SK), bytes(s_bytes))
shade_small = shade_hi.resize((S, S), Image.Resampling.LANCZOS)
shade_small.save(os.path.join(OUTPUT_DIR, "subdial_batt_radial_shade.png"))
shade_small.save(os.path.join(BASE_DIR, "subdial_batt_radial_shade.png"))
print("Saved subdial_batt_radial_shade.png!")
