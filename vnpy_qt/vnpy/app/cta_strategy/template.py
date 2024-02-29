""""""
import os
import platform
import string
from abc import ABC
from collections import defaultdict
from copy import copy, deepcopy
from datetime import datetime
from typing import Any, Callable

from vnpy.controller.trade_operation import get_order_ref_value
from vnpy.controller.risk_ctrl import risk_control_pos
from vnpy.rabbitmq.queue.order_queue import OrderQueue
from vnpy.rabbitmq.queue.trade_queue import TradeQueue
from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData, TickData, OrderData, TradeData, AccountData, PositionData
from vnpy.trader.utility import virtual
from .base import StopOrder, EngineType
from vnpy.rabbitmq.queue.position_queue import PositionQueue
from vnpy.rabbitmq.queue.stop_order_queue import StopOrderQueue


class CtaTemplate(ABC):
    """"""

    author = ""
    parameters = []
    variables = []
    parameters_chinese = {}
    account = None
    last_position = None

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        """"""
        self.cta_engine = cta_engine
        self.strategy_name = strategy_name
        self.vt_symbol = vt_symbol

        self.inited = False
        self.trading = False
        self.pos = 0
        self.is_open_today = False
        # order_ref:order_id
        self.order_id_map = {}
        # str(order_ref):order_ref
        self.order_ref_map = {}
        # 原始盈亏记录
        self.original_win_loss_record = defaultdict(list)
        # 是否在平仓委托中
        self.commission_map = {}
        # 风险控制(值为1时,表示不能开仓)
        self.strategy_value = {"risk_ctrl_cond": 0}

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.parameters_chinese = deepcopy(self.parameters_chinese)
        self.update_setting(setting)

    def update_setting(self, setting: dict):
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of strategy class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_paramenters_chinese(self):
        """
        通过参数映射在界面显示中文参数
        """
        return self.parameters_chinese

    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self):
        """
        Get strategy data.
        """
        strategy_data = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @virtual
    def on_init(self):
        """
        Callback when strategy is inited.
        """
        pass

    @virtual
    def on_start(self):
        """
        Callback when strategy is started.
        """
        pass

    @virtual
    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        pass

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    @virtual
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    def risk_control(self, vt_symbol, engine, open_price, loss_price, max_open_loss_rate=0.04, order_ref="", balance=False):
        """查询允许开仓的手数"""
        real_open_pos = risk_control_pos(self, vt_symbol, engine, open_price, loss_price, max_open_loss_rate, order_ref, balance)
        return real_open_pos

    def on_close(self, order_data, tick):
        self.cancel_all()
        order_ref = get_order_ref_value()
        self.order_id_map[str(order_ref)] = order_data.orderid
        self.order_ref_map[str(order_ref)] = order_data.order_ref
        self.original_win_loss_record[str(order_ref)].append(order_data.win_price)
        self.original_win_loss_record[str(order_ref)].append(order_data.loss_price)
        self.original_win_loss_record[str(order_ref)].append(tick.last_price)
        if order_data.direction == Direction.LONG:
            self.sell(tick.limit_down, abs(int(order_data.un_volume)), order_ref=order_ref)
            self.commission_map[str(order_data.order_ref)] = True
            self.write_local_log(self.strategy_name, f"cta:以当时价{tick.last_price}强制平多仓，orderid:{order_data.orderid}")

        else:
            self.cover(tick.limit_up, abs(int(order_data.un_volume)), order_ref=order_ref)
            self.commission_map[str(order_data.order_ref)] = True
            self.write_local_log(self.strategy_name, f"cta:以当时价{tick.last_price}强制平空仓，orderid:{order_data.orderid}")

    def obj_extends(self, obj: Any):

        obj.strategy_name = self.strategy_name
        obj.strategy_class_name = self.__class__.__name__
        obj.strategy_author = self.author
        obj.account_id = 0

        if not hasattr(obj, 'balance'):
            obj.balance = 0

        if not hasattr(obj, 'frozen'):
            obj.frozen = 0

        if not hasattr(obj, 'account_id'):
            obj.account_id = 0

        if not hasattr(obj, 'gateway_name'):
            obj.gateway_name = self.get_engine_type().name

        if self.account:
            obj.account_id = self.account.accountid
            obj.balance = self.account.balance
            obj.frozen = self.account.frozen
        return obj

    def trade_queue(self, trade: TradeData):
        """"""
        trade = self.obj_extends(trade)
        TradeQueue().push(trade_data=trade)

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def order_queue(self, order: OrderData):

        order = self.obj_extends(order)
        OrderQueue().push(order_data=order)

    def stop_order_queue(self, stop_order: StopOrder):

        stop_order = self.obj_extends(stop_order)
        StopOrderQueue().push(stop_order_data=stop_order)

    def position_queue(self, position: PositionData):

        position = self.obj_extends(position)
        PositionQueue().push(position_data=position)

    @virtual
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def on_account(self, account: AccountData):
        self.account = account

    def on_position(self, position: PositionData):

        if not self.last_position:
            self.last_position = position

        if self.last_position.__dict__ != position.__dict__:
            self.last_position = position
            self.position_queue(position)

    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False, order_ref: str = ""):
        """
        Send buy order to open a long position.
        """
        return self.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock, order_ref)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False, order_ref: str = ""):
        """
        Send sell order to close a long position.
        """
        return self.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock, order_ref)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False, order_ref: str = ""):
        """
        Send short order to open as short position.
        """
        return self.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock, order_ref)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False, order_ref: str = ""):
        """
        Send cover order to close a short position.
        """
        return self.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock, order_ref)

    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        order_ref: str = ""
    ):
        """
        Send a new order.
        """
        if self.trading:
            vt_orderids = self.cta_engine.send_order(
                self, direction, offset, price, volume, stop, lock, order_ref
            )
            return vt_orderids
        else:
            return []

    def cancel_order(self, vt_orderid: str):
        """
        Cancel an existing order.
        """
        if self.trading:
            self.cta_engine.cancel_order(self, vt_orderid)

    def cancel_all(self):
        """
        Cancel all orders sent by strategy.
        """
        if self.trading:
            self.cta_engine.cancel_all(self)

    def write_log(self, msg: str):
        """
        Write a log message.
        """
        self.cta_engine.write_log(msg, self)

    def get_engine_type(self):
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return self.cta_engine.get_engine_type()

    def get_pricetick(self):
        """
        Return pricetick data of trading contract.
        """
        return self.cta_engine.get_pricetick(self)

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        use_database: bool = False
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar

        self.cta_engine.load_bar(
            self.vt_symbol,
            days,
            interval,
            callback,
            use_database
        )

    def load_tick(self, days: int):
        """
        Load historical tick data for initializing strategy.
        """
        self.cta_engine.load_tick(self.vt_symbol, days, self.on_tick)

    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.cta_engine.put_strategy_event(self)

    def send_email(self, msg):
        """
        Send email to default receiver.
        """
        if self.inited:
            self.cta_engine.send_email(msg, self)

    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.cta_engine.sync_strategy_data(self)

    @staticmethod
    def write_local_log(strategy_name, context):
        filename = f"{strategy_name}_{datetime.now().date()}.txt"
        sys = platform.system()
        if sys == "Windows":
            disk_list = []
            for c in string.ascii_uppercase:
                disk = c + ':'
                if os.path.isdir(disk):
                    disk_list.append(disk)
            path = os.path.join(disk_list[1], f"/futures_log/{strategy_name}")
            if not os.path.exists(path):
                os.mkdir(path)
            with open(path + "/" + filename, "a") as f:
                f.write("\n%s:%s\n" % (datetime.now(), context))

        elif sys == "Linux":
            path = f"/data/futures_log/{strategy_name}"
            if not os.path.exists(path):
                os.mkdir(path)
            with open(path + "/" + filename, "a") as f:
                f.write("\n%s:%s\n" % (datetime.now(), context))

    def updata_pos(self, order_data_list):
        self.pos = 0
        for order_data in order_data_list:
            if order_data.direction == 'LONG':
                var = 1
            elif order_data.direction == 'SHORT':
                var = -1
            else:
                var = 0
            self.pos += var * int(order_data.un_volume)
        return self.pos

    def stop_trade_time(self, hour, minute, tick):
        if hour == 10 and 15 < minute <= 29:
            self.write_log(f'{tick.symbol}：10:15-10:30分不做任何操作')
            return False
        elif "11:30" < tick.datetime.strftime("%H:%M") < "13:30":
            self.write_log(f'{tick.symbol}：中午休盘时间不做任何操作')
            return False
        elif "15:00" < tick.datetime.strftime("%H:%M") < "21:00":
            self.write_log(f'{tick.symbol}：下午休盘时间不做任何操作')
            return False
        elif "2:30" < tick.datetime.strftime("%H:%M") < "9:00":
            self.write_log(f'{tick.symbol}：晚盘结束后休盘时间不做任何操作')
            return False
        else:
            return True


