
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_group_chamber_cohabs import compute_group_chamber_cohabs, write_group_chamber_cohabs
from voletron.types import Config, TagID, TimestampSeconds, ChamberName, AnimalName, CoDwell
from voletron.output.types import GroupChamberCohabRow, OutputBin

class TestWriteGroupChamberCohabs(unittest.TestCase):
    def test_compute_group_chamber_cohabs(self):
        # Setup mocks
        tag_id_to_name = {
            TagID("tag1"): AnimalName("animal1"),
            TagID("tag2"): AnimalName("animal2")
        }
        
        # CoDwells
        # Tag1 and Tag2 together in c1 from 5 to 15.
        co_dwells = [
            CoDwell(
                tag_ids=frozenset([TagID("tag1"), TagID("tag2")]),
                start=TimestampSeconds(5),
                end=TimestampSeconds(15),
                chamber=ChamberName("c1")
            )
        ]
        
        # Mocks
        mock_analyzer_1 = MagicMock()
        mock_analyzer_1.get_group_chamber_exclusive_durations.return_value = [
            MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], chamber=ChamberName("c1"), count=1, duration_seconds=5.0)
        ]
        mock_analyzer_1.duration = 10.0
        
        mock_analyzer_2 = MagicMock()
        mock_analyzer_2.get_group_chamber_exclusive_durations.return_value = [
            MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], chamber=ChamberName("c1"), count=1, duration_seconds=5.0)
        ]
        mock_analyzer_2.duration = 10.0
        
        mock_analyzer_3 = MagicMock()
        mock_analyzer_3.get_group_chamber_exclusive_durations.return_value = [
            MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], chamber=ChamberName("c1"), count=1, duration_seconds=10.0)
        ]
        mock_analyzer_3.duration = 20.0 # Wait, Bin 3 was 0-20?
        
        bins = [
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(10), analyzer=mock_analyzer_1),
            OutputBin(start=TimestampSeconds(10), end=TimestampSeconds(20), analyzer=mock_analyzer_2),
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(20), analyzer=mock_analyzer_3)
        ]

        tag_ids = [TagID("tag1"), TagID("tag2")]

        rows = compute_group_chamber_cohabs(tag_ids, tag_id_to_name, bins)

        # Expected same as pair cohabs basically but different row structure
        self.assertEqual(len(rows), 3)
        
        # Bin 1
        r1 = rows[0]
        self.assertEqual(r1.bin_start, 0)
        self.assertEqual(r1.duration_seconds, 5.0)
        self.assertEqual(r1.chamber_name, "c1")
        self.assertEqual(r1.animal_names, ["animal1", "animal2"])

        # Bin 2
        r2 = rows[1]
        self.assertEqual(r2.bin_start, 10)
        self.assertEqual(r2.duration_seconds, 5.0)

        # Bin 3
        r3 = rows[2]
        self.assertEqual(r3.bin_start, 0)
        self.assertEqual(r3.duration_seconds, 10.0)

    def test_write_group_chamber_cohabs(self):
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        
        rows = [
             GroupChamberCohabRow(
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                animal_names=["a1", "a2"],
                chamber_name="c1",
                dwell_count=1,
                duration_seconds=10.0,
                bin_duration=100.0
            )
        ]
        
        write_group_chamber_cohabs(rows, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.group_chamber_cohab.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_start,bin_end,animals,chamber,dwells,seconds,bin_duration", content)
            self.assertIn('0,100,a1 a2,c1,1,10,100', content)

if __name__ == '__main__':
    unittest.main()
