#!/usr/bin/env python3

import math
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


# --- Code from yt-dlp ---
# {
def float_or_none(v, scale=1, invscale=1, default=None):
    if v is None:
        return default
    try:
        return float(v) * invscale / scale
    except (ValueError, TypeError):
        return default


def format_decimal_suffix(num, fmt='%d%s', *, factor=1000):
    """ Formats numbers with decimal sufixes like K, M, etc """
    num, factor = float_or_none(num), float(factor)
    if num is None or num < 0:
        return None
    POSSIBLE_SUFFIXES = 'kMGTPEZY'
    exponent = 0 if num == 0 else min(int(math.log(num, factor)),
                                      len(POSSIBLE_SUFFIXES))
    suffix = ['', *POSSIBLE_SUFFIXES][exponent]
    if factor == 1024:
        suffix = {'k': 'Ki', '': ''}.get(suffix, f'{suffix}i')
    converted = num / (factor ** exponent)
    return fmt % (converted, suffix)


def format_bytes(bytes):
    return format_decimal_suffix(bytes, '%.2f%sB', factor=1024) or 'N/A'


def format_resolution(format, default='unknown'):
    if format.get('vcodec') == 'none' and format.get('acodec') != 'none':
        return 'audio only'
    if format.get('resolution') is not None:
        return format['resolution']
    if format.get('width') and format.get('height'):
        return '%dx%d' % (format['width'], format['height'])
    elif format.get('height'):
        return '%sp' % format['height']
    elif format.get('width'):
        return '%dx?' % format['width']
    return default
# }
# ------------------------


def int_or_none(v, default=None):
    try:
        return int(v)
    except ValueError:
        return default


def str_or_none(v, default=None):
    return v if v else default


def make_description(format):
    for key in format.keys():
        if format[key] == "NA":
            format[key] = None
    tbr = float_or_none(format.get("tbr"))
    desc = [
        format_resolution(format),
        format.get("ext"),
        f"{int(tbr)}kb/s" if tbr else None,
        format.get("vcodec"),
        format.get("acodec"),
        format_bytes(format.get("size")),
        format.get("format_note"),
    ]
    return ", ".join([v for v in desc if v])


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
