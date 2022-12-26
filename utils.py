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


time_pat = re.compile(r"^([\d]+)[s]*$")


def get_url_time(url):
    if qs := urlparse(url).query:
        query = parse_qs(qs)
        value = query["t"][0] if "t" in query else ""
        if m := time_pat.match(value):
            return m.group(1)
    return None


err_pat = re.compile(r"error", re.IGNORECASE)


def has_error(msg):
    return err_pat.search(msg) is not None


if __name__ == "__main__":
    def ok(v):
        return "[OK]" if v else "[FAILED]"

    tests = [
        ("error", True),
        ("Error", True),
        ("ERROR", True),
        ("Error:", True),
        ("SomeError:", True),
        ("ERROR:", True),
        ("Err", False),
        ("SomeWarning:", True),
        ("WARNING", False),
    ]
    print("Test has_error(): ",
          ok(any([has_error(msg) == ans for msg, ans in tests])))
