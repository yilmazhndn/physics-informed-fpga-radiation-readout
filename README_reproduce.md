# Reproducibility Guide

This document summarizes how to reproduce the NaI(Tl) Geant4, synthetic waveform, ADC digitization and HDL validation workflow.

## Workflow

Geant4 energy deposition -> synthetic waveform generation -> ADC digitization -> readout metric analysis -> noise/SNR sweep -> HDL replay-vector export -> Verilog testbench validation.

## Reproduction order

```bash
cd ~/Desktop/B4a

mkdir -p build
cd build
cmake ..
make -j4
./exampleB4a -m ../nai59.mac
cd ..

python scripts/plot_nai59_publication.py
python scripts/generate_nai59_adc_waveforms.py
python scripts/analyze_adc_readout_metrics.py
python scripts/select_trigger_operating_points.py
python scripts/run_adc_noise_sweep.py
python scripts/make_publication_summary_tables.py

python scripts/export_hdl_replay_vectors.py
python scripts/create_hdl_validation_files.py
bash hdl/run_hdl_validation.sh
python scripts/make_hdl_validation_summary.py

python scripts/make_results_readme.py

Main outputs
build/nai59_edep_events.csv
figures/nai59_edep_two_panel.pdf
figures/nai59_representative_analog_waveforms.pdf
figures/nai59_adc_quantization_residuals.pdf
figures/nai59_noise_sweep_rmse_vs_bits.pdf
figures/nai59_noise_sweep_threshold_for_false_trigger.pdf
figures/publication_geant4_summary_table.tex
figures/publication_adc_readout_summary_table.tex
hdl_vectors/nai59_hdl_manifest.csv
hdl/hdl_validation_summary.csv
README_results.md

Key results

Geant4 simulation:

Number of events: 1,000,000
Mean deposited energy: 56.1330 keV
Zero-deposition fraction: 0.1089%
Partial-deposition fraction: 11.1047%
Full-energy-like fraction: 88.7864%

ADC/readout:

At noise sigma = 0.001, RMSE changed from 0.863 keV at 8-bit to 0.858 keV at 12-bit.
At noise sigma = 0.003, RMSE changed from 0.897 keV at 8-bit to 0.892 keV at 12-bit.
At noise sigma = 0.006, RMSE changed from 1.031 keV at 8-bit to 1.027 keV at 12-bit.

HDL validation:

8-bit: 1024 events checked, 0 errors, PASS
10-bit: 1024 events checked, 0 errors, PASS
12-bit: 1024 events checked, 0 errors, PASS
Total replayed events: 3072
Total mismatches: 0

Note

This workflow validates a synthetic FPGA-facing readout pipeline using HDL simulation. It does not claim physical FPGA board deployment or post-place-and-route FPGA resource utilization.





