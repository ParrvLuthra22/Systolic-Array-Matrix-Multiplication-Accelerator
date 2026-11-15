# Modern Computer Architecture — Project 12: Systolic Array Matrix Multiplication Accelerator (Verilog)

## Project Context

Course: Modern Computer Architecture (B.Tech CS&AI), Project 12:
"Systolic Array Matrix Multiplication Accelerator".
Team: Parrv, Raghav, Ranjeet, Abhijeet, Malhar.
We build a 4x4 output-stationary systolic array in Verilog that computes C = A x B
for 4x4 matrices, and compare it with a one-MAC sequential design.
TOOLS: synthesizable Verilog-2005. Simulate with Icarus Verilog (iverilog -g2012) and
view waveforms in GTKWave. Synthesis in Xilinx Vivado. Python 3 + numpy for the golden model.
PARAMETERS: N = 4 (array size), DW = 8 (signed inputs, -128..127),
AW = 32 (signed accumulators), TW = 8 (width of the cycle counter t).
CODING RULES
- Every .v file starts with `timescale 1ns/1ps. One module per file; file name = module name.
- One clock clk; all flip-flops on posedge clk; synchronous, active-high reset rst.
- Declare numeric data `signed`. Never mix signed and unsigned operands in one arithmetic
expression (Verilog then treats the whole expression as unsigned).
- rtl/ files: no initial blocks, no # delays, no $display. Those belong in tb/ only.
- Verilog-2005 has no array ports, so buses are flattened: element i of a vector bus is
bus[i*DW +: DW]; the result of PE(i,j) is c_flat[(i*N+j)*AW +: AW].
- Testbenches change inputs on negedge clk (avoids races) and print PASS/FAIL themselves.
DATAFLOW (output-stationary)
- Row i of A enters the left edge of array row i and moves right one PE per clock.
- Column j of B enters the top edge of array column j and moves down one PE per clock.
- PE(i,j) keeps C[i][j] in its own accumulator.
- Skew rule, for feed cycle t = 0, 1, 2, ...:
a_left slice i = A[i][t-i] if 0 <= t-i < N, else 0
b_top slice j = B[t-j][j] if 0 <= t-j < N, else 0
- So PE(i,j) multiplies A[i][k]*B[k][j] at cycle t = i+j+k. Last product at t = 3N-3 = 9.
CONTROLLER TIMING
IDLE -> CLEAR (1 cycle) -> COMPUTE (t = 0..2N-2, 7 cycles) -> DRAIN (t = 2N-1..3N-3,
3 cycles) -> DONE. start is accepted in IDLE or DONE. Start to done = 11 cycles.
MODULE INTERFACES (exact names; row/col ports are [$clog2(N)-1:0], i.e. [1:0])
pe #(DW,AW): in clk, rst, clear, en, signed a_in[DW-1:0], signed b_in[DW-1:0];
out reg signed a_out[DW-1:0], b_out[DW-1:0], reg signed acc[AW-1:0].
At posedge: if rst, all <= 0; else a_out <= a_in; b_out <= b_in;
if clear acc <= 0; else if en acc <= acc + a_in*b_in.
systolic_array #(N,DW,AW): in clk, rst, clear, en, a_left[N*DW-1:0], b_top[N*DW-1:0];
out c_flat[N*N*AW-1:0].
input_buffer #(N,DW,TW): in clk, rst, load_en, load_sel (0=A, 1=B), load_row, load_col,
load_data[DW-1:0], feed_en, t[TW-1:0]; out a_left[N*DW-1:0], b_top[N*DW-1:0].
Stores A and B row-major (index row*N+col). Outputs are combinational, all 0 when
feed_en = 0.
output_collector #(N,AW): in c_flat, rd_row, rd_col; out rd_data[AW-1:0] (combinational).
controller #(N,TW): in clk, rst, start; out clear, en, feed_en, busy, done,
reg t[TW-1:0], reg cycle_count[15:0].
clear=1 in CLEAR; feed_en=1 in COMPUTE; en=1 in COMPUTE and DRAIN;
busy=1 in CLEAR, COMPUTE and DRAIN; done=1 in DONE.
t = 0 on entering COMPUTE, +1 every COMPUTE/DRAIN cycle.
cycle_count = 0 on start, +1 every busy cycle (final value 11).
systolic_top #(N,DW,AW,TW): in clk, rst, start, load_en, load_sel, load_row, load_col,
load_data, rd_row, rd_col; out rd_data[AW-1:0], busy, done, cycle_count[15:0].
sequential_mac #(N,DW,AW): same ports as systolic_top; one MAC unit; 64 cycles (baseline).
HOW THE TOP IS USED: while not busy, write the 32 elements one per clock (load_en=1);
pulse start for one clock; wait for done; read C[r][c] by setting rd_row/rd_col.
Results stay valid until the next start.
FOLDERS: rtl/ (design), tb/ (testbenches), model/ (Python), tests/ (hex vectors),
synth/ (Vivado), docs/ (report, screenshots).
TEST FILES: tests/test_XX_A.hex and tests/test_XX_B.hex = 16 lines, 2 hex digits each
(8-bit two's complement), row-major. tests/test_XX_C.hex = 16 lines, 8 hex digits (32-bit).
XX = 00..09. Run every simulation from the repo root so these relative paths work.

## Ownership

Parrv: rtl/controller.v, rtl/systolic_top.v, tb/tb_controller.v, tb/tb_top.v
Raghav: rtl/pe.v, tb/tb_pe.v
Ranjeet: rtl/systolic_array.v, tb/tb_array.v, synth/*
Abhijeet: rtl/input_buffer.v, rtl/output_collector.v, tb/tb_input_buffer.v,
          tb/tb_output_collector.v
Malhar: model/*, tests/*, rtl/sequential_mac.v, tb/tb_sequential.v

Rule: Never edit a file owned by someone else. If their file has a bug, write a bug report instead.
