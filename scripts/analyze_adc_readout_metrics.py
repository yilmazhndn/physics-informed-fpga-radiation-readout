from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
# Publication-ready ADC/readout metric analysis
# NaI(Tl) synthetic waveform dataset
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
WAVEFORM_DIR = PROJECT_DIR / "waveforms"
FIG_DIR = PROJECT_DIR / "hy"

FIG_DIR.mkdir(parents=True, exist_ok=True)

LABEL_PATH = WAVEFORM_DIR / "waveform_labels.csv"
PARAM_PATH = WAVEFORM_DIR / "waveform_generation_parameters.csv"

ADC_BITS = [8, 10, 12]


# =============================================================================
# Publication plotting style
# =============================================================================

ADC_COLORS = {
    8: "#2F5D8C",
    10: "#B85C38",
    12: "#3A8F6A",
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

REFERENCE_COLOR = "#444444"
GRID_COLOR = "#E6E6E6"
TEXT_COLOR = "#111111"

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
    "figure.titlesize": 9,

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
    "legend.handlelength": 2.4,
    "legend.borderaxespad": 0.3,

    "savefig.dpi": 1200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.025,

    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


# =============================================================================
# Helper plotting functions
# =============================================================================

def polish_axes(ax, grid=True):
    ax.tick_params(which="both", top=True, right=True)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())

    for axis in [ax.xaxis, ax.yaxis]:
        formatter = axis.get_major_formatter()
        if isinstance(formatter, mticker.ScalarFormatter):
            formatter.set_scientific(False)
            formatter.set_useOffset(False)

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
    ax.text(
        0.045,
        0.925,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5),
        zorder=10,
    )


def set_nice_limits(ax, x=None, y=None):
    if x is not None:
        ax.set_xlim(x)
    if y is not None:
        ax.set_ylim(y)


def save_publication_figure(fig, name):
    pdf_path = FIG_DIR / f"{name}.pdf"
    fig.savefig(pdf_path)
    print(f"Saved: {pdf_path}")


# =============================================================================
# Load labels and generation parameters
# =============================================================================

labels = pd.read_csv(LABEL_PATH)
params = pd.read_csv(PARAM_PATH)


def get_param(name, dtype=float):
    value = params.loc[params["parameter"] == name, "value"].iloc[0]
    return dtype(value)


REFERENCE_ENERGY_KEV = get_param("reference_energy_keV", float)
FULL_ENERGY_AMPLITUDE = get_param("full_energy_amplitude", float)
DT_NS = get_param("dt_ns", float)
N_SAMPLES = get_param("n_samples", int)

TIME_NS = np.arange(N_SAMPLES) * DT_NS

edep_true = labels["edep_nai_keV"].to_numpy(dtype=np.float64)
event_class = labels["event_class"].to_numpy()

nonzero_mask = edep_true > 0.0
zero_mask = edep_true == 0.0
full_mask = event_class == "full_energy_like"
partial_mask = event_class == "partial"


# =============================================================================
# Analysis helper functions
# =============================================================================

def load_adc_waveforms(n_bits):
    path = WAVEFORM_DIR / f"waveforms_nai59_{n_bits}bit.npy"
    if not path.exists():
        raise FileNotFoundError(f"Missing waveform file: {path}")
    return np.load(path, mmap_mode="r")


def adc_to_normalized(adc_waveforms, n_bits):
    adc_max = (2 ** n_bits) - 1
    return adc_waveforms.astype(np.float32) / adc_max


def estimate_baseline(normalized_waveforms, n_pretrigger=40):
    return normalized_waveforms[:, :n_pretrigger].mean(axis=1)


def estimate_peak_amplitude(normalized_waveforms, baseline):
    peak = normalized_waveforms.max(axis=1)
    return peak - baseline


def reconstruct_energy_from_amplitude(amplitude_norm):
    return amplitude_norm / FULL_ENERGY_AMPLITUDE * REFERENCE_ENERGY_KEV


