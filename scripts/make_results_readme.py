from pathlib import Path
import pandas as pd

# =============================================================================
# Create final results inventory README for the NaI(Tl) Geant4 + waveform + HDL study
# =============================================================================
#
# Output:
#   README_results.md
#
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

README_PATH = PROJECT_DIR / "README_results.md"

FIG_DIR = PROJECT_DIR / "figures"
WAVEFORM_DIR = PROJECT_DIR / "waveforms"
HDL_VECTOR_DIR = PROJECT_DIR / "hdl_vectors"
HDL_DIR = PROJECT_DIR / "hdl"


def read_text_if_exists(path):
    if path.exists():
        return path.read_text().strip()
    return "File not found."


def file_status(path):
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        return f"`{path.relative_to(PROJECT_DIR)}` — exists, {size_mb:.2f} MB"
    return f"`{path.relative_to(PROJECT_DIR)}` — missing"


def main():
    geant4_summary = read_text_if_exists(FIG_DIR / "publication_results_text_summary.txt")
    hdl_summary = read_text_if_exists(HDL_DIR / "hdl_validation_summary.txt")

    readme = f"""# Final Results Inventory

This document summarizes the final computational outputs for the NaI(Tl) Geant4, synthetic waveform, ADC digitization and HDL replay-validation study.

## Project status

The main technical workflow has been completed.

- Geant4 energy-deposition simulation completed.
- Event-by-event deposited-energy dataset generated.
- Synthetic NaI(Tl)-like waveforms generated.
- 8-bit, 10-bit and 12-bit ADC digitized waveform datasets generated.
- ADC/readout metrics and noise sweep completed.
- HDL-compatible replay vectors exported.
- Verilog HDL validation completed using Icarus Verilog testbenches.
- Publication-ready figures and tables generated.

## Simulation and dataset summary

{geant4_summary}

## HDL validation summary

{hdl_summary}

## Main Geant4 outputs

- {file_status(WAVEFORM_DIR / "waveform_labels.csv")}
- {file_status(FIG_DIR / "nai59_geant4_summary.csv")}
- {file_status(FIG_DIR / "publication_geant4_summary_table.csv")}
- {file_status(FIG_DIR / "publication_geant4_summary_table.tex")}

## Main waveform datasets

- {file_status(WAVEFORM_DIR / "waveforms_nai59_8bit.npy")}
- {file_status(WAVEFORM_DIR / "waveforms_nai59_10bit.npy")}
- {file_status(WAVEFORM_DIR / "waveforms_nai59_12bit.npy")}
- {file_status(WAVEFORM_DIR / "waveforms_nai59_analog_noisy_float32.npy")}
- {file_status(WAVEFORM_DIR / "waveform_generation_parameters.csv")}

## ADC/readout metric outputs

- {file_status(WAVEFORM_DIR / "adc_readout_metrics_summary.csv")}
- {file_status(WAVEFORM_DIR / "adc_trigger_threshold_curves.csv")}
- {file_status(WAVEFORM_DIR / "adc_trigger_operating_points.csv")}
- {file_status(WAVEFORM_DIR / "adc_noise_sweep_metrics.csv")}
- {file_status(WAVEFORM_DIR / "adc_noise_sweep_trigger_operating_points.csv")}
- {file_status(WAVEFORM_DIR / "adc_noise_sweep_threshold_curves.csv")}
- {file_status(FIG_DIR / "publication_adc_readout_summary_table.csv")}
- {file_status(FIG_DIR / "publication_adc_readout_summary_table.tex")}

## HDL replay-vector outputs

- {file_status(HDL_VECTOR_DIR / "nai59_8bit_flat.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_10bit_flat.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_12bit_flat.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_8bit_expected_trigger.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_10bit_expected_trigger.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_12bit_expected_trigger.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_8bit_expected_peak_count.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_10bit_expected_peak_count.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_12bit_expected_peak_count.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_8bit_expected_peak_index.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_10bit_expected_peak_index.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_12bit_expected_peak_index.mem")}
- {file_status(HDL_VECTOR_DIR / "nai59_hdl_labels.csv")}
- {file_status(HDL_VECTOR_DIR / "nai59_hdl_manifest.csv")}

## HDL validation files

- {file_status(HDL_DIR / "nai59_peak_trigger.v")}
- {file_status(HDL_DIR / "tb_nai59_8bit.v")}
- {file_status(HDL_DIR / "tb_nai59_10bit.v")}
- {file_status(HDL_DIR / "tb_nai59_12bit.v")}
- {file_status(HDL_DIR / "run_hdl_validation.sh")}
- {file_status(HDL_DIR / "hdl_validation_summary.csv")}
- {file_status(HDL_DIR / "hdl_validation_summary.txt")}
- {file_status(HDL_DIR / "hdl_validation_raw_output.txt")}

## Recommended main manuscript figures

1. `figures/nai59_edep_two_panel.pdf`  
   Geant4 NaI(Tl) energy-deposition spectrum for 59.5 keV gamma rays.

2. `figures/nai59_representative_analog_waveforms.pdf`  
   Representative synthetic analog waveforms for zero, partial and full-energy-like events.

3. `figures/nai59_adc_quantization_residuals.pdf`  
   ADC quantization residuals for 8-bit, 10-bit and 12-bit digitization.

4. `figures/nai59_normalized_adc_waveform_comparison.pdf`  
   Normalized ADC waveform comparison across bit depths.

5. `figures/nai59_noise_sweep_rmse_vs_bits.pdf`  
   Energy reconstruction RMSE versus ADC bit depth under different analog noise levels.

6. `figures/nai59_noise_sweep_threshold_for_false_trigger.pdf`  
   Trigger threshold required to satisfy false-trigger constraints under different noise levels.

## Recommended main manuscript tables

1. `figures/publication_geant4_summary_table.tex`  
   Geant4 simulation and event-classification summary.

2. `figures/publication_adc_readout_summary_table.tex`  
   ADC/readout performance summary under noise sweep.

3. `hdl/hdl_validation_summary.csv`  
   HDL replay-validation summary for 8-bit, 10-bit and 12-bit datasets.

## Technical conclusion

The completed workflow provides a reproducible chain from Monte Carlo detector physics to FPGA-facing waveform validation:

Geant4 energy deposition → synthetic waveform generation → ADC digitization → readout metric analysis → HDL replay-vector export → Verilog testbench validation.

The HDL validation replayed 1024 events per ADC configuration and produced zero mismatches for trigger decision, peak count and peak index across 8-bit, 10-bit and 12-bit digitization.
"""

    README_PATH.write_text(readme)

    print("------------------------------------------------------------")
    print("Final results README generated")
    print("------------------------------------------------------------")
    print(f"Saved: {README_PATH}")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
