#!/usr/bin/env python3

from pathlib import Path

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
     QWidget, QLabel, QPushButton,
     QLineEdit, QFileDialog, QHBoxLayout)

import gui.common as com
import gui.ytvideo as ytv


default_suffix = f".{ytv.video_format}"

filter_map = {
    f".{ytv.video_format}": f"Video Files (*.{ytv.video_format})",
    f".{ytv.audio_format}": f"Audio Files (*.{ytv.audio_format})",
}


class SaveAsFile(QWidget):
    changed = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        saveAsLabel = QLabel("Save as:")
        saveAsLabel.setToolTip("Сохранить как")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("File where to save / "
                                          "Файл, куда сохранить")
        saveAsLineEdit.textChanged.connect(self.filename_changed)
        self.saveAsLineEdit = saveAsLineEdit

        self.directory = Path.cwd()

        extLabel = QLabel(default_suffix)
        self.extLabel = extLabel

        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(com.icon("icons/saveAs.png"))
        saveAsPushButton.setToolTip("Choose where to save / "
                                    "Выбрать, куда сохранить")
        saveAsPushButton.clicked.connect(self.browse)
        self.saveAsPushButton = saveAsPushButton

        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(extLabel)
        layout.addWidget(saveAsPushButton)
        self.setLayout(layout)

    def lock(self):
        self.saveAsLineEdit.setReadOnly(True)
        self.saveAsPushButton.setEnabled(False)

    def unlock(self):
        self.saveAsPushButton.setEnabled(True)
        self.saveAsLineEdit.setReadOnly(False)

    @pyqtSlot(str)
    def filename_changed(self, file):
        self.saveAsLineEdit.setToolTip(self._with_suffix(file))
        self.changed.emit(bool(file))

    def reset(self, suffix=True):
        name = self.get_filename()
        if not name:
            return  # nothing to do
        tmp = Path(name).parent
        if tmp.is_dir():
            self.directory = tmp
        self.saveAsLineEdit.clear()
        if suffix:
            self.set_suffix(default_suffix)

    @pyqtSlot(str)
    def set_filename(self, file):
        if not file:
            return  # nothing to do
        if Path(file).parent == Path("."):
            file = (self.directory / file).as_posix()
        self._beautify_filename(file=file)

    def get_filename(self):
        file = self._beautify_filename()
        return self._with_suffix(file)

    def set_suffix(self, suffix):
        if suffix not in filter_map.keys():
            raise RuntimeError(f"unsupported suffix ({suffix})")
        file = self._beautify_filename()  # user may edit
        self.extLabel.setText(suffix)
        self.filename_changed(file)  # update tooltip

    def get_suffix(self):
        return self.extLabel.text()

    @pyqtSlot()
    def browse(self):
        file, filter = QFileDialog.getSaveFileName(
                                     self, caption="Save As",
                                     directory=self.get_filename(),
                                     filter=filter_map[self.get_suffix()])
        self.set_filename(file)

    def dump(self):
        return {
            "file": self.get_filename() if self.saveAsLineEdit else None,
        }

    def _with_suffix(self, file):
        """Add valid suffix to `file`"""
        if not file:
            return file
        ext = self.get_suffix()
        return file + ext if not file.endswith(ext) else file

    def _remove_suffix(self, file):
        """Remove `file` suffix if it is valid"""
        if not file:
            return file
        ext = self.get_suffix()
        return file.rsplit(".", maxsplit=1)[0] if file.endswith(ext) else file

    def _beautify_filename(self, file=None):
        if file is None:
            file = self.saveAsLineEdit.text()
        file = self._remove_suffix(file.strip()).rstrip()
        self.saveAsLineEdit.setText(file)
        return file
