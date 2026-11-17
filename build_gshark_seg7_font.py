#!/usr/bin/env python3
"""Builds res/font/gshark_seg7.ttf ("GShark Seg7 Italic") from DSEG7 Classic Italic (SIL OFL 1.1).

Reshapes DSEG7 Classic Italic v0.46 so that it can stand in for the Digital-7 Mono Italic
layout this watch face was designed around. Proportions are expressed in a 1100-unit em
with 720-unit digits:
  * 7-segment digit 420.7 wide (measured upright), slanted 5.95 deg, 520 advance (monospaced),
    '8' ink from x=16 to x=501
  * 80-unit strokes, gaps of at least 18 units between segments
  * square colon dots (80x80) centred at (241.5, 200) and (275, 520)
  * hhea/typo ascent 1000 and descent 0. With Android's metric-based vertical centring, the
    digits sit exactly where the legacy font's (broken) metrics put them on Pixel Watch 3.
Digits 0-9 and '-' are drawn from a 7-segment construction whose joints follow the legacy
layout: 20-unit diagonal gaps, rounded outer corners owned alternately by horizontal and
vertical segments, a pointed middle bar, and a horizontal/vertical segment extending into a
corner when its neighbouring segment is unlit (2, 4, 5, 6). Other glyphs (letters, etc.) are
DSEG outlines, reshaped: each segment is thickened across its width only and then shortened
along its length so the gaps between segments stay open.

DSEG is an OFL font with the Reserved Font Name "DSEG", so this modified version is renamed;
keep licenses/DSEG-LICENSE.txt alongside it.

Usage: python3 build_gshark_seg7_font.py <DSEG7Classic-Italic.ttf> <out.ttf>
Requires fontTools (pip install fonttools).
"""
import math
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables import ttProgram

SRC_SLANT = math.tan(math.radians(5.0))
DST_SLANT_DEG = 5.95
DST_SLANT = math.tan(math.radians(DST_SLANT_DEG))
UPM = 1100
ADVANCE = 520
STROKE = 80.0
MIN_GAP = 18.0
TARGET_UPRIGHT_W = 420.7   # '8' upright width
TARGET_H = 720.0
TARGET_INK_LEFT = 16.0     # '8' slanted ink xMin
COLON_DOTS = ((241.5, 200.0), (275.0, 520.0))
DOT = 80.0

FAMILY = "GShark Seg7"
STYLE = "Italic"
VERSION = "Version 1.000; derived from DSEG7 Classic Italic v0.46"
COPYRIGHT = ('Copyright (c) 2017, keshikan (http://www.keshikan.net), with Reserved Font Name "DSEG". '
             "Modifications (GShark Seg7) Copyright (c) 2026 bonstio.")
LICENSE = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
           "This license is available with a FAQ at: https://openfontlicense.org")
LICENSE_URL = "https://openfontlicense.org"


def contours_of(glyph, glyf):
    coords, ends, flags = glyph.getCoordinates(glyf)
    out, start = [], 0
    for e in ends:
        out.append(([tuple(map(float, p)) for p in coords[start:e + 1]], list(flags[start:e + 1])))
        start = e + 1
    return out


def global_xform(pts, sx, sy):
    return [((x - y * SRC_SLANT) * sx + (y * sy) * DST_SLANT, y * sy) for x, y in pts]


def axis_frame(pts):
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts)
    syy = sum((p[1] - cy) ** 2 for p in pts)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return cx, cy, math.cos(ang), math.sin(ang)


def reshape_segment(pts, shrink):
    """Set perpendicular thickness to STROKE, then shorten by `shrink` units at each end."""
    cx, cy, ux, uy = axis_frame(pts)
    vx, vy = -uy, ux
    uv = [((x - cx) * ux + (y - cy) * uy, (x - cx) * vx + (y - cy) * vy) for x, y in pts]
    vs = [v for _, v in uv]
    us = [u for u, _ in uv]
    v0, t = (max(vs) + min(vs)) / 2, max(vs) - min(vs)
    u0, length = (max(us) + min(us)) / 2, max(us) - min(us)
    kv = STROKE / t
    ku = max(0.1, (length - 2 * shrink) / length)
    out = []
    for u, v in uv:
        u2 = u0 + (u - u0) * ku
        v2 = v0 + (v - v0) * kv
        out.append((cx + u2 * ux + v2 * vx, cy + u2 * uy + v2 * vy))
    return out


def seg_dist(a, b):
    def pd(p, q1, q2):
        (x, y), (x1, y1), (x2, y2) = p, q1, q2
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L))
        return math.hypot(x - x1 - t * dx, y - y1 - t * dy)
    m = 1e9
    for P, Q in ((a, b), (b, a)):
        for p in P:
            for i in range(len(Q)):
                m = min(m, pd(p, Q[i], Q[(i + 1) % len(Q)]))
    return m


