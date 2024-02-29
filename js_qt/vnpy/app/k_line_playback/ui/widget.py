import numpy as np
from copy import copy
from datetime import datetime, timedelta
from typing import List
import pyqtgraph as pg
from tzlocal import get_localzone
from PyQt5.QtCore import Qt
from vnpy.chart import ChartWidget, CandleItem, VolumeItem
from vnpy.event import Event, EventEngine
from vnpy.trader.constant import Interval
from vnpy.trader.engine import MainEngine
from vnpy.trader.event import EVENT_TICK
from vnpy.trader.object import TickData, BarData, SubscribeRequest
from vnpy.trader.symbol_attr import ContractMultiplier, ContractPricePick, SymbolCommission, SymbolExchange
from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.utility import BarGenerator
from vnpy.trader.utility import load_json, save_json, get_letter_from_symbol
from .my_slider import MyQSlider
from ..engine import (
    APP_NAME,
    EVENT_PLAY_BACK_CHART_BACKTESTER_LOG, EVENT__PLAY_BACK_CHART_BACKTESTING_FINISHED
)
from ..engine import EVENT_PLAY_BACK_CHART_HISTORY

from typing import Dict
from vnpy.trader.ui.widget import BaseMonitor, BaseCell, DirectionCell, EnumCell


class PlayBackChartWidget(QtWidgets.QWidget):
    """"""
    setting_filename = "play_back_chart_setting.json"
    signal_tick = QtCore.pyqtSignal(Event)
    signal_history = QtCore.pyqtSignal(Event)
    signal_log = QtCore.pyqtSignal(Event)
    signal_play_back_backtesting_finished = QtCore.pyqtSignal(Event)  # noqa

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine
        self.play_back_engine = main_engine.get_engine(APP_NAME)
        self.backtester_engine = self.play_back_engine  # stop_backtesting()中的stop需要backtester_engine

        self.bgs: Dict[str, BarGenerator] = {}
        self.charts: Dict[str, ChartWidget] = {}

        self._history = []
        self._history_write_flag = False

        self.class_names = []
        self.settings = {}

        self.target_display = ""

        self.init_ui()
        self.register_event()
        self.play_back_engine.init_engine()
        self.init_strategy_settings()
        self.load_backtesting_setting()

    def init_ui(self) -> None:
        """""" # noqa
        self.setWindowTitle("K线-复盘功能")

        self.tab: QtWidgets.QTabWidget = QtWidgets.QTabWidget()  # noqa

        self.class_combo = QtWidgets.QComboBox()  # noqa
        self.symbol_line = QtWidgets.QLineEdit("RB9999.XSGE")  # noqa
        # 回测时,输入本地代码后,按回车键自动设置价格跳动和合约乘数
        self.symbol_line.returnPressed.connect(self.set_vt_symbol)

        self.interval_combo = QtWidgets.QComboBox()  # noqa
        for interval in Interval:
            if interval != Interval.TICK:
                self.interval_combo.addItem(interval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(  # noqa
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day
            )
        )
        self.end_date_edit = QtWidgets.QDateEdit(  # noqa
            QtCore.QDate.currentDate()
        )

        self.rate_line = QtWidgets.QLineEdit("0.000025") # noqa
        self.slippage_line = QtWidgets.QLineEdit("0.1")  # noqa
        self.size_line = QtWidgets.QLineEdit("300")   # noqa
        self.pricetick_line = QtWidgets.QLineEdit("0.2")  # noqa
        self.capital_line = QtWidgets.QLineEdit("1000000")  # noqa

        self.inverse_combo = QtWidgets.QComboBox()  # noqa
        self.inverse_combo.addItems(["正向", "反向"])

        self.loading_history_button = QtWidgets.QPushButton("加载历史数据")  # noqa
        self.loading_history_button.clicked.connect(self.start_backtesting)

        self.start_checking_button = QtWidgets.QPushButton("开始复盘")  # noqa
        self.start_checking_button.clicked.connect(self.start_playback)
        self.start_checking_button.setEnabled(False)

        self.backtesting_stop_button = QtWidgets.QPushButton("停止复盘")  # noqa
        self.backtesting_stop_button.clicked.connect(self.stop_playback)
        self.backtesting_stop_button.setEnabled(False)

        self.order_button = QtWidgets.QPushButton("委托记录") # noqa
        self.order_button.clicked.connect(self.show_playback_orders)
        self.order_button.setEnabled(False)

        self.trade_button = QtWidgets.QPushButton("成交记录") # noqa
        self.trade_button.clicked.connect(self.show_playback_trades)
        self.trade_button.setEnabled(False)

        self.daily_button = QtWidgets.QPushButton("每日盈亏") # noqa
        self.daily_button.clicked.connect(self.show_daily_results)
        self.daily_button.setEnabled(False)

        self.playback_report = QtWidgets.QPushButton("复盘报告") # noqa
        self.playback_report.clicked.connect(self.analyse_report)
        self.playback_report.setEnabled(False)

        self.capital_chart_button = QtWidgets.QPushButton("资金图表") # noqa
        self.capital_chart_button.clicked.connect(self.show_capital_chart)
        self.capital_chart_button.setEnabled(False)

        self.my_slider()  # 创建复盘控制速度的滚动条

        for button in [
            self.loading_history_button,
            self.backtesting_stop_button,
            self.start_checking_button,
            self.order_button,
            self.trade_button,
            self.daily_button,
            self.playback_report,
            self.capital_chart_button
        ]:
            button.setFixedHeight(button.sizeHint().height() * 2)

        form = QtWidgets.QFormLayout()
        form.addRow("交易策略", self.class_combo)
        form.addRow("本地代码", self.symbol_line)
        form.addRow("K线周期", self.interval_combo)
        form.addRow("开始日期", self.start_date_edit)
        form.addRow("结束日期", self.end_date_edit)
        form.addRow("手续费率", self.rate_line)
        form.addRow("交易滑点", self.slippage_line)
        form.addRow("合约乘数", self.size_line)
        form.addRow("价格跳动", self.pricetick_line)
        form.addRow("回测资金", self.capital_line)
        form.addRow("合约模式", self.inverse_combo)
        form.addRow("复盘速度控制条", self.Myslider)
        self.Myslider.setMinimumHeight(25)  # 此行代码是为了解决复盘速度控制条无法在服务器上界面正常显示的问题

        result_grid = QtWidgets.QGridLayout()
        result_grid.addWidget(self.trade_button, 0, 0)
        result_grid.addWidget(self.order_button, 0, 1)
        result_grid.addWidget(self.daily_button, 1, 0)
        result_grid.addWidget(self.playback_report, 1, 1)
        result_grid.addWidget(self.capital_chart_button, 2, 0)


        self.log_monitor = QtWidgets.QTextEdit()  # noqa

        left_vbox = QtWidgets.QVBoxLayout()
        left_vbox.addLayout(form)
        left_vbox.addWidget(self.loading_history_button)
        left_vbox.addWidget(self.start_checking_button)
        left_vbox.addWidget(self.backtesting_stop_button)
        left_vbox.addStretch()
        left_vbox.addLayout(result_grid)
        left_vbox.addStretch()
        left_vbox.addWidget(self.log_monitor)

        self.statistics_monitor = StatisticsMonitor()  # noqa

        self.PlayBackCapital_chart = BacktesterChart()  # noqa
        self.capital_chart_dialog = PlayBackReportDialog(self.PlayBackCapital_chart, width=1300, height=900, title="复盘-资金图表")  # noqa


        self.trade_dialog = BacktestingResultDialog(   # noqa
            self.main_engine,
            self.event_engine,
            "复盘成交记录",
            BacktestingTradeMonitor
        )
        self.order_dialog = BacktestingResultDialog(    # noqa
            self.main_engine,
            self.event_engine,
            "复盘委托记录",
            BacktestingOrderMonitor
        )
        self.daily_dialog = BacktestingResultDialog(    # noqa
            self.main_engine,
            self.event_engine,
            "复盘每日盈亏",
            DailyResultMonitor
        )

        # Candle Chart
        # self.candle_dialog = CandleChartDialog()

        # Layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tab)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(left_vbox, stretch=1)
        hbox.addLayout(vbox, stretch=3)

        self.setLayout(hbox)

        self.Myslider.valueChanged.connect(self.set_value_changed)

    def my_slider(self):
        self.Myslider = MyQSlider(self) # noqa
        self.Myslider.setMaximum(32)
        self.Myslider.setMinimum(1)
        self.Myslider.move((self.width() - self.Myslider.width()) / 2, (self.height() - self.Myslider.height()) * 0.2 / 2)
        self.Myslider.setSingleStep(1)  # 设置步长
        self.Myslider.setOrientation(Qt.Horizontal)  # 设置滚动条水平显示
        
    def set_value_changed(self):
        slider_value = int(self.Myslider.value())  # noqa
        self._timer_interval = round(60000 / ( slider_value ** 3), 2)  # noqa
        self.init_timer()
        setting = load_json(self.setting_filename)
        setting["slider_location"] = slider_value
        save_json(self.setting_filename, setting)

    def init_timer(self):
        # 设定定时器
        self.timer = pg.QtCore.QTimer()  # noqa
        # 定时器信号绑定 update_data 函数
        self.timer.timeout.connect(self.update_bar)
        # 定时器间隔self._timer_interval 刷新一次数据
        self.timer.start(self._timer_interval)

    def set_enabled_button(self):
        self.start_checking_button.setEnabled(False)

        self.trade_button.setEnabled(False)
        self.order_button.setEnabled(False)
        self.daily_button.setEnabled(False)
        self.playback_report.setEnabled(False)
        self.capital_chart_button.setEnabled(False)

    def update_bar(self):
        if self._history_write_flag:  # noqa
            if self._history:
                bar = self._history.pop(0)
                chart = self.charts.get(bar.vt_symbol, None)
                if chart:
                    chart.update_bar(bar)  # 更新一个数据,画一个bar柱状图。
                    self.play_back_engine.update_trade(bar)  # 绘制策略开平仓标记符号。
            else:
                self.timer.stop()  # 定时器结束
                self.start_checking_button.setEnabled(True)
                self.write_log("复盘完成")
                self._history_write_flag = False  # 清除加载数据的标志
                self.loading_history_button.setEnabled(True)

                self.trade_button.setEnabled(True)
                self.order_button.setEnabled(True)
                self.daily_button.setEnabled(True)
                self.playback_report.setEnabled(True)
                self.capital_chart_button.setEnabled(True)

    def create_chart(self) -> ChartWidget: # noqa
        """""" # noqa
        chart = ChartWidget()
        chart.add_plot("candle", hide_x_axis=True)
        chart.add_plot("volume", maximum_height=200)
        chart.add_item(CandleItem, "candle", "candle")
        chart.add_item(VolumeItem, "volume", "volume")
        chart.add_cursor()
        return chart

    def start_playback(self) -> None:
        """new_chart""" # noqa
        vt_symbol = self.symbol_line.text()
        self.write_log(f"{vt_symbol}-开始复盘")

        self.set_enabled_button()  # 设置对应按钮为不可点击状态
        self.loading_history_button.setEnabled(False)

        self.play_back_engine.trade_data.clear()  # 清除画交易标记散点图的数据

        self.tab.removeTab(0)  # 删除tab
        if self.charts.get(vt_symbol):
            self.charts.pop(vt_symbol)

        self.bgs[vt_symbol] = BarGenerator(self.on_bar)

        chart = self.create_chart()  # 创建个ChartWidget
        self.charts[vt_symbol] = chart
        self.play_back_engine.create_scatter_plot_item(chart)  # 创建散点图画图对象

        self.tab.addTab(chart, vt_symbol)   # 把chart放到self.tab的名为vt_symbol选项中去

        # 获取历史数据
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        interval = self.interval_combo.currentText()
        self.play_back_engine.query_history(
            vt_symbol,
            Interval(interval),
            start,
            end
        )

        self.init_timer()  # 初始化个定时器

    def register_event(self) -> None:
        """"""  # noqa
        self.signal_tick.connect(self.process_tick_event)
        self.signal_history.connect(self.process_history_event)
        self.signal_log.connect(self.process_log_event)
        self.signal_play_back_backtesting_finished.connect(self.process_backtesting_finished_event)

        self.event_engine.register(EVENT_PLAY_BACK_CHART_HISTORY, self.signal_history.emit)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        self.event_engine.register(EVENT_PLAY_BACK_CHART_BACKTESTER_LOG, self.signal_log.emit)
        self.event_engine.register(EVENT__PLAY_BACK_CHART_BACKTESTING_FINISHED, self.signal_play_back_backtesting_finished.emit)

    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        bg = self.bgs.get(tick.vt_symbol, None)

        if bg:
            bg.update_tick(tick)

            chart = self.charts[tick.vt_symbol]
            bar = copy(bg.bar)
            bar.datetime = bar.datetime.replace(second=0, microsecond=0)
            chart.update_bar(bar)

    def process_history_event(self, event: Event) -> None:
        """"""
        history: List[BarData] = event.data
        if not history:
            return
        bar = history[0]
        self._history = copy(history[1:])  
        history = history[0:1]
        chart = self.charts.get(bar.vt_symbol, None)
        chart.update_history(history)
        self._history_write_flag = True


        # # 订阅行情产生tick数据
        # contract = self.main_engine.get_contract(bar.vt_symbol)
        # req = SubscribeRequest(
        #     contract.symbol,
        #     contract.exchange
        # )
        # self.main_engine.subscribe(req, contract.gateway_name)

    def on_bar(self, bar: BarData):  # noqa
        """"""
        chart = self.charts[bar.vt_symbol]
        chart.update_bar(bar)

    def init_strategy_settings(self):
        """"""
        self.class_names = self.play_back_engine.get_strategy_class_names()
        for class_name in self.class_names:
            setting = self.backtester_engine.get_default_setting(class_name)
            self.settings[class_name] = setting

        self.class_combo.addItems(self.class_names)

    def set_vt_symbol(self) -> None:
        """
        回测时，自动调整该品种的合约乘数与价格跳动
        """
        vt_symbol = str(self.symbol_line.text())

        if not vt_symbol:
            return

        if "." not in vt_symbol:
            symbol_letter = get_letter_from_symbol(vt_symbol)
            exchange = SymbolExchange.get(symbol_letter, "")
            self.symbol_line.setText(vt_symbol + '.' + exchange)

        vt_symbol = str(self.symbol_line.text())

        if vt_symbol and ("." in vt_symbol):
            symbol = vt_symbol.split('.')[0]
            symbol_letter = get_letter_from_symbol(symbol)

            size = ContractMultiplier.get(symbol_letter, False)
            if size:
                self.size_line.setText(str(size))

            price_tick = ContractPricePick.get(symbol_letter, False)
            if price_tick:
                self.pricetick_line.setText(str(price_tick))

            commisstion = SymbolCommission.get(symbol_letter, False)
            if commisstion and (commisstion < 0.1):
                self.rate_line.setText(str(commisstion))

    def load_backtesting_setting(self):
        """"""
        setting = load_json(self.setting_filename)
        if not setting:
            return

        self.class_combo.setCurrentIndex(
            self.class_combo.findText(setting["class_name"])
        )

        self.symbol_line.setText(setting["vt_symbol"])

        self.interval_combo.setCurrentIndex(
            self.interval_combo.findText(setting["interval"])
        )

        self.rate_line.setText(str(setting["rate"]))
        self.slippage_line.setText(str(setting["slippage"]))
        self.size_line.setText(str(setting["size"]))
        self.pricetick_line.setText(str(setting["pricetick"]))
        self.capital_line.setText(str(setting["capital"]))

        if not setting["inverse"]:
            self.inverse_combo.setCurrentIndex(0)
        else:
            self.inverse_combo.setCurrentIndex(1)
        if "start" in setting and setting["start"]:
            self.start_date_edit.setDate(datetime.strptime(setting["start"], '%Y/%m/%d').date())
            self.end_date_edit.setDate(datetime.strptime(setting["end"], '%Y/%m/%d').date())

        slider_location = setting.get("slider_location", None)
        if slider_location:
            self.Myslider.setValue(slider_location)  # 设置滚动位置
        # 初始化self._timer_interval的值
        self._timer_interval = round(60000 / (int(self.Myslider.value()) ** 3), 2)   # noqa

    def process_log_event(self, event: Event):
        """"""
        msg = event.data
        self.write_log(msg)

    def write_log(self, msg):
        """"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{msg}"
        self.log_monitor.append(msg)

    def process_backtesting_finished_event(self, event: Event):
        """"""
        statistics = self.backtester_engine.get_result_statistics()
        self.statistics_monitor.set_data(statistics)

        df = self.backtester_engine.get_result_df()
        self.PlayBackCapital_chart.set_data(df)

        # self.trade_button.setEnabled(True)
        # self.order_button.setEnabled(True)
        # self.daily_button.setEnabled(True)
        # self.playback_report.setEnabled(True)
        # self.capital_chart_button.setEnabled(True)
        # self.candle_button.setEnabled(True)

        self.start_checking_button.setEnabled(True)
        self.backtesting_stop_button.setEnabled(True)


    def start_backtesting(self):
        """"""
        class_name = self.class_combo.currentText()
        vt_symbol = self.symbol_line.text()
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        size = float(self.size_line.text())
        pricetick = float(self.pricetick_line.text())
        capital = float(self.capital_line.text())

        self.tab.removeTab(0)  # 删除tab
        if self.charts.get(vt_symbol):
            self.charts.pop(vt_symbol)

        if self.inverse_combo.currentText() == "正向":
            inverse = False
        else:
            inverse = True

        # Save backtesting parameters
        backtesting_setting = {
            "class_name": class_name,
            "vt_symbol": vt_symbol,
            "interval": interval,
            "rate": rate,
            "slippage": slippage,
            "size": size,
            "pricetick": pricetick,
            "capital": capital,
            "inverse": inverse,
            "start": start.strftime("%Y/%m/%d"),
            "end": end.strftime("%Y/%m/%d")
        }
        backtesting_setting.setdefault("slider_location", int(self.Myslider.value()))  # 把进度条的位置值保存到json文件中
        save_json(self.setting_filename, backtesting_setting)

        # Get strategy setting
        old_setting = self.settings[class_name]
        dialog = BacktestingSettingEditor(class_name, old_setting)
        i = dialog.exec()
        if i != dialog.Accepted:
            return

        new_setting = dialog.get_setting()
        self.settings[class_name] = new_setting

        result = self.play_back_engine.start_backtesting(
            class_name,
            vt_symbol,
            interval,
            start,
            end,
            rate,
            slippage,
            size,
            pricetick,
            capital,
            inverse,
            new_setting
        )

        if result:
            self.set_enabled_button()  # 设置对应的按钮为不可点击状态
            self.backtesting_stop_button.setEnabled(False)
            # self.candle_button.setEnabled(False)

            self.trade_dialog.clear_data()
            self.order_dialog.clear_data()
            self.daily_dialog.clear_data()
            self.statistics_monitor.clear_data()
            self.PlayBackCapital_chart.clear_data()
            # self.candle_dialog.clear_data()
            # self.trades.clear()
            # self.orders.clear()

    def stop_playback(self):
        self.write_log("停止复盘")
        self.timer.stop()  # 定时器停止
        self.start_checking_button.setEnabled(True)
        self.loading_history_button.setEnabled(True)

    def show(self):
        """"""
        self.showMaximized()

    def show_playback_trades(self):
        """"""
        if not self.trade_dialog.is_updated():
            trades = self.backtester_engine.get_all_trades()
            self.trade_dialog.update_data(trades)

        self.trade_dialog.exec_()

    def show_playback_orders(self):
        """"""
        if not self.order_dialog.is_updated():
            orders = self.backtester_engine.get_all_orders()
            self.order_dialog.update_data(orders)

        self.order_dialog.exec_()

    def show_daily_results(self):
        """"""
        if not self.daily_dialog.is_updated():
            results = self.backtester_engine.get_all_daily_results()
            self.daily_dialog.update_data(results)
            # end_pos_list = [int(obj.end_pos) for obj in results]
            # print(min(end_pos_list), max(end_pos_list))  # 输出最小开仓数量和最开仓数量
        self.daily_dialog.exec_()

    def analyse_report(self):
        self.playBack_dialog = PlayBackReportDialog(self.statistics_monitor)  # noqa
        self.playBack_dialog.exec_()

    def show_capital_chart(self):
        # 如果self.capital_chart_dialog放在此时创建的话,会发现self.PlayBackCapital_chart无法布局到self.capital_chart_dialog中去
        # 只有放在刚创建self.PlayBackCapital_chart对象的后一行代码中才能
        # self.capital_chart_dialog = PlayBackReportDialog(self.PlayBackCapital_chart, width=1300, height=950, title="资金图表")  # noqa
        self.capital_chart_dialog.exec_()


class StatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "start_date": "首个交易日",
        "end_date": "最后交易日",

        "total_days": "总交易日",
        "profit_days": "盈利交易日",
        "loss_days": "亏损交易日",

        "capital": "起始资金",
        "end_balance": "结束资金",

        "total_return": "总收益率",
        "annual_return": "年化收益",
        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤",

        "total_net_pnl": "总盈亏",
        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "total_turnover": "总成交额",
        "total_trade_count": "总成交笔数",

        "daily_net_pnl": "日均盈亏",
        "daily_commission": "日均手续费",
        "daily_slippage": "日均滑点",
        "daily_turnover": "日均成交额",
        "daily_trade_count": "日均成交笔数",

        "daily_return": "日均收益率",
        "return_std": "收益标准差",
        "sharpe_ratio": "夏普比率",

        "win_ratio": "胜率",
        "win_loss_ratio": "盈亏比",
        "return_risk_ratio": "收益风险比",
        "return_drawdown_ratio": "收益回撤比",
        "real_yields": "实际收益率"
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setRowCount(len(self.KEY_NAME_MAP))
        self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.setColumnCount(1)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for row, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            self.setItem(row, 0, cell)
            self.cells[key] = cell

    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""
        data["capital"] = f"{data['capital']:,.2f}"
        data["end_balance"] = f"{data['end_balance']:,.2f}"
        data["total_return"] = f"{data['total_return']:,.2f}%"
        data["annual_return"] = f"{data['annual_return']:,.2f}%"
        data["max_drawdown"] = f"{data['max_drawdown']:,.2f}"
        data["max_ddpercent"] = f"{data['max_ddpercent']:,.2f}%"
        data["total_net_pnl"] = f"{data['total_net_pnl']:,.2f}"
        data["total_commission"] = f"{data['total_commission']:,.2f}"
        data["total_slippage"] = f"{data['total_slippage']:,.2f}"
        data["total_turnover"] = f"{data['total_turnover']:,.2f}"
        data["daily_net_pnl"] = f"{data['daily_net_pnl']:,.2f}"
        data["daily_commission"] = f"{data['daily_commission']:,.2f}"
        data["daily_slippage"] = f"{data['daily_slippage']:,.2f}"
        data["daily_turnover"] = f"{data['daily_turnover']:,.2f}"
        data["daily_return"] = f"{data['daily_return']:,.2f}%"
        data["return_std"] = f"{data['return_std']:,.2f}%"
        data["sharpe_ratio"] = f"{data['sharpe_ratio']:,.2f}"
        data["return_drawdown_ratio"] = f"{data['return_drawdown_ratio']:,.2f}"

        data["win_ratio"""] = f"{data['win_ratio']}"
        data["win_loss_ratio"] = f"{data['win_loss_ratio']}"
        data["return_risk_ratio"] = f"{data['return_risk_ratio']:,.2f}"
        data["real_yields"] = f"{data['real_yields']}"

        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))


