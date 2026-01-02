#!/bin/bash
set -e

# Change to the directory of this script
cd "$(dirname "$0")"

echo "Cleaning up old experiment data..."
rm -rf experiment

echo "Generating fresh test data..."
python3 generate_data.py

echo "Running Voletron..."
echo
# We need to include the parent directory in PYTHONPATH so python can find the 'voletron' package
export PYTHONPATH=$PYTHONPATH:..
python3 -m voletron.main --olcus_dir ./experiment --bin_seconds 300 --start "01.01.2022 12:00:00:000" --end "01.01.2022 12:15:00:000"

echo
echo
echo "Diffing results against golden data..."
# Compare the output CSVs in HabitatA with the golden directory
diff -r experiment/voletron/HabitatA golden

echo "✅ End-to-End Test Passed!"
