# Section 1: Introduction

**Author:** Parrv

Matrix multiplication is the core operation of modern AI workloads: the fully connected and convolution layers of a neural network reduce to large matrix products. Computing C = A × B for two N × N matrices needs N³ multiply-accumulate (MAC) operations. A conventional datapath with one MAC unit performs them one after another, so a 4×4 product takes 64 cycles.

A **systolic array** is a grid of identical processing elements (PEs) through which data moves rhythmically, one PE per clock, like a pulse. Each PE multiplies the two operands passing through it and adds the product to a local running sum. Because every operand is reused as it travels across a row or down a column, many PEs work in the same cycle while each value is read from the input buffers only once. Google's Tensor Processing Unit is built on this idea at a much larger scale.

This project implements a 4×4 **output-stationary** systolic array in synthesizable Verilog-2005 that computes C = A × B for 8-bit signed matrices with 32-bit signed accumulators. The design is verified against a Python golden model, compared with a one-MAC sequential baseline, and synthesized for a Xilinx Artix-7 FPGA.

**Contributions**

| Member | Contribution |
|---|---|
| Parrv | Controller FSM, top-level integration, full-system testbench, block diagram, report integration |
| Raghav | Processing element (PE) and PE testbench, demo |
| Ranjeet | 4x4 array wiring, array testbench, Vivado synthesis flow |
| Abhijeet | Input buffers with skew logic, output collector, their testbenches |
| Malhar | Golden model and test vectors, sequential baseline, performance analysis |
