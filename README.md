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
| `make vectors` | Generate test vectors with `model/golden_model.py` |
| `make clean` | Delete `sim_*` and `*.vcd` |
