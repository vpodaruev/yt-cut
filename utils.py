#!/usr/bin/env python3

import re
from urllib.parse import urlparse, parse_qs


def to_hhmmss(seconds, delim=":"):
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours:02d}{delim}{minutes - 60*hours:02d}" \
           f"{delim}{seconds - 60*minutes:02d}"


def to_seconds(hhmmss):
    tt = [int(x) if x else 0 for x in re.split(r"[:,.' ]", hhmmss)]
    s = 0
    for x, n in zip(reversed(tt), range(len(tt))):
        s += x * 60**n
    return s


def from_ffmpeg_time(hhmmss):
    hh, mm, ss = [float(x) for x in hhmmss.split(":")]
    return (hh*60 + mm)*60 + ss


def as_suffix(start, finish):
    start, finish = start.replace(":", "."), finish.replace(":", ".")
    return f"_{start}-{finish}"


def decode(msg):
    return bytes(msg).decode("utf8", "replace")


def get_url_time(url):
    if qs := urlparse(url).query:
        query = parse_qs(qs)
        if "t" in query:
            return query["t"][0]
    return None
