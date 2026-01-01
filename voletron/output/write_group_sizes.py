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
from collections import defaultdict
from typing import List, Dict, Union, Tuple
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import AnimalName, DurationSeconds, TagID, CoDwell, TimestampSeconds
from voletron.output.types import GroupSizeRow

def compute_group_sizes(
    tag_ids: List[TagID],
    co_dwells: List[CoDwell],
    tag_id_to_name: Dict[TagID, AnimalName],
    bins: List[Tuple[TimestampSeconds, TimestampSeconds]],
) -> List[GroupSizeRow]:
    rows = []
    
    for (start, end) in bins:
        analyzer = TimeSpanAnalyzer(co_dwells, start, end)
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
                sum_pair_time = 0.0
            else:
                avg_group_size = (
                    sum(
                        [
                            group_size * seconds
                            for (group_size, seconds) in enumerate(group_size_seconds)
                        ]
                    )
                    / analyzer.duration
                )
                
                sum_pair_time = (
                    sum(
                        [
                            (group_size_minus_two + 1) * seconds
                            for (group_size_minus_two, seconds) in enumerate(
                                group_size_seconds[2:]
                            )
                        ]
                    )
                    / analyzer.duration
                )
            
            # Total time when an animal was not alone
            total_nosolo_seconds = sum(group_size_seconds[2:])
            # If the animal was always alone, then the average not-alone group size is undefined.
            if total_nosolo_seconds == 0:
                avg_group_size_nosolo = "N/A"
            else:
                avg_group_size_nosolo = (
                    sum(
                        [
                            (group_size_minus_two + 2) * seconds
                            for (group_size_minus_two, seconds) in enumerate(
                                group_size_seconds[2:]
                            )
                        ]
                    )
                    / total_nosolo_seconds
                )

            
            size_secs_dict = {i: group_size_seconds[i] for i in range(len(group_size_seconds))}

            rows.append(GroupSizeRow(
                bin_start=start,
                bin_end=end,
                animal_name=tag_id_to_name[tag_id],
                size_seconds=size_secs_dict,
                avg_group_size=avg_group_size,
                avg_group_size_nosolo=avg_group_size_nosolo,
                sum_pair_time=sum_pair_time,
                bin_duration=analyzer.duration
            ))
    return rows

def write_group_sizes(
    rows: List[GroupSizeRow],
    out_dir: str,
    exp_name: str,
):
    group_sizes = range(0, 9)

    with open(os.path.join(out_dir, exp_name + ".group_size.csv"), "w") as f:
        f.write("bin_start,bin_end,animal,1,2,3,4,5,6,7,8,avg_group_size,avg_group_size_nosolo,sum_pair_time,bin_duration\n")
        for row in rows:
            aaa = ",".join(map(lambda a: "{:.0f}".format(row.size_seconds.get(a, 0.0)), group_sizes[1:]))
            
            avg_group_size_nosolo_str = (
                row.avg_group_size_nosolo
                if isinstance(row.avg_group_size_nosolo, str)
                else "{:.2f}".format(row.avg_group_size_nosolo)
            )

            f.write(
                "{},{},{},{},{:.2f},{},{:.4f},{:.0f}\n".format(
                    row.bin_start,
                    row.bin_end,
                    row.animal_name,
                    aaa,
                    row.avg_group_size,
                    avg_group_size_nosolo_str,
                    row.sum_pair_time,
                    row.bin_duration,
                )
            )
