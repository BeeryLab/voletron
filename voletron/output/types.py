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

from dataclasses import dataclass
from typing import Dict, List, Union, Set
from voletron.types import TimestampSeconds
from voletron.time_span_analyzer import TimeSpanAnalyzer

@dataclass
class OutputBin:
    start: TimestampSeconds
    end: TimestampSeconds
    analyzer: TimeSpanAnalyzer

@dataclass
class ChamberTimeRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    animal_name: str
    chamber_times: Dict[str, float]
    total_time: float

@dataclass
class PairCohabRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    animal_a_name: str
    animal_b_name: str
    dwell_count: int
    duration_seconds: float
    bin_duration: float

@dataclass
class GroupChamberCohabRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    animal_names: List[str]
    chamber_name: str
    dwell_count: int
    duration_seconds: float
    bin_duration: float

@dataclass
class GroupSizeRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    animal_name: str
    size_seconds: Dict[int, float]
    avg_group_size: float
    avg_group_size_nosolo: Union[float, str]
    sum_pair_time: float
    bin_duration: float

@dataclass
class LongDwellRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    animal_name: str
    chamber_name: str
    start_time: TimestampSeconds
    duration_seconds: float

@dataclass
class ActivityRow:
    bin_start: TimestampSeconds  # Was start_time
    bin_end: TimestampSeconds    # Was end_time
    bin_seconds: int
    tag_id: str
    avg_dwell_sizes: List[float]  # [size1, size2, size3, size4]
    traversal_count: int

@dataclass
class ValidationRow:
    bin_start: TimestampSeconds
    bin_end: TimestampSeconds
    correct: bool
    timestamp: TimestampSeconds
    animal_name: str
    expected_chamber: str
    observed_chambers: Set[str]
