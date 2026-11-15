`timescale 1ns/1ps

module input_buffer #(
    parameter N  = 4,
    parameter DW = 8,
    parameter TW = 8
) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire                 load_en,
    input  wire                 load_sel,   // 0 = A, 1 = B
    input  wire [$clog2(N)-1:0] load_row,
    input  wire [$clog2(N)-1:0] load_col,
    input  wire [DW-1:0]        load_data,
    input  wire                 feed_en,
    input  wire [TW-1:0]        t,
    output reg  [N*DW-1:0]      a_left,
    output reg  [N*DW-1:0]      b_top
);

    // Two internal memories for A and B in row-major layout
    reg [DW-1:0] A [0:N*N-1];
    reg [DW-1:0] B [0:N*N-1];

    integer k;
    always @(posedge clk) begin
        if (rst) begin
            for (k = 0; k < N*N; k = k + 1) begin
                A[k] <= {DW{1'b0}};
                B[k] <= {DW{1'b0}};
            end
        end else if (load_en) begin
            if (load_sel == 1'b0)
                A[load_row * N + load_col] <= load_data;
            else
                B[load_row * N + load_col] <= load_data;
        end
    end

    // Combinational skew logic
    // Row i of A is delayed by i cycles: a_left[i] = A[i][t - i] for 0 <= t - i < N
    // Col j of B is delayed by j cycles: b_top[j]  = B[t - j][j] for 0 <= t - j < N
    // Both are 0 when outside valid range or when feed_en is 0
    integer i;
    always @(*) begin
        a_left = {N*DW{1'b0}};
        b_top  = {N*DW{1'b0}};
        for (i = 0; i < N; i = i + 1) begin
            if (feed_en && (t >= i) && (t < i + N)) begin
                a_left[i*DW +: DW] = A[i*N + (t - i)];
                b_top [i*DW +: DW] = B[(t - i)*N + i];
            end
        end
    end

endmodule
