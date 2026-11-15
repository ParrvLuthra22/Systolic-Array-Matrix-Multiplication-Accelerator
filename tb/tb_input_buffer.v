`timescale 1ns/1ps

module tb_input_buffer;

    parameter N  = 4;
    parameter DW = 8;
    parameter TW = 8;

    reg                 clk;
    reg                 rst;
    reg                 load_en;
    reg                 load_sel;
    reg  [1:0]          load_row;
    reg  [1:0]          load_col;
    reg  [DW-1:0]       load_data;
    reg                 feed_en;
    reg  [TW-1:0]       t;

    wire [N*DW-1:0]     a_left;
    wire [N*DW-1:0]     b_top;

    // Byte slice aliases for waveform visualization (staircase view)
    wire [DW-1:0]       a_row0 = a_left[7:0];
    wire [DW-1:0]       a_row1 = a_left[15:8];
    wire [DW-1:0]       a_row2 = a_left[23:16];
    wire [DW-1:0]       a_row3 = a_left[31:24];

    wire [DW-1:0]       b_col0 = b_top[7:0];
    wire [DW-1:0]       b_col1 = b_top[15:8];
    wire [DW-1:0]       b_col2 = b_top[23:16];
    wire [DW-1:0]       b_col3 = b_top[31:24];

    // Instantiate Device Under Test
    input_buffer #(
        .N(N),
        .DW(DW),
        .TW(TW)
    ) dut (
        .clk(clk),
        .rst(rst),
        .load_en(load_en),
        .load_sel(load_sel),
        .load_row(load_row),
        .load_col(load_col),
        .load_data(load_data),
        .feed_en(feed_en),
        .t(t),
        .a_left(a_left),
        .b_top(b_top)
    );

    // 100 MHz clock generation (period = 10 ns)
    always #5 clk = ~clk;

    // Expected values table for t = 0..9
    reg [N*DW-1:0] exp_a_left [0:9];
    reg [N*DW-1:0] exp_b_top  [0:9];

    integer r, c, cycle, errors;

    initial begin
        $dumpfile("wave_input_buffer.vcd");
        $dumpvars(0, tb_input_buffer);

        // Prepopulate expected skew tables based on Section 3.2 & Prompt 11
        // Formatted as {slice3, slice2, slice1, slice0}
        exp_a_left[0] = {8'h00, 8'h00, 8'h00, 8'h10};
        exp_b_top[0]  = {8'h00, 8'h00, 8'h00, 8'ha0};

        exp_a_left[1] = {8'h00, 8'h00, 8'h20, 8'h11};
        exp_b_top[1]  = {8'h00, 8'h00, 8'ha1, 8'ha4};

        exp_a_left[2] = {8'h00, 8'h30, 8'h21, 8'h12};
        exp_b_top[2]  = {8'h00, 8'ha2, 8'ha5, 8'ha8};

        exp_a_left[3] = {8'h40, 8'h31, 8'h22, 8'h13};
        exp_b_top[3]  = {8'ha3, 8'ha6, 8'ha9, 8'hac};

        exp_a_left[4] = {8'h41, 8'h32, 8'h23, 8'h00};
        exp_b_top[4]  = {8'ha7, 8'haa, 8'had, 8'h00};

        exp_a_left[5] = {8'h42, 8'h33, 8'h00, 8'h00};
        exp_b_top[5]  = {8'hab, 8'hae, 8'h00, 8'h00};

        exp_a_left[6] = {8'h43, 8'h00, 8'h00, 8'h00};
        exp_b_top[6]  = {8'haf, 8'h00, 8'h00, 8'h00};

        exp_a_left[7] = 32'h00000000;
        exp_b_top[7]  = 32'h00000000;

        exp_a_left[8] = 32'h00000000;
        exp_b_top[8]  = 32'h00000000;

        exp_a_left[9] = 32'h00000000;
        exp_b_top[9]  = 32'h00000000;

        // Initialize signals
        clk       = 0;
        rst       = 1;
        load_en   = 0;
        load_sel  = 0;
        load_row  = 0;
        load_col  = 0;
        load_data = 0;
        feed_en   = 0;
        t         = 0;
        errors    = 0;

        // Apply synchronous reset for 2 clock cycles
        repeat (2) @(negedge clk);
        rst = 0;

        $display("==================================================");
        $display("   TESTBENCH: input_buffer and skew logic");
        $display("==================================================");

        // Step 1: Load matrix A: A[r][c] = 8'h10*(r+1) + c
        // and matrix B: B[r][c] = 8'hA0 + 4*r + c
        $display("[INFO] Loading Matrix A and Matrix B into input_buffer...");
        for (r = 0; r < N; r = r + 1) begin
            for (c = 0; c < N; c = c + 1) begin
                // Load A
                @(negedge clk);
                load_en   = 1;
                load_sel  = 0;
                load_row  = r;
                load_col  = c;
                load_data = 8'h10 * (r + 1) + c;

                // Load B
                @(negedge clk);
                load_en   = 1;
                load_sel  = 1;
                load_row  = r;
                load_col  = c;
                load_data = 8'hA0 + 4 * r + c;
            end
        end

        @(negedge clk);
        load_en   = 0;
        load_data = 0;

        // Step 2: Test feed_en = 0 disables all outputs regardless of t
        $display("[INFO] Checking feed_en = 0 produces all zeros...");
        feed_en = 0;
        for (cycle = 0; cycle < 10; cycle = cycle + 1) begin
            t = cycle;
            #1;
            if (a_left !== 32'h00000000 || b_top !== 32'h00000000) begin
                $display("FAIL: feed_en=0 at t=%0d produced a_left=%08x, b_top=%08x (expected 0)",
                         t, a_left, b_top);
                errors = errors + 1;
            end
        end

        // Step 3: Test skew output for t = 0..9 with feed_en = 1
        $display("[INFO] Testing skewed outputs for t = 0..9 with feed_en = 1...");
        feed_en = 1;
        for (cycle = 0; cycle < 10; cycle = cycle + 1) begin
            t = cycle;
            #1; // Allow combinational logic to settle

            // Display observed slices in order: slice 0, 1, 2, 3
            $display("t=%0d: a_left = %02x %02x %02x %02x   b_top = %02x %02x %02x %02x",
                     t,
                     a_left[7:0], a_left[15:8], a_left[23:16], a_left[31:24],
                     b_top[7:0],  b_top[15:8],  b_top[23:16],  b_top[31:24]);

            if (a_left !== exp_a_left[cycle]) begin
                $display("FAIL: t=%0d a_left mismatch! Got: %08x, Expected: %08x",
                         t, a_left, exp_a_left[cycle]);
                errors = errors + 1;
            end

            if (b_top !== exp_b_top[cycle]) begin
                $display("FAIL: t=%0d b_top mismatch! Got: %08x, Expected: %08x",
                         t, b_top, exp_b_top[cycle]);
                errors = errors + 1;
            end
        end

        // Final result reporting
        $display("--------------------------------------------------");
        if (errors == 0) begin
            $display("PASS: All input_buffer and skew tests PASSED successfully.");
        end else begin
            $display("FAIL: %0d error(s) encountered in input_buffer tests.", errors);
        end
        $display("==================================================");

        $finish;
    end

endmodule
