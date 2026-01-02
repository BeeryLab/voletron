# End-to-End Test Suite

This directory contains a complete end-to-end test suite for Voletron. It generates synthetic data with known animal behaviors, processes it through the entire Voletron pipeline, and verifies the output against a "golden" reference.

## Test Structure

*   **`generate_data.py`**: A Python script that creates a synthetic experiment. It defines the apparatus, animals, and a precise sequence of timestamped RFID reads simulating animal movements. It outputs to the `experiment/` subdirectory.
*   **`run_test.sh`**: The main entry point. This script:
    1.  Deletes any old `experiment/` directory.
    2.  Runs `generate_data.py` to create fresh input data.
    3.  Runs Voletron on the `experiment/` directory.
    4.  Diffs the generated output CSVs against the `golden/` directory.
*   **`golden/`**: Contains the verified ("golden") CSV outputs expected from Voletron.
*   **`experiment/`**: (Ignored by git) The working directory where input data and current Voletron outputs are generated.

## Running the Test

Simply execute the shell script:

```bash
./run_test.sh
```

If the test passes, it will output `✅ End-to-End Test Passed!`. If it fails, `diff` will show the discrepancies.

## Scenario Description

The test simulates **4 animals (Animal_A, Animal_B, Animal_C, Animal_D)** in an apparatus with **4 Cages**. The experiment lasts for **15 minutes** and is analyzed in **5-minute bins**.

### Bin 1 (00:00 - 05:00)
*   **Animal_A** and **Animal_B** enter **Cage 1** and stay there (forming a Pair).
*   **Animal_C** enters **Cage 2** and stays there (Solo).
*   **Animal_D** enters **Cage 3** and stays there (Solo).

### Bin 2 (05:00 - 10:00)
*   **Animal_A** leaves Cage 1 and moves to **Cage 2**, joining Animal_C.
*   **Animal_B** remains in **Cage 1** (now Solo).
*   **Animal_D** remains in **Cage 3** (still Solo).
*   *Result*: A & C are now a pair in Cage 2. B and D are solo.

### Bin 3 (10:00 - 15:00)
*   **All Animals** (A, B, C, D) move to **Cage 4**.
*   *Result*: A single group of 4 animals in Cage 4.

### Validation Data
The test also generates a `validation.csv` file with 4 entries to verify the validation logic:
1.  **Correct**: Animal_A in Cage 1 at T=100s.
2.  **Correct**: Animal_C in Cage 2 at T=100s.
3.  **Correct**: Animal_A in Cage 2 at T=400s.
4.  **Incorrect**: Animal_B in Cage 2 at T=400s (Observed: Cage 1).
