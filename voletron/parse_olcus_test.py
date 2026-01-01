# Copyright 2022-2025 Google LLC
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
import pytz

from voletron.parse_olcus import parse_raw_line
from voletron.types import Read
from voletron.apparatus_config import load_apparatus_config


class TestParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_apparatus_config("apparatus_example.json")

    def test_parse_raw_line(self):
        line = "3168630996;05.03.2020 16:14:11:796;0;0;972273000584934"
        timezone = pytz.timezone("US/Pacific")
        read : Read = parse_raw_line(line, timezone) # type: ignore
        self.assertIsNotNone(read)
        self.assertEqual(read.tag_id, "972273000584934")

        # This test hardcodes being in the US PST timezone
        # because the Olcus string is interpreted as "local time"
        # but the test checks against a GMT timestamp
        self.assertEqual(read.timestamp, 1583453651.796)
        self.assertEqual(read.antenna.tube, "Tube1")
        self.assertEqual(read.antenna.cage, "CentralA")

    def test_parse_raw_line_empty_tag(self):
        line = "3169159459;05.03.2020 16:14:12:312;0;0;"
        timezone = pytz.timezone("US/Pacific")
        read = parse_raw_line(line, timezone)
        self.assertEqual(read, None)


if __name__ == "__main__":
    unittest.main()
