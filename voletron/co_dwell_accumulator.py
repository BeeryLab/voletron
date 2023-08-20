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


from typing import Dict

# import .trajectory
from collections import defaultdict
from typing import Dict, List
from voletron.util import seconds_between_timestamps
from voletron.structs import CoDwell, Traversal


# type RecordGroupDwellFn = (tag_ids: List[str], start: float, end: float, chamber: str) -> Void


class Chamber:
    def __init__(self, name: str, record_group_dwell):  # RecordGroupDwellFn):
        self.name = name
        self.animals_since = defaultdict()
        self.last_event = None
        # self.record_co_dwell = record_co_dwell
        self.record_group_dwell = record_group_dwell

    def arrive(self, timestamp: float, tag_id: str) -> None:
        tag_ids = list(self.animals_since)
        if len(tag_ids) > 0:
            self.record_group_dwell(tag_ids, self.last_event, timestamp, self.name)
        self.animals_since[tag_id] = timestamp
        self.last_event = timestamp

    def depart(self, timestamp: float, tag_id: str) -> None:
        arrive_time = self.animals_since.get(tag_id)
        if not arrive_time:
            raise ValueError(
                "Can't depart without first arriving: {} {} {}".format(
                    tag_id, arrive_time, timestamp
                )
            )
        tag_ids = list(self.animals_since)
        if len(tag_ids) > 0:
            self.record_group_dwell(tag_ids, self.last_event, timestamp, self.name)
        del self.animals_since[tag_id]
        # for (other_tag_id, other_arrive_time) in self.animals_since.items():
        #     co_dwell_start = max(arrive_time, other_arrive_time)
        #     self.record_co_dwell(tag_id, other_tag_id, co_dwell_start, timestamp, self.name)
        # self.record_co_dwell(tag_id, tag_id, arrive_time, timestamp, self.name)
        self.last_event = timestamp


class CoDwellAccumulator:
    # Accumulate state

    def __init__(
        self,
        experiment_start_time: float,
        tag_id_to_start_chamber: Dict[str, str],
        chambers: List[str],
    ):
        if not experiment_start_time:
            raise ValueError("Experiment must have a non-zero start time")
        # self.chambers = defaultdict(
        #    lambda: Chamber(self._record_co_dwell, self._record_group_dwell)
        # )

        self._end_was_called = False
        self._chambers = {
            chamber: Chamber(chamber, self._record_group_dwell) for chamber in chambers
        }
        # self.co_dwells = defaultdict(lambda: defaultdict(list))
        self._co_dwells: List[CoDwell] = []  # defaultdict(list)
        # self.group_chamber_dwells = defaultdict(lambda: defaultdict(list))

        for [tag_id, start_chamber] in tag_id_to_start_chamber.items():
            self._chambers[start_chamber].arrive(experiment_start_time, tag_id)

    def update_state_from_traversal(self, traversal: Traversal) -> None:
        if (
            traversal.orig and traversal.orig != "ERROR"
        ):  # Initial placements have orig = None
            self._chambers[traversal.orig].depart(traversal.timestamp, traversal.tag_id)
        if traversal.dest and traversal.dest != "ERROR":
            self._chambers[traversal.dest].arrive(traversal.timestamp, traversal.tag_id)

    # def _record_co_dwell(self, tag_id_a, tag_id_b, start, end, chamber):
    #     if tag_id_a > tag_id_b:
    #         (tag_id_a, tag_id_b) = (tag_id_b, tag_id_a)
    #     self.co_dwells[tag_id_a][tag_id_b].append(CoDwell(start, end, chamber))

    def _record_group_dwell(
        self, tag_ids: List[str], start: float, end: float, chamber: str
    ) -> None:
        if not start:
            return
        self._co_dwells.append(CoDwell(tag_ids, start, end, chamber))

    def end(self, end_time: float) -> List[CoDwell]:
        self._end_was_called = True
        # end_time = max([c.last_event for c in self.chambers.values() if c.last_event])
        for chamber in self._chambers.values():
            for tag_id in list(chamber.animals_since.keys()):
                chamber.depart(end_time, tag_id)
        return self._co_dwells
