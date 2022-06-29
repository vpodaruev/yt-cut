#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout

from gui import *
from ytvideo import *


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
