#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import (
     QWidget, QLabel, QComboBox, QCheckBox,
     QPushButton, QGroupBox, QVBoxLayout, QGridLayout)

import gui.ytvideo as ytv


class ToolOptions:
    def __init__(self):
        self.reset()

    def reset(self):
        self.browser = ""
        self.use_premiere = False
        self.codecs = {"video": "copy",
                       "audio": "copy"}
        self.debug = {"logging": False}
        self.keep_vbr = False


class Options(QWidget, ToolOptions):
    def __init__(self):
        super().__init__()

        authGroup = QGroupBox("Auth via")
        browserLabel = QLabel("Browser:")
        browserLabel.setToolTip("Authorize via browser cookies"
                                " / Авторизоваться через браузер")
        self.browserComboBox = QComboBox()
        self.browserComboBox.setEditable(False)
        for browser in [""] + ytv.YoutubeVideo.browsers:
            self.browserComboBox.addItem(browser)
        self.browserComboBox.currentTextChanged.connect(self.set_browser)

        authLayout = QGridLayout()
        authLayout.addWidget(browserLabel, 0, 0)
        authLayout.addWidget(self.browserComboBox, 0, 1)
        authLayout.setRowStretch(1, 1)
        authGroup.setLayout(authLayout)

        codecGroup = QGroupBox("Codecs")
        self.premiere = QCheckBox("Premiere Pro")
        self.premiere.setToolTip("Use codecs for Premiere Pro"
                                 " / Кодеки для монтажа в Премьере")
        self.premiere.toggled.connect(self.toggle_premiere)

        vcodecLabel = QLabel("Video:")
        vcodecLabel.setToolTip("Convert video via FFMPEG"
                               " / Конвертировать видео")
        self.vcodecComboBox = QComboBox()
        self.vcodecComboBox.setEditable(False)
        for codec in ytv.YoutubeVideo.video_codecs:
            self.vcodecComboBox.addItem(codec)
        self.vcodecComboBox.currentTextChanged.connect(self.set_video_codec)

        acodecLabel = QLabel("Audio:")
        acodecLabel.setToolTip("Convert audio via FFMPEG"
                               " / Конвертировать аудио")
        self.acodecComboBox = QComboBox()
        self.acodecComboBox.setEditable(False)
        for codec in ytv.YoutubeVideo.audio_codecs:
            self.acodecComboBox.addItem(codec)
        self.acodecComboBox.currentTextChanged.connect(self.set_audio_codec)

        self.vbr = QCheckBox("Keep original VBR")
        self.vbr.setToolTip("Preserve original video bitrate when converting"
                            " / Сохранить исходный битрейт видео при конвертировании")
        self.vbr.toggled.connect(self.toggle_keep_vbr)

        codecLayout = QGridLayout()
        codecLayout.addWidget(self.premiere, 0, 0, 1, 2)
        codecLayout.addWidget(vcodecLabel, 1, 0)
        codecLayout.addWidget(self.vcodecComboBox, 1, 1)
        codecLayout.addWidget(acodecLabel, 2, 0)
        codecLayout.addWidget(self.acodecComboBox, 2, 1)
        codecLayout.addWidget(self.vbr, 3, 0, 1, 2)
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

    @pyqtSlot(str)
    def set_browser(self, name):
        self.browser = name

    @pyqtSlot(bool)
    def toggle_premiere(self, ok):
        self.use_premiere = ok

    @pyqtSlot(str)
    def set_video_codec(self, name):
        self.codecs["video"] = name

    @pyqtSlot(str)
    def set_audio_codec(self, name):
        self.codecs["audio"] = name

    @pyqtSlot(bool)
    def toggle_keep_vbr(self, ok):
        self.keep_vbr = ok

    @pyqtSlot(int)
    def set_logging(self, state):
        self.debug["logging"] = bool(state)
