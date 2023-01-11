#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt6.QtWidgets import (
     QWidget, QLabel, QLineEdit,
     QMessageBox, QHBoxLayout, QVBoxLayout)

import gui
import ytvideo as ytv


class YoutubeLink(QWidget):
    got_link = pyqtSignal(ytv.YoutubeVideo)
    edit_link = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QLabel("Link:")
        self.linkLineEdit = QLineEdit()
        self.linkLineEdit.setPlaceholderText("video link / ссылка на видео")

        self.goButton = gui.GoButton()
        self.goButton.clicked.connect(self.link_edited)

        hLayout = QHBoxLayout()
        hLayout.addWidget(label)
        hLayout.addWidget(self.linkLineEdit)
        hLayout.addWidget(self.goButton)

        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.setTextInteractionFlags(
                          Qt.TextInteractionFlag.TextSelectableByMouse)
        self.reset_title()

        self.video = None

        layout = QVBoxLayout()
        layout.addLayout(hLayout)
        layout.addWidget(self.titleLabel,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def reset_title(self, **kwargs):
        channel = kwargs["channel"] if "channel" in kwargs \
            else ytv.default_channel
        title = kwargs["title"] if "title" in kwargs \
            else ytv.default_title
        self.titleLabel.setText("<b>" + channel + "</b>: " +
                                title if channel else title)
        self.titleLabel.setToolTip(title)

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

        try:
            self.video = ytv.YoutubeVideo(url)
            self.video.info_loaded.connect(self.process_info)
            self.video.info_failed.connect(self.process_error)
            self.video.request_info()
            self.setEnabled(False)
        except ytv.NotYoutubeURL:
            QMessageBox.warning(self.parent(), "Warning",
                                "It doesn't seem to be a YouTube link"
                                f" / Похоже, это не ютуб-ссылка\nURL: '{url}'")
            self.linkLineEdit.clear()
            self.setEnabled(True)

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
        self.reset_title(channel=v.channel, title=v.title)
        try:
            v.request_formats()
            self.got_link.emit(v)
        except ytv.CalledProcessError as e:
            self.process_error(f"{e}")
