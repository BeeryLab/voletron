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

from voletron.structs import Antenna, Config, Read, Validation


def parse_config(filename: str) -> Config:
    """Parse a run configuration file.

    The file must have a header line such as:
    `AnimalName, TagId, StartChamber`

    Args:
        filename: The file name to read.

    Returns: a Config object, mapping tag_id to start_chamber and to animal_name.
    """
    tag_id_to_start_chamber = {}
    tag_id_to_name = {}
    with open(filename) as file:
        file.readline()  # skip headers
        # TODO: validate headers
        for line in file:
            (animal_name, tag_id, start_chamber) = [x.strip() for x in line.split(",")]
            tag_id_to_name[tag_id] = animal_name
            tag_id_to_start_chamber[tag_id] = start_chamber
            # TODO: validate start_chamber matches apparatus_config
    return Config(tag_id_to_name, tag_id_to_start_chamber)


def parse_validation(filename: str, name_to_tag_id: Dict[str, str], timezone: Union[StaticTzInfo, DstTzInfo]) -> list[Validation]:
    """Parse a run validation file.

    The file must have a header line such as:
    `Timestamp, AnimalID, Chamber`

    Args:
        filename: The file name to read.

    Returns: a list of Validation entries.
    """
    result: list[Validation] = []
    with open(filename) as file:
        file.readline()  # skip headers
        # TODO: validate headers
        for line in file:
            line = line.strip()
            if line.startswith("#") or line == "" or line == ",,":
                continue
            (time_str, animalid, chamber) = [x.strip() for x in line.split(",")]
            try:
                tag_id = name_to_tag_id[animalid]
                timestamp = timezone.localize(datetime.datetime.strptime(
                    time_str, "%d.%m.%Y %H:%M"
                )).timestamp()
                result.append(Validation(timestamp, tag_id, chamber))
                # TODO: validate chamber matches apparatus_config
            except KeyError:
                print("Validation config contains unknown animal: {}".format(animalid))

    return result
