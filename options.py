#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
     QWidget, QLabel, QComboBox, QCheckBox,
     QPushButton, QGroupBox, QVBoxLayout, QGridLayout)


browsers = ("", "brave", "chrome", "chromium", "edge",
            "firefox", "opera", "safari", "vivaldi")

video_codecs = {
    "copy": "Copy from source",
    "h264": "H.264 / AVC / MPEG-4 AVC"
            " / MPEG-4 part 10 (Intel Quick Sync Video acceleration)",
    "h264_nvenc": "H.264 with NVIDIA hardware acceleration",
    "mpeg4": "MPEG-4 part 2"
}
audio_codecs = {
    "copy": "Copy from source",
    "aac": "AAC (Advanced Audio Coding)",
    "mp3": "libmp3lame MP3 (MPEG audio layer 3)",
}


class ToolOptions:
    def __init__(self):
        self.reset()

    def reset(self):
        self.browser = browsers[0]
        self.use_premiere = False
        self.codecs = {"video": "copy",
                       "audio": "copy"}
        self.keep_vbr = False
        self.debug = {"logging": False}

    def dump(self):
        return {
            "browser": self.browser,
            "use_premiere": self.use_premiere,
            "codecs": self.codecs,
            "keep_vbr": self.keep_vbr,
            "debug": self.debug,
        }


class Options(QWidget, ToolOptions):
    def __init__(self):
        super().__init__()

        authGroup = QGroupBox("Auth via")
        browserLabel = QLabel("Browser:")
        browserLabel.setToolTip("Authorize via browser cookies"
                                " / Авторизоваться через браузер")
        self.browserComboBox = QComboBox()
        self.browserComboBox.setEditable(False)
        for browser in browsers:
            self.browserComboBox.addItem(browser)
        self.browserComboBox.currentTextChanged.connect(self.set_browser)

        authLayout = QGridLayout()
        authLayout.addWidget(browserLabel, 0, 0)
        authLayout.addWidget(self.browserComboBox, 0, 1)
        authLayout.setRowStretch(1, 1)
        authGroup.setLayout(authLayout)

        codecGroup = QGroupBox("Codecs")
        self.premiereCheckBox = QCheckBox("Premiere Pro")
        self.premiereCheckBox.setToolTip("Use codecs for Premiere Pro"
                                         " / Кодеки для монтажа в Премьере")
        self.premiereCheckBox.toggled.connect(self.toggle_premiere)

        vcodecLabel = QLabel("Video:")
        vcodecLabel.setToolTip("Convert video via FFMPEG"
                               " / Конвертировать видео")
        self.vcodecComboBox = QComboBox()
        self.vcodecComboBox.setEditable(False)
        for codec in video_codecs:
            self.vcodecComboBox.addItem(codec)
        self.vcodecComboBox.currentTextChanged.connect(self.set_video_codec)

        acodecLabel = QLabel("Audio:")
        acodecLabel.setToolTip("Convert audio via FFMPEG"
                               " / Конвертировать аудио")
        self.acodecComboBox = QComboBox()
        self.acodecComboBox.setEditable(False)
        for codec in audio_codecs:
            self.acodecComboBox.addItem(codec)
        self.acodecComboBox.currentTextChanged.connect(self.set_audio_codec)

        self.vbrCheckBox = QCheckBox("Keep original VBR")
        self.vbrCheckBox.setToolTip(
            "Preserve original video bitrate when converting"
            " / Сохранить исходный битрейт видео при конвертировании")
        self.vbrCheckBox.toggled.connect(self.toggle_keep_vbr)

        codecLayout = QGridLayout()
        codecLayout.addWidget(self.premiereCheckBox, 0, 0, 1, 2)
        codecLayout.addWidget(vcodecLabel, 1, 0)
        codecLayout.addWidget(self.vcodecComboBox, 1, 1)
        codecLayout.addWidget(acodecLabel, 2, 0)
        codecLayout.addWidget(self.acodecComboBox, 2, 1)
        codecLayout.addWidget(self.vbrCheckBox, 3, 0, 1, 2)
        codecGroup.setLayout(codecLayout)

        debugGroup = QGroupBox("Debug")
        self.logCheckBox = QCheckBox("Logging")
        self.logCheckBox.setToolTip("Write FFMPEG report")
        self.logCheckBox.toggled.connect(self.toggle_logging)

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
        self.premiereCheckBox.setChecked(self.use_premiere)
        self.vcodecComboBox.setCurrentText(self.codecs["video"])
        self.acodecComboBox.setCurrentText(self.codecs["audio"])
        self.vbrCheckBox.setChecked(self.keep_vbr)
        self.logCheckBox.setChecked(self.debug["logging"])

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

    @pyqtSlot(bool)
    def toggle_logging(self, ok):
        self.debug["logging"] = ok
