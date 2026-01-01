
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_chamber_times import compute_chamber_times, write_chamber_times
from voletron.types import Config, TagID, TimestampSeconds, ChamberName, AnimalName, DurationSeconds
from voletron.output.types import OutputBin
from voletron.trajectory import AllAnimalTrajectories

class TestWriteChamberTimes(unittest.TestCase):
    def test_compute_chamber_times(self):
        # Setup mocks
        config = MagicMock(spec=Config)
        config.tag_id_to_name = {TagID("tag1"): AnimalName("animal1")}
        
        mock_trajectory = MagicMock()
        # Mock time_per_chamber to return specific values
        # This needs to be dynamic based on inputs if we want rigorous testing,
        # but for unit testing the wiring, return_value or side_effect is okay.
        
        # Let's use side_effect to return different values for different bins
        def time_per_chamber_side_effect(start, end):
            if start == TimestampSeconds(0) and end == TimestampSeconds(10):
                return {ChamberName("c1"): 5.0, ChamberName("c2"): 5.0}
            elif start == TimestampSeconds(10) and end == TimestampSeconds(20):
                return {ChamberName("c1"): 10.0}
            elif start == TimestampSeconds(0) and end == TimestampSeconds(20): # Whole experiment
                 return {ChamberName("c1"): 15.0, ChamberName("c2"): 5.0}   
            return {}

        mock_trajectory.time_per_chamber.side_effect = time_per_chamber_side_effect

        mock_trajectories = MagicMock(spec=AllAnimalTrajectories)
        mock_trajectories.animalTrajectories = {TagID("tag1"): mock_trajectory}

        tag_ids = [TagID("tag1")]
        
        bins = [
            OutputBin(bin_number=1, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(10), analyzer=MagicMock()),
            OutputBin(bin_number=2, bin_start=TimestampSeconds(10), bin_end=TimestampSeconds(20), analyzer=MagicMock()),
            OutputBin(bin_number=0, bin_start=TimestampSeconds(0), bin_end=TimestampSeconds(20), analyzer=MagicMock())
        ]

        rows = compute_chamber_times(config, tag_ids, mock_trajectories, bins)

        self.assertEqual(len(rows), 3)
        
        # Row 1 (Bin 1)
        self.assertEqual(rows[0].bin_number, 1)
        self.assertEqual(rows[0].bin_start, 0)
        self.assertEqual(rows[0].bin_end, 10)
        self.assertEqual(rows[0].bin_duration, 10.0)
        self.assertEqual(rows[0].animal_name, "animal1")
        self.assertEqual(rows[0].chamber_times[ChamberName("c1")], 5.0)
        self.assertEqual(rows[0].total_time, 10.0)

        # Row 2 (Bin 2)
        self.assertEqual(rows[1].bin_number, 2)
        self.assertEqual(rows[1].bin_start, 10)
        self.assertEqual(rows[1].bin_end, 20)
        self.assertEqual(rows[1].bin_duration, 10.0)
        self.assertEqual(rows[1].chamber_times[ChamberName("c1")], 10.0)
        
        # Row 3 (Whole)
        self.assertEqual(rows[2].bin_number, 0)
        self.assertEqual(rows[2].bin_start, 0)
        self.assertEqual(rows[2].bin_end, 20)
        self.assertEqual(rows[2].bin_duration, 20.0)
        self.assertEqual(rows[2].total_time, 20.0)

    def test_write_chamber_times(self):
        # Very basic write test
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        chambers = [ChamberName("c1"), ChamberName("c2")]
        
        # Create dummy rows
        # We need to import ChamberTimeRow, but it's not exported by write_chamber_times directly usually,
        # but compute_chamber_times returns them.
        # Actually it is imported in write_chamber_times.py
        from voletron.output.types import ChamberTimeRow, OutputBin
        
        rows = [
             ChamberTimeRow(
                bin_number=0,
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                bin_duration=100.0,
                animal_name="a1",
                chamber_times={ChamberName("c1"): 50.0},
                total_time=50.0
            )
        ]
        
        write_chamber_times(rows, chambers, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.chambers.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_number,bin_start,bin_end,bin_duration,animal,c1,c2,total", content)
            self.assertIn("0,0,100,100,a1,50,0,50", content)


if __name__ == '__main__':
    unittest.main()