def build_glyph(contours, sx, sy, shrink):
    out = []
    for pts, flags in contours:
        p = global_xform(pts, sx, sy)
        if all(f & 1 for f in flags) and len(p) >= 4:
            p = reshape_segment(p, shrink)
        out.append((p, flags))
    return out


def upright_bounds(contours):
    pts = [p for c, _ in contours for p in c]
    xu = [x - y * DST_SLANT for x, y in pts]
    ys = [y for _, y in pts]
    return min(xu), max(xu), min(ys), max(ys)


def solve(eight):
    sx, sy, shrink = 0.6483, 0.7054, 0.0
    for _ in range(40):
        g = build_glyph(eight, sx, sy, shrink)
        x0, x1, y0, y1 = upright_bounds(g)
        sx *= TARGET_UPRIGHT_W / (x1 - x0)
        sy *= TARGET_H / (y1 - y0)
        segs = [c for c, _ in g]
        gap = min(seg_dist(segs[i], segs[j]) for i in range(len(segs)) for j in range(i + 1, len(segs)))
        shrink += (MIN_GAP - gap) * 0.7
    g = build_glyph(eight, sx, sy, shrink)
    x0, x1, y0, y1 = upright_bounds(g)
    segs = [c for c, _ in g]
    gap = min(seg_dist(segs[i], segs[j]) for i in range(len(segs)) for j in range(i + 1, len(segs)))
    return sx, sy, shrink, (x1 - x0, y1 - y0, gap, y0)


def dot(cx, cy):
    h = DOT / 2
    return [(cx - h - h * DST_SLANT, cy - h), (cx - h + h * DST_SLANT, cy + h),
            (cx + h + h * DST_SLANT, cy + h), (cx + h - h * DST_SLANT, cy - h)]


def set_glyph(glyf, name, contours):
    """Replace a simple glyph's outline, keeping the on/off-curve flags of each point."""
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    g = Glyph()
    coords, flags, ends = [], [], []
    for pts, fl in contours:
        coords += [(round(x), round(y)) for x, y in pts]
        flags += [f & 1 for f in fl]
        ends.append(len(coords) - 1)
    g.numberOfContours = len(contours)
    g.coordinates = GlyphCoordinates(coords)
    g.flags = bytearray(flags)
    g.endPtsOfContours = ends
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    g.recalcBounds(glyf)
    glyf[name] = g


# --- 7-segment digits -------------------------------------------------------------------
# Upright coordinates (before the 5.95 deg shear): cell x 10.6..431.4, y 0..720, 80-unit strokes.
L, R, T = 10.6, 431.4, 720.0
ON, OFF = 1, 0


def _segment(name, ext=False):
    """Returns (points, flags) for segment a-g. `ext` lengthens the end at an unlit neighbour."""
    e = 30.0 if ext else 0.0
    if name == "a":  # top: owns the rounded top-left corner, diagonal cut at top-right
        pts = [(R - 100 + e, T - 80), (L + 81.7, T - 80), (L + 1.6, T - 50), (L + 11.4, T - 10),
               (L + 51.4, T), (R - 70.4 + e, T)]
        fl = [ON, ON, ON, OFF, ON, ON]
    elif name == "b":  # upper right: owns the rounded top-right corner
        pts = [(R - 80.2, 430), (R - 80.1, T - 80), (R - 50.4, T), (R - 10.4, T - 10), (R - 0.2, T - 50),
               (R, 390), (R - 21, 370)]
        fl = [ON, ON, ON, OFF, ON, ON, ON]
    elif name == "c":  # lower right: owns the rounded bottom-right corner
        pts = [(R - 20.9, 350), (R - 0.8, 330), (R - 0.6, 50), (R - 10.4, 10), (R - 50.4, 0), (R - 80.7, 80),
               (R - 80.6, 290)]
        fl = [ON, ON, ON, OFF, ON, ON, ON]
    elif name == "d":  # bottom: owns the rounded bottom-left corner, diagonal cut at bottom-right
        pts = [(R - 70.4 + e, 0), (L + 50.4, 0), (L + 10.4, 10), (L + 0.2, 50), (L + 80.1, 80), (R - 100.7 + e, 80)]
        fl = [ON, ON, OFF, ON, ON, ON]
    elif name == "e":  # lower left: diagonal cut at the bottom, pointed at the middle
        pts = [(L + 0.1, 70), (L, 330), (L + 19.9, 350), (L + 80.2, 290), (L + 80, 100)]
        fl = [ON] * 5
    elif name == "f":  # upper left: diagonal cut at the top, pointed at the middle
        top_in, top_out = (650.0, 680.0) if ext else (620.0, 650.0)
        pts = [(L + 80.7, top_in), (L + 80.6, 430), (L + 19.8, 370), (L + 0.8, 390), (L + 0.5, top_out)]
        fl = [ON] * 5
    elif name == "g":  # middle: pointed both ends
        pts = [(R - 80.1, 400), (R - 40.9, 360), (R - 80.8, 320), (L + 80, 320), (L + 39.9, 360), (L + 80.7, 400)]
        fl = [ON] * 6
    else:
        raise ValueError(name)
    return [(x + y * DST_SLANT, y) for x, y in pts], fl


