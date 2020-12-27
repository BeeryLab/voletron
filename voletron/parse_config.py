import datetime

from voletron.structs import Antenna, Config, Read, Validation


def parse_config(filename):
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


def parse_validation(filename, name_to_tag_id):
    """Parse a run validation file.

    The file must have a header line such as:
    `Timestamp, AnimalID, Chamber`

    Args:
        filename: The file name to read.

    Returns: a list of Validation entries.
    """
    result = []
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
                timestamp = datetime.datetime.strptime(
                    time_str, "%d.%m.%Y %H:%M"
                ).timestamp()
                result.append(Validation(timestamp, tag_id, chamber))
                # TODO: validate chamber matches apparatus_config
            except KeyError:
                print("Validation config contains unknown animal: {}".format(animalid))

    return result
