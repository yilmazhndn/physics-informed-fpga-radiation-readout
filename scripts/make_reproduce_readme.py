from pathlib import Path

# =============================================================================
# Create README_reproduce.md
# =============================================================================
#
# This script creates a reproducibility guide for the NaI(Tl) Geant4,
# synthetic waveform, ADC digitization and HDL validation workflow.
#
# Output:
#   README_reproduce.md
#
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
README_PATH = PROJECT_DIR / "README_reproduce.md"


def main():
    readme = r"""# Reproducibility Guide

This document describes how to reproduce the full NaI(Tl) Geant4, synthetic waveform, ADC digitization and HDL validation workflow.

The workflow is designed to provide a reproducible chain from Monte Carlo detector simulation to FPGA-facing replay-vector validation.

```text
Geant4 energy deposition
→ synthetic waveform generation
→ ADC digitization
→ readout metric analysis
→ noise/SNR sweep
→ HDL replay-vector export
→ Verilog testbench validation
