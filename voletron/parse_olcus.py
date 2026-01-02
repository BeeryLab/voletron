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


import datetime
import glob
import logging
import os
import sys
from typing import Generator, NewType, Optional, Union
from pytz.tzinfo import StaticTzInfo, DstTzInfo

from voletron.apparatus_config import olcus_id_to_antenna_hardcode
from voletron.types import Antenna, AnimalConfig, Read, TagID, TimestampSeconds

OlcusDeviceID = NewType('OlcusDeviceID', int)
OlcusAntennaID = NewType('OlcusAntennaID', int)

def olcus_id_to_antenna(device_id: OlcusDeviceID, antenna_id: OlcusAntennaID) -> Antenna:
    """Map the Olcus ID--the (device_id, antenna_id pair) to an Antenna object.

    Returns: The Antenna corresponding to the given Olcus ID.
    """
    return olcus_id_to_antenna_hardcode[device_id][antenna_id]


def parse_raw_line(line: str, timezone: datetime.tzinfo) -> Optional[Read]:
    """Parse a line of the "raw" format, producing a Read object.

    Args:
        line: a line of raw input.

    Returns: a Read object.
    """
    (can_timestamp, date_timestamp, device_id, antenna_id, tag_id) = [
        x.strip() for x in line.split(";")
    ]
    del can_timestamp
    if not tag_id:
        return None
    antenna = olcus_id_to_antenna(OlcusDeviceID(int(device_id)), OlcusAntennaID(int(antenna_id)))

    # The time given in the Olcus file is the *local* time.  No time zone is given.
    dt = datetime.datetime.strptime(date_timestamp, "%d.%m.%Y %H:%M:%S:%f")
    if isinstance(timezone, (StaticTzInfo, DstTzInfo)):
        dt = timezone.localize(dt)
    return Read(TagID(tag_id), TimestampSeconds(dt.timestamp()), antenna)


def parse_raw_file(filename: str, timezone: datetime.tzinfo) -> Generator[Read, None, None]:
    """Parse a raw input file, producing a stream of Read objects.

    Args:
        filename: The file name from which to read.

    Yields: one Read per line of input (excluding the header line)
    """

    logging.info("Reading file: {}".format(filename))


    with open(filename) as file:
        file.readline()  # skip headers
        for line in file:
            read = parse_raw_line(line, timezone)
            if read:
                yield read


def parse_first_read(dirname: str, timezone: datetime.tzinfo) -> Read:
    """Obtain the first read from the first raw file in a directory.
    Args:
        dirname: The directory name from which to read.

    Returns: a Read.
    """
    # The files have names rawYYYYMMDD.csv, so lexicographical sort is also
    # chronological sort.
    files = sorted(glob.glob(os.path.join(dirname, "raw*.csv")))
    with open(files[0]) as file:
        file.readline()  # skip headers
        read = None
        while not read:
            line = file.readline()
            read = parse_raw_line(line, timezone)
    return read


def parse_raw_dir(dirname: str, timezone: datetime.tzinfo) -> Generator[Read, None, None]:
    """Parse raw files in a directory in order, producing a stream of Reads.

    Args:
        dirname: The directory name from which to read.

    Yields: one Read per line of input (excluding the header line)
    """
    # The files have names rawYYYYMMDD.csv, so lexicographical sort is also
    # chronological sort.
    files = sorted(glob.glob(os.path.join(dirname, "raw*.csv")))
    for f in files:
        for read in parse_raw_file(f, timezone):
            yield read
