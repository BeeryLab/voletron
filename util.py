import datetime

def seconds_between_timestamps(a, b):
    # Avoid knowing whether timestamps are sec, msec, or usec.
    # TODO: (performance) compute this directly in sec, without
    # converting back and forth
    return abs((
        datetime.datetime.fromtimestamp(a)
        - datetime.datetime.fromtimestamp(b)
    ).total_seconds())