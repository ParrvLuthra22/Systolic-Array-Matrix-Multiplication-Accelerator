"""Stitch the report sections into docs/report/final_report.md (and .docx/.html if pandoc exists).

Run from the repo root:  python3 docs/report/build_report.py   (or: make report)
A missing section is replaced by a TODO line naming its owner, so the report always builds.
"""
import shutil
import subprocess
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

SECTIONS = [
    ("section_1_introduction.md", "1. Introduction", "Parrv"),
    ("section_2_architecture.md", "2. Architecture", "Parrv"),
    ("section_3_1_pe.md", "3.1 Processing Element", "Raghav"),
    ("section_3_2_array.md", "3.2 Systolic Array", "Ranjeet"),
    ("section_3_3_buffers_and_output.md", "3.3 Input Buffers and Output Collector", "Abhijeet"),
    ("section_3_4_controller_and_top.md", "3.4 Controller and Top Level", "Parrv"),
    ("section_4_verification.md", "4. Verification", "Malhar + Parrv"),
    ("section_5_performance.md", "5. Performance", "Malhar"),
    ("section_6_synthesis.md", "6. Synthesis", "Ranjeet"),
    ("section_7_conclusion.md", "7. Conclusion and Future Work", "Parrv"),
]

TITLE = f"""---
title: "Systolic Array Matrix Multiplication Accelerator"
subtitle: "Modern Computer Architecture - Project 12"
author: "Parrv, Raghav, Ranjeet, Abhijeet, Malhar"
date: "{date.today():%d %B %Y}"
---

## Abstract

We present a 4x4 output-stationary systolic array that multiplies 8-bit signed matrices with
32-bit signed accumulators, written in synthesizable Verilog-2005. Skewed rows of A and columns
of B flow through a grid of 16 multiply-accumulate processing elements while a Moore controller
sequences clear, compute and drain phases. One multiplication completes in 11 cycles, against 64
for a one-MAC sequential baseline (5.82x), and the design matches a NumPy golden model on all 10
test cases. FPGA resource usage and maximum frequency are reported for both designs.

"""


def main() -> None:
    parts, todos = [TITLE], []
    for fname, title, owner in SECTIONS:
        path = HERE / fname
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip() + "\n")
        else:
            parts.append(f"# {title}\n\n> TODO ({owner}): `docs/report/{fname}` has not been written yet.\n")
            todos.append(f"{fname} ({owner})")
        parts.append("\n\\newpage\n")
    out = HERE / "final_report.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}")

    inline = [l.strip() for l in out.read_text(encoding="utf-8").splitlines() if "TODO" in l]
    print(f"missing sections: {', '.join(todos) if todos else 'none'}")
    print(f"TODO lines in report: {len(inline)}")
    for l in inline:
        print("  -", l[:110])

    if shutil.which("pandoc"):
        for ext in ("docx", "html"):
            target = HERE / f"final_report.{ext}"
            args = ["pandoc", str(out), "-o", str(target), "--resource-path", str(HERE)]
            if ext == "html":
                args += ["--standalone", "--embed-resources", "--mathml"]
            res = subprocess.run(args, capture_output=True, text=True)
            print(f"wrote {target}" if res.returncode == 0 else f"pandoc {ext} failed: {res.stderr[:200]}")
    else:
        print("pandoc not installed: only final_report.md was written")


if __name__ == "__main__":
    main()
