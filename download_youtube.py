import argparse
import subprocess as sp
import json

from pathlib import Path
from urllib.parse import urlparse
from pathvalidate import sanitize_filename

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


def to_hhmmss(seconds, delim=":"):
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    d = f"{seconds - 60*minutes:02d}"
    if minutes:
        d = f"{minutes - 60*hours:02d}" + delim + d
    if hours:
        d = f"{hours:02d}" + delim + d
    return d


def to_seconds(hhmmss):
    t = hhmmss.rsplit(":,.'")
    if len(t) == 1:
        return hhmmss
    elif len(t) == 2:
        mm, ss = t
        return str(int(mm)*60 + int(ss))
    hh, mm, ss = t
    return str((int(hh)*60 + int(mm))*60 + int(ss))


class NotYoutubeURL(RuntimeError):
    def __init__(self, url):
        super().__init__(f"'{url}' is not a youtube URL")


class YoutubeVideo:
    def __init__(self, url):
        netloc = urlparse(url).netloc
        if all([item not in netloc for item in {"youtube.com", "youtu.be"}]):
            raise NotYoutubeURL(url)
        p = sp.run([f"{args.youtube_dl}", "--dump-json", f"{url}"],
                    capture_output=True, encoding="utf-8", check=True)
        js = json.loads (p.stdout.strip())
        self.url = url
        self.title = js["title"]  if "title" in js  else "Video Title"
        self.channel = js["channel"]  if "channel" in js  else "Youtube Channel"
        self.duration = to_hhmmss(js["duration"])  if "duration" in js  else "0"
    
    def download_urls(self):
        p = sp.run([f"{args.youtube_dl}", "-g", f"{self.url}"],
                    capture_output=True, encoding="utf-8", check=True)
        return p.stdout.split()
    
    def download(self, filename, start, end):
        video, audio = self.download_urls()
        sp.run ([f"{args.ffmpeg}", "-y", "-loglevel", "quiet",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{video}",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{audio}",
                 "-c", "copy", f"{filename}"],
                 stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL, check=True)


class GoButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next = False
        self.toggle()
    
    def toggle(self):
        if self.next:
            self.setIcon(QIcon("go-prev.png"))
            self.setToolTip("Edit / Редактировать")
            self.next = False
        else:
            self.setIcon(QIcon("go-next.png"))
            self.setToolTip("Go! / Поехали дальше!")
            self.next = True

        
