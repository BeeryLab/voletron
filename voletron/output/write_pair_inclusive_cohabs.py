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
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import Config
from voletron.output.types import PairCohabRow

def compute_pair_inclusive_cohabs(
    config: Config, analyzer: TimeSpanAnalyzer
) -> List[PairCohabRow]:
    rows = []
    for codwell_aggregate in analyzer.get_pair_inclusive_stats():
        animal_a, animal_b = codwell_aggregate.tag_ids
        rows.append(PairCohabRow(
            animal_a_name=config.tag_id_to_name[animal_a],
            animal_b_name=config.tag_id_to_name[animal_b],
            dwell_count=codwell_aggregate.count,
            duration_seconds=codwell_aggregate.duration_seconds,
            test_duration=analyzer.duration,
        ))
    return rows

def write_pair_inclusive_cohabs(
    rows: List[PairCohabRow], out_dir: str, exp_name: str
):
    with open(os.path.join(out_dir, exp_name + ".pair-inclusive.cohab.csv"), "w") as f:
        f.write("Animal A,Animal B,dwells,seconds,test_duration\n")
        for row in rows:
            f.write(
                "{},{},{},{:.0f},{:.0f}\n".format(
                    row.animal_a_name,
                    row.animal_b_name,
                    row.dwell_count,
                    row.duration_seconds,
                    row.test_duration,
                )
            )
