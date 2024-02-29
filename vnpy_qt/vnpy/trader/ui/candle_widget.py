"""
显示期货合约行情数据
"""
from typing import Tuple

from tzlocal import get_localzone
from collections import defaultdict
from copy import copy, deepcopy
from datetime import datetime, timezone
from datetime import timedelta
from PyQt5.QtCore import Qt
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QPushButton, QGroupBox, QHBoxLayout
from dateutil import parser
from vnpy.chart.manager import BarManager

from vnpy.app.cta_strategy.convert import Convert
from vnpy.chart import ChartWidget, CandleItem, VolumeItem
from vnpy.chart.base import YELLOW_COLOR, RED_COLOR, GREEN_COLOR, WHITE_COLOR, YELLOW_COLOR_2
from vnpy.event import EventEngine
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import (BarData, TradeData)
from vnpy.trader.symbol_attr import ContractPricePick
from vnpy.trader.utility import get_contrast_direction, get_letter_from_symbol
from ..constant import Direction, Offset
from ..engine import MainEngine
from ..setting import CTA_STRATEGY_SETTING_FILENAME
from ..utility import load_json
from ...controller.global_variable import get_value,get_all_value


def show_candle_chart(main_engine, event_engine, headers):
    end_time = datetime.now()
    start_time = datetime.now() - timedelta(days=365)
    exchange = Convert().convert_jqdata_exchange(exchange=headers['exchange']['value'])
    headers['exchange']['value'] = exchange.value
    symbol = headers['symbol']['value']
    try:
        account_id = get_value("account_info").data.accountid
    except Exception:
        account_id = "0"

    # 加载近一年的日k线图数据
    one_day_bar_list = database_manager.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.DAILY,
        start=start_time,
        end=end_time,
    )
    # 加载半年前的半年左右的分钟k线图数据
    one_min_bar_list = database_manager.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.MINUTE,
        start=end_time - timedelta(days=160),
        end=end_time,
    )
    # 获取近一年的持仓单数据
    trade_data_list = TradeDataModel().select().where(
        (TradeDataModel.symbol == symbol)
        & (TradeDataModel.account_id == account_id)
        & (TradeDataModel.trade_date > start_time)
        & (TradeDataModel.trade_date < end_time)
        & (TradeDataModel.gateway_name == headers['gateway_name']['value'])
        & (TradeDataModel.un_volume > 0)
        & (TradeDataModel.offset == "OPEN")
    )

    trade_list = convert_headers_trade(headers)  # 将headers中成交信息封装list,每一个对象都是一个TradeData(开仓/平仓成交易数据对象)
    strategy_name_list = [trade_list[0].orderid]  # 存储开仓 或 平仓成交单中策略名

    for trade_data in trade_data_list:
        if trade_data.direction == 'LONG':
            direction_open = Direction.LONG
        else:
            direction_open = Direction.SHORT
        # 构建开仓单成交数据对象
        trade_open = TradeData(
            symbol=trade_data.symbol,
            exchange=Exchange(trade_data.exchange),
            orderid=trade_data.orderid,
            tradeid=trade_data.tradeid,
            direction=direction_open,
            offset=Offset.OPEN,
            price=trade_data.price,
            volume=trade_data.volume,
            time=trade_data.trade_date.strftime("%H:%M:%S"),
            gateway_name=trade_data.gateway_name,
            strategy_class_name=trade_data.strategy_class_name,
            strategy_name=trade_data.strategy_name,
        )
        trade_open.datetime = trade_data.trade_date
        trade_open.win_price = trade_data.win_price
        trade_open.loss_price = trade_data.loss_price

        if "close_date" not in headers:
            if trade_data.orderid not in strategy_name_list:
                trade_list.append(trade_open)
                strategy_name_list.append(trade_data.orderid)  # 添加最近一年的开仓的orderid(但现在还持仓的)
        else:
            # 构建平仓单成交数据对象
            if trade_data.un_volume < trade_data.volume:
                trade_data_close_list = TradeDataModel().select().where(
                    (TradeDataModel.trade_date > start_time)
                    & (TradeDataModel.trade_date < end_time)
                    & (TradeDataModel.order_ref == trade_data.order_ref)
                    & (TradeDataModel.offset != "OPEN")
                )
                for trade_data_close in trade_data_close_list:
                    trade_close = deepcopy(trade_open)
                    trade_close.direction = trade_data_close.direction
                    trade_close.offset = Offset.CLOSE
                    trade_close.price = trade_data_close.price
                    trade_close.time = trade_data_close.trade_date.strftime("%H:%M:%S")
                    trade_close.datetime = trade_data_close.trade_date
                    if trade_data.orderid not in strategy_name_list:
                        trade_list.append(trade_open)
                        trade_list.append(trade_close)
                        strategy_name_list.append(trade_data.orderid)  # 添加最近一年的平仓的orderid(单现在还持仓的)

    candle_dialog = TraderCandleChartDialog(main_engine, event_engine, headers, one_min_bar_list, one_day_bar_list, trade_list, strategy_name_list)
    candle_dialog.exec_()


