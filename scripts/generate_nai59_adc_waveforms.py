from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
# NaI(Tl) ADC waveform generation from Geant4 energy-deposition output
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "build" / "nai59_edep_events.csv"

WAVEFORM_DIR = PROJECT_DIR / "waveforms"
FIG_DIR = PROJECT_DIR / "hy"

WAVEFORM_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Reproducibility and settings
# =============================================================================

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
NOISE_SIGMA_FRACTION = 0.003

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

CLASS_COLORS = {
    "zero": "#6E6E6E",
    "partial": "#3A8F6A",
    "full-energy-like": "#2F5D8C",
    "full_energy_like": "#2F5D8C",
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
# Helper functions
# =============================================================================

def polish_axes(ax, grid=True, minor_ticks=True):
    ax.tick_params(which="both", top=True, right=True)

    if minor_ticks:
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


def save_publication_figure(fig, name):
    pdf_path = FIG_DIR / f"{name}.pdf"
    fig.savefig(pdf_path)
    print(f"Saved figure: {pdf_path}")


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
    if n_bits <= 16:
        return quantized.astype(np.uint16)

    return quantized.astype(np.uint32)


def reconstruct_normalized_from_adc(adc_waveforms, n_bits):
    adc_max = (2 ** n_bits) - 1
    return adc_waveforms.astype(np.float64) / adc_max


def classify_event(edep_kev):
    if edep_kev == 0:
        return "zero"
    if edep_kev <= 58.0:
        return "partial"
    return "full_energy_like"


def display_class_name(name):
    if name == "full_energy_like":
        return "full-energy-like"
    return name


# =============================================================================
# Load Geant4 energy-deposition data
# =============================================================================

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

event_ids = selected["event_id"].to_numpy(dtype=np.int64)
edep_kev = selected["edep_nai_keV"].to_numpy(dtype=np.float64)
track_mm = selected["track_nai_mm"].to_numpy(dtype=np.float64)


# =============================================================================
# Generate analog waveforms
# =============================================================================

template = nai_pulse_shape(
    TIME_NS,
    t0_ns=T0_NS,
    tau_rise_ns=TAU_RISE_NS,
    tau_decay_ns=TAU_DECAY_NS,
)

ideal_amplitude = FULL_ENERGY_AMPLITUDE * (edep_kev / REFERENCE_ENERGY_KEV)

gain_factor = rng.normal(
    loc=1.0,
    scale=GAIN_SIGMA_FRACTION,
    size=N_WAVEFORMS,
)

true_amplitude = ideal_amplitude * gain_factor
true_amplitude = np.clip(true_amplitude, 0.0, 0.95)

analog_clean = BASELINE_FRACTION + true_amplitude[:, None] * template[None, :]

noise = rng.normal(
    loc=0.0,
    scale=NOISE_SIGMA_FRACTION,
    size=analog_clean.shape,
)

analog_noisy = analog_clean + noise
analog_noisy = np.clip(analog_noisy, 0.0, 1.0).astype(np.float32)


# =============================================================================
# Quantize at 8, 10 and 12 bits
# =============================================================================

adc_waveforms = {}

for n_bits in ADC_BITS:
    adc_waveforms[n_bits] = quantize_adc(analog_noisy, n_bits)
    out_path = WAVEFORM_DIR / f"waveforms_nai59_{n_bits}bit.npy"
    np.save(out_path, adc_waveforms[n_bits])

np.save(WAVEFORM_DIR / "waveforms_nai59_analog_noisy_float32.npy", analog_noisy)


# =============================================================================
# Save labels and parameters
# =============================================================================

event_class = np.array([classify_event(e) for e in edep_kev])

labels = pd.DataFrame({
    "dataset_index": np.arange(N_WAVEFORMS, dtype=np.int64),
    "geant4_event_id": event_ids,
    "edep_nai_keV": edep_kev,
    "track_nai_mm": track_mm,
    "event_class": event_class,
    "true_amplitude_norm": true_amplitude,
    "baseline_fraction": BASELINE_FRACTION,
    "noise_sigma_fraction": NOISE_SIGMA_FRACTION,
    "sampling_rate_Hz": SAMPLING_RATE_HZ,
    "dt_ns": DT_NS,
    "window_ns": WINDOW_NS,
    "n_samples": N_SAMPLES,
    "t0_ns": T0_NS,
    "tau_rise_ns": TAU_RISE_NS,
    "tau_decay_ns": TAU_DECAY_NS,
})

labels.to_csv(WAVEFORM_DIR / "waveform_labels.csv", index=False)

parameters = pd.DataFrame({
    "parameter": [
        "random_seed",
        "n_waveforms",
        "sampling_rate_Hz",
        "dt_ns",
        "window_ns",
        "n_samples",
        "t0_ns",
        "tau_rise_ns",
        "tau_decay_ns",
        "reference_energy_keV",
        "full_energy_amplitude",
        "baseline_fraction",
        "gain_sigma_fraction",
        "noise_sigma_fraction",
        "adc_bits",
    ],
    "value": [
        RANDOM_SEED,
        N_WAVEFORMS,
        SAMPLING_RATE_HZ,
        DT_NS,
        WINDOW_NS,
        N_SAMPLES,
        T0_NS,
        TAU_RISE_NS,
        TAU_DECAY_NS,
        REFERENCE_ENERGY_KEV,
        FULL_ENERGY_AMPLITUDE,
        BASELINE_FRACTION,
        GAIN_SIGMA_FRACTION,
        NOISE_SIGMA_FRACTION,
        ",".join(str(b) for b in ADC_BITS),
    ],
})

parameters.to_csv(WAVEFORM_DIR / "waveform_generation_parameters.csv", index=False)


# =============================================================================
# Summary statistics
# =============================================================================

summary_rows = []

for n_bits in ADC_BITS:
    wf = adc_waveforms[n_bits]
    adc_max = (2 ** n_bits) - 1
    baseline_counts = BASELINE_FRACTION * adc_max

    peak_counts = wf.max(axis=1)
    amplitude_counts = peak_counts - baseline_counts

    summary_rows.append({
        "adc_bits": n_bits,
        "adc_max": adc_max,
        "mean_peak_counts": float(np.mean(peak_counts)),
        "std_peak_counts": float(np.std(peak_counts)),
        "mean_amplitude_counts": float(np.mean(amplitude_counts)),
        "std_amplitude_counts": float(np.std(amplitude_counts)),
        "min_count": int(wf.min()),
        "max_count": int(wf.max()),
    })

summary_adc = pd.DataFrame(summary_rows)
summary_adc.to_csv(WAVEFORM_DIR / "adc_waveform_summary.csv", index=False)


# =============================================================================
# Publication-ready figures
# =============================================================================

full_indices = np.where(event_class == "full_energy_like")[0]
partial_indices = np.where(event_class == "partial")[0]
zero_indices = np.where(event_class == "zero")[0]

if len(full_indices) == 0:
    raise RuntimeError("No full-energy-like events found in selected waveform dataset.")

example_index = int(full_indices[0])


# -----------------------------------------------------------------------------
# Figure 1: representative analog pulses from event classes
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(6.25, 3.20), constrained_layout=True)

