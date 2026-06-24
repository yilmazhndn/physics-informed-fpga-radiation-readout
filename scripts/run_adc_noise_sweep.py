from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =============================================================================
# ADC noise/SNR sweep for NaI(Tl) synthetic waveform readout
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "build" / "nai59_edep_events.csv"

WAVEFORM_DIR = PROJECT_DIR / "waveforms"
FIG_DIR = PROJECT_DIR / "hy"

WAVEFORM_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 20260618
rng = np.random.default_rng(RANDOM_SEED)

N_WAVEFORMS = 100_000
RANDOM_SAMPLE_EVENTS = True

SAMPLING_RATE_HZ = 250e6
DT_NS = 1e9 / SAMPLING_RATE_HZ
WINDOW_NS = 2000.0
N_SAMPLES = int(WINDOW_NS / DT_NS)
TIME_NS = np.arange(N_SAMPLES) * DT_NS

TAU_RISE_NS = 20.0
TAU_DECAY_NS = 250.0
T0_NS = 200.0

REFERENCE_ENERGY_KEV = 59.5
FULL_ENERGY_AMPLITUDE = 0.70
BASELINE_FRACTION = 0.10
GAIN_SIGMA_FRACTION = 0.015

NOISE_SIGMA_LEVELS = [0.001, 0.003, 0.006]
ADC_BITS = [8, 10, 12]

THRESHOLDS = np.linspace(0.0, 0.12, 121)
FALSE_TRIGGER_LIMITS_PERCENT = [1.0, 0.1, 0.01]

# Match the publication waveform-figure typography.
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
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "xtick.minor.size": 2,
    "ytick.minor.size": 2,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.minor.width": 0.6,
    "ytick.minor.width": 0.6,
    "legend.frameon": False,
    "savefig.dpi": 600,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Color palette matched to the representative waveform figures:
# blue, red and neutral gray.
NOISE_STYLES = {
    0.001: {
        "color": "#1f5aa6",
        "marker": "o",
        "linestyle": "-",
        "linewidth": 1.25,
        "markersize": 4.4,
    },
    0.003: {
        "color": "#d62728",
        "marker": "s",
        "linestyle": "--",
        "linewidth": 1.25,
        "markersize": 4.4,
    },
    0.006: {
        "color": "#6e6e6e",
        "marker": "^",
        "linestyle": "-.",
        "linewidth": 1.25,
        "markersize": 4.6,
    },
}

BIT_STYLES = {
    8: {
        "color": "#1f5aa6",
        "marker": "o",
        "linestyle": "-",
        "linewidth": 1.25,
        "markersize": 4.4,
    },
    10: {
        "color": "#d62728",
        "marker": "s",
        "linestyle": "--",
        "linewidth": 1.25,
        "markersize": 4.4,
    },
    12: {
        "color": "#6e6e6e",
        "marker": "^",
        "linestyle": "-.",
        "linewidth": 1.25,
        "markersize": 4.6,
    },
}


def nai_pulse_shape(time_ns, t0_ns, tau_rise_ns, tau_decay_ns):
    shifted_t = time_ns - t0_ns
    pulse = np.zeros_like(time_ns, dtype=np.float64)

    mask = shifted_t >= 0.0
    t = shifted_t[mask]
    pulse[mask] = (1.0 - np.exp(-t / tau_rise_ns)) * np.exp(-t / tau_decay_ns)

    max_value = pulse.max()
    if max_value > 0:
        pulse /= max_value

    return pulse


def quantize_adc(analog_waveforms, n_bits):
    adc_max = (2 ** n_bits) - 1
    clipped = np.clip(analog_waveforms, 0.0, 1.0)
    quantized = np.rint(clipped * adc_max)

    if n_bits <= 8:
        return quantized.astype(np.uint8)

    return quantized.astype(np.uint16)


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


def classify_event(edep_kev):
    if edep_kev == 0:
        return "zero"
    if edep_kev <= 58.0:
        return "partial"
    return "full_energy_like"


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


def compute_trigger_curves(amplitude_norm, thresholds, nonzero_mask, full_mask, partial_mask, zero_mask):
    trigger = amplitude_norm[:, None] >= thresholds[None, :]

    eff_nonzero = trigger[nonzero_mask].mean(axis=0)
    eff_full = trigger[full_mask].mean(axis=0)
    eff_partial = trigger[partial_mask].mean(axis=0)

    if zero_mask.sum() > 0:
        false_zero = trigger[zero_mask].mean(axis=0)
    else:
        false_zero = np.zeros_like(thresholds)

    return eff_nonzero, eff_full, eff_partial, false_zero


