#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import (
     QWidget, QLabel, QComboBox, QCheckBox,
     QPushButton, QGroupBox, QVBoxLayout, QGridLayout)

import ytvideo as ytv


class ToolOptions:
    def __init__(self):
        self.reset()

    def reset(self):
        self.browser = ""
        self.codecs = {"video": "copy",
                       "audio": "copy"}
        self.debug = {"logging": False}


class Options(QWidget, ToolOptions):
    def __init__(self):
        super().__init__()

        authGroup = QGroupBox("Auth via")
        self.browserComboBox = QComboBox()
        self.browserComboBox.setEditable(False)
        for browser in [""] + ytv.YoutubeVideo.browsers:
            self.browserComboBox.addItem(browser)
        self.browserComboBox.currentTextChanged.connect(self.set_browser)

        authLayout = QGridLayout()
        authLayout.addWidget(QLabel("Browser:"), 0, 0)
        authLayout.addWidget(self.browserComboBox, 0, 1)
        authLayout.setRowStretch(1, 1)
        authGroup.setLayout(authLayout)

        codecGroup = QGroupBox("Codecs")
        self.vcodecComboBox = QComboBox()
        self.vcodecComboBox.setEditable(False)
        for codec in ytv.YoutubeVideo.video_codecs:
            self.vcodecComboBox.addItem(codec)
        self.vcodecComboBox.currentTextChanged.connect(self.set_video_codec)

        self.acodecComboBox = QComboBox()
        self.acodecComboBox.setEditable(False)
        for codec in ytv.YoutubeVideo.audio_codecs:
            self.acodecComboBox.addItem(codec)
        self.acodecComboBox.currentTextChanged.connect(self.set_audio_codec)

        codecLayout = QGridLayout()
        codecLayout.addWidget(QLabel("Video:"), 0, 0)
        codecLayout.addWidget(self.vcodecComboBox, 0, 1)
        codecLayout.addWidget(QLabel("Audio:"), 1, 0)
        codecLayout.addWidget(self.acodecComboBox, 1, 1)
        codecGroup.setLayout(codecLayout)

        debugGroup = QGroupBox("Debug")
        self.logCheckBox = QCheckBox("Logging")
        self.logCheckBox.setToolTip("Write FFMPEG report")
        self.logCheckBox.stateChanged.connect(self.set_logging)

        debugLayout = QVBoxLayout()
        debugLayout.addWidget(self.logCheckBox)
        debugLayout.addStretch()
        debugGroup.setLayout(debugLayout)

        self.resetPushButton = QPushButton("Reset")
        self.resetPushButton.clicked.connect(self.set_defaults)

        layout = QGridLayout()
        layout.addWidget(authGroup, 0, 0)
        layout.addWidget(codecGroup, 0, 1)
        layout.setColumnStretch(2, 1)
        layout.addWidget(debugGroup, 0, 3)
        layout.setRowStretch(1, 1)
        layout.addWidget(self.resetPushButton, 2, 3)
        self.setLayout(layout)

        self.set_defaults()

    def set_defaults(self):
        super().reset()
        self.browserComboBox.setCurrentText(self.browser)
        self.vcodecComboBox.setCurrentText(self.codecs["video"])
        self.acodecComboBox.setCurrentText(self.codecs["audio"])
        self.logCheckBox.setCheckState(Qt.CheckState.Checked
                                       if self.debug["logging"]
                                       else Qt.CheckState.Unchecked)

    def get_browser(self):
        return self.browser

    @pyqtSlot(str)
    def set_browser(self, name):
        self.browser = name

    def get_codecs(self):
        return self.codecs

    @pyqtSlot(str)
    def set_video_codec(self, name):
        self.codecs["video"] = name

    @pyqtSlot(str)
    def set_audio_codec(self, name):
        self.codecs["audio"] = name

    def need_debug(self):
        return any(self.debug.values())

    def get_logging(self):
        return self.debug["logging"]

    @pyqtSlot(int)
    def set_logging(self, state):
        self.debug["logging"] = bool(state)
