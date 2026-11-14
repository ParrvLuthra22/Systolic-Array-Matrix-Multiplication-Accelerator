// Systolic array controller FSM: IDLE -> CLEAR -> COMPUTE -> DRAIN -> DONE
module controller #(
    parameter N = 4
) (
    input  wire       clk,
    input  wire       rst,        // synchronous, active high
    input  wire       start,
    output wire       clear,
    output wire       feed_en,
    output wire       en,
    output wire       busy,
    output wire       done,
    output reg  [7:0] t,
    output reg  [7:0] cycle_count
);

    localparam [2:0] IDLE    = 3'd0,
                     CLEAR   = 3'd1,
                     COMPUTE = 3'd2,
                     DRAIN   = 3'd3,
                     DONE    = 3'd4;

    reg [2:0] state;

    always @(posedge clk) begin
        if (rst) begin
            state       <= IDLE;
            t           <= 8'd0;
            cycle_count <= 8'd0;
        end else begin
            case (state)
                IDLE, DONE: begin
                    if (start) begin
                        state       <= CLEAR;
                        t           <= 8'd0;
                        cycle_count <= 8'd0;
                    end
                end
                CLEAR: begin
                    state       <= COMPUTE;
                    t           <= 8'd0;
                    cycle_count <= cycle_count + 8'd1;
                end
                COMPUTE: begin
                    t           <= t + 8'd1;
                    cycle_count <= cycle_count + 8'd1;
                    if (t == 2*N-2) state <= DRAIN;
                end
                DRAIN: begin
                    t           <= t + 8'd1;
                    cycle_count <= cycle_count + 8'd1;
                    if (t == 3*N-3) state <= DONE;
                end
                default: begin
                    state       <= IDLE;
                    t           <= 8'd0;
                    cycle_count <= 8'd0;
                end
            endcase
        end
    end

    assign clear   = (state == CLEAR);
    assign feed_en = (state == COMPUTE);
    assign en      = (state == COMPUTE) || (state == DRAIN);
    assign busy    = (state == CLEAR) || (state == COMPUTE) || (state == DRAIN);
    assign done    = (state == DONE);

endmodule
