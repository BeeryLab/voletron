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


from typing import List, Dict
from voletron.types import CHAMBER_ERROR, Antenna, HabitatName, ChamberName

# TODO: consider how to represent the apparatus config as data (e.g., json), not as
# code.

# Maps the Olcus ID of each antenna to an Antenna object representing its
# location in the apparatus.  Each tube has two antennae; the second field of
# the Antenna object gives the string ID of the chamber to which that end of
# the tube is connected.
#
# Note this implicitly describes the physical layout of the apparatus.
# In particular, one recording setup reads data from two disconnected habitats:
# One in which Cages 1-5 all connect to CentralA, and a second in which Cages
# 6-10 connect to CentralB.
olcus_id_to_antenna_hardcode = {
    0: {  # device 0
        0: Antenna(ChamberName("Tube1"), ChamberName("CentralA")),
        1: Antenna(ChamberName("Tube1"), ChamberName("Cage1")),
        2: Antenna(ChamberName("Tube2"), ChamberName("CentralA")),
        3: Antenna(ChamberName("Tube2"), ChamberName("Cage2")),
        4: Antenna(ChamberName("Tube3"), ChamberName("CentralA")),
        5: Antenna(ChamberName("Tube3"), ChamberName("Cage3")),
    },
    1: {  # device 1
        0: Antenna(ChamberName("Tube4"), ChamberName("CentralA")),
        1: Antenna(ChamberName("Tube4"), ChamberName("Cage4")),
        2: Antenna(ChamberName("Tube5"), ChamberName("CentralA")),
        3: Antenna(ChamberName("Tube5"), ChamberName("Cage5")),
        4: Antenna(ChamberName("Tube6"), ChamberName("CentralB")),
        5: Antenna(ChamberName("Tube6"), ChamberName("Cage6")),
    },
    2: {  # device 2
        0: Antenna(ChamberName("Tube7"), ChamberName("CentralB")),
        1: Antenna(ChamberName("Tube7"), ChamberName("Cage7")),
        2: Antenna(ChamberName("Tube8"), ChamberName("CentralB")),
        3: Antenna(ChamberName("Tube8"), ChamberName("Cage8")),
        4: Antenna(ChamberName("Tube9"), ChamberName("CentralB")),
        5: Antenna(ChamberName("Tube9"), ChamberName("Cage9")),
    },
    3: {
        0: Antenna(ChamberName("Tube10"), ChamberName("CentralB")),
        1: Antenna(ChamberName("Tube10"), ChamberName("Cage10")),
    },  # device 3
}

# This could be derived from the above, but I'm lazy
apparatus_chambers : Dict[HabitatName, List[ChamberName]] = {
    HabitatName("HabitatA"): [
        ChamberName("CentralA"),
        ChamberName("Cage1"),
        ChamberName("Tube1"),
        ChamberName("Cage2"),
        ChamberName("Tube2"),
        ChamberName("Cage3"),
        ChamberName("Tube3"),
        ChamberName("Cage4"),
        ChamberName("Tube4"),
        ChamberName("Cage5"),
        ChamberName("Tube5"),
        CHAMBER_ERROR,
    ],
    HabitatName("HabitatB"): [
        ChamberName("CentralB"),
        ChamberName("Cage6"),
        ChamberName("Tube6"),
        ChamberName("Cage7"),
        ChamberName("Tube7"),
        ChamberName("Cage8"),
        ChamberName("Tube8"),
        ChamberName("Cage9"),
        ChamberName("Tube9"),
        ChamberName("Cage10"),
        ChamberName("Tube10"),
        CHAMBER_ERROR,
    ],
}

all_antennae = [
    antenna
    for (device, antennae) in olcus_id_to_antenna_hardcode.items()
    for (index, antenna) in antennae.items()
]

all_chambers = sorted(
    list(set([item for a in all_antennae for item in [a.tube, a.cage]]))
)
all_chambers.append(CHAMBER_ERROR)
