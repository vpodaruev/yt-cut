#!/usr/bin/env python3

import logging

from PyQt6.QtCore import (pyqtSlot, Qt, QProcess)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
     QWidget, QLabel, QComboBox, QMessageBox, QCheckBox,
     QPushButton, QGroupBox, QGridLayout, QVBoxLayout)

import utils as ut


browsers = ("", "brave", "chrome", "chromium", "edge",
            "firefox", "opera", "safari", "vivaldi")

video_codecs = {
    "copy": "Use codec from source without conversion / Без конвертации",
    "h264": "H.264 / AVC / MPEG-4 AVC"
            " / MPEG-4 part 10 (Intel Quick Sync Video acceleration)",
    "h264_nvenc": "H.264 with NVIDIA hardware acceleration",
    "mpeg4": "MPEG-4 part 2"
}
audio_codecs = {
    "copy": "Use codec from source without conversion / Без конвертации",
    "aac": "AAC (Advanced Audio Coding)",
    "mp3": "MPEG audio layer 3",
}

log_level = {
    "disable": None,
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


class ToolOptions:
    def __init__(self):
        self.reset()

    def reset(self):
        self.browser = browsers[0]
        self.prefer_avc = True
        self.codecs = {"video": "copy",
                       "audio": "copy"}
        self.keep_vbr = False
        self.debug = {"ffmpeg": False,
                      "logLevel": "critical"}
        self.xerror = True

    def dump(self):
        return {
            "browser": self.browser,
            "prefer_avc": self.prefer_avc,
            "codecs": self.codecs,
            "keep_vbr": self.keep_vbr,
            "debug": self.debug,
            "xerror": self.xerror,
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
        self.premiereCheckBox = QCheckBox("Prefer AVC/AAC")
        self.premiereCheckBox.setToolTip(
                "Prefer Advanced Video/Audio Coding, most widely"
                " used compression standards /\n"
                "Предпочитать наиболее широко используемые стандарты"
                " сжатия для видео и аудио")
        self.premiereCheckBox.toggled.connect(self.toggle_premiere)

        vcodecLabel = QLabel("Video:")
        vcodecLabel.setToolTip("Convert video via FFMPEG"
                               " / Конвертировать видео")
        self.vcodecComboBox = QComboBox()
        self.vcodecComboBox.setEditable(False)
        for codec in video_codecs:
            self.vcodecComboBox.addItem(codec)
        self.vcodecComboBox.setToolTip(video_codecs[self.codecs["video"]])
        self.vcodecComboBox.currentTextChanged.connect(self.set_video_codec)

        acodecLabel = QLabel("Audio:")
        acodecLabel.setToolTip("Convert audio via FFMPEG"
                               " / Конвертировать аудио")
        self.acodecComboBox = QComboBox()
        self.acodecComboBox.setEditable(False)
        for codec in audio_codecs:
            self.acodecComboBox.addItem(codec)
        self.acodecComboBox.setToolTip(audio_codecs[self.codecs["audio"]])
        self.acodecComboBox.currentTextChanged.connect(self.set_audio_codec)

        self.vbrCheckBox = QCheckBox("Keep original VBR")
        self.vbrCheckBox.setToolTip(
            "Preserve original video bitrate when converting /\n"
            "Сохранить исходное качество видео при конвертировании")
        self.vbrCheckBox.toggled.connect(self.toggle_keep_vbr)
        self.vbrCheckBox.setEnabled(False)

        codecLayout = QGridLayout()
        codecLayout.addWidget(self.premiereCheckBox, 0, 0, 1, 2)
        codecLayout.addWidget(vcodecLabel, 1, 0)
        codecLayout.addWidget(self.vcodecComboBox, 1, 1)
        codecLayout.addWidget(acodecLabel, 2, 0)
        codecLayout.addWidget(self.acodecComboBox, 2, 1)
        codecLayout.addWidget(self.vbrCheckBox, 3, 0, 1, 2)
        codecGroup.setLayout(codecLayout)

        debugGroup = QGroupBox("Debug")
        self.logCheckBox = QCheckBox("FFMPEG log")
        self.logCheckBox.setToolTip("Write FFMPEG report")
        self.logCheckBox.toggled.connect(self.toggle_logging)

        logLevelLabel = QLabel("Logging:")
        logLevelLabel.setToolTip("Logging level / Уровень журналирования")
        self.logLevelComboBox = QComboBox()
        self.logLevelComboBox.setEditable(False)
        for level in log_level.keys():
            self.logLevelComboBox.addItem(level)
        self.logLevelComboBox.setCurrentText(self.debug["logLevel"])
        self.logLevelComboBox.currentTextChanged.connect(self.set_log_level)

        debugLayout = QGridLayout()
        debugLayout.addWidget(self.logCheckBox, 0, 0, 1, 2)
        debugLayout.addWidget(logLevelLabel, 1, 0)
        debugLayout.addWidget(self.logLevelComboBox, 1, 1)
        debugGroup.setLayout(debugLayout)

        thirdPartyGroup = QGroupBox("Third party")
        self.updateYtDlpPushButton = QPushButton("Update")
        self.updateYtDlpPushButton.setToolTip("Update Yt-dlp tool /"
                                              " Обновить программу Yt-dlp")
        self.updateYtDlpPushButton.clicked.connect(self.update_third_party)

        thirdPartyLayout = QVBoxLayout()
        thirdPartyLayout.addWidget(self.updateYtDlpPushButton)
        thirdPartyGroup.setLayout(thirdPartyLayout)

        self.xerrorCheckBox = QCheckBox("Stop on error")
        self.xerrorCheckBox.setToolTip("Stop download on error /"
                                       " Остановить загрузку при ошибке")
        self.xerrorCheckBox.toggled.connect(self.toggle_xerror)

        self.resetPushButton = QPushButton("Reset")
        self.resetPushButton.setToolTip("Reset settings / Сбросить настройки")
        self.resetPushButton.clicked.connect(self.set_defaults)

        layout = QGridLayout()
        layout.addWidget(authGroup, 0, 0)
        layout.addWidget(codecGroup, 0, 1, 2, 1)
        layout.setColumnStretch(2, 1)
        layout.addWidget(debugGroup, 1, 0)
        layout.setRowStretch(2, 1)
        layout.addWidget(thirdPartyGroup, 0, 3)
        layout.addWidget(self.xerrorCheckBox, 3, 0)
        layout.addWidget(self.resetPushButton, 3, 3)
        self.setLayout(layout)

        self.set_defaults()

    def set_defaults(self):
        super().reset()
        self.browserComboBox.setCurrentText(self.browser)
        self.premiereCheckBox.setChecked(self.prefer_avc)
        self.vcodecComboBox.setCurrentText(self.codecs["video"])
        self.acodecComboBox.setCurrentText(self.codecs["audio"])
        self.vbrCheckBox.setChecked(self.keep_vbr)
        self.logCheckBox.setChecked(self.debug["ffmpeg"])
        self.logLevelComboBox.setCurrentText(self.debug["logLevel"])
        self.xerrorCheckBox.setChecked(self.xerror)

    @pyqtSlot(str)
    def set_browser(self, name):
        self.browser = name

    @pyqtSlot(bool)
    def toggle_premiere(self, ok):
        self.prefer_avc = ok

    @pyqtSlot(str)
    def set_video_codec(self, name):
        if name != "copy":
            self.vbrCheckBox.setEnabled(True)
            self.vbrCheckBox.setCheckState(Qt.CheckState.Checked)
        else:
            self.vbrCheckBox.setCheckState(Qt.CheckState.Unchecked)
            self.vbrCheckBox.setEnabled(False)
        self.codecs["video"] = name
        self.vcodecComboBox.setToolTip(video_codecs[name])

    @pyqtSlot(str)
    def set_audio_codec(self, name):
        self.codecs["audio"] = name
        self.acodecComboBox.setToolTip(audio_codecs[name])

    @pyqtSlot(bool)
    def toggle_keep_vbr(self, ok):
        self.keep_vbr = ok

    @pyqtSlot(bool)
    def toggle_logging(self, ok):
        self.debug["ffmpeg"] = ok

    @pyqtSlot(str)
    def set_log_level(self, name):
        self.debug["logLevel"] = name
        if log_level[name] is not None:
            logging.disable(logging.NOTSET)
            ut.logger().setLevel(log_level[name])
        else:
            logging.disable(logging.CRITICAL)

    @pyqtSlot(bool)
    def toggle_xerror(self, ok):
        self.xerror = ok

    def update_third_party(self):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        p = QProcess()
        p.start(f"{ut.yt_dlp()}", ["-U"])
        try:
            if p.waitForFinished():
                QGuiApplication.restoreOverrideCursor()
                if status := ut.check_output(p):
                    QMessageBox.information(self.parent(),
                                            "Yt-dlp Update Status",
                                            f"{status}")
                    ut.logger().info(f"{status}")
                    return
                else:
                    raise ut.CalledProcessFailed(p)
            QGuiApplication.restoreOverrideCursor()
            raise ut.TimeoutExpired(p)
        except ut.CalledProcessError as e:
            QMessageBox.critical(self.parent(), "Yt-dlp Update Error", f"{e}")
