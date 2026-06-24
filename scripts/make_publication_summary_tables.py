from pathlib import Path
import pandas as pd

# =============================================================================
# Publication summary tables for NaI(Tl) Geant4 + ADC readout study
# =============================================================================
#
# This script collects final results from the Geant4 and ADC/readout analysis
# outputs and prepares publication-ready CSV, LaTeX, and text-summary files.
#
# This version does not require pandas.to_latex() or jinja2.
#
# Inputs:
#   figures/nai59_geant4_summary.csv
#   waveforms/adc_noise_sweep_metrics.csv
#   waveforms/adc_noise_sweep_trigger_operating_points.csv
#
# Outputs:
#   figures/publication_geant4_summary_table.csv
#   figures/publication_adc_readout_summary_table.csv
#   figures/publication_geant4_summary_table.tex
#   figures/publication_adc_readout_summary_table.tex
#   figures/publication_results_text_summary.txt
#
# =============================================================================


# =============================================================================
# Paths
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

FIG_DIR = PROJECT_DIR / "figures"
WAVEFORM_DIR = PROJECT_DIR / "waveforms"

GEANT4_SUMMARY_PATH = FIG_DIR / "nai59_geant4_summary.csv"
ADC_METRICS_PATH = WAVEFORM_DIR / "adc_noise_sweep_metrics.csv"
ADC_OPERATING_PATH = WAVEFORM_DIR / "adc_noise_sweep_trigger_operating_points.csv"

FIG_DIR.mkdir(exist_ok=True)


# =============================================================================
# Helper functions
# =============================================================================

def fmt_float(value, digits=3):
    """Format a floating-point value with fixed precision."""
    return f"{float(value):.{digits}f}"


def fmt_percent(value, digits=3):
    """Format a percentage value with fixed precision."""
    return f"{float(value):.{digits}f}"


def clean_quantity_name(name):
    """Convert internal result labels into manuscript-friendly labels."""
    mapping = {
        "Number of events": "Number of primary events",
        "Mean deposited energy [keV]": "Mean deposited energy",
        "Standard deviation [keV]": "Standard deviation",
        "Zero-deposition events": "Zero-deposition events",
        "Zero-deposition fraction [%]": "Zero-deposition fraction",
        "Partial-deposition events": "Partial-deposition events",
        "Partial-deposition fraction [%]": "Partial-deposition fraction",
        "Full-energy-like events": "Full-energy-like events",
        "Full-energy-like fraction [%]": "Full-energy-like fraction",
    }
    return mapping.get(name, name)


