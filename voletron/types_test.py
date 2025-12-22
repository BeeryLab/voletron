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
from voletron.types import (
    AnimalName,
    Antenna,
    ChamberName,
    CoDwell,
    Config,
    DurationMinutes,
    DurationSeconds,
    Dwell,
    GroupDwellAggregate,
    LongDwell,
    Read,
    TagID,
    TimestampSeconds,
    Traversal,
    Validation,
    chamberBetween,
)

class TestStructs(unittest.TestCase):

    def test_antenna_instantiation(self):
        a = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        self.assertEqual(a.tube, "tube1")
        self.assertEqual(a.cage, "cage1")

    def test_read_instantiation(self):
        a = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        r = Read(tag_id=TagID("tag1"), timestamp=TimestampSeconds(100), antenna=a)
        self.assertEqual(r.tag_id, "tag1")
        self.assertEqual(r.timestamp, 100)
        self.assertEqual(r.antenna, a)

    def test_validation_instantiation(self):
        v = Validation(timestamp=TimestampSeconds(100), tag_id=TagID("tag1"), chamber=ChamberName("cage1"))
        self.assertEqual(v.timestamp, 100)
        self.assertEqual(v.tag_id, "tag1")
        self.assertEqual(v.chamber, "cage1")

    def test_dwell_instantiation(self):
        d = Dwell(start=TimestampSeconds(100), end=TimestampSeconds(200), chamber=ChamberName("cage1"))
        self.assertEqual(d.start, 100)
        self.assertEqual(d.end, 200)
        self.assertEqual(d.chamber, "cage1")

    def test_codwell_instantiation(self):
        cd = CoDwell(tag_ids=[TagID("tag1"), TagID("tag2")], start=TimestampSeconds(100), end=TimestampSeconds(200), chamber=ChamberName("cage1"))
        self.assertEqual(cd.tag_ids, ["tag1", "tag2"])
        self.assertEqual(cd.start, 100)
        self.assertEqual(cd.end, 200)
        self.assertEqual(cd.chamber, "cage1")

    def test_longdwell_instantiation(self):
        ld = LongDwell(tag_id=TagID("tag1"), chamber=ChamberName("cage1"), start_time=TimestampSeconds(100), minutes=DurationMinutes(60))
        self.assertEqual(ld.tag_id, "tag1")
        self.assertEqual(ld.chamber, "cage1")
        self.assertEqual(ld.start_time, 100)
        self.assertEqual(ld.minutes, 60)

    def test_traversal_instantiation(self):
        t = Traversal(timestamp=TimestampSeconds(100), tag_id=TagID("tag1"), orig=ChamberName("cage1"), dest=ChamberName("tube1"))
        self.assertEqual(t.timestamp, 100)
        self.assertEqual(t.tag_id, "tag1")
        self.assertEqual(t.orig, "cage1")
        self.assertEqual(t.dest, "tube1")

    def test_config_instantiation(self):
        c = Config(tag_id_to_name={TagID("tag1"): AnimalName("name1")}, tag_id_to_start_chamber={TagID("tag1"): ChamberName("cage1")})
        self.assertEqual(c.tag_id_to_name[TagID("tag1")], AnimalName("name1"))
        self.assertEqual(c.tag_id_to_start_chamber[TagID("tag1")], ChamberName("cage1"))

    def test_group_dwell_aggregate_instantiation(self):
        gda = GroupDwellAggregate(tag_ids=[TagID("tag1"), TagID("tag2")], chamber=ChamberName("cage1"), count=5, duration_seconds=DurationSeconds(100.0))
        self.assertEqual(gda.tag_ids, ["tag1", "tag2"])
        self.assertEqual(gda.chamber, "cage1")
        self.assertEqual(gda.count, 5)
        self.assertEqual(gda.duration_seconds, 100.0)

    def test_chamber_between_shared_tube(self):
        a1 = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        a2 = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage2"))
        self.assertEqual(chamberBetween(a1, a2), "tube1")

    def test_chamber_between_shared_cage(self):
        a1 = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        a2 = Antenna(tube=ChamberName("tube2"), cage=ChamberName("cage1"))
        self.assertEqual(chamberBetween(a1, a2), "cage1")

    def test_chamber_between_no_shared(self):
        a1 = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        a2 = Antenna(tube=ChamberName("tube2"), cage=ChamberName("cage2"))
        self.assertIsNone(chamberBetween(a1, a2))

    def test_chamber_between_same_antenna(self):
        a1 = Antenna(tube=ChamberName("tube1"), cage=ChamberName("cage1"))
        with self.assertRaisesRegex(ValueError, "There is no chamber between an antenna and itself"):
            chamberBetween(a1, a1)

    def test_chamber_between_multiple_shared(self):
        a1 = Antenna(tube=ChamberName("A"), cage=ChamberName("B"))
        a2 = Antenna(tube=ChamberName("B"), cage=ChamberName("A"))
        with self.assertRaisesRegex(ValueError, "Impossible: There can't be more than one chamber between two antennae"):
            chamberBetween(a1, a2)

if __name__ == '__main__':
    unittest.main()
