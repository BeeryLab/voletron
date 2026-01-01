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

**5. Install Dependencies**

This project requires `pytz` for timezone handling.
```bash
pip install pytz
```
*(There is no need to run setup.py install)*

### 2. Prepare your data
Voletron analyzes one experiment at a time. Create a folder (e.g., `data/my_experiment/`) and place the following files inside:

**A. Raw Data from OLCUS**
-   A flat directory of `.csv` files (e.g., `raw_data_001.csv`, `raw_data_002.csv`).
-   Format: `cantimestamp; datetimestamp; deviceid; antennaID; data`.

**B. Configuration File**
-   CSV file mapping animals to RFID tags and start locations.
-   Accepted names: `config.csv` OR `*_config.csv` (case-insensitive).
-   **Columns**: `AnimalName, TagId, StartChamber`
```csv
AnimalName, TagId, StartChamber
Vole1, 982000356123456, Cage1
Vole2, 982000356654321, CentralA
```

**C. Apparatus Configuration**
-   Describes the hardware layout (which antenna ID maps to which chamber).
-   Accepted names: `apparatus.json` OR `*_apparatus.json` (case-insensitive).
-   See `apparatus_example.json` in this repo for the structure.

**D. (Optional) Validation File**
-   Ground truth observations for manual validation.
-   Accepted names: `validation.csv` OR `*_validation.csv` (case-insensitive).
-   **Columns**: `Timestamp, AnimalID, Chamber`
```csv
Timestamp, AnimalID, Chamber
13.09.2020 12:00, Vole1, Tube1
```

### 3. Running the Code

To run Voletron, use the following command structure from the main folder:

```bash
python -m voletron.main [ARGUMENTS]
```

**Example:**
```bash
python -m voletron.main --config_file="my_config.csv" --olcus_dir="data/raw_reads/" --output_dir="data/output/"
```

See the **Usage** section below for more details on arguments.

---

## Installation (Advanced Users)

Voletron can be executed directly:

```
python -m voletron.main [...]
```

or can be installed in your Python enviroment:

```
python setup.py install
```

## Usage

Please run

```
python -m voletron.main --help
```

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
[`apparatus_config.py`](voletron/apparatus_config.py_) describes 2 habitat setups,
each with 4 side chambers arrayed around a central chamber. Ring antennas on the
tubes connect the side-chambers to the central arenas. The mapping is scalable
and flexible, but presumes two antennas per tube to define a side-chamber end
and a central-chamber end of each tube.

## Outputs

A set of output files are written to the same directory where the inputs were
found.

- `*.chambers.csv`: time each tag was present in each of the defined chambers.
- `*.cohab.csv`: pairwise association times of each pair of tags (for social
  network construction).
- `*.group_cohab.csv`: time each tag was found on its own, in each pair, trio,
  quad, etc.
- `*.group_size.csv`: average group sizes each tag was found in, and average
  group sizes when in a group (excluding solo time).
- `*.longdwells.csv`: any time a vole was present in a location for more than 6
  hours. In most well-functioning tests this should not occur, so it indicates a
  removed or lost RFID tag.

## Inference logic

When pit tags are detected at locations that are inconsistent with possible
transitions through the central arena (e.g. skipping an antenna between two others), the
location is interpolated. The default interpolation logic is: [TODO: describe]

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
- Complete refactoring / rewrite
- Output cohab in tubes, not just in cages
- Binned activity

## Recently done (Kelley requests to validate)

1. Output file that sums seconds of cohab between voles in a specific chamber. Include all groupings from group cohab file (vole A+B, A+C, A+D, A+B+C, A+B+D, A+C+D, A+B+C+D etc.) for each chamber (central arena, cage 1,2,3,4). Include dwells and seconds. (Home cage analysis)
Outputs: See attached Sheet 1. 

2. Activity-I think you're already working on this, but bin transitions by 5 min increments by clock time. I'm less sure of how this output looks, so feel free to change. Could bump increments up to 10 mins. (Activity/Rhythms analysis)
Outputs: See attached Sheet 2



## Known Todos

- TODO: Add log file, containing both the command line and the text currently
  sent to stdout.
- TODO: examine error cases (e.g. cage vs. tube) and tweak heuristics
- TODO: bin transition counts into 10 min buckets per animal in order to
  generate histogram of activity pattern over the course of the day (for
  ultradian rhythms)
- TODO: consider migrating to Colab/Jupyter
- TODO: more tests






3. Summary file/general thoughts on bins-is it possible to have two outputs here? Bins for one output by clock time in and the other by amount of time in arena? Is it also possible for me to change the borders for both outputs if needed during analysis? If not, can clock time be in 30 min intervals (12:00, 12:30, 13:00 etc.)  and time in arena be hourly (starting 10 mins after first tag read for 60 mins, 120 mins etc.).
Outputs: See attached Sheet 3. Same output for time elapsed in arena.

Investigate possible bug re. config at run start time vs. analysis start time??