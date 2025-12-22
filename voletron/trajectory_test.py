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

from voletron.parse_olcus import parse_raw_line
from voletron.types import Antenna, Dwell, LongDwell, Read, Traversal, CHAMBER_OUTSIDE, CHAMBER_ERROR, TagID, ChamberName, TimestampSeconds, DurationMinutes
from voletron.trajectory import (
    AllAnimalTrajectories,
    ReadFate,
    TwoMissingReadsException,
    _AnimalTrajectory,
    chamberBetween,
    infer_missing_read,
)


class TestTrajectoryUtils(unittest.TestCase):
    def test_chamber_between(self):
        ab = Antenna(ChamberName("ChamberA"), ChamberName("ChamberB"))
        bc = Antenna(ChamberName("ChamberB"), ChamberName("ChamberC"))
        cd = Antenna(ChamberName("ChamberC"), ChamberName("ChamberD"))

        abbc = chamberBetween(ab, bc)
        self.assertEqual(abbc, "ChamberB")

        abcd = chamberBetween(ab, cd)
        self.assertEqual(abcd, None)

        with self.assertRaises(ValueError):
            chamberBetween(ab, ab)

    def test_infer_missing_read_two_missing(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read(TagID("tag_a"), TimestampSeconds(12345), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        readB = Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube3"), ChamberName("Cage3")))

        with self.assertRaises(TwoMissingReadsException):
            infer_missing_read(readA, readB)

    def test_infer_missing_tube_arena(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read(TagID("tag_a"), TimestampSeconds(12345), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        readB = Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube3"), ChamberName("CentralA")))

        inferred = infer_missing_read(readA, readB)
        self.assertEqual(inferred.tag_id, "tag_a")
        self.assertEqual(inferred.timestamp, 12345.001)
        self.assertEqual(inferred.antenna, Antenna(ChamberName("Tube1"), ChamberName("CentralA")))

    def test_infer_missing_arena_tube(self):
        # Note: this depends on the global apparatus_config.all_antennae
        readA = Read(TagID("tag_a"), TimestampSeconds(12345), Antenna(ChamberName("Tube3"), ChamberName("CentralA")))
        readB = Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))

        inferred = infer_missing_read(readA, readB)
        self.assertEqual(inferred.tag_id, "tag_a")
        self.assertEqual(inferred.timestamp, 23455.999)
        self.assertEqual(inferred.antenna, Antenna(ChamberName("Tube1"), ChamberName("CentralA")))


class TestAnimalTrajectory(unittest.TestCase):
    def test_init_dwell(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        readA = Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube1"), ChamberName("CentralA")))
        fate = t.update_from_read(readA)
        self.assertEqual(fate, ReadFate.Move)
        self.assertEqual(
            t.dwells, [Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE), Dwell(TimestampSeconds(12345), TimestampSeconds(23456), ChamberName("CentralA"))]
        )
        # There is one traversal representing the beginning of the experiment
        self.assertEqual(
            list(t.traversals()), [Traversal(TimestampSeconds(12345), TagID("tag_a"), CHAMBER_OUTSIDE, ChamberName("CentralA"))]
        )

        readB = Read(TagID("tag_a"), TimestampSeconds(34567), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        fate = t.update_from_read(readB)
        self.assertEqual(fate, ReadFate.Move)
        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                Dwell(TimestampSeconds(12345), TimestampSeconds(23456), ChamberName("CentralA")),
                Dwell(TimestampSeconds(23456), TimestampSeconds(34567), ChamberName("Tube1")),
            ],
        )
        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(TimestampSeconds(12345), TagID("tag_a"), CHAMBER_OUTSIDE, ChamberName("CentralA")),
                Traversal(TimestampSeconds(23456), TagID("tag_a"), ChamberName("CentralA"), ChamberName("Tube1")),
            ],
        )

    def test_repeated_read_short(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        antenna = Antenna(ChamberName("Tube1"), ChamberName("CentralA"))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23456), antenna))
        fate = t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23460), antenna))
        self.assertEqual(fate, ReadFate.Short_Tube)

        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                Dwell(TimestampSeconds(12345), TimestampSeconds(23456), ChamberName("CentralA")),
                # Short dwell in the tube
                Dwell(TimestampSeconds(23456), TimestampSeconds(23460), ChamberName("Tube1")),
            ],
        )

    def test_repeated_read_long(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        antenna = Antenna(ChamberName("Tube1"), ChamberName("CentralA"))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23456), antenna))
        fate = t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(34567), antenna))
        self.assertEqual(fate, ReadFate.Long_Cage)

        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                # Arena dwell extended
                Dwell(TimestampSeconds(12345), TimestampSeconds(34567), ChamberName("CentralA")),
            ],
        )

    def test_move(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        fate = t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(34567), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        self.assertEqual(fate, ReadFate.Move)

        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                Dwell(TimestampSeconds(12345), TimestampSeconds(23456), ChamberName("CentralA")),
                Dwell(TimestampSeconds(23456), TimestampSeconds(34567), ChamberName("Tube1")),
            ],
        )

    def test_one_missing(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        fate = t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(34567), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))
        self.assertEqual(fate, ReadFate.OneMissing)

        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                # Arena dwell extended
                Dwell(TimestampSeconds(12345), TimestampSeconds(34566.999), ChamberName("CentralA")),
                Dwell(TimestampSeconds(34566.999), TimestampSeconds(34567), ChamberName("Tube2")),
            ],
        )

    def test_two_missing(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(12345))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(23456), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(34567), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        fate = t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(45678), Antenna(ChamberName("Tube3"), ChamberName("Cage3"))))
        self.assertEqual(fate, ReadFate.TwoMissing)

        self.assertEqual(
            t.dwells,
            [
                Dwell(TimestampSeconds(12345), TimestampSeconds(12345), CHAMBER_OUTSIDE),
                # Arena dwell extended
                Dwell(TimestampSeconds(12345), TimestampSeconds(23456), ChamberName("CentralA")),
                Dwell(TimestampSeconds(23456), TimestampSeconds(34567), ChamberName("Tube1")),
                Dwell(TimestampSeconds(34567), TimestampSeconds(45678), CHAMBER_ERROR),
            ],
        )

    def test_traversals(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(100))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(
            Read(TagID("tag_a"), TimestampSeconds(305), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        )  # Short (< 10 sec)
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(500), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(600), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(700), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))  # Long
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(800), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))))  # OneMissing
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(900), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))

        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(timestamp=TimestampSeconds(100), tag_id=TagID("tag_a"), orig=CHAMBER_OUTSIDE, dest=ChamberName("CentralA")),
                Traversal(timestamp=TimestampSeconds(200), tag_id=TagID("tag_a"), orig=ChamberName("CentralA"), dest=ChamberName("Tube1")),
                # ...bouncing around in the tube...
                Traversal(timestamp=TimestampSeconds(600), tag_id=TagID("tag_a"), orig=ChamberName("Tube1"), dest=ChamberName("Cage1")),
                Traversal(timestamp=TimestampSeconds(700), tag_id=TagID("tag_a"), orig=ChamberName("Cage1"), dest=ChamberName("Tube1")),
                Traversal(
                    timestamp=TimestampSeconds(700.001),
                    tag_id=TagID("tag_a"),
                    orig=ChamberName("Tube1"),
                    dest=ChamberName("CentralA"),  # inserted missing read, allocating time to the arena
                ),
                Traversal(timestamp=TimestampSeconds(800), tag_id=TagID("tag_a"), orig=ChamberName("CentralA"), dest=ChamberName("Tube2"))
                # Read at 900 does not indicate a traversal (lacking a subsequent read)
            ],
        )

    def test_long_dwells(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(100))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(30300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))  # Very Long
        t.update_from_read(
            Read(TagID("tag_a"), TimestampSeconds(90300.001), Antenna(ChamberName("Tube2"), ChamberName("CentralA")))
        )  # OneMissing, very long in the arena, with extra 1 ms for missing read
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(100000), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(100), chamber=CHAMBER_OUTSIDE),
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(200), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(200), end=TimestampSeconds(300), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(300), end=TimestampSeconds(30300), chamber=ChamberName("Cage1")),
                Dwell(start=TimestampSeconds(30300), end=TimestampSeconds(30300.001), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(30300.001), end=TimestampSeconds(90300.001), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(90300.001), end=TimestampSeconds(100000), chamber=ChamberName("Tube2")),
            ],
        )

        # which of those are "very long"?
        self.assertEqual(
            list(t.long_dwells()),
            [
                LongDwell(TagID("tag_a"), ChamberName("Cage1"), TimestampSeconds(300), DurationMinutes(500.0)),  # 500 sec in cage 1
                LongDwell(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(30300.001), DurationMinutes(1000)),  # 1000 sec in the arena
            ],
        )

    def test_time_per_chamber_unrestricted(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(100))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(
            Read(TagID("tag_a"), TimestampSeconds(305), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        )  # Short (< 10 sec)
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(500), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(600), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(700), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))  # Long
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(800), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))))  # OneMissing
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(900), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(100), chamber=CHAMBER_OUTSIDE),
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(200), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(200), end=TimestampSeconds(600), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(600), end=TimestampSeconds(700), chamber=ChamberName("Cage1")),
                Dwell(start=TimestampSeconds(700), end=TimestampSeconds(700.001), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(700.001), end=TimestampSeconds(800), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(800), end=TimestampSeconds(900), chamber=ChamberName("Tube2")),
            ],
        )

        self.assertEqual(
            dict(t.time_per_chamber(TimestampSeconds(0), TimestampSeconds(1e100))),
            {
                "CentralA": 199.99900000000002,
                "Cage1": 100,
                "Tube1": 400.001,
                "Tube2": 100,
            },
        )

    def test_time_per_chamber_restricted(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(100))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(
            Read(TagID("tag_a"), TimestampSeconds(305), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        )  # Short (< 10 sec)
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(500), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(600), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(700), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))  # Long
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(800), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))))  # OneMissing
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(900), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))

        # first confirm all dwells
        self.assertEqual(
            t.dwells,
            [
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(100), chamber=CHAMBER_OUTSIDE),
                Dwell(start=TimestampSeconds(100), end=TimestampSeconds(200), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(200), end=TimestampSeconds(600), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(600), end=TimestampSeconds(700), chamber=ChamberName("Cage1")),
                Dwell(start=TimestampSeconds(700), end=TimestampSeconds(700.001), chamber=ChamberName("Tube1")),
                Dwell(start=TimestampSeconds(700.001), end=TimestampSeconds(800), chamber=ChamberName("CentralA")),
                Dwell(start=TimestampSeconds(800), end=TimestampSeconds(900), chamber=ChamberName("Tube2")),
            ],
        )

        self.assertEqual(
            dict(t.time_per_chamber(TimestampSeconds(205), TimestampSeconds(750))),
            {
                "CentralA": 49.999000000000024,
                "Cage1": 100,
                "Tube1": 395.001,
            },
        )

    def test_get_locations_between(self):
        t = _AnimalTrajectory(TagID("tag_a"), ChamberName("CentralA"), TimestampSeconds(100))

        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube1"), ChamberName("Cage1"))))
        t.update_from_read(
            Read(TagID("tag_a"), TimestampSeconds(305), Antenna(ChamberName("Tube1"), ChamberName("Cage1")))
        )  # Short (< 10 sec)
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(500), Antenna(ChamberName("Tube1"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(600), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))))
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(700), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))  
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(800), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))))  # Long
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(900), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))))  # OneMissing
        t.update_from_read(Read(TagID("tag_a"), TimestampSeconds(1000), Antenna(ChamberName("Tube3"), ChamberName("CentralA"))))

        self.assertEqual(t.get_locations_between(TimestampSeconds(0), TimestampSeconds(1100)), ["CentralA", "Tube1", "CentralA", "Tube2", "Cage2", "Tube2", "CentralA"])
        self.assertEqual(t.get_locations_between(TimestampSeconds(150), TimestampSeconds(750)), ["CentralA", "Tube1", "CentralA", "Tube2", "Cage2"])
        self.assertEqual(t.get_locations_between(TimestampSeconds(325), TimestampSeconds(610)), ['Tube1', 'CentralA', 'Tube2'])

 
