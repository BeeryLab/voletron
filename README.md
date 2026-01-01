# Voletron

Voletron is an application for tracking animals as
they move through a laboratory habitat monitored by radio frequency
identification (RFID) antennas. Individuals are uniquely identified by passive
integrated transponders (PIT tags). These tags are not powered, but are
energized by the electromagnetic field of the antenna reader. The raw data
obtained from such an apparatus consists of a set of timestamped events,
indicating that a given RFID tag was in proximity to a given reader.

We assume that the habitat consists of multiple spaces ("chambers") with
openings leading to other chambers (including passageways), and that RFID
readers are placed at the apertures. Thus, the raw data from the apparatus
indicates when an animal passes from one chamber to another, but does not
indicate _in which direction_ it was traveling.

However: given a full set of such antenna reads, it is often possible to infer
the direction of travel. For instance, if an animal is first observed at the
aperture between chambers A and B, and then later at the aperture between
chambers B and C, then we can infer that it was present in chamber B in the
interim.

That is the purpose of Voletron: it ingests raw data (antenna reads) and a map
of the habitat, and infers the locations of animals within the habitat over
time. Given these inferences, it can then derive metrics of interest, such as
the total duration that two given animals were in the same chamber
("cohabitation"), the distribution of group sizes (number of animals in the same
chamber) over time, and so forth.

## Quick Start

### 1. Install Phase

**1. Install Python**