def select_operating_points(threshold_df, noise_sigma, adc_bits):
    rows = []

    false_col = f"false_zero_{adc_bits}bit"
    nonzero_col = f"eff_nonzero_{adc_bits}bit"
    full_col = f"eff_full_{adc_bits}bit"
    partial_col = f"eff_partial_{adc_bits}bit"

    for limit_percent in FALSE_TRIGGER_LIMITS_PERCENT:
        limit_fraction = limit_percent / 100.0
        valid = threshold_df[threshold_df[false_col] <= limit_fraction]

        if len(valid) == 0:
            rows.append({
                "noise_sigma_fraction": noise_sigma,
                "adc_bits": adc_bits,
                "false_trigger_constraint_percent": limit_percent,
                "threshold_norm": np.nan,
                "false_trigger_rate_percent": np.nan,
                "eff_nonzero_percent": np.nan,
                "eff_full_energy_like_percent": np.nan,
                "eff_partial_percent": np.nan,
            })
            continue

        selected = valid.iloc[0]

        rows.append({
            "noise_sigma_fraction": noise_sigma,
            "adc_bits": adc_bits,
            "false_trigger_constraint_percent": limit_percent,
            "threshold_norm": selected["threshold_norm"],
            "false_trigger_rate_percent": 100.0 * selected[false_col],
            "eff_nonzero_percent": 100.0 * selected[nonzero_col],
            "eff_full_energy_like_percent": 100.0 * selected[full_col],
            "eff_partial_percent": 100.0 * selected[partial_col],
        })

    return rows


def style_publication_axis(ax):
    ax.grid(True, which="major", color="0.90", linewidth=0.5)
    ax.grid(True, which="minor", color="0.95", linewidth=0.35)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.tick_params(which="both", top=True, right=True)


def place_legend_above(ax):
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        borderaxespad=0.0,
        columnspacing=1.2,
        handlelength=2.2,
        handletextpad=0.5,
    )


def save_figure(fig, path_without_suffix):
    fig.savefig(path_without_suffix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path_without_suffix.with_suffix(".png"), dpi=600, bbox_inches="tight")


if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Could not find input file: {DATA_PATH}\n"
        "Make sure build/nai59_edep_events.csv exists."
    )

df = pd.read_csv(DATA_PATH)

required_columns = {"event_id", "edep_nai_keV", "track_nai_mm"}
missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise ValueError(f"Missing required columns in CSV: {missing_columns}")

if N_WAVEFORMS > len(df):
    raise ValueError(
        f"N_WAVEFORMS={N_WAVEFORMS} is larger than available events={len(df)}."
    )

if RANDOM_SAMPLE_EVENTS:
    selected = df.sample(n=N_WAVEFORMS, random_state=RANDOM_SEED).reset_index(drop=True)
else:
    selected = df.iloc[:N_WAVEFORMS].copy().reset_index(drop=True)

edep_true = selected["edep_nai_keV"].to_numpy(dtype=np.float64)
event_class = np.array([classify_event(e) for e in edep_true])

nonzero_mask = edep_true > 0.0
zero_mask = edep_true == 0.0
full_mask = event_class == "full_energy_like"
partial_mask = event_class == "partial"

template = nai_pulse_shape(
    TIME_NS,
    t0_ns=T0_NS,
    tau_rise_ns=TAU_RISE_NS,
    tau_decay_ns=TAU_DECAY_NS,
)

ideal_amplitude = FULL_ENERGY_AMPLITUDE * (edep_true / REFERENCE_ENERGY_KEV)

gain_factor = rng.normal(
    loc=1.0,
    scale=GAIN_SIGMA_FRACTION,
    size=N_WAVEFORMS,
)

true_amplitude = ideal_amplitude * gain_factor
true_amplitude = np.clip(true_amplitude, 0.0, 0.95)

analog_clean = BASELINE_FRACTION + true_amplitude[:, None] * template[None, :]
analog_clean = analog_clean.astype(np.float32)

metrics_rows = []
all_operating_rows = []
all_threshold_tables = []

