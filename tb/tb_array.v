`timescale 1ns/1ps
// ---------------------------------------------------------------------------
// tb_array : self-checking testbench for systolic_array (owner: Ranajeet)
//
// Drives the array directly (no input_buffer, no controller). The testbench
// applies the skew itself:
//     a_left slice i = A[i][t-i]  if 0 <= t-i < N, else 0
//     b_top  slice j = B[t-j][j]  if 0 <= t-j < N, else 0
// Sequence per case: clear for 1 clock, then en = 1 for t = 0..3N-3 (0..9),
// then en = 0 and inputs = 0, then compare all N*N results with a reference
// computed here with three nested loops.
//
// Cases: (1) A = identity,     B = 1..16
//        (2) A = 1..16,        B = all ones
//        (3) A, B = random signed 8-bit values
// Inputs change on negedge clk. Dumps wave_array.vcd.
// ---------------------------------------------------------------------------
module tb_array;
    localparam N  = 4;
    localparam DW = 8;
    localparam AW = 32;
    localparam T_LAST = 3*N - 3;        // last feed cycle (9)

    reg               clk = 0;
    reg               rst = 1;
    reg               clear = 0;
    reg               en = 0;
    reg  [N*DW-1:0]   a_left = 0;
    reg  [N*DW-1:0]   b_top  = 0;
    wire [N*N*AW-1:0] c_flat;

    always #5 clk = ~clk;               // 10 ns period (100 MHz)

    systolic_array #(.N(N), .DW(DW), .AW(AW)) dut (
        .clk(clk), .rst(rst), .clear(clear), .en(en),
        .a_left(a_left), .b_top(b_top), .c_flat(c_flat)
    );

    // Matrices (row-major) and expected result, held as signed integers.
    integer A    [0:N*N-1];
    integer B    [0:N*N-1];
    integer Cexp [0:N*N-1];

    integer i, j, k, t, idx;
    integer errors, checks, case_err;
    integer seed;
    reg signed [DW-1:0] rnd;
    reg signed [AW-1:0] got;

    // ---- drive the skewed inputs for feed cycle t ----
    task drive_t(input integer tt);
        integer r;
        begin
            a_left = 0;
            b_top  = 0;
            for (r = 0; r < N; r = r + 1) begin
                if (tt >= r && tt - r < N) begin
                    a_left[r*DW +: DW] = A[r*N + (tt - r)];      // A[r][t-r]
                    b_top [r*DW +: DW] = B[(tt - r)*N + r];      // B[t-r][r]
                end
            end
        end
    endtask

    // ---- run one matrix multiply on the array and check all results ----
    task run_case(input integer case_no);
        begin
            // reference model
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    Cexp[i*N+j] = 0;
                    for (k = 0; k < N; k = k + 1)
                        Cexp[i*N+j] = Cexp[i*N+j] + A[i*N+k] * B[k*N+j];
                end

            // clear the accumulators for one clock
            @(negedge clk);
            clear = 1; en = 0; a_left = 0; b_top = 0;
            @(negedge clk);
            clear = 0;

            // feed t = 0 .. 3N-3 with en = 1
            for (t = 0; t <= T_LAST; t = t + 1) begin
                en = 1;
                drive_t(t);
                @(negedge clk);
            end

            // stop accumulating, flush inputs
            en = 0; a_left = 0; b_top = 0;
            @(negedge clk);

            // compare
            case_err = 0;
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    got    = c_flat[(i*N+j)*AW +: AW];
                    checks = checks + 1;
                    if (got === Cexp[i*N+j]) begin
                        $display("  PASS case %0d C[%0d][%0d] = %0d", case_no, i, j, got);
                    end else begin
                        $display("  FAIL case %0d C[%0d][%0d] = %0d, expected %0d",
                                 case_no, i, j, got, Cexp[i*N+j]);
                        errors   = errors + 1;
                        case_err = case_err + 1;
                    end
                end
            if (case_err == 0) $display("CASE %0d PASSED (16/16)", case_no);
            else               $display("CASE %0d FAILED (%0d errors)", case_no, case_err);
        end
    endtask

    initial begin
        $dumpfile("wave_array.vcd");
        $dumpvars(0, tb_array);
        errors = 0;
        checks = 0;
        seed   = 2026;

        // synchronous reset for 2 clocks
        repeat (2) @(negedge clk);
        rst = 0;

        // Case 1: A = identity, B = 1..16  ->  C = B
        $display("Case 1: A = identity, B = 1..16");
        for (idx = 0; idx < N*N; idx = idx + 1) begin
            A[idx] = (idx / N == idx % N) ? 1 : 0;
            B[idx] = idx + 1;
        end
        run_case(1);

        // Case 2: A = 1..16, B = all ones  ->  C[i][j] = row sum of A
        $display("Case 2: A = 1..16, B = all ones");
        for (idx = 0; idx < N*N; idx = idx + 1) begin
            A[idx] = idx + 1;
            B[idx] = 1;
        end
        run_case(2);

        // Case 3: random signed 8-bit values (-128..127)
        $display("Case 3: random signed 8-bit A and B");
        for (idx = 0; idx < N*N; idx = idx + 1) begin
            rnd = $random(seed); A[idx] = rnd;   // sign-extended to integer
            rnd = $random(seed); B[idx] = rnd;
        end
        run_case(3);

        if (errors == 0)
            $display("ARRAY TESTS PASSED: %0d/%0d element checks", checks, checks);
        else
            $display("ARRAY TESTS FAILED: %0d errors out of %0d checks", errors, checks);
        $finish;
    end
endmodule
