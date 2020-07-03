import sys

import trajectory
from collections import defaultdict
import util


class Chamber:
    def __init__(self, record_co_dwell):
        self.animals_since = defaultdict()
        self.last_event = None
        self.record_co_dwell = record_co_dwell

    def arrive(self, timestamp, tag_id):
        self.animals_since[tag_id] = timestamp
        self.last_event = timestamp

    def depart(self, timestamp, tag_id):
        arrive_time = self.animals_since.get(tag_id)
        if not arrive_time:
            # Ignore initial conditions
            return
        del self.animals_since[tag_id]
        for (other_tag_id, other_arrive_time) in self.animals_since.items():
            co_dwell_start = max(arrive_time, other_arrive_time)
            co_dwell_seconds = util.seconds_between_timestamps(
                timestamp, co_dwell_start
            )
            self.record_co_dwell(tag_id, other_tag_id, co_dwell_seconds)
        self.record_co_dwell(
            tag_id, tag_id, util.seconds_between_timestamps(arrive_time, timestamp)
        )
        self.last_event = timestamp


class State:
    def __init__(self):
        self.chambers = defaultdict(lambda: Chamber(self._record_co_dwell))
        self.animals_in_chamber = defaultdict(list)
        self.last_chamber_event = {}
        self.co_dwells = defaultdict(lambda: defaultdict(list))
        pass

    def update_state_from_traversal(self, traversal):
        self.chambers[traversal.orig].depart(traversal.timestamp, traversal.tag_id)
        self.chambers[traversal.dest].arrive(traversal.timestamp, traversal.tag_id)

    def _record_co_dwell(self, tag_id_a, tag_id_b, seconds):
        if tag_id_a > tag_id_b:
            (tag_id_a, tag_id_b) = (tag_id_b, tag_id_a)
        self.co_dwells[tag_id_a][tag_id_b].append(seconds)

    def co_dwell_bouts(self):
        nested = {
            tag_id_a: {
                tag_id_b: len(co_dwells) for (tag_id_b, co_dwells) in bbb.items()
            }
            for (tag_id_a, bbb) in self.co_dwells.items()
        }
        return [
            (tag_id_a, tag_id_b, bouts)
            for (tag_id_a, bbb) in nested.items()
            for (tag_id_b, bouts) in bbb.items()
        ]

    def co_dwell_sums(self):
        nested = {
            tag_id_a: {
                tag_id_b: int(sum(co_dwells)) for (tag_id_b, co_dwells) in bbb.items()
            }
            for (tag_id_a, bbb) in self.co_dwells.items()
        }
        return [
            (tag_id_a, tag_id_b, duration)
            for (tag_id_a, bbb) in nested.items()
            for (tag_id_b, duration) in bbb.items()
        ]


def main(argv):
    filename = argv[1]
    all = trajectory.AllAnimalTrajectories()
    all.update_trajectories_from_raw_file(filename)
    state = State()
    for t in all.traversals():
        state.update_state_from_traversal(t)
    print("BOUTS:")
    for (a, b, c) in state.co_dwell_bouts():
        print("{}\t{}\t{}".format(a, b, c))
    print("CO-HAB DURATION:")
    for (a, b, c) in state.co_dwell_sums():
        print("{}\t{}\t{}".format(a, b, c))


main(sys.argv)

# TODO: specify time range to analyze
