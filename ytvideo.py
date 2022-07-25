#!/usr/bin/env python3

import json
import subprocess as sp

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject, QProcess
from PyQt6.QtGui import QGuiApplication

from utils import *


global args     # set in main module
global options  # same thing

class NotYoutubeURL(RuntimeError):
    def __init__(self, url):
        super().__init__(f"Seems not a youtube URL / Похоже, это не ютуб ссылка\nURL: '{url}'")

class CalledProcessError(RuntimeError):
    def __init__(self, process, msg):
        super().__init__(msg + f"\n{process.program()} {process.arguments()}")

class TimeoutExpired(CalledProcessError):
    def __init__(self, process):
        super().__init__(process, f"Timeout expired, no response / Тайм-аут итёк, ответа нет")

class CalledProcessFailed(CalledProcessError):
    def __init__(self, process, msg=None):
        if not msg:
            msg = "Process finished with errors / Процесс завершился с ошибками"
        super().__init__(process, msg)


class YoutubeVideo(QObject):
    info_loaded = pyqtSignal()
    progress = pyqtSignal(float)
    finished = pyqtSignal(bool)
    error_occured = pyqtSignal(str)
    default_title = "Title / Название"
    default_channel = "Channel / Канал"
    browsers = ["brave", "chrome", "chromium", "edge",
                "firefox", "opera", "safari", "vivaldi"]
    video_codecs = {
        "copy": "Copy from source",
        "h264": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (Intel Quick Sync Video acceleration)",
        "mpeg4": "MPEG-4 part 2"
    }
    audio_codecs = {
        "copy": "Copy from source",
        "aac": "AAC (Advanced Audio Coding)",
        "mp3": "libmp3lame MP3 (MPEG audio layer 3)",
        
    }
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.title = self.default_title
        self.channel = self.default_channel
        self.duration = "0"
        self.p = None
        self.time_re = re.compile(r"time=((\d\d[:]){2}\d\d[.]\d\d)")
        self.debug = False
    
    def _check_result(self):
        err = decode(self.p.readAllStandardError())
        if err:
            pass
        elif self.p.exitStatus() != QProcess.ExitStatus.NormalExit:
            err = f"Exit with error code {self.p.error()}."
        else:
            return decode(self.p.readAllStandardOutput())
        raise CalledProcessFailed(self.p, err)
    
    def _ytdl_cookies(self):
        browser = options.get_browser() if options else None
        return ["--cookies-from-browser", browser] if browser else []
    
    def request_info(self):
        self.p = QProcess()
        self.p.finished.connect(self.process_info)
        opts = self._ytdl_cookies()
        self.p.start(f"{args.youtube_dl}", opts + ["--dump-json", f"{self.url}"])
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    @pyqtSlot()
    def process_info(self):
        QGuiApplication.restoreOverrideCursor()
        try:
            js = json.loads(self._check_result())
            self.channel = js["channel"] if "channel" in js else ""
            if "title" in js:
                self.title = js["title"]
            if "duration" in js:
                self.duration = to_hhmmss(js["duration"])
            self.info_loaded.emit()
        except CalledProcessFailed as e:
            self.error_occured.emit(f"{e}")
        finally:
            self.p = None
    
    def download_urls(self):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.p = QProcess()
        opts = self._ytdl_cookies()
        self.p.start(f"{args.youtube_dl}", opts + ["-g", f"{self.url}"])
        if self.p.waitForFinished():
            QGuiApplication.restoreOverrideCursor()
            if result := self._check_result():
                return result.split()
            else:
                raise CalledProcessFailed(p)
        QGuiApplication.restoreOverrideCursor()
        raise TimeoutExpired(p)
    
    def _ffmpeg_source(self, start, end):
        time = ["-ss", f"{start}"]
        if end != self.duration:       # fix video trimming at the end
            time += ["-to", f"{end}"]
        urls = self.download_urls()
        if len(urls) == 2:
            video, audio = urls
            return time + ["-i", f"{video}"] + \
                   time + ["-i", f"{audio}"]
        elif len(urls) == 1:
            video, = urls
            return time + ["-i", f"{video}"]
        raise RuntimeError("download URLs: " + str(urls))
    
    def _ffmpeg_codecs(self):
        codecs = options.get_codecs() if options else None
        return ["-c:v", codecs["video"], "-c:a", codecs["audio"]] if codecs else []
    
    def _ffmpeg_debug(self):
        opts = []
        if options and options.need_debug():
            opts += ["-report"] if options.get_logging() else []
        return opts
    
    def download(self, filename, start, end):
        opts = []
        opts += self._ffmpeg_source(start, end)
        opts += self._ffmpeg_codecs()
        opts += self._ffmpeg_debug()
        self.p = QProcess()
        self.p.readyReadStandardError.connect(self.parse_progress)
        self.p.finished.connect(self.finish_download)
        self.p.start(f"{args.ffmpeg}", opts + ["-y", f"{filename}"])
    
    @pyqtSlot()
    def parse_progress(self):
        result = decode(self.p.readAllStandardError())
        if m := re.search(self.time_re, result):
            time = m.group(1)
            self.progress.emit(from_ffmpeg_time(time))
    
    def cancel_download(self):
        if self.p.state() == QProcess.ProcessState.NotRunning:
            self.finish_download(self.p.exitCode(), self.p.exitStatus())
        else:
            self.p.kill()
    
    @pyqtSlot(int, QProcess.ExitStatus)
    def finish_download(self, code, status):
        self.p = None
        ok = (status == QProcess.ExitStatus.NormalExit) and (code == 0)
        self.finished.emit(ok)
