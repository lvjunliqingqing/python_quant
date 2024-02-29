"""
"""
import logging
import os
import smtplib
from abc import ABC
from collections import defaultdict
from copy import copy
from datetime import datetime, timedelta
from email.message import EmailMessage
from logging import Logger
from queue import Empty, Queue
from threading import Thread
from typing import Any, Sequence, Type, Dict, List, Optional
from numpy import mean
from vnpy.controller.trade_operation import current_trade_date
from vnpy.controller.risk_ctrl import risk_ctrl_info
from vnpy.event import Event, EventEngine, EVENT_TIMER
from vnpy.model.order_data_model import OrderDataModel
from vnpy.model.strategy_name_model import StrategyNameModel
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Direction, Offset
from vnpy.trader.event import EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, EVENT_FORCED_LIQUIDATION
from vnpy.trader.object import TradeRecordData, StrategyHoldData
from vnpy.trader.symbol_attr import ContractMultiplier, ContractMarginRatio, ContractPricePick, FuturesCompanySpread
from vnpy.trader.utility import get_letter_from_symbol
from .app import BaseApp
from .event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
    EVENT_STRATEGY_HOLD_POSITION, EVENT_STRATEGY_CLOSE_POSITION)
from .gateway import BaseGateway
from .object import (
    CancelRequest,
    LogData,
    OrderRequest,
    SubscribeRequest,
    HistoryRequest,
    OrderData,
    BarData,
    TickData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    Exchange
)
from .setting import SETTINGS
from .utility import get_folder_path, TRADER_DIR
from ..controller.global_variable import init_global_variable


class MainEngine:
    """
    Acts as the core of VN Trader.
    """

    def __init__(self, event_engine: EventEngine = None):
        """"""
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        self.gateways: Dict[str, BaseGateway] = {}
        self.engines: Dict[str, BaseEngine] = {}
        self.apps: Dict[str, BaseApp] = {}
        self.exchanges: List[Exchange] = []

        self.init_global_variable()
        os.chdir(TRADER_DIR)    # Change working directory
        self.init_engines()     # Initialize function engines
        self.connection_flag = False  # 连接网关接口标志,连接成功后设为True。

    def init_global_variable(self):
        init_global_variable()

    def add_engine(self, engine_class: Any) -> "BaseEngine":
        """
        Add function engine.
        """
        engine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def add_gateway(self, gateway_class: Type[BaseGateway]) -> BaseGateway:
        """
        Add gateway.
        """
        gateway = gateway_class(self.event_engine)
        self.gateways[gateway.gateway_name] = gateway

        # Add gateway supported exchanges into engine
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def add_app(self, app_class: Type[BaseApp]) -> "BaseEngine":
        """
        Add app.
        """
        app = app_class()
        self.apps[app.app_name] = app

        engine = self.add_engine(app.engine_class)
        return engine

    def init_engines(self) -> None:
        """
        Init all engines.
        """
        self.add_engine(LogEngine)
        self.add_engine(OmsEngine)
        self.add_engine(EmailEngine)
        self.add_engine(TransactionPushEngine)
        self.add_engine(TimerEngine)

    def write_log(self, msg: str, source: str = "") -> None:
        """
        Put log event with specific message.
        """
        log = LogData(msg=msg, gateway_name=source)
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        """
        Return gateway object by name.
        """
        gateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway

    def get_engine(self, engine_name: str) -> "BaseEngine":
        """
        Return engine object by name.
        """
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        """
        Get default setting dict of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        """
        Get all names of gatewasy added in main engine.
        """
        return list(self.gateways.keys())

    def get_all_apps(self) -> List[BaseApp]:
        """
        Get all app objects.
        """
        return list(self.apps.values())

    def get_all_exchanges(self) -> List[Exchange]:
        """
        Get all exchanges.
        """
        return self.exchanges

    def connect(self, setting: dict, gateway_name: str) -> None:
        """
        Start connection of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:  # 此时的gateway可以知道具体是xtp还是ctp的gateway)
            gateway.connect(setting)
            if gateway.td_api.userid:
                self.connection_flag = True

    def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        """
        Subscribe tick data update of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """
        Send new order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_orders(self, reqs: Sequence[OrderRequest], gateway_name: str) -> List[str]:
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
        else:
            return ["" for req in reqs]

    def cancel_orders(self, reqs: Sequence[CancelRequest], gateway_name: str) -> None:
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)

    def query_history(self, req: HistoryRequest, gateway_name: str) -> Optional[List[BarData]]:
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    def close(self) -> None:
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()


