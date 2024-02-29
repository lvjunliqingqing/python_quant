"""
"""
import os
import sys
from datetime import datetime, timedelta
from time import sleep

import pytz
from dateutil.parser import parse
from pandas import read_pickle, to_pickle

from vnpy.api.ctp import (
    MdApi,
    TdApi,
    THOST_FTDC_OAS_Submitted,
    THOST_FTDC_OAS_Accepted,
    THOST_FTDC_OAS_Rejected,
    THOST_FTDC_OST_NoTradeQueueing,
    THOST_FTDC_OST_PartTradedQueueing,
    THOST_FTDC_OST_AllTraded,
    THOST_FTDC_OST_Canceled,
    THOST_FTDC_D_Buy,
    THOST_FTDC_D_Sell,
    THOST_FTDC_PD_Long,
    THOST_FTDC_PD_Short,
    THOST_FTDC_OPT_LimitPrice,
    THOST_FTDC_OPT_AnyPrice,
    THOST_FTDC_OF_Open,
    THOST_FTDC_OFEN_Close,
    THOST_FTDC_OFEN_CloseYesterday,
    THOST_FTDC_OFEN_CloseToday,
    THOST_FTDC_PC_Futures,
    THOST_FTDC_PC_Options,

    THOST_FTDC_PC_SpotOption,

    THOST_FTDC_PC_Combination,
    THOST_FTDC_CP_CallOptions,
    THOST_FTDC_CP_PutOptions,
    THOST_FTDC_HF_Speculation,
    THOST_FTDC_CC_Immediately,
    THOST_FTDC_FCC_NotForceClose,
    THOST_FTDC_TC_GFD,
    THOST_FTDC_VC_AV,
    THOST_FTDC_TC_IOC,
    THOST_FTDC_VC_CV,
    THOST_FTDC_AF_Delete
)
from vnpy.controller.global_variable import get_value, set_value
from vnpy.controller.trade_operation import get_order_ref_value, current_trade_date
from vnpy.event import Event
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    OrderType,
    Product,
    Status,
    OptionType
)
from vnpy.trader.event import EVENT_TIMER, EVENT_DOMINANT_CONTRACT_TRADE
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest)
from vnpy.trader.symbol_attr import SymbolCommission
from vnpy.trader.utility import get_folder_path, load_json

STATUS_CTP2VT = {
    THOST_FTDC_OAS_Submitted: Status.SUBMITTING,
    THOST_FTDC_OAS_Accepted: Status.SUBMITTING,
    THOST_FTDC_OAS_Rejected: Status.REJECTED,
    THOST_FTDC_OST_NoTradeQueueing: Status.NOTTRADED,
    THOST_FTDC_OST_PartTradedQueueing: Status.PARTTRADED,
    THOST_FTDC_OST_AllTraded: Status.ALLTRADED,
    THOST_FTDC_OST_Canceled: Status.CANCELLED
}

DIRECTION_VT2CTP = {
    Direction.LONG: THOST_FTDC_D_Buy,
    Direction.SHORT: THOST_FTDC_D_Sell
}
DIRECTION_CTP2VT = {v: k for k, v in DIRECTION_VT2CTP.items()}
DIRECTION_CTP2VT[THOST_FTDC_PD_Long] = Direction.LONG
DIRECTION_CTP2VT[THOST_FTDC_PD_Short] = Direction.SHORT

ORDERTYPE_VT2CTP = {
    OrderType.LIMIT: THOST_FTDC_OPT_LimitPrice,
    OrderType.MARKET: THOST_FTDC_OPT_AnyPrice
}
ORDERTYPE_CTP2VT = {v: k for k, v in ORDERTYPE_VT2CTP.items()}

OFFSET_VT2CTP = {
    Offset.OPEN: THOST_FTDC_OF_Open,
    Offset.CLOSE: THOST_FTDC_OFEN_Close,
    Offset.CLOSETODAY: THOST_FTDC_OFEN_CloseToday,
    Offset.CLOSEYESTERDAY: THOST_FTDC_OFEN_CloseYesterday,
}
OFFSET_CTP2VT = {v: k for k, v in OFFSET_VT2CTP.items()}

EXCHANGE_CTP2VT = {
    "CFFEX": Exchange.CFFEX,
    "SHFE": Exchange.SHFE,
    "CZCE": Exchange.CZCE,
    "DCE": Exchange.DCE,
    "INE": Exchange.INE
}

