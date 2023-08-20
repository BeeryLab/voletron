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


import unittest
from unittest.mock import MagicMock, call

from voletron.parse_olcus import parse_raw_line
from voletron.co_dwell_accumulator import Chamber, CoDwellAccumulator
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.structs import CoDwell, Traversal


class TestChamber(unittest.TestCase):
    def test_arrive(self):
        record_group_dwell = MagicMock()
        c = Chamber("foo", record_group_dwell)  # arrive doesn't use record_co_dwell
        self.assertIsNone(c.last_event)
        self.assertEqual(dict(c.animals_since), {})
        c.arrive(100, "tag_a")
        self.assertEqual(c.last_event, 100)
        self.assertEqual(dict(c.animals_since), {"tag_a": 100})

    def test_arrive_depart(self):
        record_group_dwell = MagicMock()
        c = Chamber("foo", record_group_dwell)
        c.arrive(100, "tag_a")
        c.depart(200, "tag_a")
        c.arrive(300, "tag_b")
        self.assertEqual(c.last_event, 300)
        self.assertEqual(dict(c.animals_since), {"tag_b": 300})
        # record_co_dwell.assert_called_once_with("tag_a", "tag_a", 100, 200, "foo")
        record_group_dwell.assert_called_once_with(["tag_a"], 100, 200, "foo")

    def test_depart_before_arrive(self):
        record_group_dwell = MagicMock()
        c = Chamber("foo", record_group_dwell)
        with self.assertRaises(ValueError):
            c.depart(100, "tag_a")

    def test_co_dwell(self):
        record_group_dwell = MagicMock()
        c = Chamber("foo", record_group_dwell)
        c.arrive(100, "tag_a")
        c.arrive(200, "tag_b")
        c.depart(300, "tag_a")
        self.assertEqual(c.last_event, 300)
        self.assertEqual(dict(c.animals_since), {"tag_b": 200})
        self.assertEqual(len(record_group_dwell.mock_calls), 2)
        record_group_dwell.assert_has_calls(
            [call(["tag_a"], 100, 200, "foo"), call(["tag_a", "tag_b"], 200, 300, "foo")]
        )


all_chambers = ["ArenaA", "Tube1", "Tube2", "Cage2"]

class TestState(unittest.TestCase):

    def test_traversal(self):
        tag_id_to_start_chamber = {"tag_a": "ArenaA", "tag_b": "ArenaA"}
        s = CoDwellAccumulator(100, tag_id_to_start_chamber, all_chambers)
        s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))

        self.assertEqual(list(s._chambers.keys()), ["ArenaA", "Tube1", "Tube2", "Cage2"])
        self.assertEqual(dict(s._chambers["ArenaA"].animals_since), {"tag_b": 100})
        self.assertEqual(s._chambers["ArenaA"].last_event, 200)

        self.assertEqual(dict(s._chambers["Tube1"].animals_since), {"tag_a": 200})
        self.assertEqual(s._chambers["Tube1"].last_event, 200)

        co_dwells = s.end(300)
        analyzer = TimeSpanAnalyzer(co_dwells, 0, 300)
        print(analyzer.co_dwells)
        self.assertEqual(len(analyzer.co_dwells), 3)
        self.assertEqual(analyzer.co_dwells[0], CoDwell(['tag_a', 'tag_b'], 100, 200, 'ArenaA'))
        self.assertEqual(analyzer.co_dwells[1], CoDwell(['tag_b'], 200, 300, 'ArenaA'))
        self.assertEqual(analyzer.co_dwells[2], CoDwell(['tag_a'], 200, 300, 'Tube1'))
        # self.assertEqual(list(s.co_dwells.keys()), ["tag_a"])
        # self.assertEqual(
        #     dict(s.co_dwells["tag_a"]),
        #     {
        #         "tag_a": [CoDwell(start=100, end=200, chamber="ArenaA")],
        #         "tag_b": [CoDwell(start=100, end=200, chamber="ArenaA")],
        #     },
        # )

    # def test_co_dwell_stats_unrestricted(self):
    #     tag_id_to_start_chamber = {
    #         "tag_a": "ArenaA",
    #         "tag_b": "ArenaA",
    #         "tag_c": "ArenaA",
    #     }
    #     s = State(100, tag_id_to_start_chamber, all_chambers)
    #     s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))
    #     s.update_state_from_traversal(Traversal(300, "tag_b", "ArenaA", "Tube1"))
    #     s.update_state_from_traversal(Traversal(400, "tag_a", "Tube1", "ArenaA"))
    #     s.update_state_from_traversal(Traversal(500, "tag_c", "ArenaA", "Tube2"))
    #     s.update_state_from_traversal(Traversal(600, "tag_b", "Tube1", "ArenaA"))
    #     s.update_state_from_traversal(Traversal(700, "tag_b", "ArenaA", "Tube2"))
    #     s.update_state_from_traversal(Traversal(800, "tag_c", "Tube2", "Cage2"))
    #     s.update_state_from_traversal(Traversal(900, "tag_b", "Tube2", "ArenaA"))
    #     s.end()

    #     self.assertEqual(
    #         s.co_dwell_stats(tag_id_to_start_chamber.keys(), 0, 1e100),
    #         [
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_a", count=3, duration=800.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_b", count=3, duration=300.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_c", count=2, duration=200.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_b", animal_b="tag_b", count=4, duration=800.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_b", animal_b="tag_c", count=2, duration=300.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_c", animal_b="tag_c", count=3, duration=800.0
    #             ),
    #         ],
    #     )

    # def test_co_dwell_stats_restricted(self):
    #     tag_id_to_start_chamber = {
    #         "tag_a": "ArenaA",
    #         "tag_b": "ArenaA",
    #         "tag_c": "ArenaA",
    #     }
    #     s = State(100, tag_id_to_start_chamber, all_chambers)
    #     s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))
    #     s.update_state_from_traversal(Traversal(300, "tag_b", "ArenaA", "Tube1"))
    #     s.update_state_from_traversal(Traversal(400, "tag_a", "Tube1", "ArenaA"))
    #     s.update_state_from_traversal(Traversal(500, "tag_c", "ArenaA", "Tube2"))
    #     s.update_state_from_traversal(Traversal(600, "tag_b", "Tube1", "ArenaA"))
    #     s.update_state_from_traversal(Traversal(700, "tag_b", "ArenaA", "Tube2"))
    #     s.update_state_from_traversal(Traversal(800, "tag_c", "Tube2", "Cage2"))
    #     s.update_state_from_traversal(Traversal(900, "tag_b", "Tube2", "ArenaA"))
    #     s.end()

    #     analyzer = StateAnalyzer(s, )

    #     self.assertEqual(
    #         analyzer.co_dwell_stats(tag_id_to_start_chamber.keys(), 205, 750),
    #         [
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_a", count=2, duration=545.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_b", count=2, duration=200.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_a", animal_b="tag_c", count=1, duration=100.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_b", animal_b="tag_b", count=4, duration=545.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_b", animal_b="tag_c", count=2, duration=145.0
    #             ),
    #             CoDwellAggregate(
    #                 animal_a="tag_c", animal_b="tag_c", count=2, duration=545.0
    #             ),
    #         ],
    #     )


if __name__ == "__main__":
    unittest.main()
