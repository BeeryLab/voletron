# Copyright 2022-2025 Google LLC
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
import logging
import os
import sys
from typing import Dict
import pytz

from voletron.output.output import write_outputs

# Removed sys.path hack. Please run as python -m voletron.main

from voletron.apparatus_config import all_chambers, load_apparatus_config
from voletron.parse_config import parse_config, parse_validation
from voletron.parse_olcus import parse_first_read, parse_raw_dir
from voletron.preprocess_reads import preprocess_reads
from voletron.co_dwell_accumulator import CoDwellAccumulator
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.constants import DEFAULT_TIME_BETWEEN_READS_THRESHOLD
from voletron.types import Config, Read, TagID, TimestampSeconds, Validation
from voletron.time_span_analyzer import TimeSpanAnalyzer


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--olcus_dir",
        "--olcusDir",
        required=True,
        help="A directory containing Olcus output files.  "
        "Any file in this directory called `raw*.csv` will be processed.  "
        "The directory must contain exactly one file called `animals.csv` (or `*_animals.csv`), "
        "comprised of lines of the form `animal_name, tag_id, initial_chamber`, "
        "and exactly one file called `apparatus.json` (or `*_apparatus.json`), "
        "formatted as shown in the provided `apparatus_example.json`, "
        "and optionally exactly one file called `validation.csv` (or `*_validation.csv`), "
        "comprised of lines of the form `timestamp, animal_name, expected_chamber`.",
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
        "--bin_seconds",
        type=int,
        help="Bin size, in seconds, for time-series outputs.  Default: 300",
        default=300
    )
    # parser.add_argument(
    #     "--habitat_time_offset_seconds",
    #     type=int,
    #     help="Seconds after the first tag read when the 'time in habitat' clock "
    #     "is considered to begin, for purposes of activity time series "
    #     "reporting.  Default: 600",
    #     default=600
    # )
    parser.add_argument(
        "--timezone",
        default="US/Pacific",
        help="Olcus logs timestamps in the local timezone, but does not record "
        "which timezone that is.  Thus, we allow specifying the timezone in "
        "which the Olcus logs should be interpreted.  This makes no difference "
        "to the current analyses, which are all just about durations anyway, "
        "not about absolute time.  Defaults to 'US/Pacific'.  Other options "
        "are listed at "
        "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones."
        )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--dwell_threshold",
        type=float,
        default=DEFAULT_TIME_BETWEEN_READS_THRESHOLD,
        help="Time in seconds between reads to switch from short dwell (tube) to long dwell (cage/arena). Default: {}".format(DEFAULT_TIME_BETWEEN_READS_THRESHOLD)
    )
    return parser.parse_args()


def _find_file(directory: str, exact_name: str, suffix: str) -> str | None:
    """Find a single file in directory matching exact_name or ending with suffix (case-insensitive).
    
    Returns: path to file, or None if not found.
    Raises: ValueError if multiple files found.
    """
    matches = []
    
    exact_lower = exact_name.lower()
    suffix_lower = suffix.lower()

    if not os.path.exists(directory):
        return None

    for filename in os.listdir(directory):
        f_lower = filename.lower()
        if f_lower == exact_lower or f_lower.endswith(suffix_lower):
            matches.append(filename)
    
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return os.path.join(directory, matches[0])
    
    raise ValueError(f"Ambiguous file match. Found multiple files matching '{exact_name}' or '*{suffix}': {matches}")


def _parse_config(args, timezone) -> tuple[Config, list[Validation], str]:
    # Look for animals.csv or *_animals.csv
    configFile = _find_file(args.olcus_dir, "animals.csv", "_animals.csv")
    if not configFile:
        raise ValueError("Could not find exactly one `*_animals.csv` or `animals.csv` file.")
    
    config = parse_config(configFile)

    validations: list[Validation] = []
    # Look for validation.csv or *_validation.csv
    try:
        validationFile = _find_file(args.olcus_dir, "validation.csv", "_validation.csv")
        if validationFile:
            logging.info(f"Found validation file: {validationFile}")
            validations = parse_validation(
                validationFile, {v: k for (k, v) in config.tag_id_to_name.items()}, timezone
            )
    except ValueError as e:
        logging.warning(f"Validation skipped: {e}")


    olcusDir = os.path.normpath(args.olcus_dir)

    return (config, validations, olcusDir)


