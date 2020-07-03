from collections import namedtuple

Antenna = namedtuple('Antenna', ['tube', 'cage'])

Read = namedtuple('Read', ['tag_id', 'timestamp', 'antenna'])

Dwell = namedtuple('Dwell', ['begin', 'end', 'chamber'])

Traversal = namedtuple('Traversal', ['timestamp', 'tag_id', 'orig', 'dest'])

# Colocation = namedtuple('Colocation', ['animalA', 'animalB', 'begin', 'end'])
