"""Plot theoretical cycle counts and speed-up for both architectures."""
from math import log10
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "speedup.png"
ARRAY_SIZES = list(range(2, 17))
SYSTOLIC_CYCLES = [3 * n - 1 for n in ARRAY_SIZES]  # (3N - 2) compute + 1 clear
SEQUENTIAL_CYCLES = [n**3 for n in ARRAY_SIZES]
SPEEDUPS = [seq / systolic for seq, systolic in zip(SEQUENTIAL_CYCLES, SYSTOLIC_CYCLES)]


def render_with_matplotlib() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, (cycles_axis, speedup_axis) = plt.subplots(1, 2, figsize=(12, 4.8))
    cycles_axis.plot(ARRAY_SIZES, SYSTOLIC_CYCLES, marker="o", label="Systolic (includes clear)")
    cycles_axis.plot(ARRAY_SIZES, SEQUENTIAL_CYCLES, marker="s", label="Sequential (one MAC)")
    cycles_axis.set_yscale("log")
    cycles_axis.set_xlabel("Matrix dimension N")
    cycles_axis.set_ylabel("Cycles (log scale)")
    cycles_axis.set_title("Cycle count")
    cycles_axis.set_xticks([2, 4, 6, 8, 10, 12, 14, 16])
    cycles_axis.grid(True, which="both", linestyle=":", alpha=0.6)
    cycles_axis.legend()

    speedup_axis.plot(ARRAY_SIZES, SPEEDUPS, marker="o", color="#c56a12")
    speedup_axis.scatter([4], [64 / 11], color="#b3261e", zorder=3)
    speedup_axis.annotate("4x4: 5.82x", (4, 64 / 11), xytext=(8, 5),
                          textcoords="offset points", fontsize=9)
    speedup_axis.set_xlabel("Matrix dimension N")
    speedup_axis.set_ylabel("Sequential / systolic cycles")
    speedup_axis.set_title("End-to-end speed-up")
    speedup_axis.set_xticks([2, 4, 6, 8, 10, 12, 14, 16])
    speedup_axis.grid(True, linestyle=":", alpha=0.6)

    figure.suptitle("Systolic array versus sequential matrix multiplication")
    figure.tight_layout()
    figure.savefig(OUTPUT, dpi=180, bbox_inches="tight")
    plt.close(figure)


def render_with_pillow() -> None:
    """Draw the same two-panel chart when matplotlib is not installed."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1280, 560), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
    draw.text((290, 18), "Systolic array versus sequential matrix multiplication",
              fill="#202124", font=title_font)

    def chart_frame(left: int, right: int, top: int, bottom: int,
                    title: str, y_ticks: list[float], log_y: bool = False) -> None:
        draw.text((left, top - 55), title, fill="#202124", font=title_font)
        draw.line((left, top, left, bottom), fill="#444444", width=2)
        draw.line((left, bottom, right, bottom), fill="#444444", width=2)
        for tick in y_ticks:
            if log_y:
                y = bottom - (log10(tick) - log10(y_ticks[0])) / (log10(y_ticks[-1]) - log10(y_ticks[0])) * (bottom - top)
            else:
                y = bottom - tick / y_ticks[-1] * (bottom - top)
            draw.line((left, int(y), right, int(y)), fill="#e5e7eb", width=1)
            draw.text((left - 38, int(y) - 5), str(int(tick)), fill="#555555", font=font)
        for n in [2, 4, 6, 8, 10, 12, 14, 16]:
            x = left + (n - 2) / 14 * (right - left)
            draw.line((int(x), bottom, int(x), bottom + 5), fill="#444444", width=1)
            draw.text((int(x) - 7, bottom + 9), str(n), fill="#555555", font=font)
        draw.text(((left + right) // 2 - 45, bottom + 30), "Matrix dimension N", fill="#555555", font=font)
        return left, right, top, bottom

    left, right, top, bottom = chart_frame(95, 625, 140, 440, "Cycle count (log scale)",
                                           [5, 10, 20, 50, 100, 500, 1000, 5000], log_y=True)

    def cycle_point(n: int, value: int) -> tuple[int, int]:
        x = int(left + (n - 2) / 14 * (right - left))
        y = int(bottom - (log10(value) - log10(5)) / (log10(5000) - log10(5)) * (bottom - top))
        return x, y

    for series, color in ((SYSTOLIC_CYCLES, "#1769aa"), (SEQUENTIAL_CYCLES, "#d04a35")):
        points = [cycle_point(n, value) for n, value in zip(ARRAY_SIZES, series)]
        draw.line(points, fill=color, width=3)
        for x, y in points:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
    draw.line((130, 112, 155, 112), fill="#1769aa", width=3)
    draw.text((160, 106), "Systolic (includes clear)", fill="#444444", font=font)
    draw.line((330, 112, 355, 112), fill="#d04a35", width=3)
    draw.text((360, 106), "Sequential (one MAC)", fill="#444444", font=font)

    left2, right2, top2, bottom2 = chart_frame(755, 1205, 140, 440,
                                                "End-to-end speed-up",
                                                [0, 20, 40, 60, 80, 100])
    speed_points = [
        (int(left2 + (n - 2) / 14 * (right2 - left2)),
         int(bottom2 - value / 100 * (bottom2 - top2)))
        for n, value in zip(ARRAY_SIZES, SPEEDUPS)
    ]
    draw.line(speed_points, fill="#c56a12", width=3)
    for x, y in speed_points:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#c56a12")
    point4 = speed_points[2]
    draw.ellipse((point4[0] - 6, point4[1] - 6, point4[0] + 6, point4[1] + 6), fill="#b3261e")
    draw.text((point4[0] + 8, point4[1] - 18), "4x4: 5.82x", fill="#b3261e", font=font)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        render_with_matplotlib()
    except ImportError:
        render_with_pillow()
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
