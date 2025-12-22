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
from typing import Dict, Union
from pytz.tzinfo import StaticTzInfo, DstTzInfo

from voletron.types import AnimalName, Antenna, ChamberName, Config, Read, TagID, TimestampSeconds, Validation
from voletron.apparatus_config import all_chambers

def parse_config(filename: str) -> Config:
    """Parse a run configuration file.

    The file must have a header line such as:
    `AnimalName, TagId, StartChamber`

    Args:
        filename: The file name to read.

    Returns: a Config object, mapping tag_id to start_chamber and to animal_name.
    """
    tag_id_to_start_chamber : Dict[TagID, ChamberName] = {}
    tag_id_to_name : Dict[TagID, AnimalName] = {}
    with open(filename) as file:
        header = file.readline().strip()
        headers = [x.strip() for x in header.split(",")]
        expected_headers = ["AnimalName", "TagId", "StartChamber"]
        if headers != expected_headers:
            raise ValueError(f"Invalid headers. Expected {expected_headers}, got {headers}")
        
        for line in file:
            (animal_name, tag_id, start_chamber) = [x.strip() for x in line.split(",")]
            tag_id_to_name[TagID(tag_id)] = AnimalName(animal_name)
            tag_id_to_start_chamber[TagID(tag_id)] = ChamberName(start_chamber)
            if ChamberName(start_chamber) not in all_chambers:
                raise ValueError(f"Invalid start chamber {start_chamber} for animal {animal_name}")
            
    return Config(tag_id_to_name, tag_id_to_start_chamber)


def parse_validation(filename: str, name_to_tag_id: Dict[AnimalName, TagID], timezone: Union[StaticTzInfo, DstTzInfo]) -> list[Validation]:
    """Parse a run validation file.

    The file must have a header line such as:
    `Timestamp, AnimalID, Chamber`

    Args:
        filename: The file name to read.

    Returns: a list of Validation entries.
    """
    result: list[Validation] = []
    with open(filename) as file:
        header = file.readline().strip()
        headers = [x.strip() for x in header.split(",")]
        expected_headers = ["Timestamp", "AnimalID", "Chamber"]
        if headers != expected_headers:
            raise ValueError(f"Invalid headers. Expected {expected_headers}, got {headers}")
        
        for line in file:
            line = line.strip()
            if line.startswith("#") or line == "" or line == ",,":
                continue
            (time_str, animalid, chamber) = [x.strip() for x in line.split(",")]
            try:
                tag_id = name_to_tag_id[AnimalName(animalid)]
                timestamp = TimestampSeconds(timezone.localize(datetime.datetime.strptime(
                    time_str, "%d.%m.%Y %H:%M"
                )).timestamp())

                if ChamberName(chamber) not in all_chambers:
                    raise ValueError(f"Invalid chamber {chamber} for animal {animalid} at time {time_str}")
            
                result.append(Validation(timestamp, tag_id, ChamberName(chamber)))
                
               
            except KeyError:
                print("Validation config contains unknown animal: {}".format(animalid))

    return result
