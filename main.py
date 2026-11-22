#!/usr/bin/env python3
"""Broadsheet front page summing up the world news of Saturday 21 November 2026.

Pure Python standard library. Renders a deterministic 1024x1024 PNG and
writes it to /output/entry.png (falling back to ./entry.png when /output
is not available). No network, no clock, no randomness: two runs always
produce byte-identical output.

Stories (all verified as 21 Nov 2026 events):
  LEAD  Mexico captures "El Chapo Isidro", FBI Top 10 fugitive (Sinaloa)
  P2    Russian missile hits Kryvyi Rih, Ukraine
  P3    COP31 climate summit slips into overtime, Antalya
  P4    AI stocks tumble worldwide (S&P -3.7%, Nikkei -5.06%)
  P5    Trump weighs a new strike on Iran
  P6    Magnitude 6.7 earthquake shakes Peru
  P7    BepiColombo enters orbit around Mercury
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 233)
INK = (26, 24, 20)
ACCENT = (154, 32, 24)
MUTED = (96, 90, 80)
RULE = (70, 65, 56)
POSTER = (233, 224, 205)
RIVER = (74, 110, 140)
GOLD = (176, 132, 40)

BUF = bytearray(bytes(PAPER) * (W * H))


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        BUF[i] = color[0]
        BUF[i + 1] = color[1]
        BUF[i + 2] = color[2]


def fill_rect(x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px(x, y, color)


def hline(x0, x1, y, color, thick=1):
    for t in range(thick):
        for x in range(x0, x1):
            px(x, y + t, color)


def vline(x, y0, y1, color, thick=1):
    for t in range(thick):
        for y in range(y0, y1):
            px(x + t, y, color)


def line(x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for t in range(thick):
            px(x, y + t, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def filled_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                px(cx + dx, cy + dy, color)


def ring(cx, cy, r, color, thick=2):
    for dy in range(-r - thick, r + thick + 1):
        for dx in range(-r - thick, r + thick + 1):
            d = dx * dx + dy * dy
            if (r - thick) ** 2 <= d <= (r + thick) ** 2:
                px(cx + dx, cy + dy, color)


# ---------------------------------------------------------------- font
# Classic 5x7 bitmap glyphs, rows top to bottom, 5 bits per row.
FONT = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11100, 0b10010, 0b10001, 0b10001, 0b10001, 0b10010, 0b11100),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b01010, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "—": (0, 0, 0, 0b11111, 0, 0, 0),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "%": (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "•": (0, 0, 0b01110, 0b01110, 0b01110, 0, 0),
}


def draw_char(x, y, ch, scale, color, bold=False):
    glyph = FONT.get(ch.upper(), FONT[" "])
    off = max(1, scale // 2) if bold else 0
    for row in range(7):
        bits = glyph[row]
        for col in range(5):
            if bits & (1 << (4 - col)):
                fill_rect(x + col * scale, y + row * scale,
                          x + col * scale + scale, y + row * scale + scale,
                          color)
                if off:
                    fill_rect(x + col * scale + off, y + row * scale,
                              x + col * scale + scale + off,
                              y + row * scale + scale, color)


def text_width(text, scale, bold=False):
    if not text:
        return 0
    w = len(text) * 6 * scale - scale
    if bold:
        w += max(1, scale // 2)
    return w


def draw_text(x, y, text, scale, color, bold=False):
    cx = x
    for ch in text:
        draw_char(cx, y, ch, scale, color, bold)
        cx += 6 * scale
    return cx


def draw_text_centered(y, text, scale, color, bold=False, cx=W // 2):
    x = cx - text_width(text, scale, bold) // 2
    draw_text(x, y, text, scale, color, bold)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            cur = ""
        while text_width(word, scale) > max_width:
            cut = 1
            while cut < len(word) and \
                    text_width(word[:cut + 1], scale) <= max_width:
                cut += 1
            lines.append(word[:cut])
            word = word[cut:]
        cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, color, max_width, line_gap, bold=False):
    lines = wrap_text(text, scale, max_width)
    lh = 7 * scale + line_gap
    for i, ln in enumerate(lines):
        draw_text(x, y + i * lh, ln, scale, color, bold)
    return len(lines) * lh - line_gap


# ---------------------------------------------------------------- motifs
def motif_starburst(cx, cy, r, color):
    for ang in range(8):
        ex = int(cx + r * math.cos(ang * math.pi / 4))
        ey = int(cy + r * math.sin(ang * math.pi / 4))
        line(cx, cy, ex, ey, color, 2)
    filled_circle(cx, cy, 4, color)


def motif_globe(cx, cy, r):
    ring(cx, cy, r, RIVER, 2)
    hline(cx - r, cx + r, cy, RIVER, 2)
    line(cx - int(r * 0.8), cy - int(r * 0.55), cx + int(r * 0.8),
         cy - int(r * 0.55), RIVER, 2)
    line(cx - int(r * 0.8), cy + int(r * 0.55), cx + int(r * 0.8),
         cy + int(r * 0.55), RIVER, 2)


def motif_chart(cx, cy):
    # three falling bars + a red down arrow
    fill_rect(cx - 18, cy - 2, cx - 10, cy + 16, INK)
    fill_rect(cx - 5, cy + 4, cx + 3, cy + 16, INK)
    fill_rect(cx + 8, cy + 10, cx + 16, cy + 16, INK)
    line(cx - 20, cy - 14, cx + 18, cy + 14, ACCENT, 2)
    line(cx + 18, cy + 14, cx + 18, cy + 6, ACCENT, 2)
    line(cx + 18, cy + 14, cx + 10, cy + 14, ACCENT, 2)


def motif_target(cx, cy):
    ring(cx, cy, 18, INK, 2)
    ring(cx, cy, 11, INK, 2)
    filled_circle(cx, cy, 4, ACCENT)


def motif_quake(cx, cy):
    pts = [(-20, 0), (-14, 0), (-10, -12), (-6, 12), (-2, -6),
           (2, 10), (6, -14), (10, 6), (14, 0), (20, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        line(cx + ax, cy + ay, cx + bx, cy + by, ACCENT, 2)


def motif_planet(cx, cy):
    filled_circle(cx, cy, 12, GOLD)
    for i in range(48):
        t = i / 48 * 2 * math.pi
        ex = int(cx + 22 * math.cos(t))
        ey = int(cy + 8 * math.sin(t))
        px(ex, ey, INK)
        px(ex, ey + 1, INK)
    filled_circle(cx + 24, cy - 10, 3, INK)


MOTIFS = {
    "burst": motif_starburst,
    "globe": motif_globe,
    "chart": motif_chart,
    "target": motif_target,
    "quake": motif_quake,
    "planet": motif_planet,
}


def draw_motif(kind, cx, cy):
    if kind == "burst":
        motif_starburst(cx, cy, 18, ACCENT)
    elif kind == "globe":
        motif_globe(cx, cy, 17)
    elif kind == "chart":
        motif_chart(cx, cy)
    elif kind == "target":
        motif_target(cx, cy)
    elif kind == "quake":
        motif_quake(cx, cy)
    elif kind == "planet":
        motif_planet(cx, cy)


# ---------------------------------------------------------------- lead art
def draw_wanted_poster(x0, y0, x1, y1):
    """WANTED poster: silhouette of the captured kingpin, FBI TOP 10."""
    fill_rect(x0, y0, x1, y1, POSTER)
    for t in range(3):
        hline(x0 + t, x1 - t, y0 + t, INK, 1)
        hline(x0 + t, x1 - t, y1 - 1 - t, INK, 1)
        vline(x0 + t, y0, y1, INK, 1)
        vline(x1 - 1 - t, y0, y1, INK, 1)
    cx = (x0 + x1) // 2
    draw_text_centered(y0 + 12, "WANTED", 4, ACCENT, bold=True, cx=cx)
    # silhouette: head + shoulders
    filled_circle(cx, y0 + 92, 32, INK)
    fill_rect(cx - 46, y0 + 128, cx + 46, y0 + 168, INK)
    filled_circle(cx - 46, y0 + 128, 20, INK)
    filled_circle(cx + 46, y0 + 128, 20, INK)
    draw_text_centered(y0 + 176, "FBI TOP 10", 2, INK, bold=True, cx=cx)
    # jail bars along the bottom
    for bx in range(x0 + 14, x1 - 10, 18):
        vline(bx, y1 - 30, y1 - 8, INK, 3)


# ---------------------------------------------------------------- layout
def draw_masthead():
    draw_text_centered(26, "EST. 2026 — ONE PAGE, ONE DAY, THE WHOLE WORLD",
                       2, MUTED)
    draw_text_centered(50, "THE WORLD IN ONE PICTURE", 6, INK, bold=True)
    draw_text_centered(102, "SATURDAY 21 NOVEMBER 2026", 3, ACCENT, bold=True)
    hline(24, 1000, 132, INK, 3)
    hline(24, 1000, 138, ACCENT, 2)


def draw_lead():
    x = 24
    y = 152
    draw_text(x, y, "MEXICO — CARTEL KINGPIN CAPTURED", 2, ACCENT, bold=True)
    draw_text(x, y + 26, "MEXICO NABS", 5, INK, bold=True)
    draw_text(x, y + 73, "EL CHAPO ISIDRO", 5, INK, bold=True)
    summary = ("Troops capture Fausto Isidro Meza Flores, alias El Chapo "
               "Isidro, a Beltran Leyva leader and one of the FBI's 10 "
               "most wanted, in Guasave, Sinaloa. Gunfights and burning "
               "roadblocks follow.")
    draw_wrapped(x, y + 126, summary, 2, INK, 636, 6)
    hline(24, 672, y + 216, RULE, 2)
    draw_wanted_poster(688, 148, 1000, 388)
    hline(24, 1000, 404, INK, 3)


def draw_panel(x, y, kicker, headline, body, motif):
    draw_text(x + 12, y + 6, kicker, 2, ACCENT, bold=True)
    draw_motif(motif, x + 428, y + 24)
    draw_wrapped(x + 12, y + 24, headline, 3, INK, 400, 7, bold=True)
    draw_wrapped(x + 12, y + 80, body, 2, MUTED, 460, 4)


def draw_panels():
    draw_text(24, 414, "AROUND THE WORLD — IN BRIEF", 2, INK, bold=True)
    hline(24, 1000, 438, RULE, 2)
    panels = [
        ("UKRAINE — KRYVYI RIH",
         "MISSILE HITS KRYVYI",
         "Russian missile hits Zelenskyy's home city in a double-tap "
         "attack: a 7-year-old and a 20-year-old killed, 60 hurt, six "
         "of them children.",
         "burst"),
        ("CLIMATE — ANTALYA",
         "COP31 SLIPS INTO OVERTIME",
         "Climate summit passes its Friday deadline with no deal. "
         "Fossil-fuel phaseout and the $120bn adaptation target are "
         "cut from the draft.",
         "globe"),
        ("MARKETS — FRIDAY",
         "AI STOCKS TUMBLE WORLDWIDE",
         "Wall Street falls 3.7% in Friday trading and Japan's Nikkei "
         "drops 5.06% as the AI sell-off spreads. Fears AI spending "
         "will not pay off.",
         "chart"),
        ("MIDDLE EAST — WASHINGTON",
         "TRUMP WEIGHS NEW IRAN STRIKE",
         "The president weighs extensive new military action against "
         "Iran amid fresh intelligence on its capabilities and Israeli "
         "pressure to move fast.",
         "target"),
        ("PERU — JUNIN",
         "QUAKE 6.7 SHAKES PERU",
         "Magnitude 6.7 quake strikes Junin in central Peru, felt as "
         "far as Lima. Residents run into the streets. No deaths or "
         "major damage reported.",
         "quake"),
        ("SPACE — MERCURY",
         "BEPICOLOMBO ENTERS MERCURY ORBIT",
         "The ESA-JAXA probe reaches orbit after an 8-year voyage, "
         "only the second mission ever to orbit the innermost planet. "
         "Science starts April 2027.",
         "planet"),
    ]
    top = 448
    row_h = 152
    col_x = (24, 512)
    for i, (kick, head, body, motif) in enumerate(panels):
        x = col_x[i % 2]
        y = top + (i // 2) * row_h
        draw_panel(x, y, kick, head, body, motif)
    vline(506, 448, 904, RULE, 2)
    hline(24, 1000, 600, RULE, 1)
    hline(24, 1000, 752, RULE, 1)


def draw_ticker():
    fill_rect(24, 912, 1000, 1000, INK)
    ticker = ("HOUTHIS STRIKE RIYADH • EU APPROVES 1BN EURO MILITARY AID "
              "FOR UKRAINE • BRAZIL MOSQUITOES CUT DENGUE 69% • "
              "EU-INDONESIA DEAL AFTER 10 YEARS")
    lines = wrap_text(ticker, 2, 940)
    lh = 20
    total = len(lines) * lh - 6
    y = 912 + (88 - total) // 2
    for i, ln in enumerate(lines):
        draw_text_centered(y + i * lh, ln, 2, PAPER, cx=512)


def render():
    for t in range(2):
        hline(10 + t, 1014 - t, 10 + t, INK, 1)
        hline(10 + t, 1014 - t, 1013 - t, INK, 1)
        vline(10 + t, 10, 1014, INK, 1)
        vline(1013 - t, 10, 1014, INK, 1)
    draw_masthead()
    draw_lead()
    draw_panels()
    draw_ticker()


# ---------------------------------------------------------------- png out
def png_bytes():
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw += BUF[y * row:(y + 1) * row]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    render()
    data = png_bytes()
    path = "./entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
        path = "/output/entry.png"
    except OSError:
        path = "./entry.png"
    try:
        with open(path, "wb") as fh:
            fh.write(data)
    except OSError:
        path = "./entry.png"
        with open(path, "wb") as fh:
            fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
