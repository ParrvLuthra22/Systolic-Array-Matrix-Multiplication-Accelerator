# Section 6: Synthesis

**Author:** Ranjeet

**Files:** `synth/run_vivado.tcl`, `synth/constraints.xdc`, `synth/reports/*`, `docs/screenshots/vivado_utilization.png`

## Setup

Both designs were synthesized and implemented with AMD Vivado v2026.1 (lin64) using the batch script `synth/run_vivado.tcl`:

- **Part:** `xc7a35tcpg236-1` (Artix-7, Basys 3 board).
- **Clock constraint:** `create_clock -period 10.000 -name clk [get_ports clk]` (100 MHz).
- **Flow:** `synth_design -mode out_of_context` → `opt_design` → `place_design` → `route_design`, then `report_utilization` and `report_timing_summary`.
- **Out-of-context mode:** we only need resource and timing numbers, so no pin assignment (`PACKAGE_PIN`/`IOSTANDARD`) or board wrapper is required.
- **Designs:** `systolic_top` (controller, input buffer, 4×4 array of PEs, output collector) and the one-MAC baseline `sequential_mac`. Both have the same ports.

## Results

| Design | LUTs | FFs | DSPs | BRAM | WNS (ns) | Fmax (MHz) |
|---|---:|---:|---:|---:|---:|---:|
| `systolic_top` | 1,940 (9.33%) | 987 (2.37%) | 0 | 0 | −0.057 | 99.4 |
| `sequential_mac` | 390 (1.88%) | 825 (1.98%) | 0 | 0 | −0.537 | 94.9 |

Percentages are of the xc7a35t (20,800 LUTs, 41,600 FFs). Fmax = 1000 / (10 − WNS) MHz.

### Where the systolic resources go

| Module | LUTs | FFs | Notes |
|---|---:|---:|---|
| `u_array` (systolic_array, 16 PEs) | 1,398 | 704 | 76–108 LUTs per PE |
| `u_buf` (input_buffer) | 182 | 256 | A and B storage: 2 × 16 × 8 bits |
| `u_ctrl` (controller) | 405 | 27 | 3-bit state + 8-bit `t` + 16-bit `cycle_count` |

The flip-flop counts match the RTL exactly:

- **Array:** 16 accumulators × 32 bits = 512 FFs, plus 192 FFs of pass-through registers. Vivado removed the `a_out` registers of column 3 and the `b_out` registers of row 3 because nothing reads them. This is why the PEs on the right and bottom edges have 40 or 32 FFs instead of 48.
- **Controller:** 27 FFs = 3 (state) + 8 (`t`) + 16 (`cycle_count`).

The `output_collector` is pure combinational logic (a 16:1 × 32-bit mux). Vivado merged it into the neighbouring logic during optimization, so it has no row of its own; the array row includes the 64 F7 and 32 F8 muxes it uses. The controller's 405 LUTs are much more than the FSM itself needs. Most likely Vivado moved part of the `t`-dependent skew selection logic across the controller/buffer boundary. The per-module rows therefore don't add up exactly to the 1,940 total.

**No DSP blocks were used.** Vivado built every 8×8 signed multiplier from LUTs and carry chains (324 CARRY4 cells in `systolic_top`) instead of DSP48E1 slices. The team plan notes this can happen for small multipliers. These are the numbers Vivado reported.

## Timing analysis

Both designs miss the 10 ns target by less than 0.6 ns, so both run at about 95–100 MHz.

| | `systolic_top` | `sequential_mac` |
|---|---|---|
| WNS / TNS | −0.057 ns / −0.092 ns | −0.537 ns / −43.032 ns |
| Failing endpoints | 2 of 1,779 | 200 of 1,387 |
| Hold (WHS) | +0.170 ns (met) | +0.240 ns (met) |
| Critical path | `u_ctrl/t_reg[1]` → skew select in `input_buffer` → PE(0,1) multiply and add → `acc_reg[29]` | `k_reg[1]` → A/B memory read mux → multiply and add → `C_reg[8][29]` |
| Path delay | 10.035 ns, 16 logic levels (9 CARRY4) | 10.212 ns, 14 logic levels (7 CARRY4) |

In the systolic design the slowest path starts at the controller's `t` counter. `t` selects which A/B elements the input buffer outputs. That combinational value goes straight into a PE's multiplier and 32-bit adder in the same clock cycle. PE(0,1) is on this path because its `b_in` comes directly from `b_top`, not from another PE's register. Inside the array, every PE-to-PE link is registered, so the array itself is not the limit. The baseline's slowest path is similar: a 16-entry memory read selected by the `i`, `j`, `k` counters, then the multiplier and adder.

If the design had to meet exactly 100 MHz, registering the `input_buffer` outputs would cut the systolic critical path (at the cost of one extra cycle of latency). Alternatively, the clock constraint can be relaxed to 11 ns. Neither change was needed for this report.

## Performance per area

| | `systolic_top` | `sequential_mac` | Ratio |
|---|---:|---:|---:|
| Cycles per 4×4 multiply | 11 | 64 | 5.82× fewer |
| Fmax (MHz) | 99.4 | 94.9 | |
| Time per multiply (cycles × 1/Fmax) | 110.6 ns | 674.4 ns | **6.10× faster** |
| LUTs | 1,940 | 390 | 4.97× more |
| FFs | 987 | 825 | 1.20× more |

The systolic array uses about 5× the LUTs of the sequential design, mostly for its 16 multipliers instead of one. In return it is about 6× faster in wall-clock time, because it does up to 12 MACs per cycle at almost the same clock frequency. Both designs use under 10% of the smallest Artix-7 on the Basys 3, so a larger array (for example 8×8) would still fit.

## Screenshot caption

**Figure: `docs/screenshots/vivado_utilization.png`.** Vivado 2026.1 view of the routed `systolic_top` checkpoint on xc7a35tcpg236-1. The Device view shows the placed and routed design on the FPGA. The Utilization panel lists Slice LUTs, Slice Registers, F7/F8 muxes and slices per module: the 4×4 array (1,398 LUTs, 704 FFs), the input buffer (182 LUTs, 256 FFs) and the controller (405 LUTs, 27 FFs), for a total of 1,940 LUTs and 987 FFs.
