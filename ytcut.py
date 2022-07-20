#!/usr/bin/env python3

import argparse

from pathlib import Path
from pathvalidate import sanitize_filename

from PyQt6.QtCore import pyqtSlot, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QWidget, QLabel, QToolButton, QVBoxLayout, QProgressBar,
                             QSizePolicy, QMessageBox, QMainWindow, QApplication)
import sys

from utils import *
from ytlink import *
from timespan import *
from saveas import *
from options import *
import ytvideo


__version__ = "1.0-rc1"


class AboutLabel(QLabel):
    def __init__(self):
        super().__init__("<font color=\"Grey\"><i>Created with<font color=\"Red\">&#10084;</font> by AllatRa IT team</i></font>")
        self.setTextFormat(Qt.TextFormat.RichText)


class AboutButton(QToolButton):
    _about_text = f"""<p><b><big>YtCut</big></b> - version {__version__}

<p>This application is just a GUI wrapper for a small part of the features of the console tools <b>yt-dlp</b> and <b>ffmpeg</b>.
<p>Это приложение - всего лишь графическая обёртка для небольшой части возможностей консольных утилит <b>yt-dlp</b> и <b>ffmpeg</b>.

<p>Inspired by the <a href="https://creativesociety.com">Creative Society</a> international project
"""
    def __init__(self, size):
        super().__init__()
        size = QSize(size, size)
        self.setIcon(QIcon("icons/cs-logo.png"))
        self.setFixedSize(size)
        self.setIconSize(0.95*size)
        self.setAutoRaise(True)
        self.clicked.connect(self.show_about)
    
    @pyqtSlot()
    def show_about(self):
        QMessageBox.information(self.parent(), "About", self._about_text)


class DownloadButton(ToggleSwitch):    
    def __init__(self):
        views = [(QIcon("icons/cancel.png"),   "Cancel / Отменить",    ""),
                 (QIcon("icons/download.png"), "Download / Загрузить", "")]
        super().__init__(views)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ytLink = YoutubeLink()
        self.ytLink.got_link.connect(self.got_yt_link)
        self.ytLink.edit_link.connect(self.edit_yt_link)
        
        self.timeSpan = TimeSpan()
        self.timeSpan.got_interval.connect(self.got_interval)
        self.timeSpan.edit_interval.connect(self.edit_interval)
        self.timeSpan.setEnabled(False)
        
        self.saveAs = SaveAsFile()
        self.saveAs.setEnabled(False)
        
        self.options = Options()
        self.options.setEnabled(False)
        
        self.downloadButton = DownloadButton()
        self.downloadButton.clicked.connect(self.download)
        self.downloadButton.setEnabled(False)
        self.saveAs.changed.connect(self.downloadButton.setEnabled)
        
        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.duration_in_sec = 1
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ytLink)
        mainLayout.addWidget(self.timeSpan)
        mainLayout.addWidget(self.saveAs)
        mainLayout.addWidget(self.options)
        mainLayout.addWidget(self.downloadButton)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(AboutLabel(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        layout = QHBoxLayout()
        layout.addWidget(AboutButton(300))
        layout.addLayout(mainLayout)
        widget = QWidget()
        widget.setLayout(layout)
        
#         change window icon to Serpinsky carpet in a circle
        
        self.setCentralWidget(widget)
        self.setMinimumWidth(700)
        self.setFixedHeight(self.sizeHint().height())
        self.setWindowTitle("YtCut - Share the positive / Делись позитивом")
        self.setWindowIcon(QIcon("icons/ytcut.png"))
    
    @pyqtSlot(YoutubeVideo)
    def got_yt_link(self, video):
        self.ytVideo = video
        self.ytVideo.finished.connect(self.download_finished)
        self.ytVideo.progress.connect(self.update_progress)
        self.timeSpan.set_duration(video.duration)
        self.timeSpan.setEnabled(True)
    
    @pyqtSlot()
    def edit_yt_link(self):
        self.ytVideo = None
        self.timeSpan.reset()
        self.timeSpan.setEnabled(False)
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
        self.options.setEnabled(False)
        self.options.detach()
        self.progressBar.setValue(0)
    
    @pyqtSlot(str, str)
    def got_interval(self, start, finish):
        name = sanitize_filename(self.ytVideo.title)
        max_name_len = 128
        if len(name) > max_name_len:
            name = name[ : max_name_len]
        file = name + as_suffix(start, finish) +".mp4"
        self.saveAs.set_filename(file)
        self.saveAs.setEnabled(True)
        self.options.setEnabled(True)
        self.options.attach(self.ytVideo)
    
    @pyqtSlot()
    def edit_interval(self):
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
        self.options.setEnabled(False)
        self.progressBar.setValue(0)
    
    @pyqtSlot()
    def download(self):
        if self.downloadButton.on:            
            file = self.saveAs.get_filename()
            if not file.endswith(".mp4"):
                file = file +".mp4"
            if Path(file).exists():
                if QMessageBox.question(self.parent(), "Question",
                                        f"'{file}'\n" \
                                        "File already exists. Overwrite it? / Файл уже существует. Перезаписать его?") \
                is QMessageBox.StandardButton.No:
                    return
            s, f = self.timeSpan.get_interval()
            self.ytLink.setEnabled(False)
            self.timeSpan.setEnabled(False)
            self.saveAs.setEnabled(False)
            self.options.setEnabled(False)
            self.downloadButton.toggle()
            self.duration_in_sec = to_seconds(f) - to_seconds(s)
            self.progressBar.reset()
            try:
                self.ytVideo.download(file, s, f)
            except CalledProcessError as e:
                QMessageBox.critical(self.parent(), "Error", f"{e}")
                self.ytVideo.cancel_download()
        else:
            self.ytVideo.cancel_download()
    
    @pyqtSlot(float)
    def update_progress(self, val):
        percent = int(val / self.duration_in_sec * 100)
        self.progressBar.setValue(percent)
    
    @pyqtSlot(bool)
    def download_finished(self, ok):
        if ok:
            self.progressBar.setValue(self.progressBar.maximum())
        self.downloadButton.toggle()
        self.ytLink.setEnabled(True)
        self.timeSpan.setEnabled(True)
        self.saveAs.setEnabled(True)
        self.options.setEnabled(True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download parts of videos from Youtube")
    parser.add_argument("--youtube-dl", type=Path, default=Path("yt-dlp"),
                        help="path to youtube-dl program [default: %(default)s]")
    parser.add_argument("--ffmpeg", type=Path, default=Path("ffmpeg"),
                        help="path to ffmpeg program [default: %(default)s]")

    app = QApplication(sys.argv)
    args = parser.parse_args()
    
    ytvideo.args = args

    window = MainWindow()
    window.show()

    app.exec()
