#!/usr/bin/env python3

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
     QWidget, QLabel, QPushButton,
     QLineEdit, QFileDialog, QHBoxLayout)

import gui.common as com


class SaveAsFile(QWidget):
    changed = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        saveAsLabel = QLabel("Save as:")
        saveAsLabel.setToolTip("Сохранить как")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("file where to save"
                                          " / файл, куда сохранить")
        saveAsLineEdit.textChanged.connect(self.filename_changed)
        self.saveAsLineEdit = saveAsLineEdit

        self.directory = Path.cwd()

        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(com.icon("icons/saveAs.png"))
        saveAsPushButton.setToolTip("Choose where to save / Выбрать, куда сохранить")
        saveAsPushButton.clicked.connect(self.browse)
        self.saveAsPushButton = saveAsPushButton

        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(saveAsPushButton)
        self.setLayout(layout)

    def lock(self):
        self.saveAsLineEdit.setReadOnly(True)
        self.saveAsPushButton.setEnabled(False)

    def unlock(self):
        self.saveAsPushButton.setEnabled(True)
        self.saveAsLineEdit.setReadOnly(False)

    def filename_changed(self, file):
        self.saveAsLineEdit.setToolTip(file)
        self.changed.emit(bool(file))

    def reset(self):
        name = self.get_filename()
        if not name:
            return  # nothing to do
        tmp = Path(name).parent
        if tmp.is_dir():
            self.directory = tmp
        self.saveAsLineEdit.clear()

    def set_filename(self, file):
        if not file:
            return
        if Path(file).parent == Path("."):
            file = (self.directory / file).as_posix()
        self.saveAsLineEdit.setText(file)

    def get_filename(self):
        return self.saveAsLineEdit.text()

    def browse(self):
        file, filter = QFileDialog.getSaveFileName(
                                     self, caption="Save As",
                                     directory=self.get_filename(),
                                     filter="Video Files (*.mp4)")
        self.set_filename(file)

    def dump(self):
        return {
            "file": self.get_filename() if self.saveAsLineEdit else None,
        }
