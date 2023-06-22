#!/usr/bin/env python3

import json
import re
import pathlib

from PyQt6.QtCore import (pyqtSignal, pyqtSlot, Qt, QObject, QProcess)
from PyQt6.QtGui import QGuiApplication

import utils as ut


options = None  # set in main window module


default_title = "Title / Название"
default_channel = "Channel / Канал"
default_format = "best available format / наилучший доступный формат"


class YoutubeVideo(QObject):
    info_loaded = pyqtSignal()
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool, str)
    info_failed = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.title = default_title
        self.channel = default_channel
        self.thumbnail = None
        self.duration = "0"
        self.formats = None
        self.p = None
        self.progress_re = re.compile(r"\[download\]\s+(\d{1,3}.\d)[%]")
        self.time_re = re.compile(r"time=((\d\d[:]){2}\d\d[.]\d\d)")
        self.err_re = re.compile(r"[Ee]rror")
        self.debug = False
        self.error = ""

    def _ytdl_cookies(self):
        browser = options.browser if options else None
        return ["--cookies-from-browser", browser] if browser else []

    def request_info(self):
        self.p = QProcess()
        self.p.finished.connect(self.process_info)
        opts = self._ytdl_cookies()
        self.p.start(f"{ut.yt_dlp()}",
                     opts + ["--no-playlist", "--print",
                             '{ "channel": %(channel)j'
                             ', "uploader": %(uploader)j'
                             ', "title": %(title)j'
                             ', "thumbnail": %(thumbnail)j'
                             ', "duration": %(duration)j }',
                             f"{self.url}"])
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    @pyqtSlot()
    def process_info(self):
        QGuiApplication.restoreOverrideCursor()
        try:
            js = json.loads(ut.check_output(self.p))
            self.channel = js["channel"] if js["channel"] != "NA" \
                else js["uploader"]
            self.title = js["title"]
            self.thumbnail = js["thumbnail"]
            self.duration = ut.to_hhmmss(ut.int_or_none(js["duration"], 0))
            self.info_loaded.emit()
        except ut.CalledProcessFailed as e:
            ut.logger().exception(f"{e}")
            self.info_failed.emit(f"{e}")
        finally:
            self.p = None

    def _prefer_avc(self):
        if options and options.prefer_avc:
            return ["-S", "quality,vcodec:h264,acodec:mp3"]
        return []

    def request_formats(self, filter="all[vcodec!=none]+ba"
                                     "/all[vcodec!=none][acodec!=none]/b*"):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.p = QProcess()
        opts = self._ytdl_cookies()
        opts += self._prefer_avc()
        opts += ["--format", filter] if filter else []
        self.p.start(f"{ut.yt_dlp()}",
                     opts + ["--no-playlist", "--print",
                             '{ "format_id": %(format_id)j'
                             ', "ext": %(ext)j'
                             ', "resolution": %(resolution)j'
                             ', "width": %(width)j'
                             ', "height": %(height)j'
                             ', "vbr": %(vbr)j'
                             ', "vcodec": %(vcodec)j'
                             ', "acodec": %(acodec)j'
                             ', "size": %(filesize,filesize_approx)j'
                             ', "format_note": %(format_note)j'
                             ', "urls": %(urls)j }, ',
                             f"{self.url}"])
        if self.p.waitForFinished():
            QGuiApplication.restoreOverrideCursor()
            if result := ut.check_output(self.p).rstrip(",\n\r \t"):
                formats = json.loads(f'{{ "formats": [{result}] }}')["formats"]
                self.formats = dict()
                for i, fmt in zip(range(len(formats)), formats):
                    desc = ut.make_description(fmt)
                    self.formats.update({f"{i+1:02d}. {desc}": fmt})
                return
            else:
                raise ut.CalledProcessFailed(self.p)
        QGuiApplication.restoreOverrideCursor()
        raise ut.TimeoutExpired(self.p)

    def get_formats(self):
        return list(self.formats.keys())

    def get_suffix(self, start, finish, format):
        res = ut.format_resolution(self.formats[format])
        if self._is_full_video(start, finish):
            return f"_{res}"
        tm_code = ut.as_suffix(start, finish)
        return f"_{res}_{tm_code}"

    def get_extension(self, format):
        return ut.str_or_none(self.formats[format]["ext"], "mp4")

    def _ffmpeg_use_gpu(self):
        codecs = options.codecs
        if not codecs or not codecs["video"].endswith("_nvenc"):
            return []
        return ["-vsync", "0",
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda"]

    def _ffmpeg_source(self, start, end, format):
        time = []
        if ut.to_seconds(start) != 0:    # fix video trimming at the begin
            time += ["-ss", f"{start}"]
        if end != self.duration:         # fix video trimming at the end
            time += ["-to", f"{end}"]
        urls = self.formats[format]["urls"].split()
        if len(urls) == 2:
            video, audio = urls
            return time + ["-i", f"{video}"] + \
                   time + ["-i", f"{audio}"]
        elif len(urls) == 1:
            video, = urls
            return time + ["-i", f"{video}"]
        raise RuntimeError(f"download URLs: {urls}")

    def _ffmpeg_codecs(self):
        codecs = options.codecs if options else None
        return ["-c:v", codecs["video"],
                "-c:a", codecs["audio"]] if codecs else []

    def _ffmpeg_keep_vbr(self, format):
        keep_vbr = options.keep_vbr if options else None
        vbr = ut.float_or_none(self.formats[format]["vbr"])
        return ["-b:v", f"{vbr}K"] if vbr and keep_vbr else []

    def _ffmpeg_debug(self):
        debug = options.debug if options else None
        return ["-report"] if debug["ffmpeg"] else []

    def _ffmpeg_xerror(self):
        xerr = options.xerror if options else None
        return ["-xerror"] if xerr else []

    def _is_full_video(self, start, end):
        return ut.to_seconds(start) == 0 and end == self.duration

    def _by_ffmpeg(self, filename, start, end, format):
        opts = []
        opts += self._ffmpeg_use_gpu()
        opts += self._ffmpeg_source(start, end, format)
        opts += self._ffmpeg_codecs()
        opts += self._ffmpeg_keep_vbr(format)
        opts += self._ffmpeg_debug()
        opts += self._ffmpeg_xerror()
        return f"{ut.ffmpeg()}", opts + ["-y", f"{filename}"]

    def _by_yt_dlp(self, filename, start, end, format):
        file = pathlib.Path(filename)
        path, filename = file.parent, file.stem
        opts = self._ytdl_cookies()
        opts += ["--no-playlist",
                 "--force-overwrites",
                 "--embed-thumbnail",
                 "--format", self.formats[format]["format_id"],
                 "--remux-video", "mp4",
                 "--paths", f"{path}",
                 "--output", f"{filename}"]
        return f"{ut.yt_dlp()}", opts + [f"{self.url}"]

    def start_download(self, filename, start, end, format):
        cmd, opts = self._by_yt_dlp(filename, start, end, format) \
                    if self._is_full_video(start, end) else \
                    self._by_ffmpeg(filename, start, end, format)
        self.p = QProcess()
        mode = QProcess.ProcessChannelMode
        self.p.setProcessChannelMode(mode.MergedChannels)
        self.p.readyRead.connect(self.parse_progress)
        self.p.finished.connect(self.finish_download)
        self.p.start(cmd, opts)

    @pyqtSlot()
    def parse_progress(self):
        result = ut.decode(self.p.readAll())
        ut.logger().debug(result)
        if m := re.search(self.progress_re, result):
            val = float(m.group(1))
            self.progress.emit(val, "%")
        elif m := re.search(self.time_re, result):
            time = m.group(1)
            self.progress.emit(ut.from_ffmpeg_time(time), "s")
        elif m := re.search(self.err_re, result):
            self.error = result

    def cancel_download(self):
        if self.p.state() == QProcess.ProcessState.NotRunning:
            self.finish_download(self.p.exitCode(), self.p.exitStatus())
        else:
            self.p.kill()

    @pyqtSlot(int, QProcess.ExitStatus)
    def finish_download(self, code, status):
        self.p = None
        ok = (status == QProcess.ExitStatus.NormalExit) and (code == 0)
        err, self.error = self.error, ""
        self.finished.emit(ok, err)
