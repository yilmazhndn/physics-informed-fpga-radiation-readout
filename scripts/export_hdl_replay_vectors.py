from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
# Export FPGA/HDL replay vectors from NaI(Tl) ADC waveform dataset
# =============================================================================
#
# Inputs:
#   waveforms/waveforms_nai59_8bit.npy
#   waveforms/waveforms_nai59_10bit.npy
#   waveforms/waveforms_nai59_12bit.npy
#   waveforms/waveform_labels.csv
#   waveforms/adc_noise_sweep_trigger_operating_points.csv
#
# Outputs:
#   hdl_vectors/nai59_8bit_flat.mem
#   hdl_vectors/nai59_10bit_flat.mem
#   hdl_vectors/nai59_12bit_flat.mem
#   hdl_vectors/nai59_8bit_expected_trigger.mem
#   hdl_vectors/nai59_10bit_expected_trigger.mem
#   hdl_vectors/nai59_12bit_expected_trigger.mem
#   hdl_vectors/nai59_8bit_expected_peak_count.mem
#   hdl_vectors/nai59_10bit_expected_peak_count.mem
#   hdl_vectors/nai59_12bit_expected_peak_count.mem
#   hdl_vectors/nai59_8bit_expected_peak_index.mem
#   hdl_vectors/nai59_10bit_expected_peak_index.mem
#   hdl_vectors/nai59_12bit_expected_peak_index.mem
#   hdl_vectors/nai59_hdl_labels.csv
#   hdl_vectors/nai59_hdl_manifest.csv
#
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

WAVEFORM_DIR = PROJECT_DIR / "waveforms"
HDL_VECTOR_DIR = PROJECT_DIR / "hdl_vectors"
HDL_VECTOR_DIR.mkdir(exist_ok=True)

LABEL_PATH = WAVEFORM_DIR / "waveform_labels.csv"
OPERATING_PATH = WAVEFORM_DIR / "adc_noise_sweep_trigger_operating_points.csv"

ADC_BITS = [8, 10, 12]

# Keep HDL simulation practical.
N_EXPORT_EVENTS = 1024

N_SAMPLES = 500
PRETRIGGER_SAMPLES = 40

# Use nominal-noise operating point from the sweep.
NOMINAL_NOISE_SIGMA = 0.003
FALSE_TRIGGER_CONSTRAINT_PERCENT = 0.1

REFERENCE_ENERGY_KEV = 59.5
FULL_ENERGY_AMPLITUDE = 0.70


def require_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def read_thresholds():
    """
    Read selected trigger thresholds from the operating-point table.
    Thresholds are stored as normalized full-scale amplitude values.
    """
    if not OPERATING_PATH.exists():
        print("WARNING: Operating-point table not found.")
        print("Using fallback threshold_norm = 0.015 for all bit depths.")
        return {bits: 0.015 for bits in ADC_BITS}

    df = pd.read_csv(OPERATING_PATH)

    thresholds = {}

    for bits in ADC_BITS:
        sub = df[
            (df["noise_sigma_fraction"] == NOMINAL_NOISE_SIGMA) &
            (df["adc_bits"] == bits) &
            (df["false_trigger_constraint_percent"] == FALSE_TRIGGER_CONSTRAINT_PERCENT)
        ]

        if len(sub) == 0:
            print(f"WARNING: Missing threshold for {bits}-bit. Using fallback 0.015.")
            thresholds[bits] = 0.015
        else:
            thresholds[bits] = float(sub["threshold_norm"].iloc[0])

    return thresholds


def write_mem_hex(path, array, width_bits):
    """
    Write a one-dimensional integer array into a hex .mem file.
    """
    hex_width = int(np.ceil(width_bits / 4))

    with open(path, "w") as f:
        for value in array:
            f.write(f"{int(value):0{hex_width}X}\n")


def compute_reference_outputs(waveforms, threshold_counts):
    """
    Compute software reference outputs using the same logic intended for HDL.

    Baseline:
        Integer average of the first PRETRIGGER_SAMPLES samples.

    Peak:
        Maximum ADC count over the full event window.

    Trigger:
        True if any sample after the pre-trigger region exceeds
        baseline + threshold_counts.
    """
    n_events, n_samples = waveforms.shape

    if n_samples != N_SAMPLES:
        raise ValueError(f"Expected {N_SAMPLES} samples/event, got {n_samples}")

    waveforms_u64 = waveforms.astype(np.uint64)

    baseline_sum = waveforms_u64[:, :PRETRIGGER_SAMPLES].sum(axis=1)
    baseline_counts = baseline_sum // PRETRIGGER_SAMPLES

    peak_counts = waveforms_u64.max(axis=1)
    peak_indices = waveforms_u64.argmax(axis=1)

    post = waveforms[:, PRETRIGGER_SAMPLES:].astype(np.int64)
    trigger_level = baseline_counts.astype(np.int64)[:, None] + int(threshold_counts)

    expected_trigger = (post >= trigger_level).any(axis=1).astype(np.uint8)

    amplitude_counts = peak_counts.astype(np.int64) - baseline_counts.astype(np.int64)
    amplitude_counts = np.maximum(amplitude_counts, 0)

    return (
        baseline_counts.astype(np.uint64),
        peak_counts.astype(np.uint64),
        peak_indices.astype(np.uint64),
        expected_trigger.astype(np.uint8),
        amplitude_counts.astype(np.uint64),
    )


