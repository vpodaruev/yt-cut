import argparse

from pathlib import Path
import subprocess as sp

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QMainWindow):
    def __yt_url (self):
        label = QLabel("Youtube link:")
        lineEdit = QLineEdit()
        lineEdit.setPlaceholderText("youtube link / ютуб ссылка")
        self.ytUrlLineEdit = lineEdit
        
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(lineEdit)
        return layout
    
    def __excerpt (self):
        fromLabel = QLabel("Cut from:")
        fromLineEdit = QLineEdit()
        fromLineEdit.setPlaceholderText("00:00:00")
        self.fromLineEdit = fromLineEdit
        
        toLabel = QLabel("to:")
        toLineEdit = QLineEdit()
        toLineEdit.setPlaceholderText("00:00:00")
        self.toLineEdit = toLineEdit
        
        layout = QHBoxLayout()
        layout.addWidget(fromLabel)
        layout.addWidget(fromLineEdit)
        layout.addSpacing(5)
        layout.addWidget(toLabel)
        layout.addWidget(toLineEdit)
        return layout
    
    def __save_as(self):
        saveAsLabel = QLabel("Save as:")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("output file / файл, куда сохранить")
        self.saveAsLineEdit = saveAsLineEdit
        
        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(QIcon("saveAs.png"))
        saveAsPushButton.clicked.connect(self.get_filename)
        
        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(saveAsPushButton)
        return layout
    
    def get_filename(self):
        file, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                   directory=Path.cwd().as_posix(),
                                                   filter="Video Files (*.mp4)")
        self.saveAsLineEdit.setText(file)
    
    def __download(self):
        pushButton = QPushButton("Download / Загрузить")
        pushButton.setIcon(QIcon("download.png"))
        pushButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.downloadPushButton = pushButton
        return pushButton
    
    def __about(self):
        label = QLabel("<font color=\"Grey\"><i>Created with love by AllatRa IT team</i></font>")
        label.setTextFormat(Qt.TextFormat.RichText)
        return label
    
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(self.__yt_url())
        mainLayout.addLayout(self.__excerpt())
        mainLayout.addLayout(self.__save_as())
        mainLayout.addWidget(self.__download())
        mainLayout.addWidget(self.__about(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)
        
        self.setCentralWidget(widget)
        self.setWindowTitle("Youtube Cut")
        self.setWindowIcon(QIcon("cs-logo.jpg"))


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
