#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt6.QtWidgets import (
     QWidget, QLabel, QLineEdit,
     QMessageBox, QHBoxLayout, QVBoxLayout)

import gui.common as com
import gui.ytvideo as ytv

import utils as ut


class YoutubeLink(QWidget):
    got_link = pyqtSignal(ytv.YoutubeVideo)
    edit_link = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QLabel("Link:")
        self.linkLineEdit = QLineEdit()
        self.linkLineEdit.setPlaceholderText("video link / ссылка на видео")

        self.goButton = com.GoButton()
        self.goButton.clicked.connect(self.link_edited)

        hLayout = QHBoxLayout()
        hLayout.addWidget(label)
        hLayout.addWidget(self.linkLineEdit)
        hLayout.addWidget(self.goButton)

        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.setTextInteractionFlags(
                          Qt.TextInteractionFlag.TextBrowserInteraction)
        self.titleLabel.setOpenExternalLinks(True)
        self.reset_title()

        self.video = None

        layout = QVBoxLayout()
        layout.addLayout(hLayout)
        layout.addWidget(self.titleLabel,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def reset_title(self, **kwargs):
        channel = kwargs.get("channel", ytv.default_channel)
        title = kwargs.get("title", ytv.default_title)
        self.titleLabel.setToolTip(title)
        if "thumbnail" in kwargs:
            title = f'<a href="{kwargs["thumbnail"]}">{title}</a>'
        self.titleLabel.setText("<b>" + channel + "</b>: " + title)

    @pyqtSlot()
    def link_edited(self):
        if not self.goButton.on:
            self.reset_title()
            self.goButton.toggle()
            self.linkLineEdit.selectAll()
            self.linkLineEdit.setEnabled(True)
            self.linkLineEdit.setFocus(Qt.FocusReason.OtherFocusReason)
            self.edit_link.emit()
            return

        url = self.linkLineEdit.text()
        if not url:
            return
        elif url.isspace():
            self.linkLineEdit.clear()
            return

        self.video = ytv.YoutubeVideo(url)
        self.video.info_loaded.connect(self.process_info)
        self.video.info_failed.connect(self.process_error)
        self.video.request_info()
        self.setEnabled(False)

    @pyqtSlot(str)
    def process_error(self, msg):
        QMessageBox.critical(self.parent(), "Error", msg)
        self.linkLineEdit.clear()
        self.setEnabled(True)

    @pyqtSlot()
    def process_info(self):
        self.setEnabled(True)
        self.linkLineEdit.setEnabled(False)
        self.goButton.toggle()
        v, self.video = self.video, None
        self.reset_title(channel=v.channel, title=v.title,
                         thumbnail=v.thumbnail)
        try:
            v.request_formats()
            self.got_link.emit(v)
        except ut.CalledProcessError as e:
            ut.logger().exception(f"{e}")
            self.process_error(f"{e}")

    def dump(self):
        return {
            "url": self.linkLineEdit.text() if self.linkLineEdit else None,
            "title": self.titleLabel.text() if self.titleLabel else None,
        }