for noise_sigma in NOISE_SIGMA_LEVELS:
    local_rng = np.random.default_rng(RANDOM_SEED + int(noise_sigma * 1_000_000))

    noise = local_rng.normal(
        loc=0.0,
        scale=noise_sigma,
        size=analog_clean.shape,
    ).astype(np.float32)

    analog_noisy = np.clip(analog_clean + noise, 0.0, 1.0)

    threshold_table = pd.DataFrame({"threshold_norm": THRESHOLDS})
    threshold_table["noise_sigma_fraction"] = noise_sigma

    for n_bits in ADC_BITS:
        adc_waveforms = quantize_adc(analog_noisy, n_bits)
        norm_wf = adc_to_normalized(adc_waveforms, n_bits)

        baseline = estimate_baseline(norm_wf)
        amplitude = estimate_peak_amplitude(norm_wf, baseline)
        edep_reco = reconstruct_energy_from_amplitude(amplitude)

        for subset_name, mask in [
            ("nonzero", nonzero_mask),
            ("full_energy_like", full_mask),
            ("partial", partial_mask),
        ]:
            m = compute_energy_metrics(edep_true, edep_reco, mask)
            m.update({
                "noise_sigma_fraction": noise_sigma,
                "adc_bits": n_bits,
                "event_subset": subset_name,
            })
            metrics_rows.append(m)

        eff_nonzero, eff_full, eff_partial, false_zero = compute_trigger_curves(
            amplitude,
            THRESHOLDS,
            nonzero_mask,
            full_mask,
            partial_mask,
            zero_mask,
        )

        threshold_table[f"eff_nonzero_{n_bits}bit"] = eff_nonzero
        threshold_table[f"eff_full_{n_bits}bit"] = eff_full
        threshold_table[f"eff_partial_{n_bits}bit"] = eff_partial
        threshold_table[f"false_zero_{n_bits}bit"] = false_zero

    for n_bits in ADC_BITS:
        all_operating_rows.extend(
            select_operating_points(threshold_table, noise_sigma, n_bits)
        )

    all_threshold_tables.append(threshold_table)

