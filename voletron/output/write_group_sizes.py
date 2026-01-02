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
from collections import defaultdict
from typing import List, Dict, Union

from voletron.types import AnimalName, DurationSeconds, TagID, TimestampSeconds
from voletron.output.types import GroupSizeRow, OutputBin

def compute_group_sizes(
    tag_ids: List[TagID],
    tag_id_to_name: Dict[TagID, AnimalName],
    bins: List[OutputBin],
) -> List[GroupSizeRow]:
    t0 = time.perf_counter()
    rows = []
    
    for bin in bins:
        if bin.analyzer is None:
            continue
        analyzer = bin.analyzer
        start = bin.bin_start
        end = bin.bin_end
        
        # Tracks time spent by each animal in groups of various sizes.
        # Key: TagID, Value: List of durations where index is group size (e.g. index 2 is time spent in a pair).
        # Obviously, the value for index 0 is always 0.
        tag_id_group_size_seconds : Dict[TagID, List[DurationSeconds]] = defaultdict(lambda: [DurationSeconds(0)] * 9)

        for group_dwell in analyzer.get_group_chamber_exclusive_durations():
            for tag_id in group_dwell.tag_ids:
                if tag_id in tag_ids:
                    tag_id_group_size_seconds[tag_id][
                        len(group_dwell.tag_ids)
                    ] = DurationSeconds(tag_id_group_size_seconds[tag_id][
                        len(group_dwell.tag_ids)
                    ] + group_dwell.duration_seconds)

        for (tag_id, group_size_seconds) in tag_id_group_size_seconds.items():
            if analyzer.duration == 0:
                avg_group_size = 0.0
            else:
                # Average size of the group this animal belongs to.
                # Weighted sum: (group size * duration at that size) / total duration
                avg_group_size = (
                    sum(size * secs for size, secs in enumerate(group_size_seconds)) 
                    / analyzer.duration
                )
           
            # Total time when an animal was not alone (group size >= 2)
            total_nosolo_seconds = sum(group_size_seconds[2:])
            # If the animal was always alone, then the average not-alone group size is undefined.
            if total_nosolo_seconds == 0:
                avg_group_size_nosolo = "N/A"
            else:
                # Average group size when excluding solo time
                avg_group_size_nosolo = (
                    sum(size * secs for size, secs in enumerate(group_size_seconds[2:], start=2))
                    / total_nosolo_seconds
                )
            
            size_secs_dict = {i: group_size_seconds[i] for i in range(len(group_size_seconds))}

            rows.append(GroupSizeRow(
                bin_number=bin.bin_number,
                bin_start=start,
                bin_end=end,
                bin_duration=analyzer.duration,
                animal_name=tag_id_to_name[tag_id],
                size_seconds=size_secs_dict,
                avg_group_size=avg_group_size,
                avg_group_size_nosolo=avg_group_size_nosolo,
            ))
    logging.debug(f"PROFILING: compute_group_sizes took {time.perf_counter() - t0:.3f} seconds")
    return rows

def write_group_sizes(
    rows: List[GroupSizeRow],
    out_dir: str,
    exp_name: str,
):
    group_sizes = range(0, 9)

    with open(os.path.join(out_dir, exp_name + ".group_size.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,animal,1,2,3,4,5,6,7,8,avg_group_size,avg_group_size_nosolo\n")
        # Sort rows to ensure deterministic output order
        rows.sort(key=lambda r: (r.bin_number, r.animal_name))
        for row in rows:
            aaa = ",".join(map(lambda a: "{:.0f}".format(row.size_seconds.get(a, 0.0)), group_sizes[1:]))
            
            avg_group_size_nosolo_str = (
                row.avg_group_size_nosolo
                if isinstance(row.avg_group_size_nosolo, str)
                else "{:.2f}".format(row.avg_group_size_nosolo)
            )

            f.write(
                "{},{:.0f},{:.0f},{:.0f},{},{},{:.2f},{}\n".format(
                    row.bin_number,
                    row.bin_start,
                    row.bin_end,
                    row.bin_duration,
                    row.animal_name,
                    aaa,
                    row.avg_group_size,
                    avg_group_size_nosolo_str,
                )
            )
