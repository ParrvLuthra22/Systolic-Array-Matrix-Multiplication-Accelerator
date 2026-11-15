# Section 7: Conclusion and Future Work

**Author:** Parrv

## 7.1 Conclusion

We designed, verified and compared a 4×4 output-stationary systolic array for signed 8-bit matrix multiplication. Skewed operands enter from the left and top edges, every PE performs one multiply-accumulate per clock, and each result stays in its own PE. A Moore controller sequences clear, feed and drain phases, so one multiplication takes 11 cycles from `start` to `done`, of which 10 are compute cycles (3N − 2).

All modules are synthesizable Verilog-2005 with self-checking testbenches. The full accelerator matches the NumPy golden model on all 10 test cases, including the extreme products at the limits of the 8-bit range. Against a one-MAC sequential design with the same interface (64 cycles), the array is **5.82x faster** end to end and averages 6.4 MACs per compute cycle; up to 12 of its 16 PEs are active in the same cycle. On the Basys 3's Artix-7 FPGA (Vivado, Section 6) the systolic design reaches 99.4 MHz against 94.9 MHz for the baseline, so one multiplication takes 110.6 ns against 674.4 ns: a **6.10× wall-clock speed-up**. The cost is hardware: about 5× the LUTs (1,940 against 390), because Vivado builds the 16 multipliers from LUTs and carry chains.

## 7.2 Limitations

- Loading is serial (one element per clock, 32 cycles for A and B), which dominates the end-to-end time for a single 4x4 multiply.
- The array computes one fixed-size 4×4 product; larger matrices would need tiling by an external controller.
- Inputs are 8-bit integers; there is no saturation or scaling for quantized neural-network layers.

## 7.3 Future work

- **Larger and parameterised arrays:** the RTL is already parameterised by `N`; an 8x8 or 16x16 array would raise the speed-up to about 22x or 87x (Section 5).
- **Higher clock rate:** register the input buffer's outputs to break the critical path (feed counter → skew multiplexer → multiplier → accumulator), trading one cycle of latency for timing margin above 100 MHz.
- **Use the DSP blocks:** mark the PE multiply-accumulate with Vivado's `use_dsp` attribute so the 16 multipliers move into DSP48E1 slices instead of LUTs.
- **Overlap load and compute:** double-buffer A and B so the next matrices load while the current product is computed.
- **Weight-stationary dataflow:** keep one matrix inside the PEs, as TPU-style accelerators do, to reuse weights across many input batches.
- **Tiling:** add a controller that multiplies large matrices block by block.
- **FPGA board demo:** wrap `systolic_top` with a UART or switch/LED interface to run on a Basys 3 board.
