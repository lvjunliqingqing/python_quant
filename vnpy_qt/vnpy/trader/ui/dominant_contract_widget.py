import re
from datetime import datetime
from datetime import timedelta
from typing import Any, Dict

from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QPushButton, QMessageBox
from pandas import to_pickle

from vnpy.controller.global_variable import get_value
from vnpy.event import Event, EventEngine
from vnpy.model.db_bar_model import DbBarModel
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Exchange, Product
from vnpy.trader.event import EVENT_DOMINANT_CONTRACT_TRADE, EVENT_DELETEID
from vnpy.trader.object import (
    OrderData
)
from .widget import OrderMonitor, BaseCell, EnumCell, DirectionCell
from ..constant import Direction, Offset
from ..engine import MainEngine
from ..utility import get_letter_from_symbol
from ..utility import save_json
from ...controller.trade_operation import get_order_ref_value
from ...model.securities_info import SecuritiesInfoModel


class DominantContractTradingWidget(QtWidgets.QWidget):
    """
    主力合约成交部件
    """
    main_contract_code_filename = "main_contract_code.json"

    signal_order: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cancel: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.dominant_contract_trade_dict = {}
        self.list_main_contract = []
        self.account_id = ""

        self.init_ui()
        self.register_event()
        self.get_dominant_contract()

    def init_ui(self) -> None:
        """"""

        symbol_label = LabelDialog()
        symbol_label.setText("品种(点击可选) ：")
        symbol_label.clicked.connect(self.show_main_contract)
        self.symbol_line = QtWidgets.QLineEdit()  # 品种输入框
        self.symbol_line.returnPressed.connect(self.set_vt_symbol)

        # 整数校验器
        int_validator = QtGui.QIntValidator(self)
        int_validator.setBottom(0)

        volume_label = QtWidgets.QLabel()
        volume_label.setText("手数(手动输入)：")
        self.volume_line = QtWidgets.QLineEdit()  # 手数输入框
        self.volume_line.setValidator(int_validator)

        intervention_label = QtWidgets.QLabel()
        intervention_label.setText("入场方式：")

        self.intervention_method = QtWidgets.QComboBox()  # 入场方式输入框
        self.intervention_method.addItems(["现价", "前一日最高价", "前一日最低价", "前两日最高价", "前两日最低价"])
        self.intervention_method.currentIndexChanged.connect(self.selection_change)

        # 止损
        self.loss_label = LabelDialog()
        self.loss_label.setText("止损方式(选择其一)：")
        self.loss_label.clicked.connect(self.show_loss_dialog)
        self.loss_line_edit = QtWidgets.QLineEdit()  # 止损输入框
        self.loss_line_edit.setEnabled(False)

        # 止盈
        self.win_label = LabelDialog()
        self.win_label.setText("止盈方式(选择其一)：")
        self.win_label.clicked.connect(self.show_win_dialog)
        self.win_line_edit = QtWidgets.QLineEdit()  # 止盈输入框
        self.win_line_edit.setEnabled(False)

        gateway_label = QtWidgets.QLabel()
        gateway_label.setText("接口(请选择)：")
        self.gateway_combo = QtWidgets.QComboBox()
        self.gateway_combo.addItems(self.main_engine.get_all_gateway_names())

        self.long_button = QtWidgets.QPushButton("买多")
        self.long_button.setObjectName("买多")
        self.long_button.clicked.connect(self.long_short)

        self.short_button = QtWidgets.QPushButton("卖空")
        self.short_button.setObjectName("卖空")
        self.short_button.clicked.connect(self.long_short)

        cancel_button = QtWidgets.QPushButton("全撤单")
        cancel_button.clicked.connect(self.cancel_all)

        grid = QtWidgets.QGridLayout()
        # addWidget(Widget部件对象,第几行,第几列,占用多少行,占用多少列)
        grid.addWidget(symbol_label, 0, 0, 1, 1)
        grid.addWidget(self.symbol_line, 0, 1, 1, 2)

        grid.addWidget(volume_label, 1, 0, 1, 1)
        grid.addWidget(self.volume_line, 1, 1, 1, 2)

        grid.addWidget(intervention_label, 2, 0, 1, 1)
        grid.addWidget(self.intervention_method, 2, 1, 1, 2)

        grid.addWidget(self.loss_label, 3, 0, 1, 1)
        grid.addWidget(self.loss_line_edit, 3, 1, 1, 2)

        grid.addWidget(self.win_label, 4, 0, 1, 1)
        grid.addWidget(self.win_line_edit, 4, 1, 1, 2)

        grid.addWidget(gateway_label, 5, 0, 1, 1)
        grid.addWidget(self.gateway_combo, 5, 1, 1, 2)

        grid.addWidget(self.long_button, 6, 0, 1, 1)
        grid.addWidget(self.short_button, 6, 1, 1, 1)
        grid.addWidget(cancel_button, 6, 2, 1, 1)

        self.main_contract_trade_order_monitor = MainContractTradeOrderMonitor(self.main_engine, self.event_engine)

        # 总布置
        h_box = QtWidgets.QHBoxLayout()
        h_box.addLayout(grid, stretch=1)
        h_box.addWidget(self.main_contract_trade_order_monitor, stretch=6)
        self.setLayout(h_box)

    def get_dominant_contract(self) -> None:
        """获取主力合约数据"""
        self.list_main_contract = SecuritiesInfoModel().get_main_contract_code(self.main_contract_code_filename)
        self.list_main_contract.sort()

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_DOMINANT_CONTRACT_TRADE, self.dominant_contract_trade_event)
        self.event_engine.register(EVENT_DELETEID, self.cancel_order_event)

    def dominant_contract_trade_event(self, event: Event) -> None:
        """主力合约成交事件处理"""
        order_information = event.data
        gateway_name = str(self.gateway_combo.currentText())
        ses = self.main_engine.get_gateway(gateway_name).getSesionFrontid()
        orderid = ses + "_" + str(order_information['order_ref'])

        self.dominant_contract_trade_dict[orderid] = order_information
        dt = datetime.utcfromtimestamp(int(order_information['order_ref']) / 100) + timedelta(hours=8)

        # 创建监测委托单
        insert_data = OrderData(orderid=orderid,
                                symbol=order_information['vt_symbol'].split('.')[0],
                                exchange=Exchange(order_information['vt_symbol'].split('.')[1]),
                                direction=Direction.LONG if order_information['direction'] == "LONG" else Direction.SHORT,
                                offset=Offset.OPEN,
                                price=order_information['open_style']['value'],
                                volume=order_information['volume']['value'],
                                status_msg="监测中",
                                time=dt.strftime("%H:%M:%S"),
                                gateway_name="CTP",
                                )
        insert_data.win_price = order_information['win_style']['value']
        insert_data.loss_price = order_information['loss_style']['value']

        self.main_contract_trade_order_monitor.add_new_row(insert_data)  # 委托信息添加到表格上

        self.main_engine.get_engine("PortfolioStrategy").on_open_builtin({order_information['order_ref']: order_information})  # 组合策略的内嵌策略的开仓挂单
        self.account_id = order_information.get("account_id", self.account_id)
        save_json("{}_dominant_contract_trade.json".format(self.account_id), self.dominant_contract_trade_dict)

    def cancel_order_event(self, event: Event) -> None:
        """撤销委托单记录,并在json文件中删除对应的委托单数据"""
        dominant_contract_trade_data = event.data
        # 删除对应的dominant_contract_trade_data数据,并重新保存json文件
        self.dominant_contract_trade_dict.pop(dominant_contract_trade_data)
        save_json(f"{self.account_id}_dominant_contract_trade.json", self.dominant_contract_trade_dict)

    def set_vt_symbol(self) -> None:
        symbol = str(self.symbol_line.text())
        if not symbol:
            return

        all_contracts = self.main_engine.get_all_contracts()

        if symbol:
            letter = get_letter_from_symbol(symbol)

            contracts = [contract for contract in all_contracts if re.findall(symbol, contract.vt_symbol, flags=re.IGNORECASE)]  # IGNORECASE:忽略大小写
            # CZCE的情况
            contracts.extend([contract for contract in all_contracts if symbol.replace("2", "", 1).upper() in contract.vt_symbol])

            if contracts:
                for contract in contracts:
                    if contract.product == Product.FUTURES and letter == get_letter_from_symbol(contract.symbol):  # 判断是否是期货
                        symbol = contract.symbol
                        exchange = contract.exchange.value
                        self.symbol_line.setText(symbol + '.' + exchange)
            else:
                message_box = self.get_message_box(title="选择失败", text="查询此合约失败(未登陆或合约不存在)")
                message_box.exec()

                self.symbol_line.setText("")

    def selection_change(self):
        text = self.intervention_method.currentText()
        if "最高价" in text:
            self.long_button.setEnabled(True)
            self.short_button.setEnabled(False)
        elif "最低价" in text:
            self.long_button.setEnabled(False)
            self.short_button.setEnabled(True)
        else:
            self.long_button.setEnabled(True)
            self.short_button.setEnabled(True)

    def show_main_contract(self):
        # 如果用show()：显示一个非模式对话框。控制权即刻返回给调用函数。创建部件对象时,必须以self.对象名 命名；命名不带self则Dialog部件无法显示出来。
        select_symbol = MainContractDialog(self, self.list_main_contract)
        # 加上这句，则可以实现子窗口不关闭无法操作父窗口
        select_symbol.setWindowModality(Qt.ApplicationModal)
        select_symbol.exec()

    def show_loss_dialog(self):
        loss_dialog = LossDialog(self)
        loss_dialog.setWindowModality(Qt.ApplicationModal)
        loss_dialog.exec()

    def show_win_dialog(self):
        win_dialog = WinDialog(self)
        win_dialog.setWindowModality(Qt.ApplicationModal)
        win_dialog.exec()

    def form_validator(self):
        """form表格校验器"""
        text = ""

        if not self.symbol_line.text():
            text = "请输入合约代码"
        elif not self.volume_line.text():
            text = "请输入委托数量"
        elif not self.loss_line_edit.text():
            text = "请输入止损方式"
        elif not self.win_line_edit.text():
            text = "请输入止盈方式"

        if text:
            message_box = self.get_message_box(y_offset=188, text=text)
            message_box.exec()
            return True

    def is_login(self):
        """检验是否已经登录"""
        account_info = get_value("account_info")
        if not account_info:
            message_box = self.get_message_box(y_offset=140, text="还未获取到账号信息")
            message_box.exec()
            return True
        else:
            self.account_id = account_info.data.accountid

    def get_contract_price(self):
        """获取symbol对应的price数据"""
        bar_data = (
            DbBarModel.select().where(
                (DbBarModel.symbol == self.symbol_line.text().split('.')[0])
                & (DbBarModel.interval == "d")
            ).order_by(DbBarModel.datetime.desc()).limit(2)
        )

        if len(bar_data) < 2:
            text = f"读取 {self.symbol_line.text()} 数据失败"
            message_box = self.get_message_box(y_offset=140, text=text)
            message_box.exec()
            return []
        else:
            yesterday_high = bar_data[0].high_price  # 昨天的最高价
            yesterday_low = bar_data[0].low_price   # 昨天的最低价
            pre_two_days_high = max(bar_data[1].high_price, bar_data[0].high_price)  # 前两天的最高价
            pre_two_days_low = min(bar_data[1].low_price, bar_data[0].low_price)  # 前二天的最低价
            return [pre_two_days_high, pre_two_days_low, yesterday_high, yesterday_low]

    def long_short(self) -> None:
        """买多/卖空 按钮的点击事件"""
        if self.form_validator() or self.is_login():  # 先校验
            return

        price_data = self.get_contract_price()
        if not price_data:
            return

        pre_two_days_high, pre_two_days_low, yesterday_high, yesterday_low = price_data

        information = ""
        information_dict = {}
        # 获取合约号
        vt_symbol = self.symbol_line.text()
        information += f"合约代码：{vt_symbol}\n"
        information_dict['vt_symbol'] = vt_symbol

        # 获取开仓数量
        volume = float(self.volume_line.text())
        if volume >= 1:
            information += f"开仓手数：{volume}\n"
            information_dict['volume'] = {"name": "number", "value": volume}
        else:
            information += f"止损比例：{volume}\n"
            information_dict['volume'] = {"name": "percentage", "value": volume}

        # 获取开仓价
        open_style = self.intervention_method.currentText()
        if open_style == "现价":
            information += f"介入方式：{open_style}\n"
            information_dict['open_style'] = {"name": "market_price", "value": 0}
        elif open_style == "前一日最高价":
            information += f"介入方式：{yesterday_high}\n"
            information_dict['open_style'] = {"name": "limit_price", "value": yesterday_high}
        elif open_style == "前一日最低价":
            information += f"介入方式：{yesterday_low}\n"
            information_dict['open_style'] = {"name": "limit_price", "value": yesterday_low}
        elif open_style == "前两日最高价":
            information += f"介入方式：{pre_two_days_high}\n"
            information_dict['open_style'] = {"name": "limit_price", "value": pre_two_days_high}
        elif open_style == "前两日最低价":
            information += f"介入方式：{pre_two_days_low}\n"
            information_dict['open_style'] = {"name": "limit_price", "value": pre_two_days_low}

        # 止损价
        loss_style = self.loss_line_edit.text()
        if loss_style == "前一日最高价":
            information += f"止损价格：{yesterday_high}\n"
            information_dict['loss_style'] = {"name": "loss_price", "value": yesterday_high}
        elif loss_style == "前一日最低价":
            information += f"止损价格：{yesterday_low}\n"
            information_dict['loss_style'] = {"name": "loss_price", "value": yesterday_low}
        elif loss_style == "前两日最高价":
            information += f"止损价格：{pre_two_days_high}\n"
            information_dict['loss_style'] = {"name": "loss_price", "value": pre_two_days_high}
        elif loss_style == "前两日最低价":
            information += f"止损价格：{pre_two_days_low}\n"
            information_dict['loss_style'] = {"name": "loss_price", "value": pre_two_days_low}
        else:
            information += f"止损价格：{loss_style}\n"
            information_dict['loss_style'] = {"name": "loss_price", "value": float(loss_style)}

        # 止盈方式
        win_style = self.win_line_edit.text()
        if "倍数" in win_style:
            information += f"止盈价格：{win_style}\n"
            information_dict['win_style'] = {"name": "multiple", "value": float(win_style.split("(")[0])}
        elif "跟踪" in win_style:
            information += f"止盈价格：{win_style}\n"
            information_dict['win_style'] = {"name": "follow_multiple", "value": float(win_style.split("(")[0])}
        else:
            information += f"止盈价格：{win_style}\n"
            information_dict['win_style'] = {"name": "win_price", "value": float(win_style)}

        # 显示信息操作
        sender_name = self.sender().objectName()

        message_box = self.get_message_box(title=sender_name, icon=QMessageBox.Information, y_offset=250, text=information)
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        message_box.button(QMessageBox.Yes).setText('确定')
        message_box.button(QMessageBox.Cancel).setText('取消')

        if message_box.exec() == QMessageBox.Yes:
            if sender_name == "买多":
                information_dict['direction'] = 'LONG'
            elif sender_name == "卖空":
                information_dict['direction'] = 'SHORT'

            information_dict['order_ref'] = get_order_ref_value()  # 生成order_ref
            # 添加记录
            self.dominant_contract_trade_event(Event(EVENT_DOMINANT_CONTRACT_TRADE, information_dict))

    def cancel_all(self) -> None:
        """全部撤单"""

        if self.is_login():
            return

        # 信息提示框
        message_box = self.get_message_box(title="全撤单", icon=QMessageBox.Warning, y_offset=140, text="是否进行全撤单操作")
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        message_box.button(QMessageBox.Yes).setText('确定')
        message_box.button(QMessageBox.Cancel).setText('取消')

        if message_box.exec() == QMessageBox.Yes:
            for orderid in self.dominant_contract_trade_dict.keys():
                insert_data = OrderData(orderid=orderid,
                                        symbol='',
                                        exchange=Exchange("CFFEX"),
                                        gateway_name="CTP",
                                        )
                self.main_contract_trade_order_monitor.remove_old_row(insert_data)  # 删除表格数据

            dominant_contract_trade = get_value('dominant_contract_trade')
            for value in set(self.dominant_contract_trade_dict.keys()).union(dominant_contract_trade.values()):
                self.main_engine.get_engine("PortfolioStrategy").on_cancel_builtin(value)  # 内嵌策略撤单操作
            # 删除数据,并保存到json文件
            self.dominant_contract_trade_dict = {}
            save_json(f"{self.account_id}_dominant_contract_trade.json", self.dominant_contract_trade_dict)

    def get_message_box(self, title="委托失败", icon=QMessageBox.Critical, y_offset: int = 0, text: str = ""):
        """返回消息框对象"""
        message_box = QMessageBox()
        message_box.setIcon(icon)
        message_box.setWindowTitle(title)

        if y_offset:
            pos = QCursor.pos()
            pos.setY(pos.y() - y_offset)
            message_box.move(pos)
        else:
            message_box.move(QCursor.pos())

        if text:
            message_box.setText(text)

        return message_box


