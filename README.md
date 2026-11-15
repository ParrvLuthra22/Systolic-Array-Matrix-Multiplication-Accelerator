# Systolic Array Matrix Multiplication Accelerator

Modern Computer Architecture, Project 12: a systolic-array matrix multiplication accelerator written in Verilog, with a Python golden model, per-module testbenches, a sequential MAC baseline for comparison, and synthesis reports.

## Folder layout

| Folder | Contents |
|---|---|
| `rtl/` | Synthesizable Verilog (PE, array, buffers, controller, top, sequential MAC) |
| `tb/` | Testbenches, one per module |
| `model/` | Python golden model and test-vector generation |
| `tests/` | Test vectors and test scripts |
| `synth/` | Synthesis scripts; `synth/reports/` holds utilization/timing reports |
| `docs/report/` | Project report |
| `docs/screenshots/` | Waveform and tool screenshots |
| `docs/demo/` | Demo material |

## Team ownership

| Member | Files |
|---|---|
| Parrv | `rtl/controller.v`, `rtl/systolic_top.v`, `tb/tb_controller.v`, `tb/tb_top.v` |
| Raghav | `rtl/pe.v`, `tb/tb_pe.v` |
| Ranjeet | `rtl/systolic_array.v`, `tb/tb_array.v`, `synth/*` |
| Abhijeet | `rtl/input_buffer.v`, `rtl/output_collector.v`, `tb/tb_input_buffer.v`, `tb/tb_output_collector.v` |
| Malhar | `model/*`, `tests/*`, `rtl/sequential_mac.v`, `tb/tb_sequential.v` |

Rule: never edit a file owned by someone else. If their file has a bug, write a bug report instead.

## Running simulations

Requires [Icarus Verilog](https://steveicarus.github.io/iverilog/) (`iverilog`, `vvp`) and Python 3.

| Command | What it does |
|---|---|
| `make pe` | Processing element testbench |
| `make array` | Systolic array (PEs + array) testbench |
| `make buf` | Input buffer testbench |
| `make out` | Output collector testbench |
| `make ctrl` | Controller testbench |
| `make top` | Full top-level testbench (all modules) |
| `make seq` | Sequential MAC baseline testbench |
| `make test` | Run all unit, integration, and baseline simulations |
| `make vectors` | Generate test vectors with `model/golden_model.py` |
| `make test` | Run every testbench in order |
| `make report` | Rebuild `docs/report/final_report.md` (+ `.docx`/`.html` if pandoc is installed) |
| `make diagram` | Redraw `docs/block_diagram.svg`/`.png` (needs `pip install reportlab`) |
| `make clean` | Delete `sim_*` and `*.vcd` |

## Results

| Metric (4x4) | Systolic array | Sequential baseline |
|---|---:|---:|
| Cycles, `start` to `done` | 11 (1 clear + 7 compute + 3 drain) | 64 |
| Speed-up | 5.82x | 1x |
| Average MACs per compute cycle | 6.4 | 1 |
| Golden-model tests | 10/10 pass | 10/10 pass |

FPGA resources and Fmax: run `vivado -mode batch -source synth/run_vivado.tcl` (Windows/Linux); results land in `synth/reports/summary.txt`.

## Viewing waveforms

Run the matching `make` target first, then open the VCD with [Surfer](https://surfer-project.org) and a view file:

| View | Command |
|---|---|
| Full system (demo) | `surfer wave_tb_top.vcd -c docs/demo/top_demo.surfer` |
| Array wavefront | `surfer wave_array.vcd -c tb/wave_array.surfer` |
| Input skew staircase | `surfer wave_input_buffer.vcd -c tb/wave_input_buffer.surfer` |

## Report

Each member writes `docs/report/section_*.md`; `make report` stitches them into `docs/report/final_report.md` and lists any missing section. Architecture diagram: `docs/block_diagram.png`.
