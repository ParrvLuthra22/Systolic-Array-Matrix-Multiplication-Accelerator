`timescale 1ns/1ps
// Self-checking top-level testbench: 10 hex-vector tests (run from repo root).
// Optional: +TESTDIR=<dir> overrides the vector directory (default "tests").
module tb_top;
    localparam N  = 4;
    localparam DW = 8;
    localparam AW = 32;
    localparam TW = 8;
    localparam NTESTS = 10;

    reg                  clk = 0;
    reg                  rst = 1;
    reg                  start = 0;
    reg                  load_en = 0;
    reg                  load_sel = 0;
    reg  [1:0]           load_row = 0;
    reg  [1:0]           load_col = 0;
    reg  signed [DW-1:0] load_data = 0;
    reg  [1:0]           rd_row = 0;
    reg  [1:0]           rd_col = 0;
    wire signed [AW-1:0] rd_data;
    wire                 busy, done;
    wire [15:0]          cycle_count;

    systolic_top #(.N(N), .DW(DW), .AW(AW), .TW(TW)) dut (
        .clk(clk), .rst(rst), .start(start),
        .load_en(load_en), .load_sel(load_sel),
        .load_row(load_row), .load_col(load_col), .load_data(load_data),
        .rd_row(rd_row), .rd_col(rd_col), .rd_data(rd_data),
        .busy(busy), .done(done), .cycle_count(cycle_count)
    );

    always #5 clk = ~clk;

    reg [DW-1:0]        memA [0:N*N-1];
    reg [DW-1:0]        memB [0:N*N-1];
    reg signed [AW-1:0] memC [0:N*N-1];

    reg [8*64-1:0] dir;
    reg [8*128-1:0] fname;
    integer xx, idx, r, c, guard, errors, test_errors;

    initial begin
        $dumpfile("wave_tb_top.vcd");
        $dumpvars(0, tb_top);
        if (!$value$plusargs("TESTDIR=%s", dir)) dir = "tests";
        errors = 0;

        repeat (2) @(negedge clk);
        rst = 0;
        @(negedge clk);

        for (xx = 0; xx < NTESTS; xx = xx + 1) begin
            test_errors = 0;
            $sformat(fname, "%0s/test_%02d_A.hex", dir, xx); $readmemh(fname, memA);
            $sformat(fname, "%0s/test_%02d_B.hex", dir, xx); $readmemh(fname, memB);
            $sformat(fname, "%0s/test_%02d_C.hex", dir, xx); $readmemh(fname, memC);

            // load A then B, one element per clock
            for (idx = 0; idx < 2*N*N; idx = idx + 1) begin
                load_en   = 1;
                load_sel  = (idx >= N*N);
                load_row  = (idx % (N*N)) / N;
                load_col  = (idx % (N*N)) % N;
                load_data = (idx < N*N) ? memA[idx] : memB[idx - N*N];
                @(negedge clk);
            end
            load_en = 0;

            // pulse start for one clock
            start = 1;
            @(negedge clk);
            start = 0;

            // wait for done (500-cycle timeout)
            guard = 0;
            while (!done && guard < 500) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (!done) begin
                $display("FAIL: test_%02d timeout waiting for done", xx);
                test_errors = test_errors + 1;
            end else begin
                // read all 16 results
                for (r = 0; r < N; r = r + 1) begin
                    for (c = 0; c < N; c = c + 1) begin
                        rd_row = r;
                        rd_col = c;
                        #1;
                        if (rd_data !== memC[r*N+c]) begin
                            $display("FAIL: test_%02d C[%0d][%0d] = %0d, expected %0d",
                                     xx, r, c, rd_data, $signed(memC[r*N+c]));
                            test_errors = test_errors + 1;
                        end
                    end
                end
            end
            $display("test_%02d done, cycle_count = %0d", xx, cycle_count);
            if (test_errors == 0) $display("PASS: test_%02d", xx);
            errors = errors + test_errors;
            @(negedge clk);
        end

        if (errors == 0) $display("ALL 10 TESTS PASSED");
        else             $display("TESTS FAILED: %0d errors", errors);
        $finish;
    end
endmodule