representatives = []

if len(zero_indices) > 0:
    representatives.append(("zero", int(zero_indices[0])))

if len(partial_indices) > 0:
    representatives.append(("partial", int(partial_indices[0])))

representatives.append(("full-energy-like", int(full_indices[0])))

for name, idx in representatives:
    color = CLASS_COLORS.get(name, "#555555")

    ax.plot(
        TIME_NS,
        analog_noisy[idx],
        linewidth=1.25,
        color=color,
        label=f"{name}, $E_{{dep}}={edep_kev[idx]:.2f}$ keV",
        zorder=3,
    )

ax.set_xlabel("Time [ns]")
ax.set_ylabel("Normalized analog amplitude")
ax.set_xlim(0, 1200)
ax.set_ylim(0, 0.9)
polish_axes(ax, grid=True)
ax.legend(loc="upper right")

save_publication_figure(fig, "nai59_representative_analog_waveforms")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 2: same event quantized at 8, 10 and 12 bits
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(6.25, 3.20), constrained_layout=True)

for n_bits in ADC_BITS:
    wf = adc_waveforms[n_bits][example_index]
    adc_max = (2 ** n_bits) - 1
    wf_norm = wf.astype(np.float64) / adc_max

    ax.step(
        TIME_NS,
        wf_norm,
        where="mid",
        linewidth=1.15,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.set_xlabel("Time [ns]")
ax.set_ylabel("Normalized ADC output")
ax.set_xlim(0, 1200)
ax.set_ylim(0, 0.9)
polish_axes(ax, grid=True)
ax.legend(loc="upper right")

text = (
    rf"$E_{{dep}}={edep_kev[example_index]:.2f}$ keV" + "\n"
    rf"$\tau_d={TAU_DECAY_NS:.0f}$ ns, "
    rf"$f_s={SAMPLING_RATE_HZ / 1e6:.0f}$ MS/s"
)

ax.text(
    0.04,
    0.90,
    text,
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=8.5,
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.80, pad=2.0),
)