PRODUCT_CTP2VT = {
    THOST_FTDC_PC_Futures: Product.FUTURES,
    THOST_FTDC_PC_Options: Product.OPTION,

    THOST_FTDC_PC_SpotOption: Product.OPTION,

    THOST_FTDC_PC_Combination: Product.SPREAD
}

OPTIONTYPE_CTP2VT = {
    THOST_FTDC_CP_CallOptions: OptionType.CALL,
    THOST_FTDC_CP_PutOptions: OptionType.PUT
}

MAX_FLOAT = sys.float_info.max
CHINA_TZ = pytz.timezone("Asia/Shanghai")


symbol_exchange_map = {}
symbol_name_map = {}
symbol_size_map = {}


class CtpGateway(BaseGateway):
    """
    VN Trader Gateway for CTP .
    """

    default_setting = {
        "用户名": "",
        "密码": "",
        "经纪商代码": "",
        "交易服务器": "",
        "行情服务器": "",
        "产品名称": "",
        "授权编码": "",
        "产品信息": ""
    }

    exchanges = list(EXCHANGE_CTP2VT.values())

    def __init__(self, event_engine):
        """Constructor"""
        super().__init__(event_engine, "CTP")

        self.td_api = CtpTdApi(self, event_engine)
        self.md_api = CtpMdApi(self)

    def connect(self, setting: dict):
        """"""
        userid = setting["用户名"]
        password = setting["密码"]
        brokerid = setting["经纪商代码"]
        td_address = setting["交易服务器"]
        md_address = setting["行情服务器"]
        appid = setting["产品名称"]
        auth_code = setting["授权编码"]
        product_info = setting["产品信息"]

        if (
            (not td_address.startswith("tcp://"))
            and (not td_address.startswith("ssl://"))
        ):
            td_address = "tcp://" + td_address

        if (
            (not md_address.startswith("tcp://"))
            and (not md_address.startswith("ssl://"))
        ):
            md_address = "tcp://" + md_address

        self.td_api.connect(td_address, userid, password, brokerid, auth_code, appid, product_info)
        self.md_api.connect(md_address, userid, password, brokerid)

        self.init_query()

    def getSesionFrontid(self):
        return self.td_api.getSesionFrontid()

    def subscribe(self, req: SubscribeRequest):
        """"""
        self.md_api.subscribe(req)

    def send_order(self, req: OrderRequest):
        """"""
        if req.type == OrderType.RFQ:
            vt_orderid = self.td_api.send_rfq(req)
        else:
            vt_orderid = self.td_api.send_order(req)
        return vt_orderid

    def cancel_order(self, req: CancelRequest):
        """"""
        self.td_api.cancel_order(req)

    def query_commission(self):
        """查询手续费数据"""
        self.td_api.query_commission()

    def query_account(self):
        """"""
        self.td_api.query_account()

    def query_position(self):
        """"""
        self.td_api.query_position()

    def query_position_detail(self):
        """"""
        self.td_api.query_position_detail()

    def close(self):
        """"""
        self.td_api.close()
        self.md_api.close()

    def write_error(self, msg: str, error: dict):
        """"""
        error_id = error["ErrorID"]
        error_msg = error["ErrorMsg"]
        msg = f"{msg}，代码：{error_id}，信息：{error_msg}"
        self.write_log(msg)

    def process_timer_event(self, event):
        """"""
        self.count += 1
        if self.count < 2:
            return
        self.count = 0

        func = self.query_functions.pop(0)
        func()
        self.query_functions.append(func)

        self.md_api.update_date()

    def init_query(self):
        """"""
        self.count = 0
        self.query_functions = [self.query_position, self.query_position_detail, self.query_account]
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)


