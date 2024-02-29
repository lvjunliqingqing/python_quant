""""""

from collections import defaultdict
from vnpy.trader.object import OrderRequest, LogData
from vnpy.event import Event, EventEngine, EVENT_TIMER
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import EVENT_TRADE, EVENT_ORDER, EVENT_LOG, EVENT_POSITION, EVENT_ACCOUNT
from vnpy.trader.constant import Status, Offset
from vnpy.trader.utility import load_json, save_json


APP_NAME = "RiskManager"


class RiskManagerEngine(BaseEngine):
    """"""
    setting_filename = "risk_manager_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.active = False

        self.order_flow_count = 0
        self.order_flow_limit = 50

        self.order_flow_clear = 1
        self.order_flow_timer = 0

        self.order_size_limit = 100

        self.trade_count = 0
        self.trade_limit = 1000
        self.account = None
        self.account_funds_availability_rate = 0
        self.account_funds_availability_rate_limit = 80
        self.one_variety_money_rate_limit = 10
        self.order_cancel_limit = 500
        self.order_cancel_counts = defaultdict(int)
        self.position_dict = defaultdict(dict)
        self.active_order_limit = 50

        self.load_setting()
        self.register_event()
        self.patch_send_order()

    def patch_send_order(self):
        """
        Patch send order function of MainEngine.
        """
        self._send_order = self.main_engine.send_order
        self.main_engine.send_order = self.send_order

    def send_order(self, req: OrderRequest, gateway_name: str):
        """"""
        result = self.check_risk(req, gateway_name)
        if not result:
            return ""
        return self._send_order(req, gateway_name)

    def update_setting(self, setting: dict):
        """"""
        self.active = setting["active"]
        self.order_flow_limit = setting["order_flow_limit"]
        self.order_flow_clear = setting["order_flow_clear"]
        self.order_size_limit = setting["order_size_limit"]
        self.trade_limit = setting["trade_limit"]
        self.active_order_limit = setting["active_order_limit"]
        self.order_cancel_limit = setting["order_cancel_limit"]

        if "account_funds_availability_rate_limit" not in setting:
            self.account_funds_availability_rate_limit = 0
        else:
            self.account_funds_availability_rate_limit = setting["account_funds_availability_rate_limit"]

        if "one_variety_money_rate_limit" not in setting:
            self.one_variety_money_rate_limit = 0
        else:
            self.one_variety_money_rate_limit = setting["one_variety_money_rate_limit"]

        if self.active:
            self.write_log("交易风控功能启动")
        else:
            self.write_log("交易风控功能停止")

    def get_setting(self):
        """"""
        setting = {
            "active": self.active,
            "order_flow_limit": self.order_flow_limit,
            "order_flow_clear": self.order_flow_clear,
            "order_size_limit": self.order_size_limit,
            "trade_limit": self.trade_limit,
            "active_order_limit": self.active_order_limit,
            "order_cancel_limit": self.order_cancel_limit,
            "account_funds_availability_rate_limit": self.account_funds_availability_rate_limit,
            "one_variety_money_rate_limit": self.one_variety_money_rate_limit,
        }
        return setting

    def load_setting(self):
        """"""
        setting = load_json(self.setting_filename)
        if not setting:
            return

        self.update_setting(setting)

    def save_setting(self):
        """"""
        setting = self.get_setting()
        save_json(self.setting_filename, setting)

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)

    def process_order_event(self, event: Event):
        """"""
        order = event.data
        if order.status != Status.CANCELLED:
            return
        self.order_cancel_counts[order.symbol] += 1

    def process_trade_event(self, event: Event):
        """"""
        trade = event.data
        self.trade_count += trade.volume

    def process_position_event(self, event: Event):
        postion = event.data
        self.position_dict[postion.vt_positionid] = {postion.vt_symbol: postion}

    def process_account_event(self, event: Event):
        account = event.data
        self.account = account

    def process_timer_event(self, event: Event):
        """"""
        self.order_flow_timer += 1

        if self.order_flow_timer >= self.order_flow_clear:
            self.order_flow_count = 0
            self.order_flow_timer = 0

    def write_log(self, msg: str):
        """"""
        log = LogData(msg=msg, gateway_name="RiskManager")
        event = Event(type=EVENT_LOG, data=log)
        self.event_engine.put(event)

    def check_risk(self, req: OrderRequest, gateway_name: str):
        """"""
        if not self.active:
            return True

        if not self.account:
            self.write_log("未获取到用户账户资金数据")
            return False

        # Check order volume
        if req.volume <= 0:
            self.write_log("委托数量必须大于0")
            return False

        if req.volume > self.order_size_limit:
            self.write_log(
                f"单笔委托数量{req.volume}，超过限制{self.order_size_limit}")
            return False

        # Check trade volume
        if self.trade_count >= self.trade_limit:
            self.write_log(
                f"今日总成交合约数量{self.trade_count}，超过限制{self.trade_limit}")
            return False

        # Check flow count
        if self.order_flow_count >= self.order_flow_limit:
            self.write_log(
                f"委托流数量{self.order_flow_count}，超过限制每{self.order_flow_clear}秒{self.order_flow_limit}次")
            return False

        # Check all active orders
        active_order_count = len(self.main_engine.get_all_active_orders())
        if active_order_count >= self.active_order_limit:
            self.write_log(
                f"当前活动委托次数{active_order_count}，超过限制{self.active_order_limit}")
            return False

        # Check order cancel counts
        if req.symbol in self.order_cancel_counts and self.order_cancel_counts[req.symbol] >= self.order_cancel_limit:
            self.write_log(
                f"当日{req.symbol}撤单次数{self.order_cancel_counts[req.symbol]}，超过限制{self.order_cancel_limit}")
            return False

        if req.offset == Offset.OPEN:
            # Add limits on the utilization of account funds
            self.account_funds_availability_rate = 100 - round(
                (self.account.available - abs(req.volume) * req.price) / self.account.balance, 2) * 100
            if self.account_funds_availability_rate_limit <= self.account_funds_availability_rate:
                self.write_log(
                    f"加上本次的开仓单金额,账户使用资金率为{self.account_funds_availability_rate}%,超过{self.account_funds_availability_rate_limit}%的限制,不允许开这么多仓")
                return False

            # Add single-type funds available rate control
            turnover = abs(req.volume) * abs(req.price)
            if self.position_dict:
                for key, value in self.position_dict.items():
                    req_vt_symbol = f"{req.symbol}.{req.exchange.value}"
                    if req_vt_symbol in value.keys():
                        turnover += abs(value[req_vt_symbol].price) * abs(value[req_vt_symbol].volume)
                # 计算单一品种已经使用资金的比率
                one_variety_money_usage_rate = round(turnover / self.account.balance * 100, 1)
                if self.one_variety_money_rate_limit <= one_variety_money_usage_rate:
                    self.write_log(f"加上本次的开仓单金额,单品种资金使用率为{one_variety_money_usage_rate}%,超过{self.one_variety_money_rate_limit}%的限制,不允许开这么多仓")
                    return False
            else:
                one_variety_money_usage_rate = round(turnover / self.account.balance * 100, 1)
                if self.one_variety_money_rate_limit <= one_variety_money_usage_rate:
                    self.write_log(f"加上本次的开仓单金额,单品种资金使用率为{one_variety_money_usage_rate}%,超过{self.one_variety_money_rate_limit}%的限制,不允许开这么多仓")
                    return False

        # Add flow count if pass all checks
        self.order_flow_count += 1
        return True
