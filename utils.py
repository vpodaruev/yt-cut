#!/usr/bin/env python3

import re


def to_hhmmss(seconds, delim=":"):
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours:02d}{delim}{minutes - 60*hours:02d}{delim}{seconds - 60*minutes:02d}"


def to_seconds(hhmmss):
    tt = [int(x) if x else 0 for x in re.split(r"[:,.']", hhmmss)]
    s = 0
    for x, n in zip(reversed(tt), range(len(tt))):
        s += x * 60**n
    return s


def as_suffix(start, finish):
    start, finish = start.replace(":", "."), finish.replace(":", ".")
    return f"_{start}-{finish}"
