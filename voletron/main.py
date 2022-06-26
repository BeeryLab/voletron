# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import datetime
import glob
import os
import sys

from voletron.apparatus_config import apparatus_chambers
from voletron.output import (
    writeChamberTimes,
    writeCohabs,
    writeGroupCohabs,
    writeGroupSizes,
    writeLongDwells,
)
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
        "olcusDir",
        help="A directory containing Olcus output files.  "
        "Any file in this directory called `raw*.csv` will be processed.  "
        "The directory must contain exactly one file called `*_Config.csv`, "
        "comprised of lines of the form `animal_name, tag_id, initial_chamber`.",
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
        action=argparse.BooleanOptionalAction,
        help="Manual validation data for the run.  "
        "Looks in the data directory for a file called `*_Validation.csv`, "
        "comprised of lines of the form `timestamp, animal_name, chamber`.",
    )
    args = parser.parse_args()

    configFiles = glob.glob(os.path.join(args.olcusDir, "*_[Cc]onfig.csv"))
    if len(configFiles) != 1:
        raise ValueError("Could not find exactly one `*_Config.csv` file.")

    config = parse_config(configFiles[0])

    if args.validation:
        validationFiles = glob.glob(os.path.join(args.olcusDir, "*_[Vv]alidation.csv"))
        if len(configFiles) != 1:
            raise ValueError("Could not find exactly one `*_Validation.csv` file.")

        validations = parse_validation(
            validationFiles[0], {v: k for (k, v) in config.tag_id_to_name.items()}
        )

    olcusDir = os.path.normpath(args.olcusDir)

    print("\n===================================")
    print("Voletron v0.1, 2020-12-27")
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

    reads_per_animal = preprocess_reads(
        reads, config.tag_id_to_start_chamber.keys(), config.tag_id_to_name
    )

    unobserved_animals = [kk for (kk, vv) in reads_per_animal.items() if len(vv) == 0]
    if unobserved_animals:


        print("\n\n-----------------------------")
        print("WARNING: Animals in config but not observed:")
        print(unobserved_animals)
        print("----------------------------\n\n")

    last_read_time = max([vv[-1].timestamp for vv in reads_per_animal.values()])
    if args.end != None:
        analysis_end_time = datetime.datetime.strptime(
            args.end, "%d.%m.%Y %H:%M:%S:%f"
        ).timestamp()
    else:
        analysis_end_time = last_read_time

    print("\nIntervals:")
    print("-----------------------------")
    print("Experiment Start (first read): {}".format(format_time(first_read_time)))
    print("               Analysis Start: {}".format(format_time(analysis_start_time)))
    print("                 Analysis End: {}".format(format_time(analysis_end_time)))
    print("   Experiment End (last read): {}".format(format_time(last_read_time)))

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

    for (desired_start_chamber, chambers) in apparatus_chambers.items():

        # Filter animals by apparatus
        tag_ids = [
            tag_id
            for (tag_id, start_chamber) in config.tag_id_to_start_chamber.items()
            if start_chamber == desired_start_chamber
        ]

        out_dir = os.path.join(olcusDir, "voletron_" + desired_start_chamber)
        os.makedirs(out_dir)

        if args.validation:
            # Validation
            validate(
                tag_ids,
                out_dir,
                exp_name,
                trajectories,
                config.tag_id_to_name,
                validations,
            )

        writeChamberTimes(
            config,
            tag_ids,
            chambers,
            out_dir,
            exp_name,
            trajectories,
            analysis_start_time,
            analysis_end_time,
        )
        writeCohabs(
            config,
            tag_ids,
            out_dir,
            exp_name,
            state,
            analysis_start_time,
            analysis_end_time,
        )
        writeGroupCohabs(
            config,
            tag_ids,
            out_dir,
            exp_name,
            state,
            analysis_start_time,
            analysis_end_time,
            config.tag_id_to_name,
        )
        writeGroupSizes(
            tag_ids,
            out_dir,
            exp_name,
            state,
            analysis_start_time,
            analysis_end_time,
            config.tag_id_to_name,
        )
        writeLongDwells(config, tag_ids, out_dir, exp_name, trajectories)


main(sys.argv)