class LabelDialog(QtWidgets.QLabel):

    clicked = QtCore.pyqtSignal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class MainContractTradeOrderMonitor(OrderMonitor):
    """主合约成交监控部件"""

    data_key = "orderid"
    headers: Dict[str, dict] = {
        "orderid": {"display": "委托号", "cell": BaseCell, "update": True},
        "symbol": {"display": "代码", "cell": BaseCell, "update": True},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": True},
        "type": {"display": "类型", "cell": EnumCell, "update": True},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": True},
        "loss_price": {"display": "止损价", "cell": BaseCell, "update": False},
        "win_price": {"display": "止盈价", "cell": BaseCell, "update": False},
        "volume": {"display": "总数量", "cell": BaseCell, "update": True},
        "traded": {"display": "已成交", "cell": BaseCell, "update": True},
        "status": {"display": "状态", "cell": EnumCell, "update": True},
        "time": {"display": "时间", "cell": BaseCell, "update": True},
        "status_msg": {"display": "状态信息", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    def init_ui(self):
        super(MainContractTradeOrderMonitor, self).init_ui()

        self.ctp_gateway = self.main_engine.get_gateway('CTP')

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.init_dominant_contract_trade_menu)

        self.setToolTip("右键撤单")

    def init_dominant_contract_trade_menu(self, pos) -> None:
        """初始化主力合约交易部件(MainContractTradeOrderMonitor)的上下文菜单"""
        # 获取委托单位置
        row_num = self.rowCount()
        for i in self.selectionModel().selection().indexes():
            row_num = i.row()

        self.extend_menu = QtWidgets.QMenu()
        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.extend_menu.addAction(resize_action)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.extend_menu.addAction(save_action)

        if row_num < self.rowCount():
            cancel_operation = QtWidgets.QAction("撤单操作", self)
            order_id = self.item(row_num, list(self.headers.keys()).index(self.data_key)).text()
            cancel_operation.triggered.connect(lambda: self.cancel_dominant_contract_order(order_id))
            self.extend_menu.addAction(cancel_operation)

        self.extend_menu.exec_(self.mapToGlobal(pos))

    def cancel_dominant_contract_order(self, order_id) -> None:
        self.dominant_contract_trade = get_value('dominant_contract_trade')
        if order_id in self.dominant_contract_trade.keys():  # dominant_contract_trade:主力合约交易委托字典
            order_id = self.dominant_contract_trade[order_id]
            self.main_engine.get_engine("PortfolioStrategy").on_cancel_builtin(order_id)  # 内嵌策略撤单操作
        else:
            # 删除表格行数据
            insert_data = OrderData(orderid=order_id, symbol='', exchange=Exchange("CFFEX"), gateway_name="CTP")
            self.remove_old_row(insert_data)

            self.event_engine.put(Event(type=EVENT_DELETEID, data=order_id))  # 推送撤销主合约交易委托单事件
            self.main_engine.get_engine("PortfolioStrategy").on_cancel_builtin(order_id)  # 内嵌策略撤单操作

    def process_event(self, event: Event) -> None:
        """
        Process new data from event and update into table.
        """
        """订单更新操作"""
        order_data = event.data
        self.dominant_contract_trade = get_value('dominant_contract_trade')  # 读取全局变量中dominant_contract_trade键对应的值
        # 判断是否已经触发开仓操作
        if order_data.orderid in self.dominant_contract_trade.keys():
            account_id = self.ctp_gateway.td_api.userid
            to_pickle(self.dominant_contract_trade, f"{account_id}_dominant_contract_trade.pkl")  # 保存为pickle文件
            if self.sorting:
                self.setSortingEnabled(False)
            self.update_old_row(event.data)
            if self.sorting:
                self.setSortingEnabled(True)

    def add_new_row(self, data: Any):
        """插入一条新委托记录(监控)"""
        # Disable sorting to prevent unwanted error.
        if self.sorting:
            self.setSortingEnabled(False)
        self.insert_new_row(data)
        # Enable sorting
        if self.sorting:
            self.setSortingEnabled(True)

    def update_old_row(self, data: Any) -> None:
        """
        Update an old row in table.
        """
        key = data.__getattribute__(self.data_key)

        if key in self.cells:
            row_cells = self.cells[key]
        else:
            order_id = self.dominant_contract_trade[key]
            if order_id not in self.cells:
                # 查询止盈止损价
                trade_data_list = TradeDataModel().select().where(
                    (TradeDataModel.orderid == key))
                if len(trade_data_list) > 0:
                    data.win_price = trade_data_list[0].win_price
                    data.loss_price = trade_data_list[0].loss_price
                else:
                    data.win_price = 0
                    data.loss_price = 0
                self.insert_new_row(data)
                return
            else:
                self.event_engine.put(Event(type=EVENT_DELETEID, data=id))  # 同步更新操作
                self.cells[key] = self.cells[order_id]
                self.cells.pop(order_id)
                row_cells = self.cells[key]

        for header, cell in row_cells.items():
            content = data.__getattribute__(header)
            cell.set_content(content, data)


class MainContractDialog(QtWidgets.QDialog):
    """品种的弹出框"""

    def __init__(self, widget, list_main_contract):
        super().__init__()
        self.widget = widget
        self.list_main_contract = list_main_contract
        self.init_ui()

    def init_ui(self):
        # self.setWindowFlags(Qt.FramelessWindowHint) # 设置无边框
        self.setWindowTitle("主力合约品种选择")
        grid = QtWidgets.QGridLayout()
        x = 0
        y = 0
        for main_contract in self.list_main_contract:
            btn = QPushButton(main_contract)
            btn.clicked.connect(self.selection)
            grid.addWidget(btn, y, x)
            x += 1
            if x > 8:
                y += 1
                x = 0
        self.setLayout(grid)
        self.move(QCursor.pos())

    def selection(self):
        self.widget.symbol_line.setText(self.sender().text())
        self.widget.set_vt_symbol()
        self.close()


class LossDialog(QtWidgets.QDialog):
    """止损的弹出框"""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        vbox = QtWidgets.QVBoxLayout()

        for text in ["前一日最高价", "前一日最低价", "前两日最高价", "前两日最低价"]:
            btn = QPushButton(text)
            btn.clicked.connect(self.selection)
            vbox.addWidget(btn)

        self.setLayout(vbox)
        self.move(QCursor.pos())

    def selection(self):
        self.widget.loss_line_edit.setText(self.sender().text())
        self.close()


class WinDialog(QtWidgets.QDialog):
    """止盈的弹出框"""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)

        double_validator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)

        form = QtWidgets.QFormLayout()
        for text in ["倍数止盈", "跟踪止盈", "自定价格"]:
            price_line = QtWidgets.QLineEdit()  # 止盈输入框对象
            price_line.setObjectName(text)
            price_line.setValidator(double_validator)
            price_line.returnPressed.connect(self.selection)
            form.addRow(text, price_line)

        self.setLayout(form)
        self.move(QCursor.pos())

    def selection(self):
        object_name = self.sender().objectName()
        if object_name == "倍数止盈":
            self.widget.win_line_edit.setText(self.sender().text() + "(倍数)")
        elif object_name == "跟踪止盈":
            self.widget.win_line_edit.setText(self.sender().text() + "(跟踪)")
        else:
            self.widget.win_line_edit.setText(self.sender().text())
        self.close()
