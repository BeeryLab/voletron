# Copyright 2022 Google LLC
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
from collections import defaultdict

from voletron.util import format_time


def writeCohabs(
    config, tag_ids, out_dir, exp_name, state, analysis_start_time, analysis_end_time
):
    with open(os.path.join(out_dir, exp_name + ".cohab.csv"), "w") as f:
        test_duration = analysis_end_time - analysis_start_time
        f.write("Animal A,Animal B,dwells,seconds,test_duration\n")
        for (a, b, dwells, seconds) in state.co_dwell_stats(
            tag_ids, analysis_start_time, analysis_end_time
        ):
            f.write(
                "{},{},{},{:.0f},{:.0f}\n".format(
                    config.tag_id_to_name[a],
                    config.tag_id_to_name[b],
                    dwells,
                    seconds,
                    test_duration,
                )
            )


def writeGroupCohabs(
    config,
    tag_ids,
    out_dir,
    exp_name,
    state,
    analysis_start_time,
    analysis_end_time,
    tag_id_to_name,
):
    with open(os.path.join(out_dir, exp_name + ".group_cohab.csv"), "w") as f:
        test_duration = analysis_end_time - analysis_start_time
        f.write("Animals,dwells,seconds,test_duration\n")
        for (group, dwells, seconds) in state.group_dwell_stats(
            analysis_start_time, analysis_end_time
        ):
            if group == "":
                continue
            group_tag_ids = group.split(" ")
            bad = False
            for tag_id in group_tag_ids:
                if tag_id not in tag_ids:
                    bad = True
            if bad:
                continue
            names = sorted(map(lambda x: tag_id_to_name[x], group_tag_ids))
            f.write(
                "{},{},{:.0f},{:.0f}\n".format(
                    " ".join(names), dwells, seconds, test_duration
                )
            )


def writeChamberTimes(
    config,
    tag_ids,
    chambers,
    out_dir,
    exp_name,
    trajectories,
    analysis_start_time,
    analysis_end_time,
):
    with open(os.path.join(out_dir, exp_name + ".chambers.csv"), "w") as f:
        f.write("animal," + ",".join(chambers) + ",total\n")
        for (tag_id, trajectory) in trajectories.animalTrajectories.items():
            if not tag_id in tag_ids:
                continue
            ct = trajectory.time_per_chamber(analysis_start_time, analysis_end_time)
            # f.write("{}, {:.0f}".format(config.tag_id_to_name[tag_id], sum(ct.values())))
            aaa = ",".join(map(lambda c: "{:.0f}".format(ct[c]), chambers))
            f.write(
                "{},{},{:.0f}\n".format(
                    config.tag_id_to_name[tag_id], aaa, sum(ct.values())
                )
            )


def write_activity(
    out_dir,
    exp_name,
    trajectories: AllAnimalTrajectories,
    analysis_start_time,
    analysis_end_time,
    bin_secs,
):
    with open(os.path.join(out_dir, exp_name + ".activity.csv"), "w") as f:
        for [tag_id, traj] in trajectories.animalTrajectories.items():
            start = analysis_start_time
            end = start + bin_secs
            while start < analysis_end_time:
                # inefficient but so what
                count = traj.count_traversals_between(start, end)
                f.write(f"{tag_id},{start},{end},{bin_secs},{count}")
                start += bin_secs
                end += bin_secs

def writeGroupSizes(
    tag_ids,
    out_dir,
    exp_name,
    state,
    analysis_start_time,
    analysis_end_time,
    tag_id_to_name
):
    group_sizes = range(0, 9)
    tag_id_group_size_seconds = defaultdict(lambda: [0]*9)
    duration = analysis_end_time - analysis_start_time
    with open(os.path.join(out_dir, exp_name + ".group_size.csv"), "w") as f:
        f.write(
            "animal,"
            + ",".join(map(str, group_sizes[1:]))
            + ",avg_group_size,avg_group_size_nosolo,sum_pair_time,test_duration\n"
        )
        for (group, dwells, seconds) in state.group_dwell_stats(
            analysis_start_time, analysis_end_time
        ):
            group_tag_ids = group.split(" ")
            for tag_id in group_tag_ids:
                if tag_id in tag_ids:
                    tag_id_group_size_seconds[tag_id][len(group_tag_ids)] += seconds
        for (tag_id, group_size_seconds) in tag_id_group_size_seconds.items():
            aaa = ','.join(map(lambda a: "{:.0f}".format(a), group_size_seconds[1:]))
            
            avg_group_size = sum([group_size * seconds for (group_size, seconds) in enumerate(group_size_seconds)])/duration
            avg_group_size_nosolo = sum([(group_size_minus_two+2) * seconds for (group_size_minus_two, seconds) in enumerate(group_size_seconds[2:])])/sum(group_size_seconds[2:])
            
            sum_pair_time = sum([(group_size_minus_two+1) * seconds for (group_size_minus_two, seconds) in enumerate(group_size_seconds[2:])])/duration

            f.write(
                "{},{},{:.2f},{:.2f},{:.4f},{:.0f}\n".format(
                    tag_id_to_name[tag_id], aaa, avg_group_size, avg_group_size_nosolo, sum_pair_time, duration
                ))


def writeLongDwells(config, tag_ids, out_dir, exp_name, trajectories):
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


# def writeFullHistory(config, out_dir, exp_name, state):
#    with open(os.path.join(out_dir, exp_name+'.states.csv'), "w") as f:
#         f.write("Animal A,Animal B,dwells\nseconds\n")
#         for (a, b, c, d) in state.co_dwell_stats(config.tag_id_to_name.keys()):
#             f.write("{},{},{},{}\n".format(config.tag_id_to_name[a], config.tag_id_to_name[b], c, d))
