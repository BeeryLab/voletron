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
from voletron.types import AnimalConfig, DurationSeconds, TagID, CHAMBER_ERROR
from voletron.output.types import PairCohabRow, OutputBin

def compute_pair_inclusive_cohabs(
    config: AnimalConfig,
    tag_ids: List[TagID],
    bins: List[OutputBin],
) -> List[PairCohabRow]:
    t0 = time.perf_counter()
    rows = []
    
    tag_id_set = set(tag_ids)
    
    # Pre-calculate all valid pairs for this habitat
    all_pairs = []
    sorted_tag_ids = sorted(tag_ids)
    for i in range(len(sorted_tag_ids)):
        for j in range(i + 1, len(sorted_tag_ids)):
            all_pairs.append((sorted_tag_ids[i], sorted_tag_ids[j]))

    for bin in bins:
        if bin.analyzer is None:
             continue
        analyzer = bin.analyzer
        start = bin.bin_start
        end = bin.bin_end
        
        # Map pair -> aggregate
        stats_map = {}
        for agg in analyzer.get_pair_inclusive_stats():
            # agg.tag_ids is a list [tag_a, tag_b]
            pair_key = tuple(sorted(agg.tag_ids))
            stats_map[pair_key] = agg
            
        for (animal_a, animal_b) in all_pairs:
            pair_key = (animal_a, animal_b)
            
            if pair_key in stats_map:
                agg = stats_map[pair_key]
                count = agg.count
                duration = agg.duration_seconds
            else:
                count = 0
                duration = DurationSeconds(0)

            rows.append(PairCohabRow(
                bin_number=bin.bin_number,
                bin_start=start,
                bin_end=end,
                bin_duration=analyzer.duration,
                animal_a_name=config.tag_id_to_name[animal_a],
                animal_b_name=config.tag_id_to_name[animal_b],
                dwell_count=count,
                duration_seconds=duration,
            ))


        # Add Unknown/Error rows
        # For each animal, calculate total time in CHAMBER_ERROR
        # A group dwell in ERROR contributes to this.
        # We assume "solo in Error" or "group in Error" all counts as "Unknown location time".
        
        tag_id_error_stats = {tid: {"count": 0, "duration": 0.0} for tid in tag_ids}
        
        for g in analyzer.get_group_chamber_exclusive_durations():
             if g.chamber == CHAMBER_ERROR:
                 for tid in g.tag_ids:
                     if tid in tag_id_error_stats:
                         tag_id_error_stats[tid]["count"] += g.count
                         tag_id_error_stats[tid]["duration"] += g.duration_seconds

        for tag_id in sorted_tag_ids:
             stat = tag_id_error_stats[tag_id]
             
             # Only include if there is actual error time, to reduce clutter.
             if stat["duration"] == 0 and stat["count"] == 0:
                 continue
             
             rows.append(PairCohabRow(
                bin_number=bin.bin_number,
                bin_start=start,
                bin_end=end,
                bin_duration=analyzer.duration,
                animal_a_name=config.tag_id_to_name[tag_id],
                animal_b_name="UNKNOWN",
                dwell_count=stat["count"],
                duration_seconds=DurationSeconds(stat["duration"]),
            ))
            
    logging.debug(f"PROFILING: compute_pair_inclusive_cohabs took {time.perf_counter() - t0:.3f} seconds")
    return rows

def write_pair_inclusive_cohabs(
    rows: List[PairCohabRow], out_dir: str, exp_name: str
):
    with open(os.path.join(out_dir, exp_name + ".pair-inclusive.cohab.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,Animal A,Animal B,dwells,seconds\n")
        for row in rows:
            f.write(
                "{},{:.0f},{:.0f},{:.0f},{},{},{},{:.0f}\n".format(
                    row.bin_number,
                    row.bin_start,
                    row.bin_end,
                    row.bin_duration,
                    row.animal_a_name,
                    row.animal_b_name,
                    row.dwell_count,
                    row.duration_seconds,
                )
            )
