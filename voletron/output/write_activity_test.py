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
from unittest.mock import MagicMock, patch, mock_open
from voletron.output.write_activity import write_activity
from voletron.types import TimestampSeconds, DurationSeconds, TagID, ChamberName, CoDwell
from voletron.trajectory import AllAnimalTrajectories

class TestWriteActivity(unittest.TestCase):
    def test_write_activity(self):
        # Setup mocks
        mock_trajectories = MagicMock(spec=AllAnimalTrajectories)
        mock_trajectories.animalTrajectories = {
            TagID("tag1"): MagicMock()
        }
        # Configure count_traversals_between to return something specific
        mock_trajectories.animalTrajectories[TagID("tag1")].count_traversals_between.return_value = 5

        # Create some CoDwells
        # Two in the first bin (0-300), one in the second (300-600)
        co_dwells = [
            CoDwell([TagID("tag1"), TagID("tag2")], TimestampSeconds(100), TimestampSeconds(200), ChamberName("c1")), # duration 100 in bin 1
            CoDwell([TagID("tag1"), TagID("tag3")], TimestampSeconds(350), TimestampSeconds(400), ChamberName("c2")), # duration 50 in bin 2
        ]

        start_time = TimestampSeconds(0)
        end_time = TimestampSeconds(600)
        bin_size = DurationSeconds(300)

        # Mock open
        m = mock_open()
        with patch("builtins.open", m):
            write_activity(
                out_dir="out",
                exp_name="exp",
                boundary_type="test",
                trajectories=mock_trajectories,
                co_dwells=co_dwells,
                analysis_start_time=start_time,
                analysis_end_time=end_time,
                bin_secs=bin_size
            )

        # Check file calls
        m.assert_called_once_with("out/exp.activity.test.csv", "w")
        handle = m()
        
        # Expected calls:
        # Header
        expected_header = "start_time,end_time,bin_seconds,tag_id,avg_dwell_size_1,avg_dwell_size_2,avg_dwell_size_3,avg_dwell_size_4,traversal_count\n"

        # Bin 1: 0-300. CoDwell {tag1, tag2} for 100s. 
        #   Group size 2: 100s.
        #   Traversals: 5
        # Bin 2: 300-600. CoDwell {tag1, tag3} for 50s.
        #   Group size 2: 50s.
        #   Traversals: 5

        # We construct expected output strings
        # Format: start,end,bin_sec,tag_id,g1_avg,g2_avg,g3_avg,g4_avg,traversals
        # Note: avg_dwells_by_group_size logic in code takes sum(durations) / count??
        # Let's inspect the code logic in write_activity.py:
        # dwells_by_group_size[len(x.tag_ids)].append(x.duration_seconds)
        # avg = sum(xx) / len(xx) if xx else 0.0
        
        # Bin 1 for tag1: 
        # one dwell of 100s, group size 2. avg = 100/1 = 100.0
        # group size 1,3,4 = 0.0
        expected_line_1 = "0,300,300,tag1,0.0,100.0,0.0,0.0,5"
        
        # Bin 2 for tag1:
        # one dwell of 50s, group size 2. avg = 50/1 = 50.0
        expected_line_2 = "300,600,300,tag1,0.0,50.0,0.0,0.0,5"

        # Check write calls. Note that 'write' is called multiple times.
        # We can aggregate all writes or check specific calls.
        
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn(expected_header, written_content)
        self.assertIn(expected_line_1, written_content)
        self.assertIn(expected_line_2, written_content)

if __name__ == '__main__':
    unittest.main()