class TestAllAnimalTrajectories(unittest.TestCase):
    def test_traversals(self):
        start_time = TimestampSeconds(100)
        tag_id_to_start_chamber = {TagID("tag_a"): ChamberName("CentralA"), TagID("tag_b"): ChamberName("CentralA")}
        reads_per_animal = {
            TagID("tag_a"): [
                Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(400), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                Read(TagID("tag_a"), TimestampSeconds(600), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                Read(TagID("tag_a"), TimestampSeconds(800), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(1000), Antenna(ChamberName("Tube4"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(1200), Antenna(ChamberName("Tube4"), ChamberName("Cage4"))),
            ],
            TagID("tag_b"): [
                Read(TagID("tag_b"), TimestampSeconds(300), Antenna(ChamberName("Tube3"), ChamberName("CentralA"))),
                Read(TagID("tag_b"), TimestampSeconds(500), Antenna(ChamberName("Tube3"), ChamberName("Cage3"))),
                Read(TagID("tag_b"), TimestampSeconds(700), Antenna(ChamberName("Tube3"), ChamberName("Cage3"))),
                Read(TagID("tag_b"), TimestampSeconds(900), Antenna(ChamberName("Tube3"), ChamberName("CentralA"))),
                Read(TagID("tag_b"), TimestampSeconds(1100), Antenna(ChamberName("Tube5"), ChamberName("CentralA"))),
                Read(TagID("tag_b"), TimestampSeconds(1300), Antenna(ChamberName("Tube5"), ChamberName("Cage5"))),
            ],
        }

        t = AllAnimalTrajectories(start_time, tag_id_to_start_chamber, reads_per_animal)

        self.assertEqual(
            list(t.traversals()),
            [
                Traversal(timestamp=TimestampSeconds(100), tag_id=TagID("tag_a"), orig=CHAMBER_OUTSIDE, dest=ChamberName("CentralA")),
                Traversal(timestamp=TimestampSeconds(100), tag_id=TagID("tag_b"), orig=CHAMBER_OUTSIDE, dest=ChamberName("CentralA")),
                Traversal(timestamp=TimestampSeconds(200), tag_id=TagID("tag_a"), orig=ChamberName("CentralA"), dest=ChamberName("Tube2")),
                Traversal(timestamp=TimestampSeconds(300), tag_id=TagID("tag_b"), orig=ChamberName("CentralA"), dest=ChamberName("Tube3")),
                Traversal(timestamp=TimestampSeconds(400), tag_id=TagID("tag_a"), orig=ChamberName("Tube2"), dest=ChamberName("Cage2")),
                Traversal(timestamp=TimestampSeconds(500), tag_id=TagID("tag_b"), orig=ChamberName("Tube3"), dest=ChamberName("Cage3")),
                Traversal(timestamp=TimestampSeconds(600), tag_id=TagID("tag_a"), orig=ChamberName("Cage2"), dest=ChamberName("Tube2")),
                Traversal(timestamp=TimestampSeconds(700), tag_id=TagID("tag_b"), orig=ChamberName("Cage3"), dest=ChamberName("Tube3")),
                Traversal(timestamp=TimestampSeconds(800), tag_id=TagID("tag_a"), orig=ChamberName("Tube2"), dest=ChamberName("CentralA")),
                Traversal(timestamp=TimestampSeconds(900), tag_id=TagID("tag_b"), orig=ChamberName("Tube3"), dest=ChamberName("CentralA")),
                Traversal(timestamp=TimestampSeconds(1000), tag_id=TagID("tag_a"), orig=ChamberName("CentralA"), dest=ChamberName("Tube4")),
                Traversal(timestamp=TimestampSeconds(1100), tag_id=TagID("tag_b"), orig=ChamberName("CentralA"), dest=ChamberName("Tube5")),
                Traversal(timestamp=TimestampSeconds(1200), tag_id=TagID("tag_a"), orig=ChamberName("Tube4"), dest=ChamberName("Cage4")),
            ],
        )


if __name__ == "__main__":
    unittest.main()
