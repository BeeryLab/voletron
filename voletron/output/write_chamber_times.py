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
