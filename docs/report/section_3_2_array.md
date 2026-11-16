# Section 3.2: Systolic Array

**Author:** Ranajeet

**Files:** `rtl/systolic_array.v`, `tb/tb_array.v`, `tb/wave_array.surfer`

## Purpose

`systolic_array` connects N × N = 16 processing elements into a 4×4 output-stationary grid. Rows of A enter from the left edge and move right one PE per clock. Columns of B enter from the top edge and move down one PE per clock. PE(i,j) keeps C[i][j] in its own accumulator, and all 16 accumulators are exposed on one flattened output bus.

## Interface

| Port | Direction | Width | Meaning |
|---|---|---:|---|
| `clk` | Input | 1 | Rising-edge clock, shared by all PEs |
| `rst` | Input | 1 | Synchronous, active-high reset, shared by all PEs |
| `clear` | Input | 1 | Clears all 16 accumulators |
| `en` | Input | 1 | Enables accumulation in all 16 PEs |
| `a_left` | Input | 32 (N·DW) | Left-edge inputs; row i uses `a_left[i*8 +: 8]` |
| `b_top` | Input | 32 (N·DW) | Top-edge inputs; column j uses `b_top[j*8 +: 8]` |
| `c_flat` | Output | 512 (N·N·AW) | All results; C[i][j] is `c_flat[(i*4+j)*32 +: 32]` |

Parameters: `N = 4`, `DW = 8` (signed inputs), `AW = 32` (signed accumulators).

## How it works

**Grid wiring.** Two `generate` loops (`g_row[i].g_col[j]`) place 16 `pe` instances. Two 2-D wire arrays carry data between neighbours:

- `a_bus[i][j]` (i = 0..3, j = 0..4) is the A value entering PE(i,j) from the left.
- `b_bus[i][j]` (i = 0..4, j = 0..3) is the B value entering PE(i,j) from above.

The edges are tied to the inputs: `a_bus[i][0] = a_left[i*8 +: 8]` and `b_bus[0][j] = b_top[j*8 +: 8]`. Each PE(i,j) reads `a_bus[i][j]` and `b_bus[i][j]`, drives its registered `a_out` onto `a_bus[i][j+1]` (the PE to its right) and its registered `b_out` onto `b_bus[i+1][j]` (the PE below), and drives its accumulator onto `c_flat[(i*4+j)*32 +: 32]`. The outputs of the last column (`a_bus[i][4]`) and last row (`b_bus[4][j]`) are unused, and synthesis removes them.

**Timing.** Because `a_out` and `b_out` are registers, a value moves exactly one PE per clock. A[i][k] takes j clocks to reach column j, and B[k][j] takes i clocks to reach row i. With the input skew from Section 3.3 (row i delayed by i cycles, column j by j cycles), the pair A[i][k] and B[k][j] meets in PE(i,j) at cycle t = i + j + k. The first product happens in PE(0,0) at t = 0, and the last happens in PE(3,3) at t = 3N − 3 = 9. This is why `en` must stay high for 10 cycles (t = 0..9).

The array has no control logic of its own. `clear` and `en` come from the controller and are broadcast to every PE.

## Verification

`tb/tb_array.v` drives the array directly, without the input buffer or controller, so that array wiring bugs are isolated from skew or FSM bugs. The testbench applies the skew itself (`a_left` slice i = A[i][t−i], `b_top` slice j = B[t−j][j], or 0 outside the matrix). For each case it pulses `clear` for one clock, then holds `en = 1` for t = 0..9, then sets `en = 0` and compares all 16 accumulators with a reference product computed by three nested loops. Inputs change on the falling clock edge.

| Case | A | B | What it checks | Result |
|---|---|---|---|---|
| 1 | Identity | Values 1..16 | Each B value reaches the correct PE (C = B) | 16/16 PASS |
| 2 | Values 1..16 | All ones | Each A row reaches every column (C[i][j] = row sum of A) | 16/16 PASS |
| 3 | Random signed 8-bit (seed 2026) | Random signed 8-bit | Signed products across the whole grid, e.g. C[0][3] = −34,780, C[2][2] = 18,448 | 16/16 PASS |

Final output with the team's `rtl/pe.v` (Icarus Verilog 13.0, `make array`):

```
CASE 1 PASSED (16/16)
CASE 2 PASSED (16/16)
CASE 3 PASSED (16/16)
ARRAY TESTS PASSED: 48/48 element checks
```

To confirm that the testbench really detects propagation errors, `b_out` was temporarily mis-wired; 36 of the 48 checks then failed. The array also passes inside the full design: `make top` reports `ALL 10 TESTS PASSED` with `cycle_count = 11` for every golden-model test.

## Waveform caption

**Figure: `docs/screenshots/array_wavefront.png`.** Data propagation in the 4×4 array (`tb_array` case 2: A = 1..16, B = all ones). The top group shows `a_out` of PE(0,0)..PE(0,3): the values 1, 2, 3, 4 appear at each PE one clock after the PE to its left (A moving right). The middle group shows `b_out` of PE(0,0)..PE(3,0): each value appears one clock later at each PE further down (B moving down). The bottom group shows the accumulators: PE(0,0) builds C[0][0] = 1 → 3 → 6 → 10 and finishes at t = 3; PE(3,3) builds C[3][3] = 13 → 27 → 42 → 58 and finishes at t = 9. This shift of six cycles between the corners is the diagonal wavefront. The view can be reopened with `surfer wave_array.vcd -c tb/wave_array.surfer`.
