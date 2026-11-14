`timescale 1ns/1ps
// ---------------------------------------------------------------------------
// systolic_array : N x N output-stationary systolic array (owner: Ranajeet)
//
//   - Row i of A enters at a_left[i*DW +: DW] and moves RIGHT one PE per clock.
//   - Column j of B enters at b_top[j*DW +: DW] and moves DOWN one PE per clock.
//   - PE(i,j) keeps C[i][j] in its own accumulator, exposed on
//     c_flat[(i*N+j)*AW +: AW].
//   - clk, rst, clear and en are broadcast to every PE.
//
// The inputs must already be skewed (row i delayed by i cycles, column j by
// j cycles); input_buffer does that in the full design.
// ---------------------------------------------------------------------------
module systolic_array #(
    parameter N  = 4,
    parameter DW = 8,
    parameter AW = 32
) (
    input  wire              clk,
    input  wire              rst,
    input  wire              clear,
    input  wire              en,
    input  wire [N*DW-1:0]   a_left,
    input  wire [N*DW-1:0]   b_top,
    output wire [N*N*AW-1:0] c_flat
);
    // Horizontal links: a_bus[i][j] is the A value entering PE(i,j) from the
    // left. a_bus[i][N] is the output of the last PE in the row (unused).
    wire [DW-1:0] a_bus [0:N-1][0:N];
    // Vertical links: b_bus[i][j] is the B value entering PE(i,j) from above.
    // b_bus[N][j] is the output of the bottom PE in the column (unused).
    wire [DW-1:0] b_bus [0:N][0:N-1];

    genvar i, j;
    generate
        // Edge inputs: left edge gets a_left slices, top edge gets b_top slices.
        for (i = 0; i < N; i = i + 1) begin : g_edge
            assign a_bus[i][0] = a_left[i*DW +: DW];
            assign b_bus[0][i] = b_top [i*DW +: DW];
        end

        // N x N grid of processing elements.
        for (i = 0; i < N; i = i + 1) begin : g_row
            for (j = 0; j < N; j = j + 1) begin : g_col
                pe #(.DW(DW), .AW(AW)) u_pe (
                    .clk   (clk),
                    .rst   (rst),
                    .clear (clear),
                    .en    (en),
                    .a_in  (a_bus[i][j]),
                    .b_in  (b_bus[i][j]),
                    .a_out (a_bus[i][j+1]),   // to the PE on the right
                    .b_out (b_bus[i+1][j]),   // to the PE below
                    .acc   (c_flat[(i*N+j)*AW +: AW])
                );
            end
        end
    endgenerate
endmodule