def latex_escape(text):
    """
    Minimal LaTeX escaping for table entries.

    This is intentionally simple because the table entries are controlled
    strings and numerical values.
    """
    text = str(text)

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def dataframe_to_latex_table(df, caption, label, column_format):
    """
    Create a simple LaTeX table without requiring jinja2.

    Parameters
    ----------
    df : pandas.DataFrame
        Table content.
    caption : str
        LaTeX table caption.
    label : str
        LaTeX table label.
    column_format : str
        Tabular column format, e.g. "lll" or "llllllll".
    """

    lines = []

    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{" + caption + r"}")
    lines.append(r"\label{" + label + r"}")
    lines.append(r"\begin{tabular}{" + column_format + r"}")
    lines.append(r"\hline")

    header = " & ".join(latex_escape(col) for col in df.columns) + r" \\"
    lines.append(header)
    lines.append(r"\hline")

    for _, row in df.iterrows():
        line = " & ".join(latex_escape(row[col]) for col in df.columns) + r" \\"
        lines.append(line)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def require_file(path):
    """Stop with a clear message if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")


# =============================================================================
# Check inputs
# =============================================================================

require_file(GEANT4_SUMMARY_PATH)
require_file(ADC_METRICS_PATH)
require_file(ADC_OPERATING_PATH)


# =============================================================================
# Table 1: Geant4 simulation summary
# =============================================================================

geant4 = pd.read_csv(GEANT4_SUMMARY_PATH)

geant4_rows = []

for _, row in geant4.iterrows():
    quantity = row["quantity"]
    value = row["value"]

    quantity_lower = quantity.lower()

    # IMPORTANT:
    # Check "events" before "energy", because "Full-energy-like events"
    # contains the word "energy" but is still an event count.
    if "fraction" in quantity_lower:
        formatted_value = fmt_percent(value, 4)
        unit = "%"
    elif "events" in quantity_lower:
        formatted_value = f"{int(round(value)):,}"
        unit = "events"
    elif "energy" in quantity_lower or "deviation" in quantity_lower:
        formatted_value = fmt_float(value, 4)
        unit = "keV"
    else:
        formatted_value = str(value)
        unit = ""

    geant4_rows.append({
        "Quantity": clean_quantity_name(quantity),
        "Value": formatted_value,
        "Unit": unit
    })

geant4_table = pd.DataFrame(geant4_rows)

geant4_csv_out = FIG_DIR / "publication_geant4_summary_table.csv"
geant4_tex_out = FIG_DIR / "publication_geant4_summary_table.tex"

geant4_table.to_csv(geant4_csv_out, index=False)

geant4_latex = dataframe_to_latex_table(
    geant4_table,
    caption=(
        "Summary of the Geant4 NaI(Tl) energy-deposition simulation for "
        "monoenergetic 59.5 keV gamma rays."
    ),
    label="tab:geant4_summary",
    column_format="lll"
)

geant4_tex_out.write_text(geant4_latex)


# =============================================================================
# Table 2: ADC/readout performance summary
# =============================================================================

metrics = pd.read_csv(ADC_METRICS_PATH)
operating = pd.read_csv(ADC_OPERATING_PATH)

# Use non-zero events for energy reconstruction summary.
metrics_nonzero = metrics[metrics["event_subset"] == "nonzero"].copy()

# Use the operating point selected under a false-trigger constraint of <= 0.1%.
target_false_constraint = 0.1

operating_target = operating[
    operating["false_trigger_constraint_percent"] == target_false_constraint
].copy()

merged = metrics_nonzero.merge(
    operating_target,
    on=["noise_sigma_fraction", "adc_bits"],
    how="left"
)

adc_rows = []

for _, row in merged.sort_values(["noise_sigma_fraction", "adc_bits"]).iterrows():
    adc_rows.append({
        "Noise sigma": fmt_float(row["noise_sigma_fraction"], 3),
        "ADC bits": int(row["adc_bits"]),
        "MAE [keV]": fmt_float(row["mae_keV"], 3),
        "RMSE [keV]": fmt_float(row["rmse_keV"], 3),
        "Bias [keV]": fmt_float(row["bias_keV"], 3),
        "Threshold": fmt_float(row["threshold_norm"], 3),
        "False trigger [%]": fmt_float(row["false_trigger_rate_percent"], 3),
        "Trigger efficiency [%]": fmt_float(row["eff_nonzero_percent"], 3),
    })

adc_table = pd.DataFrame(adc_rows)

adc_csv_out = FIG_DIR / "publication_adc_readout_summary_table.csv"
adc_tex_out = FIG_DIR / "publication_adc_readout_summary_table.tex"

adc_table.to_csv(adc_csv_out, index=False)

adc_latex = dataframe_to_latex_table(
    adc_table,
    caption=(
        "ADC/readout performance summary for synthetic NaI(Tl) waveforms. "
        "The trigger operating threshold is selected under a false-trigger "
        "constraint of 0.1\\% using zero-deposition events."
    ),
    label="tab:adc_readout_summary",
    column_format="llllllll"
)

adc_tex_out.write_text(adc_latex)


# =============================================================================
# Compact text summary for manuscript drafting
# =============================================================================

text_summary_path = FIG_DIR / "publication_results_text_summary.txt"

g_dict = dict(zip(geant4["quantity"], geant4["value"]))

full_fraction = g_dict.get("Full-energy-like fraction [%]")
partial_fraction = g_dict.get("Partial-deposition fraction [%]")
zero_fraction = g_dict.get("Zero-deposition fraction [%]")
mean_edep = g_dict.get("Mean deposited energy [keV]")
std_edep = g_dict.get("Standard deviation [keV]")

rmse_low_8 = merged[
    (merged["noise_sigma_fraction"] == 0.001) &
    (merged["adc_bits"] == 8)
]["rmse_keV"].iloc[0]

rmse_low_12 = merged[
    (merged["noise_sigma_fraction"] == 0.001) &
    (merged["adc_bits"] == 12)
]["rmse_keV"].iloc[0]

rmse_nom_8 = merged[
    (merged["noise_sigma_fraction"] == 0.003) &
    (merged["adc_bits"] == 8)
]["rmse_keV"].iloc[0]

rmse_nom_12 = merged[
    (merged["noise_sigma_fraction"] == 0.003) &
    (merged["adc_bits"] == 12)
]["rmse_keV"].iloc[0]

rmse_high_8 = merged[
    (merged["noise_sigma_fraction"] == 0.006) &
    (merged["adc_bits"] == 8)
]["rmse_keV"].iloc[0]

rmse_high_12 = merged[
    (merged["noise_sigma_fraction"] == 0.006) &
    (merged["adc_bits"] == 12)
]["rmse_keV"].iloc[0]

summary_text = f"""
Geant4 summary:
The Geant4 simulation of 10^6 monoenergetic 59.5 keV gamma events in the NaI(Tl) detector produced a mean deposited energy of {mean_edep:.4f} keV with a standard deviation of {std_edep:.4f} keV. Events were classified as full-energy-like, partial-deposition and zero-deposition with fractions of {full_fraction:.4f}%, {partial_fraction:.4f}% and {zero_fraction:.4f}%, respectively.

ADC/readout summary:
For non-zero energy-deposition events, the reconstructed-energy RMSE increased with analog noise level. At noise sigma = 0.001, the RMSE changed from {rmse_low_8:.3f} keV at 8-bit to {rmse_low_12:.3f} keV at 12-bit. At the nominal noise level sigma = 0.003, the RMSE changed from {rmse_nom_8:.3f} keV at 8-bit to {rmse_nom_12:.3f} keV at 12-bit. At the high-noise condition sigma = 0.006, the RMSE changed from {rmse_high_8:.3f} keV at 8-bit to {rmse_high_12:.3f} keV at 12-bit. These results indicate that, for the selected waveform model and operating conditions, the readout error is dominated primarily by analog noise and gain variation, while increasing ADC resolution from 8 to 12 bits provides a modest improvement.
""".strip()

text_summary_path.write_text(summary_text)


# =============================================================================
# Print report
# =============================================================================

print("------------------------------------------------------------")
print("Publication summary tables generated")
print("------------------------------------------------------------")
print("Saved:")
print(f"  {geant4_csv_out}")
print(f"  {geant4_tex_out}")
print(f"  {adc_csv_out}")
print(f"  {adc_tex_out}")
print(f"  {text_summary_path}")
print("------------------------------------------------------------")
print("Geant4 publication table:")
print(geant4_table.to_string(index=False))
print("------------------------------------------------------------")
print("ADC/readout publication table:")
print(adc_table.to_string(index=False))
print("------------------------------------------------------------")
