from typing import Optional
from PyQt5.QtWidgets import QTextEdit, QWidget
from PyQt5.QtCore import QMimeData

class PlainTextEdit(QTextEdit):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            self.insertPlainText(source.text())