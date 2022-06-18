import argparse

from pathlib import Path
import subprocess as sp

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)

        ytUrlLabel = QLabel("Youtube link:")
        ytUrlLineEdit = QLineEdit()
        ytUrlLineEdit.setPlaceholderText("youtube link")
        self.ytUrlLineEdit = ytUrlLineEdit
        ytUrlLayout = QHBoxLayout()
        ytUrlLayout.addWidget(ytUrlLabel)
        ytUrlLayout.addWidget(ytUrlLineEdit)
        
        fromLabel = QLabel("Cut from:")
        fromLineEdit = QLineEdit()
        fromLineEdit.setPlaceholderText("00:00:00")
        self.fromLineEdit = fromLineEdit
        toLabel = QLabel("to:")
        toLineEdit = QLineEdit()
        toLineEdit.setPlaceholderText("00:00:00")
        self.toLineEdit = toLineEdit
        timeLayout = QHBoxLayout()
        timeLayout.addWidget(fromLabel)
        timeLayout.addWidget(fromLineEdit)
        timeLayout.addSpacing(5)
        timeLayout.addWidget(toLabel)
        timeLayout.addWidget(toLineEdit)

        saveAsLabel = QLabel("Save as:")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("output file")
        self.saveAsLineEdit = saveAsLineEdit
        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(QIcon("saveAs.png"))
        saveAsPushButton.clicked.connect(self.get_filename)
        saveAsLayout = QHBoxLayout()
        saveAsLayout.addWidget(saveAsLabel)
        saveAsLayout.addWidget(saveAsLineEdit)
        saveAsLayout.addWidget(saveAsPushButton)

        downloadPushButton = QPushButton("Download")
        downloadPushButton.setIcon(QIcon("download.png"))
        downloadPushButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        aboutLabel = QLabel("<font color=\"Grey\"><i>Created with love by AllatRa IT team</i></font color>")
        aboutLabel.setTextFormat(Qt.TextFormat.RichText)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(ytUrlLayout)
        mainLayout.addLayout(timeLayout)
        mainLayout.addLayout(saveAsLayout)
        mainLayout.addWidget(downloadPushButton, stretch=1)
        mainLayout.addWidget(aboutLabel,
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)

        self.setCentralWidget(widget)
        self.setWindowTitle("Youtube Cut")
        self.setWindowIcon(QIcon("cs-logo.jpg"))

    def get_filename (self):
        filename, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                       directory=Path.cwd().as_posix(),
                                                       filter="Video Files (*.mp4)")
        self.saveAsLineEdit.setText(filename)
        


def direct_links(youtube_dl, url):
    print(">", f"{url}")
    p = sp.run([f"{youtube_dl}", "-g", f"{url}"], capture_output=True, encoding="utf-8", check=True)
    return p.stdout.split()

def download(ffmpeg, urls, start, end, name):
    try :
        sp.run ([f"{ffmpeg}", "-y", "-loglevel", "quiet",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{urls[0]}",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{urls[1]}",
                 "-c", "copy", f"{name}"],
                 stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL, check=True)
    except sp.SubprocessError as e :
        with open("err.log", "a") as log :
            print (e, file=log)


if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Download files from Youtube.")
#     parser.add_argument("url", type=str, help="Youtube video link")
#     parser.add_argument("--start", type=str, help="Start time")
#     parser.add_argument("--end", type=str, help="End time")
#     parser.add_argument("--youtube-dl", type=Path, default=Path("dist/youtube-dl"),
#                         help="path to youtube-dl program [default: %(default)s]")
#     parser.add_argument("--ffmpeg", type=Path, default=Path("dist/ffmpeg"),
#                         help="path to ffmpeg program [default: %(default)s]")

#     args = parser.parse_args()
#     urls = direct_links(args.youtube_dl, args.url)
#     download(args.ffmpeg, urls, args.start, args.end, "output.mp4")

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
