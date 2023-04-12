#!/usr/bin/env python3

from pathlib import Path
from pathvalidate import sanitize_filename

from PyQt6.QtCore import pyqtSlot, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
     QWidget, QLabel, QToolButton, QVBoxLayout, QHBoxLayout,
     QProgressBar, QSizePolicy, QMessageBox, QTabWidget,
     QMainWindow)

import gui.common as com
import gui.saveas as svs
import gui.timespan as tms
import gui.ytlink as ytl
import gui.ytvideo as ytv

import options as opt
import utils as ut
import version as vrs


class AboutLabel(QLabel):
    def __init__(self):
        super().__init__("<font color=\"Grey\"><i>Created with"
                         "<font color=\"Red\">&#10084;"
                         "</font> by AllatRa IT team</i></font>")
        self.setTextFormat(Qt.TextFormat.RichText)


yt_dlp_url = '<a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a>'
ffmpeg_url = '<a href="https://ffmpeg.org">ffmpeg</a>'


class AboutButton(QToolButton):
    _about_text = f"""<p><b><big>YtCut</big></b> - version {vrs.get_version()}

<p>A simple GUI application for downloading video fragments
from YouTube or other social networks. It simply wraps the
console tools {yt_dlp_url} and {ffmpeg_url} to provide a tiny
fraction of their immense capabilities to everyone.

<p>Простое приложение с графическим интерфейсом для загрузки
видеофрагментов с YouTube или других социальных сетей. Использует
консольные утилиты {yt_dlp_url} и {ffmpeg_url} и делает крошечную
часть их огромных возможностей доступной каждому.

<p>Inspired by the <a href="https://creativesociety.com">Creative Society</a>
international project
"""

    def __init__(self, size):
        super().__init__()
        size = QSize(size, size)
        self.setIcon(com.icon("icons/cs-logo.png"))
        self.setFixedSize(size)
        self.setIconSize(0.95*size)
        self.setAutoRaise(True)
        self.clicked.connect(self.show_about)

    @pyqtSlot()
    def show_about(self):
        QMessageBox.information(self.parent(), "About", self._about_text)


class DownloadButton(com.ToggleSwitch):
    def __init__(self):
        views = [(com.icon("icons/cancel.png"),   "Cancel / Отменить",    ""),
                 (com.icon("icons/download.png"), "Download / Загрузить", "")]
        super().__init__(views)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ytLink = ytl.YoutubeLink()
        self.ytLink.got_link.connect(self.got_yt_link)
        self.ytLink.edit_link.connect(self.edit_yt_link)

        self.timeSpan = tms.TimeSpan()
        self.timeSpan.got_interval.connect(self.got_interval)
        self.timeSpan.edit_interval.connect(self.edit_interval)
        self.timeSpan.setEnabled(False)

        self.saveAs = svs.SaveAsFile()
        self.saveAs.setEnabled(False)

        self.options = opt.Options()
        ytv.options = self.options    # access to other modules

        self.downloadButton = DownloadButton()
        self.downloadButton.clicked.connect(self.download)
        self.downloadButton.setEnabled(False)
        self.saveAs.changed.connect(self.downloadButton.setEnabled)

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.duration_in_sec = 1

        mainTabLayout = QVBoxLayout()
        mainTabLayout.addWidget(self.ytLink)
        mainTabLayout.addWidget(self.timeSpan)
        mainTabLayout.addWidget(self.saveAs)
        mainTabLayout.addWidget(self.downloadButton)
        mainTabLayout.addWidget(self.progressBar)
        mainTab = QWidget()
        mainTab.setLayout(mainTabLayout)

        tabs = QTabWidget()
        tabs.addTab(mainTab, "Main")
        tabs.addTab(self.options, "Options")
        tabs.setTabPosition(QTabWidget.TabPosition.East)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(AboutButton(240))
        mainLayout.addWidget(tabs)

        layout = QVBoxLayout()
        layout.addLayout(mainLayout)
        layout.addWidget(AboutLabel(),
                         alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.setMinimumWidth(700)
        self.setFixedHeight(self.sizeHint().height())
        self.setWindowTitle(f"YtCut {vrs.get_version()}"
                            " Share the positive / Делись позитивом")
        self.setWindowIcon(com.icon("icons/ytcut.png"))

    @pyqtSlot(ytv.YoutubeVideo)
    def got_yt_link(self, video):
        self.ytVideo = video
        self.ytVideo.finished.connect(self.download_finished)
        self.ytVideo.progress.connect(self.update_progress)
        self.timeSpan.set_format(video.get_formats())
        self.timeSpan.set_duration(video.duration, ut.get_url_time(video.url))
        self.timeSpan.setEnabled(True)

    @pyqtSlot()
    def edit_yt_link(self):
        self.ytVideo = None
        self.timeSpan.reset()
        self.timeSpan.setEnabled(False)
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
        self.progressBar.setValue(0)

    @pyqtSlot(str, str)
    def got_interval(self, start, finish):
        name = sanitize_filename(self.ytVideo.title)
        max_name_len = 64
        if len(name) > max_name_len:
            name = name[: max_name_len]
        format = self.timeSpan.get_format()
        file = name + self.ytVideo.get_suffix(start, finish, format) + ".mp4"
        self.saveAs.set_filename(file)
        self.saveAs.setEnabled(True)

    @pyqtSlot()
    def edit_interval(self):
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
        self.progressBar.setValue(0)

    @pyqtSlot()
    def download(self):
        if self.downloadButton.on:
            file = self.saveAs.get_filename()
            if not file.endswith(".mp4"):
                file = file + ".mp4"
            try:
                need_approve = Path(file).exists()
            except OSError as e:
                ut.logger().exception(f"{e}")
                QMessageBox.critical(self.parent(), "Error", f"{e}")
                return
            if need_approve:
                if QMessageBox.question(self.parent(), "Question",
                                        f"'{file}'\n"
                                        "File already exists. Overwrite it?"
                                        " / Файл уже существует."
                                        " Перезаписать его?") \
                  is QMessageBox.StandardButton.No:
                    return
            s, f = self.timeSpan.get_interval()
            self.ytLink.setEnabled(False)
            self.timeSpan.setEnabled(False)
            self.saveAs.setEnabled(False)
            self.downloadButton.toggle()
            self.duration_in_sec = ut.to_seconds(f) - ut.to_seconds(s)
            self.progressBar.reset()
            try:
                format = self.timeSpan.get_format()
                self.ytVideo.start_download(file, s, f, format)
            except ut.CalledProcessError as e:
                ut.logger().exception(f"{e}")
                QMessageBox.critical(self.parent(), "Error", f"{e}")
                self.ytVideo.cancel_download()
        else:
            self.ytVideo.cancel_download()

    @pyqtSlot(float)
    def update_progress(self, val):
        percent = int(val / self.duration_in_sec * 100)
        self.progressBar.setValue(percent)

    @pyqtSlot(bool, str)
    def download_finished(self, ok, errmsg):
        if ok:
            self.progressBar.setValue(self.progressBar.maximum())
        elif errmsg:
            QMessageBox.critical(self.parent(), "Error", errmsg)
        self.downloadButton.toggle()
        self.ytLink.setEnabled(True)
        self.timeSpan.setEnabled(True)
        self.saveAs.setEnabled(True)

    def dump(self):
        return {
            "ytLink": self.ytLink.dump() if self.ytLink else None,
            "timeSpan": self.timeSpan.dump() if self.timeSpan else None,
            "saveAs": self.saveAs.dump() if self.saveAs else None,
            "options": ytv.options.dump() if ytv.options else None,
        }
