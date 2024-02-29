"""
Basic widgets for VN Trader.
"""
import re
import csv
import platform
from copy import copy
from datetime import datetime
from enum import Enum
from typing import Any, Dict

import numpy as np
import rqdatac
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QMessageBox
from pandas import to_pickle, to_datetime
from tzlocal import get_localzone

import vnpy
from vnpy.controller.trade_operation import get_order_ref_value
from vnpy.event import Event, EventEngine
from vnpy.model.order_data_model import OrderDataModel
from vnpy.trader.constant import Exchange, Product
from vnpy.trader.event import EVENT_PORTFOLIO_LOG, EVENT_WINRATE, EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, EVENT_FORCED_LIQUIDATION, EVENT_STRATEGY_CLOSE_POSITION
from vnpy.trader.object import (
    OrderData
)
from vnpy.trader.object import TradeRecordData
from vnpy.trader.symbol_attr import ContractMultiplier
from vnpy.trader.ui.candle_widget import show_candle_chart
from .quick_liquidation_component_widget import QuickLiquidationComponentWidget
from ..constant import Direction, Offset, OrderType
from ..engine import MainEngine
from ..event import (
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_LOG, EVENT_CTA_LOG,
    EVENT_STRATEGY_HOLD_POSITION
)
from ..object import OrderRequest, SubscribeRequest, PositionData, TickData
from ..setting import CTA_STRATEGY_SETTING_FILENAME
from ..setting import SETTING_FILENAME, SETTINGS
from ..utility import get_letter_from_symbol
from ..utility import load_json, save_json, get_digits
from ...controller.global_variable import set_value, get_value

COLOR_LONG = QtGui.QColor("red")
COLOR_SHORT = QtGui.QColor("green")
COLOR_BID = QtGui.QColor(255, 174, 201)
COLOR_ASK = QtGui.QColor(160, 255, 160)
COLOR_BLACK = QtGui.QColor("black")


