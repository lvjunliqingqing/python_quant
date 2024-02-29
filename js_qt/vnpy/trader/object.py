"""
Basic data structure used for general trading function in VN Trader.
"""

from dataclasses import dataclass
from datetime import datetime
from logging import INFO

from .constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source
    and should inherit base data.
    """

    gateway_name: str


@dataclass
class TickData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0
    pre_settlement_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    exchange: Exchange
    orderid: str = ""
    order_ref: str = ""
    order_local_id: str = ""
    order_sys_id: str = ""
    account_id: str = ""
    balance: float = 0
    frozen: float = 0
    type: OrderType = OrderType.LIMIT
    direction: Direction = ""
    offset: Offset = Offset.NONE
    run_type: str = ""
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""
    status_msg: str = ""
    order_time: str = ""

    strategy_name: str = ""
    strategy_class_name: str = ""
    strategy_author: str = ""
    time: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"

    def is_active(self) -> bool:
        """
        Check if the order is active.
        """
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self) -> "CancelRequest":
        """
        Create cancel request object from order.
        """
        req = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = None
    userid: str = ""
    order_local_id: str = ""
    order_sys_id: str = ""
    order_ref: str = ""
    account_id: str = ""
    direction: Direction = ""
    strategy_name: str = ""
    strategy_class_name: str = ""
    strategy_author: str = ""
    order_time: str = ""
    run_type: str = ""
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    datetime: datetime = None
    trade_date: str = ""
    time: str = ""
    frozen: float = 0
    win_price: float = 0
    loss_price: float = 0
    price_sell: float = 0
    p_orderid: str = ""
    trade_option: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"

@dataclass
class TradeRecordData(BaseData):
    """
    交易记录数据对象
    """
    symbol: str
    exchange: Exchange
    account_id: str
    strategy_name: str
    strategy_class_name: str
    orderid: str
    order_ref: str
    direction: Direction
    offset: Offset
    open_price: float  # 开仓价
    open_slippage: float = 0.0  # 开仓滑点
    loss_price: float = 0.0
    max_loss: float = 0.0
    win_price: float = 0.0
    close_price: float = 0.0  # 平仓价
    close_slippage: float = 0.0
    volume: int = 0
    un_volume: int = 0  # 未平仓量(持仓量)
    real_volume: float = 0  # 实际成交量
    trade_date: datetime = None  # 开仓时间
    close_date: datetime = None  # 平仓时间
    profit: float = 0.0  # 盈亏
    margin: float = 0.0  # 保证金
    profit_margin_ratio: float = 0.0  # 盈亏保证金比
    margin_ratio: float = 0.0  # 保证金率
    price_tick: float = 0.0  # 最小价格跳动
    contract_multiplier: float = 0.0  # 合约乘数

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

@dataclass
class StrategyHoldData():
    """
    读取数据库，生成一个策略的完整成交单
    """
    strategy_name: str
    volume: int = 0

@dataclass
class PositionData(BaseData):
    """
    Positon data is used for tracking each individual position holding.
    """

    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0
    position_date: str = ""
    account_id: str = ""
    broker_id: str = ""
    hedge_flag: int = 1
    yd_position: float = 0
    position: float = 0
    long_frozen: float = 0
    short_frozen: float = 0
    long_frozen_amount: float = 0
    short_frozen_amount: float = 0
    open_volume: float = 0
    close_volume: float = 0
    open_amount: float = 0
    close_amount: float = 0
    position_cost: float = 0
    pre_margin: float = 0
    use_margin: float = 0
    frozen_margin: float = 0
    frozen_cash: float = 0
    frozen_commission: float = 0
    cash_in: float = 0
    commission: float = 0
    close_profit: float = 0
    position_profit: float = 0
    presettlement_price: float = 0
    settlement_price: float = 0
    trading_day: float = 0
    settlement_id: str = ""
    open_cost: float = 0
    exchange_margin: float = 0
    comb_position: float = 0
    comb_long_frozen: float = 0
    comb_short_frozen: float = 0
    close_profit_by_date: float = 0
    close_profit_by_trade: float = 0
    today_position: float = 0
    margin_rate_by_volume: float = 0
    margin_rate_by_money: float = 0
    strike_frozen: float = 0
    strike_frozen_amount: float = 0
    abandon_frozen: float = 0
    yd_strike_frozen: float = 0
    invest_unit_id: str = ""
    position_cost_offset: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid = f"{self.vt_symbol}.{self.direction.value}"


@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """

    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self):
        """"""
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self):
        """"""
        self.time = datetime.now()


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    """

    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: int
    pricetick: float

    min_volume: float = 1           # minimum trading volume of the contract
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume
    history_data: bool = False      # whether gateway provides bar history data

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_expiry: datetime = None
    option_portfolio: str = ""
    option_index: str = ""          # for identifying options with same strike price

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class SubscribeRequest:
    """
    Request sending to specific gateway for subscribing tick data update.
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    Request sending to specific gateway for creating a new order.
    """

    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""
    order_ref: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str) -> OrderData:
        """
        Create order data from request.
        """
        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            reference=self.reference,
            order_ref=self.order_ref,
            gateway_name=gateway_name,
        )
        return order


@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """

    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    Request sending to specific gateway for querying history data.
    """

    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime = None
    interval: Interval = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

@dataclass
class SymbolWinRate:
    """
    记录各个品种的胜率
    """

    symbol: str
    exchange: Exchange
    win_rate: float