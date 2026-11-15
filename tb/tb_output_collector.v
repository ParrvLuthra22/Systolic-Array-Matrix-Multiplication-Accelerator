`timescale 1ns/1ps

module tb_output_collector;

    parameter N  = 4;
    parameter AW = 32;

    reg  [N*N*AW-1:0]      c_flat;
    reg  [$clog2(N)-1:0]  rd_row;
    reg  [$clog2(N)-1:0]  rd_col;
    wire [AW-1:0]         rd_data;

    // Instantiate Device Under Test
    output_collector #(
        .N(N),
        .AW(AW)
    ) dut (
        .c_flat(c_flat),
        .rd_row(rd_row),
        .rd_col(rd_col),
        .rd_data(rd_data)
    );

    // Reference memory of known 32-bit signed test values
    reg signed [AW-1:0] test_matrix [0:N-1][0:N-1];

    integer r, c, errors;

    initial begin
        $dumpfile("wave_output_collector.vcd");
        $dumpvars(0, tb_output_collector);

        errors = 0;

        $display("==================================================");
        $display("   TESTBENCH: output_collector");
        $display("==================================================");

        // Assign 16 distinct test values including positives, zero, negatives, and extreme ranges
        test_matrix[0][0] = 32'sd0;
        test_matrix[0][1] = 32'sd12345;
        test_matrix[0][2] = -32'sd65024;      // Negative extreme from test_04
        test_matrix[0][3] = 32'sd64516;       // Positive extreme from test_02
        test_matrix[1][0] = -32'sd1;
        test_matrix[1][1] = 32'sd65536;       // Positive extreme from test_03
        test_matrix[1][2] = -32'sd128;
        test_matrix[1][3] = 32'sd255;
        test_matrix[2][0] = -32'sd32768;
        test_matrix[2][1] = 32'sd999999;
        test_matrix[2][2] = -32'sd54321;
        test_matrix[2][3] = 32'sd42;
        test_matrix[3][0] = 32'sd7;
        test_matrix[3][1] = -32'sd16384;
        test_matrix[3][2] = 32'sd1024;
        test_matrix[3][3] = -32'sd99;

        // Pack test_matrix into flattened c_flat bus (row-major order)
        for (r = 0; r < N; r = r + 1) begin
            for (c = 0; c < N; c = c + 1) begin
                c_flat[(r * N + c) * AW +: AW] = test_matrix[r][c];
            end
        end

        // Read all 16 locations and verify
        $display("[INFO] Reading all 16 matrix positions through output_collector...");
        for (r = 0; r < N; r = r + 1) begin
            for (c = 0; c < N; c = c + 1) begin
                rd_row = r;
                rd_col = c;
                #1; // Combinational propagation delay

                if ($signed(rd_data) !== test_matrix[r][c]) begin
                    $display("FAIL: C[%0d][%0d] mismatch! Got: %0d (%08x), Expected: %0d (%08x)",
                             r, c, $signed(rd_data), rd_data, test_matrix[r][c], test_matrix[r][c]);
                    errors = errors + 1;
                end else begin
                    $display("PASS: C[%0d][%0d] = %10d (hex: 0x%08x)",
                             r, c, $signed(rd_data), rd_data);
                end
            end
        end

        // Final summary
        $display("--------------------------------------------------");
        if (errors == 0) begin
            $display("PASS: All output_collector tests PASSED successfully.");
        end else begin
            $display("FAIL: %0d error(s) encountered in output_collector tests.", errors);
        end
        $display("==================================================");

        $finish;
    end

endmodule
