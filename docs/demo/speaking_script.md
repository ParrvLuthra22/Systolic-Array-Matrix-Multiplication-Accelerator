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

**Show:** The input skew staircase and `array_wavefront.png`.

**Say:** “Row i of A is delayed by i cycles, and column j of B is delayed by j cycles. This makes A[i][k] and B[k][j] meet at PE(i,j) together. The waveform shows values advancing across rows and down columns as a diagonal wavefront.”

## Slide 6 — Full-system verification (1:20)

**Speaker:** Parrv

**Show:** Terminal output from `make test`, especially the `tb_top` summary and cycle counts.

**Say:** “The golden-model suite has 10 test cases, including directed zero and signed-extreme cases and random matrices. The full-system simulation reports all 10 tests passing. Each systolic run completes in 11 cycles from start through clear, compute, and drain.”

## Slide 7 — Cycle comparison (1:20)

**Speaker:** Malhar

**Show:** A comparison bar or table: systolic 11 cycles; sequential 64 cycles; 5.82x end-to-end speed-up.

**Say:** “The sequential baseline uses one MAC and takes 64 cycles. The systolic design takes 11 cycles including the clear cycle. Dividing 64 by 11 gives a 5.82x end-to-end speed-up. The comparison comes from the project’s verified cycle counts.”

## Slide 8 — Vivado synthesis (1:30)

**Speaker:** Ranjeet

**Show:** Vivado utilization and timing reports for both designs. Display LUT, FF, DSP, BRAM, WNS, and Fmax only after inserting the measured report values.

**Say:** “This slide compares the hardware cost and timing of the two implementations. Show the actual Vivado resource counts and timing for the selected board target. Read those values directly from the synthesis reports; the current project materials do not contain measured resource or frequency results.”