class CtaSignal(ABC):
    """"""

    def __init__(self):
        """"""
        self.signal_pos = 0

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    def set_signal_pos(self, pos):
        """"""
        self.signal_pos = pos

    def get_signal_pos(self):
        """"""
        return self.signal_pos


class TargetPosTemplate(CtaTemplate):
    """"""
    tick_add = 1

    last_tick = None
    last_bar = None
    target_pos = 0

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.active_orderids = []
        self.cancel_orderids = []

        self.variables.append("target_pos")

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

        if self.trading:
            self.trade()

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        vt_orderid = order.vt_orderid

        if not order.is_active():
            if vt_orderid in self.active_orderids:
                self.active_orderids.remove(vt_orderid)

            if vt_orderid in self.cancel_orderids:
                self.cancel_orderids.remove(vt_orderid)

    def check_order_finished(self):
        """"""
        if self.active_orderids:
            return False
        else:
            return True

    def set_target_pos(self, target_pos):
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self):
        """"""
        if not self.check_order_finished():
            self.cancel_old_order()
        else:
            self.send_new_order()

    def cancel_old_order(self):
        """"""
        for vt_orderid in self.active_orderids:
            if vt_orderid not in self.cancel_orderids:
                self.cancel_order(vt_orderid)
                self.cancel_orderids.append(vt_orderid)

    def send_new_order(self):
        """"""
        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)

        else:
            if self.active_orderids:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderids = self.cover(long_price, pos_change)
                    else:
                        vt_orderids = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderids = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderids = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)
