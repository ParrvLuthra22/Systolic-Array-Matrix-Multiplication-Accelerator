`timescale 1ns/1ps
// Self-checking testbench for controller (N = 4). Inputs change on negedge.
module tb_controller;
    localparam N = 4;

    reg        clk = 0;
    reg        rst = 1;
    reg        start = 0;
    wire       clear, feed_en, en, busy, done;
    wire [7:0] t, cycle_count;

    controller #(.N(N)) dut (
        .clk(clk), .rst(rst), .start(start),
        .clear(clear), .feed_en(feed_en), .en(en), .busy(busy), .done(done),
        .t(t), .cycle_count(cycle_count)
    );

    always #5 clk = ~clk;

    integer fails = 0;
    integer n_clear, n_feed, n_en, n_busy, idx, guard, i;
    reg     t_ok;

    task check(input cond, input [255:0] name);
        begin
            if (cond) $display("PASS: %0s", name);
            else begin
                $display("FAIL: %0s", name);
                fails = fails + 1;
            end
        end
    endtask

    // Pulse start for one cycle (call right after a negedge), then watch the
    // run at every negedge until done goes high, and check the counts.
    task run_and_check(input [255:0] tag);
        begin
            n_clear = 0; n_feed = 0; n_en = 0; n_busy = 0;
            idx = 0; t_ok = 1; guard = 0;
            start = 1;
            @(negedge clk);
            start = 0;
            while (!done && guard < 100) begin
                if (clear)   n_clear = n_clear + 1;
                if (feed_en) n_feed  = n_feed + 1;
                if (en) begin
                    n_en = n_en + 1;
                    if (t !== idx) t_ok = 0;
                    idx = idx + 1;
                end
                if (busy)    n_busy = n_busy + 1;
                guard = guard + 1;
                @(negedge clk);
            end
            $display("-- %0s", tag);
            check(guard < 100,                 "run terminates (done reached)");
            check(n_clear == 1,                "clear high exactly 1 cycle");
            check(n_feed  == 3*N-5,            "feed_en high 7 cycles");
            check(n_en    == 3*N-2,            "en high 10 cycles");
            check(n_busy  == 3*N-1,            "busy high 11 cycles");
            check(t_ok && idx == 3*N-2,        "t counts 0..9 during COMPUTE+DRAIN");
            check(cycle_count == 3*N-1,        "cycle_count ends at 11");
            check(done && !busy && !en,        "done high, busy/en low");
        end
    endtask

    initial begin
        $dumpfile("wave_ctrl.vcd");
        $dumpvars(0, tb_controller);

        // reset
        repeat (2) @(negedge clk);
        rst = 0;
        @(negedge clk);
        check(!busy && !done && t == 0 && cycle_count == 0, "idle after reset");
        repeat (3) @(negedge clk);
        check(!busy && !done && !clear, "stays idle without start");

        // first run
        run_and_check("run 1 (from IDLE)");

        // done holds until next start
        repeat (5) @(negedge clk);
        check(done && !busy, "done stays high until next start");

        // second run straight from DONE
        run_and_check("run 2 (straight from DONE)");
        repeat (2) @(negedge clk);

        // reset in the middle of a run
        start = 1;
        @(negedge clk);
        start = 0;
        repeat (4) @(negedge clk);
        check(busy && feed_en, "mid-run: in COMPUTE before reset");
        rst = 1;
        @(negedge clk);
        rst = 0;
        check(!busy && !done && !en && t == 0 && cycle_count == 0,
              "reset mid-run returns to IDLE");
        repeat (2) @(negedge clk);
        check(!busy && !done, "stays idle after mid-run reset");

        // controller still works after a mid-run reset
        run_and_check("run 3 (after mid-run reset)");

        if (fails == 0) $display("CONTROLLER TESTS PASSED");
        else            $display("CONTROLLER TESTS FAILED (%0d failures)", fails);
        $finish;
    end

    initial begin
        #100000;
        $display("FAIL: timeout");
        $finish;
    end
endmodule
