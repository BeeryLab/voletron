import unittest

from voletron.parse_olcus import parse_raw_line
from voletron.structs import Antenna, Dwell, Read, Traversal
from voletron.trajectory import (
    AllAnimalTrajectories,
    ReadFate,
    TwoMissingReadsException,
    _AnimalTrajectory,
    chamberBetween,
    inferMissingRead,
)


class TestTrajectoryUtils(unittest.TestCase):
    def test_chamber_between(self):
        ab = Antenna("ChamberA", "ChamberB")
        bc = Antenna("ChamberB", "ChamberC")
        cd = Antenna("ChamberC", "ChamberD")

        abbc = chamberBetween(ab, bc)
        self.assertEqual(abbc, "ChamberB")

        abcd = chamberBetween(ab, cd)
        self.assertEqual(abcd, None)

        with self.assertRaises(ValueError):
            chamberBetween(ab, ab)

    def test_infer_missing_read_two_missing(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read("tag_a", 12345, Antenna("Tube1", "Cage1"))
        readB = Read("tag_a", 23456, Antenna("Tube3", "Cage3"))

        with self.assertRaises(TwoMissingReadsException):
            inferMissingRead(readA, readB)

    def test_infer_missing_tube_arena(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read("tag_a", 12345, Antenna("Tube1", "Cage1"))
        readB = Read("tag_a", 23456, Antenna("Tube3", "ArenaA"))

        inferred = inferMissingRead(readA, readB)
        self.assertEqual(inferred.tag_id, "tag_a")
        self.assertEqual(inferred.timestamp, 12345.001)
        self.assertEqual(inferred.antenna, Antenna("Tube1", "ArenaA"))

    def test_infer_missing_arena_tube(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read("tag_a", 12345, Antenna("Tube3", "ArenaA"))
        readB = Read("tag_a", 23456, Antenna("Tube1", "Cage1"))

        inferred = inferMissingRead(readA, readB)
        self.assertEqual(inferred.tag_id, "tag_a")
        self.assertEqual(inferred.timestamp, 23455.999)
        self.assertEqual(inferred.antenna, Antenna("Tube1", "ArenaA"))


class TestAnimalTrajectory(unittest.TestCase):
    def test_init_dwell(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        readA = Read("tag_a", 23456, Antenna("Tube1", "ArenaA"))
        fate = t.updateFromRead(readA)
        self.assertEqual(fate, ReadFate.Move)
        self.assertEqual(
            t.dwells, [Dwell(12345, 12345, None), Dwell(12345, 23456, "ArenaA")]
        )
        # There is one traversal representing the beginning of the experiment
        self.assertEqual(
            list(t.traversals()), [Traversal(12345, "tag_a", None, "ArenaA")]
        )

        readB = Read("tag_a", 34567, Antenna("Tube1", "Cage1"))
        fate = t.updateFromRead(readB)
        self.assertEqual(fate, ReadFate.Move)
        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                Dwell(12345, 23456, "ArenaA"),
                Dwell(23456, 34567, "Tube1"),
            ],
        )
        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(12345, "tag_a", None, "ArenaA"),
                Traversal(23456, "tag_a", "ArenaA", "Tube1"),
            ],
        )

    def test_repeated_read_short(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        antenna = Antenna("Tube1", "ArenaA")
        t.updateFromRead(Read("tag_a", 23456, antenna))
        fate = t.updateFromRead(Read("tag_a", 23460, antenna))
        self.assertEqual(fate, ReadFate.Short_Tube)

        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                Dwell(12345, 23456, "ArenaA"),
                # Short dwell in the tube
                Dwell(23456, 23460, "Tube1"),
            ],
        )

    def test_repeated_read_long(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        antenna = Antenna("Tube1", "ArenaA")
        t.updateFromRead(Read("tag_a", 23456, antenna))
        fate = t.updateFromRead(Read("tag_a", 34567, antenna))
        self.assertEqual(fate, ReadFate.Long_Cage)

        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                # Arena dwell extended
                Dwell(12345, 34567, "ArenaA"),
            ],
        )

    def test_move(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        t.updateFromRead(Read("tag_a", 23456, Antenna("Tube1", "ArenaA")))
        fate = t.updateFromRead(Read("tag_a", 34567, Antenna("Tube1", "Cage1")))
        self.assertEqual(fate, ReadFate.Move)

        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                Dwell(12345, 23456, "ArenaA"),
                Dwell(23456, 34567, "Tube1"),
            ],
        )

    def test_one_missing(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        t.updateFromRead(Read("tag_a", 23456, Antenna("Tube1", "ArenaA")))
        fate = t.updateFromRead(Read("tag_a", 34567, Antenna("Tube2", "Cage2")))
        self.assertEqual(fate, ReadFate.OneMissing)

        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                # Arena dwell extended
                Dwell(12345, 34566.999, "ArenaA"),
                Dwell(34566.999, 34567, "Tube2"),
            ],
        )

    def test_two_missing(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 12345)

        t.updateFromRead(Read("tag_a", 23456, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 34567, Antenna("Tube1", "Cage1")))
        fate = t.updateFromRead(Read("tag_a", 45678, Antenna("Tube3", "Cage3")))
        self.assertEqual(fate, ReadFate.TwoMissing)

        self.assertEqual(
            t.dwells,
            [
                Dwell(12345, 12345, None),
                # Arena dwell extended
                Dwell(12345, 23456, "ArenaA"),
                Dwell(23456, 34567, "Tube1"),
                Dwell(34567, 45678, "ERROR"),
            ],
        )

    def test_traversals(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 100)

        t.updateFromRead(Read("tag_a", 200, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 300, Antenna("Tube1", "Cage1")))
        t.updateFromRead(
            Read("tag_a", 305, Antenna("Tube1", "Cage1"))
        )  # Short (< 10 sec)
        t.updateFromRead(Read("tag_a", 500, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 600, Antenna("Tube1", "Cage1")))
        t.updateFromRead(Read("tag_a", 700, Antenna("Tube1", "Cage1")))  # Long
        t.updateFromRead(Read("tag_a", 800, Antenna("Tube2", "ArenaA")))  # OneMissing
        t.updateFromRead(Read("tag_a", 900, Antenna("Tube2", "Cage2")))

        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(timestamp=100, tag_id="tag_a", orig=None, dest="ArenaA"),
                Traversal(timestamp=200, tag_id="tag_a", orig="ArenaA", dest="Tube1"),
                # ...bouncing around in the tube...
                Traversal(timestamp=600, tag_id="tag_a", orig="Tube1", dest="Cage1"),
                Traversal(timestamp=700, tag_id="tag_a", orig="Cage1", dest="Tube1"),
                Traversal(
                    timestamp=700.001,
                    tag_id="tag_a",
                    orig="Tube1",
                    dest="ArenaA",  # inserted missing read, allocating time to the arena
                ),
                Traversal(timestamp=800, tag_id="tag_a", orig="ArenaA", dest="Tube2")
                # Read at 900 does not indicate a traversal (lacking a subsequent read)
            ],
        )

    def test_long_dwells(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 100)

        t.updateFromRead(Read("tag_a", 200, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 300, Antenna("Tube1", "Cage1")))
        t.updateFromRead(Read("tag_a", 30300, Antenna("Tube1", "Cage1")))  # Very Long
        t.updateFromRead(
            Read("tag_a", 90300.001, Antenna("Tube2", "ArenaA"))
        )  # OneMissing, very long in the arena, with extra 1 ms for missing read
        t.updateFromRead(Read("tag_a", 100000, Antenna("Tube2", "Cage2")))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=100, end=100, chamber=None),
                Dwell(start=100, end=200, chamber="ArenaA"),
                Dwell(start=200, end=300, chamber="Tube1"),
                Dwell(start=300, end=30300, chamber="Cage1"),
                Dwell(start=30300, end=30300.001, chamber="Tube1"),
                Dwell(start=30300.001, end=90300.001, chamber="ArenaA"),
                Dwell(start=90300.001, end=100000, chamber="Tube2"),
            ],
        )

        # which of those are "very long"?
        self.assertEqual(
            list(t.long_dwells()),
            [
                ["tag_a", "Cage1", 300, 500.0],  # 500 sec in cage 1
                ["tag_a", "ArenaA", 30300.001, 1000],  # 1000 sec in the arena
            ],
        )

    def test_time_per_chamber_unrestricted(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 100)

        t.updateFromRead(Read("tag_a", 200, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 300, Antenna("Tube1", "Cage1")))
        t.updateFromRead(
            Read("tag_a", 305, Antenna("Tube1", "Cage1"))
        )  # Short (< 10 sec)
        t.updateFromRead(Read("tag_a", 500, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 600, Antenna("Tube1", "Cage1")))
        t.updateFromRead(Read("tag_a", 700, Antenna("Tube1", "Cage1")))  # Long
        t.updateFromRead(Read("tag_a", 800, Antenna("Tube2", "ArenaA")))  # OneMissing
        t.updateFromRead(Read("tag_a", 900, Antenna("Tube2", "Cage2")))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=100, end=100, chamber=None),
                Dwell(start=100, end=200, chamber="ArenaA"),
                Dwell(start=200, end=600, chamber="Tube1"),
                Dwell(start=600, end=700, chamber="Cage1"),
                Dwell(start=700, end=700.001, chamber="Tube1"),
                Dwell(start=700.001, end=800, chamber="ArenaA"),
                Dwell(start=800, end=900, chamber="Tube2"),
            ],
        )

        self.assertEqual(
            dict(t.time_per_chamber(0, 1e100)),
            {
                "ArenaA": 199.99900000000002,
                "Cage1": 100,
                "Tube1": 400.001,
                "Tube2": 100,
            },
        )

    def test_time_per_chamber_restricted(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 100)

        t.updateFromRead(Read("tag_a", 200, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 300, Antenna("Tube1", "Cage1")))
        t.updateFromRead(
            Read("tag_a", 305, Antenna("Tube1", "Cage1"))
        )  # Short (< 10 sec)
        t.updateFromRead(Read("tag_a", 500, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 600, Antenna("Tube1", "Cage1")))
        t.updateFromRead(Read("tag_a", 700, Antenna("Tube1", "Cage1")))  # Long
        t.updateFromRead(Read("tag_a", 800, Antenna("Tube2", "ArenaA")))  # OneMissing
        t.updateFromRead(Read("tag_a", 900, Antenna("Tube2", "Cage2")))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=100, end=100, chamber=None),
                Dwell(start=100, end=200, chamber="ArenaA"),
                Dwell(start=200, end=600, chamber="Tube1"),
                Dwell(start=600, end=700, chamber="Cage1"),
                Dwell(start=700, end=700.001, chamber="Tube1"),
                Dwell(start=700.001, end=800, chamber="ArenaA"),
                Dwell(start=800, end=900, chamber="Tube2"),
            ],
        )

        self.assertEqual(
            dict(t.time_per_chamber(205, 750)),
            {
                "ArenaA": 49.999000000000024,
                "Cage1": 100,
                "Tube1": 395.001,
            },
        )

    def test_get_locations_between(self):
        t = _AnimalTrajectory("tag_a", "ArenaA", 100)

        t.updateFromRead(Read("tag_a", 200, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 300, Antenna("Tube1", "Cage1")))
        t.updateFromRead(
            Read("tag_a", 305, Antenna("Tube1", "Cage1"))
        )  # Short (< 10 sec)
        t.updateFromRead(Read("tag_a", 500, Antenna("Tube1", "ArenaA")))
        t.updateFromRead(Read("tag_a", 600, Antenna("Tube2", "ArenaA")))
        t.updateFromRead(Read("tag_a", 700, Antenna("Tube2", "Cage2")))  
        t.updateFromRead(Read("tag_a", 800, Antenna("Tube2", "Cage2")))  # Long
        t.updateFromRead(Read("tag_a", 900, Antenna("Tube2", "ArenaA")))  # OneMissing
        t.updateFromRead(Read("tag_a", 1000, Antenna("Tube3", "ArenaA")))

        self.assertEqual(t.get_locations_between(0, 1100), ["ArenaA", "Tube1", "ArenaA", "Tube2", "Cage2", "Tube2", "ArenaA"])
        self.assertEqual(t.get_locations_between(150, 750), ["ArenaA", "Tube1", "ArenaA", "Tube2", "Cage2"])
        self.assertEqual(t.get_locations_between(325, 610), ['Tube1', 'ArenaA', 'Tube2'])

 