class BacktestingSettingEditor(QtWidgets.QDialog):
    """
    For creating new strategy and editing strategy parameters.
    """

    def __init__(
        self, class_name: str, parameters: dict
    ):
        """"""
        super(BacktestingSettingEditor, self).__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"策略参数配置：{self.class_name}")
        button_text = "确定"
        parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)

            edit = QtWidgets.QLineEdit(str(value))
            if type_ is int:
                validator = QtGui.QIntValidator()
                edit.setValidator(validator)
            elif type_ is float:
                validator = QtGui.QDoubleValidator()
                edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)

            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow(button)

        widget = QtWidgets.QWidget()
        widget.setLayout(form)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroll)
        self.setLayout(vbox)

    def get_setting(self):
        """"""
        setting = {}

        for name, tp in self.edits.items():
            edit, type_ = tp
            value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            else:
                value = type_(value_text)

            setting[name] = value

        return setting



class BacktestingTradeMonitor(BaseMonitor):
    """
    Monitor for backtesting trade data.
    """

    headers = {
        "tradeid": {"display": "成交号 ", "cell": BaseCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "datetime": {"display": "时间", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class BacktestingOrderMonitor(BaseMonitor):
    """
    Monitor for backtesting order data.
    """

    headers = {
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "type": {"display": "类型", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "总数量", "cell": BaseCell, "update": False},
        "traded": {"display": "已成交", "cell": BaseCell, "update": False},
        "status": {"display": "状态", "cell": EnumCell, "update": False},
        "datetime": {"display": "时间", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class DailyResultMonitor(BaseMonitor):
    """
    Monitor for backtesting daily result.
    """

    headers = {
        "date": {"display": "日期", "cell": BaseCell, "update": False},
        "trade_count": {"display": "成交笔数", "cell": BaseCell, "update": False},
        "start_pos": {"display": "开盘持仓", "cell": BaseCell, "update": False},
        "end_pos": {"display": "收盘持仓", "cell": BaseCell, "update": False},
        "turnover": {"display": "成交额", "cell": BaseCell, "update": False},
        "commission": {"display": "手续费", "cell": BaseCell, "update": False},
        "slippage": {"display": "滑点", "cell": BaseCell, "update": False},
        "trading_pnl": {"display": "交易盈亏", "cell": BaseCell, "update": False},
        "holding_pnl": {"display": "持仓盈亏", "cell": BaseCell, "update": False},
        "total_pnl": {"display": "总盈亏", "cell": BaseCell, "update": False},
        "net_pnl": {"display": "净盈亏", "cell": BaseCell, "update": False},
    }

class BacktestingResultDialog(QtWidgets.QDialog):
    """
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        title: str,
        table_class: QtWidgets.QTableWidget
    ):
        """"""
        super().__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine
        self.title = title
        self.table_class = table_class

        self.updated = False

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle(self.title)
        self.resize(1100, 600)
        # QDialog设置显示最大化、最小化、关闭按钮。
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.table = self.table_class(self.main_engine, self.event_engine)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.table)

        self.setLayout(vbox)

    def clear_data(self):
        """"""
        self.updated = False
        self.table.setRowCount(0)

    def update_data(self, data: list):
        """"""
        self.updated = True

        data.reverse()
        for obj in data:
            self.table.insert_new_row(obj)

    def is_updated(self):
        """"""
        return self.updated


class BacktesterChart(pg.GraphicsWindow):
    """"""

    def __init__(self):
        """"""
        super().__init__(title="资金-图表")

        self.dates = {}

        self.init_ui()

    def init_ui(self):
        """"""
        pg.setConfigOptions(antialias=True)

        # Create plot widgets
        self.balance_plot = self.addPlot(
            title="账户净值",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.drawdown_plot = self.addPlot(
            title="净值回撤",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.pnl_plot = self.addPlot(
            title="每日盈亏",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.distribution_plot = self.addPlot(title="盈亏分布")

        # Add curves and bars on plot widgets
        self.balance_curve = self.balance_plot.plot(
            pen=pg.mkPen("#ffc107", width=3)
        )

        dd_color = "#303f9f"
        self.drawdown_curve = self.drawdown_plot.plot(
            fillLevel=-0.3, brush=dd_color, pen=dd_color
        )

        profit_color = 'r'
        loss_color = 'g'
        self.profit_pnl_bar = pg.BarGraphItem(
            x=[], height=[], width=0.3, brush=profit_color, pen=profit_color
        )
        self.loss_pnl_bar = pg.BarGraphItem(
            x=[], height=[], width=0.3, brush=loss_color, pen=loss_color
        )
        self.pnl_plot.addItem(self.profit_pnl_bar)
        self.pnl_plot.addItem(self.loss_pnl_bar)

        distribution_color = "#6d4c41"
        self.distribution_curve = self.distribution_plot.plot(
            fillLevel=-0.3, brush=distribution_color, pen=distribution_color
        )

    def clear_data(self):
        """"""
        self.balance_curve.setData([], [])
        self.drawdown_curve.setData([], [])
        self.profit_pnl_bar.setOpts(x=[], height=[])
        self.loss_pnl_bar.setOpts(x=[], height=[])
        self.distribution_curve.setData([], [])

    def set_data(self, df):
        """"""
        if df is None:
            return

        count = len(df)

        self.dates.clear()
        for n, date in enumerate(df.index):
            self.dates[n] = date

        # Set data for curve of balance and drawdown
        self.balance_curve.setData(df["balance"])
        self.drawdown_curve.setData(df["drawdown"])

        # Set data for daily pnl bar
        profit_pnl_x = []
        profit_pnl_height = []
        loss_pnl_x = []
        loss_pnl_height = []

        for count, pnl in enumerate(df["net_pnl"]):
            if pnl >= 0:
                profit_pnl_height.append(pnl)
                profit_pnl_x.append(count)
            else:
                loss_pnl_height.append(pnl)
                loss_pnl_x.append(count)

        self.profit_pnl_bar.setOpts(x=profit_pnl_x, height=profit_pnl_height)
        self.loss_pnl_bar.setOpts(x=loss_pnl_x, height=loss_pnl_height)

        # Set data for pnl distribution
        hist, x = np.histogram(df["net_pnl"], bins="auto")
        x = x[:-1]
        self.distribution_curve.setData(x, hist)


class DateAxis(pg.AxisItem):
    """Axis for showing date data"""

    def __init__(self, dates: dict, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)
        self.dates = dates

    def tickStrings(self, values, scale, spacing):
        """"""
        strings = []
        for v in values:
            dt = self.dates.get(v, "")
            strings.append(str(dt))
        return strings


class PlayBackReportDialog(QtWidgets.QDialog):

    def __init__(self, increase_widget,  width=400, height=900, title="复盘报告"):
        super(PlayBackReportDialog, self).__init__()
        self.resize(width, height)
        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(increase_widget)
        self.setLayout(vbox)
