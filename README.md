# Voletron

Voletron is an application for tracking animals (or other moving objects) as they move through a habitat monitored by radio frequency identification (RFID) antennas. Individuals are uniquely identified by passive integrated transponders (PIT tags). These tags are not powered, but are energized by the electromagnetic field of the antenna reader.




Voletron is a Python application that takes raw RFID antenna reads from multiple pit tags and builds up a model of co-occurance of those pit tags in user-defined zones. Outputs provide multiple metrics of location and cohabitation duration, namely:

Inputs: Voletron currently takes raw csv files produced by OLCUS (from FBIscience) reading signals from their Aniloc system.  These files are formatted with 5 columns: cantimestamp, datetimestamp, deviceid, antennaID, and data. Data is the 15 digit ISO FDXB RFID tag number. Antennas are indexed by the deviceid and antennaID.

Outputs:
Chambers output: time each tag was present in each of the defined chambers
Cohab: pairwise association times of each pair of tags (for social network construction)
Group_cohab:  time each tag was found on its own, in each pair, trio, quad, etc.
Group_size: average group sizes each tag was found in, and average group sizes when in a group (excluding solo time), sum_pair_time = ??
Longdwells: any time a vole was present in a location for > ??. In most well-functioning tests this should not have data, so indicates a removed or lost RFID tag.

The default apparatus configuration in <file> describes 2 arena setups, each with 4 side chambers arrayed around a central chamber. Ring antennas on the tubes connect the side-chambers to the central arenas. The mapping is scalable and flexible, but presumes two antennas per tube to define a sidechamber end and a central chamber end of each tube.

When pit tags are detected at locations that are inconsistent with possible transitions through the arena (e.g. skipping an antenna between two others), the location is interpolated. The default interpolation logic is: <describe>

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by
Google and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.

## Known Todos

----Sooner----

TODO: Add log file, recording time interval and stdout

TODO: examine error cases (e.g. cage vs. tube) and tweak heuristics

----Later----

TODO: bin transition counts into 10 min buckets per animal in order to generate histogram of activity pattern over the course of the day (for ultradian rhythms)
TODO: readme
TODO: consider migrating to CoLab
