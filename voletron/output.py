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
import math
from collections import defaultdict
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.trajectory import AllAnimalTrajectories
from voletron.structs import Config, CoDwell

from voletron.util import format_time

from typing import List, Dict


def write_pair_inclusive_cohabs(
    config: Config, out_dir: str, exp_name: str, analyzer: TimeSpanAnalyzer
):
    with open(os.path.join(out_dir, exp_name + ".pair-inclusive.cohab.csv"), "w") as f:
        f.write("Animal A,Animal B,dwells,seconds,test_duration\n")
        for codwell_aggregate in analyzer.get_pair_inclusive_stats():
            f.write(
                "{},{},{},{:.0f},{:.0f}\n".format(
                    config.tag_id_to_name[codwell_aggregate.animal_a],
                    config.tag_id_to_name[codwell_aggregate.animal_b],
                    codwell_aggregate.count,
                    codwell_aggregate.duration,
                    analyzer.duration,
                )
            )


# def write_group_cohabs(
#     config,
#     tag_ids,
#     out_dir,
#     exp_name,
#     analyzer,
#     tag_id_to_name,
# ):
#     with open(os.path.join(out_dir, exp_name + ".group_cohab.csv"), "w") as f:
#         test_duration = analysis_end_time - analysis_start_time
#         f.write("Animals,dwells,seconds,test_duration\n")
#         for (group, dwells, seconds) in state.group_dwell_stats(
#             analysis_start_time, analysis_end_time
#         ):
#             if group == "":
#                 continue
#             group_tag_ids = group.split(" ")
#             bad = False
#             for tag_id in group_tag_ids:
#                 if tag_id not in tag_ids:
#                     bad = True
#             if bad:
#                 continue
#             names = sorted(map(lambda x: tag_id_to_name[x], group_tag_ids))
#             f.write(
#                 "{},{},{:.0f},{:.0f}\n".format(
#                     " ".join(names), dwells, seconds, test_duration
#                 )
#             )


def write_group_chamber_cohabs(
    tag_ids: List[str],
    out_dir: str,
    exp_name: str,
    analyzer: TimeSpanAnalyzer,
    tag_id_to_name: Dict[str, str],
):
    with open(os.path.join(out_dir, exp_name + ".group_chamber_cohab.csv"), "w") as f:
        f.write("animals,chamber,dwells,seconds,test_duration\n")
        for (
            group,
            chamber_seconds,
        ) in analyzer.get_group_chamber_exclusive_durations().items():
            if group == "":
                continue
            for (chamber, seconds) in chamber_seconds.items():
                group_tag_ids = group.split(" ")

                # ignore any tag_ids that were not explicitly requested
                bad = False
                for tag_id in group_tag_ids:
                    if tag_id not in tag_ids:
                        bad = True
                if bad:
                    continue

                names = sorted(map(lambda x: tag_id_to_name[x], group_tag_ids))
                f.write(
                    "{},{},{:.0f},{:.0f}\n".format(
                        " ".join(names), chamber, seconds, analyzer.duration
                    )
                )


def write_chamber_times(
    config: Config,
    tag_ids: List[str],
    chambers: List[str],
    out_dir: str,
    exp_name: str,
    trajectories: AllAnimalTrajectories,
    analysis_start_time: float,
    analysis_end_time: float,
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
    out_dir: str,
    exp_name: str,
    boundary_type: str,
    trajectories: AllAnimalTrajectories,
    co_dwells: List[CoDwell],
    analysis_start_time: float,
    analysis_end_time: float,
    bin_secs: int,
):
    with open(os.path.join(out_dir, f"{exp_name}.activity.{boundary_type}.csv"), "w") as f:
        start = analysis_start_time
        end = start + bin_secs
        while start < analysis_end_time:
            analyzer = TimeSpanAnalyzer(co_dwells, start, end)
            group_dwell_aggregates = analyzer.get_group_chamber_exclusive_durations()

            # inefficient but so what
            for [tag_id, traj] in trajectories.animalTrajectories.items():
                count = traj.count_traversals_between(start, end)
                # lists of dwells for each group size 0, 1, 2, 3, 4
                # 0 is impossible but we leave it in so that the list indexes match
                dwells_by_group_size: List[List(float)] = [[], [], [], [], []]
                for x in group_dwell_aggregates:
                    if tag_id in x.tag_ids:
                        dwells_by_group_size[len(x.tag_ids)].append(x.duration_seconds)
                assert len(dwells_by_group_size[0]) == 0
                avg_dwells_by_group_size = [math.avg(xx) for xx in dwells_by_group_size]

                f.write(
                    f"{start},{end},{bin_secs},{tag_id},"
                    f"{avg_dwells_by_group_size[1]},"
                    f"{avg_dwells_by_group_size[2]},"
                    f"{avg_dwells_by_group_size[3]},"
                    f"{avg_dwells_by_group_size[4]},"
                    f"{count}"
                )
            start += bin_secs
            end += bin_secs


