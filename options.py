#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSlot, Qt, QSize
from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QCheckBox, QHBoxLayout

from ytvideo import *


class Options(QWidget):
    def __init__(self):
        super().__init__()
        
        self.video = None
        
        self.vcodec = QComboBox()
        self.vcodec.setEditable(False)
        for codec in YoutubeVideo.video_codecs:
            self.vcodec.addItem(codec)
        self.vcodec.currentTextChanged.connect(self.set_video_codec)
        
        self.acodec = QComboBox()
        self.acodec.setEditable(False)
        for codec in YoutubeVideo.audio_codecs:
            self.acodec.addItem(codec)
        self.acodec.currentTextChanged.connect(self.set_audio_codec)
        
        self.log = QCheckBox("logging")
        self.log.setToolTip("Write FFMPEG report (debug purpose)")
        self.log.stateChanged.connect(self.set_logging)
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Video codec:"))
        layout.addWidget(self.vcodec)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Audio codec:"))
        layout.addWidget(self.acodec)
        layout.addStretch()
        layout.addWidget(self.log)
        self.setLayout(layout)
    
    def attach(self, video):
        self.video = video
    
    def detach(self):
        self.video = None
    
    @pyqtSlot(str)
    def set_video_codec(self, name):
        if self.video:
            self.video.codecs["video"] = name
    
    @pyqtSlot(str)
    def set_audio_codec(self, name):
        if self.video:
            self.video.codecs["audio"] = name
    
    @pyqtSlot(int)
    def set_logging(self, state):
        if self.video:
            self.video.debug = bool(state)
