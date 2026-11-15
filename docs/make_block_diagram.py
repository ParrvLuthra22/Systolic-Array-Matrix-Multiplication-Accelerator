"""Draw docs/block_diagram.svg (and .png if rsvg-convert is installed).

Run from the repo root:  python3 docs/make_block_diagram.py
Requires: pip install reportlab
"""
import math
import shutil
import subprocess
from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors

OUT = Path(__file__).resolve().parent
INK = colors.HexColor("#1B2333")
GOLD = colors.HexColor("#A8842C")
SOFT = colors.HexColor("#F3F1EC")
MUTE = colors.HexColor("#5B6170")
OWNER = {"Parrv": "#2F5D8A", "Raghav": "#7A4E9C", "Ranjeet": "#2E7D5B",
         "Abhijeet": "#B05A2C", "Malhar": "#8A2F4F"}
F, FB = "Helvetica", "Helvetica-Bold"


def arrow(d, x1, y1, x2, y2, col=INK, w=1.0):
    d.add(Line(x1, y1, x2, y2, strokeColor=col, strokeWidth=w))
    a = math.atan2(y2 - y1, x2 - x1)
    L, s = 5.5, 0.42
    d.add(Polygon([x2, y2,
                   x2 - L * math.cos(a - s), y2 - L * math.sin(a - s),
                   x2 - L * math.cos(a + s), y2 - L * math.sin(a + s)],
                  fillColor=col, strokeColor=col))


def text(d, x, y, t, size=6.6, anchor="start", col=MUTE, font=F):
    d.add(String(x, y, t, fontName=font, fontSize=size, fillColor=col, textAnchor=anchor))


def box(d, x, y, w, h, title, sub=None, owner=None):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=SOFT, strokeColor=INK, strokeWidth=0.9))
    text(d, x + w / 2, y + h / 2 + (4 if sub else -3), title, 8.2, "middle", INK, FB)
    if sub:
        text(d, x + w / 2, y + h / 2 - 8, sub, 6.6, "middle")
    if owner:
        text(d, x + w / 2, y + 4, owner, 6.4, "middle", colors.HexColor(OWNER[owner]), FB)


def build():
    d = Drawing(495, 300)
    d.add(Rect(0, 0, 495, 300, fillColor=colors.white, strokeColor=colors.HexColor("#D8D3C7"),
               strokeWidth=0.6, strokeDashArray=[3, 3]))
    text(d, 6, 290, "systolic_top  (Parrv)", 7, "start", colors.HexColor(OWNER["Parrv"]), FB)

    # input buffer + load port
    box(d, 44, 112, 100, 116, "input_buffer", "stores A, B + skew", "Abhijeet")
    arrow(d, 2, 170, 44, 170)
    text(d, 4, 175, "load", 6.2)
    text(d, 4, 160, "port", 6.2)

    # 4x4 PE grid
    gx, gy, cell, pitch = 196, 92, 30, 40
    for i in range(4):
        for j in range(4):
            x, y = gx + j * pitch, gy + (3 - i) * pitch
            d.add(Rect(x, y, cell, cell, rx=2, ry=2, fillColor=colors.white,
                       strokeColor=INK, strokeWidth=0.8))
            text(d, x + cell / 2, y + cell / 2 - 2, f"PE{i}{j}", 6.2, "middle", INK, FB)
            if j < 3:
                arrow(d, x + cell, y + cell / 2, x + pitch, y + cell / 2, GOLD, 0.8)
            if i < 3:
                arrow(d, x + cell / 2, y, x + cell / 2, y - (pitch - cell), GOLD, 0.8)
    text(d, gx + 58, gy - 22, "systolic_array (16 x pe)", 7.2, "middle", INK, FB)
    text(d, gx + 28, gy - 32, "Ranjeet", 6.4, "middle", colors.HexColor(OWNER["Ranjeet"]), FB)
    text(d, gx + 84, gy - 32, "pe: Raghav", 6.4, "middle", colors.HexColor(OWNER["Raghav"]), FB)

    # a_left into each row
    for i in range(4):
        y = gy + (3 - i) * pitch + cell / 2
        arrow(d, 144, y, gx, y, INK, 0.9)
    text(d, 170, gy + 3 * pitch + cell + 4, "a_left", 6.8, "middle", INK, FB)

    # b_top bus into each column
    topy = gy + 4 * pitch + 14
    d.add(Line(94, 228, 94, topy, strokeColor=INK, strokeWidth=0.9))
    d.add(Line(94, topy, gx + 3 * pitch + cell / 2, topy, strokeColor=INK, strokeWidth=0.9))
    for j in range(4):
        x = gx + j * pitch + cell / 2
        arrow(d, x, topy, x, gy + 3 * pitch + cell, INK, 0.9)
    text(d, 140, topy + 4, "b_top", 6.8, "middle", INK, FB)

    # output collector
    box(d, 372, 150, 112, 62, "output_collector", "16:1 result mux", "Abhijeet")
    arrow(d, gx + 3 * pitch + cell, 181, 372, 181, INK, 0.9)
    text(d, 358, 170, "c_flat", 6.6, "middle", INK, FB)
    arrow(d, 428, 130, 428, 150, INK, 0.9)
    text(d, 428, 121, "rd_row, rd_col", 6.2, "middle")
    arrow(d, 428, 212, 428, 236, INK, 0.9)
    text(d, 428, 240, "rd_data (32-bit)", 6.4, "middle")

    # controller
    box(d, 186, 6, 170, 46, "controller (FSM)", "IDLE CLEAR COMPUTE DRAIN DONE", "Parrv")
    arrow(d, 338, 52, 338, gy, INK, 0.9)
    text(d, 342, 66, "clear, en", 6.4)
    d.add(Line(186, 30, 94, 30, strokeColor=INK, strokeWidth=0.9))
    arrow(d, 94, 30, 94, 112, INK, 0.9)
    text(d, 100, 40, "feed_en, t", 6.4)
    arrow(d, 140, 16, 186, 16, INK, 0.9)
    text(d, 112, 13, "start", 6.4)
    arrow(d, 356, 29, 400, 29, INK, 0.9)
    text(d, 404, 32, "busy, done,", 6.2)
    text(d, 404, 23, "cycle_count", 6.2)
    return d


if __name__ == "__main__":
    svg = OUT / "block_diagram.svg"
    renderSVG.drawToFile(build(), str(svg))
    print(f"wrote {svg}")
    if shutil.which("rsvg-convert"):
        png = OUT / "block_diagram.png"
        subprocess.run(["rsvg-convert", "-z", "3", "-b", "white", "-o", str(png), str(svg)],
                       check=True)
        print(f"wrote {png}")
