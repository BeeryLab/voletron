from typing import NamedTuple

# An antenna placed in a tube, near where that tube connects to a given cage.
# Tubes and cages are identified by string IDs.
Antenna = NamedTuple("Antenna", [("tube", str), ("cage", str)])

# One observation of a tag by an antenna.
Read = NamedTuple("Read", [("tag_id", str), ("timestamp", int), ("antenna", Antenna)])


Validation = NamedTuple(
    "Validation", [("timestamp", int), ("tag_id", str), ("chamber", str)]
)


# One timespan of presence of an animal in a given chamber.  The animal ID is
# not given, because these records are used only within an AnimalTrajectory.
# `start` and `end` are timestamps.  `chamber` is the string ID of the tube or
# cage where the animal stayed during this time.
Dwell = NamedTuple("Dwell", [("start", int), ("end", int), ("chamber", str)])

# Structurally the same as a Dwell, but describes pairs of animals
CoDwell = NamedTuple("CoDwell", [("start", int), ("end", int), ("chamber", str)])

# One instance of an animal crossing from one chamber (tube or cage) to another.
# This extends the idea of a `Read`, because here the direction of travel is
# known.  `orig` and `dest` are string IDs of chambers (tubes or cages)-- the
# origin and the destination, respectively.
Traversal = NamedTuple(
    "Traversal", [("timestamp", int), ("tag_id", str), ("orig", str), ("dest", str)]
)

# The configuration for this run, mapping tag IDs to animal names and start chambers.
Config = NamedTuple(
    "Config", [("tag_id_to_name", dict), ("tag_id_to_start_chamber", dict)]
)

# Aggregate statistics for the presence of two animals in the same chamber.
# animal_a should be lexicographically less than or equal to animal_b.
# `counts` provides the number of distinct 'co-dwell' events, and `duration`
# provides the sum of the durations of those events.
# When the two animal IDs are the same, the duration should roughly match the
# length of the experiment--perhaps with some noise due to various error cases.
CoDwellAggregate = NamedTuple(
    "CoDwellAggregate",
    [("animal_a", str), ("animal_b", str), ("count", int), ("duration", float)],
)


def chamberBetween(antennaA, antennaB):
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
