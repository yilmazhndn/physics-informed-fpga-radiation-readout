from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# -------------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "build" / "nai59_edep_events.csv"

FIG_DIR = PROJECT_DIR / "hy"
FIG_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------------
# Publication-style matplotlib settings
# -------------------------------------------------------------------------

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
    "legend.handlelength": 2.3,

    "savefig.dpi": 1200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.025,

    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# -------------------------------------------------------------------------
# Colors
# -------------------------------------------------------------------------

COLOR_ZERO = "#6E6E6E"
COLOR_PARTIAL = "#3A8F6A"
COLOR_FULL = "#2F5D8C"
COLOR_BOUNDARY = "#9A3B3B"
GRID_COLOR = "#E6E6E6"

# -------------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------------

df = pd.read_csv(DATA_PATH)
edep = df["edep_nai_keV"].to_numpy(dtype=float)

n_events = len(edep)

zero_mask = edep == 0.0
partial_mask = (edep > 0.0) & (edep <= 58.0)
full_mask = (edep > 58.0) & (edep <= 59.5)

zero_events = int(zero_mask.sum())
partial_events = int(partial_mask.sum())
full_events = int(full_mask.sum())

zero_fraction = zero_events / n_events
partial_fraction = partial_events / n_events
full_fraction = full_events / n_events

mean_edep = float(np.mean(edep))
std_edep = float(np.std(edep, ddof=1))

print("------------------------------------------------------------")
print("Geant4 NaI(Tl) 59.5 keV energy-deposition summary")
print("------------------------------------------------------------")
print(f"Number of events                  : {n_events:,}")
print(f"Mean deposited energy [keV]        : {mean_edep:.4f}")
print(f"Standard deviation [keV]           : {std_edep:.4f}")
print(f"Zero-deposition events             : {zero_events:,} ({100*zero_fraction:.4f} %)")
print(f"Partial-deposition events          : {partial_events:,} ({100*partial_fraction:.4f} %)")
print(f"Full-energy-like events            : {full_events:,} ({100*full_fraction:.4f} %)")
print("------------------------------------------------------------")

# -------------------------------------------------------------------------
# Figure: classified deposited-energy distribution
# -------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(6.8, 3.8), constrained_layout=True)

bins = np.linspace(0.0, 65.0, 326)

ax.hist(
    edep[zero_mask],
    bins=bins,
    histtype="stepfilled",
    color=COLOR_ZERO,
    alpha=0.55,
    edgecolor=COLOR_ZERO,
    linewidth=0.8,
    label=rf"zero deposition",
    zorder=3,
)

ax.hist(
    edep[partial_mask],
    bins=bins,
    histtype="stepfilled",
    color=COLOR_PARTIAL,
    alpha=0.42,
    edgecolor=COLOR_PARTIAL,
    linewidth=0.8,
    label=rf"partial deposition",
    zorder=2,
)

ax.hist(
    edep[full_mask],
    bins=bins,
    histtype="stepfilled",
    color=COLOR_FULL,
    alpha=0.42,
    edgecolor=COLOR_FULL,
    linewidth=0.8,
    label=rf"full energy like",
    zorder=1,
)

# Class boundary and incident gamma-energy reference
ax.axvline(
    58.0,
    color=COLOR_BOUNDARY,
    linewidth=0.85,
    linestyle="--",
    zorder=4,
)

ax.axvline(
    59.5,
    color="#222222",
    linewidth=0.85,
    linestyle=":",
    zorder=4,
)

ax.text(
    57.55,
    1.8,
    "class boundary",
    rotation=90,
    ha="right",
    va="bottom",
    fontsize=7.5,
    color=COLOR_BOUNDARY,
)

ax.text(
    59.15,
    1.8,
    r"$E_{\gamma}=59.5$ keV",
    rotation=90,
    ha="right",
    va="bottom",
    fontsize=7.5,
    color="#222222",
)

info_text = (
    rf"$N=10^6$ events" + "\n"
    rf"$\overline{{E}}_{{dep}}={mean_edep:.4f}$ keV" + "\n"
    rf"$\sigma_{{E}}={std_edep:.4f}$ keV"
)

ax.text(
    0.035,
    0.95,
    info_text,
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=8.2,
    bbox=dict(
        facecolor="white",
        edgecolor="#BBBBBB",
        linewidth=0.5,
        alpha=0.92,
        pad=3.0,
    ),
)

ax.set_xlabel(r"Deposited energy in NaI(Tl) [keV]")
ax.set_ylabel("Counts")
ax.set_xlim(0.0, 60.0)
ax.set_yscale("log")
ax.set_ylim(0.8, 2.5e6)

ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
ax.yaxis.set_minor_locator(mticker.LogLocator(base=10.0, subs="auto", numticks=10))
ax.yaxis.set_minor_formatter(mticker.NullFormatter())

ax.grid(
    True,
    which="major",
    color=GRID_COLOR,
    linewidth=0.45,
    alpha=0.65,
    zorder=0,
)

ax.tick_params(which="both", top=True, right=True)

for spine in ax.spines.values():
    spine.set_linewidth(0.75)

ax.legend(loc="upper right")

output_path = FIG_DIR / "nai59_geant4_edep_classified.pdf"
fig.savefig(output_path)
plt.close(fig)

print("Saved figure:")
print(f"  {output_path}")