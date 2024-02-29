""""""
from abc import ABC
from collections import defaultdict
from copy import copy, deepcopy
from typing import Dict, Set, List, TYPE_CHECKING, Any
from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData, TickData, OrderData, TradeData, AccountData, PositionData
from vnpy.trader.utility import virtual
from ...controller.risk_ctrl import risk_control_pos
from ...controller.trade_operation import write_local_log, get_order_ref_value
from ...rabbitmq.queue.position_queue import PositionQueue

if TYPE_CHECKING:
    from .engine import StrategyEngine


class StrategyTemplate(ABC):
    """"""

    author = ""
    parameters = []
    parameters_chinese = {}
    variables = []
    account = None

    def __init__(
        self,
        strategy_engine: "StrategyEngine",
        strategy_name: str,
        vt_symbols: List[str],
        setting: dict,
    ):
        """"""
        self.strategy_engine: "StrategyEngine" = strategy_engine
        self.strategy_name: str = strategy_name
        self.vt_symbols: List[str] = vt_symbols

        self.inited: bool = False
        self.trading: bool = False
        self.pos: Dict[str, int] = defaultdict(int)

        self.orders: Dict[str, OrderData] = {}
        self.active_orderids: Set[str] = set()
        self.order_id_map = defaultdict()
        self.order_ref_map = defaultdict()
        self.vt_orderid_map = defaultdict()
        self.original_win_loss_close_map = defaultdict(list)
        self.commission_close_map = {}
        self.risk_ctrl_cond = {}  # 风险控制字典 {symbol:1或0},1表示不开仓,0表示开仓

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables: List = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")
        self.parameters_chinese = deepcopy(self.parameters_chinese)

        self.update_setting(setting)

    def update_setting(self, setting: dict) -> None:
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls) -> Dict:
        """
        Get default parameters dict of strategy class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self) -> Dict:
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

    def get_variables(self) -> Dict:
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self) -> Dict:
        """
        Get strategy data.
        """
        strategy_data = {
            "strategy_name": self.strategy_name,
            "vt_symbols": self.vt_symbols,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @virtual
    def on_init(self) -> None:
        """
        Callback when strategy is inited.
        """
        pass

    @virtual
    def on_start(self) -> None:
        """
        Callback when strategy is started.
        """
        pass

    @virtual
    def on_stop(self) -> None:
        """
        Callback when strategy is stopped.
        """
        pass

    @virtual
    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bars(self, bars: Dict[str, BarData]) -> None:
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

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_open(self, open_dict: Dict):
        pass

    def on_cancel(self, orderid):
        pass

    def risk_control(self, vt_symbol, engine, open_price, loss_price, max_open_loss_rate=0.04, order_ref="", balance=False):
        """获取真实能开仓的手数"""
        real_open_pos = risk_control_pos(self, vt_symbol, engine, open_price, loss_price, max_open_loss_rate, order_ref, balance)
        return real_open_pos

    def on_close(self, order_data, tick):
        vt_orderid = self.vt_orderid_map.get(order_data.order_ref)
        if vt_orderid:
            self.cancel_order(vt_orderid)
        order_ref = get_order_ref_value()
        self.order_id_map[str(order_ref)] = order_data.orderid
        self.order_ref_map[str(order_ref)] = order_data.order_ref
        self.original_win_loss_close_map[str(order_ref)].append(order_data.win_price)
        self.original_win_loss_close_map[str(order_ref)].append(order_data.loss_price)
        self.original_win_loss_close_map[str(order_ref)].append(tick.last_price)
        if order_data.direction == Direction.LONG:
            vt_orderid = self.sell(tick.vt_symbol, tick.limit_down, abs(int(order_data.un_volume)), order_ref=order_ref)
            if vt_orderid:
                self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
            self.commission_close_map[str(order_data.order_ref)] = True
            write_local_log(self.strategy_name, f"portfolio:{tick.symbol},以当时价{tick.last_price}强制平仓，orderid:{order_data.orderid}")
        else:
            vt_orderid = self.cover(tick.vt_symbol, tick.limit_up, abs(int(order_data.un_volume)), order_ref=order_ref)
            if vt_orderid:
                self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
            self.commission_close_map[str(order_data.order_ref)] = True
            self.active_order_close_map[order_data.order_ref] = True
            write_local_log(self.strategy_name, f"portfolio:{tick.symbol},以当时价{tick.last_price}强制平仓，orderid:{order_data.orderid}")

    def update_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.pos[trade.vt_symbol] += trade.volume
        else:
            self.pos[trade.vt_symbol] -= trade.volume

    def update_order(self, order: OrderData) -> None:
        """
        Callback of new order data update.
        """
        self.orders[order.vt_orderid] = order

        if not order.is_active() and order.vt_orderid in self.active_orderids:
            self.active_orderids.remove(order.vt_orderid)

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

    def on_account(self, account: AccountData):
        self.account = account

    def position_queue(self, position: PositionData):

        position = self.obj_extends(position)
        PositionQueue().push(position_data=position)

    def buy(self, vt_symbol: str, price: float, volume: float, lock: bool = False, order_ref: str = "") -> List[str]:
        """
        Send buy order to open a long position.
        """
        return self.send_order(vt_symbol, Direction.LONG, Offset.OPEN, price, volume, lock, order_ref)

    def sell(self, vt_symbol: str, price: float, volume: float, lock: bool = False, order_ref: str = "") -> List[str]:
        """
        Send sell order to close a long position.
        """
        return self.send_order(vt_symbol, Direction.SHORT, Offset.CLOSE, price, volume, lock, order_ref)

    def short(self, vt_symbol: str, price: float, volume: float, lock: bool = False, order_ref: str = "") -> List[str]:
        """
        Send short order to open as short position.
        """
        return self.send_order(vt_symbol, Direction.SHORT, Offset.OPEN, price, volume, lock, order_ref)

    def cover(self, vt_symbol: str, price: float, volume: float, lock: bool = False, order_ref: str = "") -> List[str]:
        """
        Send cover order to close a short position.
        """
        return self.send_order(vt_symbol, Direction.LONG, Offset.CLOSE, price, volume, lock, order_ref)

    def send_order(
        self,
        vt_symbol: str,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        lock: bool = False,
        order_ref: str = ""
    ) -> List[str]:
        """
        Send a new order.
        """
        if self.trading:
            vt_orderids = self.strategy_engine.send_order(
                self, vt_symbol, direction, offset, price, volume, lock, order_ref
            )

            for vt_orderid in vt_orderids:
                self.active_orderids.add(vt_orderid)

            return vt_orderids
        else:
            return []

    def cancel_order(self, vt_orderid: str) -> None:
        """
        Cancel an existing order.
        """
        if self.trading:
            self.strategy_engine.cancel_order(self, vt_orderid)

    def cancel_all(self) -> None:
        """
        Cancel all orders sent by strategy.
        """
        for vt_orderid in list(self.active_orderids):
            self.cancel_order(vt_orderid)

    def get_pos(self, vt_symbol: str) -> int:
        """"""
        return self.pos.get(vt_symbol, 0)

    def get_order(self, vt_orderid: str) -> OrderData:
        """"""
        return self.orders.get(vt_orderid, None)

    def get_all_active_orderids(self) -> List[OrderData]:
        """"""
        return list(self.active_orderids)

    def write_log(self, msg: str) -> None:
        """
        Write a log message.
        """
        self.strategy_engine.write_log(msg, self)

    def load_bars(self, days: int, interval: Interval = Interval.MINUTE, use_database: bool = False) -> None:
        """
        Load historical bar data for initializing strategy.
        """
        self.strategy_engine.load_bars(self, days, interval, use_database)

    def put_event(self) -> None:
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.strategy_engine.put_strategy_event(self)

    def send_email(self, msg) -> None:
        """
        Send email to default receiver.
        """
        if self.inited:
            self.strategy_engine.send_email(msg, self)

    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.strategy_engine.sync_strategy_data(self)
