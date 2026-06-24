// =============================================================================
// Testbench for 8-bit NaI(Tl) HDL replay vectors
// =============================================================================

`timescale 1ns/1ps

module tb_nai59_8bit;

    localparam integer SAMPLE_BITS = 8;
    localparam integer N_EVENTS = 1024;
    localparam integer N_SAMPLES = 500;
    localparam integer PRETRIGGER_SAMPLES = 40;
    localparam integer THRESHOLD_COUNTS = 4;

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst = 1'b1;
    reg event_start = 1'b0;
    reg sample_valid = 1'b0;
    reg [SAMPLE_BITS-1:0] sample_in = {SAMPLE_BITS{1'b0}};

    wire event_done;
    wire triggered;
    wire [SAMPLE_BITS-1:0] peak_count;
    wire [15:0] peak_index;
    wire [SAMPLE_BITS-1:0] baseline_count;

    nai59_peak_trigger #(
        .SAMPLE_BITS(SAMPLE_BITS),
        .N_SAMPLES(N_SAMPLES),
        .PRETRIGGER_SAMPLES(PRETRIGGER_SAMPLES),
        .THRESHOLD_COUNTS(THRESHOLD_COUNTS)
    ) dut (
        .clk(clk),
        .rst(rst),
        .event_start(event_start),
        .sample_valid(sample_valid),
        .sample_in(sample_in),
        .event_done(event_done),
        .triggered(triggered),
        .peak_count(peak_count),
        .peak_index(peak_index),
        .baseline_count(baseline_count)
    );

    reg [SAMPLE_BITS-1:0] sample_mem [0:N_EVENTS*N_SAMPLES-1];
    reg expected_trigger [0:N_EVENTS-1];
    reg [SAMPLE_BITS-1:0] expected_peak_count [0:N_EVENTS-1];
    reg [15:0] expected_peak_index [0:N_EVENTS-1];

    integer evt;
    integer i;
    integer errors;
    integer total_checked;

    initial begin
        $display("------------------------------------------------------------");
        $display("Starting HDL validation for 8-bit replay vectors");
        $display("N_EVENTS          = %0d", N_EVENTS);
        $display("N_SAMPLES         = %0d", N_SAMPLES);
        $display("THRESHOLD_COUNTS  = %0d", THRESHOLD_COUNTS);
        $display("------------------------------------------------------------");

        $readmemh("../../hdl_vectors/nai59_8bit_flat.mem", sample_mem);
        $readmemh("../../hdl_vectors/nai59_8bit_expected_trigger.mem", expected_trigger);
        $readmemh("../../hdl_vectors/nai59_8bit_expected_peak_count.mem", expected_peak_count);
        $readmemh("../../hdl_vectors/nai59_8bit_expected_peak_index.mem", expected_peak_index);

        errors = 0;
        total_checked = 0;

        repeat (5) @(posedge clk);
        rst <= 1'b0;
        repeat (2) @(posedge clk);

        for (evt = 0; evt < N_EVENTS; evt = evt + 1) begin

            @(posedge clk);
            event_start <= 1'b1;
            sample_valid <= 1'b0;
            sample_in <= {SAMPLE_BITS{1'b0}};

            @(posedge clk);
            event_start <= 1'b0;

            for (i = 0; i < N_SAMPLES; i = i + 1) begin
                sample_valid <= 1'b1;
                sample_in <= sample_mem[evt*N_SAMPLES + i];
                @(posedge clk);
            end

            sample_valid <= 1'b0;
            sample_in <= {SAMPLE_BITS{1'b0}};

            repeat (2) @(posedge clk);

            total_checked = total_checked + 1;

            if (triggered !== expected_trigger[evt]) begin
                $display("ERROR evt=%0d trigger mismatch: got %0d expected %0d",
                         evt, triggered, expected_trigger[evt]);
                errors = errors + 1;
            end

            if (peak_count !== expected_peak_count[evt]) begin
                $display("ERROR evt=%0d peak_count mismatch: got %0d expected %0d",
                         evt, peak_count, expected_peak_count[evt]);
                errors = errors + 1;
            end

            if (peak_index !== expected_peak_index[evt]) begin
                $display("ERROR evt=%0d peak_index mismatch: got %0d expected %0d",
                         evt, peak_index, expected_peak_index[evt]);
                errors = errors + 1;
            end

        end

        $display("------------------------------------------------------------");
        $display("HDL validation completed for 8-bit");
        $display("Total events checked : %0d", total_checked);
        $display("Total errors         : %0d", errors);

        if (errors == 0) begin
            $display("RESULT: PASS");
        end else begin
            $display("RESULT: FAIL");
        end

        $display("------------------------------------------------------------");

        $finish;
    end

endmodule
