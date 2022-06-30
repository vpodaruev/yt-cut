#!/usr/bin/env python3

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton


class ToggleSwitch(QPushButton):
    def __init__(self, views):
        assert len(views) == 2
        for icon, text, tooltip in views:
            assert isinstance(icon, QIcon)
            assert isinstance(text, str)
            assert isinstance(tooltip, str)
        super().__init__()
        self.views = views
        self.turn_on(True)
    
    def toggle(self):
        self.turn_on(not self.on)
    
    def turn_on(self, on):
        self.on = on
        icon, text, tip = self.views[int(on)]
        self.setIcon(icon)
        self.setText(text)
        self.setToolTip(tip)


class GoButton(ToggleSwitch):    
    def __init__(self):
        views = [(QIcon("go-prev.png"), "", "Edit / Редактировать"),
                 (QIcon("go-next.png"), "", "Go! / Поехали дальше!")]
        super().__init__(views)


def getLineEditValue(lineEdit):
    text = lineEdit.text().strip()
    if not text:
        text = lineEdit.placeholderText()
    return text
