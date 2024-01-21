#!/usr/bin/env python3

import json
import re
import pathlib
import shutil

from PyQt6.QtCore import (pyqtSignal, pyqtSlot, Qt, QObject, QProcess)
from PyQt6.QtGui import QGuiApplication

import utils as ut


options = None  # set in main window module


default_title = "Title / Название"
default_channel = "Channel / Канал"
default_format = "best available format / наилучший доступный формат"

# formats to save media files
video_format = "mp4"
audio_format = "m4a"


class YtVideo(QObject):
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

        self._formats = None
        self._content = dict(video=True, audio=True)
        self._p = None
        self._error = ""
        self._progress_re = re.compile(r"\[download\]\s+(\d{1,3}.\d)[%]")
        self._time_re = re.compile(r"time=((\d\d[:]){2}\d\d[.]\d\d)")
        self._err_re = re.compile(r"[Ee]rror")

    def request_info(self):
        self._p = QProcess()
        self._p.finished.connect(self.process_info)
        opts = self._use_cookies()
        self._p.start(f"{ut.yt_dlp()}",
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
            js = json.loads(ut.check_output(self._p))
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
            self._p = None

    def request_formats(self, filter="all[vcodec!=none]+ba"
                                     "/all[vcodec!=none][acodec!=none]/b*"):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._p = QProcess()
        opts = self._use_cookies()
        opts += self._prefer_avc()
        opts += ["--format", filter] if filter else []
        self._p.start(f"{ut.yt_dlp()}",
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
        if self._p.waitForFinished():
            QGuiApplication.restoreOverrideCursor()
            if result := ut.check_output(self._p).rstrip(",\n\r \t"):
                formats = json.loads(f'{{ "formats": [{result}] }}')["formats"]
                self._formats = dict()
                for i, fmt in zip(range(len(formats)), formats):
                    desc = ut.make_description(fmt)
                    self._formats.update({f"{i+1:02d}. {desc}": fmt})
                return
            else:
                raise ut.CalledProcessFailed(self._p)
        QGuiApplication.restoreOverrideCursor()
        raise ut.TimeoutExpired(self._p)

    def get_all_formats(self):
        return list(self._formats.keys())

    def get_media_format(self):
        if self._content["video"]:
            return video_format
        elif self._content["audio"]:
            return audio_format
        raise RuntimeError("no video, no audio")

    def get_affix(self, start, finish, format):
        res = ut.format_resolution(self._formats[format])
        if self._is_full_video(start, finish):
            return f"_{res}"
        tm_code = ut.as_suffix(start, finish)
        return f"_{res}_{tm_code}"

    def get_suffix(self):
        return f".{self.get_media_format()}"

    def set_content(self, content):
        self._content.update(video=content["video"],
                             audio=content["audio"])

    def start_download(self, filename, start, end, format):
        cmd, opts = self._download_command(filename, start, end, format)
        ut.logger().debug(f"{cmd} {opts}")
        self._p = QProcess()
        mode = QProcess.ProcessChannelMode
        self._p.setProcessChannelMode(mode.MergedChannels)
        self._p.readyRead.connect(self.parse_progress)
        self._p.finished.connect(self.finish_download)
        self._p.start(cmd, opts)

    @pyqtSlot()
    def parse_progress(self):
        result = ut.decode(self._p.readAll())
        ut.logger().debug(result)
        if m := re.search(self._progress_re, result):
            val = float(m.group(1))
            self.progress.emit(val, "%")
        elif m := re.search(self._time_re, result):
            time = m.group(1)
            self.progress.emit(ut.from_ffmpeg_time(time), "s")
        elif m := re.search(self._err_re, result):
            self._error = result

    def cancel_download(self):
        if self._p.state() == QProcess.ProcessState.NotRunning:
            self.finish_download(self._p.exitCode(), self._p.exitStatus())
        else:
            self._p.kill()

    @pyqtSlot(int, QProcess.ExitStatus)
    def finish_download(self, code, status):
        self._p = None
        ok = (status == QProcess.ExitStatus.NormalExit) and (code == 0)
        err, self._error = self._error, ""
        self.finished.emit(ok, err)

    def _use_cookies(self):
        browser = options.browser if options else None
        return ["--cookies-from-browser", browser] if browser else []

    def _prefer_avc(self):
        if options and options.prefer_avc:
            return ["-S", "quality,vcodec:h264,acodec:mp3"]
        return []

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
        urls = self._formats[format]["urls"].split()
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

    def _ffmpeg_set_vbr(self, format):
        vbr = options.vbr if options else None
        if vbr == "original":
            val = ut.float_or_none(self._formats[format]["vbr"])
            vbr = f"{val}k" if val else None
        elif vbr == "auto":
            vbr = None
        return ["-b:v", f"{vbr}"] if vbr else []

    def _ffmpeg_debug(self):
        debug = options.debug if options else None
        return ["-report"] if debug["ffmpeg"] else []

    def _ffmpeg_xerror(self):
        xerr = options.xerror if options else None
        return ["-xerror"] if xerr else []

    def _ffmpeg_output(self):
        op = []
        if not self._content["video"]:
            op += ["-vn"]
        if not self._content["audio"]:
            op += ["-an"]
        return op

    def _is_full_video(self, start, end):
        return ut.to_seconds(start) == 0 and end == self.duration

    def _download_command(self, filename, start, end, format):
        if self._is_full_video(start, end):
            return self._by_yt_dlp(filename, start, end, format)
        else:
            return self._by_ffmpeg(filename, start, end, format)

    def _by_ffmpeg(self, filename, start, end, format):
        opts = []
        opts += self._ffmpeg_use_gpu()
        opts += self._ffmpeg_source(start, end, format)
        opts += self._ffmpeg_codecs()
        opts += self._ffmpeg_set_vbr(format)
        opts += self._ffmpeg_debug()
        opts += self._ffmpeg_xerror()
        opts += self._ffmpeg_output()
        return f"{ut.ffmpeg()}", opts + ["-y", f"{filename}"]

    def _yt_dlp_output(self, filename):
        file = pathlib.Path(filename)
        path, filename = file.parent, file.stem

        op = ["--paths", f"{path}",
              "--output", f"{filename}.%(ext)s"]

        if not self._content["video"]:
            op += ["--postprocessor-args", "Merger+ffmpeg_o:-vn"]
        if not self._content["audio"]:
            op += ["--postprocessor-args", "Merger+ffmpeg_o:-an"]

        op += ["--remux-video", self.get_media_format()]

        return op

    def _by_yt_dlp(self, filename, start, end, format):
        opts = self._use_cookies()
        try:
            ffmpeg = shutil.which(ut.ffmpeg())  # raise exception if no ffmpeg
            opts += ["--ffmpeg-location", f"{ffmpeg}",
                     "--embed-thumbnail"]
        except RuntimeError:
            pass
        opts += ["--no-playlist",
                 "--force-overwrites",
                 "--format", self._formats[format]["format_id"]]
        opts += self._yt_dlp_output(filename)
        return f"{ut.yt_dlp()}", opts + [f"{self.url}"]
