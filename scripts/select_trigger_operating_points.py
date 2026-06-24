from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
WAVEFORM_DIR = PROJECT_DIR / "waveforms"

INPUT_PATH = WAVEFORM_DIR / "adc_trigger_threshold_curves.csv"
OUTPUT_PATH = WAVEFORM_DIR / "adc_trigger_operating_points.csv"

ADC_BITS = [8, 10, 12]

# False-trigger constraints to evaluate
FALSE_TRIGGER_LIMITS = [1.0, 0.1, 0.01]  # percent

df = pd.read_csv(INPUT_PATH)

rows = []

for bits in ADC_BITS:
    false_col = f"false_zero_{bits}bit"
    nonzero_col = f"eff_nonzero_{bits}bit"
    full_col = f"eff_full_{bits}bit"
    partial_col = f"eff_partial_{bits}bit"

    for limit_percent in FALSE_TRIGGER_LIMITS:
        limit_fraction = limit_percent / 100.0

        valid = df[df[false_col] <= limit_fraction]

        if len(valid) == 0:
            rows.append({
                "adc_bits": bits,
                "false_trigger_constraint_percent": limit_percent,
                "threshold_norm": np.nan,
                "false_trigger_rate_percent": np.nan,
                "eff_nonzero_percent": np.nan,
                "eff_full_energy_like_percent": np.nan,
                "eff_partial_percent": np.nan,
            })
            continue

        # Choose the lowest threshold satisfying the false-trigger constraint.
        selected = valid.iloc[0]

        rows.append({
            "adc_bits": bits,
            "false_trigger_constraint_percent": limit_percent,
            "threshold_norm": selected["threshold_norm"],
            "false_trigger_rate_percent": 100.0 * selected[false_col],
            "eff_nonzero_percent": 100.0 * selected[nonzero_col],
            "eff_full_energy_like_percent": 100.0 * selected[full_col],
            "eff_partial_percent": 100.0 * selected[partial_col],
        })

out = pd.DataFrame(rows)
out.to_csv(OUTPUT_PATH, index=False)

print("------------------------------------------------------------")
print("ADC trigger operating points")
print("------------------------------------------------------------")
print(out.to_string(index=False))
print("------------------------------------------------------------")
print(f"Saved: {OUTPUT_PATH}")
print("------------------------------------------------------------")
