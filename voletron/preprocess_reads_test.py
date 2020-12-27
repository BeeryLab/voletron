import unittest
from unittest.mock import MagicMock, call

from voletron.parse_olcus import parse_raw_line
from voletron.preprocess_reads import parsimonious_reads, spaced_reads
from voletron.state import Chamber, State
from voletron.structs import Antenna, Dwell, Read, Traversal


class TestPreprocessReads(unittest.TestCase):
    def test_spaced_reads(self):
        reads = [
            Read("tag_a", 200, Antenna("Tube2", "ArenaA")),
            Read("tag_a", 210, Antenna("Tube2", "Cage2")),
            Read("tag_a", 210.001, Antenna("Tube2", "Cage2")),
            Read("tag_a", 210.002, Antenna("Tube2", "ArenaA")),
            Read("tag_a", 300, Antenna("Tube4", "ArenaA")),
            Read("tag_a", 300.001, Antenna("Tube4", "Cage4")),
        ]
        # mutating
        spaced_reads(reads)

        self.assertEqual(
            reads,
            [
                Read("tag_a", 200, Antenna("Tube2", "ArenaA")),
                Read("tag_a", 210, Antenna("Tube2", "Cage2")),
                Read("tag_a", 210.002, Antenna("Tube2", "Cage2")),
                Read("tag_a", 210.004, Antenna("Tube2", "ArenaA")),
                Read("tag_a", 300, Antenna("Tube4", "ArenaA")),
                Read("tag_a", 300.002, Antenna("Tube4", "Cage4")),
            ],
        )

    def test_parsimonious_reads(self):
        reads = [
            Read("tag_a", 200, Antenna("Tube2", "ArenaA")),
            Read("tag_a", 210, Antenna("Tube2", "Cage2")),
            # these two reversed!
            Read("tag_a", 210.002, Antenna("Tube2", "ArenaA")),
            Read("tag_a", 210.004, Antenna("Tube2", "Cage2")),
            ##
            Read("tag_a", 300, Antenna("Tube4", "ArenaA")),
            Read("tag_a", 300.002, Antenna("Tube4", "Cage4")),
        ]
        # mutating
        parsimonious_reads("tag_id", reads)

        self.assertEqual(
            reads,
            [
                Read("tag_a", 200, Antenna("Tube2", "ArenaA")),
                Read("tag_a", 210, Antenna("Tube2", "Cage2")),
                # fixed
                Read("tag_a", 210.002, Antenna("Tube2", "Cage2")),
                Read("tag_a", 210.004, Antenna("Tube2", "ArenaA")),
                ##
                Read("tag_a", 300, Antenna("Tube4", "ArenaA")),
                Read("tag_a", 300.002, Antenna("Tube4", "Cage4")),
            ],
        )


if __name__ == "__main__":
    unittest.main()
