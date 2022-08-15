# Copyright 2022 Google LLC
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
from unittest.mock import MagicMock, call

from voletron.parse_olcus import parse_raw_line
from voletron.preprocess_reads import _parsimonious_reads, _spaced_reads
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
        _spaced_reads(reads)

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
        tag_id_to_name = {"tag_a": "Animal A"}

        # mutating
        _parsimonious_reads("tag_a", reads, tag_id_to_name)

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
