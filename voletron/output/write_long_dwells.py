import os
from typing import List
from voletron.types import Config, TagID
from voletron.trajectory import AllAnimalTrajectories
from voletron.util import format_time

def write_long_dwells(
    config: Config,
    tag_ids: List[TagID],
    out_dir: str,
    exp_name: str,
    trajectories: AllAnimalTrajectories,
):
    with open(os.path.join(out_dir, exp_name + ".longdwells.csv"), "w") as f:
        f.write("animal,chamber,start_time,seconds\n")
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            if not tag_id in tag_ids:
                continue
            for d in trajectory.long_dwells():
                f.write(
                    "{},{},{},{:.0f}\n".format(
                        config.tag_id_to_name[d[0]], d[1], format_time(d[2]), d[3]
                    )
                )
