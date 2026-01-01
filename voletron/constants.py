# Copyright 2025 Google LLC
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

"""Constants used throughout the Voletron application."""

# Time in seconds between consecutive reads at the same antenna to differentiate
# between a short dwell (in the tube) and a long dwell (in the cage/arena).
DEFAULT_TIME_BETWEEN_READS_THRESHOLD = 10.0

# Small time epsilon in seconds to use when inserting inferred reads to ensure
# correct chronological ordering.
INFERRED_READ_EPSILON = 0.001

# Threshold for considering a dwell "long" (e.g. for long stay reporting).
# Currently set to 6 hours.
LONG_DWELL_THRESHOLD_SECONDS = 60 * 60 * 6

# Time to add to a read if it is nearly simultaneous with the previous one.
READ_JITTER_SECONDS = 0.002

# Window within which to consider swapping read order for parsimony.
READ_PARSIMONY_WINDOW_SECONDS = 0.010
