"""
Author: LvJun
"""

import importlib
import os
import random
import traceback
from inspect import getfile
from pathlib import Path

from vnpy.app.cta_strategy import CtaTemplate
from vnpy.event import EventEngine
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.object import TradeData

APP_NAME = "ManualPositionAdjustment"


class ManualPositionAdjustmentEngine(BaseEngine):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.file_path: str = ""

        self.symbol: str = ""
        self.exchange: Exchange = Exchange.SSE
        self.interval: Interval = Interval.MINUTE
        self.datetime_head: str = ""
        self.open_head: str = ""
        self.close_head: str = ""
        self.low_head: str = ""
        self.high_head: str = ""
        self.volume_head: str = ""
        self.classes: dict = {}  # 保存策略类名
        self.load_strategy_class()

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        加载工作目录和cta策略模块的strategies中的策略文件,把工作目录的strategies中的策略文件类名和cta策略模块策略的strategies中的策略文件类名保存到self.classes中去。
        """
        app_path = Path(__file__).parent.parent
        path1 = app_path.joinpath("cta_strategy", "strategies")  # cta策略模块策略的strategies文件夹的绝对路径
        self.load_strategy_class_from_folder(
            path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("strategies")   # 用户工作目录的strategies文件夹的绝对路径
        self.load_strategy_class_from_folder(path2, "strategies")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = ""):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                # Load python source code file
                if filename.endswith(".py"):
                    strategy_module_name = ".".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(strategy_module_name)
                # Load compiled pyd binary file
                elif filename.endswith(".pyd"):
                    strategy_module_name = ".".join(
                        [module_name, filename.split(".")[0]])
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
            print("ManualPositionAdjustmentEngine.load_strategy_class_from_module:\n", msg)

    def get_strategy_class_names(self):
        """"""
        return list(self.classes.keys())

    def get_default_setting(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def get_strategy_class_file(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        file_path = getfile(strategy_class)
        return file_path

    def save_trade_data(self, order_data, win_price, loss_price):
        tradeData = TradeData(
            gateway_name=order_data.gateway_name,
            symbol=order_data.symbol,
            exchange=order_data.exchange,
            orderid=order_data.orderid,
            tradeid=str(random.randrange(10000, 999999, 6)).ljust(6, '0')

        )

        tradeData.account_id = order_data.account_id
        tradeData.frozen = order_data.frozen
        tradeData.balance = order_data.balance
        tradeData.strategy_name = order_data.strategy_name
        tradeData.strategy_class_name = order_data.strategy_class_name
        tradeData.order_ref = order_data.order_ref
        tradeData.direction = order_data.direction
        tradeData.strategy_author = "manual"
        tradeData.offset = order_data.offset
        tradeData.price = order_data.price
        tradeData.win_price = win_price
        tradeData.loss_price = loss_price
        tradeData.volume = order_data.volume
        tradeData.order_time = order_data.order_time
        tradeData.trade_date = order_data.order_time
        tradeData.time = order_data.time
        tradeData.run_type = order_data.run_type
        tradeData.order_sys_id = order_data.order_sys_id
        tradeData.order_local_id = order_data.order_local_id
        tradeData.trade_src = "Manual"
        id_ret_trade = TradeDataModel().save_trade_data(tradeData)
        return id_ret_trade

