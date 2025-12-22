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
from typing import List, Dict
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import AnimalName, TagID

def write_group_chamber_cohabs(
    tag_ids: List[TagID],
    out_dir: str,
    exp_name: str,
    analyzer: TimeSpanAnalyzer,
    tag_id_to_name: Dict[TagID, AnimalName],
):
    with open(os.path.join(out_dir, exp_name + ".group_chamber_cohab.csv"), "w") as f:
        f.write("animals,chamber,dwells,seconds,test_duration\n")
        for group_dwell_aggregate in analyzer.get_group_chamber_exclusive_durations():
            # Skip groups with tag_ids not in the requested list
            if not all(tag_id in tag_ids for tag_id in group_dwell_aggregate.tag_ids):
                continue

            names = sorted(tag_id_to_name[tag_id] for tag_id in group_dwell_aggregate.tag_ids)
            f.write(
                "{},{},{},{:.0f},{:.0f}\n".format(
                    " ".join(names),
                    group_dwell_aggregate.chamber,
                    group_dwell_aggregate.count,
                    group_dwell_aggregate.duration_seconds,
                    analyzer.duration
                )
            )
