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


from typing import Dict, Optional

from collections import defaultdict
from typing import Dict, List
from voletron.util import seconds_between_timestamps
from voletron.types import ChamberName, CoDwell, DurationSeconds, GroupDwellAggregate, GroupID, TagID, TimestampSeconds


class TimeSpanAnalyzer:
    def __init__(
        self,
        co_dwells: List[CoDwell],
        analysis_start_time: TimestampSeconds,
        analysis_end_time: TimestampSeconds,
    ):
        # Note that the input CoDwells are "exclusive", i.e. an A+B+C CoDwell is
        # not also represented as an A+B CoDwell.

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

    def get_group_chamber_exclusive_durations(self) -> List[GroupDwellAggregate]:
        """Outputs dwell statistics for each group of animals in the "exclusive"
        sense, meaning that an A+B+C group dwell is *not* counted towards A+B,
        B+C, and A+C."""
        dwells_by_group_and_chamber: Dict[GroupID, Dict[ChamberName, list[CoDwell]]] = defaultdict(lambda: defaultdict(list))
        for d in self.co_dwells:
            group_id : GroupID = GroupID(frozenset(d.tag_ids))
            dwells_by_group_and_chamber[group_id][d.chamber].append(d)

        result = []
        for (group_id, chamber_dwells) in dwells_by_group_and_chamber.items():
            for (chamber, dwells) in chamber_dwells.items():
                result.append(
                    GroupDwellAggregate(
                        tag_ids=list(group_id),
                        chamber=chamber,
                        count=len(dwells),
                        duration_seconds=_durations_sum_seconds(dwells),
                    )
                )

        return result

    def get_pair_inclusive_stats(
        self,
    ) -> List[GroupDwellAggregate]:
        """Outputs dwell statistics for each pair of animals in the "inclusive"
        sense, meaning that an A+B+C group dwell is counted towards A+B, B+C,
        and A+C.
        
        This aggregates over chambers.
        """
        dwells_by_pair : Dict[TagID, Dict[TagID, List[CoDwell]]] = defaultdict(lambda: defaultdict(list))
        for d in self.co_dwells:
            # tag_a < tag_b lexicographically
            # Note that a dwell of >2 animals gets added to each contained pair
            for [tag_a, tag_b] in _all_pairs(d.tag_ids):
                dwells_by_pair[tag_a][tag_b].append(d)

        result = []
        for (tag_a, tag_b_dwells) in dwells_by_pair.items():
            for (tag_b, dwells) in tag_b_dwells.items():
                result.append(
                    GroupDwellAggregate(
                        tag_ids=[tag_a, tag_b],
                        chamber=ChamberName("All"),
                        count=len(dwells),
                        duration_seconds=_durations_sum_seconds(dwells),
                    )
                )

        return result


def _restrict_co_dwell(
    codwell: CoDwell, analysis_start_time: TimestampSeconds, analysis_end_time: TimestampSeconds
) -> Optional[CoDwell]:
    """Limit co-dwells to the analysis start-end interval."""
    start = TimestampSeconds(max(codwell.start, analysis_start_time))
    end = TimestampSeconds(min(codwell.end, analysis_end_time))
    if end > start:
        return CoDwell(codwell.tag_ids, start, end, codwell.chamber)
    return None


def _durations_sum_seconds(dwells: List[CoDwell]) -> DurationSeconds:
    durations = [seconds_between_timestamps(cd.start, cd.end) for cd in dwells]
    return DurationSeconds(sum(durations))


# def _all_pairs(items: Iterable[T]) => List[Tuple[T, T]]:
def _all_pairs(items):
    result = []
    for x in items:
        for y in items:
            if x < y:
                result.append([x, y])
    return result