def main():
    require_file(LABEL_PATH)

    labels = pd.read_csv(LABEL_PATH)

    if len(labels) < N_EXPORT_EVENTS:
        raise ValueError(
            f"waveform_labels.csv has only {len(labels)} rows; "
            f"need at least {N_EXPORT_EVENTS}."
        )

    selected_labels = labels.iloc[:N_EXPORT_EVENTS].copy().reset_index(drop=True)
    thresholds_norm = read_thresholds()

    manifest_rows = []
    hdl_label_rows = []

    for bits in ADC_BITS:
        waveform_path = WAVEFORM_DIR / f"waveforms_nai59_{bits}bit.npy"
        require_file(waveform_path)

        waveforms = np.load(waveform_path, mmap_mode="r")[:N_EXPORT_EVENTS]

        if waveforms.shape != (N_EXPORT_EVENTS, N_SAMPLES):
            raise ValueError(
                f"Unexpected waveform shape for {bits}-bit: {waveforms.shape}"
            )

        adc_max = (2 ** bits) - 1
        threshold_norm = thresholds_norm[bits]
        threshold_counts = int(round(threshold_norm * adc_max))

        (
            baseline_counts,
            peak_counts,
            peak_indices,
            expected_trigger,
            amplitude_counts,
        ) = compute_reference_outputs(waveforms, threshold_counts)

        amplitude_norm = amplitude_counts.astype(np.float64) / adc_max
        expected_energy_reco_keV = (
            amplitude_norm / FULL_ENERGY_AMPLITUDE * REFERENCE_ENERGY_KEV
        )

        flat_samples = np.asarray(waveforms).reshape(-1)

        flat_path = HDL_VECTOR_DIR / f"nai59_{bits}bit_flat.mem"
        trig_path = HDL_VECTOR_DIR / f"nai59_{bits}bit_expected_trigger.mem"
        peak_count_path = HDL_VECTOR_DIR / f"nai59_{bits}bit_expected_peak_count.mem"
        peak_index_path = HDL_VECTOR_DIR / f"nai59_{bits}bit_expected_peak_index.mem"

        write_mem_hex(flat_path, flat_samples, bits)
        write_mem_hex(trig_path, expected_trigger, 1)
        write_mem_hex(peak_count_path, peak_counts, bits)
        write_mem_hex(peak_index_path, peak_indices, 16)

        for i in range(N_EXPORT_EVENTS):
            hdl_label_rows.append({
                "dataset_index": int(i),
                "adc_bits": int(bits),
                "geant4_event_id": int(selected_labels.loc[i, "geant4_event_id"]),
                "edep_nai_keV": float(selected_labels.loc[i, "edep_nai_keV"]),
                "event_class": selected_labels.loc[i, "event_class"],
                "threshold_norm": float(threshold_norm),
                "threshold_counts": int(threshold_counts),
                "baseline_counts_ref": int(baseline_counts[i]),
                "expected_trigger": int(expected_trigger[i]),
                "expected_peak_count": int(peak_counts[i]),
                "expected_peak_index": int(peak_indices[i]),
                "expected_energy_reco_keV": float(expected_energy_reco_keV[i]),
            })

        manifest_rows.append({
            "adc_bits": int(bits),
            "n_events": int(N_EXPORT_EVENTS),
            "n_samples_per_event": int(N_SAMPLES),
            "pretrigger_samples": int(PRETRIGGER_SAMPLES),
            "threshold_norm": float(threshold_norm),
            "threshold_counts": int(threshold_counts),
            "flat_sample_mem": flat_path.name,
            "expected_trigger_mem": trig_path.name,
            "expected_peak_count_mem": peak_count_path.name,
            "expected_peak_index_mem": peak_index_path.name,
        })

    hdl_labels = pd.DataFrame(hdl_label_rows)
    manifest = pd.DataFrame(manifest_rows)

    hdl_labels.to_csv(HDL_VECTOR_DIR / "nai59_hdl_labels.csv", index=False)
    manifest.to_csv(HDL_VECTOR_DIR / "nai59_hdl_manifest.csv", index=False)

    print("------------------------------------------------------------")
    print("HDL replay vector export completed")
    print("------------------------------------------------------------")
    print(f"Exported events per ADC bit depth : {N_EXPORT_EVENTS}")
    print(f"Samples per event                 : {N_SAMPLES}")
    print(f"Output directory                  : {HDL_VECTOR_DIR}")
    print("------------------------------------------------------------")
    print(manifest.to_string(index=False))
    print("------------------------------------------------------------")
    print("Saved:")
    print(f"  {HDL_VECTOR_DIR / 'nai59_hdl_labels.csv'}")
    print(f"  {HDL_VECTOR_DIR / 'nai59_hdl_manifest.csv'}")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
