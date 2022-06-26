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


import datetime


def seconds_between_timestamps(a, b):
    # Avoid knowing whether timestamps are sec, msec, or usec.
    # TODO: (performance) compute this directly in sec, without
    # converting back and forth
    return abs(
        (
            datetime.datetime.fromtimestamp(a) - datetime.datetime.fromtimestamp(b)
        ).total_seconds()
    )


def format_time(a):
    return datetime.datetime.strftime(
        datetime.datetime.fromtimestamp(a), "%d.%m.%Y %H:%M:%S:%f"
    )[:-3]
