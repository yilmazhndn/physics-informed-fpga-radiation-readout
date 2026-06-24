# Physics-Informed FPGA Radiation Readout

This repository contains the simulation, waveform-generation, ADC analysis, and HDL-validation workflow used for a physics-informed synthetic radiation-detector readout study.

The workflow combines:

- Geant4-based NaI(Tl) energy-deposition modelling for a 59.5 keV reference case
- synthetic scintillation waveform generation with electronics response, noise, pile-up, and ADC quantization
- ADC readout metric analysis for 8-, 10-, and 12-bit digitization
- FPGA-facing HDL replay-vector export
- Icarus Verilog validation of trigger and peak-index logic

Large waveform arrays and high-resolution TIFF exports are intentionally excluded from the GitHub repository. Reproducibility instructions and numerical summaries are provided in the accompanying README files.

## Repository structure

- `scripts/`: Python scripts for waveform generation, readout analysis, tables, and HDL vector export
- `src/`, `include/`: Geant4 example source files
- `hdl/`: HDL modules and testbench files
- `hdl_vectors/`: compact replay vectors and labels for HDL validation
- `figures/`: publication figures, excluding large TIFF files
- `waveforms/`: summary waveform outputs, excluding large `.npy` arrays
- `README_reproduce.md`: reproduction workflow
- `README_results.md`: result summary

## Citation

Please cite this repository and the associated paper/DOI when available. A `CITATION.cff` file is included and will be updated after Zenodo DOI generation.
