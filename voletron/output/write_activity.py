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
from voletron.trajectory import AllAnimalTrajectories
from voletron.types import CoDwell, DurationSeconds, TimestampSeconds

def write_activity(
    out_dir: str,
    exp_name: str,
    boundary_type: str,
    trajectories: AllAnimalTrajectories,
    co_dwells: List[CoDwell],
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
    bin_secs: DurationSeconds,
):
    with open(os.path.join(out_dir, f"{exp_name}.activity.{boundary_type}.csv"), "w") as f:
        start = analysis_start_time
        end = TimestampSeconds(start + bin_secs)
        while start < analysis_end_time:
            analyzer = TimeSpanAnalyzer(co_dwells, start, end)
            group_dwell_aggregates = analyzer.get_group_chamber_exclusive_durations()

            # inefficient but so what   
            for [tag_id, traj] in trajectories.animalTrajectories.items():
                count = traj.count_traversals_between(start, end)
                # lists of dwells for each group size 0, 1, 2, 3, 4
                # 0 is impossible but we leave it in so that the list indexes match
                dwells_by_group_size: List[List[DurationSeconds]] = [[], [], [], [], []]
                for x in group_dwell_aggregates:
                    if tag_id in x.tag_ids:
                        dwells_by_group_size[len(x.tag_ids)].append(x.duration_seconds)
                assert len(dwells_by_group_size[0]) == 0
                
                avg_dwells_by_group_size = [
                    sum(xx) / len(xx) if xx else 0.0 for xx in dwells_by_group_size
                ]

                f.write(
                    f"{start},{end},{bin_secs},{tag_id},"
                    f"{avg_dwells_by_group_size[1]},"
                    f"{avg_dwells_by_group_size[2]},"
                    f"{avg_dwells_by_group_size[3]},"
                    f"{avg_dwells_by_group_size[4]},"
                    f"{count}"
                )
            start = TimestampSeconds(start + bin_secs)
            end = TimestampSeconds(end + bin_secs)
