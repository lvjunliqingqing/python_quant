import importlib
import os
import traceback
from datetime import datetime
from inspect import getfile
from pathlib import Path
from threading import Thread
from typing import List, Dict, Set, Callable, Any, Type
from vnpy.app.spread_trading import SpreadStrategyTemplate, LegData, SpreadData

from vnpy.app.spread_trading.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import BaseEngine, MainEngine

APP_NAME = "SpreadBacktester"

EVENT_SPREAD_BACKTESTER_LOG = "eSpreadBacktesterLog"
EVENT_SPREAD_BACKTESTER_BACKTESTING_FINISHED = "eSpreadBacktesterBacktestingFinished"
EVENT_SPREAD_BACKTESTER_OPTIMIZATION_FINISHED = "eSpreadBacktesterOptimizationFinished"


class SpreadBacktesterEngine(BaseEngine):
    """
    For running CTA strategy backtesting.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.classes = {}
        self.backtesting_engine = None
        self.thread = None
        self.spread: SpreadData = None

        # Backtesting reuslt
        self.result_df = None
        self.result_statistics = None

        # Optimization result
        self.result_values = None


    def init_engine(self):
        """"""
        self.write_log("初始化套利回测引擎")

        self.backtesting_engine = BacktestingEngine()
        self.backtesting_engine.output = self.write_log
        self.load_strategy_class()
        self.write_log("策略文件加载完成")

    def write_log(self, msg: str):
        """"""
        event = Event(EVENT_SPREAD_BACKTESTER_LOG)
        event.data = msg
        self.event_engine.put(event)

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        """
        app_path = Path(__file__).parent.parent  # 获取当前文件的上上级路径
        path1 = app_path.joinpath("spread_trading", "strategies")  # 拼接路径
        self.load_strategy_class_from_folder(
            path1, "vnpy.app.spread_trading.strategies")

        path2 = Path.cwd().joinpath("strategies")
        self.load_strategy_class_from_folder(path2, "strategies")

        path3 = Path(__file__).parent.parent.parent.parent.joinpath("strategies")

        self.load_strategy_class_from_folder(path3, "")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = ""):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(str(path)):
            for filename in filenames:
                if filename.split(".")[-1] in ("py", "pyd", "so"):
                    strategy_module_name = ".".join([module_name, filename.split(".")[0]])
                    self.load_strategy_class_from_module(strategy_module_name)

    def load_strategy_class_from_module(self, module_name: str):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)
            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, SpreadStrategyTemplate) and value is not SpreadStrategyTemplate):
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
        spread: SpreadData,
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
        """"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            spread=spread,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        )

        engine.load_data()

        try:
            engine.run_backtesting()
        except Exception:
            msg = f"策略回测失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

            self.thread = None
            return

        self.result_df = engine.calculate_result()
        self.result_statistics = engine.calculate_statistics(output=False)
        self.trades_record = engine.get_trades_record()  # 获取策略中特别处理过的成交记录数据

        # Clear thread object handler.
        self.thread = None

        # Put backtesting done event
        event = Event(EVENT_SPREAD_BACKTESTER_BACKTESTING_FINISHED)
        self.event_engine.put(event)

    def start_backtesting(
        self,
        class_name: str,
        spread: SpreadData,
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
                spread,
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

    def get_result_values(self):
        """"""
        return self.result_values

    def get_default_setting(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def run_optimization(
        self,
        spread: SpreadData,
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

        self.result_values = None

        engine = self.backtesting_engine
        engine.clear_data()
        engine.set_parameters(
            spread=spread,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            {}
        )

        if use_ga:
            self.result_values = engine.run_ga_optimization(
                spread,
                optimization_setting,
                output=False,

            )
        else:
            self.result_values = engine.run_optimization(
                spread,
                optimization_setting,
                output=False,
            )

        # Clear thread object handler.
        self.thread = None
        self.write_log("多进程参数优化完成")

        # Put optimization done event
        event = Event(EVENT_SPREAD_BACKTESTER_OPTIMIZATION_FINISHED)
        self.event_engine.put(event)

    def start_optimization(
        self,
        spread: SpreadData,
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
                spread,
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

    def create_spread(
        self,
        name: str,
        leg_settings: List[Dict],
        active_symbol: str,
        min_volume: float,
    ) -> None:
        """"""

        legs: List[LegData] = []
        price_multipliers: Dict[str, int] = {}
        trading_multipliers: Dict[str, int] = {}
        inverse_contracts: Dict[str, bool] = {}

        for leg_setting in leg_settings:
            vt_symbol = leg_setting["vt_symbol"]
            leg = LegData(vt_symbol)

            legs.append(leg)
            price_multipliers[vt_symbol] = leg_setting["price_multiplier"]
            trading_multipliers[vt_symbol] = leg_setting["trading_multiplier"]
            inverse_contracts[vt_symbol] = leg_setting.get(
                "inverse_contract", False)

        self.spread = SpreadData(
            name,
            legs,
            price_multipliers,
            trading_multipliers,
            active_symbol,
            inverse_contracts,
            min_volume
        )