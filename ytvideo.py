#!/usr/bin/env python3

import json
import subprocess as sp
from urllib.parse import urlparse

from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QProcess

from utils import *


global args  # set in main module

class NotYoutubeURL(RuntimeError):
    def __init__(self, url):
        super().__init__(f"'{url}' is not a youtube URL")


class YoutubeVideo(QObject):
    info_loaded = pyqtSignal()
    error_occured = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        netloc = urlparse(url).netloc
        if all([item not in netloc for item in {"youtube.com", "youtu.be"}]):
            raise NotYoutubeURL(url)
        self.url = url
        self.title = "Video Title"
        self.channel = "Youtube Channel"
        self.duration = "0"
        self.p = None
    
    def request_info(self):
        self.p = QProcess()
        self.p.finished.connect(self.process_info)
        self.p.start(str(args.youtube_dl), ["--dump-json", f"{self.url}"])
    
    @pyqtSlot()
    def process_info(self):
        errout = bytes(self.p.readAllStandardError()).decode("utf8")
        if errout:
            self.error_occured.emit(errout)
            return
        if self.p.exitStatus() != QProcess.ExitStatus.NormalExit:
            self.error_occured.emit(f"Exit with error code {self.p.error()}.")
            return
        result = bytes(self.p.readAllStandardOutput()).decode("utf8")
        js = json.loads(result)
        if "title" in js:
            self.title = js["title"]
        if "channel" in js:
            self.channel = js["channel"]
        if "duration" in js:
            self.duration = to_hhmmss(js["duration"])
        self.p = None
        self.info_loaded.emit()
    
    def download_urls(self):
        p = sp.run([f"{args.youtube_dl}", "-g", f"{self.url}"],
                    capture_output=True, encoding="utf-8", check=True)
        return p.stdout.split()
    
    def download(self, filename, start, end):
        video, audio = self.download_urls()
        sp.run ([f"{args.ffmpeg}", "-loglevel", "quiet",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{video}",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{audio}",
                 "-c", "copy", f"{filename}"],
                 stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL, check=True)
