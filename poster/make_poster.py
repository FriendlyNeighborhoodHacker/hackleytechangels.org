#!/usr/bin/env python3
"""Build the Hackley Tech Angels club-fair poster sheets.

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

# ---------------------------------------------------------------- brand
NAVY = HexColor("#1b2a5b")
PURPLE = HexColor("#4a3a8c")
CORAL = HexColor("#ff6b4a")
CORAL_DEEP = HexColor("#e04f2f")
TEAL = HexColor("#1b8a96")
GOLD = HexColor("#e0a32e")
INK = HexColor("#1a1d2b")
INK_SOFT = HexColor("#545a70")
TINT = HexColor("#f6f4fb")
LINE = HexColor("#e6e4ef")
WHITE = white

QR_URL = "https://www.hackleyclubz.org/clubs/qr.php?t=90073b026a3786859ae29ab2faf35d4a"
MISSION = ("The Hackley Tech Angels empowers people excited about technology "
           "to solve problems that can help their community or the broader world.")
TAGLINE = "There is a problem out there only you will think to solve."
MEETS = "DAY 1 · LUNCH"

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
    dark_bg = bg in (NAVY, CORAL, PURPLE)
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


def draw_logo(c, cx, top, height):
    ratio = 1184 / 778
    w = height * ratio
    c.drawImage(os.path.join(HERE, "assets", "logo.png"), cx - w / 2, top - height, w, height, mask="auto")
    return top - height


def draw_hornet(c, x, y, size, radius=None):
    """Hornet icon (yellow square) clipped to a rounded square."""
    radius = radius or size * 0.22
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, size, size, radius)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(os.path.join(HERE, "assets", "hornet.jpg"), x, y, size, size)
    c.restoreState()


def icon_community(c, cx, cy, s, color):
    """Three people. s = overall width."""
    c.setFillColor(color)
    for dx, scale in ((-s * 0.30, 0.82), (0, 1.0), (s * 0.30, 0.82)):
        hr = s * 0.11 * scale
        bw = s * 0.19 * scale
        bh = s * 0.17 * scale
        x = cx + dx
        base = cy - s * 0.22
        c.circle(x, base + bh + hr * 1.15, hr, stroke=0, fill=1)
        c.wedge(x - bw, base - bh, x + bw, base + bh, 0, 180, stroke=0, fill=1)
    c.setStrokeColor(color)


def icon_world(c, cx, cy, s, color):
    """Globe outline. s = diameter."""
    r = s / 2
    c.setStrokeColor(color)
    c.setLineWidth(s * 0.055)
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.ellipse(cx - r * 0.42, cy - r, cx + r * 0.42, cy + r, stroke=1, fill=0)
    c.line(cx - r, cy, cx + r, cy)
    c.line(cx - r * 0.9, cy + r * 0.45, cx + r * 0.9, cy + r * 0.45)
    c.line(cx - r * 0.9, cy - r * 0.45, cx + r * 0.9, cy - r * 0.45)
    c.line(cx, cy - r, cx, cy + r)


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


def phone_mockup(c, cx, top, height):
    """Simple phone with a Hackley Clubz screen. Returns bottom y."""
    w = height * 0.5
    h = height
    x, y = cx - w / 2, top - h
    r = w * 0.14
    c.setFillColor(NAVY)
    c.roundRect(x, y, w, h, r, stroke=0, fill=1)
    # screen
    m = w * 0.045
    sx, sy, sw_, sh = x + m, y + m, w - 2 * m, h - 2 * m
    c.setFillColor(WHITE)
    c.roundRect(sx, sy, sw_, sh, r * 0.72, stroke=0, fill=1)
    # notch
    c.setFillColor(NAVY)
    c.roundRect(cx - w * 0.16, top - m - w * 0.05, w * 0.32, w * 0.07, w * 0.035, stroke=0, fill=1)
    # header
    hy = top - m - w * 0.17
    c.setFillColor(NAVY)
    c.setFont(BOLD, w * 0.085)
    c.drawString(sx + w * 0.08, hy - w * 0.02, "Hackley Clubz")
    c.setFillColor(CORAL_DEEP)
    c.setFont(MED, w * 0.052)
    c.drawString(sx + w * 0.08, hy - w * 0.10, "Upcoming events across all of your clubs.")
    # featured card: Tech Angels meeting
    cy0 = hy - w * 0.20
    ch = w * 0.42
    c.setFillColor(TINT)
    c.roundRect(sx + w * 0.07, cy0 - ch, sw_ - w * 0.14, ch, w * 0.05, stroke=0, fill=1)
    ico = w * 0.17
    draw_hornet(c, sx + w * 0.12, cy0 - w * 0.06 - ico, ico)
    tx = sx + w * 0.12 + ico + w * 0.05
    c.setFillColor(INK_SOFT)
    c.setFont(MED, w * 0.05)
    c.drawString(tx, cy0 - w * 0.12, "Club meeting")
    c.setFillColor(NAVY)
    c.setFont(BOLD, w * 0.072)
    c.drawString(tx, cy0 - w * 0.21, "Tech Angels")
    c.setFillColor(CORAL_DEEP)
    c.setFont(SEMI, w * 0.055)
    c.drawString(sx + w * 0.12, cy0 - w * 0.36, "Day 1  ·  Lunch")
    # RSVP pill
    pw_, ph_ = w * 0.24, w * 0.11
    px = sx + sw_ - w * 0.07 - pw_ - w * 0.05
    c.setFillColor(CORAL)
    c.roundRect(px, cy0 - w * 0.38, pw_, ph_, ph_ / 2, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(BOLD, w * 0.055)
    c.drawCentredString(px + pw_ / 2, cy0 - w * 0.38 + ph_ * 0.31, "RSVP")
    # other event placeholders (no invented content)
    yy = cy0 - ch - w * 0.08
    for _ in range(3):
        if yy - w * 0.26 < sy + w * 0.16:
            break
        c.setFillColor(TINT)
        c.roundRect(sx + w * 0.07, yy - w * 0.24, sw_ - w * 0.14, w * 0.24, w * 0.05, stroke=0, fill=1)
        c.setFillColor(LINE)
        c.roundRect(sx + w * 0.12, yy - w * 0.10, w * 0.40, w * 0.045, w * 0.02, stroke=0, fill=1)
        c.roundRect(sx + w * 0.12, yy - w * 0.18, w * 0.58, w * 0.045, w * 0.02, stroke=0, fill=1)
        yy -= w * 0.30
    # home indicator
    c.setFillColor(NAVY)
    c.roundRect(cx - w * 0.15, sy + w * 0.035, w * 0.30, w * 0.02, w * 0.01, stroke=0, fill=1)
    return y


# ---------------------------------------------------------------- sheets
def sheet_1_title(c):
    x0, y0, w, h = begin_sheet(c, 1, "center top", "landscape", WHITE)
    pad = 0.35 * IN
    cx = x0 + w / 2
    inner_w = w - 2 * pad
    # thin brand bar at the very top of the card
    bar = 0.16 * IN
    c.setFillColor(CORAL)
    c.rect(x0 - BLEED, y0 + h - bar, w + 2 * BLEED, bar + BLEED, stroke=0, fill=1)

    # measure the block, then center it vertically in the space under the bar
    logo_h = 2.7 * IN
    big = fit_size("TECH ANGELS", BOLD, inner_w, 200)
    small = big * 0.5
    tsize, tlines = wrap_fit(TAGLINE, SERIF_ITALIC, inner_w * 0.92, 1.6 * IN, 46, leading=1.15)
    total = logo_h + 0.16 * IN + small * 0.95 + big * 0.98 + 0.06 * IN + len(tlines) * tsize * 1.15
    avail_top = y0 + h - bar - pad
    avail = avail_top - (y0 + pad)
    top = avail_top - max(0, (avail - total) / 2)

    bottom = draw_logo(c, cx, top, logo_h)
    y = bottom - 0.16 * IN
    tracked(c, cx, y - small * 0.78, "HACKLEY", BOLD, small, small * 0.12, CORAL_DEEP, align="center")
    y -= small * 0.95
    c.setFont(BOLD, big)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, y - big * 0.78, "TECH ANGELS")
    y -= big * 0.98 + 0.06 * IN
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
    draw_qr(c, px + 0.2 * IN, py + 0.2 * IN, qr_size)

    # right column
    col_x = px + panel + 0.35 * IN
    col_w = x0 + w - pad - col_x
    lines = ["SCAN", "TO", "JOIN"]
    size = fit_lines(lines, BOLD, col_w, 140)
    block_h = size * 0.78 + size * 0.98 * 2   # three lines
    extra = 0.22 * IN + 30 + 0.12 * IN + 36 * 1.05 + 0.18 * IN + 22  # trailing text
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
    msize = fit_size(MEETS, BOLD, col_w, 40)
    c.setFont(BOLD, msize)
    c.setFillColor(GOLD)
    c.drawCentredString(col_x + col_w / 2, y - msize * 0.78, MEETS)
    y -= msize * 0.78 + 0.28 * IN
    c.setFont(MED, 20)
    c.setFillColor(Color(1, 1, 1, 0.7))
    for ln in ["Opens in", "Hackley Clubz"]:
        c.drawCentredString(col_x + col_w / 2, y - 20 * 0.78, ln)
        y -= 20 * 1.15


def sheet_3_mission(c):
    x0, y0, w, h = begin_sheet(c, 3, "left wing top", "portrait", GOLD)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    cx = x0 + w / 2
    y = y0 + h - pad
    tracked(c, x0 + pad, y - 24 * 0.78, "WHO WE ARE", BOLD, 24, 3, NAVY)
    y -= 24 + 0.16 * IN
    c.setFillColor(NAVY)
    c.rect(x0 + pad, y, 1.1 * IN, 5, stroke=0, fill=1)
    y -= 0.36 * IN

    icons_h = 2.7 * IN
    avail = y - (y0 + pad) - icons_h - 0.3 * IN
    size, lines = wrap_fit(MISSION, SEMI, inner_w, avail, 40, leading=1.2, min_size=24)
    y = left_lines(c, x0 + pad, y, lines, SEMI, size, NAVY, leading=1.2)

    # two icons
    icon_y = y0 + pad + icons_h - 0.05 * IN
    for (col_cx, draw, label) in ((x0 + w * 0.29, icon_community, "your community"),
                                  (x0 + w * 0.71, icon_world, "the world")):
        r = 0.86 * IN
        cy = icon_y - r
        c.setFillColor(WHITE)
        c.circle(col_cx, cy, r, stroke=0, fill=1)
        draw(c, col_cx, cy, r * 1.15, NAVY)
        c.setFont(SEMI, 21)
        c.setFillColor(NAVY)
        c.drawCentredString(col_cx, cy - r - 0.42 * IN, label)


def sheet_4_startup(c):
    x0, y0, w, h = begin_sheet(c, 4, "left wing bottom", "portrait", WHITE)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    y = y0 + h - pad
    tracked(c, x0 + pad, y - 24 * 0.78, "LEARN TO BUILD", BOLD, 24, 3, CORAL_DEEP)
    y -= 24 + 0.12 * IN
    lines = ["A TECH", "START-UP"]
    size = fit_lines(lines, BOLD, inner_w, 96)
    y = left_lines(c, x0 + pad, y, lines, BOLD, size, NAVY, leading=1.0)
    y -= 0.18 * IN
    sub = "We help you build the skills you’d need to build a tech start-up."
    ssize, slines = wrap_fit(sub, MED, inner_w, 2.0 * IN, 26, leading=1.25, min_size=20)
    y = left_lines(c, x0 + pad, y, slines, MED, ssize, INK_SOFT, leading=1.25)
    y -= 0.30 * IN

    steps = ["Meet a real client",
             "Scope the problem",
             "Split up the work",
             "Ship it together",
             "Keep it running for real users"]
    avail = y - (y0 + pad)
    row = min(0.85 * IN, avail / len(steps))
    r = 0.24 * IN
    text_x = x0 + pad + 2 * r + 0.22 * IN
    text_w = x0 + w - pad - text_x
    for i, step in enumerate(steps, 1):
        cy = y - row / 2
        c.setFillColor(CORAL)
        c.circle(x0 + pad + r, cy, r, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(BOLD, 22)
        c.drawCentredString(x0 + pad + r, cy - 22 * 0.36, str(i))
        tsize, tlines = wrap_fit(step, SEMI, text_w, row - 6, 27, leading=1.1, min_size=20)
        block = len(tlines) * tsize * 1.1
        ty = cy + block / 2
        left_lines(c, text_x, ty, tlines, SEMI, tsize, NAVY, leading=1.1)
        if i < len(steps):
            c.setStrokeColor(LINE)
            c.setLineWidth(1)
            c.line(text_x, y - row, x0 + w - pad, y - row)
        y -= row


def sheet_5_clubz(c):
    x0, y0, w, h = begin_sheet(c, 5, "right wing top", "portrait", WHITE)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    cx = x0 + w / 2
    y = y0 + h - pad
    lines = ["WE MANAGE", "HACKLEY", "CLUBZ!"]
    size = fit_lines(lines, BOLD, inner_w, 84)
    y = centered_lines(c, cx, y, lines, BOLD, size, NAVY, leading=1.0)
    y -= 0.12 * IN
    sub = "The app Hackley students use for clubs."
    ssize, slines = wrap_fit(sub, MED, inner_w, 1.4 * IN, 25, leading=1.25, min_size=20)
    y = centered_lines(c, cx, y, slines, MED, ssize, INK_SOFT, leading=1.25)
    y -= 0.28 * IN

    foot = 34
    phone_h = y - (y0 + pad) - foot - 0.35 * IN
    phone_mockup(c, cx, y, phone_h)
    c.setFont(BOLD, foot)
    c.setFillColor(CORAL_DEEP)
    c.drawCentredString(cx, y0 + pad + foot * 0.1, "Real app. Real users.")


def sheet_6_cta(c):
    x0, y0, w, h = begin_sheet(c, 6, "right wing bottom", "portrait", CORAL)
    pad = 0.42 * IN
    inner_w = w - 2 * pad
    cx = x0 + w / 2
    y = y0 + h - pad - 0.1 * IN
    hook = ["Excited", "about tech?"]
    hsize = fit_lines(hook, MED, inner_w, 54)
    y = centered_lines(c, cx, y, hook, MED, hsize, WHITE, leading=1.05)
    y -= 0.25 * IN
    pay = ["You", "belong", "here."]
    psize = fit_lines(pay, BOLD, inner_w, 120)
    y = centered_lines(c, cx, y, pay, BOLD, psize, NAVY, leading=0.95)
    y -= 0.42 * IN

    # DAY 1 · LUNCH pill
    msize = fit_size(MEETS, BOLD, inner_w - 1.2 * IN, 34)
    pw_ = sw(MEETS, BOLD, msize) + 0.8 * IN
    ph_ = msize + 0.42 * IN
    c.setFillColor(WHITE)
    c.roundRect(cx - pw_ / 2, y - ph_, pw_, ph_, ph_ / 2, stroke=0, fill=1)
    c.setFillColor(CORAL_DEEP)
    c.setFont(BOLD, msize)
    c.drawCentredString(cx, y - ph_ + (ph_ - msize * 0.72) / 2, MEETS)
    y -= ph_ + 0.5 * IN

    # arrow + "scan the code to join"
    txt = "scan the code to join"
    tsize = 26
    arrow_len = 0.75 * IN
    total = arrow_len + 0.2 * IN + sw(txt, SEMI, tsize)
    if total > inner_w:
        tsize = fit_size(txt, SEMI, inner_w - arrow_len - 0.2 * IN, tsize)
        total = arrow_len + 0.2 * IN + sw(txt, SEMI, tsize)
    ax = cx - total / 2
    ay = y - tsize * 0.35
    arrow_left(c, ax, ay, arrow_len, WHITE, 6)
    c.setFont(SEMI, tsize)
    c.setFillColor(WHITE)
    c.drawString(ax + arrow_len + 0.2 * IN, y - tsize * 0.72, txt)
    y -= tsize + 0.32 * IN
    c.setFont(MED, 20)
    c.setFillColor(Color(1, 1, 1, 0.9))
    c.drawCentredString(cx, y - 20 * 0.78, "(it’s on the center panel)")


# ---------------------------------------------------------------- assembly guide
BOARD_W, BOARD_H = 28.0, 22.0
WING = 18 / 2.54          # 7.087 in
CENTER_W = BOARD_W - 2 * WING
WING_X_OFF = (WING - 6.6) / 2
CENTER_X_OFF = (CENTER_W - 10.4) / 2
SHEETS = [  # (n, label, panel x-origin, x offset in panel, y from top, w, h, color)
    (1, "Title", WING, CENTER_X_OFF, 2.7, 10.4, 7.9, WHITE),
    (2, "Scan to join", WING, CENTER_X_OFF, 2.7 + 7.9 + 0.8, 10.4, 7.9, NAVY),
    (3, "Who we are", 0, WING_X_OFF, 0.5, 6.6, 10.2, GOLD),
    (4, "Build a start-up", 0, WING_X_OFF, 0.5 + 10.2 + 0.6, 6.6, 10.2, WHITE),
    (5, "Hackley Clubz", WING + CENTER_W, WING_X_OFF, 0.5, 6.6, 10.2, WHITE),
    (6, "You belong here", WING + CENTER_W, WING_X_OFF, 0.5 + 10.2 + 0.6, 6.6, 10.2, CORAL),
]


def assembly_guide(path):
    c = canvas.Canvas(path, pagesize=landscape(letter))
    c.setTitle("Hackley Tech Angels club fair poster - assembly guide")
    pw, ph = landscape(letter)
    margin = 0.45 * IN
    c.setFont(BOLD, 20)
    c.setFillColor(NAVY)
    c.drawString(margin, ph - margin - 14, "Hackley Tech Angels — Club Fair Poster Assembly")
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
    c.setStrokeColor(CORAL_DEEP)
    c.setLineWidth(1)
    c.setDash(5, 3)
    for fx in (WING, WING + CENTER_W):
        c.line(X(fx), by, X(fx), by + bh)
    c.setDash()
    c.setFont(SEMI, 8)
    c.setFillColor(CORAL_DEEP)
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
        dark = col in (NAVY, CORAL)
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
                 "Board: 28 × 22 in. Wings 7.09 in each, center 13.82 in. Nothing crosses a fold. QR on sheet 2 links to the Tech Angels sign-up in Hackley Clubz.")
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
    c.setTitle("Hackley Tech Angels club fair poster")
    c.setAuthor("Hackley Tech Angels")
    for fn in (sheet_1_title, sheet_2_join, sheet_3_mission, sheet_4_startup, sheet_5_clubz, sheet_6_cta):
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