def compute_energy_metrics(edep_true, edep_reco, mask):
    err = edep_reco[mask] - edep_true[mask]
    abs_err = np.abs(err)

    return {
        "n_events": int(mask.sum()),
        "bias_keV": float(np.mean(err)),
        "mae_keV": float(np.mean(abs_err)),
        "rmse_keV": float(np.sqrt(np.mean(err ** 2))),
        "median_abs_error_keV": float(np.median(abs_err)),
        "p95_abs_error_keV": float(np.percentile(abs_err, 95)),
    }


def trigger_rates(amplitude_norm, thresholds):
    trigger = amplitude_norm[:, None] >= thresholds[None, :]

    efficiency_nonzero = trigger[nonzero_mask].mean(axis=0)
    efficiency_full = trigger[full_mask].mean(axis=0)
    efficiency_partial = trigger[partial_mask].mean(axis=0)

    if zero_mask.sum() > 0:
        false_rate_zero = trigger[zero_mask].mean(axis=0)
    else:
        false_rate_zero = np.zeros_like(thresholds)

    return efficiency_nonzero, efficiency_full, efficiency_partial, false_rate_zero


# =============================================================================
# Main analysis
# =============================================================================

metrics_rows = []
thresholds = np.linspace(0.0, 0.12, 121)

threshold_results = {}
reco_energy_by_bits = {}
amplitude_by_bits = {}
normalized_waveforms_for_example = {}

full_indices = np.where(full_mask)[0]
if len(full_indices) == 0:
    raise RuntimeError("No full-energy-like event found.")

example_index = int(full_indices[0])

for n_bits in ADC_BITS:
    adc_wf = load_adc_waveforms(n_bits)
    norm_wf = adc_to_normalized(adc_wf, n_bits)

    baseline = estimate_baseline(norm_wf)
    amplitude = estimate_peak_amplitude(norm_wf, baseline)
    edep_reco = reconstruct_energy_from_amplitude(amplitude)

    amplitude_by_bits[n_bits] = amplitude
    reco_energy_by_bits[n_bits] = edep_reco
    normalized_waveforms_for_example[n_bits] = norm_wf[example_index].copy()

    for subset_name, mask in [
        ("nonzero", nonzero_mask),
        ("full_energy_like", full_mask),
        ("partial", partial_mask),
    ]:
        m = compute_energy_metrics(edep_true, edep_reco, mask)
        m.update({
            "adc_bits": n_bits,
            "event_subset": subset_name,
        })
        metrics_rows.append(m)

    eff_nonzero, eff_full, eff_partial, false_zero = trigger_rates(
        amplitude,
        thresholds,
    )

    threshold_results[n_bits] = {
        "eff_nonzero": eff_nonzero,
        "eff_full": eff_full,
        "eff_partial": eff_partial,
        "false_zero": false_zero,
    }


metrics_df = pd.DataFrame(metrics_rows)
metrics_df = metrics_df[
    [
        "adc_bits",
        "event_subset",
        "n_events",
        "bias_keV",
        "mae_keV",
        "rmse_keV",
        "median_abs_error_keV",
        "p95_abs_error_keV",
    ]
]

metrics_df.to_csv(WAVEFORM_DIR / "adc_readout_metrics_summary.csv", index=False)

threshold_table = pd.DataFrame({"threshold_norm": thresholds})

for n_bits in ADC_BITS:
    threshold_table[f"eff_nonzero_{n_bits}bit"] = threshold_results[n_bits]["eff_nonzero"]
    threshold_table[f"eff_full_{n_bits}bit"] = threshold_results[n_bits]["eff_full"]
    threshold_table[f"eff_partial_{n_bits}bit"] = threshold_results[n_bits]["eff_partial"]
    threshold_table[f"false_zero_{n_bits}bit"] = threshold_results[n_bits]["false_zero"]

threshold_table.to_csv(WAVEFORM_DIR / "adc_trigger_threshold_curves.csv", index=False)


