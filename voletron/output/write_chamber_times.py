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
import math
from typing import List, Tuple
from voletron.trajectory import AllAnimalTrajectories
from voletron.types import ChamberName, Config, TagID, TimestampSeconds, DurationSeconds
from voletron.output.types import ChamberTimeRow, OutputBin

def compute_chamber_times(
    config: Config,
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
    bins: List[OutputBin],
) -> List[ChamberTimeRow]:
    rows = []
    
    for bin in bins:
        b_start = bin.start
        b_end = bin.end
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            if not tag_id in tag_ids:
                continue
            ct = trajectory.time_per_chamber(b_start, b_end)
            rows.append(ChamberTimeRow(
                bin_start=b_start,
                bin_end=b_end,
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
        f.write("bin_start,bin_end,animal," + ",".join(chambers) + ",total\n")
        for row in rows:
            aaa = ",".join(map(lambda c: "{:.0f}".format(row.chamber_times.get(c, 0.0)), chambers))
            f.write(
                "{},{},{},{},{:.0f}\n".format(
                    row.bin_start, row.bin_end, row.animal_name, aaa, row.total_time
                )
            )