class YoutubeLink(QWidget):
    got_link = pyqtSignal(YoutubeVideo)
    edit_link = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        label = QLabel("Youtube link:")
        lineEdit = QLineEdit()
        lineEdit.setPlaceholderText("youtube link / ютуб ссылка")
        self.linkLineEdit = lineEdit
        
        goButton = GoButton()
        goButton.clicked.connect(self.link_edited)
        self.goButton = goButton
        
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(lineEdit)
        layout.addWidget(goButton)
        self.setLayout(layout)
    
    def link_edited(self):
        if not self.goButton.next:
            self.linkLineEdit.selectAll()
            self.linkLineEdit.setEnabled(True)
            self.goButton.toggle()
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
            v = YoutubeVideo(url)
            self.linkLineEdit.setEnabled(False)
            self.goButton.toggle()
            self.got_link.emit(v)
        except NotYoutubeURL as e:
            QMessageBox.warning(self.parent(), "Warning", f"URL: '{url}'\n It doesn't seem to be a YouTube link / Похоже, что это не ютуб-ссылка")
            self.linkLineEdit.clear()
        except sp.CalledProcessError as e:
            QMessageBox.critical(self.parent(), "Error", f"{e}\n\n{e.stderr}")
            self.linkLineEdit.clear()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        
        self.ytLink = YoutubeLink()
        self.ytLink.got_link.connect(self.yt_link_edited)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ytLink)
        mainLayout.addWidget(self.__yt_title(),
                             alignment=Qt.AlignmentFlag.AlignCenter)
        mainLayout.addLayout(self.__excerpt())
        mainLayout.addLayout(self.__save_as())
        mainLayout.addWidget(self.__download())
        mainLayout.addWidget(self.__about(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)
        
        self.set_step1_enabled(False)
        self.set_step2_enabled(False)
        
#         add about button with CS sign... upload to GitHub to spread info about CS
#         change window icon to Serpinsky carpet in a circle
        
        self.setCentralWidget(widget)
        self.setWindowTitle("Youtube Cut - Share the positive / Делись позитивом")
        self.setWindowIcon(QIcon("cs-logo.jpg"))
    
    def set_step1_enabled(self, ok):
        self.fromLineEdit.setEnabled(ok)
        self.toLineEdit.setEnabled(ok)
        self.excerptGoPushButton.setEnabled(ok)
        return
    
    def set_step2_enabled(self, ok):
        self.saveAsLineEdit.setEnabled(ok)
        self.saveAsPushButton.setEnabled(ok)
        self.downloadPushButton.setEnabled(ok)
        return
    
    def __yt_title(self):
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.hide()
        self.ytTitle = label
        return label
    
    def yt_link_edited(self, video):
        self.ytVideo = video
        self.ytTitle.setText("<b>"+ video.channel +"</b>: "+ video.title)
        self.toLineEdit.setPlaceholderText(video.duration)
        self.set_step1_enabled(True)
        self.ytTitle.show()
    
    def __excerpt(self):
        fromLabel = QLabel("Cut from:")
        fromLineEdit = QLineEdit()
        fromLineEdit.setPlaceholderText("00:00:00")
        self.fromLineEdit = fromLineEdit
        
        toLabel = QLabel("to:")
        toLineEdit = QLineEdit()
        toLineEdit.setPlaceholderText("00:00:00")
        self.toLineEdit = toLineEdit
        
        pushButton = QPushButton()
        pushButton.setIcon(QIcon("go-next.png"))
        pushButton.setToolTip("Go! / Поехали!")
        pushButton.clicked.connect(self.excerpt_changed)
        self.excerptGoPushButton = pushButton
        
        layout = QHBoxLayout()
        layout.addWidget(fromLabel)
        layout.addWidget(fromLineEdit)
        layout.addSpacing(5)
        layout.addWidget(toLabel)
        layout.addWidget(toLineEdit)
        layout.addWidget(pushButton)
        return layout
    
    def excerpt_changed(self):
        s, f = self.fromLineEdit.text(), self.toLineEdit.text()
        s, f = s.replace(":", "."), f.replace(":", ".")
        p = Path.cwd() / sanitize_filename(self.ytVideo.title)
        p = p.with_stem(p.stem + f"_{s}-{f}.mp4")
        self.saveAsLineEdit.setText(str(p))
        self.set_step2_enabled(True)
    
    def __save_as(self):
        saveAsLabel = QLabel("Save as:")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("output file / файл, куда сохранить")
        self.saveAsLineEdit = saveAsLineEdit
        
        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(QIcon("saveAs.png"))
        saveAsPushButton.clicked.connect(self.get_filename)
        self.saveAsPushButton = saveAsPushButton
        
        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(saveAsPushButton)
        return layout
    
    def get_filename(self):
        dirname = self.saveAsLineEdit.text().strip()
        if not dirname:
            dirname = "."
        elif not Path(dirname).is_dir():
            dirname = Path(dirname).parent.as_posix()
        file, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                   directory=dirname,
                                                   filter="Video Files (*.mp4)")
        if file:
            self.saveAsLineEdit.setText(file)
    
    def __download(self):
        pushButton = QPushButton("Download / Загрузить")
        pushButton.setIcon(QIcon("download.png"))
        pushButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pushButton.setEnabled(False)
        self.downloadPushButton = pushButton
        return pushButton
    
    def __about(self):
        label = QLabel("<font color=\"Grey\"><i>Created with love by AllatRa IT team</i></font>")
        label.setTextFormat(Qt.TextFormat.RichText)
        return label


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from Youtube.")
    parser.add_argument("--youtube-dl", type=Path, default=Path("youtube-dl"),
                        help="path to youtube-dl program [default: %(default)s]")
    parser.add_argument("--ffmpeg", type=Path, default=Path("ffmpeg"),
                        help="path to ffmpeg program [default: %(default)s]")

    app = QApplication(sys.argv)
    args = parser.parse_args()

    window = MainWindow()
    window.show()

    app.exec()
