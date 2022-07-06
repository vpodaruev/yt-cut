#!/usr/bin/env python3

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout

from gui import *
from utils import *


class TimeSpan(QWidget):
    got_interval = pyqtSignal(str, str)
    edit_interval = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        timingPattern = QRegularExpression("\d+([:,.'][0-5]\d){0,2}")
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
        self.reset()
        self.setEnabled(False)
    
    def reset(self):
        self.clear_interval()
        zero = to_hhmmss(0)
        self.fromLineEdit.setPlaceholderText(zero)
        self.fromLineEdit.setToolTip(f"min {zero}")
        self.fromLineEdit.setEnabled(True)
        self.toLineEdit.setPlaceholderText(zero)
        self.toLineEdit.setToolTip(f"max {zero}")
        self.toLineEdit.setEnabled(True)
        if not self.goButton.on:
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
        if fi <= si:
            raise ValueError(f"The initial value ({s}) must be smaller than the final value ({f})!"
                             f" / Начальное значение ({s}) должно быть меньше конечного ({f})!")
        elif to_seconds(self.duration) < fi:
            raise ValueError(f"The final value ({f}) must not exceed the duration ({self.duration})!"
                             f" / Конечное значение ({f}) не должно превышать продолжительность ({self.duration})!")
        self.set_interval(si, fi)
    
    @pyqtSlot()
    def interval_edited(self):
        try:
            self.check_and_beautify()
        except ValueError as e:
            QMessageBox.warning(self.parent(), "Warning", str(e))
            return
        
        if self.goButton.on:
            self.fromLineEdit.setEnabled(False)
            self.toLineEdit.setEnabled(False)
            self.got_interval.emit(*self.get_interval())
        else:
            self.fromLineEdit.setEnabled(True)
            self.toLineEdit.setEnabled(True)
            self.edit_interval.emit()
        self.goButton.toggle()
