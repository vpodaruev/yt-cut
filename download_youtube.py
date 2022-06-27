import argparse
import subprocess as sp
import json, re

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
    return f"{hours:02d}{delim}{minutes - 60*hours:02d}{delim}{seconds - 60*minutes:02d}"


def to_seconds(hhmmss):
    t = re.split(r"[:,.']", hhmmss)
    if len(t) == 1:
        return int(hhmmss)
    elif len(t) == 2:
        mm, ss = t
        return int(mm)*60 + int(ss)
    hh, mm, ss = t
    return (int(hh)*60 + int(mm))*60 + int(ss)


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
        self.linkLineEdit = QLineEdit()
        self.linkLineEdit.setPlaceholderText("youtube link / ютуб ссылка")
        
        self.goButton = GoButton()
        self.goButton.clicked.connect(self.link_edited)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget(label)
        hLayout.addWidget(self.linkLineEdit)
        hLayout.addWidget(self.goButton)
        
        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.hide()
        
        layout = QVBoxLayout()
        layout.addLayout(hLayout)
        layout.addWidget(self.titleLabel,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
    
    def link_edited(self):
        if not self.goButton.next:
            self.titleLabel.setText("")
            self.titleLabel.hide()
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
            v = YoutubeVideo(url)
            self.linkLineEdit.setEnabled(False)
            self.goButton.toggle()
            self.titleLabel.setText("<b>"+ v.channel +"</b>: "+ v.title)
            self.titleLabel.show()
            self.got_link.emit(v)
        except NotYoutubeURL as e:
            QMessageBox.warning(self.parent(), "Warning", f"URL: '{url}'\n It doesn't seem to be a YouTube link / Похоже, что это не ютуб-ссылка")
            self.linkLineEdit.clear()
        except sp.CalledProcessError as e:
            QMessageBox.critical(self.parent(), "Error", f"{e}\n\n{e.stderr}")
            self.linkLineEdit.clear()


def getLineEditValue(lineEdit):
    text = lineEdit.text().strip()
    if not text:
        text = lineEdit.placeholderText()
    return text


class TimeSpan(QWidget):
    got_interval = pyqtSignal()
    edit_interval = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        timingPattern = QRegularExpression("((\d{1,2}[:,.']){1,2}\d{1,2})|(\d+)")
        timingValidator = QRegularExpressionValidator(timingPattern)
        
        fromLabel = QLabel("Cut from:")
        fromLineEdit = QLineEdit()
        fromLineEdit.setValidator(timingValidator)
        self.fromLineEdit = fromLineEdit
        
        toLabel = QLabel("to:")
        toLineEdit = QLineEdit()
        toLineEdit.setValidator(timingValidator)
        self.toLineEdit = toLineEdit
        
        goButton = GoButton()
        goButton.clicked.connect(self.interval_edited)
        self.goButton = goButton
        
        layout = QHBoxLayout()
        layout.addWidget(fromLabel)
        layout.addWidget(fromLineEdit)
        layout.addSpacing(5)
        layout.addWidget(toLabel)
        layout.addWidget(toLineEdit)
        layout.addWidget(goButton)
        self.setLayout(layout)
        self.init()
        self.setEnabled(False)
    
    def init(self):
        self.clear_interval()
        zero = to_hhmmss(0)
        self.fromLineEdit.setPlaceholderText(zero)
        self.fromLineEdit.setToolTip(f"min {zero}")
        self.fromLineEdit.setEnabled(True)
        self.toLineEdit.setPlaceholderText(zero)
        self.toLineEdit.setToolTip(f"max {zero}")
        self.toLineEdit.setEnabled(True)
        if not self.goButton.next:
            self.goButton.toggle()
    
    def set_duration(self, duration):
        self.duration = duration
        self.toLineEdit.setPlaceholderText(duration)
        self.toLineEdit.setToolTip(f"max {duration}")
        self.goButton.setEnabled(True)
    
    def get_interval(self):
        return getLineEditValue(self.fromLineEdit), getLineEditValue(self.toLineEdit)
    
    def set_interval(self, start, finish):
        self.fromLineEdit.setText(to_hhmmss(start))
        self.toLineEdit.setText(to_hhmmss(finish))
    
    def clear_interval(self):
        self.fromLineEdit.setText("")
        self.toLineEdit.setText("")
    
    def check_and_beautify(self):
        s, f = getLineEditValue(self.fromLineEdit), getLineEditValue(self.toLineEdit)
        si, fi = to_seconds(s), to_seconds(f)
        if fi < si:
            raise ValueError(f"The initial value ({s}) must be smaller than the final value ({f}) / Начальное значение ({s}) должно быть меньше конечного ({f})!")
        elif to_seconds(self.duration) < fi:
            raise ValueError(f"The final value ({f}) must not exceed the duration ({self.duration}) / Конечное значение ({s}) не должно превышать продолжительность ({self.duration})!")
        self.set_interval(si, fi)
    
    def interval_edited(self):
        try:
            self.check_and_beautify()
        except ValueError as e:
            QMessageBox.warning(self.parent(), "Warning", str(e))
            return
        
        if self.goButton.next:
            self.fromLineEdit.setEnabled(False)
            self.toLineEdit.setEnabled(False)
            self.got_interval.emit()
        else:
            self.fromLineEdit.setEnabled(True)
            self.toLineEdit.setEnabled(True)
            self.edit_interval.emit()
        self.goButton.toggle()
    
    def as_suffix(self):
        s, f = self.get_interval()
        s, f = s.replace(":", "."), f.replace(":", ".")
        return f"_{s}-{f}"


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        
        self.ytLink = YoutubeLink()
        self.ytLink.got_link.connect(self.got_yt_link)
        self.ytLink.edit_link.connect(self.edit_yt_link)
        
        self.timeSpan = TimeSpan()
        self.timeSpan.setEnabled(False)
        self.timeSpan.got_interval.connect(self.got_interval)
        self.timeSpan.edit_interval.connect(self.edit_interval)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ytLink)
        mainLayout.addWidget(self.timeSpan)
        mainLayout.addLayout(self.__save_as())
        mainLayout.addWidget(self.__download())
        mainLayout.addWidget(self.__about(),
                             alignment=Qt.AlignmentFlag.AlignRight)
        widget = QWidget()
        widget.setLayout(mainLayout)
        
        self.set_step2_enabled(False)
        
