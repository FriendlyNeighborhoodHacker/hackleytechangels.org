#!/usr/bin/env python3
"""Build the Hackley Improv Club club-fair poster sheets.

Outputs (in this directory):
  club-fair-poster.pdf   6 letter-size pages, one mounting sheet per page
  assembly-guide.pdf     1 landscape letter page with the board layout + steps
  board-preview.png      composite of the six trimmed sheets on the board

Run:  python3 make_poster.py     (needs: pip install reportlab qrcode pillow)
"""
import os
import subprocess
import sys

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import qrcode

HERE = os.path.dirname(os.path.abspath(__file__))
IN = 72.0  # points per inch

# ---------------------------------------------------------------- brand (sampled from the club logo)
NAVY = HexColor("#041646")
YELLOW = HexColor("#FEC021")
BLUE = HexColor("#0FB9ED")
PINK = HexColor("#FC3A77")
ORANGE = HexColor("#FE8E11")
GREEN = HexColor("#ADCB1B")
PURPLE = HexColor("#7F55B9")
INK = HexColor("#141a2e")
INK_SOFT = HexColor("#4f5670")
TINT = HexColor("#f3f6fb")
LINE = HexColor("#e2e6ef")
WHITE = white

QR_URL = "https://www.hackleyclubz.org/clubs/qr.php?t=63fe8297836739dd373955847912315e"
MISSION = "we make stuff up."
PLAN = "\u2026 and we perform!"
DESCRIPTION = "If you are funny, join improv club!! We have fun!"
MEETS = "DAY 6 \u00b7 LUNCH"
WHERE = "the chapel"

