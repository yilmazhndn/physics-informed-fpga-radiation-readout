from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
# Create Verilog HDL validation files for NaI(Tl) replay-vector dataset
# =============================================================================
#
# Inputs:
#   hdl_vectors/nai59_hdl_manifest.csv
#
# Outputs:
#   hdl/nai59_validation/nai59_peak_trigger.v
#   hdl/nai59_validation/tb_nai59_8bit.v
#   hdl/nai59_validation/tb_nai59_10bit.v
#   hdl/nai59_validation/tb_nai59_12bit.v
#   hdl/nai59_validation/run_hdl_validation.sh
#   hdl/nai59_validation/logs/*.log
#
#   figures/hdl_validation_publication/nai59_hdl_validation_manifest_summary.pdf
#   figures/hdl_validation_publication/nai59_hdl_validation_manifest_summary.svg
#   figures/hdl_validation_publication/nai59_hdl_validation_manifest_summary.png
#   figures/hdl_validation_publication/nai59_hdl_validation_manifest_summary.tiff
#
# Purpose:
#   Validate FPGA-facing replay vectors using a Verilog testbench.
#   The HDL module performs:
#       1. baseline estimation from pre-trigger samples
#       2. threshold trigger decision
#       3. peak-count extraction
#       4. peak-index extraction
#
# =============================================================================


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

HDL_BASE_DIR = PROJECT_DIR / "hdl"
HDL_DIR = HDL_BASE_DIR / "nai59_validation"
HDL_LOG_DIR = HDL_DIR / "logs"

VECTOR_DIR = PROJECT_DIR / "hdl_vectors"
MANIFEST_PATH = VECTOR_DIR / "nai59_hdl_manifest.csv"

FIG_BASE_DIR = PROJECT_DIR / "figures"
FIG_DIR = FIG_BASE_DIR / "hdl_validation_publication"

HDL_DIR.mkdir(parents=True, exist_ok=True)
HDL_LOG_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Publication-style plotting settings
# -----------------------------------------------------------------------------

ADC_COLORS = {
    8: "#1F5AA6",     # vivid royal blue
    10: "#D62728",    # clear crimson red
    12: "#009E73",    # vivid teal
}

ADC_LINESTYLES = {
    8: "-",
    10: "--",
    12: "-.",
}

ADC_MARKERS = {
    8: "o",
    10: "s",
    12: "^",
}

REFERENCE_COLOR = "#555555"
GRID_COLOR = "#E5E5E5"
TEXT_COLOR = "#111111"
STEM_COLOR = "#B8B8B8"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",

    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,

    "axes.linewidth": 0.75,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,

    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "xtick.minor.size": 2,
    "ytick.minor.size": 2,
    "xtick.major.width": 0.75,
    "ytick.major.width": 0.75,
    "xtick.minor.width": 0.55,
    "ytick.minor.width": 0.55,

    "legend.frameon": False,
    "legend.handlelength": 2.2,

    "savefig.dpi": 1200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.025,

    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})


def polish_axes(ax, grid=True):
    """Apply journal-style formatting to one axis."""
    ax.tick_params(which="both", top=True, right=True)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.ticklabel_format(axis="both", style="plain", useOffset=False)

    if grid:
        ax.grid(
            True,
            which="major",
            color=GRID_COLOR,
            linewidth=0.45,
            alpha=0.75,
            zorder=0,
        )

    for spine in ax.spines.values():
        spine.set_linewidth(0.75)


def panel_label(ax, label):
    """Add clean panel label such as (a), (b)."""
    ax.text(
        0.045,
        0.925,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            alpha=0.85,
            pad=1.5,
        ),
        zorder=10,
    )


def save_publication_figure(fig, name):
    """Save one figure in vector and high-resolution raster formats."""
    pdf_path = FIG_DIR / f"{name}.pdf"
    svg_path = FIG_DIR / f"{name}.svg"
    png_path = FIG_DIR / f"{name}.png"
    tiff_path = FIG_DIR / f"{name}.tiff"

    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    fig.savefig(png_path, dpi=1200)
    fig.savefig(tiff_path, dpi=1200)

    print(f"Saved figure: {pdf_path}")
    print(f"Saved figure: {svg_path}")
    print(f"Saved figure: {png_path}")
    print(f"Saved figure: {tiff_path}")


# =============================================================================
# HDL module
# =============================================================================

MODULE_TEXT = r'''
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
'''.strip()


