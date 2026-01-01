
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_pair_inclusive_cohabs import compute_pair_inclusive_cohabs, write_pair_inclusive_cohabs
from voletron.types import Config, TagID, TimestampSeconds, ChamberName, AnimalName, CoDwell
from voletron.output.types import PairCohabRow, OutputBin

class TestWritePairInclusiveCohabs(unittest.TestCase):
    def test_compute_pair_inclusive_cohabs(self):
        # Setup mocks
        config = MagicMock(spec=Config)
        config.tag_id_to_name = {
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
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(10), analyzer=mock_analyzer_1),
            OutputBin(start=TimestampSeconds(10), end=TimestampSeconds(20), analyzer=mock_analyzer_2),
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(20), analyzer=mock_analyzer_3)
        ]

        rows = compute_pair_inclusive_cohabs(config, bins)

        # Bin 1 (0-10): Overlap is 5 to 10. Duration 5.
        # Bin 2 (10-20): Overlap is 10 to 15. Duration 5.
        # Bin 3 (0-20): Overlap is 5 to 15. Duration 10.
        
        self.assertEqual(len(rows), 3)
        
        # Bin 1
        r1 = rows[0]
        self.assertEqual(r1.bin_start, 0)
        self.assertEqual(r1.duration_seconds, 5.0)
        self.assertEqual(r1.animal_a_name, "animal1")
        self.assertEqual(r1.animal_b_name, "animal2")

        # Bin 2
        r2 = rows[1]
        self.assertEqual(r2.bin_start, 10)
        self.assertEqual(r2.duration_seconds, 5.0)

        # Bin 3
        r3 = rows[2]
        self.assertEqual(r3.bin_start, 0)
        self.assertEqual(r3.duration_seconds, 10.0)

    def test_write_pair_inclusive_cohabs(self):
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        
        rows = [
             PairCohabRow(
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                animal_a_name="a1",
                animal_b_name="a2",
                dwell_count=1,
                duration_seconds=10.0,
                bin_duration=100.0
            )
        ]
        
        write_pair_inclusive_cohabs(rows, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.pair-inclusive.cohab.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_start,bin_end,Animal A,Animal B,dwells,seconds,bin_duration", content)
            self.assertIn("0,100,a1,a2,1,10,100", content)

if __name__ == '__main__':
    unittest.main()