# ---------------------------------------------------------------- fonts
FONT_DIR = os.path.join(HERE, "fonts")
for name, file in [("Poppins-Bold", "Poppins-Bold.ttf"),
                   ("Poppins-SemiBold", "Poppins-SemiBold.ttf"),
                   ("Poppins-Medium", "Poppins-Medium.ttf"),
                   ("Poppins-Regular", "Poppins-Regular.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, file)))
try:
    pdfmetrics.registerFont(TTFont("Playfair-Italic", os.path.join(FONT_DIR, "PlayfairDisplay-Italic.ttf")))
    SERIF_ITALIC = "Playfair-Italic"
except Exception:
    SERIF_ITALIC = "Poppins-Medium"

BOLD, SEMI, MED, REG = "Poppins-Bold", "Poppins-SemiBold", "Poppins-Medium", "Poppins-Regular"

# ---------------------------------------------------------------- geometry
BLEED = 0.1 * IN
WING_TRIM = (6.6 * IN, 10.2 * IN)      # portrait sheet, trimmed to width
CENTER_TRIM = (10.4 * IN, 7.9 * IN)    # landscape sheet


def sw(text, font, size):
    return pdfmetrics.stringWidth(text, font, size)


def fit_size(text, font, max_w, max_size, min_size=8):
    """Largest font size (<= max_size) at which text fits in max_w."""
    size = max_size
    while size > min_size and sw(text, font, size) > max_w:
        size -= 0.5
    return size


def fit_lines(lines, font, max_w, max_size):
    return min(fit_size(t, font, max_w, max_size) for t in lines)


def wrap_fit(text, font, max_w, max_h, max_size, leading=1.18, min_size=18):
    """Largest size (<= max_size) whose wrapped block fits in max_w x max_h."""
    size = max_size
    while size > min_size:
        lines = simpleSplit(text, font, size, max_w)
        if len(lines) * size * leading <= max_h:
            return size, lines
        size -= 1
    return size, simpleSplit(text, font, size, max_w)


def tracked(c, x, y, text, font, size, tracking, color, align="left"):
    """Draw text with letter-spacing. align: left | center."""
    width = sw(text, font, size) + tracking * (len(text) - 1)
    if align == "center":
        x = x - width / 2
    c.saveState()
    t = c.beginText(x, y)
    t.setFont(font, size)
    t.setCharSpace(tracking)
    t.setFillColor(color)
    t.textOut(text)
    t.setCharSpace(0)  # Tc persists in the PDF graphics state; reset it
    c.drawText(t)
    c.restoreState()
    return width


def centered_lines(c, cx, top_y, lines, font, size, color, leading=1.02):
    """Draw lines centered on cx starting with the first baseline at top_y - size*0.75.
    Returns the y below the block."""
    c.setFont(font, size)
    c.setFillColor(color)
    y = top_y - size * 0.78
    for ln in lines:
        c.drawCentredString(cx, y, ln)
        y -= size * leading
    return y + size * leading - size * 0.3


def left_lines(c, x, top_y, lines, font, size, color, leading=1.15):
    c.setFont(font, size)
    c.setFillColor(color)
    y = top_y - size * 0.78
    for ln in lines:
        c.drawString(x, y, ln)
        y -= size * leading
    return y + size * leading - size * 0.3


# ---------------------------------------------------------------- sheet frame
def begin_sheet(c, n, label, orient, bg):
    """Start a page; paint the bleed-extended background; draw trim marks.
    Returns the trim rectangle (x0, y0, w, h)."""
    if orient == "portrait":
        page = letter
        w, h = WING_TRIM
    else:
        page = landscape(letter)
        w, h = CENTER_TRIM
    c.setPageSize(page)
    pw, ph = page
    x0, y0 = (pw - w) / 2, (ph - h) / 2

    # background with bleed
    c.setFillColor(bg)
    c.rect(x0 - BLEED, y0 - BLEED, w + 2 * BLEED, h + 2 * BLEED, stroke=0, fill=1)

    # corner trim marks, outside the bleed
    c.setStrokeColor(HexColor("#888888"))
    c.setLineWidth(0.4)
    gap, ln = BLEED + 2, 10
    for (cx, sx) in ((x0, -1), (x0 + w, 1)):
        for (cy, sy) in ((y0, -1), (y0 + h, 1)):
            c.line(cx + sx * gap, cy, cx + sx * (gap + ln), cy)
            c.line(cx, cy + sy * gap, cx, cy + sy * (gap + ln))

    # tiny label inside the bottom bleed strip (trimmed away), plus a
    # second copy in the outer margin on portrait pages where there is room
    dark_bg = bg in (NAVY, BLUE, PINK, PURPLE)
    c.setFillColor(Color(1, 1, 1, 0.8) if dark_bg else HexColor("#8a8a8a"))
    c.setFont(REG, 5.5)
    c.drawCentredString(x0 + w / 2, y0 - BLEED + 1.5, f"Sheet {n} — {label}")
    if orient == "portrait":
        c.setFillColor(HexColor("#8a8a8a"))
        c.setFont(REG, 7)
        c.drawCentredString(x0 + w / 2, y0 - BLEED - 14, f"Sheet {n} — {label}   ·   trim on the marks to 6.6 in × 10.2 in")
    return x0, y0, w, h


# ---------------------------------------------------------------- drawing helpers
def draw_qr(c, x, y, size, fg=INK, bg=WHITE):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0)
    qr.add_data(QR_URL)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    cell = size / n
    c.setFillColor(bg)
    c.rect(x, y, size, size, stroke=0, fill=1)
    c.setFillColor(fg)
    for r in range(n):
        for col in range(n):
            if m[r][col]:
                # +0.15 overlap hides hairline gaps between cells in some viewers
                c.rect(x + col * cell, y + size - (r + 1) * cell, cell + 0.15, cell + 0.15, stroke=0, fill=1)


def draw_logo(c, cx, cy, diameter):
    """Club logo (masks in a navy circle) clipped to a circle."""
    c.saveState()
    p = c.beginPath()
    p.circle(cx, cy, diameter / 2)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(os.path.join(HERE, "assets", "logo.jpg"), cx - diameter / 2, cy - diameter / 2, diameter, diameter)
    c.restoreState()


def draw_hero(c, x, y, w, h, radius):
    """Hero photo (3:1) cropped to fill a rounded rectangle."""
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    img_w, img_h = 1536, 512
    scale = max(w / img_w, h / img_h)
    dw, dh = img_w * scale, img_h * scale
    c.drawImage(os.path.join(HERE, "assets", "hero.png"), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
    c.restoreState()


def confetti(c, x0, y0, w, h, seed=3, n=14, alpha=1.0):
    """Scatter of logo-colored teardrop/dot shapes, kept near the card edges."""
    import random
    rnd = random.Random(seed)
    cols = [PINK, ORANGE, GREEN, PURPLE, BLUE, YELLOW]
    for i in range(n):
        col = cols[i % len(cols)]
        c.setFillColor(Color(col.red, col.green, col.blue, alpha))
        # keep confetti in a border band so it never sits under text
        side = rnd.choice("tblr")
        if side == "t":
            x, y = x0 + rnd.uniform(0, w), y0 + h - rnd.uniform(0.05, 0.45) * IN
        elif side == "b":
            x, y = x0 + rnd.uniform(0, w), y0 + rnd.uniform(0.05, 0.45) * IN
        elif side == "l":
            x, y = x0 + rnd.uniform(0.05, 0.4) * IN, y0 + rnd.uniform(0, h)
        else:
            x, y = x0 + w - rnd.uniform(0.05, 0.4) * IN, y0 + rnd.uniform(0, h)
        r = rnd.uniform(4, 9)
        if rnd.random() < 0.5:
            c.circle(x, y, r, stroke=0, fill=1)
        else:
            c.saveState()
            c.translate(x, y)
            c.rotate(rnd.uniform(0, 360))
            p = c.beginPath()
            p.moveTo(0, r * 2.6)
            p.curveTo(r * 1.1, r * 0.6, r * 1.1, -r * 0.8, 0, -r * 0.8)
            p.curveTo(-r * 1.1, -r * 0.8, -r * 1.1, r * 0.6, 0, r * 2.6)
            c.drawPath(p, stroke=0, fill=1)
            c.restoreState()


def icon_bubble(c, cx, cy, s, color):
    """Speech bubble with a spark: 'we make stuff up'."""
    c.setFillColor(color)
    w, h = s, s * 0.72
    c.roundRect(cx - w / 2, cy - h / 2 + s * 0.08, w, h, s * 0.18, stroke=0, fill=1)
    p = c.beginPath()
    p.moveTo(cx - s * 0.22, cy - h / 2 + s * 0.09)
    p.lineTo(cx - s * 0.32, cy - h / 2 - s * 0.18)
    p.lineTo(cx - s * 0.02, cy - h / 2 + s * 0.09)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # spark (four-point star) cut out in white
    c.setFillColor(WHITE)
    sx, sy, r = cx, cy + s * 0.08, s * 0.2
    p = c.beginPath()
    p.moveTo(sx, sy + r)
    p.curveTo(sx + r * 0.1, sy + r * 0.1, sx + r * 0.1, sy + r * 0.1, sx + r, sy)
    p.curveTo(sx + r * 0.1, sy - r * 0.1, sx + r * 0.1, sy - r * 0.1, sx, sy - r)
    p.curveTo(sx - r * 0.1, sy - r * 0.1, sx - r * 0.1, sy - r * 0.1, sx - r, sy)
    p.curveTo(sx - r * 0.1, sy + r * 0.1, sx - r * 0.1, sy + r * 0.1, sx, sy + r)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def icon_stage(c, cx, cy, s, color):
    """Spotlight cone over a stage line: 'we perform'."""
    c.setFillColor(color)
    # lamp
    c.roundRect(cx - s * 0.13, cy + s * 0.32, s * 0.26, s * 0.16, s * 0.05, stroke=0, fill=1)
    # cone (lighter)
    c.setFillColor(Color(color.red, color.green, color.blue, 0.35))
    p = c.beginPath()
    p.moveTo(cx - s * 0.10, cy + s * 0.33)
    p.lineTo(cx + s * 0.10, cy + s * 0.33)
    p.lineTo(cx + s * 0.42, cy - s * 0.28)
    p.lineTo(cx - s * 0.42, cy - s * 0.28)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # performer
    c.setFillColor(color)
    c.circle(cx, cy + s * 0.02, s * 0.09, stroke=0, fill=1)
    c.wedge(cx - s * 0.16, cy - s * 0.30, cx + s * 0.16, cy - s * 0.04, 0, 180, stroke=0, fill=1)
    # stage floor
    c.roundRect(cx - s * 0.5, cy - s * 0.42, s, s * 0.09, s * 0.03, stroke=0, fill=1)


def masks_small(c, cx, cy, s):
    """Tiny two-mask motif drawn from the logo image."""
    draw_logo(c, cx, cy, s)


def arrow_left(c, x_tip, y, length, color, weight):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(weight)
    c.setLineCap(1)
    c.line(x_tip + weight * 1.2, y, x_tip + length, y)
    p = c.beginPath()
    head = weight * 2.6
    p.moveTo(x_tip, y)
    p.lineTo(x_tip + head * 1.15, y + head)
    p.lineTo(x_tip + head * 1.15, y - head)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


# ---------------------------------------------------------------- sheets
def sheet_1_title(c):
    x0, y0, w, h = begin_sheet(c, 1, "center top", "landscape", WHITE)
    pad = 0.35 * IN
    cx = x0 + w / 2
    inner_w = w - 2 * pad
    bar = 0.16 * IN
    c.setFillColor(YELLOW)
    c.rect(x0 - BLEED, y0 + h - bar, w + 2 * BLEED, bar + BLEED, stroke=0, fill=1)
    confetti(c, x0, y0, w, h - bar, seed=11, n=16)

    logo_d = 2.9 * IN
    big = fit_size("IMPROV CLUB", BOLD, inner_w, 200)
    small = big * 0.42
    tlines = [MISSION, PLAN]
    tsize = fit_lines(tlines, SERIF_ITALIC, inner_w * 0.92, 50)
    total = logo_d + 0.2 * IN + small * 0.95 + big * 0.98 + 0.08 * IN + len(tlines) * tsize * 1.15
    avail_top = y0 + h - bar - pad
    avail = avail_top - (y0 + pad)
    top = avail_top - max(0, (avail - total) / 2)

    draw_logo(c, cx, top - logo_d / 2, logo_d)
    y = top - logo_d - 0.2 * IN
    tracked(c, cx, y - small * 0.78, "HACKLEY", BOLD, small, small * 0.14, BLUE, align="center")
    y -= small * 0.95
    c.setFont(BOLD, big)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, y - big * 0.78, "IMPROV CLUB")
    y -= big * 0.98 + 0.08 * IN
    centered_lines(c, cx, y, tlines, SERIF_ITALIC, tsize, INK_SOFT, leading=1.15)


def sheet_2_join(c):
    x0, y0, w, h = begin_sheet(c, 2, "center bottom", "landscape", NAVY)
    pad = 0.4 * IN
    qr_size = 4.8 * IN
    panel = qr_size + 0.4 * IN
    px = x0 + pad
    py = y0 + (h - panel) / 2
    c.setFillColor(WHITE)
    c.roundRect(px, py, panel, panel, 0.25 * IN, stroke=0, fill=1)
    draw_qr(c, px + 0.2 * IN, py + 0.2 * IN, qr_size, fg=NAVY)

    col_x = px + panel + 0.35 * IN
    col_w = x0 + w - pad - col_x
    lines = ["SCAN", "TO", "JOIN"]
    size = fit_lines(lines, BOLD, col_w, 140)
    block_h = size * 0.78 + size * 0.98 * 2
    msize = fit_size(MEETS, BOLD, col_w, 40)
    extra = 0.22 * IN + 26 * 0.78 + 0.12 * IN + msize * 0.78 + 0.1 * IN + 22 + 0.28 * IN + 20 * 1.15 * 2
    total = block_h + extra
    y = y0 + h / 2 + total / 2
    c.setFont(BOLD, size)
    c.setFillColor(WHITE)
    for ln in lines:
        c.drawCentredString(col_x + col_w / 2, y - size * 0.78, ln)
        y -= size * 0.98
    y -= 0.22 * IN
    c.setFont(MED, 26)
    c.setFillColor(Color(1, 1, 1, 0.85))
    c.drawCentredString(col_x + col_w / 2, y - 26 * 0.78, "We meet")
    y -= 26 * 0.78 + 0.12 * IN
    c.setFont(BOLD, msize)
    c.setFillColor(YELLOW)
    c.drawCentredString(col_x + col_w / 2, y - msize * 0.78, MEETS)
    y -= msize * 0.78 + 0.1 * IN
    c.setFont(SEMI, 22)
    c.setFillColor(BLUE)
    c.drawCentredString(col_x + col_w / 2, y - 22 * 0.78, "in " + WHERE)
    y -= 22 * 0.78 + 0.28 * IN
    c.setFont(MED, 20)
    c.setFillColor(Color(1, 1, 1, 0.7))
    for ln in ["Opens in", "Hackley Clubz"]:
        c.drawCentredString(col_x + col_w / 2, y - 20 * 0.78, ln)
        y -= 20 * 1.15


def sheet_3_mission(c):
    x0, y0, w, h = begin_sheet(c, 3, "left wing top", "portrait", YELLOW)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    y = y0 + h - pad
    tracked(c, x0 + pad, y - 24 * 0.78, "WHO WE ARE", BOLD, 24, 3, NAVY)
    y -= 24 + 0.16 * IN
    c.setFillColor(NAVY)
    c.rect(x0 + pad, y, 1.1 * IN, 5, stroke=0, fill=1)
    y -= 0.4 * IN

    # the mission, huge, exactly as the club wrote it
    lines = ["we make", "stuff up."]
    size = fit_lines(lines, BOLD, inner_w, 110)
    y = left_lines(c, x0 + pad, y, lines, BOLD, size, NAVY, leading=0.98)
    y -= 0.3 * IN
    plines = ["\u2026 and we", "perform!"]
    psize = fit_lines(plines, MED, inner_w, size * 0.72)
    y = left_lines(c, x0 + pad, y, plines, MED, psize, NAVY, leading=1.0)

    # two icons at the bottom
    icons_h = 2.7 * IN
    icon_y = y0 + pad + icons_h - 0.05 * IN
    for (col_cx, draw, label) in ((x0 + w * 0.29, icon_bubble, "make it up"),
                                  (x0 + w * 0.71, icon_stage, "perform it")):
        r = 0.86 * IN
        cy = icon_y - r
        c.setFillColor(WHITE)
        c.circle(col_cx, cy, r, stroke=0, fill=1)
        draw(c, col_cx, cy, r * 1.2, NAVY)
        c.setFont(SEMI, 22)
        c.setFillColor(NAVY)
        c.drawCentredString(col_cx, cy - r - 0.42 * IN, label)


def sheet_4_howitworks(c):
    x0, y0, w, h = begin_sheet(c, 4, "left wing bottom", "portrait", WHITE)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    y = y0 + h - pad
    tracked(c, x0 + pad, y - 24 * 0.78, "NO SCRIPT", BOLD, 24, 3, PINK)
    y -= 24 + 0.12 * IN
    lines = ["HOW A", "SCENE", "HAPPENS"]
    size = fit_lines(lines, BOLD, inner_w, 84)
    y = left_lines(c, x0 + pad, y, lines, BOLD, size, NAVY, leading=0.98)
    y -= 0.3 * IN

    steps = ["Get a one-word suggestion",
             "Say \u201cyes, and\u2026\u201d",
             "Build the scene together",
             "Commit to the bit",
             "Take a bow"]
    cols = [PINK, ORANGE, GREEN, BLUE, PURPLE]
    avail = y - (y0 + pad)
    row = min(0.88 * IN, avail / len(steps))
    r = 0.25 * IN
    text_x = x0 + pad + 2 * r + 0.22 * IN
    text_w = x0 + w - pad - text_x
    for i, step in enumerate(steps, 1):
        cy = y - row / 2
        c.setFillColor(cols[i - 1])
        c.circle(x0 + pad + r, cy, r, stroke=0, fill=1)
        c.setFillColor(WHITE if cols[i - 1] not in (GREEN, YELLOW) else NAVY)
        c.setFont(BOLD, 22)
        c.drawCentredString(x0 + pad + r, cy - 22 * 0.36, str(i))
        tsize, tlines = wrap_fit(step, SEMI, text_w, row - 6, 27, leading=1.1, min_size=20)
        block = len(tlines) * tsize * 1.1
        left_lines(c, text_x, cy + block / 2, tlines, SEMI, tsize, NAVY, leading=1.1)
        if i < len(steps):
            c.setStrokeColor(LINE)
            c.setLineWidth(1)
            c.line(text_x, y - row, x0 + w - pad, y - row)
        y -= row


def sheet_5_perform(c):
    x0, y0, w, h = begin_sheet(c, 5, "right wing top", "portrait", WHITE)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    cx = x0 + w / 2
    y = y0 + h - pad
    lines = ["\u2026AND WE", "PERFORM!"]
    size = fit_lines(lines, BOLD, inner_w, 90)
    y = centered_lines(c, cx, y, lines, BOLD, size, NAVY, leading=1.0)
    y -= 0.25 * IN

    # hero photo, cropped tall-ish so faces read from a distance
    foot_h = 1.5 * IN
    photo_h = y - (y0 + pad) - foot_h - 0.3 * IN
    draw_hero(c, x0 + pad, y - photo_h, inner_w, photo_h, 0.25 * IN)
    y -= photo_h + 0.3 * IN

    sub = "Come see a show. Better yet, be in one."
    ssize, slines = wrap_fit(sub, SEMI, inner_w, foot_h, 30, leading=1.2, min_size=22)
    centered_lines(c, cx, y, slines, SEMI, ssize, PINK, leading=1.2)


def sheet_6_cta(c):
    x0, y0, w, h = begin_sheet(c, 6, "right wing bottom", "portrait", BLUE)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    cx = x0 + w / 2
    y = y0 + h - pad - 0.05 * IN
    hook = ["If you are", "funny\u2026"]
    hsize = fit_lines(hook, MED, inner_w, 50)
    y = centered_lines(c, cx, y, hook, MED, hsize, WHITE, leading=1.05)
    y -= 0.16 * IN
    pay = ["join", "improv", "club!!"]
    psize = fit_lines(pay, BOLD, inner_w, 100)
    y = centered_lines(c, cx, y, pay, BOLD, psize, NAVY, leading=0.95)
    y -= 0.22 * IN
    c.setFont(SEMI, 34)
    c.setFillColor(WHITE)
    c.drawCentredString(cx, y - 34 * 0.78, "We have fun!")
    y -= 34 + 0.3 * IN

    msize = fit_size(MEETS, BOLD, inner_w - 1.2 * IN, 34)
    pw_ = sw(MEETS, BOLD, msize) + 0.8 * IN
    ph_ = msize + 0.42 * IN
    c.setFillColor(WHITE)
    c.roundRect(cx - pw_ / 2, y - ph_, pw_, ph_, ph_ / 2, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont(BOLD, msize)
    c.drawCentredString(cx, y - ph_ + (ph_ - msize * 0.72) / 2, MEETS)
    y -= ph_ + 0.12 * IN
    c.setFont(SEMI, 22)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, y - 22 * 0.78, "in " + WHERE)
    y -= 22 + 0.3 * IN

    txt = "scan the code to join"
    tsize = 26
    arrow_len = 0.75 * IN
    total = arrow_len + 0.2 * IN + sw(txt, SEMI, tsize)
    if total > inner_w:
        tsize = fit_size(txt, SEMI, inner_w - arrow_len - 0.2 * IN, tsize)
        total = arrow_len + 0.2 * IN + sw(txt, SEMI, tsize)
    ax = cx - total / 2
    arrow_left(c, ax, y - tsize * 0.35, arrow_len, WHITE, 6)
    c.setFont(SEMI, tsize)
    c.setFillColor(WHITE)
    c.drawString(ax + arrow_len + 0.2 * IN, y - tsize * 0.72, txt)


# ---------------------------------------------------------------- assembly guide
BOARD_W, BOARD_H = 28.0, 22.0
WING = 18 / 2.54          # 7.087 in
CENTER_W = BOARD_W - 2 * WING
WING_X_OFF = (WING - 6.6) / 2
CENTER_X_OFF = (CENTER_W - 10.4) / 2
SHEETS = [  # (n, label, panel x-origin, x offset in panel, y from top, w, h, color)
    (1, "Title", WING, CENTER_X_OFF, 2.7, 10.4, 7.9, WHITE),
    (2, "Scan to join", WING, CENTER_X_OFF, 2.7 + 7.9 + 0.8, 10.4, 7.9, NAVY),
    (3, "Who we are", 0, WING_X_OFF, 0.5, 6.6, 10.2, YELLOW),
    (4, "How it works", 0, WING_X_OFF, 0.5 + 10.2 + 0.6, 6.6, 10.2, WHITE),
    (5, "And we perform", WING + CENTER_W, WING_X_OFF, 0.5, 6.6, 10.2, WHITE),
    (6, "Join improv club", WING + CENTER_W, WING_X_OFF, 0.5 + 10.2 + 0.6, 6.6, 10.2, BLUE),
]


def assembly_guide(path):
    c = canvas.Canvas(path, pagesize=landscape(letter))
    c.setTitle("Hackley Improv Club club fair poster - assembly guide")
    pw, ph = landscape(letter)
    margin = 0.45 * IN
    c.setFont(BOLD, 20)
    c.setFillColor(NAVY)
    c.drawString(margin, ph - margin - 14, "Hackley Improv Club — Club Fair Poster Assembly")
    c.setFont(REG, 10.5)
    c.setFillColor(INK_SOFT)
    c.drawString(margin, ph - margin - 32,
                 "22 in × 28 in posterboard used landscape (28 wide × 22 tall). All measurements in inches unless noted.")

    # --- diagram
    scale = 0.205 * IN  # points per board inch
    bx = margin + 0.55 * IN
    by = ph - margin - 0.75 * IN - BOARD_H * scale
    bw, bh = BOARD_W * scale, BOARD_H * scale

    def X(v):
        return bx + v * scale

    def Y(v_from_top):
        return by + bh - v_from_top * scale

    c.setFillColor(HexColor("#f2f2f2"))
    c.setStrokeColor(INK)
    c.setLineWidth(1.2)
    c.rect(bx, by, bw, bh, stroke=1, fill=1)
    # fold lines
    c.setStrokeColor(PINK)
    c.setLineWidth(1)
    c.setDash(5, 3)
    for fx in (WING, WING + CENTER_W):
        c.line(X(fx), by, X(fx), by + bh)
    c.setDash()
    c.setFont(SEMI, 8)
    c.setFillColor(PINK)
    c.drawCentredString(X(WING), by + bh + 4, "fold  (18 cm = 7.09 in from edge)")
    c.drawCentredString(X(WING + CENTER_W), by + bh + 4, "fold  (18 cm = 7.09 in from edge)")

    # sheets
    for n, label, px, xo, yt, w_, h_, col in SHEETS:
        x = X(px + xo)
        y = Y(yt + h_)
        c.setFillColor(col)
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.rect(x, y, w_ * scale, h_ * scale, stroke=1, fill=1)
        dark = col in (NAVY, BLUE)
        c.setFillColor(WHITE if dark else NAVY)
        c.setFont(BOLD, 15)
        c.drawCentredString(x + w_ * scale / 2, y + h_ * scale / 2 + 2, str(n))
        c.setFont(REG, 7.5)
        c.drawCentredString(x + w_ * scale / 2, y + h_ * scale / 2 - 10, label)
        c.setFont(REG, 6.5)
        c.drawCentredString(x + w_ * scale / 2, y + 4, f"{w_} × {h_}")

    # dimension annotations
    c.setFont(REG, 7)
    c.setFillColor(INK)
    c.setStrokeColor(INK_SOFT)
    c.setLineWidth(0.5)

    def dim_v(xv, y_top, y_bot, text, side=1):
        xx = X(xv)
        c.line(xx, Y(y_top), xx, Y(y_bot))
        c.line(xx - 2, Y(y_top), xx + 2, Y(y_top))
        c.line(xx - 2, Y(y_bot), xx + 2, Y(y_bot))
        c.saveState()
        c.translate(xx + (5 if side > 0 else -5), (Y(y_top) + Y(y_bot)) / 2)
        c.rotate(90)
        c.drawCentredString(0, -2.5 if side > 0 else 2.5, text)
        c.restoreState()

    def dim_h(y_from_top, x1, x2, text):
        yy = Y(y_from_top)
        c.line(X(x1), yy, X(x2), yy)
        c.line(X(x1), yy - 2, X(x1), yy + 2)
        c.line(X(x2), yy - 2, X(x2), yy + 2)
        c.drawCentredString((X(x1) + X(x2)) / 2, yy + 3, text)

    # wing vertical: 0.5 / 10.2 / 0.6 / 10.2 / 0.5 (left of board)
    lx = -1.1
    dim_v(lx, 0, 0.5, "0.5")
    dim_v(lx, 0.5, 10.7, "10.2")
    dim_v(lx, 10.7, 11.3, "0.6")
    dim_v(lx, 11.3, 21.5, "10.2")
    dim_v(lx, 21.5, 22, "0.5")
    # center vertical: 2.7 / 7.9 / 0.8 / 7.9 / 2.7 (right of board)
    rx = BOARD_W + 1.1
    dim_v(rx, 0, 2.7, "2.7", -1)
    dim_v(rx, 2.7, 10.6, "7.9", -1)
    dim_v(rx, 10.6, 11.4, "0.8", -1)
    dim_v(rx, 11.4, 19.3, "7.9", -1)
    dim_v(rx, 19.3, 22, "2.7", -1)
    # horizontal below board
    dim_h(23.0, 0, WING, "7.09 (18 cm)")
    dim_h(23.0, WING, WING + CENTER_W, "13.82")
    dim_h(23.0, WING + CENTER_W, BOARD_W, "7.09 (18 cm)")
    dim_h(24.2, 0, WING_X_OFF, "0.25")
    dim_h(24.2, WING_X_OFF, WING - WING_X_OFF, "6.6")
    dim_h(24.2, WING + 0, WING + CENTER_X_OFF, "1.71")
    dim_h(24.2, WING + CENTER_X_OFF, WING + CENTER_X_OFF + 10.4, "10.4")
    dim_h(24.2, WING + CENTER_X_OFF + 10.4, WING + CENTER_W, "1.71")
    dim_h(24.2, WING + CENTER_W + WING_X_OFF, BOARD_W - WING_X_OFF, "6.6")
    dim_h(24.2, BOARD_W - WING_X_OFF, BOARD_W, "0.25")

    # --- right column: steps + table
    col_x = X(BOARD_W) + 0.85 * IN
    col_w = pw - margin - col_x
    y = ph - margin - 0.75 * IN
    c.setFont(BOLD, 12)
    c.setFillColor(NAVY)
    c.drawString(col_x, y, "Steps")
    y -= 16
    steps = [
        "Print club-fair-poster.pdf on letter paper, color, at 100% / “Actual size” (turn off “fit to page”).",
        "Cut each sheet on the corner trim marks. Wing sheets become 6.6 × 10.2 in; center sheets 10.4 × 7.9 in.",
        "Fold each wing 18 cm (7.09 in) in from the short edges so the board stands on a table.",
        "Wings: 0.5 in from the top, 0.6 in gap, 0.5 in at the bottom; center each sheet across the wing (about 0.25 in each side).",
        "Center panel: stack the two landscape sheets with a 0.8 in gap; leave about 2.7 in above and below; 1.71 in each side.",
        "Glue-stick or double-stick tape near the corners. Keep every sheet inside one panel so nothing crosses a fold.",
    ]
    c.setFillColor(INK)
    for i, s in enumerate(steps, 1):
        lines = simpleSplit(s, REG, 8.5, col_w - 14)
        c.setFont(BOLD, 8.5)
        c.drawString(col_x, y, f"{i}.")
        c.setFont(REG, 8.5)
        for ln in lines:
            c.drawString(col_x + 12, y, ln)
            y -= 10.8
        y -= 3

    y -= 8
    c.setFont(BOLD, 12)
    c.setFillColor(NAVY)
    c.drawString(col_x, y, "Sheets  (left, top from panel corner, in)")
    y -= 15
    c.setFont(SEMI, 8.5)
    c.setFillColor(INK_SOFT)
    cols = (0, 14, 92, 152)
    for cx_, t in zip(cols, ("#", "Content", "Panel", "Left, top")):
        c.drawString(col_x + cx_, y, t)
    y -= 4
    c.setStrokeColor(LINE)
    c.line(col_x, y, col_x + col_w, y)
    y -= 11
    panel_names = {0: "Left wing", WING: "Center", WING + CENTER_W: "Right wing"}
    c.setFillColor(INK)
    for n, label, px, xo, yt, w_, h_, col in sorted(SHEETS):
        c.setFont(BOLD, 8.5)
        c.drawString(col_x, y, str(n))
        c.setFont(REG, 8.5)
        c.drawString(col_x + cols[1], y, label)
        c.drawString(col_x + cols[2], y, panel_names[px])
        c.drawString(col_x + cols[3], y, f"{xo:.2f}, {yt:.1f}")
        y -= 12

    c.setFont(REG, 7.5)
    c.setFillColor(INK_SOFT)
    c.drawString(margin, margin - 8,
                 "Board: 28 × 22 in. Wings 7.09 in each, center 13.82 in. Nothing crosses a fold. QR on sheet 2 links to the Improv Club sign-up in Hackley Clubz.")
    c.showPage()
    c.save()


# ---------------------------------------------------------------- preview
def board_preview(pdf_path, out_png, dpi=50):
    """Render the six pages and paste the trimmed sheets onto a board image."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    tmp = os.path.join(HERE, ".preview")
    os.makedirs(tmp, exist_ok=True)
    try:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf_path, os.path.join(tmp, "p")], check=True)
    except (OSError, subprocess.CalledProcessError):
        return
    files = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    board = Image.new("RGB", (int(BOARD_W * dpi), int(BOARD_H * dpi)), (236, 232, 222))
    d = ImageDraw.Draw(board)
    for fx in (WING, WING + CENTER_W):
        d.line([(fx * dpi, 0), (fx * dpi, BOARD_H * dpi)], fill=(150, 150, 150), width=2)
    for (n, label, px, xo, yt, w_, h_, col), f in zip(SHEETS, files):
        im = Image.open(os.path.join(tmp, f))
        pw_in, ph_in = im.width / dpi, im.height / dpi
        left = (pw_in - w_) / 2 * dpi
        top = (ph_in - h_) / 2 * dpi
        crop = im.crop((int(left), int(top), int(left + w_ * dpi), int(top + h_ * dpi)))
        board.paste(crop, (int((px + xo) * dpi), int(yt * dpi)))
    board.save(out_png)
    for f in files:
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


# ---------------------------------------------------------------- main
def main():
    out = os.path.join(HERE, "club-fair-poster.pdf")
    c = canvas.Canvas(out, pagesize=landscape(letter))
    c.setTitle("Hackley Improv Club club fair poster")
    c.setAuthor("Hackley Improv Club")
    for fn in (sheet_1_title, sheet_2_join, sheet_3_mission, sheet_4_howitworks, sheet_5_perform, sheet_6_cta):
        fn(c)
        c.showPage()
    c.save()
    print("wrote", out)

    guide = os.path.join(HERE, "assembly-guide.pdf")
    assembly_guide(guide)
    print("wrote", guide)

    preview = os.path.join(HERE, "board-preview.png")
    board_preview(out, preview)
    if os.path.exists(preview):
        print("wrote", preview)


if __name__ == "__main__":
    sys.exit(main())
