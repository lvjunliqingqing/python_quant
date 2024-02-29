import re
from collections import defaultdict
from copy import copy, deepcopy

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMessageBox, QDialog, QPushButton
import inspect
import ctypes
import pyqtgraph as pg


def get_message_box(title="委托失败", icon=QMessageBox.Critical, y_offset: int = 0, x_offset: int = 0, text: str = ""):
    """返回消息框对象"""
    message_box = QMessageBox()
    message_box.setIcon(icon)
    message_box.setWindowTitle(title)

    if y_offset:
        pos = QCursor.pos()
        pos.setY(pos.y() - y_offset)
        message_box.move(pos)
    elif x_offset:
        pos = QCursor.pos()
        pos.setX(pos.x() - x_offset)
        message_box.move(pos)
    else:
        message_box.move(QCursor.pos())

    if text:
        message_box.setText(text)

    return message_box


class TerminateThread(object):
    """终止线程类"""

    def stop(self, obj, text="停止回测"):
        obj.write_log(text)
        try:
            if obj.backtester_engine.thread:
                self._async_raise(obj.backtester_engine.thread.ident, SystemExit)
        except Exception as e:
            pass
            print(e)

    def _async_raise(self, tid, exctype):
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


class RelationshipChartDialog(QDialog):

    def __init__(self, result_values, linear_params, target_display, width=800, height=800, title="策略参数-线性关系图表"):
        super(RelationshipChartDialog, self).__init__()
        self.btnName_plot_map = defaultdict(list)
        self.init_ui(result_values, linear_params, target_display, width, height, title)

    def init_ui(self, result_values, linear_params, target_display, width, height, title):
        self.resize(width, height)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.groupbox_left = QtWidgets.QGroupBox("策略变量") # noqa
        self.groupbox_vbox = QtWidgets.QVBoxLayout()  # noqa 垂直布局对象(动态添加按钮)

        self.groupbox_left.setLayout(self.groupbox_vbox)

        if linear_params:
            for k, v in linear_params.items():
                if len(v) > 1:
                    name = copy(k)
                    btn = QPushButton(name, self)
                    btn.setObjectName(name)
                    btn.setCheckable(True)
                    btn.clicked[bool].connect(lambda: self.one_relationship_btn_click(result_values, linear_params, target_display))
                    self.groupbox_vbox.addWidget(btn)


        self.plot_widget = pg.GraphicsWindow()  # noqa

        h_box_layout = QtWidgets.QHBoxLayout()
        h_box_layout.addWidget(self.groupbox_left, stretch=2)
        h_box_layout.addWidget(self.plot_widget, stretch=10)

        self.setLayout(h_box_layout)

    def one_relationship_btn_click(self, result_values, linear_params, target_display):
        """点击策略变量按钮,画出线性关系图"""
        name = self.sender().text()
        if self.sender().isChecked():
            self.sender().setStyleSheet("QPushButton{background:blue}")  # noqa 设置按钮的背景色

            self.plot_widget.setBackground('w')  # 设置背景色
            x_temp = linear_params[name]
            y_dict = {}
            for i in result_values:
                a, b, c = i
                params_dict = re.search(r"{.+}", a).group()
                y_dict[str(copy(params_dict))] = copy(b)

            temp_dict = {}
            for k, v in linear_params.items():
                temp_dict[k] = v[-1]

            y = []
            x = []
            for j in x_temp:
                temp_dict[name] = j
                value = y_dict.get(str(temp_dict))
                if value:
                    y.append(round(copy(value), 3))
                    x.append(round(copy(j), 3))

            xdict = dict(enumerate(x))
            stringaxis = pg.AxisItem(orientation='bottom')
            stringaxis.setTicks([xdict.items()])
            plot = self.plot_widget.addPlot(axisItems={'bottom': stringaxis})
            self.btnName_plot_map[name].append(plot)
            plot.setTitle(title=f"{name} / {target_display} --- 线性关系", size='18pt', color="r")
            styles = {'color': 'r', 'font-size': '20px'}
            plot.setLabel('bottom', name, **styles)  # 如果背景色是黑色,则无法设置label的字体大小
            plot.setLabel('left', f"{target_display}(%)", **styles)
            curve = plot.plot(list(xdict.keys()), y, pen=(255, 0, 0), symbolBrush=(0, 0, 255), symbolPen='b')

        else:
            plot_list = self.btnName_plot_map.pop(name)
            for plot in plot_list:
                self.plot_widget.removeItem(plot)
            # self.plot_widget.clear()  # 清除画布上所有的画图
            self.sender().setStyleSheet("QPushButton{background:(100, 100, 100)}")