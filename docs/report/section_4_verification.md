# Section 4: Verification

**Authors:** Malhar (golden model, baseline), Parrv (full-system test)

## 4.1 Method

1. `model/golden_model.py` (NumPy, seed 42) generates 10 test cases and computes the expected product with 64-bit integers. Each case is written as three row-major hex files: `tests/test_XX_A.hex` and `_B.hex` (8-bit two's complement) and `_C.hex` (32-bit two's complement).
2. Every module has a self-checking unit testbench that prints PASS/FAIL itself.
3. `tb_top` loads each case through the accelerator's load port, pulses `start`, waits for `done` (500-cycle timeout), reads all 16 results through `rd_row`/`rd_col` and compares them with `_C.hex`. `tb_sequential` does the same for the one-MAC baseline.
4. All testbenches change inputs on the falling clock edge to avoid races, and run from the repo root (`make <target>`).

## 4.2 Unit tests

| Testbench | Module | What it checks | Result |
|---|---|---|---|
| `tb_pe` | `pe` | Reset, signed MAC (68; mixed signs), extremes (64,516 / 65,536 / -65,024), `clear` priority, `en` hold, pass-through timing | 27 checks pass |
| `tb_array` | `systolic_array` | Skewed inputs driven by the testbench; identity x 1..16, 1..16 x ones, random signed | 48/48 element checks pass |
| `tb_input_buffer` | `input_buffer` | Skew staircase for t = 0..9 against the expected table; zeros when `feed_en = 0` | All checks pass |
| `tb_output_collector` | `output_collector` | All 16 read positions, including negative values | All checks pass |
| `tb_controller` | `controller` | State sequence and signal lengths (1, 7, 10, 11 cycles), back-to-back runs, mid-run reset | 31 checks pass |

## 4.3 Full-system and baseline tests

| Test | Case | Expected C[0][0] | systolic_top | Cycles | sequential_mac | Cycles |
|---|---|---:|---|---:|---|---:|
| test_00 | identity x random | -106 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_01 | all zeros x all zeros | 0 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_02 | all 127 x all 127 | 64,516 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_03 | all -128 x all -128 | 65,536 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_04 | all 127 x all -128 | -65,024 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_05 | random x random | -15,004 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_06 | random x random | -5,958 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_07 | random x random | -16,154 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_08 | random x random | 3,538 | PASS (16/16) | 11 | PASS (16/16) | 64 |
| test_09 | random x random | 14,421 | PASS (16/16) | 11 | PASS (16/16) | 64 |

Both designs print **ALL 10 TESTS PASSED** (160 of 160 result elements each). Tests 02-04 exercise the extreme products: the largest positive result (65,536) and the most negative one (-65,024). They confirm that signed arithmetic is correct end to end. Test 00 checks the data path element by element, since C must equal B exactly.

All results above come from the final RTL on `main` (`make test`, Icarus Verilog), with every module written by its owner.

## 4.4 Waveform evidence

| Figure | What it shows | Owner |
|---|---|---|
| `docs/screenshots/array_wavefront.png` | A moving right and B moving down one PE per clock (diagonal wavefront) | Ranjeet |
| `docs/screenshots/skew_staircase.png` | `a_left`/`b_top` staircase for t = 0..9 | Abhijeet |
| `docs/screenshots/pe_waveform.png` | Signed MAC, `clear`, `en` hold, pass-through | Raghav |
| `docs/screenshots/top_run.png` (view: `docs/demo/top_demo.surfer`) | Load, start, 11 busy cycles, done, read-out | Parrv |
