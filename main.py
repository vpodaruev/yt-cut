#!/usr/bin/env python3

from argparse import ArgumentParser

from pathlib import Path
import sys

from PyQt6.QtWidgets import (QApplication)

import mainwindow as mw
import ytvideo as ytv


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

    window = mw.MainWindow()
    window.show()

    app.exec()
