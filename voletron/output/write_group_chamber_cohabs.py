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
from typing import List, Dict

from voletron.types import AnimalName, TagID, TimestampSeconds, DurationSeconds
from voletron.output.types import GroupChamberCohabRow, OutputBin

def compute_group_chamber_cohabs(
    tag_ids: List[TagID],
    tag_id_to_name: Dict[TagID, AnimalName],
    bins: List[OutputBin],
) -> List[GroupChamberCohabRow]:
    t0 = time.perf_counter()
    rows = []
    
    for bin in bins:
        if bin.analyzer is None:
            continue
        analyzer = bin.analyzer
        start = bin.bin_start
        end = bin.bin_end
        for group_dwell_aggregate in analyzer.get_group_chamber_exclusive_durations():
            # Skip groups with tag_ids not in the requested list
            if not all(tag_id in tag_ids for tag_id in group_dwell_aggregate.tag_ids):
                continue

            names = sorted(tag_id_to_name[tag_id] for tag_id in group_dwell_aggregate.tag_ids)
            rows.append(GroupChamberCohabRow(
                bin_number=bin.bin_number,
                bin_start=start,
                bin_end=end,
                bin_duration=analyzer.duration,
                animal_names=names,
                chamber_name=group_dwell_aggregate.chamber,
                dwell_count=group_dwell_aggregate.count,
                duration_seconds=group_dwell_aggregate.duration_seconds,
            ))
    logging.debug(f"PROFILING: compute_group_chamber_cohabs took {time.perf_counter() - t0:.3f} seconds")
    return rows

def write_group_chamber_cohabs(
    rows: List[GroupChamberCohabRow],
    out_dir: str,
    exp_name: str,
):
    with open(os.path.join(out_dir, exp_name + ".group_chamber_cohab.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,animals,chamber,dwells,seconds\n")
        for row in rows:
            f.write(
                "{},{:.0f},{:.0f},{:.0f},{},{},{},{:.0f}\n".format(
                    row.bin_number,
                    row.bin_start,
                    row.bin_end,
                    row.bin_duration,
                    " ".join(row.animal_names),
                    row.chamber_name,
                    row.dwell_count,
                    row.duration_seconds,
                )
            )
