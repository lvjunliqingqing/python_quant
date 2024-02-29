"""
Author: lv jun
"""
import random

from PyQt5 import QtGui
from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QIntValidator

from vnpy.controller.global_variable import get_value
from vnpy.controller.trade_operation import get_order_ref_value
from vnpy.event import EventEngine
from vnpy.model.order_data_model import OrderDataModel
from vnpy.trader.constant import Exchange, Direction, Offset, OrderType, Status
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderData
from vnpy.trader.setting import CTA_STRATEGY_SETTING_FILENAME
from vnpy.trader.ui import QtCore, QtWidgets
from vnpy.trader.utility import load_json
from ..engine import APP_NAME


class ManualPositionAdjustmentWidget(QtWidgets.QWidget):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()
        self.manualPositionAdjustment_engine = main_engine.get_engine(APP_NAME)
        self.main_engine = main_engine
        self.settings = {}  # 存储策略配置参数,类名为键,策略配置参数为值。
        self.init_ui()
        self.init_strategy_settings()
        # test-定时器的使用
        # event_engine.register(EVENT_TIMER, self.timer_test)

    def init_ui(self):
        """"""
        self.setWindowTitle("手工输入开仓单")
        # 设置了固定高度或者使用setWindowFlags设置要显示按钮,但没有设置最大化显示时,则最大化按钮不可点击。
        self.setFixedWidth(600)
        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        self.exchange_combo = QtWidgets.QComboBox()
        for i in Exchange:
            self.exchange_combo.addItem(str(i.name), i)

        self.symbol_edit = QtWidgets.QLineEdit()

        self.direction_combo = QtWidgets.QComboBox()
        for i in Direction:
            self.direction_combo.addItem(str(i.value), i)

        self.offset_combo = QtWidgets.QComboBox()
        for i in Offset:
            if i.value:
                self.offset_combo.addItem(str(i.value), i)

        self.orderType_combo = QtWidgets.QComboBox()
        for i in OrderType:
            if i.value:
                self.orderType_combo.addItem(str(i.value), i)

        self.datetime_edit = QtWidgets.QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd  HH:mm:ss")
        self.datetime_edit.setMaximumDate(QDate.currentDate())

        double_validator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)
        self.trade_edit = QtWidgets.QLineEdit()
        self.trade_edit.setValidator(double_validator)
        self.trade_edit.setMaxLength(10)

        int_validator = QIntValidator()
        int_validator.setBottom(0)
        self.volume_edit = QtWidgets.QLineEdit()
        self.volume_edit.setValidator(int_validator)
        self.volume_edit.setMaxLength(5)

        self.gateway_combo = QtWidgets.QComboBox()
        self.gateway_combo.addItems(self.main_engine.get_all_gateway_names())

        self.strategy_name_combo = QtWidgets.QComboBox()
        self.strategy_name_combo.addItems(self.load_strategy_setting())

        load_button = QtWidgets.QPushButton("保存数据")
        load_button.clicked.connect(self.save_position_data)

        form = QtWidgets.QFormLayout()
        form.addRow("交易所", self.exchange_combo)
        form.addRow("代码", self.symbol_edit)
        form.addRow("方向", self.direction_combo)
        form.addRow("开平", self.offset_combo)
        form.addRow("类型", self.orderType_combo)
        form.addRow("时间", self.datetime_edit)
        form.addRow("成交价", self.trade_edit)
        form.addRow("成交量(手数)", self.volume_edit)
        form.addRow("接口", self.gateway_combo)
        form.addRow("策略", self.strategy_name_combo)

        form.addRow(QtWidgets.QLabel())
        form.addRow(load_button)
        self.setLayout(form)

    def save_position_data(self):
        """"""
        account_info = get_value("account_info")
        symbol = str(self.symbol_edit.text())
        if not symbol:
            QtWidgets.QMessageBox.critical(self, "保存失败", "请输入合约代码")
            return

        price_text = str(self.trade_edit.text())
        if not price_text:
            QtWidgets.QMessageBox.critical(self, "输入提示", "请输入成交价")
            return
        else:
            price = float(price_text)

        volume_text = str(self.volume_edit.text())
        if not volume_text:
            QtWidgets.QMessageBox.critical(self, "输入提示", "请输入成交量")
            return
        else:
            volume = int(volume_text)

        if not account_info:
            QtWidgets.QMessageBox.critical(self, "登录提示", "还未获取到账号信息，请登录账号")
            return

        vt_symbol = f"{symbol}.{self.exchange_combo.currentText()}"
        vt_symbol_contract = self.main_engine.get_contract(vt_symbol)
        if not vt_symbol_contract:
            QtWidgets.QMessageBox.critical(self, "输入错误", "请输入正确的合约代码和交易所代码")
            return

        direction = Direction(str(self.direction_combo.currentText()))
        if direction == Direction.LONG:
            win_price = price * (1 + 0.1)
            loss_price = price * (1 - 0.1)
        else:
            win_price = price * (1 - 0.1)
            loss_price = price * (1 + 0.1)

        order_ref = get_order_ref_value()
        gateway_name = str(self.gateway_combo.currentText())
        strategy_name = self.strategy_name_combo.currentText()

        if strategy_name:
            account = account_info.data
            order_data = OrderData(
                gateway_name=gateway_name,
                symbol=symbol,
                exchange=Exchange(str(self.exchange_combo.currentText())),

            )
            order_data.account_id = account.accountid
            order_data.balance = account.balance
            order_data.frozen = account.frozen
            order_data.direction = Direction(str(self.direction_combo.currentText()))
            order_data.type = OrderType(str(self.orderType_combo.currentText()))
            order_data.traded = volume
            order_data.volume = volume
            order_data.price = price
            order_data.offset = Offset(str(self.offset_combo.currentText()))
            order_data.order_time = self.datetime_edit.text()
            order_data.time = self.datetime_edit.text()
            tmp = strategy_name.split('-')
            order_data.strategy_name = tmp[0]
            order_data.strategy_class_name = tmp[1]
            order_data.strategy_author = 'manual'
            order_data.run_type = 'undersell'
            order_data.order_ref = order_ref
            order_data.status = Status.ALLTRADED
            order_data.order_local_id = str(random.randrange(10000, 999999, 6)).ljust(6, '0')
            order_data.order_sys_id = str(random.randrange(10000, 999999, 6)).ljust(6, '0')
            OrderModel = OrderDataModel()

            ses = self.main_engine.get_gateway(gateway_name).getSesionFrontid()
            orderid = ses + "_" + str(order_ref)
            order_data.orderid = orderid

            # 保存委托单和成交单
            id_ret = OrderModel.save_order_data(order_data=order_data)
            if id_ret:
                id_ret_trade = self.manualPositionAdjustment_engine.save_trade_data(order_data, win_price, loss_price)
                if id_ret_trade:
                    QtWidgets.QMessageBox.information(self, "成功", "委托单和成交单添加成功")
                else:
                    OrderModel.get(order_ref=order_ref).delete_instance()
                    QtWidgets.QMessageBox.critical(self, "失败", "委托单和成交单添加失败")
            else:
                QtWidgets.QMessageBox.critical(self, "失败", "委托单和成交单添加失败")
                return

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

    # def timer_test(self, event: Event):
    #     time.sleep(4)
    #     print(f"haha:{datetime.now()}")

    def load_strategy_setting(self):
        """
        Load setting file.
        """
        cta_strategy_setting_dict = load_json(CTA_STRATEGY_SETTING_FILENAME)
        strategy_class_list = []

        for strategy_name, row in cta_strategy_setting_dict.items():
            strategy_class_list.append(f"{strategy_name}-{row['class_name']}")

        return strategy_class_list

    def init_strategy_settings(self):
        """"""
        self.class_names = self.manualPositionAdjustment_engine.get_strategy_class_names()
        for class_name in self.class_names:
            setting = self.manualPositionAdjustment_engine.get_default_setting(class_name)
            self.settings[class_name] = setting
