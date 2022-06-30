#!/usr/bin/env python3

import argparse

from pathlib import Path
from pathvalidate import sanitize_filename

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QMainWindow, QApplication
import sys

from utils import *
from ytlink import *
from timespan import *
from saveas import *
import ytvideo


class AboutLabel(QLabel):
    def __init__(self):
        super().__init__("<font color=\"Grey\"><i>Created with<font color=\"Red\">&#10084;</font> by AllatRa IT team</i></font>")
        self.setTextFormat(Qt.TextFormat.RichText)


class DownloadButton(QPushButton):
    def __init__(self):
        super().__init__("Download / Загрузить")
        self.setIcon(QIcon("download.png"))
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
        
        self.downloadButton = DownloadButton()
        self.downloadButton.clicked.connect(self.download)
        self.downloadButton.setEnabled(False)
        self.saveAs.changed.connect(self.downloadButton.setEnabled)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ytLink)
        mainLayout.addWidget(self.timeSpan)
        mainLayout.addWidget(self.saveAs)
        mainLayout.addWidget(self.downloadButton)
        mainLayout.addWidget(AboutLabel(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)
        
#         add about button with CS sign... upload to GitHub to spread info about CS
#         change window icon to Serpinsky carpet in a circle
        
        self.setCentralWidget(widget)
        self.setWindowTitle("YtCut - Share the positive / Делись позитивом")
        self.setWindowIcon(QIcon("cs-logo.jpg"))
    
    def got_yt_link(self, video):
        self.ytVideo = video
        self.timeSpan.set_duration(video.duration)
        self.timeSpan.setEnabled(True)
    
    def edit_yt_link(self):
        self.timeSpan.reset()
        self.timeSpan.setEnabled(False)
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
    
    def got_interval(self, start, finish):
        file = sanitize_filename(self.ytVideo.title) + as_suffix(start, finish) +".mp4"
        self.saveAs.set_filename(file)
        self.saveAs.setEnabled(True)
    
    def edit_interval(self):
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
    
    def download(self):
        file = self.saveAs.get_filename()
        if not file.endswith(".mp4"):
            file = file +".mp4"
        print(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from Youtube.")
    parser.add_argument("--youtube-dl", type=Path, default=Path("youtube-dl"),
                        help="path to youtube-dl program [default: %(default)s]")
    parser.add_argument("--ffmpeg", type=Path, default=Path("ffmpeg"),
                        help="path to ffmpeg program [default: %(default)s]")

    app = QApplication(sys.argv)
    args = parser.parse_args()
    
    ytvideo.args = args

    window = MainWindow()
    window.show()

    app.exec()