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
from voletron.trajectory import AllAnimalTrajectories
from voletron.types import ChamberName, Config, TagID, TimestampSeconds

def write_chamber_times(
    config: Config,
    tag_ids: List[TagID],
    chambers: List[ChamberName],
    out_dir: str,
    exp_name: str,
    trajectories: AllAnimalTrajectories,
    analysis_start_time: TimestampSeconds,
    analysis_end_time: TimestampSeconds,
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("animal," + ",".join(chambers) + ",total\n")
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            if not tag_id in tag_ids:
                continue
            ct = trajectory.time_per_chamber(analysis_start_time, analysis_end_time)
            
            aaa = ",".join(map(lambda c: "{:.0f}".format(ct[c]), chambers))
            f.write(
                "{},{},{:.0f}\n".format(
                    config.tag_id_to_name[tag_id], aaa, sum(ct.values())
                )
            )
