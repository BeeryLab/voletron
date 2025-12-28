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
from typing import List, Dict, Set
from voletron.types import AnimalName, TagID, Validation
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.output.types import ValidationRow

def compute_validation(
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
    tag_id_to_name: Dict[TagID, AnimalName],
    validations: List[Validation],
) -> List[ValidationRow]:
    rows = []
    relevant_validations = [vv for vv in validations if vv.tag_id in tag_ids]
    
    for v in relevant_validations:
        # Charitably use a 2-minute window
        actual = trajectories.get_locations_between(
            v.tag_id, v.timestamp - 30, v.timestamp + 90
        )
        ok = v.chamber in actual
        
        rows.append(ValidationRow(
            correct=ok,
            timestamp=v.timestamp,
            animal_name=tag_id_to_name[v.tag_id],
            expected_chamber=v.chamber,
            observed_chambers=actual
        ))
    return rows

def write_validation(rows: List[ValidationRow], out_dir: str, exp_name: str) -> None:
    print("\nValidation:")
    print("-----------------------------")

    # Calculate correctness for printing
    if rows:
        correct_count = sum(1 for row in rows if row.correct)
        total_count = len(rows)
        percentage = correct_count / total_count
    else:
        correct_count = 0
        total_count = 0
        percentage = 0.0

    with open(os.path.join(out_dir, exp_name + ".validate.csv"), "w") as f:
        f.write("Correct,Timestamp,AnimalID,Expected,Observed\n")
        
        for row in rows:
            f.write("{},{},{},{},{}\n".format(
                row.correct,
                format_time(row.timestamp),
                row.animal_name,
                row.expected_chamber,
                row.observed_chambers
            ))

    if total_count > 0:
        print(
            "{} of {} ({:>6.2%}) validation points correct.".format(
                correct_count, total_count, percentage
            )
        )

