
from copy import copy
from datetime import datetime
import pyqtgraph as pg
from PyQt5 import QtWidgets, sip
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QScrollArea, QTableWidget, QTableWidgetItem
from tzlocal import get_localzone
from pandas import to_datetime
from vnpy.chart import CandleItem, VolumeItem
from vnpy.chart.base import YELLOW_COLOR, RED_COLOR, GREY_COLOR, WHITE_COLOR
from vnpy.trader.constant import Direction, Offset, Exchange
from vnpy.trader.object import TradeData
from vnpy.trader.ui import QtCore, QtGui
from vnpy.trader.utility import get_contrast_direction
from vnpy.usertools.beautiful_chart import NewChartWidget
from vnpy.usertools.chart_items import LineItem, SmaItem, OrderItem, TradeItem, MacdItem, RsiItem


class NewCandleChartDialog(QtWidgets.QDialog):
    """
    """

    def __init__(self):
        """"""
        super().__init__()
        self.updated = False
        self.dt_ix_map = {}
        self.ix_bar_map = {}
        self.high_price = 0
        self.low_price = 0
        self.price_range = 0
        self.items = []
        self.symbol: str = ""
        self.exchange: str = ""
        self.list_trades: list = []
        self.list_history: list = []
        self.list_trades_record: list = []
        # 存储btn对象
        self.list_btn: list = []
        # 存储infinite_line对象
        self.list_infinite_line: list = []

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("回测K线图表")
        # QDialog设置显示最大化、最小化、关闭按钮。
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # Create chart widget
        self.chart = NewChartWidget()
        # self.chart = ChartWidget()
        self.chart.add_plot("candle", hide_x_axis=True)
        self.chart.add_plot("volume", maximum_height=120)
        self.chart.add_plot_axis("candle")
        self.chart.add_item(CandleItem, "candle", "candle")
        self.chart.add_item(SmaItem, "sma", "candle")
        self.chart.add_item(VolumeItem, "volume", "volume")

        self.chart.add_item(LineItem, "line", "candle")
        self.chart.add_item(OrderItem, "order", "candle")
        self.chart.add_item(TradeItem, "trade", "candle")

        # 侧边栏单个查看成记录
        self.groupbox_left = QtWidgets.QGroupBox("成交单信息")
        # 垂直布局对象(动态添加按钮)
        self.groupbox_vbox = QtWidgets.QVBoxLayout()

        self.main_btn = QPushButton('显示全部成交单', self)
        self.main_btn.setCheckable(True)
        self.main_btn.setChecked(True)
        self.main_btn.clicked[bool].connect(self.show_all_trades_record)

        self.groupbox_vbox.addWidget(self.main_btn)

        self.groupbox_left.setLayout(self.groupbox_vbox)

        self.scroll_left = QScrollArea()
        self.scroll_left.setFixedWidth(400)
        self.scroll_left.setWidgetResizable(True)
        self.scroll_left.setWidget(self.groupbox_left)

        # 创建RSI附图及绘图部件
        self.chart.add_plot("rsi", maximum_height=120)
        self.chart.add_item(RsiItem, "rsi", "rsi")

        # 创建MACD附图及绘图部件
        self.chart.add_plot("macd", maximum_height=200)
        self.chart.add_item(MacdItem, "macd", "macd")

        # 创建最新价格线
        self.chart.add_last_price_line()

        vbox = QtWidgets.QVBoxLayout()
        # 创建 qtablewidget
        self.list_columns = ['首个交易日', '最后交易日', '总交易日', '盈利交易日', '亏损交易日', '起始资金', '结束资金',
                             '总收益率', '年化收益', '最大回撤', '百分比最大回撤', '最长回撤天数', '总盈亏', '总手续费',
                             '总滑点', '总成交金额', '总成交笔数', '日均盈亏', '日均手续费', '日均滑点', '日均成交金额',
                             '日均成交笔数', '日均收益率', '收益标准差', 'Sharpe Ratio', '收益回撤比']

        self.list_columns_english = ['start_date', 'end_date', 'total_days', 'profit_days', 'loss_days', 'capital', 'end_balance',
                                     'total_return', 'annual_return', 'max_drawdown', 'max_ddpercent', 'max_drawdown_duration', 'total_net_pnl', 'total_commission',
                                     'total_slippage', 'total_turnover', 'total_trade_count', 'daily_net_pnl', 'daily_commission', 'daily_slippage', 'daily_turnover',
                                     'daily_trade_count', 'daily_return', 'return_std', 'sharpe_ratio', 'return_drawdown_ratio']

        self.tbwg = QTableWidget(1, len(self.list_columns), self)
        self.tbwg.setHorizontalHeaderLabels(self.list_columns)
        self.tbwg.verticalHeader().setVisible(False)
        self.tbwg.setEditTriggers(self.tbwg.NoEditTriggers)
        # 创建光标对象
        self.chart.add_cursor()

        # Create help widget
        text1 = "红色虚线 —— 盈利交易"
        label1 = QtWidgets.QLabel(text1)
        label1.setStyleSheet("color:red;font:bold 12px")

        text2 = "绿色虚线 —— 亏损交易"
        label2 = QtWidgets.QLabel(text2)
        label2.setStyleSheet("color:#00FF00;font:bold 12px")

        text3 = "黄色向上箭头 —— 买入开仓 Buy"
        label3 = QtWidgets.QLabel(text3)
        label3.setStyleSheet("color:yellow;font:bold 12px")

        text4 = "黄色向下箭头 —— 卖出平仓 Sell"
        label4 = QtWidgets.QLabel(text4)
        label4.setStyleSheet("color:yellow;font:bold 12px")

        text5 = "紫红向下箭头 —— 卖出开仓 Short"
        label5 = QtWidgets.QLabel(text5)
        label5.setStyleSheet("color:magenta;font:bold 12px")

        text6 = "紫红向上箭头 —— 买入平仓 Cover"
        label6 = QtWidgets.QLabel(text6)
        label6.setStyleSheet("color:magenta;font:bold 12px")

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addStretch()
        hbox1.addWidget(label1)
        hbox1.addStretch()
        hbox1.addWidget(label2)
        hbox1.addStretch()

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addStretch()
        hbox2.addWidget(label3)
        hbox2.addStretch()
        hbox2.addWidget(label4)
        hbox2.addStretch()

        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addStretch()
        hbox3.addWidget(label5)
        hbox3.addStretch()
        hbox3.addWidget(label6)
        hbox3.addStretch()
        vbox.addWidget(self.tbwg, stretch=1)
        vbox.addWidget(self.chart, stretch=10)

        # vbox.addLayout(hbox1)
        # vbox.addLayout(hbox2)
        # vbox.addLayout(hbox3)

        # Add scatter item for showing tradings
        self.trade_scatter = pg.ScatterPlotItem()
        self.candle_plot = self.chart.get_plot("candle")
        self.candle_plot.addItem(self.trade_scatter)
        self.candle_left = self.chart.plot_left

        # Set layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.scroll_left)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

    def update_history(self, history: list):
        """更新历史数据时,把相关的数据设置到变量中去,好能够在其他地方使用"""
        self.updated = True
        self.chart.update_history(history)
        self.list_history = history

        for ix, bar in enumerate(history):
            self.ix_bar_map[ix] = bar
            self.symbol = bar.symbol
            self.exchange = bar.exchange
            self.setWindowTitle(f"回测_{self.symbol}.{self.exchange.value}_K线图表")
            self.dt_ix_map[bar.datetime] = ix

            if not self.high_price:
                self.high_price = bar.high_price
                self.low_price = bar.low_price
            else:
                self.high_price = max(self.high_price, bar.high_price)
                self.low_price = min(self.low_price, bar.low_price)

        self.price_range = self.high_price - self.low_price

    def update_trades(self, trades: list, show_lines=False):
        """"""
        trade_pairs = generate_trade_pairs(trades)
        candle_plot = self.chart.get_plot("candle")
        # scatter_data = []
        # y_adjustment = self.price_range * 0.001   # y轴范围调整
        self.chart._trade_line_item = []
        for d in trade_pairs:
            open_ix = self.dt_ix_map[d["open_dt"]]
            close_ix = self.dt_ix_map[d["close_dt"]]
            open_price = d["open_price"]
            close_price = d["close_price"]

            # Trade Line(交易连接线)
            x = [open_ix, close_ix]
            y = [open_price, close_price]

            if d["direction"] == Direction.LONG and close_price >= open_price:
                color = "r"
            elif d["direction"] == Direction.SHORT and close_price <= open_price:
                color = "r"
            else:
                color = "g"

            pen = pg.mkPen(color, width=1.5, style=QtCore.Qt.DashLine)
            item = pg.PlotCurveItem(x, y, pen=pen)

            self.items.append(item)
            self.chart._trade_line_item.append(item)
            candle_plot.addItem(item)

            # Trade Scatter(交易散点图)
            # open_bar = self.ix_bar_map[open_ix]
            # close_bar = self.ix_bar_map[close_ix]
            # if d["direction"] == Direction.LONG:
            #     scatter_color = "yellow"
            #     open_symbol = "t1"
            #     close_symbol = "t"
            #     open_side = 1
            #     close_side = -1
            #     open_y = open_bar.low_price
            #     close_y = close_bar.high_price
            # else:
            #     scatter_color = "magenta"
            #     open_symbol = "t"
            #     close_symbol = "t1"
            #     open_side = -1
            #     close_side = 1
            #     open_y = open_bar.high_price
            #     close_y = close_bar.low_price
            # pen = pg.mkPen(QtGui.QColor(scatter_color))
            # brush = pg.mkBrush(QtGui.QColor(scatter_color))
            # size = 10
            # open_scatter = {
            #     "pos": (open_ix, open_y - open_side * y_adjustment),
            #     "size": size,
            #     "pen": pen,
            #     "brush": brush,
            #     "symbol": open_symbol
            # }
            # close_scatter = {
            #     "pos": (close_ix, close_y - close_side * y_adjustment),
            #     "size": size,
            #     "pen": pen,
            #     "brush": brush,
            #     "symbol": close_symbol
            # }
            # scatter_data.append(open_scatter)
            # scatter_data.append(close_scatter)

            # # Trade text(框住交易散点图图形的中括号框)
            # volume = d["volume"]
            # text_color = QtGui.QColor(scatter_color)
            # open_text = pg.TextItem(f"[{volume}]", color=text_color, anchor=(0.5, 0.5))
            # close_text = pg.TextItem(f"[{volume}]", color=text_color, anchor=(0.5, 0.5))
            # open_text.setPos(open_ix, open_y - open_side * y_adjustment * 3)
            # close_text.setPos(close_ix, close_y - close_side * y_adjustment * 3)
            # self.items.append(open_text)
            # self.items.append(close_text)
            # candle_plot.addItem(open_text)
            # candle_plot.addItem(close_text)


        trade_data = []
        if not len(self.list_trades):
            self.list_trades = trades

        labelOpts = {'color': YELLOW_COLOR, 'movable': True, 'fill': (0, 0, 200, 100), 'rotateAxis': [0.9, 0], 'position': 0.6}
        labelOpts_close = {'color': YELLOW_COLOR, 'movable': True, 'fill': (0, 0, 200, 100), 'rotateAxis': [0.9, 0], 'position': 0.5}

        for trade in trades:
            ix = self.dt_ix_map[trade.datetime]
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

            # 画开仓平仓止盈止损线
            labelOpts['position'] -= 0.1
            labelOpts_close['position'] -= 0.1
            if (trade.offset == Offset.OPEN) and hasattr(trade, 'win_price') and show_lines:
                labelOpts['color'] = YELLOW_COLOR
                open_line = pg.InfiniteLine(pos=trade.price, angle=0, label=f'开仓价: {round(trade.price,2)}', labelOpts=labelOpts)
                labelOpts['color'] = RED_COLOR
                win_line = pg.InfiniteLine(pos=trade.win_price, angle=0, pen=labelOpts['color'], label=f'止盈价: {round(trade.win_price,2)}', labelOpts=labelOpts)
                labelOpts['color'] = GREY_COLOR
                loss_line = pg.InfiniteLine(pos=trade.loss_price, angle=0, pen=labelOpts['color'], label=f'止损价: {round(trade.loss_price,2)}', labelOpts=labelOpts)
                labelOpts_close['color'] = WHITE_COLOR
                price_sell_line = pg.InfiniteLine(pos=trade.price_sell, angle=0, pen=labelOpts_close['color'], label=f'平仓价: {round(trade.price_sell,2)}', labelOpts=labelOpts_close)
                self.candle_plot.addItem(open_line)
                self.candle_plot.addItem(win_line)
                self.candle_plot.addItem(loss_line)
                self.candle_plot.addItem(price_sell_line)
                self.list_infinite_line.extend([open_line, win_line, loss_line, price_sell_line])

                # 点击按钮时光标自动跳到到达对应的区域
                min_ix = max(self.dt_ix_map[trade.datetime] - 50, 0)
                max_ix = min(self.dt_ix_map[trade.datetime] + 50, max(list(self.dt_ix_map.values())))

                for plot in self.chart._plots.values():
                    plot.setRange(xRange=(min_ix, max_ix), padding=0)

            trade_data.append(scatter)

        self.trade_scatter.setData(trade_data)
        # trade_scatter = pg.ScatterPlotItem(scatter_data)
        # self.items.append(trade_scatter)
        # candle_plot.addItem(trade_scatter)

    def update_balance(self, series_balance):
        """把资金曲线设置到k线图组件上"""
        # 由于前面初始化时的几天,传过来的series_balance中没有,所以添加上去。
        for history in self.list_history:
            if history.datetime.date() not in series_balance.index:
                series_balance.loc[history.datetime.date()] = series_balance[0]
        series_balance = series_balance.sort_index()  # 排序
        series_balance = series_balance.bfill()  # 缺失值填充

        # 如果要想把资金曲线设置在k线图上,必须写上下行代码。参考http://bazaar.launchpad.net/~luke-campagnola/pyqtgraph/inp/view/head:/examples/MultiplePlotAxes.py。
        # 参考网址：https://www.pythonheidong.com/blog/article/475455/82679f0b9a8a97c959d4/
        self.candle_plot.vb.sigResized.connect(self.updateViews)
        # 为什么没有传x轴坐标值,ChartWidget.add_plot_axis中有说明。
        self.chart.candle_left_item = self.candle_left_item = pg.PlotCurveItem(series_balance.tolist(), pen=pg.mkPen("#ffc107", width=2))
        self.candle_left.setMenuEnabled(False)  # 注释默认上下文菜单
        self.candle_left.addItem(self.candle_left_item)

    def updateViews(self):
        """视图调整事件处理函数,如果要想把资金曲线设置在k线图上,必须设置此函数"""
        # 设置self.candle_left的位置/大小和self.candle_plot一样。
        self.candle_left.setGeometry(self.candle_plot.vb.sceneBoundingRect())
        # 需要重新更新链接轴，因为当视图有不同的形状时，就会被调用。
        self.candle_left.linkedViewChanged(self.candle_plot.vb, self.candle_left.XAxis)

    def update_backester_result(self, backtester_result):
        """往k线图组件对应区域上设置回测结果"""
        for i, value in enumerate(self.list_columns_english):
            self.tbwg.setItem(0, i, QTableWidgetItem(str(backtester_result[value])))

    def update_trades_record(self, trades_record):
        """以成交单信息创建按钮的形式设置到k线图组件对应区域上"""
        trades_record.reverse()
        self.list_trades_record = trades_record
        for num, trade in enumerate(trades_record):
            btn = QPushButton(f"T:{trade['date_open'].strftime('%Y%m%d')} O_P:{round(trade['price_open'],1)} C_P:{round(trade['price_sell'],1)} R:{round(trade['price_profits'],1)}", self)
            btn.setObjectName(str(num))
            btn.setCheckable(True)
            btn.clicked[bool].connect(self.one_trade_btn_click)
            self.list_btn.append(btn)  # 添加btn按钮
            self.groupbox_vbox.addWidget(btn)

    def clear_data(self):
        """"""
        self.updated = False
        candle_plot = self.chart.get_plot("candle")
        for item in self.items:
            candle_plot.removeItem(item)
        self.items.clear()
        self.chart.clear_all()
        self.dt_ix_map.clear()
        self.ix_bar_map.clear()
        self.trade_scatter.clear()
        self.symbol = ""
        self.exchange = ""
        self.list_trades = []  # trades交易记录
        # 删除净值曲线
        if hasattr(self, "candle_left_item"):
            self.candle_left.removeItem(self.candle_left_item)
        self.list_history = []   # history交易记录
        self.list_trades_record = []  # 成交记录
        # 删除list_btn
        for i in range(len(self.list_btn)):
            btn = self.list_btn.pop(0)
            self.groupbox_vbox.removeWidget(btn)
            sip.delete(btn)
        for line in self.list_infinite_line:  # 删除线条操作
            self.candle_plot.removeItem(line)

        self.main_btn.setChecked(True)

    def clear_trades_data(self):
        """清除交易记录"""
        self.trade_scatter.clear()  # 清除散点图数据
        for line in self.list_infinite_line:  # 删除线条操作
            self.candle_plot.removeItem(line)
        for item in self.chart._trade_line_item:  # 删除交易连接线
            self.candle_plot.removeItem(item)

    def is_updated(self):
        """"""
        return self.updated
    
    def show_all_trades_record(self, pressed):
        """显示全部成交单按钮的点击事件处理函数"""
        # 如果传过来值为True则显示散点图(交易信号的画图符号),否则清除交易记录数据

        # for item in self.chart._trade_line_item:  # 删除点击单个按钮的交易连接线
            # self.candle_plot.removeItem(item)

        self.clear_trades_data()  # 先清除,再考虑是否从新画。

        if pressed:
            # 设置单个子按钮都为未选中状态和按钮的背景色设置成灰色。
            for each_pushbutton in self.list_btn:
                each_pushbutton.setChecked(False)
                each_pushbutton.setStyleSheet("QPushButton{background:(100, 100, 100)}")
            self.update_trades(self.list_trades)

            if self.chart.trade_connection_line_hidden_flag:  # 决定是否显示交易盈亏曲线
                for item in self.items:
                    item.hide()
        # else:
        #     self.clear_trades_data()

    def one_trade_btn_click(self, pressed):
        """k线图部件中单个成交按钮的点击事件"""
        self.main_btn.setChecked(False)  # 将主按钮设置成未选中状态
        show_trades = []  # 记录展示交易单
        trades_data = []
        self.clear_trades_data()  # 删除之前的交易记录和所画的线。
        for btn in self.list_btn:
            if btn == self.sender():
                show_trades.append(self.list_trades_record[int(btn.objectName())])
                btn.setStyleSheet("QPushButton{background:blue}")
            else:
                # 复原原先选中单个按钮(按钮设置成未选中状态,背景色设置成灰色)
                btn.setChecked(False)
                btn.setStyleSheet("QPushButton{background:(100, 100, 100)}")

        for trade in show_trades:
            trade["date_open"] = to_datetime(trade["date_open"])
            trade["date_sell"] = to_datetime(trade["date_sell"])

            if trade.get('win_long', False):
                open_direction = Direction.LONG
                close_direction = Direction.SHORT
                win_price = trade['win_long']
                loss_price = trade['loss_long']
                price_sell = trade["price_sell"]
            elif trade.get('win_short', False):
                open_direction = Direction.SHORT
                close_direction = Direction.LONG
                win_price = trade['win_short']
                loss_price = trade['loss_short']
                price_sell = trade["price_sell"]
            else:
                open_direction = trade['direction']
                close_direction = get_contrast_direction(open_direction)
                win_price = trade['win_price']
                loss_price = trade['loss_price']
                price_sell = trade["price_sell"]

            # 构建开仓单数据对象
            trade_open = TradeData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                orderid="",
                tradeid="",
                direction=open_direction,
                offset=Offset.OPEN,
                price=trade['price_open'],
                volume=1,
                time=trade["date_open"].time(),
                gateway_name="",
                price_sell=price_sell
            )
            trade_open.win_price = win_price
            trade_open.loss_price = loss_price
            trade_open.datetime = trade["date_open"]
            trades_data.append(trade_open)

            # 构建平仓单数据对象
            trade_close = TradeData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                orderid="",
                tradeid="",
                direction=close_direction,
                offset=Offset.CLOSE,
                price=trade['price_sell'],
                volume=1,
                time=trade["date_sell"].time(),
                gateway_name=""
            )
            trade_close.datetime = trade["date_sell"]
            trades_data.append(trade_close)

        self.update_trades(trades_data, show_lines=True)

        if self.chart.trade_connection_line_hidden_flag:
            for item in self.chart._trade_line_item:
                item.hide()


def generate_trade_pairs(trades: list) -> list:
    """构建包含开仓日期、平仓日期、开仓价、平仓价、成交量、交易方向的数据对象"""
    long_trades = []
    short_trades = []
    trade_pairs = []

    for trade in trades:
        trade = copy(trade)

        if trade.direction == Direction.LONG:
            same_direction = long_trades
            opposite_direction = short_trades
        else:
            same_direction = short_trades
            opposite_direction = long_trades

        while trade.volume and opposite_direction:
            open_trade = opposite_direction[0]

            close_volume = min(open_trade.volume, trade.volume)

            open_dt = open_trade.datetime

            close_dt = trade.datetime

            d = {
                "open_dt": open_dt,
                "open_price": open_trade.price,
                "close_dt": close_dt,
                "close_price": trade.price,
                "direction": open_trade.direction,
                "volume": close_volume,
            }
            trade_pairs.append(d)

            open_trade.volume -= close_volume
            if not open_trade.volume:
                opposite_direction.pop(0)

            trade.volume -= close_volume

        if trade.volume:
            same_direction.append(trade)

    return trade_pairs

