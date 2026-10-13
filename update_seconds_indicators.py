import os, math
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "app/src/main/res/drawable")

W, H = 20, 225
K = 4
WK, HK = W * K, H * K  # 80 x 900

# Pivot is at bottom-center (10.0, 225.0) -> (40, 900) at 4x.
# Index marks span r=210..220 (major) and r=214..220 (minor); middle is r=215.5px.
# So y_center = 225.0 - 215.5 = 9.5px -> 38.0px at 4x.
cx = 10.0 * K  # 40.0
cy = 9.5 * K   # 38.0

# 1. Circle (radius = 5.0px -> 20px at 4x)
img_circle = Image.new("RGBA", (WK, HK), (0, 0, 0, 0))
dc = ImageDraw.Draw(img_circle)
r_c = 5.0 * K
dc.ellipse((cx - r_c, cy - r_c, cx + r_c, cy + r_c), fill=(255, 255, 255, 255))
circle_small = img_circle.resize((W, H), Image.Resampling.LANCZOS)
for name in ("sec_dot_white.png", "sec_dot_theme.png"):
    circle_small.save(os.path.join(OUTPUT_DIR, name))

# 2. Square (9.5x9.5px centered at (cx, cy), subtle 1.2px corner radius)
img_square = Image.new("RGBA", (WK, HK), (0, 0, 0, 0))
ds = ImageDraw.Draw(img_square)
hs = 4.75 * K
ds.rounded_rectangle((cx - hs, cy - hs, cx + hs, cy + hs), radius=int(1.2 * K), fill=(255, 255, 255, 255))
square_small = img_square.resize((W, H), Image.Resampling.LANCZOS)
for name in ("sec_square_white.png", "sec_square_theme.png"):
    square_small.save(os.path.join(OUTPUT_DIR, name))

# 3. Triangle (Equilateral pointer centered at (cx, cy), pointing radially outward)
img_tri = Image.new("RGBA", (WK, HK), (0, 0, 0, 0))
dt = ImageDraw.Draw(img_tri)
# Bounding box vertically centered at cy=38.0 from cy - 5.2*K to cy + 5.2*K
h_tri = 5.2 * K
w_tri = 5.8 * K
pts_tri = [
    (cx, cy - h_tri),          # Top apex (pointing radially outward toward bezel)
    (cx + w_tri, cy + h_tri),  # Bottom-right vertex
    (cx - w_tri, cy + h_tri),  # Bottom-left vertex
]
dt.polygon(pts_tri, fill=(255, 255, 255, 255))
tri_small = img_tri.resize((W, H), Image.Resampling.LANCZOS)
for name in ("sec_triangle_white.png", "sec_triangle_theme.png"):
    tri_small.save(os.path.join(OUTPUT_DIR, name))

print("Generated circle, square, and triangle seconds orbit indicators at r=215.5!")
