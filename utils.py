#!/usr/bin/env python3

import re


def to_hhmmss(seconds, delim=":"):
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours:02d}{delim}{minutes - 60*hours:02d}{delim}{seconds - 60*minutes:02d}"


def to_seconds(hhmmss):
    t = re.split(r"[:,.']", hhmmss)
    if len(t) == 1:
        return int(hhmmss)
    elif len(t) == 2:
        mm, ss = t
        return int(mm)*60 + int(ss)
    hh, mm, ss = t
    return (int(hh)*60 + int(mm))*60 + int(ss)


def as_suffix(start, finish):
    start, finish = start.replace(":", "."), finish.replace(":", ".")
    return f"_{start}-{finish}"