# =============================================================================
# Publication-ready figures
# =============================================================================

# -----------------------------------------------------------------------------
# Figure 1: same-event normalized ADC waveform comparison
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(6.25, 3.20), constrained_layout=True)

for n_bits in ADC_BITS:
    ax.step(
        TIME_NS,
        normalized_waveforms_for_example[n_bits],
        where="mid",
        linewidth=1.20,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.set_xlabel("Time [ns]")
ax.set_ylabel("Normalized ADC output")
set_nice_limits(ax, x=(0, 1200), y=(0, 0.9))
polish_axes(ax, grid=True)
ax.legend(loc="upper right", ncol=1)

ax.text(
    0.04,
    0.90,
    rf"$E_{{dep}}={edep_true[example_index]:.2f}$ keV",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=8.5,
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.80, pad=2.0),
)

save_publication_figure(fig, "nai59_adc_waveform_comparison")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 2: energy reconstruction error versus ADC resolution
# -----------------------------------------------------------------------------

plot_df = metrics_df[metrics_df["event_subset"] == "nonzero"].copy()

fig, ax = plt.subplots(figsize=(4.55, 3.30), constrained_layout=True)

ax.plot(
    plot_df["adc_bits"],
    plot_df["mae_keV"],
    marker="o",
    markersize=4.8,
    linewidth=1.30,
    color=ADC_COLORS[8],
    label="MAE",
    zorder=3,
)

ax.plot(
    plot_df["adc_bits"],
    plot_df["rmse_keV"],
    marker="s",
    markersize=4.8,
    linewidth=1.30,
    color=ADC_COLORS[10],
    label="RMSE",
    zorder=3,
)

ax.set_xlabel("ADC resolution [bits]")
ax.set_ylabel("Energy error [keV]")
ax.set_xticks(ADC_BITS)
polish_axes(ax, grid=True)
ax.legend(loc="best")

save_publication_figure(fig, "nai59_energy_error_vs_adc_bits")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 3: trigger performance versus threshold
# -----------------------------------------------------------------------------

fig, axes = plt.subplots(
    1,
    2,
    figsize=(7.25, 3.25),
    sharex=True,
    constrained_layout=True,
)

ax = axes[0]

for n_bits in ADC_BITS:
    ax.plot(
        thresholds,
        100 * threshold_results[n_bits]["eff_nonzero"],
        linewidth=1.30,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.set_xlabel("Threshold")
ax.set_ylabel("Trigger efficiency [%]")
set_nice_limits(ax, x=(thresholds.min(), thresholds.max()), y=(-2, 105))
polish_axes(ax, grid=True)
panel_label(ax, "(a)")
ax.legend(loc="lower left")

ax = axes[1]

for n_bits in ADC_BITS:
    ax.plot(
        thresholds,
        100 * threshold_results[n_bits]["false_zero"],
        linewidth=1.30,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.set_xlabel("Threshold")
ax.set_ylabel("False trigger rate [%]")
set_nice_limits(ax, x=(thresholds.min(), thresholds.max()), y=(-2, 105))
polish_axes(ax, grid=True)
panel_label(ax, "(b)")

save_publication_figure(fig, "nai59_trigger_performance_vs_threshold")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 4: reconstructed energy versus true energy
# -----------------------------------------------------------------------------

rng = np.random.default_rng(20260618)
subsample_size = min(20_000, len(edep_true))
sub_idx = rng.choice(np.arange(len(edep_true)), size=subsample_size, replace=False)

fig, axes = plt.subplots(
    1,
    3,
    figsize=(7.30, 2.85),
    sharex=True,
    sharey=True,
    constrained_layout=True,
)

for ax, n_bits, label in zip(axes, ADC_BITS, ["(a)", "(b)", "(c)"]):
    ax.scatter(
        edep_true[sub_idx],
        reco_energy_by_bits[n_bits][sub_idx],
        s=2.2,
        alpha=0.25,
        color=ADC_COLORS[n_bits],
        linewidths=0,
        rasterized=True,
        zorder=2,
    )

    ax.plot(
        [0, 65],
        [0, 65],
        linestyle="--",
        linewidth=0.9,
        color=REFERENCE_COLOR,
        zorder=3,
    )

    ax.set_title(f"{n_bits}-bit")
    set_nice_limits(ax, x=(0, 65), y=(0, 65))
    polish_axes(ax, grid=True)
    panel_label(ax, label)

axes[0].set_ylabel("Reconstructed energy [keV]")

for ax in axes:
    ax.set_xlabel("True deposited energy [keV]")

save_publication_figure(fig, "nai59_reconstructed_energy_scatter_by_adc_bits")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 5: energy residual distributions
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.35, 3.30), constrained_layout=True)