metrics_df = pd.DataFrame(metrics_rows)
metrics_df = metrics_df[
    [
        "noise_sigma_fraction",
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

metrics_path = WAVEFORM_DIR / "adc_noise_sweep_metrics.csv"
metrics_df.to_csv(metrics_path, index=False)

operating_df = pd.DataFrame(all_operating_rows)
operating_path = WAVEFORM_DIR / "adc_noise_sweep_trigger_operating_points.csv"
operating_df.to_csv(operating_path, index=False)

threshold_curves_df = pd.concat(all_threshold_tables, ignore_index=True)
threshold_curves_path = WAVEFORM_DIR / "adc_noise_sweep_threshold_curves.csv"
threshold_curves_df.to_csv(threshold_curves_path, index=False)

plot_df = metrics_df[metrics_df["event_subset"] == "nonzero"]

fig, ax = plt.subplots(figsize=(5.6, 3.4))
fig.subplots_adjust(top=0.82)

for noise_sigma in NOISE_SIGMA_LEVELS:
    sub = plot_df[plot_df["noise_sigma_fraction"] == noise_sigma].sort_values("adc_bits")
    ax.plot(
        sub["adc_bits"],
        sub["rmse_keV"],
        label=rf"$\sigma_n={noise_sigma:.3f}$",
        **NOISE_STYLES[noise_sigma],
    )

ax.set_xlabel("ADC resolution [bits]")
ax.set_ylabel("Energy RMSE [keV]")
ax.set_xticks(ADC_BITS)
style_publication_axis(ax)
place_legend_above(ax)
save_figure(fig, FIG_DIR / "nai59_noise_sweep_rmse_vs_bits")
plt.close(fig)

fig, ax = plt.subplots(figsize=(5.6, 3.4))
fig.subplots_adjust(top=0.82)

for noise_sigma in NOISE_SIGMA_LEVELS:
    sub = plot_df[plot_df["noise_sigma_fraction"] == noise_sigma].sort_values("adc_bits")
    ax.plot(
        sub["adc_bits"],
        sub["mae_keV"],
        label=rf"$\sigma_n={noise_sigma:.3f}$",
        **NOISE_STYLES[noise_sigma],
    )

ax.set_xlabel("ADC resolution [bits]")
ax.set_ylabel("Energy MAE [keV]")
ax.set_xticks(ADC_BITS)
style_publication_axis(ax)
place_legend_above(ax)
save_figure(fig, FIG_DIR / "nai59_noise_sweep_mae_vs_bits")
plt.close(fig)

nominal_noise = 0.003
nominal_threshold = threshold_curves_df[
    threshold_curves_df["noise_sigma_fraction"] == nominal_noise
]

fig, ax = plt.subplots(figsize=(5.8, 3.4))
fig.subplots_adjust(top=0.82)

for n_bits in ADC_BITS:
    ax.plot(
        nominal_threshold["threshold_norm"],
        100.0 * nominal_threshold[f"eff_nonzero_{n_bits}bit"],
        label=f"{n_bits}-bit",
        **BIT_STYLES[n_bits],
    )

ax.set_xlabel("Trigger threshold above baseline")
ax.set_ylabel("Trigger efficiency [%]")
ax.set_xlim(0.0, 0.12)
ax.set_ylim(0.0, 105.0)
style_publication_axis(ax)
place_legend_above(ax)
save_figure(fig, FIG_DIR / "nai59_noise_sweep_trigger_efficiency_nominal")
plt.close(fig)

fig, ax = plt.subplots(figsize=(5.8, 3.4))
fig.subplots_adjust(top=0.82)

for n_bits in ADC_BITS:
    ax.plot(
        nominal_threshold["threshold_norm"],
        100.0 * nominal_threshold[f"false_zero_{n_bits}bit"],
        label=f"{n_bits}-bit",
        **BIT_STYLES[n_bits],
    )

ax.set_xlabel("Trigger threshold above baseline")
ax.set_ylabel("False trigger rate [%]")
ax.set_xlim(0.0, 0.12)
ax.set_ylim(0.0, 105.0)
style_publication_axis(ax)
place_legend_above(ax)
save_figure(fig, FIG_DIR / "nai59_noise_sweep_false_trigger_nominal")
plt.close(fig)

target_constraint = 0.1
op_sub = operating_df[
    operating_df["false_trigger_constraint_percent"] == target_constraint
]

fig, ax = plt.subplots(figsize=(5.6, 3.4))
fig.subplots_adjust(top=0.82)

for n_bits in ADC_BITS:
    sub = op_sub[op_sub["adc_bits"] == n_bits].sort_values("noise_sigma_fraction")
    ax.plot(
        sub["noise_sigma_fraction"],
        sub["threshold_norm"],
        label=f"{n_bits}-bit",
        **BIT_STYLES[n_bits],
    )

ax.set_xlabel("Noise standard deviation")
ax.set_ylabel("Selected threshold")
style_publication_axis(ax)
place_legend_above(ax)
save_figure(fig, FIG_DIR / "nai59_noise_sweep_threshold_for_false_trigger")
plt.close(fig)

print("------------------------------------------------------------")
print("ADC noise/SNR sweep completed")
print("------------------------------------------------------------")
print(f"Input Geant4 file        : {DATA_PATH}")
print(f"Number of waveforms      : {N_WAVEFORMS:,}")
print(f"ADC bits                 : {ADC_BITS}")
print(f"Noise sigma levels       : {NOISE_SIGMA_LEVELS}")
print("------------------------------------------------------------")
print("Saved tables:")
print(f"  {metrics_path}")
print(f"  {operating_path}")
print(f"  {threshold_curves_path}")
print("------------------------------------------------------------")
print("Saved figures:")
print(f"  {FIG_DIR / 'nai59_noise_sweep_rmse_vs_bits.pdf'}")
print(f"  {FIG_DIR / 'nai59_noise_sweep_mae_vs_bits.pdf'}")
print(f"  {FIG_DIR / 'nai59_noise_sweep_trigger_efficiency_nominal.pdf'}")
print(f"  {FIG_DIR / 'nai59_noise_sweep_false_trigger_nominal.pdf'}")
print(f"  {FIG_DIR / 'nai59_noise_sweep_threshold_for_false_trigger.pdf'}")
print("------------------------------------------------------------")

print("Energy metrics, nonzero events:")
print(
    metrics_df[metrics_df["event_subset"] == "nonzero"]
    .sort_values(["noise_sigma_fraction", "adc_bits"])
    .to_string(index=False)
)

print("------------------------------------------------------------")
print("Operating points:")
print(operating_df.to_string(index=False))
print("------------------------------------------------------------")