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
import logging
import time
from typing import List, Dict, Set, Tuple
from voletron.types import AnimalName, TagID, Validation, TimestampSeconds, DurationSeconds, HabitatName
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.output.types import ValidationRow, OutputBin

def compute_validation(
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
    tag_id_to_name: Dict[TagID, AnimalName],
    validations: List[Validation],
    bins: List[OutputBin],
) -> List[ValidationRow]:
    t0 = time.perf_counter()
    rows = []
    relevant_validations = [vv for vv in validations if vv.tag_id in tag_ids]
    
    if not bins:
        return []
        
    bin = bins[0]
    b_start = bin.bin_start
    b_end = bin.bin_end
    for v in relevant_validations:
        if v.timestamp >= b_start and v.timestamp < b_end:
            # Charitably use a 2-minute window.
            trajectory = trajectories.animalTrajectories[v.tag_id]
            actual = trajectory.get_locations_between(
                v.timestamp - 30, v.timestamp + 90
            )
            
            ok = v.chamber in actual
            
            rows.append(ValidationRow(
                bin_number=bin.bin_number,
                bin_start=b_start,
                bin_end=b_end,
                bin_duration=b_end - b_start,
                correct=ok,
                timestamp=v.timestamp,
                animal_name=tag_id_to_name[v.tag_id],
                expected_chamber=v.chamber,
                observed_chambers=actual
            ))

    logging.debug(f"PROFILING: compute_validation took {time.perf_counter() - t0:.3f} seconds")
    return rows

def write_validation(rows: List[ValidationRow], out_dir: str, exp_name: str, habitat_name: HabitatName) -> None:
    logging.info(f"\nValidation ({habitat_name}):")
    logging.info("-----------------------------")

    if rows:
        correct_count = sum(1 for row in rows if row.correct)
        total_count = len(rows)
        percentage = correct_count / total_count
    else:
        correct_count = 0
        total_count = 0
        percentage = 0.0

    with open(os.path.join(out_dir, exp_name + ".validate.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,Correct,Timestamp,AnimalName,Expected,Observed\n")
        
        for row in rows:
            f.write("{},{:.0f},{:.0f},{:.0f},{},{},{},{},{}\n".format(
                row.bin_number,
                row.bin_start,
                row.bin_end,
                row.bin_duration,
                row.correct,
                format_time(row.timestamp),
                row.animal_name,
                row.expected_chamber,
                row.observed_chambers
            ))

    if total_count > 0:
        logging.info(
            "{} of {} ({:>6.2%}) validation points correct (across all bins).".format(
                correct_count, total_count, percentage
            )
        )

