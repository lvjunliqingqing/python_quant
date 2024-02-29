from copy import deepcopy
from vnpy.trader.constant import Direction

from vnpy.app.cta_strategy import (
    CtaTemplate,  # Cta模板
    StopOrder,  # 订单停止信息
    TickData,  # tick数据
    BarData,  # bar数据
    TradeData,  # 交易数据
    OrderData,  # 订单数据
    BarGenerator,  # bar生成器
)
from vnpy.trader.utility import ArrayManager

"""
持仓仍开仓
    1.做多：
        (1).第二根蜡烛的收盘价在第一根蜡烛的的中上部【(最高+最低)除以2】入场:
        2.做多买入价：前两日的最高价
    2.做空
        (1).第二根蜡烛的收盘价在第一根蜡烛的的中下部【(最高+最低)除以2】可入场:
        (2).做空买价:前两日的最低价

止损点：
    1：前一日蜡烛最低价或最高价
    ps：止损点至少比成交价低30
    当盈利达到x倍时，把止损开仓当日的最低价。

止盈点：
    1:（成交价 - 止损价）* 固定止盈倍数 + 成交价
    2:固定止盈倍数为1.5。
"""


class ReachConditionLossSetOpenDateLowStrategy(CtaTemplate):
    author = "jun"
    fixed_size = 1
    multiple_win_long = 1.5
    multiple_win_short = 1.5
    long_or_short_net = 'long'
    n_day = 5
    # 盈利倍数
    margin_of_profitableness = 0.78
    x_loss_point = 1.5
    # 参数
    parameters = ["fixed_size", "multiple_win_long", "multiple_win_short", "long_or_short_net", "n_day", "margin_of_profitableness", "x_loss_point"]

    # 变量
    long_dict = {}
    short_dict = {}
    variables = ["long_dict", "short_dict"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(ReachConditionLossSetOpenDateLowStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        # 将on_bar传进bar生成器中，
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.history_data = None
        self.list1 = []
        self.dist = {}
        self.rise1 = 0
        self.rise2 = 0
        self.bars = [BarData]
        self.dict_l = {}
        self.long_dict = {}
        self.short_dict = {}
        self.storage = {}
        self.data = []
        self.size = 0
        self.is_write_csv = True
        self.storage1 = []
        self.ying_yang = ""
        self.n_advantage_list = []
        self.today_to_bar = {}

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        # 加载前n天历史bar，进行初始化。
        self.load_bar(self.n_day)
        if not self.history_data:
            return
        for data in self.history_data:
            self.today_to_bar["%s" % "".join(str(data.datetime.date()).split("-"))] = data
            self.list1.append(data.datetime.date())
            if len(self.list1) <= 2:
                continue
            else:
                self.list1.pop(0)
            self.dist["%s" % self.list1[-2]] = data
        self.last_bar = self.history_data[-1]
        self.penultimate_day_date = self.list1[-2]
        self.list1.clear()

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.bars.append(bar)
        if len(self.bars) <= 2:
            return
        else:
            self.bars.pop(0)

        if not self.inited:
            return

        # 最后一天不交易
        if self.last_bar.datetime.date() == bar.datetime.date():

            return
        # 倒数第二天全平仓
        if self.penultimate_day_date == bar.datetime.date():
            for long in list(self.long_dict):
                self.sell(self.last_bar.open_price, self.long_dict[long]['pos'], stop=True)
                # print(long, self.today_to_bar[f"{long}"])
                if self.is_write_csv:
                    self.storage[long] = deepcopy(self.long_dict[long])
                    self.storage1.append(self.storage[long])
                self.long_dict.pop(long)
            for short in list(self.short_dict):
                self.cover(self.last_bar.open_price, self.short_dict[short]['pos'], stop=True)

                if self.is_write_csv:
                    self.storage[short] = deepcopy(self.short_dict[short])
                    self.storage1.append(self.storage[short])
                self.short_dict.pop(short)
            return

        middle = (self.bars[0].low_price + self.bars[0].high_price) / 2

        # 开仓
        if self.trading:
            if bar.close_price >= middle and (self.long_or_short_net == 'long' or self.long_or_short_net == 'net'):
                if bar.close_price > bar.open_price:
                    self.ying_yang = "阳线"
                if bar.close_price < bar.open_price:
                    self.ying_yang = "阴线"
                enter_price = max(self.bars[1].high_price, self.bars[0].high_price)
                self.buy(enter_price, self.fixed_size, stop=True)

            elif bar.close_price <= middle and (self.long_or_short_net == 'short' or self.long_or_short_net == 'net'):
                if bar.close_price > bar.open_price:
                    self.ying_yang = "阳线"
                if bar.close_price < bar.open_price:
                    self.ying_yang = "阴线"
                enter_price = min(self.bars[1].low_price, self.bars[0].low_price)
                self.short(enter_price, self.fixed_size, stop=True)

        # 平仓
        if self.long_or_short_net == 'long' or self.long_or_short_net == 'net':
            for long in list(self.long_dict):
                if (self.long_dict[long]["price_open"] - self.long_dict[long]["loss_price"]):
                    if round((bar.high_price - self.long_dict[long]["price_open"]) / (self.long_dict[long]["price_open"] - self.long_dict[long]["loss_price"]), 2) >= self.margin_of_profitableness:
                        if not self.long_dict[long]["is_change"]:
                            self.long_dict[long]["is_change"] = True
                            self.long_dict[long]["loss_price"] = self.today_to_bar[f"{long}"].low_price
                            self.long_dict[long]["change_date"] = bar.datetime

                if self.long_dict[long]["win_price"] < self.dist["%s" % bar.datetime.date()].high_price and self.long_dict[long]["loss_price"] > self.dist["%s" % bar.datetime.date()].low_price:
                    if self.dist["%s" % bar.datetime.date()].close_price > self.dist["%s" % bar.datetime.date()].open_price:
                        self.sell(self.long_dict[long]["loss_price"], self.long_dict[long]["pos"], stop=True)
                        if self.is_write_csv:
                            self.storage[long] = deepcopy(self.long_dict[long])
                            self.storage1.append(self.storage[long])
                        self.long_dict.pop(long)
                    else:
                        self.sell(self.long_dict[long]["win_price"], self.long_dict[long]["pos"])
                        if self.is_write_csv:
                            self.storage[long] = deepcopy(self.long_dict[long])
                            self.storage1.append(self.storage[long])
                        self.long_dict.pop(long)

                elif self.long_dict[long]["win_price"] < self.dist["%s" % bar.datetime.date()].high_price:
                    self.sell(self.long_dict[long]["win_price"], self.long_dict[long]["pos"])

                    if self.is_write_csv:
                        self.storage[long] = deepcopy(self.long_dict[long])
                        self.storage1.append(self.storage[long])
                    self.long_dict.pop(long)

                elif self.long_dict[long]["loss_price"] > self.dist["%s" % bar.datetime.date()].low_price:
                    self.sell(self.long_dict[long]["loss_price"], self.long_dict[long]["pos"], stop=True)

                    if self.is_write_csv:
                        self.storage[long] = deepcopy(self.long_dict[long])
                        self.storage1.append(self.storage[long])
                    self.long_dict.pop(long)

        if self.long_or_short_net == 'short' or self.long_or_short_net == 'net':
            for short in list(self.short_dict):
                if (self.long_dict[long]["price_open"] - self.long_dict[long]["loss_price"]):
                    if round((self.long_dict[long]["price_open"] - bar.low_price) / (self.long_dict[long]["price_open"] - self.long_dict[long]["loss_price"]), 2) >= self.margin_of_profitableness:
                        if not self.short_dict[short]["is_change"]:
                            self.short_dict[short]["is_change"] = True
                            self.short_dict[short]["loss_price"] = self.short_dict[short]["price_open"]
                            self.short_dict[short]["change_date"] = bar.datetime

                if self.short_dict[short]["loss_price"] < self.dist["%s" % bar.datetime.date()].high_price:
                    self.cover(self.short_dict[short]["loss_price"], self.short_dict[short]['pos'], stop=True)

                    if self.is_write_csv:
                        self.storage[short] = deepcopy(self.short_dict[short])
                        self.storage1.append(self.storage[short])
                    self.short_dict.pop(short)
                elif self.short_dict[short]["win_price"] > self.dist["%s" % bar.datetime.date()].low_price:
                    self.cover(self.short_dict[short]["win_price"], self.short_dict[short]['pos'])

                    if self.is_write_csv:
                        self.storage[short] = deepcopy(self.short_dict[short])
                        self.storage1.append(self.storage[short])
                    self.short_dict.pop(short)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.offset.name == "OPEN":
            if trade.direction.name == "LONG":
                loss_price = self.bars[-1].low_price
                # if loss_price > trade.price - 30:
                #     loss_price = trade.price - 30

                if (trade.price - loss_price) / trade.price * 100 < self.x_loss_point:
                    loss_price = trade.price * (1 - self.x_loss_point / 100)
                    # print(trade.datetime.date())
                win_price = (trade.price - loss_price) * self.multiple_win_long + trade.price
                self.dict_l["direction"] = Direction.LONG
                self.dict_l["win_price"] = win_price
                self.dict_l["loss_price"] = loss_price
                self.dict_l["no_change_loss_price"] = loss_price
                self.dict_l["price_open"] = trade.price
                self.dict_l['pos'] = trade.volume
                self.dict_l['阴阳线'] = self.ying_yang
                self.dict_l["multiple_win_long"] = self.multiple_win_long
                self.dict_l["change_date"] = None
                self.dict_l["is_today"] = True
                self.dict_l["is_change"] = False
                self.dict_l["date_open"] = trade.datetime
                self.long_dict["%s" % "".join(str(trade.datetime.date()).split("-"))] = deepcopy(self.dict_l)

            else:
                loss_price = self.bars[-1].high_price
                # if loss_price < trade.price + 30:
                #     loss_price = trade.price + 30
                if (trade.price - loss_price) / trade.price * 100 < self.x_loss_point:
                    loss_price = trade.price * (1 + self.x_loss_point / 100)
                win_price = trade.price - (loss_price - trade.price) * self.multiple_win_short
                self.dict_l["direction"] = Direction.SHORT
                self.dict_l["win_price"] = win_price
                self.dict_l["loss_price"] = loss_price
                self.dict_l["no_change_loss_price"] = loss_price
                self.dict_l["price_open"] = trade.price
                self.dict_l['pos'] = trade.volume
                self.dict_l['阴阳线'] = self.ying_yang
                self.dict_l["multiple_win_short"] = self.multiple_win_short
                self.dict_l["change_date"] = None
                self.dict_l["is_today"] = True
                self.dict_l["is_change"] = False
                self.dict_l["date_open"] = trade.datetime
                self.short_dict["%s" % "".join(str(trade.datetime.date()).split("-"))] = deepcopy(self.dict_l)

        else:
            if self.is_write_csv:
                if trade.direction.name == "SHORT":
                    self.storage1[0]["price_sell"] = trade.price
                    self.storage1[0]["date_sell"] = trade.datetime
                    price_profits = trade.price - self.storage1[0]["price_open"]
                    self.storage1[0]["price_profits"] = price_profits * self.size * trade.volume
                    if price_profits >= 0:
                        win_loss = 1
                    else:
                        win_loss = 0
                    self.storage1[0]["win_loss"] = win_loss
                    self.storage1[0]["parameters"] = self.long_or_short_net + "_" + self.vt_symbol
                    self.storage1[0].pop("is_today")
                    self.data.append(self.storage1[0])
                    self.storage1.pop(0)
                else:
                    self.storage1[0]["price_sell"] = trade.price
                    self.storage1[0]["date_sell"] = trade.datetime
                    price_profits = self.storage1[0]["price_open"] - trade.price
                    self.storage1[0]["price_profits"] = price_profits * self.size * trade.volume
                    if price_profits >= 0:
                        win_loss = 1
                    else:
                        win_loss = 0
                    self.storage1[0]["win_loss"] = win_loss
                    self.storage1[0]["parameters"] = self.long_or_short_net + "_" + self.vt_symbol
                    self.storage1[0].pop("is_today")
                    self.data.append(self.storage1[0])
                    self.storage1.pop(0)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass



