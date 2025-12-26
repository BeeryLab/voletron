# Voletron Output Formats

Voletron generates several CSV files containing different analyses of the animal tracking data. These files are typically found in a subdirectory named `voletron_<chamber_name>` within your data directory.

## 1. Chamber Times (`*.chambers.csv`)

Records the total time each animal spent in each defined chamber.

**Columns:**
- `animal`: Name of the animal.
- `[chamber_names...]`: One column for each chamber name (e.g., `CentralA`, `Cage1`, `Tube1`), containing the time in seconds spent in that chamber.
- `total`: Total tracked time for the animal in seconds.

## 2. Pairwise Cohabitation (`*.cohab.csv` / `*.pair-inclusive.cohab.csv`)

Records the amount of time each pair of animals spent in the same location (chamber). "Inclusive" means that if animals A, B, and C are together, that counts for the pairs {A,B}, {B,C}, and {A,C}.

**Columns:**
- `Animal A`: Name of the first animal in the pair.
- `Animal B`: Name of the second animal in the pair.
- `dwells`: Number of separate cohabitation events (bouts).
- `seconds`: Total duration of cohabitation in seconds.
- `test_duration`: Total duration of the analysis period.

## 3. Group Chamber Cohabitation (`*.group_chamber_cohab.csv`)

Records cohabitation stats broken down by specific groups of animals in specific chambers. This is "exclusive", meaning a group of {A,B,C} is counted as that specific trio, not as subsets.

**Columns:**
- `animals`: Names of the animals in the group, space-separated.
- `chamber`: Name of the chamber where the group was located.
- `dwells`: Number of times this exact group was found in this chamber.
- `seconds`: Total duration in seconds.
- `test_duration`: Total duration of the analysis period.

## 4. Group Sizes (`*.group_size.csv`)

Summary statistics about social group sizes for each animal.

**Columns:**
- `animal`: Name of the animal.
- `1` through `8`: Total seconds the animal spent in a group of size N (where N=1 is solo).
- `avg_group_size`: The average size of the group the animal was in (weighted by time).
- `avg_group_size_nosolo`: The average size of the group when the animal was NOT alone.
- `sum_pair_time`: Metric reflecting total social exposure.
- `test_duration`: Total duration of the analysis period.

## 5. Long Dwells (`*.longdwells.csv`)

Lists dwells that exceed a certain duration threshold (default 6 hours), which might indicate a dropped tag or died animal.

**Columns:**
- `animal`: Name of the animal.
- `chamber`: Chamber where the long dwell occurred.
- `start_time`: Timestamp when the dwell began.
- `seconds`: Duration of the dwell in seconds.

## 6. Activity Time Series (`*.activity.*.csv`)

Time-series, data binning activity and social context into fixed time intervals (default 5 minutes).

**Columns:**
- `start_time`: Start timestamp of the bin.
- `end_time`: End timestamp of the bin.
- `bin_seconds`: Duration of the bin in seconds.
- `tag_id`: ID of the animal.
- `avg_dwell_size_1`: Average duration of solo dwells in this bin (?). *Note: Name might be misleading; code suggests it aggregates durations by group size.*
- `avg_dwell_size_2`: Metrics related to group size 2.
- `avg_dwell_size_3`: Metrics related to group size 3.
- `avg_dwell_size_4`: Metrics related to group size 4.
- `traversal_count`: Number of chamber transitions (movements) made by the animal during this bin.

## 7. Validation (`*.validate.csv`)

(Only generated if validation file provided)
Compares inferred locations against a manual ground-truth validation file.

**Columns:**
- `Correct`: `True` or `False`.
- `Timestamp`: Time of the validation check.
- `AnimalID`: Name of the animal.
- `Expected`: Chamber reported in validation file.
- `Observed`: List of chambers inferred by Voletron near that timestamp.
