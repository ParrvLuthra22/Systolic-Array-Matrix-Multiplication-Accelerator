`timescale 1ns/1ps
// One-MAC, row-major matrix multiplier used as the sequential baseline.
module sequential_mac #(
    parameter N  = 4,
    parameter DW = 8,
    parameter AW = 32
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
    output reg  [15:0]               cycle_count
);

    localparam CW = (N <= 1) ? 1 : $clog2(N);
    localparam [1:0] IDLE = 2'd0,
                     RUN  = 2'd1,
                     DONE = 2'd2;

    reg [1:0] state;
    reg [CW-1:0] i, j, k;
    reg signed [DW-1:0] A [0:N*N-1];
    reg signed [DW-1:0] B [0:N*N-1];
    reg signed [AW-1:0] C [0:N*N-1];
    reg signed [AW-1:0] acc;
    wire signed [2*DW-1:0] product = A[i*N+k] * B[k*N+j];

    integer index;
    always @(posedge clk) begin
        if (rst) begin
            state       <= IDLE;
            i           <= {CW{1'b0}};
            j           <= {CW{1'b0}};
            k           <= {CW{1'b0}};
            acc         <= {AW{1'b0}};
            cycle_count <= 16'd0;
            for (index = 0; index < N*N; index = index + 1) begin
                A[index] <= {DW{1'b0}};
                B[index] <= {DW{1'b0}};
                C[index] <= {AW{1'b0}};
            end
        end else begin
            // Matrix contents may be loaded in IDLE or DONE, but not mid-run.
            if (load_en && state != RUN) begin
                if (!load_sel)
                    A[load_row*N + load_col] <= load_data;
                else
                    B[load_row*N + load_col] <= load_data;
            end

            case (state)
                IDLE, DONE: begin
                    if (start) begin
                        state       <= RUN;
                        i           <= {CW{1'b0}};
                        j           <= {CW{1'b0}};
                        k           <= {CW{1'b0}};
                        acc         <= {AW{1'b0}};
                        cycle_count <= 16'd0;
                    end
                end

                RUN: begin
                    cycle_count <= cycle_count + 16'd1;
                    if (k == N-1) begin
                        // The last product completes this output element.
                        C[i*N + j] <= acc + product;
                        acc <= {AW{1'b0}};
                        k <= {CW{1'b0}};

                        if (j == N-1) begin
                            j <= {CW{1'b0}};
                            if (i == N-1) begin
                                i <= {CW{1'b0}};
                                state <= DONE;
                            end else begin
                                i <= i + 1'b1;
                            end
                        end else begin
                            j <= j + 1'b1;
                        end
                    end else begin
                        acc <= acc + product;
                        k <= k + 1'b1;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

    assign rd_data = C[rd_row*N + rd_col];
    assign busy = (state == RUN);
    assign done = (state == DONE);

endmodule
