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
from voletron.trajectory import AllAnimalTrajectories
from voletron.types import ChamberName, Config, TagID, TimestampSeconds
from voletron.output.types import ChamberTimeRow

def compute_chamber_times(
    config: Config,
    tag_ids: List[TagID],
    chambers: List[ChamberName],
    trajectories: AllAnimalTrajectories,
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
) -> List[ChamberTimeRow]:
    rows = []
    for (tag_id, trajectory) in trajectories.animalTrajectories.items():
        if not tag_id in tag_ids:
            continue
        ct = trajectory.time_per_chamber(analysis_start_time, analysis_end_time)
        rows.append(ChamberTimeRow(
            animal_name=config.tag_id_to_name[tag_id],
            chamber_times=ct,
            total_time=sum(ct.values())
        ))
    return rows

def write_chamber_times(
    rows: List[ChamberTimeRow],
    chambers: List[ChamberName],
    out_dir: str,
    exp_name: str,
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("animal," + ",".join(chambers) + ",total\n")
        for row in rows:
            aaa = ",".join(map(lambda c: "{:.0f}".format(row.chamber_times[c]), chambers))
            f.write(
                "{},{},{:.0f}\n".format(
                    row.animal_name, aaa, row.total_time
                )
            )