class BaseEngine(ABC):
    """
    Abstract class for implementing an function engine.
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        engine_name: str,
    ):
        """"""
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        """"""
        pass


class LogEngine(BaseEngine):
    """
    Processes log event and output with logging module.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(LogEngine, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level: int = SETTINGS["log.level"]

        self.logger: Logger = logging.getLogger("VN Trader")
        self.logger.setLevel(self.level)

        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        """
        Add file output of log.
        """
        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"vt_{today_date}.log"
        log_path = get_folder_path("log")
        file_path = log_path.joinpath(filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        """
        Process log event.
        """
        log = event.data
        self.logger.log(log.level, log.msg)


class OmsEngine(BaseEngine):
    """
    Provides order management system function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(OmsEngine, self).__init__(main_engine, event_engine, "oms")

        self.ticks: Dict[str, TickData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}

        self.active_orders: Dict[str, OrderData] = {}
        # 品种均价字典
        self.symbol_ma_price: Dict[str, float] = {}
        # 记录持仓所有品种的总保证金和最大亏损总和
        self.account_margin_loss: Dict[str, List] = {}
        # 所有品种的最大亏损总和比率
        self.sum_max_loss_ratio: float = 0.0

        self.add_function()
        self.register_event()

    def add_function(self) -> None:
        """Add query function to main engine."""
        self.main_engine.get_tick = self.get_tick
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        self.main_engine.get_contract = self.get_contract
        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_active_orders = self.get_all_active_orders

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

    def process_tick_event(self, event: Event) -> None:
        """"""
        tick = event.data
        self.ticks[tick.vt_symbol] = tick

    def process_order_event(self, event: Event) -> None:
        """"""
        order = event.data
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def process_trade_event(self, event: Event) -> None:
        """"""
        trade = event.data
        self.trades[trade.vt_tradeid] = trade

    def process_position_event(self, event: Event) -> None:
        """"""
        position = event.data
        self.positions[position.vt_positionid] = position

    def process_account_event(self, event: Event) -> None:
        """"""
        account = event.data
        self.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event) -> None:
        """"""
        contract = event.data
        self.contracts[contract.vt_symbol] = contract
        if contract.last and contract.gateway_name == 'CTP':
            if hasattr(self.main_engine, 'BuiltInFunction'):  # main_engine有内嵌策略则执行内嵌策略
                if not self.main_engine.BuiltInFunction.status:
                    self.main_engine.BuiltInFunction.run()

    def get_tick(self, vt_symbol: str) -> Optional[TickData]:
        """
        Get latest market tick data by vt_symbol.
        """
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """
        Get latest order data by vt_orderid.
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid: str) -> Optional[TradeData]:
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid: str) -> Optional[PositionData]:
        """
        Get latest position data by vt_positionid.
        """
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid: str) -> Optional[AccountData]:
        """
        Get latest account data by vt_accountid.
        """
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        """
        Get contract data by vt_symbol.
        """
        return self.contracts.get(vt_symbol, None)

    def get_all_ticks(self) -> List[TickData]:
        """
        Get all tick data.
        """
        return list(self.ticks.values())

    def get_all_orders(self) -> List[OrderData]:
        """
        Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        """
        Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self) -> List[PositionData]:
        """
        Get all position data.
        """
        return list(self.positions.values())

    def get_all_accounts(self) -> List[AccountData]:
        """
        Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self) -> List[ContractData]:
        """
        Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_active_orders(self, vt_symbol: str = "") -> List[OrderData]:
        """
        Get all active orders by vt_symbol.

        If vt_symbol is empty, return all active orders.
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders

    def set_symbol_ma_price(self, symbol: str = "", ma_price: float = 0.0) -> None:
        """设置品种的均价"""
        self.symbol_ma_price[symbol] = ma_price

    def get_symbol_ma_price(self, symbol: str = "") -> float:
        return self.symbol_ma_price.get(symbol, 0)

    def set_account_margin_loss(self, accountid: str, sum_margin: float, sum_loss: float) -> None:
        """设置持仓总保证金和最大亏损总和"""
        self.account_margin_loss[accountid] = [sum_margin, sum_loss]

    def get_account_margin_loss(self, accountid: str) -> List:
        return self.account_margin_loss.get(accountid, [0, 0])


class EmailEngine(BaseEngine):
    """
    Provides email sending function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(EmailEngine, self).__init__(main_engine, event_engine, "email")

        self.thread: Thread = Thread(target=self.run)
        self.queue: Queue = Queue()
        self.active: bool = False

        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = "") -> None:
        """"""
        # Start email engine when sending first email.
        if not self.active:
            self.start()

        # Use default receiver if not specified.
        if not receiver:
            receiver = SETTINGS["email.receiver"]

        msg = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self) -> None:
        """"""
        while self.active:
            try:
                msg = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                    SETTINGS["email.server"], SETTINGS["email.port"]
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self) -> None:
        """"""
        self.active = True
        self.thread.start()

    def close(self) -> None:
        """"""
        if not self.active:
            return

        self.active = False
        self.thread.join()


