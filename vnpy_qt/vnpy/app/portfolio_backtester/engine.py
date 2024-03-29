import importlib
import os
import traceback
from datetime import datetime
from inspect import getfile
from pathlib import Path
from threading import Thread
from typing import List, Dict

from vnpy.app.portfolio_strategy import (
    StrategyTemplate,
    BacktestingEngine,
)
from vnpy.app.portfolio_strategy.backtesting import OptimizationSetting
from vnpy.event import Event, EventEngine
from vnpy.trader.constant import Interval
from vnpy.trader.engine import BaseEngine, MainEngine

APP_NAME = "PortfolioBacktester"

EVENT_PORTFOLIO_BACKTESTER_LOG = "ePortfolioBacktesterLog"
EVENT_PORTFOLIO_BACKTESTING_FINISHED = "ePortfolioBacktesterBacktestingFinished"
EVENT_PORTFOLIO_BACKTESTER_OPTIMIZATION_FINISHED = "ePortfolioBacktesterOptimizationFinished"

class BacktesterEngine(BaseEngine):
    """
    For running PORTFOLIO strategy backtesting.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.classes = {}
        self.backtesting_engine = None
        self.thread = None

        # Backtesting reuslt
        self.result_df = None
        self.result_statistics = None
        self.trades_record = None

    def init_engine(self):
        """"""
        self.write_log("初始化portfolio回测引擎")

        self.backtesting_engine = BacktestingEngine()
        # Redirect log from backtesting engine outside.
        self.backtesting_engine.output = self.write_log

        self.load_strategy_class()
        self.write_log("策略文件加载完成")


    def write_log(self, msg: str):
        """"""
        event = Event(EVENT_PORTFOLIO_BACKTESTER_LOG)
        event.data = msg
        self.event_engine.put(event)

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        """
        app_path = Path(__file__).parent.parent
        path1 = app_path.joinpath("portfolio_strategy", "strategies")
        self.load_strategy_class_from_folder(
            path1, "vnpy.app.portfolio_strategy.strategies")

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

            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, StrategyTemplate) and value is not StrategyTemplate):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def reload_strategy_class(self):
        """"""
        self.classes.clear()
        self.load_strategy_class()
        self.write_log("策略文件重载刷新完成")

    def get_strategy_class_names(self):
        """"""
        return list(self.classes.keys())

    def run_backtesting(
        self,
        class_name: str,
        vt_symbol_list: List[str],
        interval: str,
        start: datetime,
        end: datetime,
        rates: Dict[str, float],
        slippages: Dict[str, float],
        sizes: Dict[str, float],
        priceticks: Dict[str, float],
        capital: int,
        inverse: bool,
        setting: dict
    ):
        """"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine
        engine.clear_data()

        if interval == 'd':
            interval = Interval.DAILY
        elif interval == '1m':
            interval = Interval.MINUTE
        elif interval == '1h':
            interval = Interval.HOUR

        engine.set_parameters(
            vt_symbols=vt_symbol_list,
            interval=interval,
            start=start,
            end=end,
            rates=rates,
            slippages=slippages,
            sizes=sizes,
            priceticks=priceticks,
            capital=capital,
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        )

        engine.load_data()
        engine.run_backtesting()
        self.result_df = engine.calculate_result()
        self.result_statistics = engine.calculate_statistics(output=False)
        self.trades_record = engine.get_trades_record()  # 获取策略中特别处理过的成交记录数据

        # Clear thread object handler.
        self.thread = None

        # Put backtesting done event
        event = Event(EVENT_PORTFOLIO_BACKTESTING_FINISHED)
        self.event_engine.put(event)

    def start_backtesting(
        self,
        class_name: str,
        vt_symbol: list,
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

    def run_optimization(
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
        optimization_setting: OptimizationSetting,
        use_ga: bool
    ):
        """"""
        if use_ga:
            self.write_log("开始遗传算法参数优化")
        else:
            self.write_log("开始多进程参数优化")

        self.result_statistics = None

        if interval == 'd':
            interval = Interval.DAILY
        elif interval == '1m':
            interval = Interval.MINUTE
        elif interval == '1h':
            interval = Interval.HOUR

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            vt_symbols=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rates=rate,
            slippages=slippage,
            sizes=size,
            priceticks=pricetick,
            capital=capital,
            inverse=inverse
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            {}
        )

        if use_ga:
            self.result_values = engine.run_ga_optimization(
                optimization_setting,
                output=False
            )
        else:
            self.result_values = engine.run_optimization(
                optimization_setting,
                output=False
            )

        # Clear thread object handler.
        self.thread = None
        self.write_log("多进程参数优化完成")

        # Put optimization done event
        event = Event(EVENT_PORTFOLIO_BACKTESTER_OPTIMIZATION_FINISHED)
        self.event_engine.put(event)

    def start_optimization(
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
        optimization_setting: OptimizationSetting,
        use_ga: bool
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False
        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_optimization,
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
                optimization_setting,
                use_ga
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

    def get_result_values(self):
        """"""
        return self.result_values

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

    def get_strategy_class_file(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        file_path = getfile(strategy_class)
        return file_path