#         add about button with CS sign... upload to GitHub to spread info about CS
#         change window icon to Serpinsky carpet in a circle
        
        self.setCentralWidget(widget)
        self.setWindowTitle("Youtube Cut - Share the positive / Делись позитивом")
        self.setWindowIcon(QIcon("cs-logo.jpg"))
    
    def set_step2_enabled(self, ok):
        self.saveAsLineEdit.setEnabled(ok)
        self.saveAsPushButton.setEnabled(ok)
        self.downloadPushButton.setEnabled(ok)
        return
    
    def got_yt_link(self, video):
        self.ytVideo = video
        self.timeSpan.set_duration(video.duration)
        self.timeSpan.setEnabled(True)
    
    def edit_yt_link(self):
        self.timeSpan.init()
        self.timeSpan.setEnabled(False)
    
    def got_interval(self):
        p = Path.cwd() / sanitize_filename(self.ytVideo.title)
        p = p.with_stem(p.stem + self.timeSpan.as_suffix() +".mp4")
        path = str(p)
        self.saveAsLineEdit.setPlaceholderText(path)
        self.saveAsLineEdit.setToolTip(path)
        self.set_step2_enabled(True)
    
    def edit_interval(self):
        pass
    
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
        dirname = getLineEditValue(self.saveAsLineEdit)
        if not dirname:
            dirname = "."
        file, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                   directory=dirname,
                                                   filter="Video Files (*.mp4)")
        if file:
            self.saveAsLineEdit.setText(file)
            self.saveAsLineEdit.setToolTip(file)
    
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
