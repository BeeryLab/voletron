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
from voletron.types import Config, TimestampSeconds, DurationSeconds
from voletron.output.types import PairCohabRow, OutputBin

def compute_pair_inclusive_cohabs(
    config: Config,
    bins: List[OutputBin],
) -> List[PairCohabRow]:
    rows = []
    
    for bin in bins:
        if bin.analyzer is None:
             continue
        analyzer = bin.analyzer
        start = bin.bin_start
        end = bin.bin_end
        
        for pair_dwell_aggregate in analyzer.get_pair_inclusive_stats():
            animal_a, animal_b = pair_dwell_aggregate.tag_ids
            rows.append(PairCohabRow(
                bin_number=bin.bin_number,
                bin_start=start,
                bin_end=end,
                bin_duration=analyzer.duration,
                animal_a_name=config.tag_id_to_name[animal_a],
                animal_b_name=config.tag_id_to_name[animal_b],
                dwell_count=pair_dwell_aggregate.count,
                duration_seconds=pair_dwell_aggregate.duration_seconds,
            ))
    return rows

def write_pair_inclusive_cohabs(
    rows: List[PairCohabRow], out_dir: str, exp_name: str
):
    with open(os.path.join(out_dir, exp_name + ".pair-inclusive.cohab.csv"), "w") as f:
        f.write("bin_number,bin_start,bin_end,bin_duration,Animal A,Animal B,dwells,seconds\n")
        for row in rows:
            f.write(
                "{},{},{},{:.0f},{},{},{},{:.0f}\n".format(
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