save_publication_figure(fig, "nai59_adc_example_waveforms")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 3: quantization residual distributions
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.8, 3.25), constrained_layout=True)

residual_bins = np.linspace(-0.0022, 0.0022, 180)

for n_bits in ADC_BITS:
    reconstructed = reconstruct_normalized_from_adc(
        adc_waveforms[n_bits][example_index],
        n_bits,
    )

    residual = reconstructed - analog_noisy[example_index]

    ax.hist(
        residual,
        bins=residual_bins,
        histtype="step",
        linewidth=1.25,
        color=ADC_COLORS[n_bits],
        linestyle=ADC_LINESTYLES[n_bits],
        density=True,
        label=f"{n_bits}-bit",
        zorder=3,
    )

ax.axvline(
    0.0,
    color=REFERENCE_COLOR,
    linestyle="--",
    linewidth=0.85,
    zorder=2,
)

ax.set_xlabel("Quantization residual")
ax.set_ylabel("Probability density")
ax.set_xlim(-0.0022, 0.0022)
polish_axes(ax, grid=True)
ax.legend(loc="upper right")

save_publication_figure(fig, "nai59_adc_quantization_residuals")
plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 4: waveform amplitude population by event class
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.9, 3.35), constrained_layout=True)

amp_bins = np.linspace(0.0, 0.85, 150)

for class_name in ["partial", "full_energy_like"]:
    mask = event_class == class_name
    if not np.any(mask):
        continue

    ax.hist(
        true_amplitude[mask],
        bins=amp_bins,
        histtype="stepfilled",
        linewidth=0.9,
        alpha=0.35,
        color=CLASS_COLORS[class_name],
        edgecolor=CLASS_COLORS[class_name],
        label=display_class_name(class_name),
        zorder=3,
    )

ax.axvline(
    FULL_ENERGY_AMPLITUDE,
    color=REFERENCE_COLOR,
    linestyle="--",
    linewidth=0.95,
    label="nominal full-energy amplitude",
    zorder=4,
)

ax.set_xlabel("Normalized true pulse amplitude")
ax.set_ylabel("Waveform events [count]")
ax.set_xlim(0.0, 0.85)

polish_axes(ax, grid=True)
ax.legend(loc="upper left")

save_publication_figure(fig, "nai59_waveform_generation_summary")
plt.close(fig)

# =============================================================================
# Print final report
# =============================================================================

print("------------------------------------------------------------")
print("NaI(Tl) ADC waveform generation completed")
print("------------------------------------------------------------")
print(f"Input Geant4 file              : {DATA_PATH}")
print(f"Number of generated waveforms  : {N_WAVEFORMS:,}")
print(f"Samples per waveform           : {N_SAMPLES}")
print(f"Sampling interval              : {DT_NS:.2f} ns")
print(f"Waveform window                : {WINDOW_NS:.1f} ns")
print(f"ADC bit depths                 : {ADC_BITS}")
print("------------------------------------------------------------")
print("Saved waveform files:")
for n_bits in ADC_BITS:
    path = WAVEFORM_DIR / f"waveforms_nai59_{n_bits}bit.npy"
    print(f"  {path}")
print(f"  {WAVEFORM_DIR / 'waveforms_nai59_analog_noisy_float32.npy'}")
print(f"  {WAVEFORM_DIR / 'waveform_labels.csv'}")
print(f"  {WAVEFORM_DIR / 'waveform_generation_parameters.csv'}")
print(f"  {WAVEFORM_DIR / 'adc_waveform_summary.csv'}")
print("------------------------------------------------------------")
print("Saved PDF figures to:")
print(f"  {FIG_DIR}")
print("------------------------------------------------------------")