class BaseCell(QtWidgets.QTableWidgetItem):
    """
    General cell used in tableWidgets
    """
    _data = None

    def __init__(self, content: Any, data: Any):
        """"""
        super(BaseCell, self).__init__()
        self.setTextAlignment(QtCore.Qt.AlignCenter)
        self.set_content(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Set text content.
        """
        self.setText(str(content))
        self._data = data

    def get_data(self) -> Any:
        """
        Get data object.
        """
        return self._data


class EnumCell(BaseCell):
    """
    Cell used for showing enum data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(EnumCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Set text using enum.constant.value.
        """
        if content:
            super(EnumCell, self).set_content(content.value, data)


class DirectionCell(EnumCell):
    """
    Cell used for showing direction data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(DirectionCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Cell color is set according to direction.
        """
        super(DirectionCell, self).set_content(content, data)

        if content is Direction.SHORT:
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class BidCell(BaseCell):
    """
    Cell used for showing bid price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(BidCell, self).__init__(content, data)

        self.setForeground(COLOR_BID)


class AskCell(BaseCell):
    """
    Cell used for showing ask price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(AskCell, self).__init__(content, data)

        self.setForeground(COLOR_ASK)


class PnlCell(BaseCell):
    """
    Cell used for showing pnl data.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(PnlCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Cell color is set based on whether pnl is
        positive or negative.
        """
        super(PnlCell, self).set_content(content, data)

        if str(content).startswith("-"):
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class TimeCell(BaseCell):
    """
    Cell used for showing time string from datetime object.
    """

    local_tz = get_localzone()

    def __init__(self, content: Any, data: Any):
        """"""
        super(TimeCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """"""
        if content is None:
            return

        content = content.astimezone(self.local_tz)
        timestamp = content.strftime("%H:%M:%S")

        millisecond = int(content.microsecond / 1000)
        if millisecond:
            timestamp = f"{timestamp}.{millisecond}"

        self.setText(timestamp)
        self._data = data


class MsgCell(BaseCell):
    """
    Cell used for showing msg data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(MsgCell, self).__init__(content, data)
        self.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)


class BaseMonitor(QtWidgets.QTableWidget):
    """
    Monitor data update in VN Trader.
    """

    event_type: str = ""
    data_key: str = ""
    sorting: bool = False
    headers: Dict[str, dict] = {}

    signal: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(BaseMonitor, self).__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.cells: Dict[str, dict] = {}  # {data(数据对象)属性值:{表格header:cell对象}}

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """"""
        self.init_table()
        self.init_menu()

    def init_table(self) -> None:
        """
        Initialize table.
        """
        self.setColumnCount(len(self.headers))

        labels = [d["display"] for d in self.headers.values()]
        self.setHorizontalHeaderLabels(labels)
        # 设置显示垂直表头
        if self.event_type not in [EVENT_STRATEGY_CLOSE_POSITION, EVENT_STRATEGY_HOLD_POSITION, EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, EVENT_FORCED_LIQUIDATION]:
            self.verticalHeader().setVisible(True)
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(self.sorting)

    def init_menu(self) -> None:
        """
        Create right click menu.
        """
        self.menu = QtWidgets.QMenu(self)

        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.menu.addAction(resize_action)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

        if self.event_type in [EVENT_STRATEGY_CLOSE_POSITION, EVENT_STRATEGY_HOLD_POSITION]:
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # 设置策略持仓和策略平仓的上下文菜单(因为它的上下文菜单跟别的组件有点区别的，所有要特别设置下)
            self.customContextMenuRequested.connect(self.init_strategy_open_close_context_menu)

        if self.event_type in [EVENT_FORCED_LIQUIDATION]:  # 设置强制平仓上下文菜单,增加全选和全撤消选项。
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.init_forced_liquidation_context_menu)

    def init_strategy_open_close_context_menu(self, pos) -> None:
        """
        初始化策略开仓和平仓组件的上下文菜单,给它在通用组件的上下文件基础上增加显示k线图的菜单。0.
        """
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
            candle_chart = QtWidgets.QAction("K线图表", self)
            candle_headers = self.headers.copy()
            for column_num, key in enumerate(candle_headers.keys()):
                candle_headers[key]['value'] = self.item(row_num, column_num).text()  # 将用户在策略持仓或策略平仓组件中右击选中的那条交易数据封装到headers中去

            candle_chart.triggered.connect(lambda: show_candle_chart(self.main_engine, self.event_engine, candle_headers))
            self.extend_menu.addAction(candle_chart)
        self.extend_menu.exec_(self.mapToGlobal(pos))

    def init_forced_liquidation_context_menu(self, pos) -> None:
        """
        初始化强制平仓组件的上下文菜单,给增加全选和全撤销的子菜单。
        """
        self.extend_menu = QtWidgets.QMenu()
        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.extend_menu.addAction(resize_action)

        select_all = QtWidgets.QAction("全部选择", self)
        select_all.triggered.connect(lambda: self.set_check(True))
        self.extend_menu.addAction(select_all)

        cancel_all = QtWidgets.QAction("撤消选择", self)
        cancel_all.triggered.connect(lambda: self.set_check(False))
        self.extend_menu.addAction(cancel_all)
        
        self.extend_menu.exec_(self.mapToGlobal(pos))

    def set_check(self, check: bool):
        for row in range(self.rowCount()):
            item = self.item(row, self.columnCount() - 1)
            if check:
                item.setCheckState(Qt.Checked)  # 设置选中
            else:
                item.setCheckState(Qt.Unchecked)  # 设置成未选中

    def register_event(self) -> None:
        """
        Register event handler into event engine.
        """
        if self.event_type:
            self.signal.connect(self.process_event)
            self.event_engine.register(self.event_type, self.signal.emit)

    def process_event(self, event: Event) -> None:
        """
        Process new data from event and update into table.
        """

        if event.type == EVENT_ACCOUNT:
            """账户资金情况操作"""
            set_value("account_info", event)
            account_data = event.data
            oms = self.main_engine.get_engine('oms')
            margin_loss_list = oms.get_account_margin_loss(account_data.accountid)
            # 总保证金
            account_data.cum_margin = margin_loss_list[0]
            # 最大风险(最大亏损)
            account_data.cum_loss = margin_loss_list[1]
            if account_data.balance > 0:
                # 计算最大风险比率
                account_data.cum_loss_ratio = str(round(margin_loss_list[1] * 100 / account_data.balance, 2)) + "%"
                # 所有品种的最大亏损总和比率(= 最大亏损总和 / 总资金)
                oms.sum_max_loss_ratio = round(margin_loss_list[1] / account_data.balance, 2)
            else:
                account_data.cum_loss_ratio = 0
                oms.sum_max_loss_ratio = 0

        elif event.type == EVENT_ORDER:
            """订单更新操作"""
            if get_value("account_info"):
                account = get_value("account_info").data
                order_data = event.data
                order_data.frozen = account.frozen
                order_data.balance = account.balance
                # if OrderDataModel().update_order_status(order_data=order_data): # zhou
                #     print('ok')

        elif event.type == EVENT_TRADE:
            """成功交易信息"""
            trade_data = event.data
            if get_value("account_info"):
                account = get_value("account_info").data
                trade_data.frozen = account.frozen
                trade_data.balance = account.balance
                # if trade_data.offset.name == 'OPEN':
                #     TradeDataModel().save_widget_event_trade_data(trade_data=trade_data) # zhou

        elif event.type == EVENT_POSITION:
            """更改持仓均值,计算盈亏"""
            position_data = event.data
            vt_symbol = position_data.vt_symbol
            old_price = position_data.price
            old_pnl = position_data.pnl
            oms = self.main_engine.get_engine('oms')
            contract = oms.get_contract(vt_symbol)
            if contract:
                the_contract_multiplier = contract.size
            else:
                the_contract_multiplier = ContractMultiplier.get(get_letter_from_symbol(position_data.symbol), None)
            if the_contract_multiplier:
                price = oms.get_symbol_ma_price(position_data.symbol)  # 获取持仓均值
                position_data.price = price if price else old_price
                if position_data.direction == Direction.LONG:
                    position_data.pnl = round(old_pnl + (old_price - position_data.price) * position_data.volume * the_contract_multiplier, 2)
                else:
                    position_data.pnl = round(old_pnl + (old_price - position_data.price) * position_data.volume * the_contract_multiplier * (-1), 2)
                self.main_engine.subscribe(SubscribeRequest(position_data.symbol, position_data.exchange), 'CTP')

        elif event.type in [EVENT_STRATEGY_HOLD_POSITION, EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, EVENT_FORCED_LIQUIDATION]:
            if event.data.volume == 0:
                data = event.data
                self.remove_old_row(data)
                self.setSortingEnabled(True)
                # 因为删除volume为0的旧行时、不需要执行后面更新旧行、插入新行,所以执行return结束程序。
                return

        elif event.type in [EVENT_CTA_LOG, EVENT_PORTFOLIO_LOG]:
            if hasattr(self, "log_data_list"):
                self.log_data_list.append(event)  # 记录日志
                account_id = self.main_engine.get_gateway('CTP').td_api.userid
                if account_id:
                    to_pickle(self.log_data_list, f"{account_id}.pkl")

        # Disable sorting to prevent unwanted error.
        # if self.sorting:
        #     self.setSortingEnabled(False)

        # Update data into table.
        data = event.data

        if not self.data_key:
            self.insert_new_row(data)
        else:
            key = data.__getattribute__(self.data_key)

            if key in self.cells:
                self.update_old_row(data)
            else:
                self.insert_new_row(data)

        # Enable sorting
        if self.sorting:
            self.setSortingEnabled(True)

    def insert_new_row(self, data: Any):
        """
        Insert a new row at the top of table.
        """
        self.insertRow(0)

        row_cells = {}
        for column, header in enumerate(self.headers.keys()):
            setting = self.headers[header]

            content = data.__getattribute__(header)
            cell = setting["cell"](content, data)
            self.setItem(0, column, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells

    def remove_old_row(self, data: Any) -> None:
        """
        remove a old row at the top of table.
        """
        key = data.__getattribute__(self.data_key)
        for row in range(self.rowCount()):
            if self.item(row, list(self.headers.keys()).index(self.data_key)).text() == key:
                self.removeRow(row)
                self.cells.pop(key)
                break

    def update_old_row(self, data: Any) -> None:
        """
        Update an old row in table.
        """
        key = data.__getattribute__(self.data_key)
        row_cells = self.cells[key]

        for header, cell in row_cells.items():
            content = data.__getattribute__(header)
            cell.set_content(content, data)

    def resize_columns(self) -> None:
        """
        Resize all columns according to contents.
        """
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def save_csv(self) -> None:
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存数据", "", "CSV(*.csv)")
        if not path:
            return
        try:
            with open(path, "w") as f:
                writer = csv.writer(f, lineterminator="\n")

                column_name = []
                for i in self.headers.keys():
                    column_name.append(self.headers[i]["display"])
                writer.writerow(column_name)

                for row in range(self.rowCount()):
                    row_data = []
                    for column in range(self.columnCount()):
                        item = self.item(row, column)
                        if item:
                            row_data.append(str(item.text()))
                        else:
                            row_data.append("")
                    writer.writerow(row_data)
        except PermissionError:
            QtWidgets.QMessageBox.critical(self, "保存失败", "写入的文件被打开,请关闭文件后再操作")

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())


class TickMonitor(BaseMonitor):
    """
    Monitor for tick data.
    """

    event_type = EVENT_TICK
    data_key = "vt_symbol"
    sorting = True

    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "name": {"display": "名称", "cell": BaseCell, "update": True},
        "last_price": {"display": "最新价", "cell": BaseCell, "update": True},
        "volume": {"display": "成交量", "cell": BaseCell, "update": True},
        "open_price": {"display": "开盘价", "cell": BaseCell, "update": True},
        "high_price": {"display": "最高价", "cell": BaseCell, "update": True},
        "low_price": {"display": "最低价", "cell": BaseCell, "update": True},
        "bid_price_1": {"display": "买1价", "cell": BidCell, "update": True},
        "bid_volume_1": {"display": "买1量", "cell": BidCell, "update": True},
        "ask_price_1": {"display": "卖1价", "cell": AskCell, "update": True},
        "ask_volume_1": {"display": "卖1量", "cell": AskCell, "update": True},
        "datetime": {"display": "时间", "cell": TimeCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class LogMonitor(BaseMonitor):
    """
    Monitor for log data.
    """

    event_type = EVENT_LOG
    data_key = ""
    sorting = False

    headers = {
        "time": {"display": "时间", "cell": TimeCell, "update": False},
        "msg": {"display": "信息", "cell": MsgCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    def init_ui(self):
        super(LogMonitor, self).init_ui()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)


class StrategyLogMonitor(BaseMonitor):
    """
    Monitor for Strategy log data.
    """
    data_key = ""
    sorting = False
    log_data_list = []

    headers = {
        "time": {"display": "时间", "cell": TimeCell, "update": False},
        "msg": {"display": "信息", "cell": MsgCell, "update": False},
    }

    def register_event(self) -> None:
        """
        Register event handler into event engine.
        """
        self.signal.connect(self.process_event)
        self.event_engine.register(EVENT_CTA_LOG, self.signal.emit)
        self.event_engine.register(EVENT_PORTFOLIO_LOG, self.signal.emit)


class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """

    event_type = EVENT_TRADE
    data_key = ""
    sorting = True

    headers: Dict[str, dict] = {
        "tradeid": {"display": "成交号 ", "cell": BaseCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "datetime": {"display": "时间", "cell": TimeCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class OrderMonitor(BaseMonitor):
    """
    Monitor for order data.
    """

    event_type = EVENT_ORDER
    data_key = "vt_orderid"
    sorting = True

    headers: Dict[str, dict] = {
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "reference": {"display": "来源", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "type": {"display": "类型", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "总数量", "cell": BaseCell, "update": True},
        "traded": {"display": "已成交", "cell": BaseCell, "update": True},
        "status": {"display": "状态", "cell": EnumCell, "update": True},
        "datetime": {"display": "时间", "cell": TimeCell, "update": True},
        "status_msg": {"display": "状态信息", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    def init_ui(self):
        """
        Connect signal.
        """
        super(OrderMonitor, self).init_ui()

        self.setToolTip("双击单元格撤单")
        self.itemDoubleClicked.connect(self.cancel_order)

    def cancel_order(self, cell: BaseCell) -> None:
        """
        Cancel order if cell double clicked.
        """
        order = cell.get_data()
        req = order.create_cancel_request()
        self.main_engine.cancel_order(req, order.gateway_name)


class PositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """

    event_type = EVENT_POSITION
    data_key = "vt_positionid"
    sorting = True

    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": True},
        "yd_volume": {"display": "昨仓", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "price": {"display": "均价", "cell": BaseCell, "update": True},
        "pnl": {"display": "盈亏", "cell": PnlCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
        "pre_margin": {"display": "上次占用的保证金", "cell": BaseCell, "update": True},
        "use_margin": {"display": "占用的保证金", "cell": BaseCell, "update": True},
    }


class AccountMonitor(BaseMonitor):
    """
    Monitor for account data.
    """

    event_type = EVENT_ACCOUNT
    data_key = "vt_accountid"
    sorting = True

    headers = {
        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "balance": {"display": "余额", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "available": {"display": "可用", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
        "cum_margin": {"display": "总保证金", "cell": BaseCell, "update": True},
        "cum_loss": {"display": "最大风险", "cell": BaseCell, "update": True},
        "cum_loss_ratio": {"display": "最大风险比率", "cell": BaseCell, "update": True},
    }

    def init_table(self) -> None:
        """
        Initialize table.
        """
        self.setRowCount(len(self.headers))
        labels = [d["display"] for d in self.headers.values()]
        self.setVerticalHeaderLabels(labels)

        self.horizontalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(self.sorting)

    def insert_new_row(self, data: Any):
        """
        Insert a new row at the top of table.
        """
        self.insertColumn(0)

        row_cells = {}
        for column, header in enumerate(self.headers.keys()):
            setting = self.headers[header]
            content = data.__getattribute__(header)
            cell = setting["cell"](content, data)
            self.setItem(column, 0, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells


class StrategyHoldPositionMonitor(BaseMonitor):
    """
    Monitor for strategy close position data.
    """
    event_type = EVENT_STRATEGY_HOLD_POSITION
    data_key = "orderid"
    headers = {
        "trade_date": {"display": "开仓时间", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "volume": {"display": "持仓量", "cell": BaseCell, "update": True},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "open_slippage": {"display": "开仓滑点", "cell": PnlCell, "update": False},
        "open_price": {"display": "开仓价", "cell": BaseCell, "update": False},
        "max_loss": {"display": "最大亏损", "cell": BaseCell, "update": True},
        "profit": {"display": "盈亏", "cell": PnlCell, "update": True},
        "profit_loss_rate": {"display": "盈亏比", "cell": PnlCell, "update": True},
        "margin": {"display": "保证金", "cell": BaseCell, "update": True},
        "profit_margin_ratio": {"display": "盈亏保证金比", "cell": PnlCell, "update": True},
        "loss_price": {"display": "止损价", "cell": BaseCell, "update": True},
        "win_price": {"display": "止盈价", "cell": BaseCell, "update": True},
        "strategy_name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "strategy_class_name": {"display": "策略类名", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
        "orderid": {"display": "订单id", "cell": BaseCell, "update": False},
    }

    def init_ui(self):
        """
        Connect signal.
        """
        super(StrategyHoldPositionMonitor, self).init_ui()
        self.setToolTip("双击单元格快速强制平仓")
        self.itemDoubleClicked.connect(self.quickly_close)

    def quickly_close(self, cell: BaseCell) -> None:
        data = cell.get_data()
        try:
            tick = copy(self.main_engine.get_engine('oms').ticks[data.vt_symbol])
        except Exception:
            return
        data.un_volume = data.volume
        dialog = QuickLiquidationComponentWidget(self.main_engine, self.event_engine, data, tick)
        dialog.exec()


class StrategyClosePositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """
    event_type = EVENT_STRATEGY_CLOSE_POSITION
    data_key = "orderid"
    sorting = True

    headers = {
        "trade_date": {"display": "开仓时间", "cell": BaseCell, "update": True},
        "close_date": {"display": "平仓时间", "cell": BaseCell, "update": True},
        "open_price": {"display": "开仓价", "cell": BaseCell, "update": True},
        "open_slippage": {"display": "开仓滑点", "cell": PnlCell, "update": True},
        "close_price": {"display": "平仓价", "cell": BaseCell, "update": True},
        "close_slippage": {"display": "平仓滑点", "cell": PnlCell, "update": True},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "volume": {"display": "成交量", "cell": BaseCell, "update": True},
        "profit": {"display": "盈亏", "cell": PnlCell, "update": True},
        # "profit_loss_rate": {"display": "盈亏比", "cell": PnlCell, "update": True},
        "margin": {"display": "保证金", "cell": BaseCell, "update": True},
        "profit_margin_ratio": {"display": "盈亏保证金比", "cell": PnlCell, "update": True},
        "loss_price": {"display": "止损价", "cell": BaseCell, "update": True},
        "win_price": {"display": "止盈价", "cell": BaseCell, "update": True},
        "strategy_name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "strategy_class_name": {"display": "策略类名", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
        "orderid": {"display": "订单id", "cell": BaseCell, "update": False},
    }


class SymbolWinRateMonitor(BaseMonitor):
    """
    品种胜率Monitor
    """
    event_type = EVENT_WINRATE
    data_key = "symbol"
    sorting = True

    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "win_rate": {"display": "品种胜率", "cell": BaseCell, "update": False},
    }


class ForcedLiquidationMonitor(BaseMonitor):
    """
    Monitor for forced liquidation data.
    """
    event_type = EVENT_FORCED_LIQUIDATION
    data_key = "orderid"
    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "strategy_name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "strategy_class_name": {"display": "策略类名", "cell": BaseCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "open_price": {"display": "开仓价", "cell": BaseCell, "update": False},
        "loss_price": {"display": "止损价", "cell": BaseCell, "update": True},
        "win_price": {"display": "止盈价", "cell": BaseCell, "update": True},
        "volume": {"display": "持仓量", "cell": BaseCell, "update": True},
        "trade_date": {"display": "开仓时间", "cell": BaseCell, "update": False},
        "max_loss": {"display": "最大亏损", "cell": BaseCell, "update": True},
        "profit": {"display": "盈亏", "cell": PnlCell, "update": True},
        "margin": {"display": "保证金", "cell": BaseCell, "update": True},
        "profit_margin_ratio": {"display": "盈亏保证金比", "cell": PnlCell, "update": True},
        "orderid": {"display": "订单id", "cell": BaseCell, "update": False},
        "order_ref": {"display": "唯一编号", "cell": BaseCell, "update": False},
        "is_force": {"display": "是否强平", "cell": BaseCell, "update": False},
    }

    def insert_new_row(self, data: Any):
        """
        Insert a new row at the top of table.
        """
        self.insertRow(0)  # 表格顶部插入一行

        row_cells = {}
        for column, header in enumerate(self.headers.keys()):
            setting = self.headers[header]
            # 把强平这一列的单元格设置可复选框框,其他列的单元格用来显示content。
            if header != "is_force":
                content = data.__getattribute__(header)
                cell = setting["cell"](content, data)
                self.setItem(0, column, cell)
            else:
                content = "是否强平"
                cell = setting["cell"](content, data)
                cell.setCheckState(Qt.Unchecked)  # 把表格单元格设置成复选状态:单元格就可以被勾选。
                self.setItem(0, column, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells


class StrategyWhetherContinueOpenMonitor(BaseMonitor):
    """
    Whether to continue to open positions
    """
    event_type = EVENT_STRATEGY_WHETHER_CONTINUE_OPEN
    data_key = "strategy_name"

    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "strategy_name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": True},
        "volume": {"display": "持仓量(手数)", "cell": BaseCell, "update": True},
        "opening_volume": {"display": "开仓量(手数)", "cell": BaseCell, "update": True},
        "is_opening": {"display": "是否继续开仓", "cell": BaseCell, "update": False},
    }

    def update_old_row(self, data: Any) -> None:
        """
        更新旧行时,对成交量进行累加操作。
        """
        key = data.__getattribute__(self.data_key)
        row_cells = self.cells[key]
        for header, cell in row_cells.items():
            if header in ["volume"]:
                content = data.__getattribute__("volume") + int(cell.text())
                cell.set_content(content, data)


class ConnectDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self, main_engine: MainEngine, gateway_name: str):
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.gateway_name: str = gateway_name
        self.filename: str = f"connect_{gateway_name.lower()}.json"

        self.widgets: Dict[str, QtWidgets.QWidget] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(f"连接{self.gateway_name}")

        # Default setting provides field name, field data type and field default value.
        default_setting = self.main_engine.get_default_setting(
            self.gateway_name)

        # Saved setting provides field data used last time.
        loaded_setting = load_json(self.filename)

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in default_setting.items():
            field_type = type(field_value)

            if field_type == list:
                widget = QtWidgets.QComboBox()
                widget.addItems(field_value)

                if field_name in loaded_setting:
                    saved_value = loaded_setting[field_name]
                    ix = widget.findText(saved_value)
                    widget.setCurrentIndex(ix)
            else:
                widget = QtWidgets.QLineEdit(str(field_value))

                if field_name in loaded_setting:
                    saved_value = loaded_setting[field_name]
                    widget.setText(str(saved_value))

                if "密码" in field_name:
                    widget.setEchoMode(QtWidgets.QLineEdit.Password)

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("连接")
        button.clicked.connect(self.connect)
        form.addRow(button)

        self.setLayout(form)

    def connect(self) -> None:
        """
        Get setting value from line edits and connect the gateway.
        """
        setting = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            if field_type == list:
                field_value = str(widget.currentText())
            else:
                field_value = field_type(widget.text())
            setting[field_name] = field_value

        save_json(self.filename, setting)

        self.main_engine.connect(setting, self.gateway_name)

        self.accept()


class TradingWidget(QtWidgets.QWidget):
    """
    General manual trading widget.
    """

    signal_tick = QtCore.pyqtSignal(Event)

    data_filename = "cta_strategy_data.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.vt_symbol: str = ""
        self.price_digits: int = 0

        self.init_ui()

        self.register_event()

    def init_ui(self) -> None:
        """"""
        self.setFixedWidth(500)
        # Trading function area
        exchanges = self.main_engine.get_all_exchanges()
        self.exchange_combo = QtWidgets.QComboBox()
        self.exchange_combo.addItems([exchange.value for exchange in exchanges])

        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.returnPressed.connect(self.set_vt_symbol)

        self.name_line = QtWidgets.QLineEdit()
        self.name_line.setReadOnly(True)

        self.direction_combo = QtWidgets.QComboBox()
        self.direction_combo.addItems(
            [Direction.LONG.value, Direction.SHORT.value])

        self.offset_combo = QtWidgets.QComboBox()
        self.offset_combo.addItems([offset.value for offset in Offset])

        self.order_type_combo = QtWidgets.QComboBox()
        self.order_type_combo.addItems(
            [order_type.value for order_type in OrderType])

        double_validator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)

        self.price_line = QtWidgets.QLineEdit()
        self.price_line.setValidator(double_validator)

        self.volume_line = QtWidgets.QLineEdit()
        self.volume_line.setValidator(double_validator)

        self.gateway_combo = QtWidgets.QComboBox()
        self.gateway_combo.addItems(self.main_engine.get_all_gateway_names())

        self.price_check = QtWidgets.QCheckBox()
        self.price_check.setToolTip("设置价格随行情更新")

        self.strategy_name_combo = QtWidgets.QComboBox()  # 策略名选择框
        self.strategy_name_combo.addItems(self.load_strategy_setting())

        send_button = QtWidgets.QPushButton("委托")
        send_button.clicked.connect(self.send_order)

        cancel_button = QtWidgets.QPushButton("全撤")
        cancel_button.clicked.connect(self.cancel_all)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("交易所"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("代码"), 1, 0)
        grid.addWidget(QtWidgets.QLabel("名称"), 2, 0)
        grid.addWidget(QtWidgets.QLabel("方向"), 3, 0)
        grid.addWidget(QtWidgets.QLabel("开平"), 4, 0)
        grid.addWidget(QtWidgets.QLabel("类型"), 5, 0)
        grid.addWidget(QtWidgets.QLabel("价格"), 6, 0)
        grid.addWidget(QtWidgets.QLabel("数量"), 7, 0)
        grid.addWidget(QtWidgets.QLabel("接口"), 8, 0)
        grid.addWidget(self.exchange_combo, 0, 1, 1, 2)
        grid.addWidget(self.symbol_line, 1, 1, 1, 2)
        grid.addWidget(self.name_line, 2, 1, 1, 2)
        grid.addWidget(self.direction_combo, 3, 1, 1, 2)
        grid.addWidget(self.offset_combo, 4, 1, 1, 2)
        grid.addWidget(self.order_type_combo, 5, 1, 1, 2)
        grid.addWidget(self.price_line, 6, 1, 1, 1)
        grid.addWidget(self.price_check, 6, 2, 1, 1)
        grid.addWidget(self.volume_line, 7, 1, 1, 2)
        grid.addWidget(self.gateway_combo, 8, 1, 1, 2)
        grid.addWidget(send_button, 9, 0, 1, 3)
        grid.addWidget(cancel_button, 10, 0, 1, 3)

        # Market depth display area
        bid_color = "rgb(255,174,201)"
        ask_color = "rgb(160,255,160)"

        self.bp1_label = self.create_label(bid_color)
        self.bp2_label = self.create_label(bid_color)
        self.bp3_label = self.create_label(bid_color)
        self.bp4_label = self.create_label(bid_color)
        self.bp5_label = self.create_label(bid_color)

        self.bv1_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv2_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv3_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv4_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv5_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)

        self.ap1_label = self.create_label(ask_color)
        self.ap2_label = self.create_label(ask_color)
        self.ap3_label = self.create_label(ask_color)
        self.ap4_label = self.create_label(ask_color)
        self.ap5_label = self.create_label(ask_color)

        self.av1_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av2_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av3_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av4_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av5_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)

        self.lp_label = self.create_label()
        self.return_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        form = QtWidgets.QFormLayout()
        form.addRow(QtWidgets.QLabel("卖5价/卖5量:"), self.av5_label)
        form.addRow(QtWidgets.QLabel("卖4价/卖4量:"), self.av4_label)
        form.addRow(QtWidgets.QLabel("卖3价/卖3量:"), self.av3_label)
        form.addRow(QtWidgets.QLabel("卖2价/卖2量:"), self.av2_label)
        form.addRow(QtWidgets.QLabel("卖1价/卖1量:"), self.av1_label)
        form.addRow(QtWidgets.QLabel())
        form.addRow(QtWidgets.QLabel("最新价/涨跌幅比率:"), self.return_label)
        form.addRow(QtWidgets.QLabel())
        form.addRow(QtWidgets.QLabel("买1价/买1量:"), self.bv1_label)
        form.addRow(QtWidgets.QLabel("买2价/买2量:"), self.bv2_label)
        form.addRow(QtWidgets.QLabel("买3价/买3量:"), self.bv3_label)
        form.addRow(QtWidgets.QLabel("买4价/买4量:"), self.bv4_label)
        form.addRow(QtWidgets.QLabel("买5价/买5量:"), self.bv5_label)

        # Overall layout
        vbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(form)
        self.setLayout(vbox)

    def load_strategy_setting(self):
        """
        加载配置文件,返回配置文件中的策略名和策略类名。
        """
        cta_strategy_setting_data = load_json(CTA_STRATEGY_SETTING_FILENAME)
        temporary_list = ['']
        for strategy_name, row in cta_strategy_setting_data.items():
            temporary_list.append(f"{strategy_name};{row['class_name']}")
        return temporary_list

    def create_label(
        self,
        color: str = "",
        alignment: int = QtCore.Qt.AlignLeft
    ) -> QtWidgets.QLabel:
        """
        Create label with certain font color.
        """
        label = QtWidgets.QLabel()
        if color:
            label.setStyleSheet(f"color:{color}")
        label.setAlignment(alignment)
        return label

    def register_event(self) -> None:
        """"""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    def process_tick_event(self, event: Event) -> None:
        """"""
        tick = event.data
        if tick.vt_symbol != self.vt_symbol:
            return
        price_digits = self.price_digits

        self.av1_label.setText(f"{tick.ask_price_1} / {tick.ask_volume_1}")
        self.bv1_label.setText(f"{tick.bid_price_1} / {tick.bid_volume_1}")

        if tick.pre_close:
            r = (tick.last_price / tick.pre_settlement_price - 1) * 100
            self.return_label.setText(f"{tick.last_price:.{price_digits}f} / {r:.2f}")
        else:
            self.return_label.setText(f"{tick.last_price:.{price_digits}f} / 0")

        self.av5_label.setText(f"{tick.ask_price_5:.{price_digits}f} / {tick.ask_volume_5}")
        self.av4_label.setText(f"{tick.ask_price_4:.{price_digits}f} / {tick.ask_volume_4}")
        self.av3_label.setText(f"{tick.ask_price_3:.{price_digits}f} / {tick.ask_volume_3}")
        self.av2_label.setText(f"{tick.ask_price_2:.{price_digits}f} / {tick.ask_volume_2}")
        self.av1_label.setText(f"{tick.ask_price_1:.{price_digits}f} / {tick.ask_volume_1}")

        self.bv1_label.setText(f"{tick.bid_price_1:.{price_digits}f} / {tick.bid_volume_1}")
        self.bv2_label.setText(f"{tick.bid_price_2:.{price_digits}f} / {tick.bid_volume_2}")
        self.bv3_label.setText(f"{tick.bid_price_3:.{price_digits}f} / {tick.bid_volume_3}")
        self.bv4_label.setText(f"{tick.bid_price_4:.{price_digits}f} / {tick.bid_volume_4}")
        self.bv5_label.setText(f"{tick.bid_price_5:.{price_digits}f} / {tick.bid_volume_5}")

        if self.price_check.isChecked():
            self.price_line.setText(f"{tick.last_price:.{price_digits}f}")

    def set_vt_symbol(self) -> None:
        """
        Set the tick depth data to monitor by vt_symbol.
        """
        symbol = str(self.symbol_line.text())

        if not symbol:
            return

        all_contracts = self.main_engine.get_all_contracts()
        if symbol:
            letter = get_letter_from_symbol(symbol)
            contracts = [contract for contract in all_contracts if re.findall(symbol, contract.vt_symbol, flags=re.IGNORECASE)]  # IGNORECASE:忽略大小写
            # CZCE的情况
            contracts.extend([contract for contract in all_contracts if symbol.replace("2", "", 1).upper() in contract.vt_symbol])
            for contract in contracts:
                if contract.product == Product.FUTURES and letter == get_letter_from_symbol(contract.symbol):  # 判断是否是期货
                    symbol = contract.symbol
                    exchange = contract.exchange
                    self.symbol_line.setText(symbol)
                    self.exchange_combo.setCurrentIndex(self.main_engine.get_all_exchanges().index(exchange))

        # Generate vt_symbol from symbol and exchange
        exchange_value = str(self.exchange_combo.currentText())
        vt_symbol = f"{symbol}.{exchange_value}"

        if vt_symbol == self.vt_symbol:
            return
        self.vt_symbol = vt_symbol

        # Update name line widget and clear all labels
        contract = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.name_line.setText("")
            gateway_name = self.gateway_combo.currentText()
        else:
            self.name_line.setText(contract.name)
            gateway_name = contract.gateway_name

            # Update gateway combo box.
            ix = self.gateway_combo.findText(gateway_name)
            self.gateway_combo.setCurrentIndex(ix)

            # Update price digits
            self.price_digits = get_digits(contract.pricetick)

        self.clear_label_text()
        self.volume_line.setText("")
        self.price_line.setText("")

        # Subscribe tick data
        req = SubscribeRequest(
            symbol=symbol, exchange=Exchange(exchange_value)
        )

        self.main_engine.subscribe(req, gateway_name)

    def clear_label_text(self) -> None:
        """
        Clear text on all labels.
        """
        self.lp_label.setText("")
        self.return_label.setText("")

        self.bv1_label.setText("")
        self.bv2_label.setText("")
        self.bv3_label.setText("")
        self.bv4_label.setText("")
        self.bv5_label.setText("")

        self.av1_label.setText("")
        self.av2_label.setText("")
        self.av3_label.setText("")
        self.av4_label.setText("")
        self.av5_label.setText("")

        self.bp1_label.setText("")
        self.bp2_label.setText("")
        self.bp3_label.setText("")
        self.bp4_label.setText("")
        self.bp5_label.setText("")

        self.ap1_label.setText("")
        self.ap2_label.setText("")
        self.ap3_label.setText("")
        self.ap4_label.setText("")
        self.ap5_label.setText("")

    def send_order(self) -> None:
        """
        Send new order manually.
        """
        symbol = str(self.symbol_line.text())
        if not symbol:
            QtWidgets.QMessageBox.critical(self, "委托失败", "请输入合约代码")
            return

        volume_text = str(self.volume_line.text())
        if not volume_text:
            QtWidgets.QMessageBox.critical(self, "委托失败", "请输入委托数量")
            return

        if not get_value("account_info"):
            QtWidgets.QMessageBox.critical(self, "委托失败", "还未获取到账号信息")
            return

        volume = float(volume_text)
        price_text = str(self.price_line.text())
        if not price_text:
            price = 0
        else:
            price = float(price_text)

        order_ref = get_order_ref_value()

        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange(str(self.exchange_combo.currentText())),
            direction=Direction(str(self.direction_combo.currentText())),
            type=OrderType(str(self.order_type_combo.currentText())),
            volume=volume,
            price=price,
            offset=Offset(str(self.offset_combo.currentText())),
            reference="ManualTrading",
            order_ref=order_ref
        )

        gateway_name = str(self.gateway_combo.currentText())

        strategy_name = self.strategy_name_combo.currentText()

        if not strategy_name:
            self.main_engine.send_order(req, gateway_name)
        else:
            account = get_value("account_info").data

            order_data = OrderData(
                gateway_name=gateway_name,
                symbol=symbol,
                exchange=Exchange(str(self.exchange_combo.currentText())),
            )
            order_data.account_id = account.accountid
            order_data.balance = account.balance
            order_data.frozen = account.frozen
            order_data.direction = Direction(str(self.direction_combo.currentText()))
            order_data.type = OrderType(str(self.order_type_combo.currentText()))
            order_data.volume = volume
            order_data.price = price
            order_data.offset = Offset(str(self.offset_combo.currentText()))
            order_data.order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order_data.time = datetime.now().strftime("%H:%M:%S")
            temporary_list = strategy_name.split(';')
            order_data.strategy_name = temporary_list[0]
            order_data.strategy_class_name = temporary_list[1]
            order_data.strategy_author = 'auto'
            order_data.run_type = 'undersell'
            order_data.order_ref = order_ref

            id_ret = OrderDataModel().save_order_data(order_data=order_data)
            if id_ret:
                """委托单插入成功后再向系统发送委托请求"""
                vt_order_id = self.main_engine.send_order(req, gateway_name)
                order_id = str(vt_order_id.split('.')[1])
                # 开始保存委托单时,保存的orderid是OrderData中orderid属性值,默认为""。当给交易服务器成功发送订单时交易服务器会返回个orderid值,所以需要执行更新。
                order_update_ret = OrderDataModel().update(orderid=order_id).where(OrderDataModel.id == id_ret).limit(1).execute()
                print('order_update_ret', order_update_ret)
            else:
                QtWidgets.QMessageBox.critical(self, "委托失败", "数据库插入失败")

    def cancel_all(self) -> None:
        """
        Cancel all active orders.
        """
        order_list = self.main_engine.get_all_active_orders()
        for order in order_list:
            req = order.create_cancel_request()
            self.main_engine.cancel_order(req, order.gateway_name)

    def update_with_cell(self, cell: BaseCell) -> None:
        """
        When you double-click another component, set the relevant data to the input box of the TradingWidget component
        """
        data = cell.get_data()

        self.symbol_line.setText(data.symbol)
        self.exchange_combo.setCurrentIndex(
            self.exchange_combo.findText(data.exchange.value)
        )

        self.set_vt_symbol()

        if isinstance(data, PositionData):
            if data.direction == Direction.SHORT:
                direction = Direction.LONG
            elif data.direction == Direction.LONG:
                direction = Direction.SHORT
            else:       # Net position mode
                if data.volume > 0:
                    direction = Direction.SHORT
                else:
                    direction = Direction.LONG

            self.direction_combo.setCurrentIndex(
                self.direction_combo.findText(direction.value)
            )
            self.offset_combo.setCurrentIndex(
                self.offset_combo.findText(Offset.CLOSE.value)
            )
            self.volume_line.setText(str(abs(data.volume)))
            
        if isinstance(data, TickData):
            self.price_line.setText(str(data.bid_price_1))


class ActiveOrderMonitor(OrderMonitor):
    """
    Monitor which shows active order only.
    """

    def process_event(self, event) -> None:
        """
        Hides the row if order is not active.
        """
        super(ActiveOrderMonitor, self).process_event(event)

        order = event.data
        row_cells = self.cells[order.vt_orderid]
        row = self.row(row_cells["volume"])

        if order.is_active():
            self.showRow(row)
        else:
            self.hideRow(row)


class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers: Dict[str, str] = {
        "vt_symbol": "本地代码",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "gateway_name": "交易接口",
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText("输入合约代码或者交易所，留空则查询所有合约")

        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self) -> None:
        """
        Show contracts by symbol
        """
        if not self.main_engine.connection_flag:
            QMessageBox.about(self, '查询提示', '请连接网关接口后再进行合约查询')
        flt = str(self.filter_line.text())

        all_contracts = self.main_engine.get_all_contracts()
        if flt:
            contracts = [
                contract for contract in all_contracts if flt in contract.vt_symbol
            ]
        else:
            contracts = all_contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()


class ForcedLiquidationPosition(QtWidgets.QWidget):
    """
    forced liquidation Widget
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("强制平仓")
        self.resize(1000, 600)

        self.force_table = ForcedLiquidationMonitor(self.main_engine, self.event_engine)  # 创建强制平仓表格对象

        hbox = QtWidgets.QHBoxLayout()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.force_table)

        self.setLayout(vbox)

    def closeEvent(self, event):
        """窗口的关闭事件处理函数"""
        # region 代码的折叠功能
        text = ""
        object_list = []

        if self.isHidden():  # 如果框架隐藏,
            # 如果想窗口被关闭，那么必须显示调用event->accept（）；如果不想关闭窗口，必须显示调用ignore（），否则窗口默认会关闭。
            event.accept()
            return

        # 获取所有表格的数据遍历找出勾选的用于平仓的数据
        for row in range(self.force_table.rowCount()):
            item = self.force_table.item(row, self.force_table.columnCount() - 1)
            if item.checkState() == 2:  # 选中状态item的状态值为2,用checkState()获取状态值。
                text += f"symbol:{self.force_table.item(row, 0).text()}     策略名称:{self.force_table.item(row, 2).text()}     volume:{self.force_table.item(row, 8).text()}\n"
                if self.force_table.item(row, 4).text() == '多':
                    the_direction = Direction.LONG
                else:
                    the_direction = Direction.SHORT
                forced_liquidation_data = TradeRecordData(
                    symbol=self.force_table.item(row, 0).text(),
                    exchange=Exchange(self.force_table.item(row, 1).text()),
                    strategy_name=self.force_table.item(row, 2).text(),
                    strategy_class_name=self.force_table.item(row, 3).text(),
                    direction=the_direction,
                    open_price=float(self.force_table.item(row, 5).text()),
                    loss_price=float(self.force_table.item(row, 6).text()),
                    win_price=float(self.force_table.item(row, 7).text()),
                    volume=int(self.force_table.item(row, 8).text()),
                    trade_date=to_datetime(self.force_table.item(row, 9).text()),
                    max_loss=float(self.force_table.item(row, 10).text()),
                    profit=float(self.force_table.item(row, 11).text()),
                    margin=float(self.force_table.item(row, 12).text()),
                    profit_margin_ratio=self.force_table.item(row, 13).text(),
                    orderid=self.force_table.item(row, 14).text(),
                    gateway_name="",
                    account_id="",
                    order_ref=self.force_table.item(row, 15).text(),
                    offset=Offset.OPEN,
                )
                forced_liquidation_data.un_volume = forced_liquidation_data.volume
                object_list.append(forced_liquidation_data)
        # endregion

        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle('确认是否强平下列持仓（默认取消并退出）')
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        message_box.setDefaultButton(QMessageBox.No)
        message_box.button(QMessageBox.Yes).setText('强平并退出')
        message_box.button(QMessageBox.No).setText('返回')
        message_box.button(QMessageBox.Cancel).setText('取消并退出')

        selected_button = message_box.exec()
        if selected_button == QMessageBox.Yes:
            event.accept()
            # 复原按钮
            for row in range(self.force_table.rowCount()):
                item = self.force_table.item(row, self.force_table.columnCount() - 1)
                item.setCheckState(Qt.Unchecked)
            # 进行强制平仓操作
            for obj in object_list:
                tick = copy(self.main_engine.get_engine('oms').ticks[obj.vt_symbol])
                # cta策略平仓
                cta_strategy_engine = self.main_engine.get_engine("CtaStrategy")
                if cta_strategy_engine:
                    cta_strategy_engine.on_close(obj, tick)
                # 组合策略平仓
                portfolio_strategy_engine = self.main_engine.get_engine("PortfolioStrategy")
                if portfolio_strategy_engine:
                    portfolio_strategy_engine.on_close(obj, tick)

        elif selected_button == QMessageBox.No:
            event.ignore()

        elif selected_button == QMessageBox.Cancel:
            # 复原按钮
            for row in range(self.force_table.rowCount()):
                item = self.force_table.item(row, self.force_table.columnCount() - 1)
                item.setCheckState(Qt.Unchecked)
            event.accept()


class AboutDialog(QtWidgets.QDialog):
    """
    About VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(f"关于VN Trader")

        text = f"""
            By Traders, For Traders.


            License：MIT
            Website：www.vnpy.com
            Github：www.github.com/vnpy/vnpy


            vn.py - {vnpy.__version__}
            Python - {platform.python_version()}
            PyQt5 - {Qt.PYQT_VERSION_STR}
            Numpy - {np.__version__}
            RQData - {rqdatac.__version__}
            """

        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        self.setLayout(vbox)


class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.widgets: Dict[str, Any] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("全局配置")
        self.setMinimumWidth(800)

        settings = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type = type(field_value)
            widget = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("确定")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setLayout(form)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroll_area)
        self.setLayout(vbox)

    def update_setting(self) -> None:
        """
        Get setting value from line edits and update global setting file.
        """
        settings = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text = widget.text()

            if field_type == bool:
                if value_text == "True":
                    field_value = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "全局配置的修改需要重启VN Trader后才会生效！",
            QtWidgets.QMessageBox.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()
