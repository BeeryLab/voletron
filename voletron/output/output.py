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


import os
from typing import List
from voletron.apparatus_config import apparatus_chambers
from voletron.output.write_validation import write_validation, compute_validation
from voletron.types import AnimalConfig, CoDwell, DurationSeconds, TimestampSeconds, Validation
from voletron.output.types import OutputBin
from voletron.trajectory import AllAnimalTrajectories
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.output.write_chamber_times import write_chamber_times, compute_chamber_times
from voletron.output.write_long_dwells import write_long_dwells, compute_long_dwells
# from voletron.output.write_activity import write_activity, compute_activity
from voletron.output.write_pair_inclusive_cohabs import write_pair_inclusive_cohabs, compute_pair_inclusive_cohabs
from voletron.output.write_group_chamber_cohabs import write_group_chamber_cohabs, compute_group_chamber_cohabs
from voletron.output.write_group_sizes import write_group_sizes, compute_group_sizes

def write_outputs(
    olcusDir: str,
    config: AnimalConfig,
    trajectories: AllAnimalTrajectories,
    co_dwells: List[CoDwell],
    # first_read_time: TimestampSeconds,
    # last_read_time: TimestampSeconds,
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
    validations: List[Validation],
    validation: bool,
    bin_seconds: DurationSeconds,
    # habitat_time_offset_seconds: DurationSeconds,
):
    """Write all output files organized by apparatus."""
    exp_name = str(os.path.basename(olcusDir))
    
    # Create bins
    bins: List[OutputBin] = []

    # Add whole experiment bin
    full_analyzer = TimeSpanAnalyzer(co_dwells, analysis_start_time, analysis_end_time)
    bins.append(OutputBin(
        bin_number=0,
        bin_start=analysis_start_time, 
        bin_end=analysis_end_time, 
        analyzer=full_analyzer
    ))

    current_start = analysis_start_time
    bin_counter = 1
    while current_start < analysis_end_time:
        current_end = min(TimestampSeconds(current_start + bin_seconds), analysis_end_time)
        bin_analyzer = TimeSpanAnalyzer(co_dwells, TimestampSeconds(current_start), TimestampSeconds(current_end))
        bins.append(OutputBin(
            bin_number=bin_counter,
            bin_start=TimestampSeconds(current_start), 
            bin_end=TimestampSeconds(current_end),
            analyzer=bin_analyzer
        ))
        current_start = TimestampSeconds(current_start + bin_seconds)
        bin_counter += 1

    for (desired_start_chamber, chambers) in apparatus_chambers.items():

        # Filter animals by apparatus
        tag_ids = [
            tag_id
            for (tag_id, start_chamber) in config.tag_id_to_start_chamber.items()
            if start_chamber in chambers
        ]

        out_dir = os.path.join(olcusDir, "voletron", desired_start_chamber)
        os.makedirs(out_dir, exist_ok=True)

        # Trajectory-based outputs

        if validation:
            # Validation
            validation_rows = compute_validation(
                tag_ids, 
                trajectories, 
                config.tag_id_to_name, 
                validations, 
                bins
            )
            write_validation(validation_rows, out_dir, exp_name, desired_start_chamber)

        chamber_time_rows = compute_chamber_times(
            config, 
            tag_ids, 
            trajectories, 
            bins
        )
        write_chamber_times(chamber_time_rows, chambers, out_dir, exp_name)

        long_dwell_rows = compute_long_dwells(
            config, 
            tag_ids, 
            trajectories, 
            bins
        )
        write_long_dwells(long_dwell_rows, out_dir, exp_name)


        # TimeSpanAnalyzer-based outputs

        pair_cohab_rows = compute_pair_inclusive_cohabs(
            config, 
            tag_ids,
            bins
        )
        write_pair_inclusive_cohabs(
            pair_cohab_rows,
            out_dir,
            exp_name,
        )

        group_chamber_rows = compute_group_chamber_cohabs(
            tag_ids, 
            config.tag_id_to_name, 
            bins
        )
        write_group_chamber_cohabs(
            group_chamber_rows,
            out_dir,
            exp_name,
        )

        group_size_rows = compute_group_sizes(
            tag_ids, 
            config.tag_id_to_name, 
            bins
        )
        write_group_sizes(
            group_size_rows,
            out_dir,
            exp_name,
        )

