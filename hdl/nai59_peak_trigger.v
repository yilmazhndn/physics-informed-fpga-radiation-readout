// =============================================================================
// NaI(Tl) FPGA-facing peak and threshold trigger block
// =============================================================================
//
// This module implements a simple streaming readout algorithm:
//
//   - estimate the baseline from the first PRETRIGGER_SAMPLES samples
//   - detect whether the waveform crosses baseline + threshold
//   - extract the peak ADC count
//   - extract the peak sample index
//
// It is intended as a reproducible HDL validation block for synthetic
// FPGA-facing detector waveform replay vectors.
//
// =============================================================================

`timescale 1ns/1ps

module nai59_peak_trigger #(
    parameter integer SAMPLE_BITS = 12,
    parameter integer N_SAMPLES = 500,
    parameter integer PRETRIGGER_SAMPLES = 40,
    parameter integer THRESHOLD_COUNTS = 61
)(
    input  wire                     clk,
    input  wire                     rst,
    input  wire                     event_start,
    input  wire                     sample_valid,
    input  wire [SAMPLE_BITS-1:0]   sample_in,

    output reg                      event_done,
    output reg                      triggered,
    output reg [SAMPLE_BITS-1:0]    peak_count,
    output reg [15:0]               peak_index,
    output reg [SAMPLE_BITS-1:0]    baseline_count
);

    reg [15:0] sample_index;
    reg [31:0] baseline_sum;
    reg [31:0] trigger_level;

    always @(posedge clk) begin
        if (rst) begin
            sample_index   <= 16'd0;
            baseline_sum   <= 32'd0;
            baseline_count <= {SAMPLE_BITS{1'b0}};
            trigger_level  <= 32'd0;
            peak_count     <= {SAMPLE_BITS{1'b0}};
            peak_index     <= 16'd0;
            triggered      <= 1'b0;
            event_done     <= 1'b0;
        end else begin

            event_done <= 1'b0;

            if (event_start) begin
                sample_index   <= 16'd0;
                baseline_sum   <= 32'd0;
                baseline_count <= {SAMPLE_BITS{1'b0}};
                trigger_level  <= 32'd0;
                peak_count     <= {SAMPLE_BITS{1'b0}};
                peak_index     <= 16'd0;
                triggered      <= 1'b0;
                event_done     <= 1'b0;
            end else if (sample_valid) begin

                // Peak finder.
                // The strict ">" comparison keeps the first occurrence if
                // multiple samples have the same maximum value.
                if (sample_index == 16'd0) begin
                    peak_count <= sample_in;
                    peak_index <= 16'd0;
                end else if (sample_in > peak_count) begin
                    peak_count <= sample_in;
                    peak_index <= sample_index;
                end

                // Baseline estimation from first PRETRIGGER_SAMPLES samples.
                if (sample_index < PRETRIGGER_SAMPLES) begin
                    baseline_sum <= baseline_sum + sample_in;

                    if (sample_index == PRETRIGGER_SAMPLES - 1) begin
                        baseline_count <= (baseline_sum + sample_in) / PRETRIGGER_SAMPLES;
                        trigger_level  <= ((baseline_sum + sample_in) / PRETRIGGER_SAMPLES)
                                          + THRESHOLD_COUNTS;
                    end
                end else begin
                    // Threshold trigger after pre-trigger region.
                    if (sample_in >= trigger_level) begin
                        triggered <= 1'b1;
                    end
                end

                // End of event.
                if (sample_index == N_SAMPLES - 1) begin
                    event_done <= 1'b1;
                end

                sample_index <= sample_index + 16'd1;
            end
        end
    end

endmodule
