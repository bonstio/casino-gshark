import os, math
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")

# Remove old 12..59 segment drawables so AAPT2 only packages 00..11
for old_i in range(12, 60):
    p = os.path.join(OUTPUT_DIR, f"subdial_sec_{old_i:02d}.png")
    if os.path.exists(p):
        os.remove(p)

# 100x100 sub-dial coordinate space, rendered at 4x supersampling (400x400) for razor-sharp edges
S = 100
K = 4
SK = S * K  # 400
cx_s, cy_s = SK // 2, SK // 2  # 200, 200

# Match the enlarged battery segment outer/inner radii:
# r_pie_1x = 37.85 (leaves ~1px clean clearance inside the sub-dial inner border)
# r_cut_1x = 17.10 (leaves ~1.2px clean gap around the center hub cap)
r_pie_1x = 37.85
r_cut_1x = 17.10

r_pie = int(round(r_pie_1x * K))      # 151 px at 4x
r_cut_hub = int(round(r_cut_1x * K))  # 68 px at 4x

# Build subtle monochrome radial gradient field (400x400 grayscale L)
grad_bytes = bytearray(SK * SK)
lx, ly = -0.6, -0.8  # upper-left light direction
for y in range(SK):
    dy = y - cy_s
    row_off = y * SK
    for x in range(SK):
        dx = x - cx_s
        r = math.hypot(dx, dy)
        if r_cut_hub - 4 <= r <= r_pie + 4:
            u = max(0.0, min(1.0, (r - r_cut_hub) / float(r_pie - r_cut_hub)))
            if u <= 0.55:
                t = u / 0.55
                rad_shade = 0.85 + 0.15 * math.sin(t * (math.pi / 2.0))
            else:
                t = (u - 0.55) / 0.45
                rad_shade = 1.00 - 0.22 * (t ** 1.6)

            dir_dot = (dx * lx + dy * ly) / float(r_pie)
            shade = max(0.72, min(1.0, rad_shade + 0.04 * dir_dot))
            grad_bytes[row_off + x] = int(round(shade * 255.0))

grad_L = Image.frombytes("L", (SK, SK), bytes(grad_bytes))
grad_rgba = Image.merge("RGBA", (grad_L, grad_L, grad_L, Image.new("L", (SK, SK), 255)))

mask_all = Image.new("L", (SK, SK), 0)
d_all = ImageDraw.Draw(mask_all)

# 12 segments around 360 degrees -> 30.0 degrees per step.
# Use a 2.5-degree half-gap (5.0-degree total gap between segments, 25.0-degree wedge)
# matching the bold tactical aesthetic of the 8-segment battery gauge.
half_gap_deg = 2.50
wedge_span_deg = 30.0 - 2.0 * half_gap_deg  # 25.0 degrees

for i in range(12):
    m_seg = Image.new("L", (SK, SK), 0)
    dw = ImageDraw.Draw(m_seg)
    a_start = -90.0 + i * 30.0 + half_gap_deg
    a_end = -90.0 + (i + 1) * 30.0 - half_gap_deg
    dw.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=255)
    dw.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=0)

    d_all.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=255)

    w_img = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
    w_img.paste(grad_rgba, (0, 0), m_seg)
    w_small = w_img.resize((S, S), Image.Resampling.LANCZOS)
    w_small.save(os.path.join(OUTPUT_DIR, f"subdial_sec_{i:02d}.png"))

# Also generate the 10 cumulative 0.5s fill steps (subdial_sec_fill_01 .. subdial_sec_fill_10)
# at segment 0's position (-90.0 + 2.5 to -90.0 + 2.5 + step * 2.5 deg),
# so each 5-second segment visually fills up in 10 half-second increments!
for step in range(1, 11):
    m_fill = Image.new("L", (SK, SK), 0)
    df = ImageDraw.Draw(m_fill)
    a_start = -90.0 + half_gap_deg
    a_end = a_start + (wedge_span_deg * step) / 10.0
    df.pieslice((cx_s - r_pie, cy_s - r_pie, cx_s + r_pie, cy_s + r_pie), start=a_start, end=a_end, fill=255)
    df.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=0)

    f_img = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
    f_img.paste(grad_rgba, (0, 0), m_fill)
    f_small = f_img.resize((S, S), Image.Resampling.LANCZOS)
    f_small.save(os.path.join(OUTPUT_DIR, f"subdial_sec_fill_{step:02d}.png"))

d_all.ellipse((cx_s - r_cut_hub, cy_s - r_cut_hub, cx_s + r_cut_hub, cy_s + r_cut_hub), fill=0)
wedges_all = Image.new("RGBA", (SK, SK), (0, 0, 0, 0))
wedges_all.paste(grad_rgba, (0, 0), mask_all)
ghost_small = wedges_all.resize((S, S), Image.Resampling.LANCZOS)
ghost_small.save(os.path.join(OUTPUT_DIR, "subdial_sec_ghost.png"))
ghost_small.save(os.path.join(BASE_DIR, "subdial_sec_ghost.png"))
print("Saved 12 full segments + 10 progressive 0.5s fill steps + subdial_sec_ghost.png!")

# Generate subdial_sec_radial_shade.png clipped to the 12-segment mask
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
            dir_dot = (dx * lx + dy * ly) / float(r_pie)
            if u < 0.42:
                t = (0.42 - u) / 0.42
                rad_delta = 0.06 - 0.24 * (t ** 1.4)
            else:
                t = (u - 0.42) / 0.58
                rad_delta = 0.06 - 0.36 * (t ** 1.5)

            delta = rad_delta + 0.07 * dir_dot
            idx = (row_off + x) * 4
            if delta >= 0.0:
                a_out = min(255, int(round(delta * 255.0 * (m_val / 255.0))))
                s_bytes[idx] = 255
                s_bytes[idx+1] = 255
                s_bytes[idx+2] = 255
                s_bytes[idx+3] = a_out
            else:
                a_out = min(255, int(round((-delta) * 255.0 * (m_val / 255.0))))
                s_bytes[idx] = 0
                s_bytes[idx+1] = 0
                s_bytes[idx+2] = 0
                s_bytes[idx+3] = a_out

shade_hi = Image.frombytes("RGBA", (SK, SK), bytes(s_bytes))
shade_small = shade_hi.resize((S, S), Image.Resampling.LANCZOS)
shade_small.save(os.path.join(OUTPUT_DIR, "subdial_sec_radial_shade.png"))
shade_small.save(os.path.join(BASE_DIR, "subdial_sec_radial_shade.png"))
print("Saved subdial_sec_radial_shade.png!")