residual_bins = np.linspace(-8, 8, 161)

for n_bits in ADC_BITS:
    residual = reco_energy_by_bits[n_bits][nonzero_mask] - edep_true[nonzero_mask]

    ax.hist(
        residual,
        bins=residual_bins,
        histtype="step",
        linewidth=1.30,
        density=True,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.axvline(
    0,
    color=REFERENCE_COLOR,
    linewidth=0.9,
    linestyle="--",
    zorder=2,
)

ax.set_xlabel(r"Energy residual, $E_{\mathrm{rec}} - E_{\mathrm{true}}$ [keV]")
ax.set_ylabel("Probability density")
set_nice_limits(ax, x=(residual_bins.min(), residual_bins.max()))
polish_axes(ax, grid=True)
ax.legend(loc="upper right")

save_publication_figure(fig, "nai59_energy_residual_distribution")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 6: compact three-panel metric figure
# -----------------------------------------------------------------------------

nonzero_df = metrics_df[metrics_df["event_subset"] == "nonzero"].copy()

fig, axes = plt.subplots(
    1,
    3,
    figsize=(7.30, 2.90),
    sharex=True,
    constrained_layout=True,
)

metric_specs = [
    ("bias_keV", "Bias [eV]", "(a)", ADC_COLORS[8], 1000.0),
    ("mae_keV", "MAE [keV]", "(b)", ADC_COLORS[10], 1.0),
    ("rmse_keV", "RMSE [keV]", "(c)", ADC_COLORS[12], 1.0),
]

for ax, (metric, ylabel, label, color, scale) in zip(axes, metric_specs):
    y_values = nonzero_df[metric].to_numpy(dtype=float) * scale

    ax.plot(
        nonzero_df["adc_bits"],
        y_values,
        marker="o",
        markersize=4.8,
        linewidth=1.30,
        color=color,
        zorder=3,
    )

    ax.set_xlabel("ADC resolution [bits]")
    ax.set_ylabel(ylabel)
    ax.set_xticks(ADC_BITS)

    y_min = float(np.min(y_values))
    y_max = float(np.max(y_values))
    y_range = y_max - y_min

    if y_range == 0:
        margin = 0.05 * abs(y_max) if y_max != 0 else 1.0
    else:
        margin = 0.18 * y_range

    ax.set_ylim(y_min - margin, y_max + margin)

    polish_axes(ax, grid=True)
    panel_label(ax, label)

save_publication_figure(fig, "nai59_adc_energy_metrics_three_panel")
plt.close(fig)


# =============================================================================
# Print summary
# =============================================================================

print("------------------------------------------------------------")
print("ADC/readout metric analysis completed")
print("------------------------------------------------------------")
print("Saved tables:")
print(f"  {WAVEFORM_DIR / 'adc_readout_metrics_summary.csv'}")
print(f"  {WAVEFORM_DIR / 'adc_trigger_threshold_curves.csv'}")
print("------------------------------------------------------------")
print("Saved PDF figures to:")
print(f"  {FIG_DIR}")
print("------------------------------------------------------------")
print(metrics_df)
print("------------------------------------------------------------")