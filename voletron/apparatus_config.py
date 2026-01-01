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

import json
import os

# Globals are initially empty and populated by load_apparatus_config
olcus_id_to_antenna_hardcode = {}
apparatus_chambers: Dict[HabitatName, List[ChamberName]] = {}
all_antennae = []
all_chambers = []

def load_apparatus_config(json_path: str):
    """
    Loads apparatus configuration from a JSON file and populates the module-level
    globals. This function mutates the globals in-place so that imported references
    remain valid.
    """
    if not os.path.exists(json_path):
         raise FileNotFoundError(f"Could not find apparatus config file: {json_path}")
    
    with open(json_path, 'r') as f:
        _config = json.load(f)

    # 1. Parse olcus_devices
    # Clear existing data to support re-loading (e.g. in tests)
    olcus_id_to_antenna_hardcode.clear()
    
    for device_id_str, antennae_dict in _config["olcus_devices"].items():
        device_id = int(device_id_str)
        olcus_id_to_antenna_hardcode[device_id] = {}
        for antenna_id_str, antenna_data in antennae_dict.items():
            antenna_id = int(antenna_id_str)
            olcus_id_to_antenna_hardcode[device_id][antenna_id] = Antenna(
                ChamberName(antenna_data["tube"]), ChamberName(antenna_data["cage"])
            )

    # 2. Parse habitats
    apparatus_chambers.clear()
    for habitat_name, chambers in _config["habitats"].items():
        apparatus_chambers[HabitatName(str(habitat_name))] = [
            ChamberName(c) if c != "Error" else CHAMBER_ERROR for c in chambers
        ]

    # 3. Derive all_antennae
    all_antennae.clear()
    all_antennae.extend([
        antenna
        for (device, antennae) in olcus_id_to_antenna_hardcode.items()
        for (index, antenna) in antennae.items()
    ])

    # 4. Derive all_chambers
    all_chambers.clear()
    _chambers = sorted(
        list(set([item for a in all_antennae for item in [a.tube, a.cage]]))
    )
    all_chambers.extend(_chambers)
    all_chambers.append(CHAMBER_ERROR)
