import argparse
import datetime
import os
import sys

from voletron.apparatus_config import all_chambers
from voletron.parse_config import parse_config, parse_validation
from voletron.parse_olcus import parse_first_read, parse_raw_dir
from voletron.preprocess_reads import preprocess_reads
from voletron.state import State
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time


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

    # TODO: Perform validation
    # Validation
    validate(out_dir, exp_name, trajectories, args.validation, config.tag_id_to_name)

    writeChamberTimes(
        config, out_dir, exp_name, trajectories, analysis_start_time, analysis_end_time
    )
    writeCohabs(
        config, out_dir, exp_name, state, analysis_start_time, analysis_end_time
    )
    writeLongDwells(config, out_dir, exp_name, trajectories)


# def writeFullHistory(config, out_dir, exp_name, state):
#    with open(os.path.join(out_dir, exp_name+'.states.csv'), "w") as f:
#         f.write("Animal A,Animal B,dwells\nseconds\n")
#         for (a, b, c, d) in state.co_dwell_stats(config.tag_id_to_name.keys()):
#             f.write("{},{},{},{}\n".format(config.tag_id_to_name[a], config.tag_id_to_name[b], c, d))


def validate(out_dir, exp_name, trajectories, filename, tag_id_to_name):
    print("\nValidation:")
    print("-----------------------------")
    if not filename:
        print("No validation file provided")
        return

    validations = parse_validation(
        filename, {v: k for (k, v) in tag_id_to_name.items()}
    )

    with open(os.path.join(out_dir, exp_name + ".validate.csv"), "w") as f:
        f.write("Correct,Timestamp,AnimalID,Expected,Observed\n")
        correct = 0
        for v in validations:
            # Charitably use a 2-minute window
            actual = trajectories.get_locations_between(
                v.tag_id, v.timestamp - 30, v.timestamp + 90
            )
            ok = v.chamber in actual
            correct += ok

            f.write("{},{},{},{},{}\n".format(ok,format_time(v.timestamp),tag_id_to_name[v.tag_id], v.chamber, actual))

    print(
        "{} of {} ({:>6.2%}) validation points correct.".format(
            correct, len(validations), correct / len(validations)
        )
    )


def writeCohabs(
    config, out_dir, exp_name, state, analysis_start_time, analysis_end_time
):
    with open(os.path.join(out_dir, exp_name + ".cohab.csv"), "w") as f:
        f.write("Animal A,Animal B,dwells,seconds\n")
        for (a, b, c, d) in state.co_dwell_stats(
            config.tag_id_to_name.keys(), analysis_start_time, analysis_end_time
        ):
            f.write(
                "{},{},{},{:.0f}\n".format(
                    config.tag_id_to_name[a], config.tag_id_to_name[b], c, d
                )
            )


def writeChamberTimes(
    config, out_dir, exp_name, trajectories, analysis_start_time, analysis_end_time
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("animal," + ",".join(all_chambers) + ",total\n")
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            ct = trajectory.time_per_chamber(analysis_start_time, analysis_end_time)
            # f.write("{}, {:.0f}".format(config.tag_id_to_name[tag_id], sum(ct.values())))
            aaa = ",".join(map(lambda c: "{:.0f}".format(ct[c]), all_chambers))
            f.write(
                "{},{},{:.0f}\n".format(
                    config.tag_id_to_name[tag_id], aaa, sum(ct.values())
                )
            )


def writeLongDwells(config, out_dir, exp_name, trajectories):
    with open(os.path.join(out_dir, exp_name + ".longdwells.csv"), "w") as f:
        f.write("animal,chamber,start_time,seconds\n")
        for trajectory in trajectories.animalTrajectories.values():
            for d in trajectory.long_dwells():
                f.write(
                    "{},{},{},{:.0f}\n".format(
                        config.tag_id_to_name[d[0]], d[1], format_time(d[2]), d[3]
                    )
                )


main(sys.argv)
