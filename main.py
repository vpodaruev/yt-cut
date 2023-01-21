#!/usr/bin/env python3

from argparse import ArgumentParser

from pathlib import Path
import sys
import traceback

from PyQt6.QtCore import (QObject, pyqtSignal)
from PyQt6.QtWidgets import (QApplication, QMessageBox)

import gui.mainwindow as mw
import gui.ytvideo as ytv


def show_exception_box(log_msg):
    """Checks if a QApplication instance is available and shows a messagebox with the exception message.
    If unavailable (non-console application), log an additional notice.
    """
    errorbox = QMessageBox(window)
    errorbox.setText("Oops. An unexpected error occured:\n{0}".format(log_msg))
    errorbox.exec()


def restore_on_error():
    window.edit_yt_link()
    window.ytLink.setEnabled(True)


class UncaughtHook(QObject):
    _exception_caught = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super(UncaughtHook, self).__init__(*args, **kwargs)

        # register as hook with the Python interpreter
        sys.excepthook = self.exception_hook

        # connect signal to execute the message box function always on main thread
        self._exception_caught.connect(show_exception_box)

    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # ignore keyboard interrupt to support console applications
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            log_msg = '\n'.join([''.join(traceback.format_tb(exc_traceback)),
                                 '{0}: {1}'.format(exc_type.__name__, exc_value)])

            # trigger message box show
            self._exception_caught.emit(log_msg)

            restore_on_error()


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

    # to register the hook
    qt_exception_hook = UncaughtHook()

    # access to other modules
    ytv.args = args

    window = mw.MainWindow()
    window.show()

    app.exec()
