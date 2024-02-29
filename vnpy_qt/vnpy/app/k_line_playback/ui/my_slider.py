
from PyQt5.QtWidgets import QSlider, QLabel


class MyQSlider(QSlider):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.resize(200, 30)
        label = QLabel(self)
        self.label = label
        label.setText('1')
        label.setStyleSheet('background-color:white;color:black;font:bold 20px;')
        label.hide()

    def mousePressEvent(self, evt):
        super().mousePressEvent(evt)  # noqa
        y = (1 - ((self.value() - self.minimum()) / (self.maximum() - self.minimum()))) * (self.height() - self.label.height())
        x = (self.width() - self.label.width()) / 2
        self.label.move(x, y)
        self.label.show()
        self.label.setText(str(self.value()))

    def mouseMoveEvent(self, evt):
        super().mouseMoveEvent(evt)  # noqa
        y = (1 - ((self.value() - self.minimum()) / (self.maximum() - self.minimum()))) * (self.height() - self.label.height())
        x = (self.width() - self.label.width()) / 2
        self.label.move(x, y)
        self.label.setText(str(self.value()))
        self.label.adjustSize()

    def mouseReleaseEvent(self, evt):
        super().mouseReleaseEvent(evt)
        self.label.hide()
