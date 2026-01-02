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
from typing import List, Tuple
from voletron.types import AnimalName, ChamberName, AnimalConfig, DurationMinutes, LongDwell, TagID, TimestampSeconds, DurationSeconds
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time
from voletron.output.types import LongDwellRow, OutputBin


def compute_long_dwells(
    config: AnimalConfig,
    tag_ids: List[TagID],
    trajectories: AllAnimalTrajectories,
    bins: List[OutputBin],
) -> List[LongDwellRow]:
    rows = []
    
    # Pre-fetch all long dwells for relevant tags
    all_dwells = []
    for (tag_id, trajectory) in trajectories.animalTrajectories.items():
        if not tag_id in tag_ids:
            continue
        for d in trajectory.long_dwells():
            # d is (tag_id_str, chamber_name, start_time, duration)
            # trajectory.long_dwells() returns tuple with tag_id as first element? 
            # Let's check previous code: `config.tag_id_to_name[d[0]]`. Yes.
            all_dwells.append(d)

    for bin in bins:
        b_start = bin.bin_start
        b_end = bin.bin_end
        for d in all_dwells:
            # d: (tag_id, chamber, start_time, duration)
            start_time = d[2]
            
            # Check if dwell starts within this bin
            # For the 'whole experiment' bin, we include everything within analysis range?
            # Or just everything?
            # Let's strictly respect analysis range for all bins including the whole one.
            # But wait, if a dwell is outside analysis range, should it be reported?
            # Assuming logic: dwell must start >= b_start and < b_end
            
            if start_time >= b_start and start_time < b_end:
                rows.append(LongDwellRow(
                    bin_number=bin.bin_number,
                    bin_start=b_start,
                    bin_end=b_end,
                    bin_duration=b_end - b_start,
                    animal_name=config.tag_id_to_name[d[0]],
                    chamber_name=d[1],
                    start_time=start_time,
                    duration_seconds=d[3]
                ))
    return rows

def write_long_dwells(
    rows: List[LongDwellRow],
    out_dir: str,
    exp_name: str,
):
    with open(os.path.join(out_dir, exp_name + ".longdwells.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,animal,chamber,start_time,seconds\n")
        for row in rows:
            f.write(
                "{},{:.0f},{:.0f},{:.0f},{},{},{},{:.0f}\n".format(
                    row.bin_number, row.bin_start, row.bin_end, row.bin_duration, row.animal_name, row.chamber_name, format_time(row.start_time), row.duration_seconds
                )
            )
