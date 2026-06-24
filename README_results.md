# Final Results Inventory

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

Geant4 summary:
The Geant4 simulation of 10^6 monoenergetic 59.5 keV gamma events in the NaI(Tl) detector produced a mean deposited energy of 56.1330 keV with a standard deviation of 9.6234 keV. Events were classified as full-energy-like, partial-deposition and zero-deposition with fractions of 88.7864%, 11.1047% and 0.1089%, respectively.

ADC/readout summary:
For non-zero energy-deposition events, the reconstructed-energy RMSE increased with analog noise level. At noise sigma = 0.001, the RMSE changed from 0.863 keV at 8-bit to 0.858 keV at 12-bit. At the nominal noise level sigma = 0.003, the RMSE changed from 0.897 keV at 8-bit to 0.892 keV at 12-bit. At the high-noise condition sigma = 0.006, the RMSE changed from 1.031 keV at 8-bit to 1.027 keV at 12-bit. These results indicate that, for the selected waveform model and operating conditions, the readout error is dominated primarily by analog noise and gain variation, while increasing ADC resolution from 8 to 12 bits provides a modest improvement.

## HDL validation summary

HDL validation summary:
The HDL validation was performed using Icarus Verilog replay testbenches for 8-bit, 10-bit and 12-bit ADC waveform datasets. Each testbench replayed 1024 synthetic NaI(Tl) waveform events, with 500 samples per event. The Verilog module implemented pre-trigger baseline estimation, threshold triggering, peak-count extraction and peak-index extraction.

Validation result:
ADC configurations tested : 3
Configurations passed     : 3
Total replayed events     : 3072
Total mismatches          : 0

Per-configuration result:
- 8-bit: 1024 events checked, 0 errors, PASS
- 10-bit: 1024 events checked, 0 errors, PASS
- 12-bit: 1024 events checked, 0 errors, PASS

All HDL outputs matched the software reference labels for trigger decision, peak count and peak index.

## Main Geant4 outputs

- `waveforms/waveform_labels.csv` — exists, 11.17 MB
- `figures/nai59_geant4_summary.csv` — exists, 0.00 MB
- `figures/publication_geant4_summary_table.csv` — exists, 0.00 MB
- `figures/publication_geant4_summary_table.tex` — exists, 0.00 MB

## Main waveform datasets

- `waveforms/waveforms_nai59_8bit.npy` — exists, 47.68 MB
- `waveforms/waveforms_nai59_10bit.npy` — exists, 95.37 MB
- `waveforms/waveforms_nai59_12bit.npy` — exists, 95.37 MB
- `waveforms/waveforms_nai59_analog_noisy_float32.npy` — exists, 190.73 MB
- `waveforms/waveform_generation_parameters.csv` — exists, 0.00 MB

## ADC/readout metric outputs

- `waveforms/adc_readout_metrics_summary.csv` — exists, 0.00 MB
- `waveforms/adc_trigger_threshold_curves.csv` — exists, 0.02 MB
- `waveforms/adc_trigger_operating_points.csv` — exists, 0.00 MB
- `waveforms/adc_noise_sweep_metrics.csv` — exists, 0.00 MB
- `waveforms/adc_noise_sweep_trigger_operating_points.csv` — exists, 0.00 MB
- `waveforms/adc_noise_sweep_threshold_curves.csv` — exists, 0.05 MB
- `figures/publication_adc_readout_summary_table.csv` — exists, 0.00 MB
- `figures/publication_adc_readout_summary_table.tex` — exists, 0.00 MB

## HDL replay-vector outputs

- `hdl_vectors/nai59_8bit_flat.mem` — exists, 1.46 MB
- `hdl_vectors/nai59_10bit_flat.mem` — exists, 1.95 MB
- `hdl_vectors/nai59_12bit_flat.mem` — exists, 1.95 MB
- `hdl_vectors/nai59_8bit_expected_trigger.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_10bit_expected_trigger.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_12bit_expected_trigger.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_8bit_expected_peak_count.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_10bit_expected_peak_count.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_12bit_expected_peak_count.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_8bit_expected_peak_index.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_10bit_expected_peak_index.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_12bit_expected_peak_index.mem` — exists, 0.00 MB
- `hdl_vectors/nai59_hdl_labels.csv` — exists, 0.22 MB
- `hdl_vectors/nai59_hdl_manifest.csv` — exists, 0.00 MB

## HDL validation files

- `hdl/nai59_peak_trigger.v` — exists, 0.00 MB
- `hdl/tb_nai59_8bit.v` — exists, 0.00 MB
- `hdl/tb_nai59_10bit.v` — exists, 0.00 MB
- `hdl/tb_nai59_12bit.v` — exists, 0.00 MB
- `hdl/run_hdl_validation.sh` — exists, 0.00 MB
- `hdl/hdl_validation_summary.csv` — exists, 0.00 MB
- `hdl/hdl_validation_summary.txt` — exists, 0.00 MB
- `hdl/hdl_validation_raw_output.txt` — exists, 0.00 MB

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
