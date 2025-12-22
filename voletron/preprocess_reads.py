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


from typing import Dict, Iterable, List
from voletron.types import AnimalName, Read, TagID, TimestampSeconds, chamberBetween


def preprocess_reads(
    reads: Iterable[Read], tag_ids: Iterable[TagID], tag_id_to_name: Dict[TagID, AnimalName]
) -> Dict[TagID, List[Read]]:
    # Normalize the reads per animal by spacing them out in time a bit and
    # swapping the order of nearly-simultaneous reads for increased parsimony.
    reads_per_animal = split_reads_per_animal(reads, tag_ids)

    print("\nPreprocessing:")
    print("-----------------------------")
    for [tag_id, animal_reads] in reads_per_animal.items():
        # mutating
        _spaced_reads(animal_reads)
        _parsimonious_reads(tag_id, animal_reads, tag_id_to_name)
    return reads_per_animal


def split_reads_per_animal(
    reads: Iterable[Read], tag_ids: Iterable[TagID]
) -> Dict[TagID, List[Read]]:
    result = {tag_id: [] for tag_id in tag_ids}
    for read in reads:
        try:
            result[read.tag_id].append(read)
        except KeyError:
            print("    *** UNKNOWN TAG: {} ***".format(read.tag_id))
    return result


def _spaced_reads(reads: List[Read]) -> None:
    """Space out nearly-simultaneous reads slightly in time.

    Mutates the provided `reads`.
    """
    # Two exactly simultaneous reads are not impossible, because the sensors
    # are slow and effectively add noise in time.
    # To deal with this, we simply add 2 ms to the second read.
    # We do this to leave room for a possible "missing read" between them.
    # It may be that the two near-simultaneous reads end up out of order.
    # In this case, most likely, two additional reads would be inferred,
    # making it appear that the animal rapidly zig-zagged about.
    # The "parsimony" transformation below resolves these situations by swapping the two reads in time.
    for i in range(0, len(reads) - 1):
        [a, b] = reads[i : i + 2]
        b_orig = b.timestamp

        if abs(b.timestamp - a.timestamp) < 0.002:
            b_new = TimestampSeconds(((a.timestamp * 1000) + 2) / 1000)  # float precision shenanigans
            b = Read(b.tag_id, b_new, b.antenna)
            reads[i + 1] = b
            jitter = b_new - b_orig
            # print("Jitter: {}: {} -> {} ({})".format(a.timestamp, b_orig, b_new, jitter))
            if jitter > 0.003:
                print("Jitter > 3 msec!")


def _parsimonious_reads(
    tag_id: TagID, reads: List[Read], tag_id_to_name: Dict[TagID, AnimalName]
) -> None:
    """Swap the order of nearly-simultaneous reads when it makes sense.

    Mutates the provided `reads`.
    """
    count = 0
    for i in range(0, len(reads) - 4):
        [a, b, c, d] = reads[i : i + 4]
        if abs(c.timestamp - b.timestamp) < 0.010:
            # Middle two reads are close enough to consider swapping them, if parsimonious.
            # Each of these values is True if the read pair is parsimonious, false otherwise
            ab = a.antenna == b.antenna or (
                chamberBetween(a.antenna, b.antenna) != None
            )
            ac = a.antenna == c.antenna or (
                chamberBetween(a.antenna, c.antenna) != None
            )
            bc = b.antenna == c.antenna or (
                chamberBetween(b.antenna, c.antenna) != None
            )
            bd = b.antenna == d.antenna or (
                chamberBetween(b.antenna, d.antenna) != None
            )
            cd = c.antenna == d.antenna or (
                chamberBetween(c.antenna, d.antenna) != None
            )

            if bc == None:
                print("Simultaneous disparate reads: {} {}".format(b, c))
            else:
                if ac + bd > ab + cd:  # Greater parsimony if we swap b and c
                    count += 1
                    c_earlier = Read(c.tag_id, b.timestamp, c.antenna)
                    b_later = Read(b.tag_id, c.timestamp, b.antenna)
                    reads[i : i + 4] = [a, c_earlier, b_later, d]

    print("Parsimony swaps: {} {}".format(tag_id_to_name[tag_id], count))