def main(argv):
    """Analyze a 'raw' file describing Olcus antenna data from a Beery Lab
    vole group-living RFID apparatus.  Infers co-habitation bouts and total
    co-hab duration for each pair of animals."""
    args = _parse_args(argv)
    
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='%(message)s')

    logging.info("===================================")
    logging.info("Voletron v2.1, 2026-01-01")
    logging.info("http://github.com/beerylab/voletron")
    logging.info("===================================")


    timezone : datetime.tzinfo = pytz.timezone(args.timezone)

    ### Read input config and validation files
    apparatusFile = _find_file(args.olcus_dir, "apparatus.json", "_apparatus.json")
    if not apparatusFile:
        raise FileNotFoundError(f"Could not find apparatus config file (apparatus.json or *_apparatus.json) in {args.olcus_dir}")
    
    load_apparatus_config(apparatusFile)
    config, validations, olcusDir = _parse_config(args, timezone)
    
    ### Read raw data
    reads_per_animal, first_read_time, analysis_start_time, analysis_end_time, last_read_time = _load_and_validate_data(args, config, olcusDir, timezone)
    
    ### Infer animal trajectories from antenna reads
    trajectories = _build_trajectories(first_read_time, config, reads_per_animal, args.dwell_threshold)
    
    # Simulate state forwards, accumulating stats in the state object
    # and write it out along the way
    state = CoDwellAccumulator(first_read_time, config.tag_id_to_start_chamber, all_chambers)
    for t in trajectories.traversals():
        state.update_state_from_traversal(t)
    co_dwells = state.end(analysis_end_time)
    

    write_outputs(
        olcusDir,
        config,
        trajectories,
        co_dwells,
        # analyzer,
        # first_read_time,
        # last_read_time,
        analysis_start_time,
        analysis_end_time,
        validations,
        len(validations) > 0,
        args.bin_seconds,
        # args.habitat_time_offset_seconds,
    )


def _load_and_validate_data(args, config, olcusDir, timezone):
    """Load raw data, handle preprocessing, and determine time intervals."""
    logging.info("\nReading Data:")
    logging.info("-----------------------------")
    reads = parse_raw_dir(olcusDir, timezone)
    
    # The first read may require inserting a missing read before it;
    # start the experiment 5 ms earlier to account for this.
    first_read_time: TimestampSeconds = TimestampSeconds(parse_first_read(args.olcus_dir, timezone).timestamp - 0.005)
    analysis_start_time = _get_analysis_start_time(args, timezone, first_read_time)
    
    ### Initial cleanup of the reads, per animal
    reads_per_animal = preprocess_reads(reads, config.tag_id_to_start_chamber.keys(), config.tag_id_to_name)
    
    _warn_unobserved_animals(reads_per_animal)
    
    last_read_time = max([vv[-1].timestamp for vv in reads_per_animal.values()])
    analysis_end_time = _get_analysis_end_time(args, timezone, last_read_time)
    
    _print_time_intervals(first_read_time, analysis_start_time, analysis_end_time, last_read_time)
    
    return reads_per_animal, first_read_time, analysis_start_time, analysis_end_time, last_read_time


def _get_analysis_start_time(args, timezone, first_read_time):
    if args.start != None:
        return TimestampSeconds(timezone.localize(datetime.datetime.strptime(
            args.start, "%d.%m.%Y %H:%M:%S:%f"
        )).timestamp())
    return first_read_time


def _get_analysis_end_time(args, timezone, last_read_time):
    if args.end != None:
        return TimestampSeconds(timezone.localize(datetime.datetime.strptime(
            args.end, "%d.%m.%Y %H:%M:%S:%f"
        )).timestamp())
    return last_read_time


def _warn_unobserved_animals(reads_per_animal):
    unobserved_animals = [kk for (kk, vv) in reads_per_animal.items() if len(vv) == 0]
    if unobserved_animals:
        logging.warning("\n-----------------------------")
        logging.warning("WARNING: Animals in config but not observed:")
        logging.warning(unobserved_animals)
        logging.warning("----------------------------\n")


def _print_time_intervals(first_read_time, analysis_start_time, analysis_end_time, last_read_time):
    logging.info("\nIntervals:")
    logging.info("-----------------------------")
    logging.info("Experiment Start (first read): {}".format(format_time(first_read_time)))
    logging.info("               Analysis Start: {}".format(format_time(analysis_start_time)))
    logging.info("                 Analysis End: {}".format(format_time(analysis_end_time)))
    logging.info("   Experiment End (last read): {}".format(format_time(last_read_time)))


def _build_trajectories(first_read_time: TimestampSeconds, config: Config, reads_per_animal: Dict[TagID, list[Read]], dwell_threshold: float) -> AllAnimalTrajectories:
    """Build animal trajectories from preprocessed reads."""
    all_animal_trajectories = AllAnimalTrajectories(
        first_read_time, config.tag_id_to_start_chamber, reads_per_animal, dwell_threshold
    )

    logging.info("\nRead Interpretations:")
    logging.info("-----------------------------")
    for [key, value] in all_animal_trajectories.fate_percent.items():
        logging.info("{:>10}: {}".format(key, value))
        
    return all_animal_trajectories


if __name__ == "__main__":
    main(sys.argv)

