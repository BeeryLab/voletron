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
import time
import logging
from typing import List, Tuple
from voletron.trajectory import AllAnimalTrajectories
from voletron.types import ChamberName, AnimalConfig, TagID, TimestampSeconds, DurationSeconds
from voletron.output.types import ChamberTimeRow, OutputBin

def compute_chamber_times(
    config: AnimalConfig,
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
    bins: List[OutputBin],
) -> List[ChamberTimeRow]:
    t0 = time.perf_counter()
    rows = []
    
    # Maintain next start index for each animal to avoid re-scanning dwells
    next_start_indices: Dict[TagID, int] = {tag_id: 0 for tag_id in tag_ids}

    for bin in bins:
        b_start = bin.bin_start
        b_end = bin.bin_end
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            if tag_id not in next_start_indices:
                continue
            
            ct, last_idx = trajectory.time_per_chamber(b_start, b_end, start_idx=next_start_indices[tag_id])
            next_start_indices[tag_id] = last_idx
            
            rows.append(ChamberTimeRow(
                bin_number=bin.bin_number,
                bin_start=b_start,
                bin_end=b_end,
                bin_duration=b_end - b_start,
                animal_name=config.tag_id_to_name[tag_id],
                chamber_times=ct,
                total_time=sum(ct.values())
            ))
    logging.debug(f"PROFILING: compute_chamber_times took {time.perf_counter() - t0:.3f} seconds")
    return rows

def write_chamber_times(
    rows: List[ChamberTimeRow],
    chambers: List[ChamberName],
    out_dir: str,
    exp_name: str,
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,animal," + ",".join(chambers) + ",total\n")
        for row in rows:
            aaa = ",".join(map(lambda c: "{:.0f}".format(row.chamber_times.get(c, 0.0)), chambers))
            f.write(
                "{},{:.0f},{:.0f},{:.0f},{},{},{:.0f}\n".format(
                    row.bin_number, row.bin_start, row.bin_end, row.bin_duration, row.animal_name, aaa, row.total_time
                )
            )
