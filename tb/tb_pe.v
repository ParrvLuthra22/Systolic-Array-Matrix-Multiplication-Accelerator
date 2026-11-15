`timescale 1ns/1ps
module tb_pe;
    reg clk = 0;
    reg rst = 1;
    reg clear = 0;
    reg en = 0;
    reg signed [7:0] a_in = 0;
    reg signed [7:0] b_in = 0;
    wire signed [7:0] a_out;
    wire signed [7:0] b_out;
    wire signed [31:0] acc;

    integer errors = 0;
    integer checks = 0;
    integer expected_acc = 0;
    integer before_group;
    integer repeat_index;

    always #5 clk = ~clk;

    pe #(.DW(8), .AW(32)) dut (
        .clk(clk), .rst(rst), .clear(clear), .en(en),
        .a_in(a_in), .b_in(b_in), .a_out(a_out), .b_out(b_out), .acc(acc)
    );

    task step;
        input integer rst_value;
        input integer clear_value;
        input integer en_value;
        input integer a_value;
        input integer b_value;
        input integer acc_expected;
        begin
            @(negedge clk);
            rst = rst_value;
            clear = clear_value;
            en = en_value;
            a_in = a_value;
            b_in = b_value;
            @(posedge clk);
            #1;
            checks = checks + 1;
            if ($signed(acc) !== acc_expected) begin
                errors = errors + 1;
                $display("FAIL cycle %0d acc: got %0d expected %0d", checks,
                         $signed(acc), acc_expected);
            end
            if (rst_value != 0) begin
                if (a_out !== 0 || b_out !== 0) begin
                    errors = errors + 1;
                    $display("FAIL cycle %0d reset did not clear pass-through outputs", checks);
                end
            end else if ($signed(a_out) !== a_value || $signed(b_out) !== b_value) begin
                errors = errors + 1;
                $display("FAIL cycle %0d pass-through: got (%0d,%0d) expected (%0d,%0d)",
                         checks, $signed(a_out), $signed(b_out), a_value, b_value);
            end
        end
    endtask

    task group_result;
        input [8*80-1:0] label_text;
        begin
            if (errors == before_group)
                $display("PASS: %0s", label_text);
            else
                $display("FAIL: %0s", label_text);
            before_group = errors;
        end
    endtask

    initial begin
        $dumpfile("wave_pe.vcd");
        $dumpvars(0, tb_pe);

        before_group = errors;
        step(1, 0, 0, 31, -17, 0);
        group_result("synchronous reset clears acc and both outputs");

        before_group = errors;
        expected_acc = 6;  step(0, 0, 1, 2, 3, expected_acc);
        expected_acc = 26; step(0, 0, 1, 4, 5, expected_acc);
        expected_acc = 68; step(0, 0, 1, 6, 7, expected_acc);
        group_result("positive MAC accumulation reaches 68");

        before_group = errors;
        step(0, 1, 0, -5, 7, 0);
        expected_acc = -35; step(0, 0, 1, -5, 7, expected_acc);
        expected_acc = 37;  step(0, 0, 1, -8, -9, expected_acc);
        group_result("signed products handle negative operands");

        before_group = errors;
        step(0, 1, 0, 3, 4, 0);
        expected_acc = 0;
        for (repeat_index = 0; repeat_index < 4; repeat_index = repeat_index + 1) begin
            expected_acc = expected_acc + (127 * 127);
            step(0, 0, 1, 127, 127, expected_acc);
        end
        group_result("four 127 x 127 products equal 64516");

        before_group = errors;
        step(0, 1, 0, -128, -128, 0);
        expected_acc = 0;
        for (repeat_index = 0; repeat_index < 4; repeat_index = repeat_index + 1) begin
            expected_acc = expected_acc + ( -128 * -128 );
            step(0, 0, 1, -128, -128, expected_acc);
        end
        group_result("four -128 x -128 products equal 65536");

        before_group = errors;
        step(0, 1, 0, 127, -128, 0);
        expected_acc = 0;
        for (repeat_index = 0; repeat_index < 4; repeat_index = repeat_index + 1) begin
            expected_acc = expected_acc + (127 * -128);
            step(0, 0, 1, 127, -128, expected_acc);
        end
        group_result("four 127 x -128 products equal -65024");

        before_group = errors;
        step(0, 1, 1, 12, -13, 0);
        group_result("clear takes priority over en and pass-through still updates");

        before_group = errors;
        step(0, 0, 1, 3, 4, 12);
        step(0, 0, 0, -7, 9, 12);
        step(0, 0, 0, 11, -12, 12);
        step(0, 0, 1, 2, 5, 22);
        group_result("en=0 holds accumulator while pass-through keeps advancing");

        if (errors == 0)
            $display("PE TESTS PASSED (%0d checks)", checks);
        else
            $display("PE TESTS FAILED: %0d errors across %0d checks", errors, checks);
        $finish;
    end
endmodule
