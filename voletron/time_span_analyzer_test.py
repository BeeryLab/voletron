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
from voletron.time_span_analyzer import TimeSpanAnalyzer, _restrict_co_dwell
from voletron.types import CoDwell, TagID, ChamberName, TimestampSeconds, GroupDwellAggregate, DurationSeconds

class TestTimeSpanAnalyzer(unittest.TestCase):
    def test_restrict_co_dwell_inside(self):
        cd = CoDwell([TagID("a"), TagID("b")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1"))
        restricted = _restrict_co_dwell(cd, TimestampSeconds(50), TimestampSeconds(250))
        self.assertEqual(restricted, cd)

    def test_restrict_co_dwell_clipped(self):
        cd = CoDwell([TagID("a"), TagID("b")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1"))
        restricted = _restrict_co_dwell(cd, TimestampSeconds(150), TimestampSeconds(180))
        self.assertEqual(restricted.start, 150)
        self.assertEqual(restricted.end, 180)

    def test_restrict_co_dwell_clipped_start(self):
        # Dwell starts before analysis window (50 < 100) but ends inside (150 < 200)
        cd = CoDwell([TagID("a"), TagID("b")], TimestampSeconds(50), TimestampSeconds(150), ChamberName("c1"))
        restricted = _restrict_co_dwell(cd, TimestampSeconds(100), TimestampSeconds(200))
        self.assertEqual(restricted.start, 100)
        self.assertEqual(restricted.end, 150)

    def test_restrict_co_dwell_clipped_end(self):
        # Dwell starts inside (150 > 100) but ends after analysis window (250 > 200)
        cd = CoDwell([TagID("a"), TagID("b")], TimestampSeconds(150), TimestampSeconds(250), ChamberName("c1"))
        restricted = _restrict_co_dwell(cd, TimestampSeconds(100), TimestampSeconds(200))
        self.assertEqual(restricted.start, 150)
        self.assertEqual(restricted.end, 200)

    def test_restrict_co_dwell_outside(self):
        cd = CoDwell([TagID("a"), TagID("b")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1"))
        restricted = _restrict_co_dwell(cd, TimestampSeconds(300), TimestampSeconds(400))
        self.assertIsNone(restricted)

    def test_get_group_chamber_exclusive_durations(self):
        # A+B in c1 for 100s
        # A+B in c1 for 50s
        # A+C in c2 for 10s
        co_dwells = [
            CoDwell([TagID("a"), TagID("b")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1")),
            CoDwell([TagID("a"), TagID("b")], TimestampSeconds(300), TimestampSeconds(350), ChamberName("c1")),
            CoDwell([TagID("a"), TagID("c")], TimestampSeconds(400), TimestampSeconds(410), ChamberName("c2")),
        ]
        analyzer = TimeSpanAnalyzer(co_dwells, TimestampSeconds(0), TimestampSeconds(1000))
        stats = analyzer.get_group_chamber_exclusive_durations()
        
        # We expect two aggregates: {a,b} in c1, and {a,c} in c2
        self.assertEqual(len(stats), 2)
        
        ab_stats = [s for s in stats if set(s.tag_ids) == {"a", "b"}][0]
        self.assertEqual(ab_stats.chamber, "c1")
        self.assertEqual(ab_stats.count, 2)
        self.assertEqual(ab_stats.duration_seconds, 150.0)

        ac_stats = [s for s in stats if set(s.tag_ids) == {"a", "c"}][0]
        self.assertEqual(ac_stats.chamber, "c2")
        self.assertEqual(ac_stats.count, 1)
        self.assertEqual(ac_stats.duration_seconds, 10.0)

    def test_get_pair_inclusive_stats(self):
        # A+B+C in c1 for 100s
        # This implies inclusive pairs: {A,B}, {B,C}, {A,C} all have 100s
        co_dwells = [
            CoDwell([TagID("a"), TagID("b"), TagID("c")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1")),
        ]
        analyzer = TimeSpanAnalyzer(co_dwells, TimestampSeconds(0), TimestampSeconds(1000))
        stats = analyzer.get_pair_inclusive_stats()

        self.assertEqual(len(stats), 3)
        self.assertTrue(all(s.chamber == "All" for s in stats))
        self.assertTrue(all(s.duration_seconds == 100.0 for s in stats))
        
        pair_sets = [set(s.tag_ids) for s in stats]
        self.assertIn({"a", "b"}, pair_sets)
        self.assertIn({"b", "c"}, pair_sets)
        self.assertIn({"a", "c"}, pair_sets)

if __name__ == '__main__':
    unittest.main()
