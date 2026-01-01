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



from collections import defaultdict
from enum import Enum
import heapq
from typing import Dict, Generator, List, Iterator

from voletron.apparatus_config import all_antennae
from voletron.constants import INFERRED_READ_EPSILON, LONG_DWELL_THRESHOLD_SECONDS
from voletron.types import CHAMBER_ERROR, CHAMBER_OUTSIDE, Antenna, ChamberName, DurationMinutes, DurationSeconds, Dwell, LongDwell, Read, TagID, TimestampSeconds, Traversal, chamberBetween
from voletron.util import seconds_between_timestamps

"""Converts a series of antenna Reads into a series of Traversals, describing
the movements of each animal from one chamber to another.  The result
incorporates heuristics needed to resolve ambiguous situations (i.e., 
consecutive reads at the same antenna, and skipped reads).

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


def short_dwell_chamber(antenna: Antenna):
    """Heuristic for which chamber an animal was likely in, given two
    consecutive reads at the same antenna with a brief time interval.
    """
    return antenna.tube


def long_dwell_chamber(antenna: Antenna):
    """Heuristic for which chamber an animal was likely in, given two
    consecutive reads at the same antenna with a long time interval.
    """
    return antenna.cage


class TwoMissingReadsException(Exception):
    def __init__(self, ambiguous_seconds: float, readA: Read, readB: Read):
        self.ambiguous_seconds = ambiguous_seconds
        self.readA = readA
        self.readB = readB


def infer_missing_read(readA: Read, readB: Read):
    """Given two non-adjacent Reads, infer a single Read between them.

    Only a single Read can be inferred by this method.  If two consecutive Reads
    were skipped, the method fails.  For instance, given a star-shaped
    apparatus, if Reads A and B are on the cage side of two different tubes,
    that suggests that *two* consecutive reads were missed, on the central arena side
    of both respective tubes.  This function does not address that situation,
    which we expect will never occur.

    There is no way to know the true timestamp of the missed Read.  It could be
    anywhere between the timestamp of Read A and that of Read B.

    On the one hand, we know (from independent video data) that the voles spend
    about half of their time in tubes, and about half in cages (or in the
    central arena).  That argument might support allocating the time equally.

    However: if the voles spent any significant time in the tube, we would
    expect more reads there.  Thus, as a simple heuristic, we allocate all of
    the ambiguous time to the central arena.

    Args:
        readA: The first (earlier) read of the non-adjacent pair.
        readB: The second (later) read of the non-adjacent pair.

    Returns: A Read that can be inserted between reads A and B, to produce a
        consistent trajectory.
    """
    for antenna in all_antennae:
        if antenna.tube == readA.antenna.tube and antenna.cage == readB.antenna.cage:
            # Tube => Central Arena case.
            infer_timestamp = TimestampSeconds(readA.timestamp + INFERRED_READ_EPSILON)  # Add epsilon to enforce sort order
            return Read(readA.tag_id, infer_timestamp, antenna)
        elif antenna.cage == readA.antenna.cage and antenna.tube == readB.antenna.tube:
            # Central Arena => Tube case.
            infer_timestamp = (
                TimestampSeconds(readB.timestamp - INFERRED_READ_EPSILON)  # Subtract epsilon to enforce sort order
            )
            return Read(readA.tag_id, infer_timestamp, antenna)

    ambiguous_seconds = readB.timestamp - readA.timestamp
    raise TwoMissingReadsException(ambiguous_seconds, readA, readB)


class ReadFate(Enum):
    Long_Cage = 0
    Short_Tube = 1
    Move = 2
    OneMissing = 3
    TwoMissing = 4


class _AnimalTrajectory:
    """Tracks the path of a single animal through the apparatus over time."""

    def __init__(self, tag_id: TagID, initial_chamber: ChamberName, start_time: TimestampSeconds, dwell_threshold: float):
        self.tag_id = tag_id
        self.chamber = initial_chamber
        self.dwell_threshold = dwell_threshold
        self.dwells = [
            Dwell(start_time, start_time, CHAMBER_OUTSIDE)
        ]  # The animal was outside the apparatus before the experiment
        self.priorRead = Read(tag_id, start_time, Antenna(CHAMBER_OUTSIDE, initial_chamber))

    def _append_dwell(self, start: TimestampSeconds, end: TimestampSeconds, chamber: ChamberName):
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
            if lastDwell.end != start:
                raise ValueError(
                    "Consecutive dwells are not adjacent.\n{}\n{}".format(
                        lastDwell.end, start
                    )
                )
            if lastDwell.chamber == chamber:
                self.dwells.pop()
                start = lastDwell.start
        self.dwells.append(Dwell(start, end, chamber))

    def update_from_read(self, read: Read) -> ReadFate:
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
              (i.e., the adjoining cage or central arena).
            * When the reads are from non-adjacent antennae, that means that the
              animal passed at least one antenna without a read being taken.  If
              only one antenna is between the two observed ones, we infer the
              missing read, and insert it into the read stream in order to
              produce a consistent trajectory.  If there are two missing reads,
              we effectively disappear the animal for the time between the two
              surrounding reads.

        Args:
            read: a Read object representing the presence of the animal at an
            Antenna.
        """
        if read.tag_id != self.tag_id:
            raise ValueError("Can't update trajectory with Read from the wrong tag.")

        if read.timestamp < self.priorRead.timestamp:
            raise ValueError(
                "Reads must arrive in chronological order: {} <= {}.  {}  {}".format(
                    read.timestamp, self.priorRead.timestamp, self.priorRead, read
                )
            )

        if not self.priorRead:
            raise ValueError("There must be a prior read.")

        if read.antenna == self.priorRead.antenna:
            seconds_between_reads = seconds_between_timestamps(
                read.timestamp, self.priorRead.timestamp
            )

            if seconds_between_reads >= self.dwell_threshold:
                dwellChamber = long_dwell_chamber(read.antenna)
                fate = ReadFate.Long_Cage
            else:
                dwellChamber = short_dwell_chamber(read.antenna)
                fate = ReadFate.Short_Tube
        else:
            dwellChamber = chamberBetween(self.priorRead.antenna, read.antenna)
            if dwellChamber:
                fate = ReadFate.Move
            else:  # At least one missing read
                try:
                    missingRead = infer_missing_read(self.priorRead, read)
                    a = self.update_from_read(missingRead)
                    assert a == ReadFate.Move
                    dwellChamber = chamberBetween(missingRead.antenna, read.antenna)
                    if not dwellChamber:
                        raise ValueError("Inferred read did not resolve the missing read situation.")
                    fate = ReadFate.OneMissing
                except TwoMissingReadsException:
                    # TODO: configurable warning threshold
                    # if e.ambiguous_seconds > 60:
                    # print(
                    #     "Missing reads, {:.2f} sec\n\t{}\n\t{}".format(
                    #         e.ambiguous_seconds, e.readA, e.readB
                    #     )
                    # )
                    dwellChamber = CHAMBER_ERROR
                    fate = ReadFate.TwoMissing

        self._append_dwell(self.priorRead.timestamp, read.timestamp, dwellChamber)
        self.priorRead = read
        return fate

    def traversals(self) -> Generator[Traversal, None, None]:
        """
        Represent the animal's Trajectory as a series of Traversals
        describing when the animal moved from one Chamber into another.

        Yields:
            A stream of Traversal objects for a single animal, in chronological
            order.
        """
        # Neglect the first "Dwell", which was outside the apparatus
        for (i, d) in enumerate(self.dwells):
            if i:
                yield Traversal(
                    d.start, self.tag_id, self.dwells[i - 1].chamber, d.chamber
                )

    def long_dwells(self) -> Generator[LongDwell, None, None]:
        for d in self.dwells:
            dwell_time = d.end - d.start
            if dwell_time > LONG_DWELL_THRESHOLD_SECONDS:
                yield LongDwell(self.tag_id, d.chamber, d.start, DurationMinutes(dwell_time / 60))

    def time_per_chamber(
        self, analysis_start_time: TimestampSeconds, analysis_end_time: TimestampSeconds
    ) -> Dict[ChamberName, DurationSeconds]:
        chamber_times : Dict[ChamberName, DurationSeconds] = defaultdict[ChamberName, DurationSeconds](lambda: DurationSeconds(0))
        for d in self.dwells:
            start = max(d.start, analysis_start_time)
            end = min(d.end, analysis_end_time)
            if end > start:
                chamber_times[d.chamber] = DurationSeconds(chamber_times[d.chamber] + (end - start))
        return chamber_times

    def get_locations_between(
        self, analysis_start_time: TimestampSeconds, analysis_end_time: TimestampSeconds
    ) -> List[str]:
        chambers = []
        for d in self.dwells:
            start = max(d.start, analysis_start_time)
            end = min(d.end, analysis_end_time)
            if end > start:
                chambers.append(d.chamber)
        return chambers

    def count_traversals_between(
        self, analysis_start_time: TimestampSeconds, analysis_end_time: TimestampSeconds
    ) -> int:
        count = 0
        for d in self.dwells:
            start = max(d.start, analysis_start_time)
            end = min(d.end, analysis_end_time)
            if end > start:
                count += 1
        return count


