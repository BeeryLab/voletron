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
import datetime
from voletron import util

class TestUtil(unittest.TestCase):

    def test_seconds_between_timestamps(self):
        # Test with seconds (integers)
        t1 = 1600000000
        t2 = 1600000010
        self.assertEqual(util.seconds_between_timestamps(t1, t2), 10.0)
        self.assertEqual(util.seconds_between_timestamps(t2, t1), 10.0)
        
        # Test with milliseconds (large ints)
        t3 = 1600000000000
        t4 = 1600000001000
        self.assertEqual(util.seconds_between_timestamps(t3, t4), 1.0)

        # Test with microseconds (large ints)
        t5 = 1600000000000000
        t6 = 1600000001000000
        self.assertEqual(util.seconds_between_timestamps(t5, t6), 1.0)
        
        # Test with same timestamp
        self.assertEqual(util.seconds_between_timestamps(t1, t1), 0.0)

    def test_format_time(self):
        ts = 1600000000.123456
        # We can't easily assert the exact string because of timezones,
        # but we can check the format and the milliseconds part.
        formatted = util.format_time(ts)
        
        # Check length: "DD.MM.YYYY HH:MM:SS:mmm" -> 10 + 1 + 8 + 1 + 3 = 23 chars
        # Example: 13.09.2020 12:26:40:123
        self.assertEqual(len(formatted), 23)
        
        # Check the milliseconds part (last 3 chars)
        # .123456 -> 123
        self.assertTrue(formatted.endswith("123"))
        
        # Check structure
        try:
            date_part, time_part = formatted.split(' ')
            self.assertEqual(len(date_part.split('.')), 3)
            # Time part should be H:M:S:mmm
            self.assertEqual(len(time_part.split(':')), 4) 
        except ValueError:
            self.fail("format_time output format is incorrect")

    def test_format_time_with_timezone(self):
        ts = 1600000000.0
        # UTC
        formatted_utc = util.format_time(ts, datetime.timezone.utc)
        # 1600000000 is 2020-09-13 12:26:40 UTC
        self.assertEqual(formatted_utc, "13.09.2020 12:26:40:000")
        
        # UTC+1
        tz_plus_1 = datetime.timezone(datetime.timedelta(hours=1))
        formatted_plus_1 = util.format_time(ts, tz_plus_1)
        self.assertEqual(formatted_plus_1, "13.09.2020 13:26:40:000")

if __name__ == '__main__':
    unittest.main()