# =============================================================================
# Testbench template
# =============================================================================

def make_testbench_text(bits, threshold_counts, n_events, n_samples, pretrigger_samples):
    return f'''
// =============================================================================
// Testbench for {bits}-bit NaI(Tl) HDL replay vectors
// =============================================================================

`timescale 1ns/1ps

module tb_nai59_{bits}bit;

    localparam integer SAMPLE_BITS = {bits};
    localparam integer N_EVENTS = {n_events};
    localparam integer N_SAMPLES = {n_samples};
    localparam integer PRETRIGGER_SAMPLES = {pretrigger_samples};
    localparam integer THRESHOLD_COUNTS = {threshold_counts};

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst = 1'b1;
    reg event_start = 1'b0;
    reg sample_valid = 1'b0;
    reg [SAMPLE_BITS-1:0] sample_in = {{SAMPLE_BITS{{1'b0}}}};

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
        $display("Starting HDL validation for {bits}-bit replay vectors");
        $display("N_EVENTS          = %0d", N_EVENTS);
        $display("N_SAMPLES         = %0d", N_SAMPLES);
        $display("THRESHOLD_COUNTS  = %0d", THRESHOLD_COUNTS);
        $display("------------------------------------------------------------");

        $readmemh("../../hdl_vectors/nai59_{bits}bit_flat.mem", sample_mem);
        $readmemh("../../hdl_vectors/nai59_{bits}bit_expected_trigger.mem", expected_trigger);
        $readmemh("../../hdl_vectors/nai59_{bits}bit_expected_peak_count.mem", expected_peak_count);
        $readmemh("../../hdl_vectors/nai59_{bits}bit_expected_peak_index.mem", expected_peak_index);

        errors = 0;
        total_checked = 0;

        repeat (5) @(posedge clk);
        rst <= 1'b0;
        repeat (2) @(posedge clk);

        for (evt = 0; evt < N_EVENTS; evt = evt + 1) begin

            @(posedge clk);
            event_start <= 1'b1;
            sample_valid <= 1'b0;
            sample_in <= {{SAMPLE_BITS{{1'b0}}}};

            @(posedge clk);
            event_start <= 1'b0;

            for (i = 0; i < N_SAMPLES; i = i + 1) begin
                sample_valid <= 1'b1;
                sample_in <= sample_mem[evt*N_SAMPLES + i];
                @(posedge clk);
            end

            sample_valid <= 1'b0;
            sample_in <= {{SAMPLE_BITS{{1'b0}}}};

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
        $display("HDL validation completed for {bits}-bit");
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
'''.strip()


# =============================================================================
# Publication-ready manifest figure
# =============================================================================

def create_manifest_summary_figure(manifest):
    """
    Create a compact publication-style summary figure of the HDL validation
    replay-vector manifest.

    Panel (a) is intentionally drawn as a dot/lollipop summary instead of a bar
    chart. Since the number of replay events is typically identical across ADC
    resolutions, large bars look visually heavy without adding much information.
    """

    manifest = manifest.sort_values("adc_bits").copy()

    adc_bits = manifest["adc_bits"].astype(int).to_numpy()
    n_events = manifest["n_events"].astype(int).to_numpy()
    threshold_counts = manifest["threshold_counts"].astype(int).to_numpy()

    colors = [ADC_COLORS.get(int(bits), "#555555") for bits in adc_bits]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.25, 3.20),
        constrained_layout=True,
    )

    # -------------------------------------------------------------------------
    # Panel (a): replay event count summary
    # Dot/lollipop style; lighter and more elegant than full bars.
    # -------------------------------------------------------------------------

    ax = axes[0]

    y_min = 0
    y_max = max(n_events) * 1.12

    for x, y, color in zip(adc_bits, n_events, colors):
        ax.vlines(
            x,
            y_min,
            y,
            color=STEM_COLOR,
            linewidth=1.05,
            alpha=0.85,
            zorder=1,
        )
        ax.scatter(
            x,
            y,
            s=46,
            color=color,
            edgecolor="#222222",
            linewidth=0.45,
            zorder=3,
        )
        ax.text(
            x,
            y + 0.035 * y_max,
            f"{y:,}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=TEXT_COLOR,
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.75,
                pad=1.0,
            ),
            zorder=4,
        )

    ax.set_xlabel("ADC resolution [bits]")
    ax.set_ylabel("Replay events [count]")
    ax.set_xticks(adc_bits)
    ax.set_xlim(min(adc_bits) - 0.55, max(adc_bits) + 0.55)
    ax.set_ylim(y_min, y_max)

    polish_axes(ax, grid=True)
    panel_label(ax, "(a)")

    # -------------------------------------------------------------------------
    # Panel (b): threshold counts versus ADC resolution
    # -------------------------------------------------------------------------

    ax = axes[1]

    ax.plot(
        adc_bits,
        threshold_counts,
        marker="o",
        markersize=5.0,
        linewidth=1.35,
        color=ADC_COLORS[8],
        markerfacecolor=ADC_COLORS[8],
        markeredgecolor="#222222",
        markeredgewidth=0.45,
        zorder=3,
    )

    for x, y in zip(adc_bits, threshold_counts):
        ax.text(
            x,
            y + 0.045 * max(threshold_counts),
            f"{y}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=TEXT_COLOR,
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.75,
                pad=1.0,
            ),
            zorder=4,
        )

    ax.set_xlabel("ADC resolution [bits]")
    ax.set_ylabel("Trigger threshold [ADC counts]")
    ax.set_xticks(adc_bits)
    ax.set_xlim(min(adc_bits) - 0.55, max(adc_bits) + 0.55)

    y_lower = max(0, min(threshold_counts) - 0.12 * max(threshold_counts))
    y_upper = max(threshold_counts) * 1.18
    ax.set_ylim(y_lower, y_upper)

    polish_axes(ax, grid=True)
    panel_label(ax, "(b)")

    save_publication_figure(fig, "nai59_hdl_validation_manifest_summary")
    plt.close(fig)