class AllAnimalTrajectories:
    """
    Tracks the trajectories of all animals through the apparatus, based on
    a sequence of antenna reads.
    """

    def __init__(
        self,
        start_time: TimestampSeconds,
        tag_id_to_start_chamber: Dict[TagID, ChamberName],
        reads_per_animal: Dict[TagID, List[Read]],
        dwell_threshold: float,
    ):
        self.animalTrajectories = {
            tag_id: _AnimalTrajectory(tag_id, initialChamber, start_time, dwell_threshold)
            for [tag_id, initialChamber] in tag_id_to_start_chamber.items()
        }
        fate_counts = {member: 0 for fate, member in ReadFate.__members__.items()}
        end_time = max([reads[-1].timestamp for reads in reads_per_animal.values()])
        for [tag_id, reads] in reads_per_animal.items():
            if len(reads) == 0:
                continue
            animalTrajectory = self.animalTrajectories[tag_id]
            last_read: Read = reads[0]
            for read in reads:
                fate = animalTrajectory.update_from_read(read)
                fate_counts[fate] += 1
                last_read = read
            end_read = Read(last_read.tag_id, end_time, last_read.antenna)
            fate = animalTrajectory.update_from_read(end_read)
            fate_counts[fate] += 1
        count = sum(fate_counts.values())
        self.fate_percent = {
            key.name: "{:>8} ({:>6.2%})".format(value, value / count)
            for key, value in fate_counts.items()
        }

    def traversals(self) -> Iterator[Traversal]:
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
        traversalsPerAnimal = [
            traj.traversals()
            for traj in self.animalTrajectories.values()
        ]
        
        return heapq.merge(*traversalsPerAnimal, key=lambda t: t.timestamp)

    def get_locations_between(self, tag_id: TagID, start: TimestampSeconds, end: TimestampSeconds) -> List[str]:
        return self.animalTrajectories[tag_id].get_locations_between(start, end)
