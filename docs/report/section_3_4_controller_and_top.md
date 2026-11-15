# Section 3.4: Controller and Top-Level Integration

**Author:** Parrv  
**Modules owned:** `rtl/controller.v`, `rtl/systolic_top.v`  
**Testbenches:** `tb/tb_controller.v`, `tb/tb_top.v`

## 1. Purpose

The **controller** is a Moore finite-state machine that sequences one matrix multiplication: it clears the accumulators, tells the input buffer which feed cycle `t` it is on, keeps the PEs accumulating until the last product has passed through the array, and reports completion and latency. **systolic_top** connects the controller, input buffer, systolic array and output collector into the accelerator.

## 2. Interfaces

### 2.1 `controller` (parameters `N = 4`, `TW = 8`)

| Port | Direction | Width | Meaning |
|---|---|---|---|
| `clk` | in | 1 | Clock, rising edge |
| `rst` | in | 1 | Synchronous, active-high reset |
| `start` | in | 1 | Starts a run; accepted in IDLE or DONE |
| `clear` | out | 1 | High in CLEAR: resets all accumulators |
| `feed_en` | out | 1 | High in COMPUTE: input buffer drives skewed data |
| `en` | out | 1 | High in COMPUTE and DRAIN: PEs accumulate |
| `busy` | out | 1 | High in CLEAR, COMPUTE and DRAIN |
| `done` | out | 1 | High in DONE until the next `start` |
| `t` | out | `TW` | Feed-cycle counter, 0..9 during COMPUTE and DRAIN |
| `cycle_count` | out | 16 | Busy cycles of the current run (ends at 11) |

### 2.2 `systolic_top` (parameters `N = 4`, `DW = 8`, `AW = 32`, `TW = 8`)

| Port | Direction | Width | Meaning |
|---|---|---|---|
| `clk`, `rst`, `start` | in | 1 | Clock, reset, start pulse |
| `load_en`, `load_sel` | in | 1 | Write one element; `load_sel` 0 = A, 1 = B |
| `load_row`, `load_col` | in | 2 | Element position (row-major) |
| `load_data` | in | 8, signed | Element value |
| `rd_row`, `rd_col` | in | 2 | Result to read |
| `rd_data` | out | 32, signed | `C[rd_row][rd_col]` (combinational) |
| `busy`, `done` | out | 1 | Status |
| `cycle_count` | out | 16 | Latency of the last run |

## 3. How it works

### 3.1 State machine

| State | Next state | Transition condition | `t` update | `cycle_count` update |
|---|---|---|---|---|
| IDLE | CLEAR | `start` | 0 | 0 |
| CLEAR | COMPUTE | always (1 cycle) | 0 | +1 |
| COMPUTE | DRAIN | `t == 2N-2` (6) | +1 | +1 |
| DRAIN | DONE | `t == 3N-3` (9) | +1 | +1 |
| DONE | CLEAR | `start` | 0 | 0 |

All outputs are decoded combinationally from the 3-bit state register (`clear = CLEAR`, `feed_en = COMPUTE`, `en = COMPUTE | DRAIN`, `busy = CLEAR | COMPUTE | DRAIN`, `done = DONE`), so they change exactly on state boundaries. `t` and `cycle_count` are registers. COMPUTE lasts 2N-1 = 7 cycles, the window in which some skewed input is non-zero; DRAIN lasts N-1 = 3 more cycles so the last operands reach PE(3,3). `en` therefore stays high for 10 cycles, through the final product at `t = 9`. A run takes 1 + 7 + 3 = **11 cycles**.

Accepting `start` in DONE lets back-to-back multiplications run without a reset, and CLEAR guarantees that each run starts from zero accumulators. Because `en` drops in DONE, the accumulators hold their results until the next `start`.

### 3.2 Integration

`systolic_top` instantiates `u_ctrl`, `u_buf`, `u_array` and `u_out` with named port connections and five internal nets:

| Net | From | To |
|---|---|---|
| `clear`, `en` | controller | systolic_array (all 16 PEs) |
| `feed_en`, `t` | controller | input_buffer |
| `a_left`, `b_top` (32 bits each) | input_buffer | systolic_array edges |
| `c_flat` (512 bits) | systolic_array | output_collector |

The load port goes straight to the input buffer, and `rd_data` comes straight from the output collector, so loading and reading add no extra latency.

## 4. Verification

**`tb_controller`** (self-checking, inputs change on negedge) runs the FSM three times: from IDLE, a second `start` directly from DONE, and a third run. On each run it checks that `clear` is high for exactly 1 cycle, `feed_en` for 7, `en` for 10 and `busy` for 11; that `t` counts 0..9; that `cycle_count` ends at 11; and that `done` is high with `busy`/`en` low at the end. It also checks idle behaviour without `start`, that `done` stays high until the next `start`, and that a reset in the middle of COMPUTE returns the FSM to IDLE. Result: **31 checks pass, "CONTROLLER TESTS PASSED"**.

**`tb_top`** runs the 10 golden-model test cases end to end through the real load and read ports; the results are in Section 4.

## 5. Figure captions

- *Figure 3.4.1: Controller waveform: `start`, `state`, `t`, `clear`, `feed_en`, `en`, `busy`, `done`, `cycle_count` for one run (open with `surfer wave_ctrl.vcd`).*
- *Figure 3.4.2: Full-system run of test_00 (open with `surfer wave_tb_top.vcd -c docs/demo/top_demo.surfer`): load phase, one-cycle `start`, 11 busy cycles with the skewed `a_left`/`b_top` staircase, C00 and C33 accumulating, `done`, then reading all 16 results.*
