# Revision validation package

The ZIP in this directory is the complete reproducibility supplement used for
the revised manuscript. It is kept inside the repository so that the GitHub
source archive includes both the original workflow and the additional studies.
It is the same package archived as Zenodo DOI 10.5281/zenodo.23977073.

## Reproduce the additional studies

Extract the ZIP into a separate directory and run commands from that directory.
Do not extract it over the original repository because both contain README.md.
For example, from the repository root:

```bash
python3 -m zipfile -e revision_materials/JINST_Revision_Reproducibility_20261104.zip revision_reproduced
cd revision_reproduced
```

Follow the extracted README.md. The package includes:

- Original, width-restricted and pipelined RTL, HDL tests and Icarus regression.
- Eight routed Artix-7 Vivado 2026.1 report sets at 250 and 125 MHz, constraints,
  report verification code and numerical comparisons.
- Pulse-shape sensitivity code, reference outputs and replay vectors for nine
  parameter combinations at three ADC resolutions.
- Independent noise-validation code, inputs, frozen thresholds, reference
  results and seeds for 600,000 synthetic Gaussian noise-only windows.
- SHA256SUMS.txt for the extracted supplement files.

Large noise waveform arrays are regenerated rather than stored in the ZIP.
Internal FPGA timing closure does not establish board-interface timing or
physical FPGA operation. No measured-detector validation is claimed.

## Package integrity

SHA-256 of JINST_Revision_Reproducibility_20261104.zip:

```text
60f1e752c3dd600eca9880a9e04a46968e6ae17371d15c1595836e1a5c548ec0
```

## License scope of this supplement

The author's original source code in the supplement is licensed under MIT.
The author's original data and documentation in the supplement are licensed
under CC BY 4.0. Third-party materials and notices in tool-generated reports
remain subject to their respective terms. These scopes match the supplement's
Zenodo record and do not replace notices on Geant4-derived files in the
original workflow.

License texts: https://opensource.org/license/mit and
https://creativecommons.org/licenses/by/4.0/legalcode .