class TestAllAnimalTrajectories(unittest.TestCase):
    def test_traversals(self):
        start_time = 100
        tag_id_to_start_chamber = {"tag_a": "ArenaA", "tag_b": "ArenaA"}
        reads_per_animal = {
            "tag_a": [
                Read("tag_a", 200, Antenna("Tube2", "ArenaA")),
                Read("tag_a", 400, Antenna("Tube2", "Cage2")),
                Read("tag_a", 600, Antenna("Tube2", "Cage2")),
                Read("tag_a", 800, Antenna("Tube2", "ArenaA")),
                Read("tag_a", 1000, Antenna("Tube4", "ArenaA")),
                Read("tag_a", 1200, Antenna("Tube4", "Cage4")),
            ],
            "tag_b": [
                Read("tag_b", 300, Antenna("Tube3", "ArenaA")),
                Read("tag_b", 500, Antenna("Tube3", "Cage3")),
                Read("tag_b", 700, Antenna("Tube3", "Cage3")),
                Read("tag_b", 900, Antenna("Tube3", "ArenaA")),
                Read("tag_b", 1100, Antenna("Tube5", "ArenaA")),
                Read("tag_b", 1300, Antenna("Tube5", "Cage5")),
            ],
        }

        t = AllAnimalTrajectories(start_time, tag_id_to_start_chamber, reads_per_animal)

        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(timestamp=100, tag_id="tag_a", orig=None, dest="ArenaA"),
                Traversal(timestamp=100, tag_id="tag_b", orig=None, dest="ArenaA"),
                Traversal(timestamp=200, tag_id="tag_a", orig="ArenaA", dest="Tube2"),
                Traversal(timestamp=300, tag_id="tag_b", orig="ArenaA", dest="Tube3"),
                Traversal(timestamp=400, tag_id="tag_a", orig="Tube2", dest="Cage2"),
                Traversal(timestamp=500, tag_id="tag_b", orig="Tube3", dest="Cage3"),
                Traversal(timestamp=600, tag_id="tag_a", orig="Cage2", dest="Tube2"),
                Traversal(timestamp=700, tag_id="tag_b", orig="Cage3", dest="Tube3"),
                Traversal(timestamp=800, tag_id="tag_a", orig="Tube2", dest="ArenaA"),
                Traversal(timestamp=900, tag_id="tag_b", orig="Tube3", dest="ArenaA"),
                Traversal(timestamp=1000, tag_id="tag_a", orig="ArenaA", dest="Tube4"),
                Traversal(timestamp=1100, tag_id="tag_b", orig="ArenaA", dest="Tube5"),
                Traversal(timestamp=1200, tag_id="tag_a", orig="Tube4", dest="Cage4"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
