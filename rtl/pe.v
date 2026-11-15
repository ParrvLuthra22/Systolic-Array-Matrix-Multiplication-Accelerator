`timescale 1ns/1ps
module pe #(parameter DW = 8, parameter AW = 32) (
    input wire clk,
    input wire rst,
    input wire clear,
    input wire en,
    input wire signed [DW-1:0] a_in,
    input wire signed [DW-1:0] b_in,
    output reg signed [DW-1:0] a_out,
    output reg signed [DW-1:0] b_out,
    output reg signed [AW-1:0] acc
);
    wire signed [2*DW-1:0] prod = a_in * b_in;

    always @(posedge clk) begin
        if (rst) begin
            a_out <= 0;
            b_out <= 0;
            acc <= 0;
        end else begin
            // The data pipeline advances every clock, independently of en.
            a_out <= a_in;
            b_out <= b_in;

            if (clear)
                acc <= 0;
            else if (en)
                acc <= acc + prod;
        end
    end
endmodule
