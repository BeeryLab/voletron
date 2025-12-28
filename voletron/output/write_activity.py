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
from voletron.output.types import ActivityRow

def compute_activity(
    trajectories: AllAnimalTrajectories,
    co_dwells: List[CoDwell],
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
    bin_secs: DurationSeconds,
) -> List[ActivityRow]:
    rows = []
    start = analysis_start_time
    end = TimestampSeconds(start + bin_secs)
    while start < analysis_end_time:
        analyzer = TimeSpanAnalyzer(co_dwells, start, end)
        group_dwell_aggregates = analyzer.get_group_chamber_exclusive_durations()

        for [tag_id, traj] in trajectories.animalTrajectories.items():
            count = traj.count_traversals_between(start, end)
            
            dwells_by_group_size: List[List[DurationSeconds]] = [[], [], [], [], []]
            for x in group_dwell_aggregates:
                if tag_id in x.tag_ids:
                    dwells_by_group_size[len(x.tag_ids)].append(x.duration_seconds)
            
            avg_dwells_by_group_size = [
                sum(xx) / len(xx) if xx else 0.0 for xx in dwells_by_group_size
            ]

            rows.append(ActivityRow(
                start_time=start,
                end_time=end,
                bin_seconds=bin_secs,
                tag_id=tag_id,
                avg_dwell_sizes=[
                     avg_dwells_by_group_size[1],
                     avg_dwells_by_group_size[2],
                     avg_dwells_by_group_size[3],
                     avg_dwells_by_group_size[4]
                ],
                traversal_count=count
            ))

        start = TimestampSeconds(start + bin_secs)
        end = TimestampSeconds(end + bin_secs)
    return rows

def write_activity(
    rows: List[ActivityRow],
    out_dir: str,
    exp_name: str,
    boundary_type: str,
):
    with open(os.path.join(out_dir, f"{exp_name}.activity.{boundary_type}.csv"), "w") as f:
        f.write("start_time,end_time,bin_seconds,tag_id,avg_dwell_size_1,avg_dwell_size_2,avg_dwell_size_3,avg_dwell_size_4,traversal_count\n")
        
        for row in rows:
            f.write(
                f"{row.start_time},{row.end_time},{row.bin_seconds},{row.tag_id},"
                f"{row.avg_dwell_sizes[0]},"
                f"{row.avg_dwell_sizes[1]},"
                f"{row.avg_dwell_sizes[2]},"
                f"{row.avg_dwell_sizes[3]},"
                f"{row.traversal_count}\n"
            )
