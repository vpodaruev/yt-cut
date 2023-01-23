#!/usr/bin/env python3

from PyQt6.QtCore import (pyqtSignal, pyqtSlot, QRegularExpression)
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QComboBox, QMessageBox, QHBoxLayout, QVBoxLayout)

import gui.common as com
import gui.ytvideo as ytv

import utils as ut


class TimeSpan(QWidget):
    got_interval = pyqtSignal(str, str)
    edit_interval = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        timingPattern = QRegularExpression(r"\d+([:,.' ][0-5]\d){0,2}")
        timingValidator = QRegularExpressionValidator(timingPattern)

        formatComboBox = QComboBox()
        formatComboBox.setEditable(False)
        self.formatComboBox = formatComboBox

        fromLabel = QLabel("Cut from:")
        fromLineEdit = QLineEdit()
        fromLineEdit.setValidator(timingValidator)
        self.fromLineEdit = fromLineEdit

        toLabel = QLabel("to:")
        toLineEdit = QLineEdit()
        toLineEdit.setValidator(timingValidator)
        self.toLineEdit = toLineEdit

        goButton = com.GoButton()
        goButton.clicked.connect(self.interval_edited)
        self.goButton = goButton

        hLayout = QHBoxLayout()
        hLayout.addWidget(fromLabel)
        hLayout.addWidget(fromLineEdit)
        hLayout.addSpacing(5)
        hLayout.addWidget(toLabel)
        hLayout.addWidget(toLineEdit)
        hLayout.addSpacing(5)
        hLayout.addWidget(goButton)

        layout = QVBoxLayout()
        layout.addWidget(formatComboBox)
        layout.addLayout(hLayout)
        self.setLayout(layout)
        self.reset()
        self.setEnabled(False)

    def reset(self):
        self.clear_interval()
        zero = ut.to_hhmmss(0)
        self.fromLineEdit.setPlaceholderText(zero)
        self.fromLineEdit.setToolTip(f"min {zero}")
        self.fromLineEdit.setEnabled(True)
        self.toLineEdit.setPlaceholderText(zero)
        self.toLineEdit.setToolTip(f"max {zero}")
        self.toLineEdit.setEnabled(True)
        self.clear_format()
        self.formatComboBox.setEnabled(True)
        if not self.goButton.on:
            self.goButton.toggle()

    def set_duration(self, duration, url_time=None):
        self.duration = duration
        self.toLineEdit.setPlaceholderText(duration)
        self.toLineEdit.setToolTip(f"max {duration}")
        if url_time:
            self.fromLineEdit.setText(ut.to_hhmmss(url_time))
        self.goButton.setEnabled(True)

    def get_format(self):
        return self.formatComboBox.currentText()

    def set_format(self, formats):
        self.formatComboBox.clear()
        for f in formats:
            self.formatComboBox.addItem(f)

    def clear_format(self):
        self.set_format([ytv.default_format])

    def get_interval(self):
        return (com.getLineEditValue(self.fromLineEdit),
                com.getLineEditValue(self.toLineEdit))

    def set_interval(self, start, finish):
        self.fromLineEdit.setText(ut.to_hhmmss(start))
        self.toLineEdit.setText(ut.to_hhmmss(finish))

    def clear_interval(self):
        self.fromLineEdit.setText("")
        self.toLineEdit.setText("")

    def check_and_beautify(self):
        s, f = (com.getLineEditValue(self.fromLineEdit),
                com.getLineEditValue(self.toLineEdit))
        si, fi = (ut.to_seconds(s),
                  ut.to_seconds(f))
        if fi <= si:
            raise ValueError(f"The initial value ({s}) must be smaller"
                             f" than the final value ({f})!"
                             f" / Начальное значение ({s}) должно быть"
                             f" меньше конечного ({f})!")
        elif ut.to_seconds(self.duration) < fi:
            raise ValueError(f"The final value ({f}) must"
                             f" not exceed the duration ({self.duration})!"
                             f" / Конечное значение ({f}) не должно превышать"
                             f" продолжительность ({self.duration})!")
        self.set_interval(si, fi)

    @pyqtSlot()
    def interval_edited(self):
        try:
            self.check_and_beautify()
        except ValueError as e:
            QMessageBox.warning(self.parent(), "Warning", str(e))
            return

        if self.goButton.on:
            self.formatComboBox.setEnabled(False)
            self.fromLineEdit.setEnabled(False)
            self.toLineEdit.setEnabled(False)
            self.got_interval.emit(*self.get_interval())
        else:
            self.formatComboBox.setEnabled(True)
            self.fromLineEdit.setEnabled(True)
            self.toLineEdit.setEnabled(True)
            self.edit_interval.emit()
        self.goButton.toggle()

    def dump(self):
        return {
            "format": self.get_format() if self.formatComboBox else None,
            "from": self.fromLineEdit.text() if self.fromLineEdit else None,
            "to": self.toLineEdit.text() if self.toLineEdit else None,
        }
