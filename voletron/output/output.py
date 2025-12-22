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
from voletron.output.write_validation import write_validation
from voletron.types import Config, CoDwell, DurationSeconds, TimestampSeconds, Validation
from voletron.trajectory import AllAnimalTrajectories
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.output.write_chamber_times import write_chamber_times
from voletron.output.write_long_dwells import write_long_dwells
from voletron.output.write_activity import write_activity
from voletron.output.write_pair_inclusive_cohabs import write_pair_inclusive_cohabs
from voletron.output.write_group_chamber_cohabs import write_group_chamber_cohabs
from voletron.output.write_group_sizes import write_group_sizes

def write_outputs(
    olcusDir: str,
    config: Config,
    trajectories: AllAnimalTrajectories,
    co_dwells: List[CoDwell],
    analyzer: TimeSpanAnalyzer,
    first_read_time: TimestampSeconds,
    last_read_time: TimestampSeconds,
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
    validations: List[Validation],
    validation: bool,
    bin_seconds: DurationSeconds,
    habitat_time_offset_seconds: DurationSeconds,
):
    """Write all output files organized by apparatus."""
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

        if validation:
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
            bin_seconds,
        )
        
        write_activity(
            out_dir,
            exp_name,
            "habitat_time",
            trajectories,
            co_dwells,
            TimestampSeconds(first_read_time + habitat_time_offset_seconds),
            last_read_time,
            bin_seconds,
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

