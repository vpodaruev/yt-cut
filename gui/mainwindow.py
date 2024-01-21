#!/usr/bin/env python3

import pathlib as pl
from pathvalidate import sanitize_filename
import platform
import shutil

from PyQt6.QtCore import pyqtSlot, Qt, QSize, QUrl, QProcess
from PyQt6.QtGui import QDesktopServices
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
                         "</font> for people</i></font>")
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

<p><i>Inspired by the idea of a creative society</i>
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


class VideoButton(com.ToggleSwitch):
    def __init__(self):
        views = [(com.icon("icons/no_video.png"),
                  "", "Enable video / Включить видео"),
                 (com.icon("icons/video_on.png"),
                  "", "Disable video / Отключить видео")]
        super().__init__(views)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Fixed)


class AudioButton(com.ToggleSwitch):
    def __init__(self):
        views = [(com.icon("icons/no_audio.png"),
                  "", "Enable audio / Включить звук"),
                 (com.icon("icons/audio_on.png"),
                  "", "Disable audio / Отключить звук")]
        super().__init__(views)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Fixed)


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
        self.ytLink.edit_link.connect(self.reset)

        self.timeSpan = tms.TimeSpan()
        self.timeSpan.got_interval.connect(self.got_interval)
        self.timeSpan.edit_interval.connect(self.edit_interval)
        self.timeSpan.setEnabled(False)

        self.saveAs = svs.SaveAsFile()
        self.saveAs.setEnabled(False)

        self.options = opt.Options()
        ytv.options = self.options    # access to other modules

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.duration_in_sec = 1

        self.videoButton = VideoButton()
        self.videoButton.clicked.connect(self.toggle_video)
        self.videoButton.setEnabled(True)

        self.audioButton = AudioButton()
        self.audioButton.clicked.connect(self.toggle_audio)
        self.audioButton.setEnabled(True)

        self.downloadButton = DownloadButton()
        self.downloadButton.clicked.connect(self.download)
        self.downloadButton.setEnabled(False)
        self.saveAs.changed.connect(self.downloadButton.setEnabled)

        self.showInFolderPushButton = com.ShowInFolderButton()
        self.showInFolderPushButton.turn_on(False)
        self.showInFolderPushButton.clicked.connect(self.show_in_folder)
        self.showInFolderPushButton.setEnabled(False)
        self.saveAs.changed.connect(self.showInFolderPushButton.setEnabled)

        downloadHBoxLayout = QHBoxLayout()
        downloadHBoxLayout.addWidget(self.videoButton)
        downloadHBoxLayout.addWidget(self.audioButton)
        downloadHBoxLayout.addWidget(self.downloadButton)
        downloadHBoxLayout.addWidget(self.showInFolderPushButton)

        mainTabLayout = QVBoxLayout()
        mainTabLayout.addWidget(self.ytLink)
        mainTabLayout.addWidget(self.timeSpan)
        mainTabLayout.addWidget(self.saveAs)
        mainTabLayout.addWidget(self.progressBar)
        mainTabLayout.addLayout(downloadHBoxLayout)
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

    @pyqtSlot()
    def reset(self):
        self.progressBar.setValue(0)
        self.downloadButton.turn_on(True)
        self.showInFolderPushButton.turn_on(False)
        self.saveAs.reset()
        self.saveAs.setEnabled(False)
        self.timeSpan.reset()
        self.timeSpan.setEnabled(False)
        self.ytLink.reset()
        self.ytLink.setEnabled(True)
        self.ytVideo = None

    @pyqtSlot(ytv.YtVideo)
    def got_yt_link(self, video):
        self.ytVideo = video
        self.ytVideo.finished.connect(self.download_finished)
        self.ytVideo.progress.connect(self.update_progress)
        self.timeSpan.set_format(video.get_all_formats())
        self.timeSpan.set_duration(video.duration, ut.get_url_time(video.url))
        self.timeSpan.setEnabled(True)

    @pyqtSlot(str, str)
    def got_interval(self, start, finish):
        name = sanitize_filename(self.ytVideo.title)
        max_name_len = 64
        if len(name) > max_name_len:
            name = name[: max_name_len]
        format = self.timeSpan.get_format()
        file = "".join([name,
                        self.ytVideo.get_affix(start, finish, format),
                        self.ytVideo.get_suffix()])
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
            try:
                need_approve = pl.Path(file).exists()
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
            self.ytLink.lock()
            self.timeSpan.lock()
            self.saveAs.lock()
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

    @pyqtSlot(float, str)
    def update_progress(self, val, unit):
        percent = 0
        if unit == "%":
            percent = int(val)
        elif unit == "s":
            percent = int(val / self.duration_in_sec * 100)
        else:
            ut.logger().warning(f"unknown progress unit ({unit})")
        self.progressBar.setValue(percent)

    @pyqtSlot(bool, str)
    def download_finished(self, ok, errmsg):
        if ok:
            self.progressBar.setValue(self.progressBar.maximum())
        elif errmsg:
            QMessageBox.critical(self.parent(), "Error", errmsg)
        self.downloadButton.toggle()
        self.ytLink.unlock()
        self.timeSpan.unlock()
        self.saveAs.unlock()
        if self.showInFolderPushButton.on:
            self.showInFolderPushButton.toggle()
            if ok:
                self.show_in_folder()

    @pyqtSlot()
    def toggle_video(self):
        self.videoButton.toggle()
        if not (self.videoButton.on or self.audioButton.on):
            self.audioButton.toggle()
        self._reset_content()

    @pyqtSlot()
    def toggle_audio(self):
        self.audioButton.toggle()
        if not (self.videoButton.on or self.audioButton.on):
            self.videoButton.toggle()
        self._reset_content()

    @pyqtSlot()
    def show_in_folder(self):
        if not self.downloadButton.on:
            self.showInFolderPushButton.toggle()
            return  # in progress, to be invoked later with download_finished()

        self.showInFolderPushButton.turn_on(False)
        file = pl.Path(self.saveAs.get_filename())
        if platform.system() == "Windows" and file.exists():
            ex = shutil.which("explorer.exe")
            if ex is not None:
                file = pl.WindowsPath(file).resolve()
                QProcess.startDetached(f"{ex}", ["/select,", f"{file}"])
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(f"{file.parent.resolve()}"))

    def dump(self):
        return {
            "ytLink": self.ytLink.dump() if self.ytLink else None,
            "timeSpan": self.timeSpan.dump() if self.timeSpan else None,
            "saveAs": self.saveAs.dump() if self.saveAs else None,
            "options": ytv.options.dump() if ytv.options else None,
        }

    def _reset_content(self):
        self.ytVideo.set_content(dict(
            video=self.videoButton.on,
            audio=self.audioButton.on,
        ))
        self.saveAs.set_suffix(self.ytVideo.get_suffix())
