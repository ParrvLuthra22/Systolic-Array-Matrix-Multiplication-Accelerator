`timescale 1ns/1ps
// Self-checking testbench for the sequential baseline; run from the repo root.
// Optional: +TESTDIR=<dir> overrides the vector directory (default "tests").
module tb_sequential;
    localparam N = 4;
    localparam DW = 8;
    localparam AW = 32;
    localparam NTESTS = 10;

    reg clk = 0;
    reg rst = 1;
    reg start = 0;
    reg load_en = 0;
    reg load_sel = 0;
    reg [1:0] load_row = 0;
    reg [1:0] load_col = 0;
    reg signed [DW-1:0] load_data = 0;
    reg [1:0] rd_row = 0;
    reg [1:0] rd_col = 0;
    wire signed [AW-1:0] rd_data;
    wire busy, done;
    wire [15:0] cycle_count;

    sequential_mac #(.N(N), .DW(DW), .AW(AW)) dut (
        .clk(clk), .rst(rst), .start(start),
        .load_en(load_en), .load_sel(load_sel),
        .load_row(load_row), .load_col(load_col), .load_data(load_data),
        .rd_row(rd_row), .rd_col(rd_col), .rd_data(rd_data),
        .busy(busy), .done(done), .cycle_count(cycle_count)
    );

    always #5 clk = ~clk;

    reg signed [DW-1:0] memA [0:N*N-1];
    reg signed [DW-1:0] memB [0:N*N-1];
    reg signed [AW-1:0] memC [0:N*N-1];
    reg [8*64-1:0] dir;
    reg [8*128-1:0] fname;
    integer test_index, index, row, col, guard, errors, test_errors;

    initial begin
        $dumpfile("wave_tb_sequential.vcd");
        $dumpvars(0, tb_sequential);
        if (!$value$plusargs("TESTDIR=%s", dir)) dir = "tests";
        errors = 0;

        repeat (2) @(negedge clk);
        rst = 0;
        @(negedge clk);

        for (test_index = 0; test_index < NTESTS; test_index = test_index + 1) begin
            test_errors = 0;
            $sformat(fname, "%0s/test_%02d_A.hex", dir, test_index);
            $readmemh(fname, memA);
            $sformat(fname, "%0s/test_%02d_B.hex", dir, test_index);
            $readmemh(fname, memB);
            $sformat(fname, "%0s/test_%02d_C.hex", dir, test_index);
            $readmemh(fname, memC);

            // Load A then B. Inputs change only on falling clock edges.
            for (index = 0; index < 2*N*N; index = index + 1) begin
                load_en = 1;
                load_sel = (index >= N*N);
                load_row = (index % (N*N)) / N;
                load_col = (index % (N*N)) % N;
                if (index < N*N)
                    load_data = memA[index];
                else
                    load_data = memB[index - N*N];
                @(negedge clk);
            end
            load_en = 0;

            // Start for one clock, then allow the FSM to finish all N^3 MACs.
            start = 1;
            @(negedge clk);
            start = 0;
            guard = 0;
            while (!done && guard < 500) begin
                @(negedge clk);
                guard = guard + 1;
            end

            if (!done) begin
                $display("FAIL: test_%02d timed out waiting for done", test_index);
                test_errors = test_errors + 1;
            end else begin
                for (row = 0; row < N; row = row + 1) begin
                    for (col = 0; col < N; col = col + 1) begin
                        rd_row = row;
                        rd_col = col;
                        #1;
                        if (rd_data !== memC[row*N + col]) begin
                            $display("FAIL: test_%02d C[%0d][%0d] = %0d, expected %0d",
                                     test_index, row, col, $signed(rd_data),
                                     $signed(memC[row*N + col]));
                            test_errors = test_errors + 1;
                        end
                    end
                end
                if (cycle_count !== 16'd64) begin
                    $display("FAIL: test_%02d cycle_count = %0d, expected 64",
                             test_index, cycle_count);
                    test_errors = test_errors + 1;
                end
            end

            $display("test_%02d done, cycle_count = %0d", test_index, cycle_count);
            if (test_errors == 0) $display("PASS: test_%02d", test_index);
            errors = errors + test_errors;
            @(negedge clk);
        end

        if (errors == 0) $display("ALL 10 TESTS PASSED");
        else             $display("TESTS FAILED: %0d errors", errors);
        $finish;
    end
endmodule