def convert_headers_trade(headers):
    """将headers里面包含的成交数据构建成TradeData(成交数据对象)"""
    # 构建开仓单成交数据对象
    trade_open = TradeData(
        symbol=headers['symbol']['value'],
        exchange=Exchange(headers['exchange']['value']),
        orderid=headers["orderid"]["value"],
        tradeid="0",
        direction=Direction(headers['direction']['value']),
        offset=Offset.OPEN,
        price=float(headers['open_price']['value']),
        volume=float(headers['volume']['value']),
        time=headers['trade_date']['value'].split(' ')[1],
        strategy_name=headers['strategy_name']['value'],
        gateway_name=headers['gateway_name']['value']
    )
    trade_open.datetime = parser.parse(headers['trade_date']['value'])
    trade_open.win_price = float(headers['win_price']['value'])
    trade_open.loss_price = float(headers['loss_price']['value'])

    # 构建平仓成交单数据对象
    if "close_date" in headers.keys():  # 判断是策略开仓组件还是策略平仓组件(策略开仓组件中headers中是没有close_date键的)
        trade_close = deepcopy(trade_open)
        trade_close.direction = get_contrast_direction(trade_open.direction)
        trade_close.offset = Offset.CLOSE
        trade_close.price = float(headers['close_price']['value'])
        trade_close.time = headers['close_date']['value'].split(' ')[1]
        trade_close.datetime = parser.parse(headers['close_date']['value'])
        return [trade_open, trade_close]
    else:
        return [trade_open]