# =============================================================================
# Main
# =============================================================================

def main():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_PATH}\n"
            "Run scripts/export_hdl_replay_vectors.py first."
        )

    manifest = pd.read_csv(MANIFEST_PATH)

    module_path = HDL_DIR / "nai59_peak_trigger.v"
    module_path.write_text(MODULE_TEXT + "\n")

    run_lines = []
    run_lines.append("#!/bin/bash")
    run_lines.append("set -e")
    run_lines.append("")
    run_lines.append("cd \"$(dirname \"$0\")\"")
    run_lines.append("mkdir -p logs")
    run_lines.append("")
    run_lines.append("echo \"Running NaI(Tl) HDL validation...\"")
    run_lines.append("echo \"Working directory: $(pwd)\"")
    run_lines.append("")

    for _, row in manifest.iterrows():
        bits = int(row["adc_bits"])
        n_events = int(row["n_events"])
        n_samples = int(row["n_samples_per_event"])
        pretrigger = int(row["pretrigger_samples"])
        threshold_counts = int(row["threshold_counts"])

        tb_text = make_testbench_text(
            bits=bits,
            threshold_counts=threshold_counts,
            n_events=n_events,
            n_samples=n_samples,
            pretrigger_samples=pretrigger,
        )

        tb_path = HDL_DIR / f"tb_nai59_{bits}bit.v"
        tb_path.write_text(tb_text + "\n")

        run_lines.append(f"echo \"--- {bits}-bit validation ---\"")
        run_lines.append(
            f"iverilog -g2012 -o tb_nai59_{bits}bit.vvp "
            f"nai59_peak_trigger.v tb_nai59_{bits}bit.v"
        )
        run_lines.append(
            f"vvp tb_nai59_{bits}bit.vvp | tee logs/nai59_{bits}bit_validation.log"
        )
        run_lines.append("")

    run_script = HDL_DIR / "run_hdl_validation.sh"
    run_script.write_text("\n".join(run_lines) + "\n")
    run_script.chmod(0o755)

    create_manifest_summary_figure(manifest)

    print("------------------------------------------------------------")
    print("HDL validation files created")
    print("------------------------------------------------------------")
    print(f"Saved HDL module   : {module_path}")

    for _, row in manifest.iterrows():
        bits = int(row["adc_bits"])
        print(f"Saved testbench    : {HDL_DIR / f'tb_nai59_{bits}bit.v'}")

    print(f"Saved run script   : {run_script}")
    print(f"Saved HDL logs to  : {HDL_LOG_DIR}")
    print(f"Saved figures to   : {FIG_DIR}")
    print("------------------------------------------------------------")
    print("To run validation:")
    print("  cd ~/Desktop/B4a")
    print("  bash hdl/nai59_validation/run_hdl_validation.sh")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
