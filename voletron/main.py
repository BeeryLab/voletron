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
from cmath import exp
import datetime
import glob
import os
import sys
import pytz

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from voletron.apparatus_config import apparatus_chambers, all_chambers
from voletron.output import (
    write_activity,
    write_chamber_times,
    write_pair_inclusive_cohabs,
    write_group_chamber_cohabs,
    write_group_sizes,
    write_long_dwells,
)
from voletron.parse_config import parse_config, parse_validation
from voletron.parse_olcus import parse_first_read, parse_raw_dir
from voletron.preprocess_reads import preprocess_reads
from voletron.co_dwell_accumulator import CoDwellAccumulator
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.validate import write_validation
from voletron.types import Config, TimestampSeconds, Validation
from voletron.time_span_analyzer import TimeSpanAnalyzer


def _parse_args(argv):
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
    parser.add_argument(
        "--bin_seconds",
        type=int,
        help="Bin size, in seconds, for time-series outputs.  Default: 1800",
        default=1800
    )
    parser.add_argument(
        "--habitat_time_offset_seconds",
        type=int,
        help="Seconds after the first tag read when the 'time in habitat' clock "
        "is considered to begin, for purposes of activity time series "
        "reporting.  Default: 600",
        default=600
    )
    parser.add_argument(
        "timezone",
        default="US/Pacific",
        help="Olcus logs timestamps in the local timezone, but does not record "
        "which timezone that is.  Thus, we allow specifying the timezone in "
        "which the Olcus logs should be interpreted.  This makes no difference "
        "to the current analyses, which are all just about durations anyway, "
        "not about absolute time.  Defaults to 'US/Pacific'.  Other options "
        "are listed at "
        "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones."
        )
    return parser.parse_args()


def _parse_config(args, timezone) -> tuple[Config, list[Validation], str]:
    configFiles = glob.glob(os.path.join(args.olcusDir, "*_[Cc]onfig.csv"))
    if len(configFiles) != 1:
        raise ValueError("Could not find exactly one `*_Config.csv` file.")

    config = parse_config(configFiles[0])

    validations: list[Validation] = []
    if args.validation:
        validationFiles = glob.glob(os.path.join(args.olcusDir, "*_[Vv]alidation.csv"))
        if len(configFiles) != 1:
            raise ValueError("Could not find exactly one `*_Validation.csv` file.")

        validations = parse_validation(
            validationFiles[0], {v: k for (k, v) in config.tag_id_to_name.items()}, timezone
        )

    olcusDir = os.path.normpath(args.olcusDir)

    return (config, validations, olcusDir)


def main(argv):
    """Analyze a 'raw' file describing Olcus antenna data from a Beery Lab
    vole group-living RFID apparatus.  Infers co-habitation bouts and total
    co-hab duration for each pair of animals."""

    print("\n===================================")
    print("Voletron v0.2, 2022-08-14")
    print("http://github.com/beerylab/voletron")
    print("===================================")
    print("")

    ### Parse command-line arguments

    args = _parse_args(argv)
    timezone : datetime.tzinfo = pytz.timezone(args.timezone)

    ### Read input config and validation files

    (config, validations, olcusDir) = _parse_config(args, timezone)

    ### Read raw data

    print("\nReading Data:")
    print("-----------------------------")
    reads = parse_raw_dir(olcusDir, timezone)

    # The first read may require inserting a missing read before it;
    # start the experiment 5 ms earlier to account for this.
    first_read_time: TimestampSeconds = TimestampSeconds(parse_first_read(args.olcusDir, timezone).timestamp - 0.005)
    if args.start != None:
        analysis_start_time = TimestampSeconds(timezone.localize(datetime.datetime.strptime(
            args.start, "%d.%m.%Y %H:%M:%S:%f"
        )).timestamp())
    else:
        analysis_start_time = first_read_time

    ### Initial cleanup of the reads, per animal

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
        analysis_end_time = TimestampSeconds(timezone.localize(datetime.datetime.strptime(
            args.end, "%d.%m.%Y %H:%M:%S:%f"
        )).timestamp())
    else:
        analysis_end_time = last_read_time

    print("\nIntervals:")
    print("-----------------------------")
    print("Experiment Start (first read): {}".format(format_time(first_read_time)))
    print("               Analysis Start: {}".format(format_time(analysis_start_time)))
    print("                 Analysis End: {}".format(format_time(analysis_end_time)))
    print("   Experiment End (last read): {}".format(format_time(last_read_time)))

    ### Infer animal trajectories from antenna reads

    trajectories = AllAnimalTrajectories(
        first_read_time, config.tag_id_to_start_chamber, reads_per_animal
    )

    # all_chambers =  [item for sublist in apparatus_chambers.values() for item in sublist]
    
    # print("----CHAMBERS")
    # print(all_chambers)
    # print("----CHAMBERS")

    # Simulate state forwards, accumulating stats in the state object
    # and write it out along the way
    state = CoDwellAccumulator(first_read_time, config.tag_id_to_start_chamber, all_chambers)
    for t in trajectories.traversals():
        state.update_state_from_traversal(t)
    co_dwells = state.end(analysis_end_time)

    # Slice out the time span of interest for analysis
    # TODO(soergel): bins here
    analyzer = TimeSpanAnalyzer(co_dwells, analysis_start_time, analysis_end_time)

    # Output

    exp_name = str(os.path.basename(olcusDir))

    for (desired_start_chamber, chambers) in apparatus_chambers.items():

        # Filter animals by apparatus
        tag_ids = [
            tag_id
            for (tag_id, start_chamber) in config.tag_id_to_start_chamber.items()
            if start_chamber == desired_start_chamber
        ]

        out_dir = os.path.join(olcusDir, "voletron_" + desired_start_chamber)
        os.makedirs(out_dir)

        # Trajectory-based outputs

        if args.validation:
            # Validation
            write_validation(
                tag_ids,
                out_dir,
                exp_name,
                trajectories,
                config.tag_id_to_name,
                validations,
            )

        write_chamber_times(
            config,
            tag_ids,
            chambers,
            out_dir,
            exp_name,
            trajectories,
            analysis_start_time,
            analysis_end_time,
        )

        write_long_dwells(config, tag_ids, out_dir, exp_name, trajectories)
        
        # This one builds its own analyzer per bin
        write_activity(
            out_dir,
            exp_name,
            "wall_clock",
            trajectories,
            co_dwells,
            analysis_start_time,
            analysis_end_time,
            args.bin_seconds,
        )
        
        write_activity(
            out_dir,
            exp_name,
            "habitat_time",
            trajectories,
            co_dwells,
            first_read_time + args.habitat_time_offset_seconds,
            last_read_time,
            args.bin_seconds,
        )

        # TimeSpanAnalyzer-based outputs

        write_pair_inclusive_cohabs(
            config,
            out_dir,
            exp_name,
            analyzer,
        )

        write_group_chamber_cohabs(
            tag_ids,
            out_dir,
            exp_name,
            analyzer,
            config.tag_id_to_name,
        )

        write_group_sizes(
            tag_ids,
            out_dir,
            exp_name,
            analyzer,
            config.tag_id_to_name,
        )


main(sys.argv)
