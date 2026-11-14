## Project 12 - Systolic Array Matrix Multiplication Accelerator
## Timing constraint shared by systolic_top and sequential_mac.
## 100 MHz target clock (10 ns period) on the top-level port clk.
## No pin (PACKAGE_PIN / IOSTANDARD) constraints: designs are synthesized
## out-of-context, so only resource and timing numbers are produced.

create_clock -period 10.000 -name clk [get_ports clk]
