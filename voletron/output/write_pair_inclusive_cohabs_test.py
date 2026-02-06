
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


    def test_stationary_scenarios_integration(self):
        """
        Integration test verifying that stationary animals are correctly handled.
        Scenario 1: Co-dwelling Stationary (Both Cage1) -> Should have 1 dwell, full duration.
        Scenario 2: Separated Stationary (Cage1 vs Cage2) -> Should have 0 dwells, 0 duration.
        """
        from voletron.trajectory import AllAnimalTrajectories, Read
        from voletron.co_dwell_accumulator import CoDwellAccumulator
        from voletron.time_span_analyzer import TimeSpanAnalyzer
        from voletron.types import AnimalConfig, TagID, TimestampSeconds, ChamberName, Antenna, CHAMBER_ERROR

        def run_scenario(tag_id_to_start_chamber):
            start_time = TimestampSeconds(1.0)
            analysis_end_time = TimestampSeconds(7200) # 2 hours
            
            reads_per_animal = {
                TagID("A"): [
                    Read(TagID("A"), TimestampSeconds(10), Antenna(ChamberName("Tube1"), tag_id_to_start_chamber[TagID("A")])),
                ],
                TagID("B"): [
                    Read(TagID("B"), TimestampSeconds(10), Antenna(ChamberName("Tube1"), tag_id_to_start_chamber[TagID("B")])),
                ]
            }
            
            config = AnimalConfig(
                tag_id_to_name={TagID("A"): "AnimalA", TagID("B"): "AnimalB"},
                tag_id_to_start_chamber=tag_id_to_start_chamber
            )

            trajectories = AllAnimalTrajectories(
                start_time, 
                analysis_end_time, 
                tag_id_to_start_chamber, 
                reads_per_animal, 
                dwell_threshold=10.0
            )
            
            # Mock all_chambers since we don't load full apparatus
            all_chambers = [ChamberName("Cage1"), ChamberName("Cage2"), CHAMBER_ERROR]
            
            accumulator = CoDwellAccumulator(start_time, tag_id_to_start_chamber, all_chambers)
            for t in trajectories.traversals():
                accumulator.update_state_from_traversal(t)
            co_dwells = accumulator.end(analysis_end_time)
            
            # Create Bin 2: 3600 to 7200
            b_start = TimestampSeconds(3600)
            b_end = TimestampSeconds(7200)
            
            # Output.py binning logic emulation
            bin_dwells = []
            for d in sorted(co_dwells, key=lambda x: x.end):
                if d.end <= b_start: continue
                if d.start >= b_end: continue
                bin_dwells.append(d)
                
            analyzer = TimeSpanAnalyzer(bin_dwells, b_start, b_end)
            
            bin2 = OutputBin(
                bin_number=2,
                bin_start=b_start,
                bin_end=b_end,
                analyzer=analyzer
            )
            
            rows = compute_pair_inclusive_cohabs(
                config,
                [TagID("A"), TagID("B")],
                [bin2]
            )
            
            for r in rows:
                if r.animal_a_name == "AnimalA" and r.animal_b_name == "AnimalB":
                    return r.dwell_count, r.duration_seconds
            return -1, -1

        # Scenario 1: Co-dwelling
        d1, s1 = run_scenario({TagID("A"): ChamberName("Cage1"), TagID("B"): ChamberName("Cage1")})
        self.assertEqual(d1, 1, "Expected 1 dwell for stationary co-dwelling pair")
        self.assertEqual(s1, 3600, "Expected full duration for stationary co-dwelling pair")

        # Scenario 2: Separated
        d2, s2 = run_scenario({TagID("A"): ChamberName("Cage1"), TagID("B"): ChamberName("Cage2")})
        self.assertEqual(d2, 0, "Expected 0 dwells for separated stationary pair")
        self.assertEqual(s2, 0, "Expected 0 duration for separated stationary pair")


if __name__ == '__main__':
    unittest.main()