class TraderCandleChartDialog(QtWidgets.QDialog):
    """
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, headers: list,
                 one_min_bars: list, one_day_bars: list, trade_list: list, strategy_list: list):
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.headers = headers
        self.symbol = self.headers["symbol"]['value']
        self.exchange: Exchange = self.headers["exchange"]['value']
        self.vt_symbol = f"{self.symbol}.{self.exchange}"
        self.pricePick: float = 0
        self.interval_list = ['1D', '1M', '5M', '10M', '15M', '30M', '60M']
        self.interval_button_list = []  # 存储K线的不同interval的按钮对象
        self.strategy_button_list = []  # 存储右边的成交单的所在区的那些按钮对象
        self.one_min_bars = one_min_bars  # 获取1分钟的Bars
        self.min_datetime_series = pd.Series(self.one_min_bars).apply(lambda x: x.datetime)  # 构建Series对象,元素为日bar的datetime。
        self.one_day_bars = one_day_bars
        self.day_datetime_series = pd.Series(self.one_day_bars).apply(lambda x: x.datetime)  # 构建Series对象,元素为分钟bar的datetime。
        self.interval_bars_dict = {}  # {interval:对应的bar数据}
        self.trade_list = trade_list  # 存储开仓和/平仓数据对象
        self.dt_ix_map = {}
        self.infinite_line_list = []  # 存储开仓线、止盈线、止损线
        self.interval_datetime_dict = {}  # {interval:不同周期的datetime的series对象}
        self.strategy_list = strategy_list  # 存储开仓/平仓成交单中策略名
        self.strategy_trades_dict = defaultdict(list)   # {成交单的策略名:成交单数据对象}
        self.chart: ChartWidget = None
        self.init_variable()
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle(f"实盘交易K线图表")
        # QDialog设置显示最大化、最小化、关闭按钮。
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.resize(1800, 1000)
        # 创建图表小部件
        self.chart = self.create_chart()
        # 添加散点图对象用来显示交易记录
        self.trade_scatter = pg.ScatterPlotItem()
        self.candle_plot = self.chart.get_plot("candle")  # 获取蜡烛图表
        self.candle_plot.addItem(self.trade_scatter)
        h_box_top = self.create_groupbox()   # 创建一个分组框,用来放置点击按钮。
        show_table = self.create_table()  # 创建一个用来显示交易单数据的tableWidget,并且在tableWidget中显示成交单数据。
        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(show_table, stretch=2)  # stretch=2指在布局中占用的比例
        vbox.addLayout(h_box_top, stretch=1)
        vbox.addWidget(self.chart, stretch=13)
        self.setLayout(vbox)

    def init_variable(self):
        """初始化一些变量"""
        symbol_letter = get_letter_from_symbol(self.symbol)
        contracts = self.main_engine.get_engine('oms').contracts
        if self.vt_symbol in contracts.keys():
            self.pricePick = contracts[self.vt_symbol].pricetick  # 初始化最小价格跳动
        else:
            self.pricePick = ContractPricePick.get(symbol_letter)
            
        for interval in self.interval_list:
            if interval == '1D':
                self.interval_datetime_dict[interval] = pd.Series(self.one_day_bars).apply(lambda x: x.datetime)  # 1D周期的datetime的Series对象
            else:
                num = int(interval[:-1])
                temp_series = pd.Series(self.one_min_bars).apply(lambda x: x.datetime)
                temp_series = temp_series[temp_series.apply(lambda x: True if x.minute % num == 0 else False)]
                self.interval_datetime_dict[interval] = temp_series  # 非1D周期的datetime的Series对象

        for trade in self.trade_list:
            if trade.orderid in self.strategy_list:
                self.strategy_trades_dict[trade.orderid].append(trade)

    def create_chart(self) -> ChartWidget:
        """"""
        chart = ChartWidget()
        chart.add_plot("candle", hide_x_axis=True)
        chart.add_plot("volume", maximum_height=200)
        chart.add_item(TradeCandleItem, "candle", "candle")
        chart.add_item(VolumeItem, "volume", "volume")
        chart.add_cursor()
        return chart

    def create_table(self):
        """创建一个tableWidget,并且在tableWidget中显示成交单信息"""
        show_table = QtWidgets.QTableWidget(1, len(self.headers), self)
        labels = [d["display"] for d in self.headers.values()]
        show_table.setHorizontalHeaderLabels(labels)  # 设置表头
        show_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        show_table.setEditTriggers(show_table.NoEditTriggers)
        show_table.setAlternatingRowColors(True)

        for num, value in enumerate(self.headers.values()):
            show_table.setItem(0, num, QtWidgets.QTableWidgetItem(str(value['value'])))
        show_table.resizeColumnsToContents()
        return show_table

    def create_groupbox(self):
        """创建一个分组框, 用来放置点击按钮"""
        h_box_top = QHBoxLayout()
        # 创建['1D', '1M', '5M', '10M', '15M', '30M', '60M']那部分的按钮
        groupbox_interval = QGroupBox()
        h_box_l = QHBoxLayout()
        groupbox_interval.setLayout(h_box_l)
        for interval in self.interval_list:
            push_button = QPushButton(interval, self)
            push_button.setCheckable(True)
            if interval == '1D':  # 设计初始化k-线图界面的时候就画出日-K线,把日k-线的按钮设置成选中状态
                self.update_history(self.one_day_bars)
                push_button.setChecked(True)
            push_button.clicked[bool].connect(self.different_interval__k_line)
            h_box_l.addWidget(push_button)
            self.interval_button_list.append(push_button)
        h_box_l.addStretch(1)

        # 创建右边的成交单的所在区的那些按钮
        groupbox_strategy_order = QGroupBox()
        h_box_r = QHBoxLayout()
        groupbox_strategy_order.setLayout(h_box_r)
        for strategy in self.strategy_list:
            push_button = QPushButton(strategy, self)
            push_button.setCheckable(True)
            push_button.clicked[bool].connect(self.draw_strategy_positions_line)
            h_box_r.addWidget(push_button)
            self.strategy_button_list.append(push_button)
        h_box_r.addStretch(1)

        h_box_top.addWidget(groupbox_interval, stretch=1)
        h_box_top.addWidget(groupbox_strategy_order, stretch=2)
        return h_box_top

    def update_history(self, history: list):
        """"""
        self.chart.update_history(history)
        for ix, bar in enumerate(history):
            self.dt_ix_map[bar.datetime] = ix

    def update_trades(self, trades: list):
        """"""
        trade_data = []
        label_opts = {'color': WHITE_COLOR, 'movable': True, 'fill': (0, 100, 100, 10), 'rotateAxis': [10, 0.1], 'position': 0.95}
        for trade in trades:
            if self.dt_ix_map.get(trade.datetime, None):
                scatter = self.get_scatter_data(trade)  # 获取散点图数据
                label_opts['position'] -= 0.2
                # 画出 开仓线，止盈线，止损线
                if trade.offset == Offset.OPEN:
                    label_opts['color'] = WHITE_COLOR
                    open_line = pg.InfiniteLine(pos=trade.price, angle=0, label=f'开仓价: {trade.price}', labelOpts=label_opts)
                    label_opts['color'] = RED_COLOR
                    win_line = pg.InfiniteLine(pos=trade.win_price, angle=0, pen=label_opts['color'], label=f'止盈价: {trade.win_price}', labelOpts=label_opts)
                    label_opts['color'] = GREEN_COLOR
                    loss_line = pg.InfiniteLine(pos=trade.loss_price, angle=0, pen=label_opts['color'], label=f'止损价: {trade.loss_price}', labelOpts=label_opts)
                    self.candle_plot.addItem(open_line)
                    self.candle_plot.addItem(win_line)
                    self.candle_plot.addItem(loss_line)
                    self.infinite_line_list.extend([open_line, win_line, loss_line])
                else:
                    label_opts['color'] = YELLOW_COLOR_2
                    close_line = pg.InfiniteLine(pos=trade.price, angle=0, pen=label_opts['color'], label=f'平仓价: {trade.price}', labelOpts=label_opts)
                    self.candle_plot.addItem(close_line)
                    self.infinite_line_list.append(close_line)

                # 设置视图的可视范围
                view_range = self.candle_plot.getViewBox().viewRange()
                y_low = view_range[1][0]
                y_high = view_range[1][1]
                max_price = (max([trade.win_price, trade.loss_price, y_high]) + self.pricePick * 10) * 1.1
                min_price = (min([trade.win_price, trade.loss_price, y_low]) - self.pricePick * 10) * 0.9
                self.candle_plot.setLimits(
                    xMin=-1,
                    xMax=self.chart._manager.get_count(),
                    yMin=min_price,
                    yMax=max_price
                )

                # 点击按钮时光标自动跳到到达对应的区域
                min_ix = max(self.dt_ix_map[trade.datetime] - 100, 0)
                max_ix = min(self.dt_ix_map[trade.datetime] + 100, max(list(self.dt_ix_map.values())))
                for plot in self.chart._plots.values():
                    plot.setRange(xRange=(min_ix, max_ix), padding=0)

                trade_data.append(scatter)

        self.trade_scatter.setData(trade_data)  # 把数据设置到散点图上

    def clear_data(self):
        """"""
        self.chart.clear_all()
        self.dt_ix_map.clear()
        self.trade_scatter.clear()  # 清除交易记录数据

        for line in self.infinite_line_list:  # 删除开仓线、止盈线、止损线
            self.candle_plot.removeItem(line)
        self.infinite_line_list = []

    def different_interval__k_line(self, pressed):
        """不同周期的k线图点击事件"""
        if pressed:
            text = self.sender().text()
            # 将未选中的按钮复原
            for btn in self.interval_button_list:
                if btn != self.sender():
                    btn.setChecked(False)
            self.clear_data()  # 清空相关数据
            # 将策略交易按钮设置成未选中状态(按钮复原)
            self.strategy_trade_button_recover()
            # 蜡烛图的切换操作
            if text == '1D':
                self.update_history(self.one_day_bars)
            elif text == '1M':
                self.update_history(self.one_min_bars)
            else:
                if text in self.interval_bars_dict.keys():
                    self.update_history(self.interval_bars_dict[text])
                else:
                    interval = int(text[:-1])
                    window_bar_list = []
                    window_bar = None
                    last_bar = None
                    for bar in self.one_min_bars:  # 循环遍历分钟Bar
                        if not window_bar:   # 初始化window_bar
                            window_bar = BarData(
                                symbol=bar.symbol,
                                exchange=bar.exchange,
                                datetime=bar.datetime,
                                gateway_name=bar.gateway_name,
                                open_price=bar.open_price,
                                high_price=bar.high_price,
                                low_price=bar.low_price
                            )
                        else:  # 否则更新window_bar的最高/最低价
                            window_bar.high_price = max(
                                window_bar.high_price, bar.high_price)
                            window_bar.low_price = min(
                                window_bar.low_price, bar.low_price)
                        # 更新收盘价和成交量
                        window_bar.close_price = bar.close_price
                        window_bar.volume += int(bar.volume)
                        window_bar.open_interest = bar.open_interest
                        finished = False
                        # x-minute bar
                        if interval < 60:
                            if not bar.datetime.minute % interval:
                                window_bar.datetime = bar.datetime
                                finished = True
                        elif interval == 60:  # 1h bar
                            if last_bar and bar.datetime.hour != last_bar.datetime.hour and bar.datetime.minute == 0:
                                window_bar.datetime = bar.datetime
                                finished = True
                        if finished:
                            window_bar_list.append(copy(window_bar))
                            window_bar = None
                        last_bar = bar  # 记录上一个bar
                    self.interval_bars_dict[text] = window_bar_list
                    self.update_history(self.interval_bars_dict[text])
        else:
            self.sender().setChecked(True)

    def strategy_trade_button_recover(self):
        """将按钮设置成未选中状态"""
        for btn in self.strategy_button_list:
            btn.setChecked(False)

    def draw_strategy_positions_line(self, pressed):
        """点击按钮,画出策略仓位相关的线"""
        # 获取点击按钮的文本
        for btn in self.interval_button_list:
            if btn.isChecked():
                interval_text = btn.text()
                break

        # 删除开仓线、止盈线、止损线
        for line in self.infinite_line_list:
            self.candle_plot.removeItem(line)
        self.infinite_line_list = []

        # 获取被选中状态的按钮对应的成交数据
        trades = []
        for btn in self.strategy_button_list:
            if btn.isChecked():
                trades.extend(deepcopy(self.strategy_trades_dict[btn.text()]))

        # 成交单时间处理
        temp_series = self.interval_datetime_dict[interval_text]  # 获取不同interval的datetime的series对象
        for trade in trades:
            if interval_text == '1D':
                trade.datetime = datetime(year=trade.datetime.year, month=trade.datetime.month, day=trade.datetime.day, hour=trade.datetime.hour, minute=trade.datetime.minute,
                                          second=trade.datetime.second, tzinfo=get_localzone())  # 给datetime带上时区
                trade.datetime = (trade.datetime + timedelta(hours=6)).replace(hour=0, minute=0, second=0)  # 把夜盘算作第二天
                # 如果把夜盘成交的trade的datetime更改次日日期,会存在次日不是交易日的问题。
                if temp_series.shape[0] and temp_series.iat[-1] >= trade.datetime:
                    # 防止上面构建的trade.datetime为未交易日时间,通过数据库中的bar数据日期来更正。
                    trade.datetime = temp_series[temp_series >= trade.datetime].iat[0]

        self.update_trades(trades)


    def load_strategy_setting(self):
        """
        加载配置文件,返回配置文件中的策略名
        """
        cta_strategy_setting_data = load_json(CTA_STRATEGY_SETTING_FILENAME)
        temporary_list = []
        for strategy_name, row in cta_strategy_setting_data.items():
            temporary_list.append(strategy_name)
        return temporary_list

    def get_scatter_data(self, trade):
        """返回画交易标志符号的散点图数据"""
        ix = self.dt_ix_map[trade.datetime]  # trade.datetime一定要要是bar.datetime里面的,否则trade.datetime就是非交易日,就会报键错误。
        scatter = {
            "pos": (ix, trade.price),
            "data": 1,
            "size": 14,
            "pen": pg.mkPen((255, 255, 255))
        }
        if trade.direction == Direction.LONG:
            scatter_symbol = "t1"  # Up arrow
        else:
            scatter_symbol = "t"  # Down arrow
        if trade.offset == Offset.OPEN:
            scatter_brush = pg.mkBrush((255, 255, 0))  # Yellow
        else:
            scatter_brush = pg.mkBrush((0, 0, 255))  # Blue
        scatter["symbol"] = scatter_symbol
        scatter["brush"] = scatter_brush
        return scatter


class TradeCandleItem(CandleItem):
    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        min_price, max_price = self._manager.get_price_range(min_ix, max_ix)
        return min_price * 0.9, max_price * 1.1

