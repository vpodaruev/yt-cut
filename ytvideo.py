#!/usr/bin/env python3

import json
import subprocess as sp
from urllib.parse import urlparse

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject, QProcess
from PyQt6.QtGui import QGuiApplication

from utils import *


global args  # set in main module

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
    error_occured = pyqtSignal(str)
    default_title = "Title / Название"
    default_channel = "Channel / Канал"
    
    def __init__(self, url):
        super().__init__()
        netloc = urlparse(url).netloc
        if all([item not in netloc for item in {"youtube.com", "youtu.be"}]):
            raise NotYoutubeURL(url)
        self.url = url
        self.title = self.default_title
        self.channel = self.default_channel
        self.duration = "0"
        self.p = None
    
    def __check_result(self):
        p, self.p = self.p, None
        err = bytes(p.readAllStandardError()).decode("utf8")
        if err:
            pass
        elif p.exitStatus() != QProcess.ExitStatus.NormalExit:
            err = f"Exit with error code {p.error()}."
        else:
            return bytes(p.readAllStandardOutput()).decode("utf8")
        raise CalledProcessFailed(p, err)
    
    def request_info(self):
        self.p = QProcess()
        self.p.finished.connect(self.process_info)
        self.p.start(str(args.youtube_dl), ["--dump-json", f"{self.url}"])
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    @pyqtSlot()
    def process_info(self):
        QGuiApplication.restoreOverrideCursor()
        try:
            js = json.loads(self.__check_result())
            if "title" in js:
                self.title = js["title"]
            if "channel" in js:
                self.channel = js["channel"]
            if "duration" in js:
                self.duration = to_hhmmss(js["duration"])
            self.info_loaded.emit()
        except CalledProcessFailed as e:
            self.error_occured.emit(f"{e}")
    
    def download_urls(self):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.p = QProcess()
        self.p.start(str(args.youtube_dl), ["-g", f"{self.url}"])
        if self.p.waitForFinished():
            QGuiApplication.restoreOverrideCursor()
            if result := self.__check_result():
                return result.split()
            else:
                p, self.p = self.p, None
                raise CalledProcessFailed(p)
        QGuiApplication.restoreOverrideCursor()
        p, self.p = self.p, None
        p.kill()
        raise TimeoutExpired(p)
    
    def download(self, filename, start, end):
        video, audio = self.download_urls()
        sp.run ([f"{args.ffmpeg}", "-loglevel", "quiet",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{video}",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{audio}",
                 "-c", "copy", f"{filename}"],
                 stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL, check=True)