class CtpMdApi(MdApi):
    """"""

    def __init__(self, gateway):
        """Constructor"""
        super(CtpMdApi, self).__init__()

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.reqid = 0

        self.connect_status = False
        self.login_status = False
        self.subscribed = set()

        self.userid = ""
        self.password = ""
        self.brokerid = ""

        self.current_date = datetime.now().strftime("%Y%m%d")

    def onFrontConnected(self):
        """
        Callback when front server is connected.
        """
        self.gateway.write_log("行情服务器连接成功")
        self.login()

    def onFrontDisconnected(self, reason: int):
        """
        Callback when front server is disconnected.
        """
        self.login_status = False
        self.gateway.write_log(f"行情服务器连接断开，原因{reason}")

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback when user is logged in.
        """
        if not error["ErrorID"]:
            self.login_status = True
            self.gateway.write_log("行情服务器登录成功")

            for symbol in self.subscribed:
                self.subscribeMarketData(symbol)
        else:
            self.gateway.write_error("行情服务器登录失败", error)

    def onRspError(self, error: dict, reqid: int, last: bool):
        """
        Callback when error occured.
        """
        self.gateway.write_error("行情接口报错", error)

    def onRspSubMarketData(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error or not error["ErrorID"]:
            return

        self.gateway.write_error("行情订阅失败", error)

    def onRtnDepthMarketData(self, data: dict):
        """
        Callback of tick data update.
        """
        # Filter data update with no timestamp
        if not data["UpdateTime"]:
            return

        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            return

        timestamp = f"{self.current_date} {data['UpdateTime']}.{int(data['UpdateMillisec']/100)}"
        dt = datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f")
        dt = CHINA_TZ.localize(dt)

        tick = TickData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            name=symbol_name_map[symbol],
            volume=data["Volume"],
            open_interest=data["OpenInterest"],
            last_price=data["LastPrice"],
            limit_up=data["UpperLimitPrice"],
            limit_down=data["LowerLimitPrice"],
            open_price=adjust_price(data["OpenPrice"]),
            high_price=adjust_price(data["HighestPrice"]),
            low_price=adjust_price(data["LowestPrice"]),
            pre_close=adjust_price(data["PreClosePrice"]),
            bid_price_1=adjust_price(data["BidPrice1"]),
            ask_price_1=adjust_price(data["AskPrice1"]),
            bid_volume_1=data["BidVolume1"],
            ask_volume_1=data["AskVolume1"],
            gateway_name=self.gateway_name,
            pre_settlement_price=data["PreSettlementPrice"]
        )
        tick.pre_settlement_price = data["PreSettlementPrice"]  # 昨日结算价

        if data["BidVolume2"] or data["AskVolume2"]:
            tick.bid_price_2 = adjust_price(data["BidPrice2"])
            tick.bid_price_3 = adjust_price(data["BidPrice3"])
            tick.bid_price_4 = adjust_price(data["BidPrice4"])
            tick.bid_price_5 = adjust_price(data["BidPrice5"])

            tick.ask_price_2 = adjust_price(data["AskPrice2"])
            tick.ask_price_3 = adjust_price(data["AskPrice3"])
            tick.ask_price_4 = adjust_price(data["AskPrice4"])
            tick.ask_price_5 = adjust_price(data["AskPrice5"])

            tick.bid_volume_2 = data["BidVolume2"]
            tick.bid_volume_3 = data["BidVolume3"]
            tick.bid_volume_4 = data["BidVolume4"]
            tick.bid_volume_5 = data["BidVolume5"]

            tick.ask_volume_2 = data["AskVolume2"]
            tick.ask_volume_3 = data["AskVolume3"]
            tick.ask_volume_4 = data["AskVolume4"]
            tick.ask_volume_5 = data["AskVolume5"]

        self.gateway.on_tick(tick)

    def connect(self, address: str, userid: str, password: str, brokerid: int):
        """
        Start connection to server.
        """
        self.userid = userid
        self.password = password
        self.brokerid = brokerid

        # If not connected, then start connection first.
        if not self.connect_status:
            path = get_folder_path(self.gateway_name.lower())
            self.createFtdcMdApi((str(path) + "\\Md").encode("GBK"))

            self.registerFront(address)
            self.init()

            self.connect_status = True
        # If already connected, then login immediately.
        elif not self.login_status:
            self.login()

    def login(self):
        """
        Login onto server.
        """
        req = {
            "UserID": self.userid,
            "Password": self.password,
            "BrokerID": self.brokerid
        }

        self.reqid += 1
        self.reqUserLogin(req, self.reqid)

    def subscribe(self, req: SubscribeRequest):
        """
        Subscribe to tick data update.
        """
        if self.login_status:
            self.subscribeMarketData(req.symbol)
        self.subscribed.add(req.symbol)

    def close(self):
        """
        Close the connection.
        """
        if self.connect_status:
            self.exit()

    def update_date(self):
        """"""
        self.current_date = datetime.now().strftime("%Y%m%d")


class CtpTdApi(TdApi):
    """"""

    def __init__(self, gateway, event_engine):
        """Constructor"""
        super(CtpTdApi, self).__init__()

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name
        self.event_engine = event_engine

        self.reqid = 0
        self.order_ref = 0

        self.connect_status = False
        self.login_status = False
        self.auth_status = False
        self.login_failed = False
        self.contract_inited = False

        self.userid = ""
        self.password = ""
        self.brokerid = ""
        self.auth_code = ""
        self.appid = ""
        self.product_info = ""

        self.frontid = 0
        self.sessionid = 0

        self.order_data = []
        self.trade_data = []
        self.positions = {}
        self.sysid_orderid_map = {}

        self.list_instrument = []

        self.mark_read_log = True
        self.mark_dominant_contract_trade = True

    def onFrontConnected(self):
        """"""
        self.gateway.write_log("交易服务器连接成功")

        if self.auth_code:
            self.authenticate()
        else:
            self.login()

    def onFrontDisconnected(self, reason: int):
        """"""
        self.login_status = False
        self.gateway.write_log(f"交易服务器连接断开，原因{reason}")

    def onRspAuthenticate(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error['ErrorID']:
            self.auth_status = True
            self.gateway.write_log("交易服务器授权验证成功")
            self.login()
        else:
            self.gateway.write_error("交易服务器授权验证失败", error)

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error["ErrorID"]:
            self.frontid = data["FrontID"]
            self.sessionid = data["SessionID"]
            self.login_status = True
            self.gateway.write_log("交易服务器登录成功")

            # Confirm settlement
            req = {
                "BrokerID": self.brokerid,
                "InvestorID": self.userid
            }
            self.reqid += 1
            self.reqSettlementInfoConfirm(req, self.reqid)
        else:
            self.login_failed = True

            self.gateway.write_error("交易服务器登录失败", error)

    def getSesionFrontid(self):
        # return str(self.frontid) + "_" + str(self.sessionid)[2:].ljust(9, '0')
        return str(self.frontid) + "_" + str(self.sessionid)

    def onRspOrderInsert(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        order_ref = data["OrderRef"]
        orderid = f"{self.frontid}_{self.sessionid}_{order_ref}"

        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map[symbol]

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            order_ref=order_ref,
            orderid=orderid,
            account_id=data['InvestorID'],
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT.get(data["CombOffsetFlag"], Offset.NONE),
            price=data["LimitPrice"],
            volume=data["VolumeTotalOriginal"],
            status=Status.REJECTED,
            gateway_name=self.gateway_name
        )
        self.gateway.on_order(order)

        self.gateway.write_error("交易委托失败", error)

    def onRspOrderAction(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        self.gateway.write_error("交易撤单失败", error)

    def onRspQueryMaxOrderVolume(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        pass

    def onRspSettlementInfoConfirm(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of settlment info confimation.
        """
        self.gateway.write_log("结算信息确认成功")

        while True:
            self.reqid += 1
            n = self.reqQryInstrument({}, self.reqid)

            if not n:
                break
            else:
                sleep(1)

        # 这里读取日志的pickle文件
        if self.mark_read_log:
            self.mark_read_log = False
            self.pickle_name = f"{self.userid}.pkl"
            if self.pickle_name not in os.listdir("."):
                event_cta_log = []
            else:
                event_cta_log = read_pickle(self.pickle_name)

            the_day = datetime.now() + timedelta(hours=6)
            # 如果今天是周一、六、日则返回上周五的日期时间,否则返回上前一天的日期时间。
            if the_day.isoweekday() in [1, 6, 7]:
                if the_day.isoweekday() == 1:
                    compare_time = (the_day - timedelta(days=3)).replace(hour=19, minute=0, second=0)
                elif the_day.isoweekday() == 6:
                    compare_time = (the_day - timedelta(days=1)).replace(hour=19, minute=0, second=0)
                elif the_day.isoweekday() == 7:
                    compare_time = (the_day - timedelta(days=2)).replace(hour=19, minute=0, second=0)
            else:
                compare_time = (the_day - timedelta(days=1)).replace(hour=19, minute=0, second=0)
            for event in event_cta_log:
                if event.data.time > compare_time:
                    self.event_engine.put(event)

            # 读取pickle文件
            self.read_dominant_contract_trade_pickle()

    def read_dominant_contract_trade_pickle(self):
        if f"{self.userid}_dominant_contract_trade.pkl" in os.listdir("."):
            dominant_contract_trade = read_pickle(f"{self.userid}_dominant_contract_trade.pkl")
            now = datetime.now()
            for key, value in dominant_contract_trade.copy().items():
                dt = datetime.utcfromtimestamp(int(value) / 100) + timedelta(hours=8)  # 15:15分：
                now_trade_day = current_trade_date(now + timedelta(hours=3, minutes=45))
                dt_trade_day = current_trade_date(dt + timedelta(hours=3, minutes=45))
                if now_trade_day != dt_trade_day:
                    dominant_contract_trade.pop(key)
            to_pickle(dominant_contract_trade, f"{self.userid}_dominant_contract_trade.pkl")
        else:
            dominant_contract_trade = {}
        set_value('dominant_contract_trade', dominant_contract_trade)

    def onRspQryInvestorPositionDetail(self, data: dict, error: dict, reqid: int, last: bool):
        """
        持仓明细查询回调
        """
        pass

    def onRspQryInvestorPosition(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not data:
            return

        # Check if contract data received
        if data["InstrumentID"] in symbol_exchange_map:
            # Get buffered position object
            key = f"{data['InstrumentID'], data['PosiDirection']}"
            position = self.positions.get(key, None)
            if not position:
                position = PositionData(
                    symbol=data["InstrumentID"],
                    exchange=symbol_exchange_map[data["InstrumentID"]],
                    direction=DIRECTION_CTP2VT[data["PosiDirection"]],
                    gateway_name=self.gateway_name,
                    position_date=data['PositionDate'],
                    account_id=data['InvestorID'],
                    broker_id=data['BrokerID'],
                    hedge_flag=data['HedgeFlag'],
                    yd_position=data['YdPosition'],
                    position=data['Position'],
                    long_frozen=data['LongFrozen'],
                    short_frozen=data['ShortFrozen'],
                    long_frozen_amount=data['LongFrozenAmount'],
                    short_frozen_amount=data['ShortFrozenAmount'],
                    open_volume=data['OpenVolume'],
                    close_volume=data['CloseVolume'],
                    open_amount=data['OpenAmount'],
                    close_amount=data['CloseAmount'],
                    position_cost=data['PositionCost'],
                    pre_margin=data['PreMargin'],
                    use_margin=data['UseMargin'],
                    frozen_margin=data['FrozenMargin'],
                    frozen_cash=data['FrozenCash'],
                    frozen_commission=data['FrozenCommission'],
                    cash_in=data['CashIn'],
                    commission=data['Commission'],
                    close_profit=data['CloseProfit'],
                    position_profit=data['PositionProfit'],
                    presettlement_price=data['PreSettlementPrice'],
                    settlement_price=data['SettlementPrice'],
                    trading_day=data['TradingDay'],
                    settlement_id=data['SettlementID'],
                    open_cost=data['OpenCost'],
                    exchange_margin=data['ExchangeMargin'],
                    comb_position=data['CombPosition'],
                    comb_long_frozen=data['CombLongFrozen'],
                    comb_short_frozen=data['CombShortFrozen'],
                    close_profit_by_date=data['CloseProfitByDate'],
                    close_profit_by_trade=data['CloseProfitByTrade'],
                    today_position=data['TodayPosition'],
                    margin_rate_by_volume=data['MarginRateByMoney'],
                    margin_rate_by_money=data['MarginRateByVolume'],
                    strike_frozen=data['StrikeFrozen'],
                    strike_frozen_amount=data['StrikeFrozenAmount'],
                    abandon_frozen=data['AbandonFrozen'],
                    yd_strike_frozen=data['YdStrikeFrozen'],
                    invest_unit_id=data['InvestUnitID'],
                    position_cost_offset=data['PositionCostOffset'] if hasattr(data, 'PositionCostOffset') else '',
                )
                self.positions[key] = position

            # For SHFE and INE position data update
            if position.exchange in [Exchange.SHFE, Exchange.INE]:
                if data["YdPosition"] and not data["TodayPosition"]:
                    position.yd_volume = data["Position"]
            # For other exchange position data update
            else:
                position.yd_volume = data["Position"] - data["TodayPosition"]

            # Get contract size (spread contract has no size value)
            size = symbol_size_map.get(position.symbol, 0)

            # Calculate previous position cost
            cost = position.price * position.volume * size

            # Update new position volume
            position.volume += data["Position"]
            position.pnl += data["PositionProfit"]

            # Calculate average position price
            if position.volume and size:
                cost += data["PositionCost"]
                position.price = cost / (position.volume * size)

            # Get frozen volume
            if position.direction == Direction.LONG:
                position.frozen += data["ShortFrozen"]
            else:
                position.frozen += data["LongFrozen"]

        if last:
            for position in self.positions.values():
                if position.volume:
                    self.gateway.on_position(position)

            self.positions.clear()

    def onRspQryTradingAccount(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if "AccountID" not in data:
            return

        account = AccountData(
            accountid=data["AccountID"],
            balance=round(data["Balance"], 3),
            frozen=round(data["FrozenMargin"] + data["FrozenCash"] + data["FrozenCommission"], 3),
            gateway_name=self.gateway_name
        )
        account.available = round(data["Available"], 3)

        self.gateway.on_account(account)

    def onRspQryInstrument(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of instrument query.
        """
        product = PRODUCT_CTP2VT.get(data["ProductClass"], None)
        if product:
            contract = ContractData(
                symbol=data["InstrumentID"],
                exchange=EXCHANGE_CTP2VT[data["ExchangeID"]],
                name=data["InstrumentName"],
                product=product,
                size=data["VolumeMultiple"],
                pricetick=data["PriceTick"],
                gateway_name=self.gateway_name,
            )
            contract.LongMarginRatio = data["LongMarginRatio"]  # 多头保证金率
            contract.ShortMarginRatio = data["ShortMarginRatio"]  # 空头保证金
            contract.last = last
            self.list_instrument.append(data["InstrumentID"])

            # For option only
            if contract.product == Product.OPTION:
                # Remove C/P suffix of CZCE option product name
                if contract.exchange == Exchange.CZCE:
                    contract.option_portfolio = data["ProductID"][:-1]
                else:
                    contract.option_portfolio = data["ProductID"]

                contract.option_underlying = data["UnderlyingInstrID"]
                contract.option_type = OPTIONTYPE_CTP2VT.get(data["OptionsType"], None)
                contract.option_strike = data["StrikePrice"]
                contract.option_index = str(data["StrikePrice"])
                contract.option_expiry = datetime.strptime(data["ExpireDate"], "%Y%m%d")

            self.gateway.on_contract(contract)

            symbol_exchange_map[contract.symbol] = contract.exchange
            symbol_name_map[contract.symbol] = contract.name
            symbol_size_map[contract.symbol] = contract.size

        if last:
            self.contract_inited = True
            self.gateway.write_log("合约信息查询成功")

            # 读取 pickle 文件
            self.read_pickle_file()

            for data in self.order_data:
                self.onRtnOrder(data)
            self.order_data.clear()

            for data in self.trade_data:
                self.onRtnTrade(data)
            self.trade_data.clear()

    def read_pickle_file(self):
        if self.mark_dominant_contract_trade:
            self.mark_dominant_contract_trade = False
            self.json_name = f"{self.userid}_dominant_contract_trade.json"
            if self.json_name not in os.listdir(".vntrader"):
                dominant_contract_trade_dict = {}
            else:
                dominant_contract_trade_dict = load_json(self.json_name)
            now = datetime.now()
            dominant_contract_trade = get_value('dominant_contract_trade')
            for order_ref, order_information in dominant_contract_trade_dict.items():
                order_information['account_id'] = self.userid
                dt = datetime.utcfromtimestamp(int(order_information['order_ref']) / 100) + timedelta(
                    hours=8)  # 15:15分：
                now_trade_day = current_trade_date(now + timedelta(hours=3, minutes=45))
                dt_trade_day = current_trade_date(dt + timedelta(hours=3, minutes=45))
                if now_trade_day == dt_trade_day and (order_information['order_ref'] not in dominant_contract_trade.values()):
                    self.event_engine.put(Event(EVENT_DOMINANT_CONTRACT_TRADE, order_information))

    def onRtnOrder(self, data: dict):
        """
        Callback of order status update.
        """
        if not self.contract_inited:
            self.order_data.append(data)
            return

        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map[symbol]

        frontid = data["FrontID"]
        sessionid = data["SessionID"]
        order_ref = data["OrderRef"]
        orderid = f"{frontid}_{sessionid}_{order_ref}"

        timestamp = f"{data['InsertDate']} {data['InsertTime']}"
        dt = datetime.strptime(timestamp, "%Y%m%d %H:%M:%S")
        dt = CHINA_TZ.localize(dt)
        order_time = f"{data['InsertDate']} {data['InsertTime']}"
        order_sys_id = (data["OrderSysID"]).strip()
        order_local_id = (data["OrderLocalID"]).strip()

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            order_local_id=order_local_id,
            order_sys_id=order_sys_id,
            order_ref=order_ref,
            account_id=data['InvestorID'],
            type=ORDERTYPE_CTP2VT[data["OrderPriceType"]],
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["CombOffsetFlag"]],
            price=data["LimitPrice"],
            volume=data["VolumeTotalOriginal"],
            traded=data["VolumeTraded"],
            status=STATUS_CTP2VT[data["OrderStatus"]],
            datetime=dt,
            status_msg=data["StatusMsg"],
            order_time=order_time,
            time=data["InsertTime"],
            gateway_name=self.gateway_name
        )
        self.gateway.on_order(order)

        self.sysid_orderid_map[data["OrderSysID"]] = orderid

    def onRtnTrade(self, data: dict):
        """
        Callback of trade status update.
        """
        if not self.contract_inited:
            self.trade_data.append(data)
            return

        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map[symbol]

        orderid = self.sysid_orderid_map[data["OrderSysID"]]

        timestamp = f"{data['TradeDate']} {data['TradeTime']}"
        dt = datetime.strptime(timestamp, "%Y%m%d %H:%M:%S")
        dt = CHINA_TZ.localize(dt)
        order_sys_id = (data["OrderSysID"]).strip()
        order_local_id = (data["OrderLocalID"]).strip()
        tradeid = (data["TradeID"]).strip()
        order_ref = data['OrderRef']
        trade_date = f"{str(parse(str(data['TradeDate'])))[0:10]} {data['TradeTime']}"

        trade = TradeData(
            symbol=symbol,
            exchange=exchange,
            order_local_id=order_local_id,
            order_sys_id=order_sys_id,
            order_ref=order_ref,
            userid=data['UserID'],
            account_id=data['InvestorID'],
            orderid=orderid,
            tradeid=tradeid,
            trade_date=trade_date,
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["OffsetFlag"]],
            price=data["Price"],
            volume=data["Volume"],
            datetime=dt,
            time=data["TradeTime"],
            gateway_name=self.gateway_name
        )
        self.gateway.on_trade(trade)

    def onRspForQuoteInsert(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error["ErrorID"]:
            symbol = data["InstrumentID"]
            msg = f"{symbol}询价请求发送成功"
            self.gateway.write_log(msg)
        else:
            self.gateway.write_error("询价请求发送失败", error)

    def connect(
        self,
        address: str,
        userid: str,
        password: str,
        brokerid: int,
        auth_code: str,
        appid: str,
        product_info
    ):
        """
        Start connection to server.
        """
        self.userid = userid
        self.password = password
        self.brokerid = brokerid
        self.auth_code = auth_code
        self.appid = appid
        self.product_info = product_info

        if not self.connect_status:
            path = get_folder_path(self.gateway_name.lower())
            self.createFtdcTraderApi((str(path) + "\\Td").encode("GBK"))

            self.subscribePrivateTopic(0)
            self.subscribePublicTopic(0)

            self.registerFront(address)
            self.init()

            self.connect_status = True
        else:
            self.authenticate()

    def authenticate(self):
        """
        Authenticate with auth_code and appid.
        """
        req = {
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "AuthCode": self.auth_code,
            "AppID": self.appid
        }

        if self.product_info:
            req["UserProductInfo"] = self.product_info

        self.reqid += 1
        self.reqAuthenticate(req, self.reqid)

    def login(self):
        """
        Login onto server.
        """
        if self.login_failed:
            return

        req = {
            "UserID": self.userid,
            "Password": self.password,
            "BrokerID": self.brokerid,
            "AppID": self.appid
        }

        if self.product_info:
            req["UserProductInfo"] = self.product_info

        self.reqid += 1
        self.reqUserLogin(req, self.reqid)

    def send_order(self, req: OrderRequest):
        """
        Send new order.
        """
        if req.offset not in OFFSET_VT2CTP:
            self.gateway.write_log("请选择开平方向")
            return ""

        if req.type not in ORDERTYPE_VT2CTP:
            self.gateway.write_log(f"当前接口不支持该类型的委托{req.type.value}")
            return ""

        # self.order_ref += 1
        if hasattr(req, 'order_ref') and req.order_ref:
            self.order_ref = req.order_ref
        else:
            self.order_ref = get_order_ref_value()

        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange.value,
            "LimitPrice": req.price,
            "VolumeTotalOriginal": int(req.volume),
            "OrderPriceType": ORDERTYPE_VT2CTP.get(req.type, ""),
            "Direction": DIRECTION_VT2CTP.get(req.direction, ""),
            "CombOffsetFlag": OFFSET_VT2CTP.get(req.offset, ""),
            "OrderRef": str(self.order_ref),
            "InvestorID": self.userid,
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "CombHedgeFlag": THOST_FTDC_HF_Speculation,
            "ContingentCondition": THOST_FTDC_CC_Immediately,
            "ForceCloseReason": THOST_FTDC_FCC_NotForceClose,
            "IsAutoSuspend": 0,
            "TimeCondition": THOST_FTDC_TC_GFD,
            "VolumeCondition": THOST_FTDC_VC_AV,
            "MinVolume": 1
        }

        if req.type == OrderType.FAK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_AV
        elif req.type == OrderType.FOK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_CV

        self.reqid += 1
        self.reqOrderInsert(ctp_req, self.reqid)

        orderid = f"{self.frontid}_{self.sessionid}_{self.order_ref}"
        order = req.create_order_data(orderid, self.gateway_name)
        self.gateway.on_order(order)

        return order.vt_orderid

    def cancel_order(self, req: CancelRequest):
        """
        Cancel existing order.
        """
        frontid, sessionid, order_ref = req.orderid.split("_")

        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange.value,
            "OrderRef": order_ref,
            "FrontID": int(frontid),
            "SessionID": int(sessionid),
            "ActionFlag": THOST_FTDC_AF_Delete,
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqOrderAction(ctp_req, self.reqid)

    def send_rfq(self, req: OrderRequest) -> str:
        """"""
        self.order_ref += 1

        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange.value,
            "ForQuoteRef": str(self.order_ref),
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqForQuoteInsert(ctp_req, self.reqid)

        orderid = f"{self.frontid}_{self.sessionid}_{self.order_ref}"
        vt_orderid = f"{self.gateway_name}.{orderid}"

        return vt_orderid

    def query_account(self):
        """
        Query account balance data.
        """
        self.reqid += 1
        self.reqQryTradingAccount({}, self.reqid)

    def query_position(self):
        """
        Query position holding data.
        """
        if not symbol_exchange_map:
            return

        req = {
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqQryInvestorPosition(req, self.reqid)

    def query_position_detail(self):
        """
        持仓明细
        """
        if not symbol_exchange_map:
            return

        req = {
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }
        self.reqid += 1
        self.reqQryInvestorPositionDetail(req, self.reqid)

    def query_commission(self):
        # 手续费率查询字典
        if self.list_instrument:
            symbol = self.list_instrument.pop(0)
            self.commission_req = {}
            self.commission_req['BrokerID'] = self.brokerid
            self.commission_req['InvestorID'] = self.userid
            self.commission_req['InstrumentID'] = symbol
            self.reqid += 1
            # 请求查询手续费率
            self.reqQryInstrumentCommissionRate(self.commission_req, self.reqid)

    def onRspQryInstrumentCommissionRate(self, data: dict, error: dict, reqid: int, last: bool):
        """查询合约手续费率"""
        symbol = data.get('InstrumentID', None)
        if symbol:
            if data['OpenRatioByMoney']:
                SymbolCommission[symbol.upper()] = round(data['OpenRatioByMoney'], 7)
            if data['OpenRatioByVolume']:
                SymbolCommission[symbol.upper()] = round(data['OpenRatioByVolume'], 7)

    def close(self):
        """"""
        if self.connect_status:
            self.exit()


def adjust_price(price: float) -> float:
    """"""
    if price == MAX_FLOAT:
        price = 0
    return price
