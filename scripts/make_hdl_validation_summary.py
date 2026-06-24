from pathlib import Path
import subprocess
import pandas as pd
import re

# =============================================================================
# Create HDL validation summary files
# =============================================================================
#
# This script runs the existing HDL validation flow and parses the terminal
# output into publication-friendly CSV and TXT summary files.
#
# Inputs:
#   hdl/run_hdl_validation.sh
#
# Outputs:
#   hdl/hdl_validation_summary.csv
#   hdl/hdl_validation_summary.txt
#   hdl/hdl_validation_raw_output.txt
#
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
HDL_DIR = PROJECT_DIR / "hdl"

RUN_SCRIPT = HDL_DIR / "run_hdl_validation.sh"

RAW_OUTPUT_PATH = HDL_DIR / "hdl_validation_raw_output.txt"
SUMMARY_CSV_PATH = HDL_DIR / "hdl_validation_summary.csv"
SUMMARY_TXT_PATH = HDL_DIR / "hdl_validation_summary.txt"


def require_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def parse_hdl_output(output_text):
    """
    Parse Icarus Verilog validation output.

    Expected blocks contain:
      Starting HDL validation for 8-bit replay vectors
      Total events checked : 1024
      Total errors         : 0
      RESULT: PASS
    """

    rows = []

    current_bits = None
    current_events = None
    current_errors = None
    current_result = None

    for line in output_text.splitlines():
        line = line.strip()

        m_bits = re.search(r"Starting HDL validation for\s+(\d+)-bit", line)
        if m_bits:
            current_bits = int(m_bits.group(1))
            current_events = None
            current_errors = None
            current_result = None
            continue

        m_events = re.search(r"Total events checked\s*:\s*(\d+)", line)
        if m_events:
            current_events = int(m_events.group(1))
            continue

        m_errors = re.search(r"Total errors\s*:\s*(\d+)", line)
        if m_errors:
            current_errors = int(m_errors.group(1))
            continue

        m_result = re.search(r"RESULT:\s*(PASS|FAIL)", line)
        if m_result:
            current_result = m_result.group(1)

            if current_bits is None:
                raise RuntimeError("Found RESULT line before ADC bit-depth line.")

            rows.append({
                "adc_bits": current_bits,
                "events_checked": current_events,
                "total_errors": current_errors,
                "result": current_result,
            })

            current_bits = None
            current_events = None
            current_errors = None
            current_result = None

    if not rows:
        raise RuntimeError("Could not parse HDL validation output.")

    return pd.DataFrame(rows)


def main():
    require_file(RUN_SCRIPT)

    print("------------------------------------------------------------")
    print("Running HDL validation and generating summary files")
    print("------------------------------------------------------------")

    result = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    combined_output = ""
    combined_output += result.stdout
    if result.stderr:
        combined_output += "\n--- STDERR ---\n"
        combined_output += result.stderr

    RAW_OUTPUT_PATH.write_text(combined_output)

    if result.returncode != 0:
        print(combined_output)
        raise RuntimeError(
            f"HDL validation script failed with return code {result.returncode}."
        )

    summary = parse_hdl_output(combined_output)
    summary.to_csv(SUMMARY_CSV_PATH, index=False)

    n_pass = int((summary["result"] == "PASS").sum())
    n_total = len(summary)
    total_events = int(summary["events_checked"].sum())
    total_errors = int(summary["total_errors"].sum())

    summary_text = f"""
HDL validation summary:
The HDL validation was performed using Icarus Verilog replay testbenches for 8-bit, 10-bit and 12-bit ADC waveform datasets. Each testbench replayed 1024 synthetic NaI(Tl) waveform events, with 500 samples per event. The Verilog module implemented pre-trigger baseline estimation, threshold triggering, peak-count extraction and peak-index extraction.

Validation result:
ADC configurations tested : {n_total}
Configurations passed     : {n_pass}
Total replayed events     : {total_events}
Total mismatches          : {total_errors}

Per-configuration result:
""".strip()

    for _, row in summary.iterrows():
        summary_text += (
            f"\n- {int(row['adc_bits'])}-bit: "
            f"{int(row['events_checked'])} events checked, "
            f"{int(row['total_errors'])} errors, "
            f"{row['result']}"
        )

    if total_errors == 0 and n_pass == n_total:
        summary_text += (
            "\n\nAll HDL outputs matched the software reference labels for "
            "trigger decision, peak count and peak index."
        )
    else:
        summary_text += (
            "\n\nAt least one HDL configuration produced mismatches relative "
            "to the software reference labels."
        )

    SUMMARY_TXT_PATH.write_text(summary_text)

    print(combined_output)
    print("------------------------------------------------------------")
    print("HDL validation summary generated")
    print("------------------------------------------------------------")
    print(summary.to_string(index=False))
    print("------------------------------------------------------------")
    print("Saved:")
    print(f"  {SUMMARY_CSV_PATH}")
    print(f"  {SUMMARY_TXT_PATH}")
    print(f"  {RAW_OUTPUT_PATH}")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
