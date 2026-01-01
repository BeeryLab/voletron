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


import os
import unittest
import tempfile
from unittest.mock import MagicMock

from voletron.output.write_group_sizes import write_group_sizes, compute_group_sizes
from voletron.co_dwell_accumulator import CoDwellAccumulator
from voletron.time_span_analyzer import TimeSpanAnalyzer
from voletron.types import AnimalName, ChamberName, TagID, TimestampSeconds, Traversal, DurationSeconds
from voletron.output.types import OutputBin

# TODO write all the tests


class TestWriteGroupSizes(unittest.TestCase):
    def test_group_sizes_nosolo_never(self):
        tag_ids = [TagID('foo'), TagID('bar')]
        out_dir = tempfile.mkdtemp()
        exp_name = "test"
        analysis_start_time = TimestampSeconds(100)
        analysis_end_time = TimestampSeconds(200)
        tag_id_to_name = {TagID('foo'): AnimalName('foo_name'), TagID('bar'): AnimalName('bar_name')}
        tag_id_to_start_chamber : dict[TagID, ChamberName] = {TagID('foo'): ChamberName('chamber_1'), TagID('bar'): ChamberName('chamber_2')}
        bin_seconds = DurationSeconds(300) # Whole experiment is smaller than one bin

        # Animals foo and bar start in chambers 1 and 2, and never move, so
        # they're always alone.
        traversals = []

        state = CoDwellAccumulator(analysis_start_time, tag_id_to_start_chamber, [ChamberName("chamber_1"), ChamberName("chamber_2")])
        for t in traversals:
            state.update_state_from_traversal(t)
        bin_start = TimestampSeconds(0)
        bin_end = TimestampSeconds(100)
        mock_analyzer = MagicMock()
        # We need to mock get_group_chamber_exclusive_durations because that's what compute_group_sizes uses now.
        # It aggregates durations per group size.
        # Logic:
        # tag_id_group_size_seconds[tag_id][len(group_dwell.tag_ids)] += duration
        
        # We want foo to have size 1 (50s) and size 2 (50s)
        # We want bar to have size 2 (50s) and size 3 (50s)
        
        dwells = []
        # Foo alone (size 1)
        dwells.append(MagicMock(tag_ids=[TagID("foo")], duration_seconds=100.0))
        # Bar alone (size 1)
        dwells.append(MagicMock(tag_ids=[TagID("bar")], duration_seconds=100.0))
        
        mock_analyzer.get_group_chamber_exclusive_durations.return_value = dwells
        mock_analyzer.duration = 100.0
        
        bins = [OutputBin(start=bin_start, end=bin_end, analyzer=mock_analyzer)]

        rows = compute_group_sizes(
            tag_ids, 
            tag_id_to_name,
            bins
        )
        
        # bin_start,bin_end,animal,1,2,3,4,5,6,7,8,avg_group_size,avg_group_size_nosolo,sum_pair_time,bin_duration)
        write_group_sizes(rows, out_dir, exp_name)

        with open(os.path.join(out_dir, exp_name + ".group_size.csv"), "r") as f:
            f.readline()
            foo_line = f.readline()
            self.assertEqual(foo_line.split(',')[12], "N/A")
            bar_line = f.readline()
            self.assertEqual(bar_line.split(',')[12], "N/A")


if __name__ == "__main__":
    unittest.main()