class TransactionPushEngine(BaseEngine):
    """
    交易推送引擎:
        从数据库上读取成交单数据推送到强制平仓组件、策略持仓组件、策略平仓组件。
    """
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(TransactionPushEngine, self).__init__(main_engine, event_engine, "forced_liquidation")
        self.orderRef_trade: Dict[str, TradeRecordData] = {}
        self.uTime: datetime = datetime(1970, 1, 1)
        self.hold_record_dict: Dict[str, TradeRecordData] = {}
        self.max_loss_dict: Dict[str, float] = {}
        self.margin_dict: Dict[str, float] = {}
        self.count: int = 0
        self.hold_record_set: set = set()

        # 策略是否再开仓操作
        self.strategy_is_open_dict: Dict[str, bool] = {}
        self.get_strategy_is_open()

        self.current_trade_date = current_trade_date(datetime.now())

        # 定时执行操作
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def get_strategy_is_open(self):
        """查询数据库判断策略是否再开仓"""
        query_set = StrategyNameModel().select_strategy_data()
        for queryset in query_set:
            self.strategy_is_open_dict[queryset.strategy_class_name] = queryset.open_is

    def transaction_data_update_push(self):
        """
        交易数据更新推送定时任务函数:
            查询数据库,把相关的数据封装成事件对象推送给相应的组件。
            1、推送给策略持仓组件。
            2、推送给策略平仓组件。
            3、推送给是否继续开仓组件。
        """
        account_id = self.main_engine.get_gateway('CTP').td_api.userid
        # 查询数据库中获取成交单数据
        trade_data_list = TradeDataModel().select().where(
            (TradeDataModel.account_id == account_id)
            & (TradeDataModel.utime > self.uTime)
            & (TradeDataModel.utime < datetime.now() - timedelta(seconds=1))).order_by(TradeDataModel.atime)

        oms = self.main_engine.get_engine('oms')
        for trade_data in trade_data_list:
            symbol_letter = get_letter_from_symbol(trade_data.symbol)
            vt_symbol = f"{trade_data.symbol}.{trade_data.exchange}"
            the_contract = oms.get_contract(vt_symbol)

            if the_contract:  # 从合约中查询保证金率、价格最小跳动、合约乘数。
                margin_ratio = the_contract.LongMarginRatio  # 注意多头保证率和空头保证金率是一样的,所以不用区分多和空。
                price_tick = the_contract.pricetick
                the_contract_multiplier = the_contract.size
            else:
                margin_ratio = ContractMarginRatio.get(symbol_letter)  # 保证金比率
                price_tick = ContractPricePick.get(symbol_letter)  # 价格最小变化
                the_contract_multiplier = ContractMultiplier.get(symbol_letter)  # 合约乘数
            # 个人投资的保证金率 = 交易所的保证金率+期货公司的保证金率
            margin_ratio += FuturesCompanySpread.get(symbol_letter, 0)  # 加上期货公司增收保证金

            if trade_data.offset == 'OPEN':
                offset = Offset.OPEN
            else:
                offset = Offset.CLOSE

            # 开仓
            if offset == Offset.OPEN:
                un_volume = int(abs(trade_data.un_volume)) if trade_data.un_volume else 0  # 未平仓的量
                if trade_data.direction == 'LONG':
                    direction_open = Direction.LONG
                    real_volume = un_volume  # 实际持仓量(多头为正,空头为负)
                else:
                    direction_open = Direction.SHORT
                    real_volume = un_volume * (-1)

                order_data = OrderDataModel().select().where(
                    (OrderDataModel.orderid == trade_data.orderid))
                if order_data:
                    theoretical_open_price = order_data[0].price  # 理论开仓价
                else:
                    theoretical_open_price = 0

                transaction_data = TradeRecordData(
                    symbol=trade_data.symbol,
                    exchange=Exchange(trade_data.exchange),
                    account_id=trade_data.account_id,
                    orderid=trade_data.orderid,
                    order_ref=trade_data.order_ref,
                    direction=direction_open,
                    offset=offset,
                    open_price=trade_data.price,
                    loss_price=trade_data.loss_price if trade_data.loss_price else 0,
                    win_price=trade_data.win_price if trade_data.win_price else 0,
                    volume=un_volume,
                    real_volume=real_volume,
                    trade_date=trade_data.trade_date,
                    strategy_class_name=trade_data.strategy_class_name,
                    strategy_name=trade_data.strategy_name,
                    gateway_name=trade_data.gateway_name,
                    margin_ratio=margin_ratio,
                    price_tick=price_tick,
                    contract_multiplier=the_contract_multiplier,
                )
                transaction_data.symbol_letter = symbol_letter
                transaction_data.opening_volume = trade_data.volume  # 开仓量
                self.orderRef_trade[transaction_data.order_ref] = transaction_data

                open_price = transaction_data.open_price  # 实际开仓价
                # 计算占用的保证金 （= 开仓价 * 实际成交量 * 合约乘数 * 保证金率）
                transaction_data.margin = round(abs(open_price * real_volume * the_contract_multiplier * margin_ratio), 2)
                # 计算最大亏损(单笔)
                transaction_data.max_loss = round((transaction_data.loss_price - transaction_data.open_price) * real_volume * the_contract_multiplier, 2)

                self.uTime = max(self.uTime, trade_data.utime)  # self.uTime变成成交单的修改时间,当成交单为当前时间时,上面的查表操作相当于查询最新的数据,查询过的不会再去查询。

                if real_volume > 0:  # 做多
                    open_slippage_sign = (-1)  # 开仓滑点系数
                else:  # 做空
                    open_slippage_sign = 1
                # 计算开仓滑点(= 滑点系数 * (实际开仓价 - 理论开仓价）/ 价格最小跳动)
                transaction_data.open_slippage = round(open_slippage_sign * (transaction_data.open_price - theoretical_open_price) / price_tick)

                transaction_data.current_trade_date = current_trade_date(transaction_data.trade_date)

                if transaction_data.volume or (transaction_data.orderid in self.hold_record_dict.keys()):

                    event = Event(EVENT_STRATEGY_HOLD_POSITION, transaction_data)  # 推送事件给策略持仓组件
                    self.event_engine.put(event)

                    event = Event(EVENT_FORCED_LIQUIDATION, transaction_data)      # 推送事件给强制平仓组件
                    self.event_engine.put(event)

                    if transaction_data.volume:
                        self.hold_record_dict[transaction_data.orderid] = transaction_data  # 成交量不为0的交易单数据,用持仓字典存储起来(表示保留这条记录)。
                    else:
                        self.hold_record_dict.pop(transaction_data.orderid)  # 成交量为0的话，从持仓字典中删除(表示删除这条记录)。

                    self.max_loss_dict[transaction_data.orderid] = transaction_data.max_loss
                    self.margin_dict[transaction_data.orderid] = transaction_data.margin
            # 平仓
            elif (offset != Offset.OPEN) and (trade_data.order_ref in self.orderRef_trade):
                """
                trade_data.order_ref in self.orderRef_trade这行代码说明:
                    self.orderRef_trade的键是开仓单的order_ref,平仓单的order_ref能在开仓单order_ref中找到,才能证明平仓的是策略开仓的单,否则就是手动开仓没有指定策略名的单。
                    手动开仓没有指定策略名的单是不能计算出止损价和止盈价等等的。
                """
                transaction_data = copy(self.orderRef_trade[trade_data.order_ref])
                transaction_data.close_date = trade_data.trade_date
                transaction_data.orderid = trade_data.orderid
                transaction_data.close_price = trade_data.price
                transaction_data.volume = int(trade_data.volume)
                transaction_data.loss_price = trade_data.loss_price if trade_data.loss_price else 0
                transaction_data.win_price = trade_data.win_price if trade_data.win_price else 0

                if transaction_data.direction == Direction.LONG:
                    real_volume = transaction_data.volume
                else:
                    real_volume = transaction_data.volume * (-1)

                transaction_data.profit = round((transaction_data.close_price - transaction_data.open_price) * real_volume * the_contract_multiplier, 2)  # 盈亏
                close_price = transaction_data.close_price
                transaction_data.margin = round(abs(close_price * real_volume * the_contract_multiplier * margin_ratio), 2)  # 保证金
                transaction_data.profit_margin_ratio = str(round(transaction_data.profit * 100 / transaction_data.margin, 2)) + '%'  # 盈亏保证金比

                # 判断平仓是止盈平仓还是止损平仓(平仓价越接近止盈价,就说明以止盈价平仓的这就止盈平仓,反则就是止损平仓)
                if abs(transaction_data.close_price - transaction_data.loss_price) >= abs(transaction_data.close_price - transaction_data.win_price):  # 止盈
                    theoretical_close_price = transaction_data.win_price  # 理论平仓价
                else:
                    theoretical_close_price = transaction_data.loss_price

                if real_volume > 0:  # 做多
                    close_slippage_sign = 1  # 平仓滑点系数
                else:  # 做空
                    close_slippage_sign = (-1)
                # 计算平仓滑点
                transaction_data.close_slippage = round(close_slippage_sign * (transaction_data.close_price - theoretical_close_price) / price_tick)

                event = Event(EVENT_STRATEGY_CLOSE_POSITION, transaction_data)  # 推送事件给策略平仓组件
                self.event_engine.put(event)

                self.uTime = max(self.uTime, trade_data.utime)

        # 开仓价字典:以symbol为键,[]为值,[]中的元素为单品种的每笔开仓价的值。
        symbol_open_price_dict: {str: list} = defaultdict(list)

        # 持续开仓记录清零
        for strategy_name in self.hold_record_set:
            transaction_data = StrategyHoldData(
                strategy_name=strategy_name,
                volume=0,
            )
            event = Event(EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, transaction_data)
            self.event_engine.put(event)
        self.hold_record_set: set = set()

        # 更新最大亏损,盈亏,保证多比率
        for orderid, transaction_data in self.hold_record_dict.items():
            vt_symbol = transaction_data.vt_symbol
            the_contract = oms.get_contract(vt_symbol)

            if the_contract:  # 查看是否获取合约的基本信息
                margin_ratio = the_contract.LongMarginRatio
                margin_ratio += FuturesCompanySpread.get(transaction_data.symbol_letter, 0)
            else:
                margin_ratio = transaction_data.margin_ratio

            # 保存开仓价到对应字典中( 比如:rb2103以100成交3手。{rb2103:[100,100,100]} ),用于后面计算品种均价。
            for num in range(transaction_data.volume):
                symbol_open_price_dict[transaction_data.symbol].append(transaction_data.open_price)

            if vt_symbol in self.main_engine.engines['oms'].ticks.keys():
                last_price = self.main_engine.engines['oms'].ticks[vt_symbol].last_price
                transaction_data.profit = round((last_price - transaction_data.open_price) * transaction_data.real_volume * transaction_data.contract_multiplier, 2)  # 盈亏
                if transaction_data.current_trade_date == self.current_trade_date:
                    open_price = transaction_data.open_price
                else:
                    open_price = self.main_engine.engines['oms'].ticks[vt_symbol].pre_settlement_price
                transaction_data.margin = round(abs(open_price * transaction_data.real_volume * transaction_data.contract_multiplier * margin_ratio), 2)
                self.margin_dict[transaction_data.orderid] = transaction_data.margin  # 使用实时价格计算保证金,更加合理。

                if transaction_data.direction == Direction.LONG:
                    loss_block = transaction_data.open_price - transaction_data.loss_price
                    profit_block = (last_price - transaction_data.open_price)
                else:
                    loss_block = (transaction_data.open_price - transaction_data.loss_price) * (-1)
                    profit_block = (last_price - transaction_data.open_price) * (-1)
                if loss_block > 0:
                    transaction_data.profit_loss_rate = round(profit_block / loss_block, 3)
                else:
                    transaction_data.profit_loss_rate = round(profit_block, 3)
            else:
                transaction_data.profit = 0
                transaction_data.profit_loss_rate = 0

            if transaction_data.margin > 0:
                transaction_data.profit_margin_ratio = str(round(transaction_data.profit * 100 / transaction_data.margin, 2)) + '%'  # 盈亏保证金比
            else:
                transaction_data.profit_margin_ratio = 0

            event = Event(EVENT_STRATEGY_HOLD_POSITION, transaction_data)  # 推送事件给策略持仓组件
            self.event_engine.put(event)

            event = Event(EVENT_FORCED_LIQUIDATION, transaction_data)   # 推送事件给强制平仓组件
            self.event_engine.put(event)

            transaction_data = copy(transaction_data)

            transaction_data.is_opening = self.strategy_is_open_dict.get(transaction_data.strategy_class_name, True)
            if transaction_data.is_opening:
                transaction_data.is_opening = '是'  # 是否继续开仓
            else:
                transaction_data.is_opening = '否'

            event = Event(EVENT_STRATEGY_WHETHER_CONTINUE_OPEN, transaction_data)  # 推送事件给策略是否继续开仓组件
            self.event_engine.put(event)

            self.hold_record_set.add(transaction_data.strategy_name)

        # 设置品种的获取持仓均值
        for symbol in symbol_open_price_dict.keys():
            oms.set_symbol_ma_price(symbol, round(mean(symbol_open_price_dict[symbol]), 2))
        # 设置持仓总保证金和最大亏损总和
        oms.set_account_margin_loss(account_id, round(sum(self.margin_dict.values()), 2), round(sum(filter(lambda x: x < 0, self.max_loss_dict.values())), 2))

    def process_timer_event(self, event):
        self.count += 1
        if self.count < 10:  # 10 秒刷新一次。
            return
        self.count = 0
        self.transaction_data_update_push()


class TimerEngine(BaseEngine):
    """
    定时任务引擎
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(TimerEngine, self).__init__(main_engine, event_engine, "time_operation")
        self.count: int = 0
        # 用定时任务事件注册,构构建一个定时任务。
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def process_timer_event(self, event):
        self.count += 1
        if self.count < 30:  # 30秒刷新一次
            return
        self.count = 0
        self.update_risk_ctrl_info()

    def update_risk_ctrl_info(self):
        """更新风险控制信息相关数据"""
        oms = self.main_engine
        account_id = self.main_engine.get_gateway('CTP').td_api.userid

        if not account_id:
            return
        if self.main_engine.get_all_active_orders():
            return
        risk_ctrl_info(oms, account_id)
