
import unittest
import tempfile
import os
from unittest.mock import MagicMock
from voletron.output.write_validation import compute_validation, write_validation
from voletron.types import Config, TagID, TimestampSeconds, ChamberName, AnimalName, Validation
from voletron.trajectory import AllAnimalTrajectories
from voletron.output.types import ValidationRow, OutputBin

class TestWriteValidation(unittest.TestCase):
    def test_compute_validation(self):
        # Setup mocks
        tag_id_to_name = {TagID("tag1"): AnimalName("animal1")}
        
        mock_trajectories = MagicMock(spec=AllAnimalTrajectories)
        # Mock get_locations_between
        # It takes tag_id, start, end.
        # We need it to return a set of chamber names.
        
        def get_locations_side_effect(tag_id, start, end):
            # Let's say at approx time 5 (range -25 to 95), it is in "c1"
            # at approx time 15 (range -15 to 105), it is in "c2"
            if start <= 5 <= end or start <= 15 <= end:
                 # It's crude but if query covers 5, return c1. If covers 15, return c2.
                 # The call is always timestamp - 30 to timestamp + 90.
                 # V1 timestamp 5: range -25 to 95. Covers 5 and 15 actually if we assume strict logic.
                 pass
            
            # Simplified:
            # V1 at 5 -> query -25 to 95. We return {"c1"}.
            # V2 at 15 -> query -15 to 105. We return {"c1"} (incorrect) or {"c2"} (correct).
            
            # Let's rely on call args matching in a simple way or just static return if sufficient.
            # But we have multiple calls.
            return {"c1"}

        mock_trajectories.get_locations_between.return_value = {"c1"}
        
        validations = [
            Validation(TimestampSeconds(5), TagID("tag1"), ChamberName("c1")), # Correct
            Validation(TimestampSeconds(15), TagID("tag1"), ChamberName("c2")) # Incorrect (mock returns c1)
        ]

        tag_ids = [TagID("tag1")]
        
        bins = [
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(10), analyzer=MagicMock()),
            OutputBin(start=TimestampSeconds(10), end=TimestampSeconds(20), analyzer=MagicMock()),
            OutputBin(start=TimestampSeconds(0), end=TimestampSeconds(20), analyzer=MagicMock())
        ]

        rows = compute_validation(tag_ids, mock_trajectories, tag_id_to_name, validations, bins)

        self.assertEqual(len(rows), 4)
        
        # Bin 1 (0-10): Validation at 5.
        r1 = [r for r in rows if r.bin_start == 0 and r.bin_end == 10][0]
        self.assertEqual(r1.timestamp, 5)
        self.assertTrue(r1.correct)
        self.assertEqual(r1.expected_chamber, "c1")
        
        # Bin 2 (10-20): Validation at 15.
        r2 = [r for r in rows if r.bin_start == 10 and r.bin_end == 20][0]
        self.assertEqual(r2.timestamp, 15)
        self.assertFalse(r2.correct) # Expected c2, observed c1
        self.assertEqual(r2.expected_chamber, "c2")
        
        # Bin 3 (0-20): Both.
        r3_list = [r for r in rows if r.bin_start == 0 and r.bin_end == 20]
        self.assertEqual(len(r3_list), 2)

    def test_write_validation(self):
        out_dir = tempfile.mkdtemp()
        exp_name = "test_exp"
        
        rows = [
             ValidationRow(
                bin_start=TimestampSeconds(0),
                bin_end=TimestampSeconds(100),
                correct=True,
                timestamp=TimestampSeconds(50),
                animal_name="a1",
                expected_chamber="c1",
                observed_chambers={"c1"}
            )
        ]
        
        write_validation(rows, out_dir, exp_name)
        
        expected_file = os.path.join(out_dir, "test_exp.validate.csv")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("bin_start,bin_end,Correct,Timestamp,AnimalName,Expected,Observed", content)
            self.assertIn("0,100,True", content)

if __name__ == '__main__':
    unittest.main()
