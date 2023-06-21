#!/usr/bin/env python3

import logging
import math
import re
import pathlib
import shutil
import sys
from urllib.parse import urlparse, parse_qs

from PyQt6.QtCore import QProcess, QCoreApplication


package_dir = pathlib.Path(sys.argv[0]).parent
args = None     # set in main module

logging.basicConfig(filename="yt-cut.log", encoding="utf-8",
                    format="%(asctime)s:%(module)s:%(levelname)s: %(message)s",
                    level=logging.CRITICAL)


def logger():
    return logging.getLogger("yt-cut")


def as_command(s):
    """Return command `s` as pathlib.Path object
       if available from the command line"""
    cmd = pathlib.Path(s)
    if shutil.which(s) is not None:
        return cmd

    app_dir = QCoreApplication.applicationDirPath()
    cmd = pathlib.Path(app_dir)/cmd
    if shutil.which(f"{cmd}") is not None:
        return cmd

    raise RuntimeError(f"command not available ({s})")


def yt_dlp():
    """Return path to `yt-dlp` executable"""
    return as_command(args.youtube_dl)


def ffmpeg():
    """Return path to `ffmpeg` executable"""
    return as_command(args.ffmpeg)


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


class CalledProcessError(RuntimeError):
    def __init__(self, process, msg):
        super().__init__(msg + f"\n{process.program()} {process.arguments()}")


class TimeoutExpired(CalledProcessError):
    def __init__(self, process):
        super().__init__(process, "Timeout expired, no response"
                                  " / Тайм-аут итёк, ответа нет")


class CalledProcessFailed(CalledProcessError):
    def __init__(self, process, msg=None):
        if not msg:
            msg = "Process finished with errors" \
                  " / Процесс завершился с ошибками"
        super().__init__(process, msg)


def check_output(process):
    err = decode(process.readAllStandardError())
    if has_error(err):
        pass
    elif process.exitStatus() != QProcess.ExitStatus.NormalExit:
        err = f"Exit with error code {process.error()}. " + err
    else:
        if err:
            logger().warning(err)
        out = decode(process.readAllStandardOutput())
        logger().debug(out)
        return out
    raise CalledProcessFailed(process, err)


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
    vbr = float_or_none(format.get("vbr"))
    desc = [
        format_resolution(format),
        format.get("ext"),
        f"{int(vbr)}kb/s" if vbr else None,
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
