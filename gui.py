#!/usr/bin/env python3

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton


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


def getLineEditValue(lineEdit):
    text = lineEdit.text().strip()
    if not text:
        text = lineEdit.placeholderText()
    return text
