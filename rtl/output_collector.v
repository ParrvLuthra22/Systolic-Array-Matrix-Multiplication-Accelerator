`timescale 1ns/1ps

module output_collector #(
    parameter N  = 4,
    parameter AW = 32
) (
    input  wire [N*N*AW-1:0]      c_flat,
    input  wire [$clog2(N)-1:0]  rd_row,
    input  wire [$clog2(N)-1:0]  rd_col,
    output wire [AW-1:0]         rd_data
);

    // Combinational 16:1 mux selecting 32-bit element C[rd_row][rd_col]
    // Memory mapping: row-major layout where PE(i,j) accumulator is at (i*N + j)
    assign rd_data = c_flat[(rd_row * N + rd_col) * AW +: AW];

endmodule
