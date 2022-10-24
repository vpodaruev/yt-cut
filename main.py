#!/usr/bin/env python3

from argparse import ArgumentParser

from pathlib import Path
from pathvalidate import sanitize_filename

from PyQt6.QtCore import pyqtSlot, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
     QWidget, QLabel, QToolButton, QVBoxLayout, QHBoxLayout,
     QProgressBar, QSizePolicy, QMessageBox, QTabWidget,
     QMainWindow, QApplication)
import sys

import gui
import utils as ut
import options as opt
import saveas as svs
import timespan as tms
import version as vrs
import ytlink as ytl
import ytvideo as ytv


class AboutLabel(QLabel):
    def __init__(self):
        super().__init__("<font color=\"Grey\"><i>Created with"
                         "<font color=\"Red\">&#10084;"
                         "</font> by AllatRa IT team</i></font>")
        self.setTextFormat(Qt.TextFormat.RichText)


class AboutButton(QToolButton):
    _about_text = f"""<p><b><big>YtCut</big></b> - version {vrs.get_version()}

<p>This application is just a GUI wrapper for a small
part of the features of the console tools <b>yt-dlp</b> and <b>ffmpeg</b>.
<p>Это приложение - всего лишь графическая обёртка для небольшой
части возможностей консольных утилит <b>yt-dlp</b> и <b>ffmpeg</b>.

<p>Inspired by the <a href="https://creativesociety.com">Creative Society</a>
international project
"""

    def __init__(self, size):
        super().__init__()
        size = QSize(size, size)
        self.setIcon(QIcon("icons/cs-logo.png"))
        self.setFixedSize(size)
        self.setIconSize(0.95*size)
        self.setAutoRaise(True)
        self.clicked.connect(self.show_about)

    @pyqtSlot()
    def show_about(self):
        QMessageBox.information(self.parent(), "About", self._about_text)


class DownloadButton(gui.ToggleSwitch):
    def __init__(self):
        views = [(QIcon("icons/cancel.png"),   "Cancel / Отменить",    ""),
                 (QIcon("icons/download.png"), "Download / Загрузить", "")]
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
        self.setWindowIcon(QIcon("icons/ytcut.png"))

    @pyqtSlot(ytv.YoutubeVideo)
    def got_yt_link(self, video):
        self.ytVideo = video
        self.ytVideo.finished.connect(self.download_finished)
        self.ytVideo.progress.connect(self.update_progress)
        self.timeSpan.set_duration(video.duration, ut.get_url_time(video.url))
        self.timeSpan.set_quality(["1080p", "720p", "480p",
                                   "360p", "240p", "144p"])
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
        max_name_len = 128
        if len(name) > max_name_len:
            name = name[: max_name_len]
        file = name + ut.as_suffix(start, finish) + ".mp4"
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
            if Path(file).exists():
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
                self.ytVideo.start_download(file, s, f)
            except ytv.CalledProcessError as e:
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


if __name__ == "__main__":
    parser = ArgumentParser(description="Download parts of videos"
                            " from various social nets such as Youtube,"
                            " FaceBook, Instagram, TikTok, VK, etc.")
    parser.add_argument("--youtube-dl", type=Path,
                        default=Path("tools/yt-dlp"),
                        help="path to yt-dlp program [default: %(default)s]")
    parser.add_argument("--ffmpeg", type=Path, default=Path("tools/ffmpeg"),
                        help="path to ffmpeg program [default: %(default)s]")

    app = QApplication(sys.argv)
    args = parser.parse_args()

    # access to other modules
    ytv.args = args

    window = MainWindow()
    window.show()

    app.exec()
