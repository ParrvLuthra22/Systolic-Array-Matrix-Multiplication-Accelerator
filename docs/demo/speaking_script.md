# 10-minute live demo: systolic array matrix multiplication

Eight slides, following Prompt 9B. Timing totals 10 minutes. The performance figures are 11 systolic cycles, 64 sequential cycles, 5.82x end-to-end speed-up, and 10/10 golden-model tests passed.

## Slide 1 — Matrix multiplication in AI (1:00)

**Speaker:** Parrv

**Show:** A simple 4×4 matrix multiplication example and the 64 individual MAC operations.

**Say:** “Matrix multiplication is a core operation in many AI workloads. For two 4×4 matrices, each of the 16 output elements is a dot product with four multiply-add steps. A single MAC unit performs those 64 operations one after another. Our project explores how a grid of processing elements can perform many of them in parallel.”

## Slide 2 — Systolic array dataflow (1:10)

**Speaker:** Parrv

**Show:** A 4×4 PE grid, with A values entering from the left and B values from the top.

**Say:** “Each PE keeps one output accumulator. A values move right, and B values move down. The inputs are staggered so matching A and B values reach the same PE on the same cycle. Each PE then adds their product to its local accumulator.”

## Slide 3 — Accelerator blocks (1:10)

**Speaker:** Parrv

**Show:** The system diagram: input buffer and skew, controller, PE array, output collector, and host load/read ports.

**Say:** “The input buffer stores both matrices and produces the skewed edge values. The controller clears the accumulators, runs compute and drain cycles, and signals completion. The array forms all output values, and the output collector lets the host read one result at a time.”

## Slide 4 — Processing element (1:20)

**Speaker:** Raghav

**Show:** `pe_waveform.png` with `a_in`, `b_in`, `a_out`, `b_out`, `acc`, `clear`, and `en` visible. Point to signed MAC accumulation, clear, and pass-through.

**Say:** “This PE has a signed multiplier, an accumulator, and two registered pass-through outputs. The pass-through registers advance every clock, even when accumulation is disabled, so the array data keeps moving. Reset clears all state. Clear takes priority over enable, and enable controls whether the signed product is added. The directed checks include negative operands, the input extremes, clear priority, accumulator hold, and one-cycle forwarding.”

## Slide 5 — Skew and wavefront (1:10)

**Speaker:** Abhijeet, then Ranjeet

**Show:** `array_wavefront.png` and `skew_staircase.png`, showing the array wavefront and input-buffer row/column delays.

**Say:** “Row i of A is delayed by i cycles, and column j of B is delayed by j cycles. This makes A[i][k] and B[k][j] meet at PE(i,j) together. The waveform shows values advancing across rows and down columns as a diagonal wavefront.”

## Slide 6 — Full-system verification (1:20)

**Speaker:** Parrv

**Show:** `top_run.png` with the full-system run phases, `done`, and the 11-cycle count, alongside the `make test` summary.

**Say:** “The golden-model suite has 10 test cases, including directed zero and signed-extreme cases and random matrices. The full-system simulation reports all 10 tests passing. Each systolic run completes in 11 cycles from start through clear, compute, and drain.”

## Slide 7 — Cycle comparison (1:20)

**Speaker:** Malhar

**Show:** The 11 vs 64 cycle comparison and `speedup.png`, whose 4×4 point is 5.82×.

**Say:** “The sequential baseline uses one MAC and takes 64 cycles. The systolic design takes 11 cycles including the clear cycle. Dividing 64 by 11 gives a 5.82x end-to-end speed-up. The comparison comes from the project’s verified cycle counts.”

## Slide 8 — Vivado synthesis (1:30)

**Speaker:** Ranjeet

**Show:** Vivado 2026.1 results for `xc7a35tcpg236-1` at a 100 MHz target:

| Design | LUT | FF | DSP | BRAM | WNS | Fmax |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `systolic_top` | 1,940 | 987 | 0 | 0 | −0.057 ns | 99.4 MHz |
| `sequential_mac` | 390 | 825 | 0 | 0 | −0.537 ns | 94.9 MHz |

**Say:** “For the xc7a35tcpg236-1 at a 100 megahertz target, Vivado 2026.1 reports 1,940 LUTs and 987 flip-flops for the systolic design, versus 390 LUTs and 825 flip-flops for the sequential MAC. Both use zero DSPs and BRAMs. The reported per-multiply delay is 110.6 nanoseconds versus 674.4 nanoseconds, so the systolic design is 6.10 times faster at about five times the LUT count. WNS is minus 0.057 nanoseconds for systolic and minus 0.537 nanoseconds for sequential; reported Fmax is 99.4 and 94.9 megahertz, respectively.”
