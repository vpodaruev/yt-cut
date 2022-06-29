#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout


class SaveAsFile(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        saveAsLabel = QLabel("Save as:")
        saveAsLineEdit = QLineEdit()
        saveAsLineEdit.setPlaceholderText("file where to save / файл, куда сохранить")
        saveAsLineEdit.textChanged.connect(saveAsLineEdit.setToolTip)
        self.saveAsLineEdit = saveAsLineEdit
        
        saveAsPushButton = QPushButton()
        saveAsPushButton.setIcon(QIcon("saveAs.png"))
        saveAsPushButton.clicked.connect(self.browse)
        self.saveAsPushButton = saveAsPushButton
        
        layout = QHBoxLayout()
        layout.addWidget(saveAsLabel)
        layout.addWidget(saveAsLineEdit)
        layout.addWidget(saveAsPushButton)
        self.setLayout(layout)
    
    def set_filename(self, file):
        if not file:
            return
        self.saveAsLineEdit.setText(file)
    
    def get_filename(self):
        return self.saveAsLineEdit.text()
    
    def browse(self):
        file, filter = QFileDialog.getSaveFileName(self, caption="Save As",
                                                   directory=self.get_filename(),
                                                   filter="Video Files (*.mp4)")
        self.set_filename(file)
