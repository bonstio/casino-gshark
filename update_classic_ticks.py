import os, math
from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/app/src/main/res/drawable"
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

S = 4
W = 450 * S
cx = cy = 225.0 * S

def draw_radial_tick(draw, deg, r_in, r_out, half_w, color):
    rad = math.radians(deg - 90.0)
    ca, sa = math.cos(rad), math.sin(rad)
    # Normal unit vector
    nx, ny = -sa, ca
    r1, r2 = r_in * S, r_out * S
    hw = half_w * S
    pts = [
        (cx + r1 * ca - hw * nx, cy + r1 * sa - hw * ny),
        (cx + r2 * ca - hw * nx, cy + r2 * sa - hw * ny),
        (cx + r2 * ca + hw * nx, cy + r2 * sa + hw * ny),
        (cx + r1 * ca + hw * nx, cy + r1 * sa + hw * ny),
    ]
    draw.polygon(pts, fill=color)

# 1. Regenerate ticks_0_classic.png (4x supersampled)
#    - 12 Major 5-minute indices: r=209.5..220.5, width=2.2px, color=(205, 218, 235, 255)
#    - 48 Minor 1-minute indices: r=213.5..220.5, width=1.5px, color=(140, 155, 175, 245)
classic_hi = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d_classic = ImageDraw.Draw(classic_hi)

# Also regenerate ticks_5_theme_minor.png so Theme Accent Indices benefits from the brighter minor ticks too
theme_minor_hi = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d_theme_minor = ImageDraw.Draw(theme_minor_hi)

for i in range(60):
    deg = i * 6.0
    if i % 5 == 0:
        draw_radial_tick(d_classic, deg, 209.5, 220.5, 1.1, (205, 218, 235, 255))
    else:
        draw_radial_tick(d_classic, deg, 213.5, 220.5, 0.75, (140, 155, 175, 245))
        draw_radial_tick(d_theme_minor, deg, 213.5, 220.5, 0.75, (140, 155, 175, 245))

classic_1x = classic_hi.resize((450, 450), Image.Resampling.LANCZOS)
classic_1x.save(os.path.join(OUTPUT_DIR, "ticks_0_classic.png"))

theme_minor_1x = theme_minor_hi.resize((450, 450), Image.Resampling.LANCZOS)
theme_minor_1x.save(os.path.join(OUTPUT_DIR, "ticks_5_theme_minor.png"))

print("Updated ticks_0_classic.png and ticks_5_theme_minor.png with 4x supersampled, brightened minor minute ticks!")
