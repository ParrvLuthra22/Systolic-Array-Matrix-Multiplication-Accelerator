# Project 12: Systolic Array Matrix Multiplication Accelerator
## Abhijeet's Implementation & Verification Log

**Author:** Abhijeet  
**Branch:** `abhijeet-buffers`  
**Role:** Input Buffers, Skew Logic, and Output Collector  
**Date:** November 15, 2026  

---

## 1. Modules Implemented

### 1.1 `rtl/input_buffer.v`
* **What it does:**
  * Synchronously stores $4 \times 4$ matrices $A$ and $B$ (8-bit signed two's-complement numbers, $-128 \dots 127$) in internal memories using row-major order: `index = row * 4 + col`.
  * Computes the combinational "staircase" skew for array feeding:
    * Row $i$ of Matrix $A$ is delayed by $i$ clock cycles: $A[i][t - i]$ for $0 \le t - i < 4$.
    * Column $j$ of Matrix $B$ is delayed by $j$ clock cycles: $B[t - j][j]$ for $0 \le t - j < 4$.
    * When `feed_en = 0` or outside the valid window, outputs evaluate strictly to `0`.
* **Why this implementation:**
  * For output-stationary systolic arrays, $\text{PE}(i, j)$ accumulates $C[i][j] = \sum_k A[i][k] \cdot B[k][j]$.
  * Because $A[i][k]$ travels $j$ steps right and $B[k][j]$ travels $i$ steps down, delaying row $i$ by $i$ cycles and column $j$ by $j$ cycles ensures that both inputs meet at $\text{PE}(i, j)$ at cycle $t = i + j + k$.
  * Doing this combinationally via index arithmetic rather than physical shift registers avoids unnecessary flip-flop area while keeping control fully deterministic.

### 1.2 `rtl/output_collector.v`
* **What it does:**
  * Slices the 512-bit flattened bus `c_flat` ($16 \times 32$-bit signed accumulators) to extract individual matrix element $C[\text{rd\_row}][\text{rd\_col}]$.
* **Why this implementation:**
  * Implemented as a pure combinational 16:1 multiplexer.
  * Provides **0 clock cycle read latency**: once the accelerator reaches `DONE`, the host or testbench reads any accumulated value immediately without pipeline stalls.

---

## 2. Test Execution & Verified Results

Simulations were performed using **Icarus Verilog 13.0 (stable)** (`iverilog -g2012` and `vvp`).

### 2.1 Test 1: Input Buffer & Skew Logic (`tb/tb_input_buffer.v`)
* **Command:**
  ```bash
  make buf
  # or: iverilog -g2012 -o sim_buf rtl/input_buffer.v tb/tb_input_buffer.v && vvp sim_buf
  ```
* **Status:** **PASS (0 errors)**
* **Execution Log:**
```text
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
```
* **Key Verifications:**
  * Confirmed that `feed_en = 0` forces all outputs to 0 across cycles $t = 0 \dots 9$.
  * Confirmed the staircase delay pattern matches Table 3.2 from the project specification across all 10 cycles.

---

### 2.2 Test 2: Output Collector Read Mux (`tb/tb_output_collector.v`)
* **Command:**
  ```bash
  make out
  # or: iverilog -g2012 -o sim_out rtl/output_collector.v tb/tb_output_collector.v && vvp sim_out
  ```
* **Status:** **PASS (0 errors)**
* **Execution Log:**
```text
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
```
* **Key Verifications:**
  * Confirmed all 16 matrix locations are addressable combinatorially via `rd_row` and `rd_col`.
  * Verified correct two's complement sign preservation for negative extremes (`-65024`, `-54321`, `-32768`, `-1`) and positive extremes (`+64516`, `+65536`).

---

## 3. Waveform Artifacts Generated

* `wave_input_buffer.vcd`: Full VCD waveform of input buffer and skew timing.
* `wave_output_collector.vcd`: Full VCD waveform of output collector read multiplexing.
* `tb/wave_input_buffer.surfer`: Configuration script to visualize the staircase waveform in Surfer:
  ```bash
  surfer wave_input_buffer.vcd -c tb/wave_input_buffer.surfer
  ```

---

## 4. Hand-off Readiness
* **Parrv (`systolic_top.v`):** `rtl/input_buffer.v` and `rtl/output_collector.v` are verified and ready for top-level instantiation.
* **Ranjeet (`systolic_array.v`):** Interface verified to provide `a_left[31:0]` and `b_top[31:0]` in exact format required by the PE grid.
