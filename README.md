# Voletron

Voletron is an application for tracking animals (or other moving objects) as
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

## Installation

Voletron can be executed directly:

```
python voletron/main.py [...]
```

or can be installed in your Python enviroment:

```
python setup.py install
```

## Usage

Please run

```
python voletron/main.py --help
```

## Run unit tests

```
python -m unittest discover -p "*_test.py"
```

## Inputs

**Raw antenna reads**. Voletron accepts csv files produced by OLCUS (from
[FBI-science GmbH](https://fbiscience.com)) reading signals from their
[Aniloc](https://fbiscience.com/wp/index.php/en/aniloc-2/) system. These files
are formatted with 5 columns: `cantimestamp`, `datetimestamp`, `deviceid`,
`antennaID`, and `data`. `data` is the 15 digit ISO FDX-B RFID transponder
number. Antennas are indexed by the `deviceid` and `antennaID`.

**Apparatus configuration**. The default apparatus configuration in
[`apparatus_config.py`](voletron/apparatus_config.py_) describes 2 arena setups,
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
- `*.longdwells.csv`: any time a vole was present in a location for > ??. In
  most well-functioning tests this should not have data, so indicates a removed
  or lost RFID tag.

## Inference logic

When pit tags are detected at locations that are inconsistent with possible
transitions through the arena (e.g. skipping an antenna between two others), the
location is interpolated. The default interpolation logic is: [TODO: describe]

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by Google
and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.

## Known Todos

- TODO: Add log file, containing both the command line and the text currently
  sent to stdout.
- TODO: examine error cases (e.g. cage vs. tube) and tweak heuristics
- TODO: bin transition counts into 10 min buckets per animal in order to
  generate histogram of activity pattern over the course of the day (for
  ultradian rhythms)
- TODO: consider migrating to Colab/Jupyter
