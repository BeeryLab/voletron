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


import unittest
from unittest.mock import MagicMock
from voletron.output.write_group_sizes import compute_group_sizes
from voletron.types import AnimalName, TagID, TimestampSeconds
from voletron.output.types import OutputBin

class TestComputeGroupSizes(unittest.TestCase):
    def setUp(self):
        self.tag_id = TagID('foo')
        self.tag_ids = [self.tag_id]
        self.tag_id_to_name = {self.tag_id: AnimalName('foo_name')}

    def _create_mock_bin(self, bin_number, start, end, durations):
        """
        durations: list of (tag_ids, duration_seconds) tuples
        """
        mock_analyzer = MagicMock()
        mock_analyzer.duration = float(end - start)
        
        dwells = []
        for tags, duration in durations:
            dwell = MagicMock()
            dwell.tag_ids = tags
            dwell.duration_seconds = float(duration)
            dwells.append(dwell)
            
        mock_analyzer.get_group_chamber_exclusive_durations.return_value = dwells
        return OutputBin(bin_number=bin_number, bin_start=start, bin_end=end, analyzer=mock_analyzer)

    def test_solo_scenario(self):
        # Animal 'foo' is always alone for 100 seconds
        bin = self._create_mock_bin(1, TimestampSeconds(0), TimestampSeconds(100), [
            ([TagID('foo')], 100.0)
        ])
        
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin])
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.animal_name, "foo_name")
        self.assertEqual(row.avg_group_size, 1.0)
        self.assertEqual(row.avg_group_size_nosolo, "N/A")
        self.assertEqual(row.size_seconds[1], 100.0)
        self.assertEqual(row.size_seconds[2], 0.0)

    def test_pair_scenario(self):
        # Animal 'foo' is always in a pair for 100 seconds
        bin = self._create_mock_bin(1, TimestampSeconds(0), TimestampSeconds(100), [
            ([TagID('foo'), TagID('bar')], 100.0)
        ])
        
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin])
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.avg_group_size, 2.0)
        self.assertEqual(row.avg_group_size_nosolo, 2.0)
        self.assertEqual(row.size_seconds[1], 0.0)
        self.assertEqual(row.size_seconds[2], 100.0)

    def test_mixed_scenario(self):
        # Animal 'foo' spends 40s alone, 60s in a trio (group size 3)
        # avg_group_size = (1*40 + 3*60) / 100 = (40 + 180) / 100 = 2.2
        # avg_group_size_nosolo = (3*60) / 60 = 3.0
        bin = self._create_mock_bin(1, TimestampSeconds(0), TimestampSeconds(100), [
            ([TagID('foo')], 40.0),
            ([TagID('foo'), TagID('bar'), TagID('baz')], 60.0)
        ])
        
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin])
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertAlmostEqual(row.avg_group_size, 2.2)
        self.assertAlmostEqual(row.avg_group_size_nosolo, 3.0)
        self.assertEqual(row.size_seconds[1], 40.0)
        self.assertEqual(row.size_seconds[3], 60.0)

    def test_multiple_bins(self):
        # Bin 1: Always alone
        # Bin 2: Always in pair
        bin1 = self._create_mock_bin(1, TimestampSeconds(0), TimestampSeconds(100), [([TagID('foo')], 100.0)])
        bin2 = self._create_mock_bin(2, TimestampSeconds(100), TimestampSeconds(200), [([TagID('foo'), TagID('bar')], 100.0)])
        
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin1, bin2])
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].bin_number, 1)
        self.assertEqual(rows[0].avg_group_size, 1.0)
        self.assertEqual(rows[1].bin_number, 2)
        self.assertEqual(rows[1].avg_group_size, 2.0)

    def test_empty_bin(self):
        # Duration 0
        bin = self._create_mock_bin(1, TimestampSeconds(100), TimestampSeconds(100), [])
        
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin])
        
        # If duration is 0, we still get an entry if it exists in tag_id_group_size_seconds?
        # Actually, tag_id_group_size_seconds is populated from analyzer.get_group_chamber_exclusive_durations()
        # If there are no dwells, the animal won't appear in rows.
        self.assertEqual(len(rows), 0)

    def test_duration_zero_safe(self):
        # Explicitly test the duration == 0 check in compute_group_sizes
        bin = self._create_mock_bin(1, TimestampSeconds(100), TimestampSeconds(100), [([TagID('foo')], 0.0)])
        rows = compute_group_sizes(self.tag_ids, self.tag_id_to_name, [bin])
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].avg_group_size, 0.0)

if __name__ == "__main__":
    unittest.main()
