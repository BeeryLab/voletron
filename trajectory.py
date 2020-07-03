from collections import namedtuple
import datetime
import parse
import sys
from core import Dwell, Read, Traversal
from config import InitialChambers, all_antennae

"""Converts a series of antenna Reads into a series of Traversals, describing
the movements of each animal from one chamber to another.  The result
incorporates heuristics needed to resolve ambiguous situations (i.e., 
consecitev reads at the same antenna, and skipped reads).

Note it is not possible to perform the desired analysis in a streaming manner
using only one pass over the raw inputs.  This is because the sequence of
Traversals is not known until the entire raw input has been parsed.  For
instance: when we encounter a read that requires inferring a prior missing read,
we may insert the inferred read substantially in the past--at a time that would
already have been processed in a streaming approach.

Thus, two passes are needed: one over the raw reads, and a second over the
derived trajectories.  For now we simply hold the trajectories in memory to
support the second pass.  Optionally they could be written to disk, and re-read
for the next phase.
"""


def shortDwellChamber(antenna):
    """Heuristic for which chamber an animal was likely in, given two
    consecutive reads at the same antenna with a brief time interval.
    """
    return antenna.tube


def longDwellChamber(antenna):
    """Heuristic for which chamber an animal was likely in, given two
    consecutive reads at the same antenna with a long time interval.
    """
    return antenna.cage


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


def inferMissingRead(readA, readB):
    """Given two non-adjacent Reads, infer a single Read between them.

    Only a single Read can be inferred by this method.  If two consecutive Reads
    were skipped, the method fails.  For instance, given a star-shaped
    apparatus, if Reads A and B are on the cage side of two different tubes,
    that suggests that *two* consecutive reads were missed, on the arena side
    of both respective tubes.  This function does not address that situation,
    which we expect will never occur.

    There is no way to know the true timestamp of the missed Read.  It could be
    anywhere between the timestamp of Read A and that of Read B.  Here, as a 
    simple heuristic, we assign the time halfway between the two known reads to
    the inferred read.  This is supported by the observation (from independent
    video data) that the voles spend about half of their time in tubes, and
    about half in cages (or in the arena).

    Args:
        readA: The first (earlier) read of the non-adjacent pair.
        readB: The second (later) read of the non-adjacent pair.
    
    Returns: A Read that can be inserted between reads A and B, to produce a
        consistent trajectory.
    """
    for antenna in all_antennae:
        if antenna.tube == readA.antenna.tube and antenna.cage == readB.antenna.cage:
            # Tube => Arena case.
            # TODO: consider best allocation
            infer_timestamp = (readA.timestamp + readB.timestamp) / 2
            # print("{} -> {} <- {}".format(readA.timestamp, infer_timestamp, readB.timestamp))
            return Read(readA.tag_id, infer_timestamp, antenna)
        elif antenna.cage == readA.antenna.cage and antenna.tube == readB.antenna.tube:
            # Arena => Tube case.
            # TODO: consider best allocation
            infer_timestamp = (readA.timestamp + readB.timestamp) / 2
            return Read(readA.tag_id, infer_timestamp, antenna)
    raise ValueError(
        "Failed to infer missing read between:\n{}\n{}".format(readA, readB)
    )