You need Python 3 installed. We recommend the latest version (e.g., Python 3.9, 3.10, or newer).
-   **Mac**: [Download Python for Mac](https://www.python.org/downloads/mac-osx/)
-   **Windows**: [Download Python for Windows](https://www.python.org/downloads/windows/) (Check "Add Python to PATH" during installation)

**2. Open your Terminal**

-   **Mac**: Open the "Terminal" app.
-   **Windows**: Open "Command Prompt" or "PowerShell".

**3. Navigate to this folder**

Use the `cd` command to go to the folder containing this README.
```bash
cd /path/to/voletron
```

**4. Set up a "Virtual Environment" (Optional but Recommended)**

This keeps the project dependencies isolated from your other files.
```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat
```

**6. Install Voletron (Optional but Recommended)**

Install Voletron in your Python environment:

```
python setup.py install
```

Once installed, you can run it like this:

```bash

voletron [ARGUMENTS]
```

***Advantages of Installation:***
1.  **Convenience**: You can run `voletron` from *any* directory, not just the source folder.
2.  **Cleanliness**: You don't need to type `python -m voletron.main`.
3.  **Integration**: It behaves like a standard system tool.


**7. Running Voletron without installing it**

If you prefer not to install Voletron, you can run it directly from the source folder.

In this case, first install `pytz`, which is required for timezone handling:
```bash
pip install pytz
```

With this setup, Voletron can be executed directly, but only from the source folder:

```
python -m voletron.main [...]
```

### 2. Prepare your data

Voletron analyzes one experiment at a time. Create a folder (e.g., `data/my_experiment/`) and place the following files inside:

**A. Raw Data from OLCUS**
-   A set of `.csv` files (e.g., `raw_data_001.csv`, `raw_data_002.csv`) containing the raw data from OLCUS.
-   Format: `cantimestamp; datetimestamp; deviceid; antennaID; data`.

**B. Animal Configuration File**
-   CSV file mapping animals to RFID tags and start locations.
-   Accepted names: `animals.csv` OR `*_animals.csv` (case-insensitive).
-   **Columns**: `AnimalName, TagId, StartChamber`
```csv
AnimalName, TagId, StartChamber
Vole1, 982000356123456, Cage1
Vole2, 982000356654321, CentralA
```
*Note: `StartChamber` defines the animal's location at the **very beginning of the experiment** (the time of the first data point in your raw files). Even if you use the `--start` argument to analyze a later time window, you must still provide the location at the experiment start. Voletron uses this to simulate the animal's movements up to your analysis start time.*

**C. Apparatus Configuration**
-   Describes the hardware layout (which antenna ID maps to which chamber).
-   Accepted names: `apparatus.json` OR `*_apparatus.json` (case-insensitive).
-   See `example_apparatus.json` in this repo for the structure.

**D. (Optional) Validation File**
-   Ground truth observations for manual validation.
-   Accepted names: `validation.csv` OR `*_validation.csv` (case-insensitive).
-   **Columns**: `Timestamp, AnimalName, Chamber`
```csv
Timestamp, AnimalName, Chamber
13.09.2020 12:00, Vole1, Tube1
```

### 3. Running the Analysis

To run Voletron, simply type:

```bash
voletron
```

If the `--olcus_dir` argument is not specified, Voletron will look for the default files in the current directory (i.e., you can navigate to the data directory first).

Outputs will be written to a subdirectory named `voletron/` within the data directory.

All arguments are optional.  For more details on arguments, please run

```
voletron --help
```

**Example (All Arguments):**
```bash
voletron \
  --olcus_dir="data/raw_reads/" \
  --start="01.01.2023 12:00:00:000" \
  --end="02.01.2023 12:00:00:000" \
  --bin_seconds=300 \
  --timezone="US/Pacific" \
  --dwell_threshold=10 \
  --verbose
```



---


## Run unit tests

```
python -m unittest discover -p "*_test.py"
```

## Inputs

**Raw antenna reads**. Voletron accepts CSV files produced by OLCUS (from
[FBI-science GmbH](https://fbiscience.com)) reading signals from their
[Aniloc](https://fbiscience.com/wp/index.php/en/aniloc-2/) system. These files
are formatted with 5 columns: `cantimestamp`, `datetimestamp`, `deviceid`,
`antennaID`, and `data`. `data` is the 15 digit ISO FDX-B RFID transponder
number. Antennas are indexed by the `deviceid` and `antennaID`.

**Apparatus configuration**. The default apparatus configuration in
[`example_apparatus.json`](example_apparatus.json) describes 2 habitat setups,
each with 4 side chambers arrayed around a central chamber. Ring antennas on the
tubes connect the side-chambers to the central arenas. The mapping is scalable
and flexible, but presumes two antennas per tube to define a side-chamber end
and a central-chamber end of each tube.

## Outputs

Outputs will be written to a subdirectory named `voletron/` within the data directory.

- `*.chambers.csv`: time each tag was present in each of the defined chambers.
- `*.pair-inclusive.cohab.csv`: pairwise association times of each pair of tags
  (for social network construction).
- `*.group_chamber_cohab.csv`: time each tag was found on its own, in each pair, trio,
  quad, etc., broken down by chamber.
- `*.group_size.csv`: average group sizes each tag was found in, and average
  group sizes when in a group (excluding solo time).
- `*.longdwells.csv`: reports any time an animal was present in a location for more than 6
  hours. In most well-functioning tests this should not occur, so this indicates a
  removed or lost RFID tag.
- `*.validate.csv` (optional): if validation data is provided, this file details
    whether the inferred animal location matched the expected location at specific timestamps.

See [outputs.md](outputs.md) for more details.

## Inference logic

When pit tags are detected at locations that are inconsistent with possible
transitions through the apparatus (e.g. skipping an antenna between two others), the
location is interpolated. The logic is:

1.  **Adjacent Reads**: If two consecutive reads are from adjacent antennas (sharing a chamber), the animal is assumed to be in that shared chamber for the duration.
2.  **Same Antenna**:
    *   **Short Dwell (< 10s)**: Assumed to be in the **Tube**.
    *   **Long Dwell (>= 10s)**: Assumed to be in the **Cage/Arena**.
3.  **Missing Reads (Non-Adjacent)**:
    *   If an animal appears at a location that is not adjacent to its last known location (e.g., jumping from `Tube1` connected to `Cage1` directly to `Tube2`), Voletron attempts to infer a single missing read at the Central Arena boundary.
    *   **Heuristic**: The logic assumes the animal passed through the Central Arena. To handle the time ambiguity (since we don't know exactly when it entered/left the arena), Voletron **maximizes the time allocated to the Central Arena** and minimizes time in the Tube.
    *   *Example (Tube -> Arena)*: If an animal is seen at the Cage-end of Tube 1, then next seen at a different Tube, the system infers it entered the Arena immediately after the first read.
    *   *Example (Arena -> Tube)*: If an animal is seen at a different Tube, then next seen at the Cage-end of Tube 1, the system infers it stayed in the Arena until just before the second read.


## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by Google
and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.

## Changelog

Version 2.0
- Complete refactoring / rewrite.
- Output cohab in tubes, not just in cages.
- Time-binned reports throughout.

## Known Todos

- TODO: examine error cases (e.g. cage vs. tube) and tweak heuristics, perhaps based on validation files.
- TODO: consider migrating to Colab/Jupyter?  Probably not, unless there is specific demand for it.
- Awaiting demand: bin transition counts into 10 min buckets per animal in order to
  generate histogram of activity pattern over the course of the day (for
  ultradian rhythms).  This is largely implemented but disabled, and could be revived on request.




