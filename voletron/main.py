import argparse
import datetime
import os
import sys

from voletron.apparatus_config import all_chambers
from voletron.output import writeChamberTimes, writeCohabs, writeLongDwells
from voletron.parse_config import parse_config, parse_validation
from voletron.parse_olcus import parse_first_read, parse_raw_dir
from voletron.preprocess_reads import preprocess_reads
from voletron.state import State
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.validate import validate


def main(argv):
    """Analyze a 'raw' file describing Olcus antenna data from a Beery Lab
    vole group-living RFID apparatus.  Infers co-habitation bouts and total
    co-hab duration for each pair of animals."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        help="Configuration file for the run.  "
        "CSV with lines of the form `animal_name, tag_id, initial_chamber`.",
    )
    parser.add_argument(
        "olcusDir",
        help="A directory containing Olcus output files.  "
        "Any file in this directory called `raw*.csv` will be processed.",
    )
    parser.add_argument(
        "--start",
        help="Time at which to start the analysis, in the form "
        "`DD.MM.YYYY HH:MM:SS:fff` (matching what is found in the Olcus "
        "raw*.csv files).  Note the hour is given in 24-hour time. "
        "Default: Start from the beginning of the provided data. "
        "Note: Data from the beginning of the experiment will be analyzed "
        "anyway, to determine the locations of the animals at the given start "
        "time.",
    )
    parser.add_argument(
        "--end",
        help="Time at which to end the analysis, in the form "
        "`DD.MM.YYYY HH:MM:SS:fff` (matching what is found in the Olcus "
        "raw*.csv files).  Note the hour is given in 24-hour time.  "
        "Default: continue to the end of the provided data.",
    )
    parser.add_argument(
        "--validation",
        help="Manual validation data for the run.  "
        "CSV with lines of the form `timestamp, animal_name, chamber`.",
    )
    args = parser.parse_args()

    config = parse_config(args.config)
    olcusDir = os.path.normpath(args.olcusDir)

    print("\n===================================")
    print("VoleTron v0.1, 2020-12-27")
    print("http://github.com/beerylab/voletron")
    print("===================================")
    print("")

    print("\nReading Data:")
    print("-----------------------------")
    reads = parse_raw_dir(olcusDir)

    # The first read may require inserting a missing read before it;
    # start the experiment 5 ms earlier to account for this.
    first_read_time = parse_first_read(args.olcusDir).timestamp - 0.005
    if args.start != None:
        analysis_start_time = datetime.datetime.strptime(
            args.start, "%d.%m.%Y %H:%M:%S:%f"
        ).timestamp()
    else:
        analysis_start_time = first_read_time

    reads_per_animal = preprocess_reads(reads, config.tag_id_to_start_chamber.keys(), config.tag_id_to_name)

    last_read_time = max([vv[-1].timestamp for vv in reads_per_animal.values()])
    if args.end != None:
        analysis_end_time = datetime.datetime.strptime(
            args.end, "%d.%m.%Y %H:%M:%S:%f"
        ).timestamp()
    else:
        analysis_end_time = last_read_time

    # Infer animal trajectories from antenna reads
    trajectories = AllAnimalTrajectories(
        first_read_time, config.tag_id_to_start_chamber, reads_per_animal
    )

    # Simulate state forwards, accumulating stats in the state object
    # and write it out along the way

    state = State(first_read_time, config.tag_id_to_start_chamber)
    for t in trajectories.traversals():
        state.update_state_from_traversal(t)
    state.end()

    # Output

    exp_name = os.path.basename(olcusDir)
    out_dir = os.path.join(olcusDir, "voletron")
    os.makedirs(out_dir)

    # Validation
    validate(out_dir, exp_name, trajectories, args.validation, config.tag_id_to_name)

    writeChamberTimes(
        config, out_dir, exp_name, trajectories, analysis_start_time, analysis_end_time
    )
    writeCohabs(
        config, out_dir, exp_name, state, analysis_start_time, analysis_end_time
    )
    writeLongDwells(config, out_dir, exp_name, trajectories)



main(sys.argv)
