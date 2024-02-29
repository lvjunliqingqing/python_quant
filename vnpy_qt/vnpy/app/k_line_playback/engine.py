
""""""
import importlib
import os
import traceback
from datetime import datetime
from pathlib import Path
from threading import Thread
import pyqtgraph as pg
from vnpy.app.cta_strategy import CtaTemplate
from vnpy.app.k_line_playback.backtesting import PlaybackBacktestingEngine, load_bar_data
from vnpy.event import Event, EventEngine
from vnpy.trader.constant import Interval, Exchange, Direction, Offset
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.rqdata import rqdata_client

APP_NAME = "PlayBackChart"
EVENT_PLAY_BACK_CHART_HISTORY = "ePlayBackChartHistory"
EVENT_PLAY_BACK_CHART_BACKTESTER_LOG = "ePlayBackChartBacktesterLog"  # noqa
EVENT__PLAY_BACK_CHART_BACKTESTING_FINISHED = "ePlayBackChartBacktestingFinished"  # noqa


class PlayBackChartEngine(BaseEngine):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.classes = {}
        rqdata_client.init()
        self.backtesting_engine = None  # PlaybackBacktestingEngine的实例化对象
        self.thread = None
        self.result_df = None  # 每日盈亏数据df对象,df的每一行都是一条交易盈亏数据。
        self.result_statistics = None  # 策略统计指标(是个字典)
        self.trades_record = None
        self.dt_ix_map = {}
        self.ix_bar_map = {}
        self.trade_data = []

    def query_history(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> None:
        """"""
        thread = Thread(
            target=self._query_history,
            args=[vt_symbol, interval, start, end]
        )
        thread.start()

    def _query_history(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> None:
        """"""
        symbol, exchange = vt_symbol.split(".")
        exchange = Exchange(exchange)
        data = load_bar_data(
                symbol,
                exchange,
                interval,
                start,
                end
                )

        for ix, bar in enumerate(data):
            self.ix_bar_map[ix] = bar
            self.dt_ix_map[bar.datetime] = ix

        event = Event(EVENT_PLAY_BACK_CHART_HISTORY, data)
        self.event_engine.put(event)

    def init_engine(self):
        """"""
        self.write_log("初始化复盘引擎")

        self.backtesting_engine = PlaybackBacktestingEngine()
        # output属性指向写日志函数赋值给
        self.backtesting_engine.output = self.write_log

        self.load_strategy_class()
        self.write_log("策略文件加载完成")

    def write_log(self, msg: str):
        """"""
        event = Event(EVENT_PLAY_BACK_CHART_BACKTESTER_LOG)
        event.data = msg
        self.event_engine.put(event)

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        """
        app_path = Path(__file__).parent.parent
        path1 = app_path.joinpath("cta_strategy", "strategies")
        self.load_strategy_class_from_folder(
            path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("strategies")
        self.load_strategy_class_from_folder(path2, "strategies")

        path3 = Path(__file__).parent.parent.parent.parent.joinpath("strategies")

        self.load_strategy_class_from_folder(path3, "")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = ""):
        """
        Load strategy class from certain folder.
        """
        if module_name is "":
            module_name = "strategies"

        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                # Load python source code file
                if filename.endswith(".py"):
                    strategies_dir = dirpath.split("strategies")
                    if strategies_dir[1]:
                        tmp_list = [str_dir.replace('\\', '') for str_dir in strategies_dir[1:]]
                        module_name = "strategies" + "." + ".".join(tmp_list)

                    strategy_module_name = ".".join([module_name, filename.replace(".py", "")])

                # Load compiled pyd binary file
                elif filename.endswith(".pyd"):
                    strategies_dir = dirpath.split("strategies")
                    if strategies_dir[1]:
                        tmp_list = [str_dir.replace('\\', '') for str_dir in strategies_dir[1:]]
                        module_name = "strategies" + "." + ".".join(tmp_list)
                    strategy_module_name = ".".join([module_name, filename.replace(".py", "")])

                self.load_strategy_class_from_module(strategy_module_name)

    def load_strategy_class_from_module(self, module_name: str):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)

            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def get_strategy_class_names(self):
        """"""
        return list(self.classes.keys())

    def run_backtesting(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        inverse: bool,
        setting: dict
    ):
        """做个标记:回测一次只会调用一次函数。"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine
        engine.clear_data()  # 每次加载数据时,都会删除之前的那些数据。

        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
            inverse=inverse
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        )
        engine.load_data()  # 加载数据

        try:
            engine.run_backtesting()  # 真正执行回测的逻辑函数
        except Exception:  # noqa
            msg = f"策略回测失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

            self.thread = None
            return

        self.result_df = engine.calculate_result()
        self.result_statistics = engine.calculate_statistics(output=False)
        self.trades_record = engine.get_trades_record()  # 获取策略中特别处理过的成交记录数据

        # 清除线程对象
        self.thread = None

        # 推送回测完成事件
        event = Event(EVENT__PLAY_BACK_CHART_BACKTESTING_FINISHED)
        self.event_engine.put(event)

    def start_backtesting(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        inverse: bool,
        setting: dict
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_backtesting,
            args=(
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
                setting
            )
        )
        self.thread.start()

        return True

    def get_result_df(self):
        """"""
        return self.result_df

    def get_result_statistics(self):
        """"""
        return self.result_statistics

    def get_trades_record(self):
        """"""
        return self.trades_record

    def get_default_setting(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def get_all_trades(self):
        """"""
        return self.backtesting_engine.get_all_trades()

    def get_all_orders(self):
        """"""
        return self.backtesting_engine.get_all_orders()

    def get_all_daily_results(self):
        """"""
        return self.backtesting_engine.get_all_daily_results()

    def get_history_data(self):
        """"""
        return self.backtesting_engine.history_data

    def update_trade(self, bar):
        """"""
        dt_trades_map = self.backtesting_engine.get_all_dt_trades_map()
        trades = dt_trades_map[bar.datetime]
        for trade in trades:
            ix = self.dt_ix_map[trade.datetime]
            scatter = {
                "pos": (ix, trade.price),
                "data": 1,
                "size": 14,
                "pen": pg.mkPen((255, 255, 255))
            }

            if trade.direction == Direction.LONG:
                scatter_symbol = "t1"   # Up arrow
            else:
                scatter_symbol = "t"    # Down arrow

            if trade.offset == Offset.OPEN:
                scatter_brush = pg.mkBrush((255, 255, 0))   # Yellow
            else:
                scatter_brush = pg.mkBrush((0, 0, 255))     # Blue

            scatter["symbol"] = scatter_symbol
            scatter["brush"] = scatter_brush

            self.trade_data.append(scatter)
            self.trade_scatter.setData(self.trade_data)

    def create_scatter_plot_item(self, chart):
        """创建个散点图画图对象"""
        self.trade_scatter = pg.ScatterPlotItem()
        self.candle_plot = chart.get_plot("candle")
        self.candle_plot.addItem(self.trade_scatter)