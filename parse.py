import datetime
import sys
from core import Antenna, Read
from config import olcus_id_to_antenna_hardcode


def olcus_id_to_antenna(device_id: int, antenna_id: int):
    """Map the Olcus ID--the (device_id, antenna_id pair) to an Antenna object.
    
    Returns: The Antenna corresponding to the given Olcus ID.
    """
    return olcus_id_to_antenna_hardcode[device_id][antenna_id]


def parse_raw_line(line):
    """Parse a line of the "raw" format, producing a Read object.

    Args:
        line: a line of raw input.

    Returns: a Read object.
    """
    (can_timestamp, date_timestamp, device_id, antenna_id, tag_id) = line.split(";")
    del can_timestamp
    if not tag_id:
        return None
    # vole_id = tag_to_vole[tag_id]
    # olcus_id = "%s,%s".format(device_id, antenna_id)
    antenna = olcus_id_to_antenna(int(device_id), int(antenna_id))
    dt = datetime.datetime.strptime(date_timestamp, "%d.%m.%Y %H:%M:%S:%f")
    return Read(tag_id, dt.timestamp(), antenna)


def parse_raw_file(filename):
    """Parse a raw input file, producing a stream of Read objects.

    Args:
        filename: The file name from which to read.
    
    Yields: one Read per line of input (excluding the header line)
    """
    with open(filename) as file:
        file.readline()  # skip headers
        for line in file:
            read = parse_raw_line(line)
            if read:
                yield read


def main(argv):
    filename = argv[1]
    for read in parse_raw_file(filename):
        print(read)


# main(sys.argv)
