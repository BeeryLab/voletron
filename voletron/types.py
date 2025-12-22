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


from typing import Dict, List, NamedTuple, NewType, Optional

TagID = NewType('TagID', str)

GroupID = NewType('GroupID', str)

AnimalName = NewType('AnimalName', str)

HabitatName = NewType('HabitatName', str)

ChamberName = NewType('ChamberName', str)

CHAMBER_OUTSIDE = ChamberName("Outside")

CHAMBER_ERROR = ChamberName("Error")

TimestampSeconds = NewType('TimestampSeconds', float)

DurationSeconds = NewType('DurationSeconds', float)

DurationMinutes = NewType('DurationMinutes', float)

# An antenna placed in a tube, near where that tube connects to a given cage.
# Tubes and cages are identified by string IDs.
Antenna = NamedTuple("Antenna", [("tube", ChamberName), ("cage", ChamberName)])

# One observation of a tag by an antenna.
Read = NamedTuple("Read", [("tag_id", TagID), ("timestamp", TimestampSeconds), ("antenna", Antenna)])

# One validation event, when an animal was observed by a human to be in a certain chamber.
# Timestamps are in seconds since the epoch.
Validation = NamedTuple(
    "Validation", [("timestamp", TimestampSeconds), ("tag_id", TagID), ("chamber", ChamberName)]
)

# One timespan of presence of an animal in a given chamber.  The animal ID is
# not given, because these records are used only within an AnimalTrajectory.
# `start` and `end` are timestamps.  `chamber` is the string ID of the tube or
# cage where the animal stayed during this time.
Dwell = NamedTuple("Dwell", [("start", TimestampSeconds), ("end", TimestampSeconds), ("chamber", ChamberName)])

# Describes pairs or groups of animals together in a given chamber during a
# given time span.
CoDwell = NamedTuple("CoDwell", [("tag_ids", List[TagID]), ("start", TimestampSeconds), ("end", TimestampSeconds), ("chamber", ChamberName)])
# An instance of an animal staying put for a very long time, which likely
# indicates an error of some kind.
LongDwell = NamedTuple(
    "LongDwell",
    [("tag_id", TagID), ("chamber", ChamberName), ("start_time", TimestampSeconds), ("minutes", DurationMinutes)],
)

# One instance of an animal crossing from one chamber (tube or cage) to another.
# This extends the idea of a `Read`, because here the direction of travel is
# known.  `orig` and `dest` are string IDs of chambers (tubes or cages)-- the
# origin and the destination, respectively.
Traversal = NamedTuple(
    "Traversal", [("timestamp", TimestampSeconds), ("tag_id", TagID), ("orig", ChamberName), ("dest", ChamberName)]
)

# The configuration for this run, mapping tag IDs to animal names and start chambers.
Config = NamedTuple(
    "Config", [("tag_id_to_name", Dict[TagID, AnimalName]), ("tag_id_to_start_chamber", Dict[TagID, ChamberName])]
)

GroupDwellAggregate = NamedTuple(
    "GroupDwellAggregate",
    [("tag_ids", List[TagID]), ("chamber", ChamberName), ("count", int), ("duration_seconds", DurationSeconds)],
)

def chamberBetween(antennaA: Antenna, antennaB: Antenna) -> Optional[ChamberName]:
    """Determine which chamber is between two Antennae."""
    if antennaA == antennaB:
        raise ValueError("There is no chamber between an antenna and itself")
    i = list(set([antennaA.tube, antennaA.cage]) & set([antennaB.tube, antennaB.cage]))
    if not i:
        return None
    if len(i) != 1:
        raise ValueError(
            "Impossible: There can't be more than one chamber between two antennae"
        )
    return i[0]