class AnimalTrajectory:
    """Tracks the path of a single animal through the apparatus over time."""

    def __init__(self, tag_id, initial_chamber):
        self.tag_id = tag_id
        self.chamber = initial_chamber
        self.dwells = []
        self.priorRead = None

    def _appendDwell(self, begin, end, chamber):
        """
        Records that the animal was in a chamber during a time interval.

        This method enforces that the beginning of the current dwell matches the
        end of the previous one.  Thus, this method must be called in
        chronological order, and the animal must always be in exactly one
        chamber.

        If the animal was already in the specified chamber, the preexisting
        Dwell record is extended, rather than adding a new one.
        """
        if self.dwells:
            lastDwell = self.dwells[-1]
            if lastDwell.end != begin:
                raise ValueError(
                    "Consecutive dwells are not adjacent.\n{}\n{}".format(
                        lastDwell.end, begin
                    )
                )
            if lastDwell.chamber == chamber:
                self.dwells.pop()
                begin = lastDwell.begin
        self.dwells.append(Dwell(begin, end, chamber))

    def updateFromRead(self, read):
        """
        Extends the tracked Trajectory based on a new Read.
        
        Compares this read to the previous one, to determine where the animal
        was in between the two reads.

        There are three cases:
            * When the reads are from adjacent antennae, the animal was clearly
              in the chamber between the antennae.
            * When the reads are from the same antenna, we apply a heuristic
              based on the time between reads.  For a dwell time less than 10
              sec, choose one chamber (i.e., the adjoining tube).  For a dwell
              time greater than or equal to 10 sec, choose another chamber
              (i.e., the adjoining cage or arena).
            * When the reads are from non-adjacent antennae, that means that the
              animal passed at least one antenna without a read being taken.  In
              this case we infer the missing read, and insert it into the read
              stream in order to produce a consistent trajectory.
    
        Args:
            read: a Read object representing the presence of the animal at an
              Antenna.
        """
        if read.tag_id != self.tag_id:
            raise ValueError("Can't update trajectory with Read from the wrong tag.")

        if self.priorRead and read.timestamp < self.priorRead.timestamp:
            raise ValueError("Reads must arrive in chronological order")

        if not self.priorRead:
            self.priorRead = read
            # Neglect the initial stay in the Arena.
            return

        if read.antenna == self.priorRead.antenna:
            # Avoid knowing whether timestamps are sec, msec, or usec.
            # TODO: (performance) compute this directly in sec, without
            # converting back and forth
            seconds_between_reads = (
                datetime.datetime.fromtimestamp(read.timestamp)
                - datetime.datetime.fromtimestamp(self.priorRead.timestamp)
            ).total_seconds()

            # TODO: make the dwell time threshold configurable.
            if seconds_between_reads >= 10:
                dwellChamber = longDwellChamber(read.antenna)
            else:
                dwellChamber = shortDwellChamber(read.antenna)
        else:
            dwellChamber = chamberBetween(self.priorRead.antenna, read.antenna)
            if not dwellChamber:
                try:
                    missingRead = inferMissingRead(self.priorRead, read)
                    self.updateFromRead(missingRead)
                    self.updateFromRead(read)
                    return
                except ValueError as e:
                    print(e)
                    dwellChamber = "ERROR"

        self._appendDwell(self.priorRead.timestamp, read.timestamp, dwellChamber)

        self.priorRead = read

    def traversals(self):
        """
        Represent the animal's Trajectory as a series of Traversals
        describing when the animal moved from one Chamber into another.

        Yields:
            A stream of Traversal objects for a single animal, in chronological
            order.
        """
        for (i, d) in enumerate(self.dwells):
            yield Traversal(d.begin, self.tag_id, self.dwells[i - 1].chamber, d.chamber)


class AllAnimalTrajectories:
    """
    Tracks the trajectories of all animals through the apparatus, based on
    reading a file of 'raw' antenna reads.
    """

    def __init__(self):
        # {tag_id: AnimalTrajectory}
        # self.animalTrajectories = dict(
        #    map(lambda x: [x[0], AnimalTrajectory(x[0], x[1])], InitialChambers.items())
        # )
        self.animalTrajectories = {
            tag_id: AnimalTrajectory(tag_id, initialChamber)
            for (tag_id, initialChamber) in InitialChambers.items()
        }

    # TODO: factor file reading and parsing out; this should accept an iterable of Reads.
    def update_trajectories_from_raw_file(self, filename):
        with open(filename) as file:
            file.readline()
            # skip headers
            for line in file:
                read = parse.parse_raw_line(line.rstrip())
                if read:
                    try:
                        animalTrajectory = self.animalTrajectories[read.tag_id]
                        animalTrajectory.updateFromRead(read)
                    except KeyError:
                        print("UNKNOWN TAG: {}".format(read.tag_id))

    def traversals(self):
        """
        Provides all Traversals of all animals through the apparatus, in
        chronological order.  This differs from the sequence of Reads in that
        a Traversal (unlike a Read) describes the direction of travel of the
        animal.  Also, consecutive reads at the same antenna have now been
        collapsed (and interpreted), and inconsistencies due to missing reads
        have been resolved.

        Yields:
            A stream of Traversal objects for all animals, in chronological
            order.
        """
        # traversalsPerAnimal = map(
        #    lambda x: (x[0], x[1].traversals), self.animalTrajectories.items()
        # )
        traversalsPerAnimal = {
            tag_id: traj.traversals()
            for (tag_id, traj) in self.animalTrajectories.items()
        }
        peeks = {tag_id: trav.__next__() for (tag_id, trav) in traversalsPerAnimal.items()}
        while peeks:
            next_tag_id = min(peeks, key=(lambda x: peeks[x].timestamp))
            result = peeks[next_tag_id]
            try:
                peeks[next_tag_id] = traversalsPerAnimal[next_tag_id].__next__()
            except StopIteration:
                del peeks[next_tag_id]
            yield result


def main(argv):
    filename = argv[1]
    all = AllAnimalTrajectories()
    all.update_trajectories_from_raw_file(filename)
    for t in all.traversals():
        print(t)
        pass


main(sys.argv)

# TODO: specify time range to analyze
