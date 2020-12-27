import unittest
from unittest.mock import MagicMock, call

from voletron.parse_olcus import parse_raw_line
from voletron.state import Chamber, State
from voletron.structs import Antenna, CoDwellAggregate, CoDwell, Dwell, Read, Traversal


class TestChamber(unittest.TestCase):
    def test_arrive(self):
        c = Chamber(None)  # arrive doesn't use record_co_dwell
        self.assertIsNone(c.last_event)
        self.assertEqual(dict(c.animals_since), {})
        c.arrive(100, "tag_a")
        self.assertEqual(c.last_event, 100)
        self.assertEqual(dict(c.animals_since), {"tag_a": 100})

    def test_arrive_depart(self):
        record_co_dwell = MagicMock()
        c = Chamber(record_co_dwell)
        c.arrive(100, "tag_a")
        c.depart(200, "tag_a")
        c.arrive(300, "tag_b")
        self.assertEqual(c.last_event, 300)
        self.assertEqual(dict(c.animals_since), {"tag_b": 300})
        record_co_dwell.assert_called_once_with("tag_a", "tag_a", 100, 200)

    def test_depart_before_arrive(self):
        record_co_dwell = MagicMock()
        c = Chamber(record_co_dwell)
        with self.assertRaises(ValueError):
            c.depart(100, "tag_a")

    def test_co_dwell(self):
        record_co_dwell = MagicMock()
        c = Chamber(record_co_dwell)
        c.arrive(100, "tag_a")
        c.arrive(200, "tag_b")
        c.depart(300, "tag_a")
        self.assertEqual(c.last_event, 300)
        self.assertEqual(dict(c.animals_since), {"tag_b": 200})
        self.assertEqual(len(record_co_dwell.mock_calls), 2)
        record_co_dwell.assert_has_calls(
            [call("tag_a", "tag_b", 200, 300), call("tag_a", "tag_a", 100, 300)]
        )


class TestState(unittest.TestCase):
    def test_traversal(self):
        tag_id_to_start_chamber = {"tag_a": "ArenaA", "tag_b": "ArenaA"}
        s = State(100, tag_id_to_start_chamber)
        s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))

        self.assertEqual(list(s.chambers.keys()), ["ArenaA", "Tube1"])
        self.assertEqual(dict(s.chambers["ArenaA"].animals_since), {"tag_b": 100})
        self.assertEqual(s.chambers["ArenaA"].last_event, 200)

        self.assertEqual(dict(s.chambers["Tube1"].animals_since), {"tag_a": 200})
        self.assertEqual(s.chambers["Tube1"].last_event, 200)

        self.assertEqual(list(s.co_dwells.keys()), ["tag_a"])
        self.assertEqual(
            dict(s.co_dwells["tag_a"]),
            {
                "tag_a": [CoDwell(begin=100, end=200, chamber=None)],
                "tag_b": [CoDwell(begin=100, end=200, chamber=None)],
            },
        )

    def test_co_dwell_stats_unrestricted(self):
        tag_id_to_start_chamber = {
            "tag_a": "ArenaA",
            "tag_b": "ArenaA",
            "tag_c": "ArenaA",
        }
        s = State(100, tag_id_to_start_chamber)
        s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))
        s.update_state_from_traversal(Traversal(300, "tag_b", "ArenaA", "Tube1"))
        s.update_state_from_traversal(Traversal(400, "tag_a", "Tube1", "ArenaA"))
        s.update_state_from_traversal(Traversal(500, "tag_c", "ArenaA", "Tube2"))
        s.update_state_from_traversal(Traversal(600, "tag_b", "Tube1", "ArenaA"))
        s.update_state_from_traversal(Traversal(700, "tag_b", "ArenaA", "Tube2"))
        s.update_state_from_traversal(Traversal(800, "tag_c", "Tube2", "Cage2"))
        s.update_state_from_traversal(Traversal(900, "tag_b", "Tube2", "ArenaA"))
        s.end()

        self.assertEqual(
            s.co_dwell_stats(tag_id_to_start_chamber.keys(), 0, 1e100),
            [
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_a", count=3, duration=800.0
                ),
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_b", count=3, duration=300.0
                ),
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_c", count=2, duration=200.0
                ),
                CoDwellAggregate(
                    animal_a="tag_b", animal_b="tag_b", count=4, duration=800.0
                ),
                CoDwellAggregate(
                    animal_a="tag_b", animal_b="tag_c", count=2, duration=300.0
                ),
                CoDwellAggregate(
                    animal_a="tag_c", animal_b="tag_c", count=3, duration=800.0
                ),
            ],
        )

    def test_co_dwell_stats_restricted(self):
        tag_id_to_start_chamber = {
            "tag_a": "ArenaA",
            "tag_b": "ArenaA",
            "tag_c": "ArenaA",
        }
        s = State(100, tag_id_to_start_chamber)
        s.update_state_from_traversal(Traversal(200, "tag_a", "ArenaA", "Tube1"))
        s.update_state_from_traversal(Traversal(300, "tag_b", "ArenaA", "Tube1"))
        s.update_state_from_traversal(Traversal(400, "tag_a", "Tube1", "ArenaA"))
        s.update_state_from_traversal(Traversal(500, "tag_c", "ArenaA", "Tube2"))
        s.update_state_from_traversal(Traversal(600, "tag_b", "Tube1", "ArenaA"))
        s.update_state_from_traversal(Traversal(700, "tag_b", "ArenaA", "Tube2"))
        s.update_state_from_traversal(Traversal(800, "tag_c", "Tube2", "Cage2"))
        s.update_state_from_traversal(Traversal(900, "tag_b", "Tube2", "ArenaA"))
        s.end()

        self.assertEqual(
            s.co_dwell_stats(tag_id_to_start_chamber.keys(), 205, 750),
            [
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_a", count=2, duration=545.0
                ),
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_b", count=2, duration=200.0
                ),
                CoDwellAggregate(
                    animal_a="tag_a", animal_b="tag_c", count=1, duration=100.0
                ),
                CoDwellAggregate(
                    animal_a="tag_b", animal_b="tag_b", count=4, duration=545.0
                ),
                CoDwellAggregate(
                    animal_a="tag_b", animal_b="tag_c", count=2, duration=145.0
                ),
                CoDwellAggregate(
                    animal_a="tag_c", animal_b="tag_c", count=2, duration=545.0
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
