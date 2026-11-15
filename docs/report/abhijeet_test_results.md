# Test Execution and Verification Report: Input Buffers & Output Collector

**Author:** Abhijeet  
**Branch:** `abhijeet-buffers`  
**Date:** November 15, 2026  
**Simulator:** Icarus Verilog 13.0 (stable) (`iverilog -g2012`, `vvp`)  

---

## 1. Summary of Verification

Both modules owned by Abhijeet (`rtl/input_buffer.v` and `rtl/output_collector.v`) were compiled, simulated, and validated against self-checking testbenches. All test vectors executed with **0 errors**.

| Module | Testbench | Status | Key Criteria Validated |
| :--- | :--- | :---: | :--- |
| `input_buffer.v` | `tb/tb_input_buffer.v` | **PASS (0 errors)** | Synchronous matrix load; `feed_en=0` zero gating; cycle-by-cycle staircase skew matching Section 3.2. |
| `output_collector.v` | `tb/tb_output_collector.v` | **PASS (0 errors)** | Combinational 16:1 mux; 32-bit signed extraction across all 16 locations including positive, negative, and extreme limits. |

---

## 2. Test 1: Input Buffer & Skew Logic Verification

### 2.1 Execution Command
```bash
make buf
# Equivalent to:
# iverilog -g2012 -o sim_buf rtl/input_buffer.v tb/tb_input_buffer.v && vvp sim_buf
```

### 2.2 Terminal Output Log
```text
iverilog -g2012 -o sim_buf rtl/input_buffer.v tb/tb_input_buffer.v
vvp sim_buf
VCD info: dumpfile wave_input_buffer.vcd opened for output.
==================================================
   TESTBENCH: input_buffer and skew logic
==================================================
[INFO] Loading Matrix A and Matrix B into input_buffer...
[INFO] Checking feed_en = 0 produces all zeros...
[INFO] Testing skewed outputs for t = 0..9 with feed_en = 1...
t=0: a_left = 10 00 00 00   b_top = a0 00 00 00
t=1: a_left = 11 20 00 00   b_top = a4 a1 00 00
t=2: a_left = 12 21 30 00   b_top = a8 a5 a2 00
t=3: a_left = 13 22 31 40   b_top = ac a9 a6 a3
t=4: a_left = 00 23 32 41   b_top = 00 ad aa a7
t=5: a_left = 00 00 33 42   b_top = 00 00 ae ab
t=6: a_left = 00 00 00 43   b_top = 00 00 00 af
t=7: a_left = 00 00 00 00   b_top = 00 00 00 00
t=8: a_left = 00 00 00 00   b_top = 00 00 00 00
t=9: a_left = 00 00 00 00   b_top = 00 00 00 00
--------------------------------------------------
PASS: All input_buffer and skew tests PASSED successfully.
==================================================
tb/tb_input_buffer.v:192: $finish called at 370000 (1ps)
```

### 2.3 Verification Observations
1. **Reset & Synchronous Load:** Matrices $A$ and $B$ loaded successfully into row-major memories without race conditions.
2. **Inactivation Check:** Tested with `feed_en = 0` for all $t \in [0, 9]$. Confirmed both `a_left` and `b_top` outputs remain strictly `32'h00000000`.
3. **Staircase Skew:** Values injected into row $i$ and column $j$ strictly followed the delay rule $t = i + j + k$, matching the reference simulation table in Section 3.2.

---

## 3. Test 2: Output Collector Verification

### 3.1 Execution Command
```bash
make out
# Equivalent to:
# iverilog -g2012 -o sim_out rtl/output_collector.v tb/tb_output_collector.v && vvp sim_out
```

### 3.2 Terminal Output Log
```text
iverilog -g2012 -o sim_out rtl/output_collector.v tb/tb_output_collector.v
vvp sim_out
VCD info: dumpfile wave_output_collector.vcd opened for output.
==================================================
   TESTBENCH: output_collector
==================================================
[INFO] Reading all 16 matrix positions through output_collector...
PASS: C[0][0] =          0 (hex: 0x00000000)
PASS: C[0][1] =      12345 (hex: 0x00003039)
PASS: C[0][2] =     -65024 (hex: 0xffff0200)
PASS: C[0][3] =      64516 (hex: 0x0000fc04)
PASS: C[1][0] =         -1 (hex: 0xffffffff)
PASS: C[1][1] =      65536 (hex: 0x00010000)
PASS: C[1][2] =       -128 (hex: 0xffffff80)
PASS: C[1][3] =        255 (hex: 0x000000ff)
PASS: C[2][0] =     -32768 (hex: 0xffff8000)
PASS: C[2][1] =     999999 (hex: 0x000f423f)
PASS: C[2][2] =     -54321 (hex: 0xffff2bcf)
PASS: C[2][3] =         42 (hex: 0x0000002a)
PASS: C[3][0] =          7 (hex: 0x00000007)
PASS: C[3][1] =     -16384 (hex: 0xffffc000)
PASS: C[3][2] =       1024 (hex: 0x00000400)
PASS: C[3][3] =        -99 (hex: 0xffffff9d)
--------------------------------------------------
PASS: All output_collector tests PASSED successfully.
==================================================
tb/tb_output_collector.v:92: $finish called at 16000 (1ps)
```

### 3.3 Verification Observations
1. All 16 positions ($4 \times 4$) were accessed combinatorially using `rd_row` and `rd_col`.
2. Negative two's-complement numbers (e.g. `-65024`, `-54321`, `-128`, `-1`) and maximum positive bounds (`+65536`, `+64516`) were faithfully preserved across the bit-slicing boundary without unintended truncation or sign corruption.

---

## 4. Waveform Visualization Setup

The simulation generated VCD files in the repo root:
- `wave_input_buffer.vcd`
- `wave_output_collector.vcd`

To view the staircase waveform in Surfer:
```bash
surfer wave_input_buffer.vcd -c tb/wave_input_buffer.surfer
```
To view in GTKWave:
```bash
gtkwave wave_input_buffer.vcd
```
Signals to view: `clk`, `rst`, `feed_en`, `t`, `a_row0..3`, and `b_col0..3`.
