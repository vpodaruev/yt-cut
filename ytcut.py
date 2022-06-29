#!/usr/bin/env python3

import argparse

from pathlib import Path
from pathvalidate import sanitize_filename

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys

from gui import *
from utils import *
from ytlink import *
from timespan import *
import ytvideo


class AboutLabel(QLabel):
    def __init__(self):
        super().__init__("<font color=\"Grey\"><i>Created with<font color=\"Red\">&#10084;</font> by AllatRa IT team</i></font>")
        self.setTextFormat(Qt.TextFormat.RichText)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ytLink = YoutubeLink()
        self.ytLink.got_link.connect(self.got_yt_link)
        self.ytLink.edit_link.connect(self.edit_yt_link)
        
        self.timeSpan = TimeSpan()
        self.timeSpan.setEnabled(False)
        self.timeSpan.got_interval.connect(self.got_interval)
        self.timeSpan.edit_interval.connect(self.edit_interval)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ytLink)
        mainLayout.addWidget(self.timeSpan)
        mainLayout.addLayout(self.__save_as())
        mainLayout.addWidget(self.__download())
        mainLayout.addWidget(AboutLabel(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)
        
        self.set_step2_enabled(False)
        
#         add about button with CS sign... upload to GitHub to spread info about CS
#         change window icon to Serpinsky carpet in a circle
        
        self.setCentralWidget(widget)
        self.setWindowTitle("YtCut - Share the positive / Делись позитивом")
        self.setWindowIcon(QIcon("cs-logo.jpg"))
    
    def set_step2_enabled(self, ok):
        self.saveAsLineEdit.setEnabled(ok)
        self.saveAsPushButton.setEnabled(ok)
        self.downloadPushButton.setEnabled(ok)
        return
    
    def got_yt_link(self, video):
        self.ytVideo = video
        self.timeSpan.set_duration(video.duration)
        self.timeSpan.setEnabled(True)
    
    def edit_yt_link(self):
        self.timeSpan.init()
        self.timeSpan.setEnabled(False)
    
    def got_interval(self):
        file = sanitize_filename(self.ytVideo.title) + self.timeSpan.as_suffix() +".mp4"
        self.saveAsLineEdit.setPlaceholderText(file)
        self.saveAsLineEdit.setToolTip(file)
        self.set_step2_enabled(True)
    
    def edit_interval(self):
        pass
    
    def download(self):
        print(getLineEditValue(self.saveAsLineEdit))
    
    def __save_as(self):
        saveAsLabel = QLabel("Save as:")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("output file / файл, куда сохранить")
        self.saveAsLineEdit = saveAsLineEdit
        
        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(QIcon("saveAs.png"))
        saveAsPushButton.clicked.connect(self.get_filename)
        self.saveAsPushButton = saveAsPushButton
        
        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(saveAsPushButton)
        return layout
    
    def get_filename(self):
        dirname = getLineEditValue(self.saveAsLineEdit)
        if not dirname:
            dirname = "."
        file, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                   directory=dirname,
                                                   filter="Video Files (*.mp4)")
        if file:
            self.saveAsLineEdit.setText(file)
            self.saveAsLineEdit.setToolTip(file)
    
    def __download(self):
        pushButton = QPushButton("Download / Загрузить")
        pushButton.setIcon(QIcon("download.png"))
        pushButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pushButton.setEnabled(False)
        pushButton.clicked.connect(self.download)
        self.downloadPushButton = pushButton
        return pushButton


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
