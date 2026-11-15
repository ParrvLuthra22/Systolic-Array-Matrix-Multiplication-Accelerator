`timescale 1ns/1ps
// Top level: controller + input buffer + systolic array + output collector
module systolic_top #(
    parameter N  = 4,
    parameter DW = 8,
    parameter AW = 32,
    parameter TW = 8
) (
    input  wire                      clk,
    input  wire                      rst,
    input  wire                      start,
    input  wire                      load_en,
    input  wire                      load_sel,   // 0 = A, 1 = B
    input  wire [$clog2(N)-1:0]      load_row,
    input  wire [$clog2(N)-1:0]      load_col,
    input  wire signed [DW-1:0]      load_data,
    input  wire [$clog2(N)-1:0]      rd_row,
    input  wire [$clog2(N)-1:0]      rd_col,
    output wire signed [AW-1:0]      rd_data,
    output wire                      busy,
    output wire                      done,
    output wire [15:0]               cycle_count
);

    wire                clear;
    wire                en;
    wire                feed_en;
    wire [TW-1:0]       t;
    wire [N*DW-1:0]     a_left;
    wire [N*DW-1:0]     b_top;
    wire [N*N*AW-1:0]   c_flat;

    controller #(.N(N), .TW(TW)) u_ctrl (
        .clk         (clk),
        .rst         (rst),
        .start       (start),
        .clear       (clear),
        .en          (en),
        .feed_en     (feed_en),
        .busy        (busy),
        .done        (done),
        .t           (t),
        .cycle_count (cycle_count)
    );

    input_buffer #(.N(N), .DW(DW), .TW(TW)) u_buf (
        .clk       (clk),
        .rst       (rst),
        .load_en   (load_en),
        .load_sel  (load_sel),
        .load_row  (load_row),
        .load_col  (load_col),
        .load_data (load_data),
        .feed_en   (feed_en),
        .t         (t),
        .a_left    (a_left),
        .b_top     (b_top)
    );

    systolic_array #(.N(N), .DW(DW), .AW(AW)) u_array (
        .clk    (clk),
        .rst    (rst),
        .clear  (clear),
        .en     (en),
        .a_left (a_left),
        .b_top  (b_top),
        .c_flat (c_flat)
    );

    output_collector #(.N(N), .AW(AW)) u_out (
        .c_flat  (c_flat),
        .rd_row  (rd_row),
        .rd_col  (rd_col),
        .rd_data (rd_data)
    );

endmodule