def write_group_sizes(
    tag_ids: List[str],
    out_dir: str,
    exp_name: str,
    analyzer: TimeSpanAnalyzer,
    tag_id_to_name: Dict[str, str],
):
    group_sizes = range(0, 9)
    tag_id_group_size_seconds = defaultdict(lambda: [0] * 9)
    with open(os.path.join(out_dir, exp_name + ".group_size.csv"), "w") as f:
        f.write(
            "animal,"
            + ",".join(map(str, group_sizes[1:]))
            + ",avg_group_size,avg_group_size_nosolo,sum_pair_time,test_duration\n"
        )
        for group_dwell in analyzer.get_group_chamber_exclusive_durations():
            for tag_id in group_dwell.tag_ids:
                if tag_id in tag_ids:
                    tag_id_group_size_seconds[tag_id][
                        len(group_dwell.tag_ids)
                    ] += group_dwell.duration_seconds

        # for (group, dwells, seconds) in analyzer.group_dwell_stats():
        #     group_tag_ids = group.split(" ")
        #     for tag_id in group_tag_ids:
        #         if tag_id in tag_ids:
        #             tag_id_group_size_seconds[tag_id][len(group_tag_ids)] += seconds

        for (tag_id, group_size_seconds) in tag_id_group_size_seconds.items():
            aaa = ",".join(map(lambda a: "{:.0f}".format(a), group_size_seconds[1:]))

            avg_group_size = (
                sum(
                    [
                        group_size * seconds
                        for (group_size, seconds) in enumerate(group_size_seconds)
                    ]
                )
                / analyzer.duration
            )
            # Total time when an animal was not alone
            total_nosolo_seconds = sum(group_size_seconds[2:])
            # If the animal was always alone, then the average not-alone group size is undefined.
            if total_nosolo_seconds == 0:
                avg_group_size_nosolo = "N/A"
            else:
                avg_group_size_nosolo = (
                    sum(
                        [
                            (group_size_minus_two + 2) * seconds
                            for (group_size_minus_two, seconds) in enumerate(
                                group_size_seconds[2:]
                            )
                        ]
                    )
                    / total_nosolo_seconds
                )

            sum_pair_time = (
                sum(
                    [
                        (group_size_minus_two + 1) * seconds
                        for (group_size_minus_two, seconds) in enumerate(
                            group_size_seconds[2:]
                        )
                    ]
                )
                / analyzer.duration
            )

            avg_group_size_nosolo_str = (
                avg_group_size_nosolo
                if isinstance(avg_group_size_nosolo, str)
                else "{:.2f}".format(avg_group_size_nosolo)
            )
            f.write(
                "{},{},{:.2f},{},{:.4f},{:.0f}\n".format(
                    tag_id_to_name[tag_id],
                    aaa,
                    avg_group_size,
                    avg_group_size_nosolo_str,
                    sum_pair_time,
                    analyzer.duration,
                )
            )


def write_long_dwells(
    config: Config,
    tag_ids: List[str],
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


# def writeFullHistory(config, out_dir, exp_name, state):
#    with open(os.path.join(out_dir, exp_name+'.states.csv'), "w") as f:
#         f.write("Animal A,Animal B,dwells\nseconds\n")
#         for (a, b, c, d) in state.co_dwell_stats(config.tag_id_to_name.keys()):
#             f.write("{},{},{},{}\n".format(config.tag_id_to_name[a], config.tag_id_to_name[b], c, d))
