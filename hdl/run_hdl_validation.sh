#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Running NaI(Tl) HDL validation..."

echo "--- 8-bit validation ---"
iverilog -g2012 -o tb_nai59_8bit.vvp nai59_peak_trigger.v tb_nai59_8bit.v
vvp tb_nai59_8bit.vvp

echo "--- 10-bit validation ---"
iverilog -g2012 -o tb_nai59_10bit.vvp nai59_peak_trigger.v tb_nai59_10bit.v
vvp tb_nai59_10bit.vvp

echo "--- 12-bit validation ---"
iverilog -g2012 -o tb_nai59_12bit.vvp nai59_peak_trigger.v tb_nai59_12bit.v
vvp tb_nai59_12bit.vvp

