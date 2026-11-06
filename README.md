# Physics-Informed FPGA Radiation Readout

This repository contains the original simulation, waveform-generation, ADC
analysis and HDL-validation workflow together with the additional validation
studies supporting the revised manuscript, "Physics-Informed Synthetic Waveform
Generation and HDL Replay Validation for Radiation Detector Readout Development."

## Complete release

Version 0.3.0 combines the original workflow and the revision reproducibility
package in one repository. The revision ZIP is committed under
`revision_materials/`, so it is included in GitHub's source-code archive.
The original scripts, vectors and results remain in their existing locations.

## Original workflow

- Geant4-based NaI(Tl) energy deposition for the 59.5 keV reference case.
- Synthetic waveform generation with detector and electronics response, noise,
  optional pulse overlap and ADC quantization.
- Readout analysis for 8-, 10- and 12-bit digitization.
- HDL replay vectors and Icarus Verilog validation of trigger and peak outputs.

See [README_reproduce.md](README_reproduce.md) and
[README_results.md](README_results.md) for the original workflow and results.
Their statements about absent routed implementation results describe that
original workflow; the additional implementation results are in the revision
package described below.

## Additional validation studies

[revision_materials/README.md](revision_materials/README.md) provides the package
contents, extraction instructions, integrity hash and license scope.

- FPGA implementation comparison and functional regression for the original,
  width-restricted and two pipelined RTL variants at 250 and 125 MHz.
- Paired pulse-shape sensitivity for nine rise/decay combinations at three ADC
  resolutions, including software and HDL replay reference results.
- Independent false-trigger validation with 600,000 synthetic noise-only
  windows, separate calibration and held-out validation sets, confidence bounds
  and signal-efficiency results.

The reported timing closure concerns internally constrained paths. Board I/O
timing, physical FPGA operation and agreement with measured detector waveforms
remain unvalidated. The noise study assumes the specified Gaussian model.

## Repository structure

- `scripts/`: original generation and analysis scripts.
- `src/`, `include/`: Geant4-derived simulation source files.
- `hdl/`, `hdl_vectors/`: original RTL, tests and compact replay vectors.
- `figures/`: publication figures, excluding large TIFF exports.
- `waveforms/`: waveform summaries, excluding large arrays.
- `revision_materials/`: complete additional validation package and instructions.

Large waveform arrays and high-resolution TIFF exports are excluded and can be
regenerated using the corresponding reproduction instructions.

## Archives and citation

Use the DOI of the complete v0.3.0 Zenodo release after it is archived. The
existing original-workflow series is available through
https://doi.org/10.5281/zenodo.20829060 . That series link resolves to its latest
published version; until v0.3.0 is archived, it still resolves to an earlier
release and should not be described as the complete revised package.

For provenance, the original v0.2.0 archive has DOI
10.5281/zenodo.21299917 and the separately archived revision supplement has DOI
10.5281/zenodo.23977073. These historical records are preserved.

A CITATION.cff file supplies author and version metadata. Update its DOI field
once the complete v0.3.0 archive has been assigned its version-specific DOI.

## Licensing

See [LICENSE](LICENSE) for the original workflow's licensing note, and
[revision_materials/README.md](revision_materials/README.md) for the supplement's
MIT / CC BY 4.0 scopes. Geant4-derived source files retain their notices and
applicable Geant4 terms.
