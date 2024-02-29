"""
Author: lv jun
"""
from PyQt5 import QtGui
from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QIntValidator

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange, Direction, Offset, OrderType
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtCore, QtWidgets


class QuickLiquidationComponentWidget(QtWidgets.QDialog):
    """"""
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, data, tick):
        """"""
        super().__init__()
        self.evnet_engine = event_engine
        self.main_engine = main_engine
        self.tick = tick
        self.data = data
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("卖出")
        # 设置了固定高度或者使用setWindowFlags设置要显示按钮,但没有设置最大化显示时,则最大化按钮不可点击。
        self.setFixedWidth(300)
        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        self.exchange_combo = QtWidgets.QLineEdit()  # 交易所输入框
        self.exchange_combo.setFocusPolicy(QtCore.Qt.NoFocus)

        self.symbol_edit = QtWidgets.QLineEdit()   # 代码输入框
        self.symbol_edit.setFocusPolicy(QtCore.Qt.NoFocus)

        double_validator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)
        self.trade_edit = QtWidgets.QLineEdit()  # 卖出价输入框
        self.trade_edit.setValidator(double_validator)
        self.trade_edit.setMaxLength(10)

        self.trade_edit.setText(str(self.tick.last_price))
        self.exchange_combo.setText(str(self.data.exchange.value))
        self.symbol_edit.setText(str(self.data.symbol))

        int_validator = QIntValidator()
        int_validator.setBottom(0)
        self.volume_SpinBox = QtWidgets.QLineEdit()  # 卖出数量输入框
        self.volume_SpinBox.setText(str(self.data.volume))
        self.volume_SpinBox.setFocusPolicy(QtCore.Qt.NoFocus)

        close_position_button = QtWidgets.QPushButton("卖出")
        close_position_button.clicked.connect(self.close_a_position)

        form = QtWidgets.QFormLayout()
        form.addRow("交易所", self.exchange_combo)
        form.addRow("代码", self.symbol_edit)
        form.addRow("卖出价格", self.trade_edit)
        form.addRow("卖出数量(手数)", self.volume_SpinBox)
        form.addRow(QtWidgets.QLabel())
        form.addRow(close_position_button)
        self.setLayout(form)

    def close_a_position(self, event):
        reply = QtWidgets.QMessageBox.question(
            self,
            "委托确认",
            f"合约代码：{self.data.symbol}.{self.data.exchange.value}   卖出价格：{self.trade_edit.text()}   卖出数量：{self.data.volume}  ",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # cta策略平仓
            cta_strategy_engine = self.main_engine.get_engine("CtaStrategy")
            if cta_strategy_engine:
                cta_strategy_engine.on_close(self.data, self.tick)
            # 组合策略平仓
            portfolio_strategy_engine = self.main_engine.get_engine("PortfolioStrategy")
            if portfolio_strategy_engine:
                portfolio_strategy_engine.on_close(self.data, self.tick)
        else:
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Call csv_loader engine close function before exit.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "退出",
            "确认退出？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

