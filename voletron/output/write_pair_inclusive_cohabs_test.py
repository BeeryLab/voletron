
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_pair_inclusive_cohabs import compute_pair_inclusive_cohabs, write_pair_inclusive_cohabs
from voletron.types import TagID, TimestampSeconds, ChamberName, AnimalName, AnimalConfig
from voletron.output.types import PairCohabRow, OutputBin

class TestWritePairInclusiveCohabs(unittest.TestCase):
    def test_compute_pair_inclusive_cohabs(self):
        # Setup mocks
        config = MagicMock(spec=AnimalConfig)
        config.tag_id_to_name = {
            TagID("tag1"): AnimalName("animal1"),
            TagID("tag2"): AnimalName("animal2")
        }
        

        
        # Mocks for analyzers
        # Bin 1
        mock_analyzer_1 = MagicMock()
        mock_analyzer_1.get_pair_inclusive_stats.return_value = [
            MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], count=1, duration_seconds=5.0)
        ]
        mock_analyzer_1.duration = 10.0
        
        # Bin 2
        mock_analyzer_2 = MagicMock()
        mock_analyzer_2.get_pair_inclusive_stats.return_value = [
            MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], count=1, duration_seconds=5.0)
        ]
        mock_analyzer_2.duration = 10.0
        
        # Bin 3
        mock_analyzer_3 = MagicMock()
        mock_analyzer_3.get_pair_inclusive_stats.return_value = [
             MagicMock(tag_ids=[TagID("tag1"), TagID("tag2")], count=1, duration_seconds=10.0)
        ]
        mock_analyzer_3.duration = 20.0
        
        bins = [
            OutputBin(bin_number=1, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(10), analyzer=mock_analyzer_1),
            OutputBin(bin_number=2, bin_start=TimestampSeconds(10), bin_end=TimestampSeconds(20), analyzer=mock_analyzer_2),
            OutputBin(bin_number=0, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(20), analyzer=mock_analyzer_3)
        ]

        tag_ids = [TagID("tag1"), TagID("tag2")]
        rows = compute_pair_inclusive_cohabs(config, tag_ids, bins)

        # Bin 1 (0-10): Overlap is 5 to 10. Duration 5.
        # Bin 2 (10-20): Overlap is 10 to 15. Duration 5.
        # Bin 3 (0-20): Overlap is 5 to 15. Duration 10.
        
        self.assertEqual(len(rows), 3)
        
        # Bin 1
        r1 = rows[0]
        self.assertEqual(r1.bin_number, 1)
        self.assertEqual(r1.bin_start, 0)
        self.assertEqual(r1.duration_seconds, 5.0)
        self.assertEqual(r1.bin_duration, 10.0)
        self.assertEqual(r1.animal_a_name, "animal1")
        self.assertEqual(r1.animal_b_name, "animal2")

        # Bin 2
        r2 = rows[1]
        self.assertEqual(r2.bin_number, 2)
        self.assertEqual(r2.bin_start, 10)
        self.assertEqual(r2.duration_seconds, 5.0)
        self.assertEqual(r2.bin_duration, 10.0)

        # Bin 3
        r3 = rows[2]
        self.assertEqual(r3.bin_number, 0)
        self.assertEqual(r3.bin_start, 0)
        self.assertEqual(r3.duration_seconds, 10.0)
        self.assertEqual(r3.bin_duration, 20.0)

    def test_write_pair_inclusive_cohabs(self):
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        
        rows = [
             PairCohabRow(
                bin_number=0,
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                bin_duration=100.0,
                animal_a_name="a1",
                animal_b_name="a2",
                dwell_count=1,
                duration_seconds=10.0,
            )
        ]
        
        write_pair_inclusive_cohabs(rows, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.pair-inclusive.cohab.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_number,bin_start,bin_end,bin_duration,Animal A,Animal B,dwells,seconds", content)
            self.assertIn("0,0,100,100,a1,a2,1,10", content)

if __name__ == '__main__':
    unittest.main()
