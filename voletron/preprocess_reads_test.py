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
from voletron.co_dwell_accumulator import Chamber, CoDwellAccumulator
from voletron.types import Antenna, Dwell, Read, Traversal, TagID, TimestampSeconds, ChamberName, AnimalName


class TestPreprocessReads(unittest.TestCase):
    def test_spaced_reads(self):
        reads = [
            Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(210), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
            Read(TagID("tag_a"), TimestampSeconds(210.001), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
            Read(TagID("tag_a"), TimestampSeconds(210.002), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube4"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(300.001), Antenna(ChamberName("Tube4"), ChamberName("Cage4"))),
        ]
        # mutating
        _spaced_reads(reads)

        self.assertEqual(
            reads,
            [
                Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(210), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                Read(TagID("tag_a"), TimestampSeconds(210.002), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                Read(TagID("tag_a"), TimestampSeconds(210.004), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube4"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(300.002), Antenna(ChamberName("Tube4"), ChamberName("Cage4"))),
            ],
        )

    def test_parsimonious_reads(self):
        reads = [
            Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(210), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
            # these two reversed!
            Read(TagID("tag_a"), TimestampSeconds(210.002), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(210.004), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
            ##
            Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube4"), ChamberName("CentralA"))),
            Read(TagID("tag_a"), TimestampSeconds(300.002), Antenna(ChamberName("Tube4"), ChamberName("Cage4"))),
        ]
        tag_id_to_name = {TagID("tag_a"): AnimalName("Animal A")}

        # mutating
        _parsimonious_reads(TagID("tag_a"), reads, tag_id_to_name)

        self.assertEqual(
            reads,
            [
                Read(TagID("tag_a"), TimestampSeconds(200), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(210), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                # fixed
                Read(TagID("tag_a"), TimestampSeconds(210.002), Antenna(ChamberName("Tube2"), ChamberName("Cage2"))),
                Read(TagID("tag_a"), TimestampSeconds(210.004), Antenna(ChamberName("Tube2"), ChamberName("CentralA"))),
                ##
                Read(TagID("tag_a"), TimestampSeconds(300), Antenna(ChamberName("Tube4"), ChamberName("CentralA"))),
                Read(TagID("tag_a"), TimestampSeconds(300.002), Antenna(ChamberName("Tube4"), ChamberName("Cage4"))),
            ],
        )


if __name__ == "__main__":
    unittest.main()
