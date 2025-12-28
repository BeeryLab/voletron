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
from voletron.types import Config, TagID
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.output.types import LongDwellRow

def compute_long_dwells(
    config: Config,
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
) -> List[LongDwellRow]:
    rows = []
    for (tag_id, trajectory) in trajectories.animalTrajectories.items():
        if not tag_id in tag_ids:
            continue
        for d in trajectory.long_dwells():
            rows.append(LongDwellRow(
                animal_name=config.tag_id_to_name[d[0]],
                chamber_name=d[1],
                start_time=d[2],
                duration_seconds=d[3]
            ))
    return rows

def write_long_dwells(
    rows: List[LongDwellRow],
    out_dir: str,
    exp_name: str,
):
    with open(os.path.join(out_dir, exp_name + ".longdwells.csv"), "w") as f:
        f.write("animal,chamber,start_time,seconds\n")
        for row in rows:
            f.write(
                "{},{},{},{:.0f}\n".format(
                    row.animal_name, row.chamber_name, format_time(row.start_time), row.duration_seconds
                )
            )
