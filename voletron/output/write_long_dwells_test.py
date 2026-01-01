
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_long_dwells import compute_long_dwells, write_long_dwells
from voletron.types import Config, TagID, TimestampSeconds, ChamberName, AnimalName
from voletron.trajectory import AllAnimalTrajectories
from voletron.output.types import LongDwellRow, OutputBin

class TestWriteLongDwells(unittest.TestCase):
    def test_compute_long_dwells(self):
        # Setup mocks
        config = MagicMock(spec=Config)
        config.tag_id_to_name = {TagID("tag1"): AnimalName("animal1")}
        
        mock_trajectory = MagicMock()
        # Mock long_dwells to return a list of tuples (tag_id, chamber, start, duration)
        # Note: compute_long_dwells iterates over ALL dwells and filters by bin
        mock_trajectory.long_dwells.return_value = [
            (TagID("tag1"), ChamberName("c1"), TimestampSeconds(5), 10.0),  # In bin 1
            (TagID("tag1"), ChamberName("c2"), TimestampSeconds(15), 20.0), # In bin 2
            (TagID("tag1"), ChamberName("c1"), TimestampSeconds(25), 5.0)   # Outside tested bins?
        ]

        mock_trajectories = MagicMock(spec=AllAnimalTrajectories)
        mock_trajectories.animalTrajectories = {TagID("tag1"): mock_trajectory}

        tag_ids = [TagID("tag1")]
        
        bins = [
            OutputBin(bin_number=1, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(10), analyzer=MagicMock()),
            OutputBin(bin_number=2, bin_start=TimestampSeconds(10), bin_end=TimestampSeconds(20), analyzer=MagicMock()),
            OutputBin(bin_number=0, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(30), analyzer=MagicMock()) # Whole
        ]

        rows = compute_long_dwells(config, tag_ids, mock_trajectories, bins)

        # Expected:
        # Bin 1 (0-10): Dwell starting at 5 should be here.
        # Bin 2 (10-20): Dwell starting at 15 should be here.
        # Bin 3 (0-30): All 3 dwells should be here.
        
        self.assertEqual(len(rows), 1 + 1 + 3)
        
        # Check specific rows
        # We can't guarantee order between bins easily unless we sort, but logic appends in bin order.
        
        # Bin 1
        bin1_rows = [r for r in rows if r.bin_number == 1]
        self.assertEqual(len(bin1_rows), 1)
        self.assertEqual(bin1_rows[0].start_time, 5)
        self.assertEqual(bin1_rows[0].bin_duration, 10.0)
        
        # Bin 2
        bin2_rows = [r for r in rows if r.bin_number == 2]
        self.assertEqual(len(bin2_rows), 1)
        self.assertEqual(bin2_rows[0].start_time, 15)
        self.assertEqual(bin2_rows[0].bin_duration, 10.0)
        
        # Bin 3
        bin3_rows = [r for r in rows if r.bin_number == 0]
        self.assertEqual(len(bin3_rows), 3)
        self.assertEqual(bin3_rows[0].bin_duration, 30.0)

    def test_write_long_dwells(self):
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        
        rows = [
             LongDwellRow(
                bin_number=0,
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                bin_duration=100.0,
                animal_name="a1",
                chamber_name="c1",
                start_time=TimestampSeconds(50),
                duration_seconds=10.0
            )
        ]
        
        write_long_dwells(rows, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.longdwells.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_number,bin_start,bin_end,bin_duration,animal,chamber,start_time,seconds", content)
            self.assertIn("0,0,100,100,a1,c1", content) # partial match

if __name__ == '__main__':
    unittest.main()
