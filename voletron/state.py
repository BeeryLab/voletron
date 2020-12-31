import sys

# import .trajectory
from collections import defaultdict
from voletron.util import seconds_between_timestamps
from voletron.structs import CoDwell, CoDwellAggregate, GroupDwellAggregate


class Chamber:
    def __init__(self, record_co_dwell, record_group_dwell):
        self.animals_since = defaultdict()
        self.last_event = None
        self.record_co_dwell = record_co_dwell
        self.record_group_dwell = record_group_dwell

    def arrive(self, timestamp, tag_id):
        self.record_group_dwell(list(self.animals_since), self.last_event, timestamp)
        self.animals_since[tag_id] = timestamp
        self.last_event = timestamp

    def depart(self, timestamp, tag_id):
        arrive_time = self.animals_since.get(tag_id)
        if not arrive_time:
            raise ValueError(
                "Can't depart without first arriving: {} {} {}".format(
                    tag_id, arrive_time, timestamp
                )
            )
        self.record_group_dwell(list(self.animals_since), self.last_event, timestamp)
        del self.animals_since[tag_id]
        for (other_tag_id, other_arrive_time) in self.animals_since.items():
            co_dwell_start = max(arrive_time, other_arrive_time)
            self.record_co_dwell(tag_id, other_tag_id, co_dwell_start, timestamp)
        self.record_co_dwell(tag_id, tag_id, arrive_time, timestamp)
        self.last_event = timestamp


class State:
    def __init__(self, experiment_start_time, tag_id_to_start_chamber):
        self.chambers = defaultdict(
            lambda: Chamber(self._record_co_dwell, self._record_group_dwell)
        )
        self.co_dwells = defaultdict(lambda: defaultdict(list))
        self.group_dwells = defaultdict(list)
        for [tag_id, start_chamber] in tag_id_to_start_chamber.items():
            self.chambers[start_chamber].arrive(experiment_start_time, tag_id)

    def update_state_from_traversal(self, traversal):
        if (
            traversal.orig and traversal.orig != "ERROR"
        ):  # Initial placements have orig = None
            self.chambers[traversal.orig].depart(traversal.timestamp, traversal.tag_id)
        if traversal.dest and traversal.dest != "ERROR":
            self.chambers[traversal.dest].arrive(traversal.timestamp, traversal.tag_id)

    def _record_co_dwell(self, tag_id_a, tag_id_b, start, end):  # chamber
        if tag_id_a > tag_id_b:
            (tag_id_a, tag_id_b) = (tag_id_b, tag_id_a)
        self.co_dwells[tag_id_a][tag_id_b].append(CoDwell(start, end, None))

    def _record_group_dwell(self, tag_ids, start, end):
        if not start:
            return
        self.group_dwells[" ".join(sorted(tag_ids))].append(CoDwell(start, end, None))

    def end(self):
        self.end_was_called = True
        end_time = max([c.last_event for c in self.chambers.values()])
        for chamber in self.chambers.values():
            for tag_id in list(chamber.animals_since.keys()):
                chamber.depart(end_time, tag_id)

    def co_dwell_stats(self, all_tag_ids, analysis_start_time, analysis_end_time):
        if not self.end_was_called:
            raise ValueError("Must call State.end() before State.co_dwell_stats()")
        restricted_dwells = [
            [
                tag_id_a,
                tag_id_b,
                self._get_co_dwell_stats(
                    tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
                ),
            ]
            for (tag_id_a) in all_tag_ids
            for (tag_id_b) in all_tag_ids
            if tag_id_a <= tag_id_b
        ]
        # TODO ugh hacky
        return [
            CoDwellAggregate(
                rd[0],
                rd[1],
                rd[2][0],
                rd[2][1],
            )
            for rd in restricted_dwells
        ]

    def _get_co_dwell_stats(
        self, tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    ):
        cds = self._get_co_dwells(
            tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
        )
        durations = [seconds_between_timestamps(cd.start, cd.end) for cd in cds]
        return [len(durations), sum(durations)]

    def _get_co_dwells(
        self, tag_id_a, tag_id_b, analysis_start_time, analysis_end_time
    ):
        all = self.co_dwells[tag_id_a][tag_id_b]
        filtered = [
            restrict_co_dwell(cd, analysis_start_time, analysis_end_time) for cd in all
        ]
        return [x for x in filtered if x]

    def _restricted_group_dwells(self, analysis_start_time, analysis_end_time):
        return {
            group: [
                x
                for x in [
                    restrict_co_dwell(d, analysis_start_time, analysis_end_time)
                    for d in dwells
                ]
                if x
            ]
            for (group, dwells) in self.group_dwells.items()
        }

    def _group_digest(self, dwells):
        durations = [seconds_between_timestamps(cd.start, cd.end) for cd in dwells]
        return [len(durations), sum(durations)]

    def _get_group_dwell_stats(self, analysis_start_time, analysis_end_time):
        return {
            group: self._group_digest(dwells)
            for (group, dwells) in self._restricted_group_dwells(
                analysis_start_time, analysis_end_time
            ).items()
        }

    def group_dwell_stats(self, analysis_start_time, analysis_end_time):
        if not self.end_was_called:
            raise ValueError("Must call State.end() before State.co_dwell_stats()")
        # print(analysis_start_time, analysis_end_time)
        restricted_dwells = self._get_group_dwell_stats(
            analysis_start_time, analysis_end_time
        )
        # TODO ugh hacky
        result = [
            GroupDwellAggregate(
                group,
                value[0],
                value[1],
            )
            for (group, value) in restricted_dwells.items()
        ]
        result.sort(key=lambda a: a.group)
        result.sort(key=lambda a: len(a.group))
        return result


def restrict_co_dwell(codwell, analysis_start_time, analysis_end_time):
    if not codwell.start or not analysis_start_time:
        print(codwell.start, analysis_start_time, analysis_end_time)
    start = max(codwell.start, analysis_start_time)
    end = min(codwell.end, analysis_end_time)
    if end > start:
        return CoDwell(start, end, codwell.chamber)
    return None