# Lit segments per glyph; uppercase = extended into the corner left free by an unlit neighbour.
SEVEN_SEG = {
    "zero": "abcdef", "one": "bc", "two": "abgeD", "three": "abgcd", "four": "Fgbc",
    "five": "Afgcd", "six": "Afgedc", "seven": "abcf", "eight": "abcdefg", "nine": "abcdfg",
    "hyphen": "g",
}


def seven_segment_glyph(spec):
    return [_segment(ch.lower(), ext=ch.isupper()) for ch in spec]


def main(src, dst):
    f = TTFont(src)
    glyf = f["glyf"]
    cmap = f.getBestCmap()
    eight = contours_of(glyf[cmap[ord("8")]], glyf)
    sx, sy, shrink, stats = solve(eight)
    print("sx=%.4f sy=%.4f shrink=%.2f -> upright w %.1f h %.1f min gap %.1f yMin %.1f" % ((sx, sy, shrink) + stats))

    # x offset so the '8' ink starts at TARGET_INK_LEFT
    g8 = build_glyph(eight, sx, sy, shrink)
    dx = TARGET_INK_LEFT - min(p[0] for c, _ in g8 for p in c)
    dy = -min(p[1] for c, _ in g8 for p in c)

    # Scale font units: source upm 1000 -> 1100 is already folded into sx/sy (targets are in 1100 units).
    for name in f.getGlyphOrder():
        gl = glyf[name]
        if name == "colon":
            set_glyph(glyf, name, [(dot(*c), [1, 1, 1, 1]) for c in COLON_DOTS])
            continue
        if name in SEVEN_SEG:
            set_glyph(glyf, name, seven_segment_glyph(SEVEN_SEG[name]))
            continue
        if gl.numberOfContours <= 0:
            continue
        cs = build_glyph(contours_of(gl, glyf), sx, sy, shrink)
        cs = [([(x + dx, y + dy) for x, y in c], fl) for c, fl in cs]
        set_glyph(glyf, name, cs)

    hmtx = f["hmtx"]
    for name in f.getGlyphOrder():
        gl = glyf[name]
        gl.recalcBounds(glyf) if gl.numberOfContours else None
        lsb = gl.xMin if gl.numberOfContours else 0
        adv = 0 if name in (".null", ".notdef") and hmtx[name][0] == 0 else ADVANCE
        hmtx[name] = (adv, lsb)

    head = f["head"]
    head.unitsPerEm = UPM
    head.fontRevision = 1.0
    head.macStyle = 0x02
    for t in ("cvt ", "fpgm", "prep", "FFTM", "hdmx", "LTSH", "VDMX"):
        if t in f:
            del f[t]
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    f["gasp"] = gasp

    hhea = f["hhea"]
    hhea.ascent, hhea.descent, hhea.lineGap = 1000, 0, 0
    hhea.caretSlopeRise, hhea.caretSlopeRun = 1000, round(1000 * DST_SLANT)
    os2 = f["OS/2"]
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = 1000, 0, 0
    ymin = min((glyf[n].yMin for n in f.getGlyphOrder() if glyf[n].numberOfContours), default=0)
    os2.usWinAscent, os2.usWinDescent = 1000, max(0, -ymin)
    os2.fsSelection = (1 << 0) | (1 << 7)  # ITALIC | USE_TYPO_METRICS
    os2.xAvgCharWidth = ADVANCE
    os2.panose.bProportion = 9  # monospaced
    os2.achVendID = "NONE"
    capH = round(TARGET_H)
    os2.sCapHeight = os2.sxHeight = capH
    post = f["post"]
    post.italicAngle = -DST_SLANT_DEG
    post.isFixedPitch = 1

    name = f["name"]
    name.names = []
    ps = "GSharkSeg7-Italic"
    for nid, s in ((0, COPYRIGHT), (1, FAMILY), (2, STYLE), (3, "1.000;NONE;" + ps), (4, FAMILY + " " + STYLE),
                   (5, VERSION), (6, ps), (13, LICENSE), (14, LICENSE_URL)):
        name.setName(s, nid, 3, 1, 0x409)
        name.setName(s, nid, 1, 0, 0)

    f.save(dst)
    print("wrote", dst)


if __name__ == "__main__":
    main(*sys.argv[1:3])
