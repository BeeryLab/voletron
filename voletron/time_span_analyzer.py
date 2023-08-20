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


import sys
from typing import Iterable, Dict

# import .trajectory
from collections import defaultdict
from typing import Dict, List
from voletron.util import seconds_between_timestamps
from voletron.structs import CoDwell, GroupDwellAggregate


class TimeSpanAnalyzer:
    def __init__(
        self,
        co_dwells: List[CoDwell],
        analysis_start_time: float,
        analysis_end_time: float,
    ):
        # Note that the input CoDwells are "exclusive", i.e. an A+B+C CoDwell is
        # not also represented as an A+B CoDwell.

        # if not state._end_was_called:
        #     raise ValueError(
        #         "Must call State.end() before constructing a StateAnalyzer"
        #     )
        # self.state = state
        self.analysis_start_time = analysis_start_time
        self.analysis_end_time = analysis_end_time
        self.duration = analysis_end_time - analysis_start_time

        # restrict to the analysis time interval
        self.co_dwells = [
            x
            for x in [
                _restrict_co_dwell(d, analysis_start_time, analysis_end_time)
                for d in co_dwells
            ]
            if x
        ]

    # TODO(soergel): refactor to output a list of GroupDwellAggregate
    def get_group_chamber_exclusive_durations(self) -> List[GroupDwellAggregate]:
        """Outputs dwell statistics for each group of animals in the "exclusive"
        sense, meaning that an A+B+C group dwell is *not* counted towards A+B,
        B+C, and A+C."""
        dwells_by_group_and_chamber: Dict[str, Dict[str, list[CoDwell]]] = defaultdict(lambda: defaultdict(list))
        for d in self.co_dwells:
            group_id = " ".join(sorted(d.tag_ids))
            dwells_by_group_and_chamber[group_id][d.chamber].append(d)

        # sum_by_group_and_chamber = defaultdict(lambda: defaultdict(int))
        result = []
        for (group_id, chamber_dwells) in dwells_by_group_and_chamber.items():
            for (chamber, dwells) in chamber_dwells.items():
                result.append(
                    GroupDwellAggregate(
                        tag_ids=group_id.split(' '),  # a bit hacky
                        chamber=chamber,
                        count=len(dwells),
                        duration_seconds=_durations_sum_seconds(dwells),
                    )
                )
                # sum_by_group_and_chamber[group][chamber] = _durations_sum(dwells)

        return result

    def get_pair_inclusive_stats(
        self,
    ) -> List[GroupDwellAggregate]:  # Dict[str, Dict[str, int]]:
        """Outputs dwell statistics for each pair of animals in the "inclusive"
        sense, meaning that an A+B+C group dwell is counted towards A+B, B+C,
        and A+C.
        
        This aggregates over chambers.
        """
        dwells_by_pair = defaultdict(lambda: defaultdict(list))
        for d in self.co_dwells:
            # tag_a < tag_b lexicographically
            # Note that a dwell of >2 animals gets added to each contained pair
            for [tag_a, tag_b] in _all_pairs(d.tag_ids):
                dwells_by_pair[tag_a][tag_b].append(d)

        # sum_by_pair = defaultdict(lambda: defaultdict(int))
        result = []
        for (tag_a, tag_b_dwells) in dwells_by_pair.items():
            for (tag_b, dwells) in tag_b_dwells.items():
                # sum_by_pair[tag_a][tag_b] = _durations_sum(dwells)
                result.append(
                    GroupDwellAggregate(
                        tag_ids=[tag_a, tag_b],
                        chamber=None,
                        count=len(dwells),
                        duration_seconds=_durations_sum_seconds(dwells),
                    )
                )

        return result

    # Analyze state

    # def co_dwell_stats(self, all_tag_ids, analysis_start_time, analysis_end_time):
    #     if not self.end_was_called:
    #         raise ValueError("Must call State.end() before State.co_dwell_stats()")
    #     restricted_dwells = [
    #         [
    #             tag_id_a,
    #             tag_id_b,
    #             self._get_co_dwell_stats(
    #                 tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    #             ),
    #         ]
    #         for (tag_id_a) in all_tag_ids
    #         for (tag_id_b) in all_tag_ids
    #         if tag_id_a <= tag_id_b
    #     ]
    #     # TODO ugh hacky
    #     return [
    #         CoDwellAggregate(
    #             rd[0],
    #             rd[1],
    #             rd[2][0],
    #             rd[2][1],
    #         )
    #         for rd in restricted_dwells
    #     ]

    # def _get_co_dwell_stats(
    #     self, tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    # ):
    #     cds = self._get_co_dwells(
    #         tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    #     )
    #     durations = [seconds_between_timestamps(cd.start, cd.end) for cd in cds]
    #     return [len(durations), sum(durations)]

    # def _get_co_dwells(
    #     self, tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    # ):
    #     all = self.co_dwells[tag_id_a][tag_id_b]
    #     filtered = [
    #         restrict_co_dwell(cd, analysis_start_time, analysis_end_time) for cd in all
    #     ]
    #     return [x for x in filtered if x]

    # def _restricted_group_dwells(self, analysis_start_time, analysis_end_time):
    #     return {
    #         group: [
    #             x
    #             for x in [
    #                 restrict_co_dwell(d, analysis_start_time, analysis_end_time)
    #                 for d in dwells
    #             ]
    #             if x
    #         ]
    #         for (group, dwells) in self.group_dwells.items()
    #     }

    # def _get_group_dwell_stats(self, analysis_start_time, analysis_end_time):
    #     return {
    #         group: self._group_digest(dwells)
    #         for (group, dwells) in self.group_dwells.items()
    #     }

    # def group_dwell_stats(self):
    #     # print(analysis_start_time, analysis_end_time)
    #     restricted_dwells = self._get_group_dwell_stats(
    #         self.analysis_start_time, self.analysis_end_time
    #     )
    #     # TODO ugh hacky
    #     result = [
    #         GroupDwellAggregate(
    #             group,
    #             value[0],
    #             value[1],
    #         )
    #         for (group, value) in restricted_dwells.items()
    #     ]
    #     result.sort(key=lambda a: a.group)
    #     result.sort(key=lambda a: len(a.group))
    #     return result


def _restrict_co_dwell(
    codwell: CoDwell, analysis_start_time: float, analysis_end_time: float
) -> CoDwell:
    """Limit co-dwells to the analysis start-end interval."""
    if not codwell.start or not analysis_start_time:
        print(codwell.start, analysis_start_time, analysis_end_time)
    start = max(codwell.start, analysis_start_time)
    end = min(codwell.end, analysis_end_time)
    if end > start:
        return CoDwell(codwell.tag_ids, start, end, codwell.chamber)
    return None


def _durations_sum_seconds(dwells: List[CoDwell]) -> float:
    durations = [seconds_between_timestamps(cd.start, cd.end) for cd in dwells]
    return sum(durations)  # [len(durations), sum(durations)]


# def _all_pairs(items: Iterable[T]) => List[Tuple[T, T]]:
def _all_pairs(items):
    result = []
    for x in items:
        for y in items:
            if x < y:
                result.append([x, y])
    return result