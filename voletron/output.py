import os

from voletron.apparatus_config import all_chambers
from voletron.util import format_time


def writeCohabs(
    config, out_dir, exp_name, state, analysis_start_time, analysis_end_time
):
    with open(os.path.join(out_dir, exp_name + ".cohab.csv"), "w") as f:
        f.write("Animal A,Animal B,dwells,seconds\n")
        for (a, b, c, d) in state.co_dwell_stats(
            config.tag_id_to_name.keys(), analysis_start_time, analysis_end_time
        ):
            f.write(
                "{},{},{},{:.0f}\n".format(
                    config.tag_id_to_name[a], config.tag_id_to_name[b], c, d
                )
            )


def writeChamberTimes(
    config, out_dir, exp_name, trajectories, analysis_start_time, analysis_end_time
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("animal," + ",".join(all_chambers) + ",total\n")
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            ct = trajectory.time_per_chamber(analysis_start_time, analysis_end_time)
            # f.write("{}, {:.0f}".format(config.tag_id_to_name[tag_id], sum(ct.values())))
            aaa = ",".join(map(lambda c: "{:.0f}".format(ct[c]), all_chambers))
            f.write(
                "{},{},{:.0f}\n".format(
                    config.tag_id_to_name[tag_id], aaa, sum(ct.values())
                )
            )


def writeLongDwells(config, out_dir, exp_name, trajectories):
    with open(os.path.join(out_dir, exp_name + ".longdwells.csv"), "w") as f:
        f.write("animal,chamber,start_time,seconds\n")
        for trajectory in trajectories.animalTrajectories.values():
            for d in trajectory.long_dwells():
                f.write(
                    "{},{},{},{:.0f}\n".format(
                        config.tag_id_to_name[d[0]], d[1], format_time(d[2]), d[3]
                    )
                )


# def writeFullHistory(config, out_dir, exp_name, state):
#    with open(os.path.join(out_dir, exp_name+'.states.csv'), "w") as f:
#         f.write("Animal A,Animal B,dwells\nseconds\n")
#         for (a, b, c, d) in state.co_dwell_stats(config.tag_id_to_name.keys()):
#             f.write("{},{},{},{}\n".format(config.tag_id_to_name[a], config.tag_id_to_name[b], c, d))
