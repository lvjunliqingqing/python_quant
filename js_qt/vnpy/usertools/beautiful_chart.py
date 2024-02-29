from typing import List
import pyqtgraph as pg
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from vnpy.app.cta_strategy.base import (
    EVENT_CTA_TICK,
    EVENT_CTA_BAR,
    EVENT_CTA_HISTORY_BAR
)
from vnpy.chart import ChartWidget
from vnpy.chart.base import NORMAL_FONT
from vnpy.event import Event, EventEngine
from vnpy.trader.object import BarData
from vnpy.trader.object import (
    OrderData,
    TradeData,
)
from vnpy.trader.ui import QtCore, QtWidgets
from vnpy.usertools.chart_items import (
    TradeItem,
    OrderItem,
)


class NewChartWidget(ChartWidget):
    """
    基于ChartWidget的K线图表窗口部件
    """
    MIN_BAR_COUNT = 100
    signal_cta_history_bar: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_tick: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_bar: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, parent: QtWidgets.QWidget = None, event_engine: EventEngine = None, strategy_name: str = ""):

        super().__init__(parent)
        self.strategy_name = strategy_name
        self.event_engine = event_engine
        # 委托单列表
        self.orders: List[str, OrderData] = {}
        # 成交单列表
        self.trades: List[str, TradeData] = {}
        self._trade_line_item = []  # 存储交易连线item对象
        self.last_price_hidden_flag = False  # 控制是否隐藏最新线
        self.net_asset_curve_hidden_flag = False  # 控制资金曲线是否隐藏
        self.SMA_line_hidden_flag = False  # 控制SMA曲线是否隐藏
        self.trade_connection_line_hidden_flag = False  # 控制交易连接线是否隐藏

        # self.register_event()
        # self.event_engine.start()

    def initialize_context_menu(self, pos):

        self.menu = QtWidgets.QMenu()

        self.k_line_menu = QtWidgets.QMenu("k线指标线")

        self.cursor_hidden_action = QtWidgets.QAction("鼠标光标线隐藏   Ctrl+X", self)
        self.cursor_hidden_action.setCheckable(True)
        if self.cursor_hidden_flag:
            self.cursor_hidden_action.setChecked(True)
        self.cursor_hidden_action.triggered.connect(self.whether_cursor_hidden)

        self.last_price_hidden_action = QtWidgets.QAction("隐藏最新价格线   Ctrl+L", self)
        self.last_price_hidden_action.setCheckable(True)
        if self.last_price_hidden_flag:
            self.last_price_hidden_action.setChecked(True)
        self.last_price_hidden_action.triggered.connect(self.whether_last_price_line_hidden)
        self.k_line_menu.addAction(self.last_price_hidden_action)

        self.net_asset_curve_hidden_action = QtWidgets.QAction("隐藏资金曲线   Ctrl+Z", self)
        self.net_asset_curve_hidden_action.setCheckable(True)
        if self.net_asset_curve_hidden_flag:
            self.net_asset_curve_hidden_action.setChecked(True)
        self.net_asset_curve_hidden_action.triggered.connect(self.whether_net_asset_curve_hidden)
        self.k_line_menu.addAction(self.net_asset_curve_hidden_action)

        self.SMA_hidden_action = QtWidgets.QAction("隐藏SMA线   Ctrl+S", self)
        self.SMA_hidden_action.setCheckable(True)
        if self.SMA_line_hidden_flag:
            self.SMA_hidden_action.setChecked(True)
        self.SMA_hidden_action.triggered.connect(self.whether_sma_line_hidden)
        self.k_line_menu.addAction(self.SMA_hidden_action)

        self.trade_connection_line_hidden_action = QtWidgets.QAction("隐藏交易盈亏连接线   Ctrl+J", self)
        self.trade_connection_line_hidden_action.setCheckable(True)
        if self.trade_connection_line_hidden_flag:
            self.trade_connection_line_hidden_action.setChecked(True)
        self.trade_connection_line_hidden_action.triggered.connect(self.whether_trade_connection_line_hidden)
        self.k_line_menu.addAction(self.trade_connection_line_hidden_action)

        background_action = QtWidgets.QAction("背景色改变    Ctrl+C", self)
        background_action.setCheckable(True)
        if self.had_change_background:
            background_action.setChecked(True)
        background_action.triggered.connect(self.change_background)

        self.k_line_menu.addAction(self.cursor_hidden_action)
        self.menu.addMenu(self.k_line_menu)
        self.menu.addAction(background_action)

        background_action.actionGroup()

        self.menu.exec_(self.mapToGlobal(pos))

    def chart_shortcut(self):
        """热键设置"""
        super(NewChartWidget, self).chart_shortcut()

        self.last_price_hidden_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.last_price_hidden_shortcut.activated.connect(self.whether_last_price_line_hidden)

        self.net_asset_curve_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.net_asset_curve_shortcut.activated.connect(self.whether_net_asset_curve_hidden)

        self.SMA_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.SMA_shortcut.activated.connect(self.whether_sma_line_hidden)

        self.trade_connection_line_shortcut = QShortcut(QKeySequence("Ctrl+J"), self)
        self.trade_connection_line_shortcut.activated.connect(self.whether_trade_connection_line_hidden)

    def whether_last_price_line_hidden(self):
        """隐藏最新价格画线"""
        if not self.last_price_hidden_flag:
            self.last_price_line.hide()
        else:
            self.last_price_line.show()
        self.last_price_hidden_flag = (not self.last_price_hidden_flag)

    def whether_net_asset_curve_hidden(self):
        """隐藏资金曲线"""
        if not self.net_asset_curve_hidden_flag:
            self.candle_left_item.hide()
        else:
            self.candle_left_item.show()
        self.net_asset_curve_hidden_flag = (not self.net_asset_curve_hidden_flag)

    def whether_sma_line_hidden(self):
        """隐藏SMA曲线"""
        if not self.SMA_line_hidden_flag:
            self._items["sma"].hide()
        else:
            self._items["sma"].show()
        self.SMA_line_hidden_flag = (not self.SMA_line_hidden_flag)

    def whether_trade_connection_line_hidden(self):
        """隐藏交易连接线"""
        if not self.trade_connection_line_hidden_flag:
            for item in self._trade_line_item:
                item.hide()
        else:
            for item in self._trade_line_item:
                item.show()
        self.trade_connection_line_hidden_flag = (not self.trade_connection_line_hidden_flag)

    def register_event(self) -> None:
        """"""
        self.signal_cta_history_bar.connect(self.process_cta_history_bar)
        self.event_engine.register(EVENT_CTA_HISTORY_BAR, self.signal_cta_history_bar.emit)

        self.signal_cta_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_CTA_TICK, self.signal_cta_tick.emit)

        self.signal_cta_bar.connect(self.process_cta_bar)
        self.event_engine.register(EVENT_CTA_BAR, self.signal_cta_bar.emit)

    def process_cta_history_bar(self, event: Event) -> None:
        """ 处理历史K线推送 """
        strategy_name, history_bars = event.data
        if strategy_name == self.strategy_name:
            self.update_history(history_bars)

            # print(f" {strategy_name} got an EVENT_CTA_HISTORY_BAR")

    def process_tick_event(self, event: Event) -> None:
        """ 处理tick数据推送 """
        strategy_name, tick = event.data
        if strategy_name == self.strategy_name:
            if self.last_price_line:
                self.last_price_line.setValue(tick.last_price)
            # print(f" {strategy_name} got an EVENT_CTA_TICK")

    def process_cta_bar(self, event: Event) -> None:
        """ 处理K线数据推送 """

        strategy_name, bar = event.data
        if strategy_name == self.strategy_name:
            self.update_bar(bar)
            # print(f"{strategy_name} got an EVENT_CTA_BAR")

    def add_last_price_line(self):
        """增加最新价格线(在最新价格上画一条直线)"""
        plot = list(self._plots.values())[0]
        color = (0, 255, 0)

        self.last_price_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            label="最新价:{value:.3f}",
            pen=pg.mkPen(color, width=1),
            labelOpts={
                "color": color,
                "position": 1,
                "anchors": [(1, 1), (1, 1)]
            }
        )
        self.last_price_line.label.setFont(NORMAL_FONT)
        plot.addItem(self.last_price_line)

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()
        self.update_last_price_line(history[-1])

    def update_bar(self, bar: BarData) -> None:
        """
            Update single bar data.
        """
        self._manager.update_bar(bar)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

        self.update_last_price_line(bar)

    def update_last_price_line(self, bar: BarData) -> None:
        """设置最新价线的位置"""
        if self.last_price_line:
            self.last_price_line.setValue(bar.close_price)

    def add_orders(self, orders: List[OrderData]) -> None:
        """
        增加委托单列表到委托单绘图部件
        """
        # for order in orders:
        #     self.orders[order.orderid] = order

        order_item: OrderItem = self.get_item('order')
        if order_item:
            order_item.add_orders(orders)

    def add_trades(self, trades: List[TradeData]) -> None:
        """
        增加成交单列表到委托单绘图部件
        """
        # for trade in trades:
        #     self.trades[trade.tradeid] = trade

        trade_item: TradeItem = self.get_item('trade')
        if trade_item:
            trade_item.add_trades(trades)


