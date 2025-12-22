import os
from collections import defaultdict
from typing import List, Dict
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import AnimalName, DurationSeconds, TagID

def write_group_sizes(
    tag_ids: List[TagID],
    out_dir: str,
    exp_name: str,
    analyzer: TimeSpanAnalyzer,
    tag_id_to_name: Dict[TagID, AnimalName],
):
    group_sizes = range(0, 9)
    tag_id_group_size_seconds : Dict[TagID, List[DurationSeconds]] = defaultdict[TagID, List[DurationSeconds]](lambda: [DurationSeconds(0)] * 9)
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
                    ] = DurationSeconds(tag_id_group_size_seconds[tag_id][
                        len(group_dwell.tag_ids)
                    ] + group_dwell.duration_seconds)

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
