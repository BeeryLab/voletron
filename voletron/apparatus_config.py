from voletron.structs import Antenna

# TODO: consider how to represent the apparatus config as data (e.g., json), not as
# code.

# Maps the Olcus ID of each antenna to an Antenna object representing its
# location in the apparatus.  Each tube has two antennae; the second field of
# the Antenna object gives the string ID of the chamber to which that end of
# the tube is connected.
#
# Note this implicitly describes the physical layout of the apparatus.
# In particular, one recording setup reads data from two disconnected habitats:
# One in which Cages 1-5 all connect to Arena A, and a second in which Cages
# 6-10 connect to Arena B.
olcus_id_to_antenna_hardcode = {
    0: {  # device 0
        0: Antenna("Tube1", "ArenaA"),
        1: Antenna("Tube1", "Cage1"),
        2: Antenna("Tube2", "ArenaA"),
        3: Antenna("Tube2", "Cage2"),
        4: Antenna("Tube3", "ArenaA"),
        5: Antenna("Tube3", "Cage3"),
    },
    1: {  # device 1
        0: Antenna("Tube4", "ArenaA"),
        1: Antenna("Tube4", "Cage4"),
        2: Antenna("Tube5", "ArenaA"),
        3: Antenna("Tube5", "Cage5"),
        4: Antenna("Tube6", "ArenaB"),
        5: Antenna("Tube6", "Cage6"),
    },
    2: {  # device 2
        0: Antenna("Tube7", "ArenaB"),
        1: Antenna("Tube7", "Cage7"),
        2: Antenna("Tube8", "ArenaB"),
        3: Antenna("Tube8", "Cage8"),
        4: Antenna("Tube9", "ArenaB"),
        5: Antenna("Tube9", "Cage9"),
    },
    3: {
        0: Antenna("Tube10", "ArenaB"),
        1: Antenna("Tube10", "Cage10"),
    },  # device 3
}

all_antennae = [
    antenna
    for (device, antennae) in olcus_id_to_antenna_hardcode.items()
    for (index, antenna) in antennae.items()
]

all_chambers = sorted(
    list(set([item for a in all_antennae for item in [a.tube, a.cage]]))
)
all_chambers.append("ERROR")

# Maps Tag IDs to the initial chamber for each animal.
# InitialChambers = {
#     "972273000583241": "ArenaA",
#     "972273000591811": "ArenaA",
#     "972273000585334": "ArenaA",
#     "972273000584934": "ArenaA",
#     "972273000591336": "ArenaB",
#     "972273000592118": "ArenaB",
#     "972273000583609": "ArenaB",
#     "972273000584356": "ArenaB",
#     "972273000585057": "ArenaB",
#     # "97227300058356" : "ArenaB",  # Tag broken, exclude (??)
#     "972273000588368": "ArenaB",
#     "972273000583889": "ArenaB",
#     "972273000585644": "ArenaB",
# }
