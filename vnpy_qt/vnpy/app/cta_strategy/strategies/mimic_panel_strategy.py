from collections import defaultdict
from datetime import timedelta, datetime

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.app.cta_strategy.convert import Convert
from vnpy.controller.trade_operation import get_order_ref_value, save_strategy_order, strategy_update_trade, whether_open_today
from vnpy.model.strategy_ram_value import RamValue
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Interval
from vnpy.trader.database import database_manager
from vnpy.trader.utility import extract_vt_symbol

"""
自动中上部或中下部开仓平仓策略, 达到止盈平一半。持仓后可以再开仓

    做多止损点(point_loss_long)：
        1：昨日最低点 + 浮动点
        2：前日最低点 + 浮动点
        3：前日中点 + 浮动点
        4：前日开盘价 + 浮动点
        5：成交价 + 浮动点
        6：在前日最低价与昨日的中点之间取最大值
        其他:昨日蜡烛最高点 + 浮动点
        ps：如果 止损价 < 成交价 - 最新价 * 0.01 ， 则 止损价 =  成交价 - 最新价 * 0.01
    做空止损点(point_loss_short):
        1：昨日最高点 + 浮动点
        2：前日蜡烛最高点 + 浮动点
        3：前日蜡烛中点 + 浮动点
        4：前日蜡烛的开盘价 + 浮动点
        5：成交价 + 浮动点
        6：在昨日最高价与前日中点之间取最小值
        ps：如果 止损价 < 成交价 + 最新价 * 0.01 ， 则 止损价 =  成交价 + 最新价 * 0.01
        
    
    
    做多止盈点(point_win_long)：
        2: 初始止盈点：（成交价 - 止损价）* 倍数 + 成交价
            浮动止盈点： 参考point_win_long == 2
        3: 初始止盈点：（成交价 - 止损价）* 倍数 + 成交价
            浮动止盈点： 参考point_win_long == 3
        4: 初始止盈点：（成交价 - 止损价）* 倍数 + 成交价
            浮动止盈点： 参考point_win_long == 4
        其他:（成交价 - 止损价）* 倍数 + 成交价
        
    做空止盈点(point_win_short)：
        2: 初始止盈点：成交价 -（止损价 - 成交价）* 倍数
            浮动止盈点： 参考point_win_short == 2
        3: 初始止盈点：成交价 -（止损价 - 成交价）* 倍数
            浮动止盈点： 参考point_win_short == 3
        4: 初始止盈点：（成交价 -（止损价 - 成交价）* 倍数
            浮动止盈点： 参考point_win_short == 4
        其他: 成交价 -（止损价 - 成交价）* 倍数
"""


class MimicPanelStrategy(CtaTemplate):
    # region
    author = "jun"
    # 开仓手数
    fixed_size = 10
    # (1:做多,2:做空,3:多空都做)
    short_or_long = 3
    # 入场点 1是昨日高（低）点 2是前两日高（低）点
    point_enter = 2
    # 是否暂停开仓(1:暂停,0:不暂停)
    pause = 0
    # 分割线
    line = '此空无需填写'

    # 做多止损点
    point_loss_long = 1
    # 做多止盈点
    point_win_long = 2
    # 做多止损浮动点数(价格)
    num_float_loss_long = 0.0
    # 做多止盈倍数
    multiple_win_long = 1.5
    # 做多向下浮动(最高价与成交价的差百分比)
    percent_long = -0.1

    # 做多做空分割线
    line_long_short = '此空无需填写'
    # 做空止损点
    point_loss_short = 1
    # 做空止盈点
    point_win_short = 2
    # 做空止损浮动点数(价格)
    num_float_loss_short = 0.0
    # 做空止盈倍数
    multiple_win_short = 1.5
    # 做空向上浮动(最低价与成交价的差百分比)
    percent_short = 0.1

    parameters = ["fixed_size", "short_or_long", "point_enter", "pause", "line", "point_loss_long", "point_win_long", "num_float_loss_long", "multiple_win_long",
                  "percent_long", "line_long_short", "point_loss_short", "point_win_short",
                  "num_float_loss_short", "multiple_win_short", "percent_short"]

    parameters_chinese = {
        "fixed_size": "手数",
        "short_or_long": "做多填1，做空填2，多空都做填3",
        "point_enter": "入场点，突破昨日高(低)点填1，突破前两日高(低)点填2",
        "pause": "是否暂停开仓：暂停填1，默认为0(开仓)",
        "line": "-----------------------做多分界线-------------------------",
        "point_loss_long": "做多止损点",
        "point_win_long": "做多止盈点",
        "num_float_loss_long": "做多止损浮动价格",
        "multiple_win_long": "做多止盈倍数",
        "percent_long": "做多止盈向下浮动百分比",
        "line_long_short": "-----------------------做空分界线-------------------------",
        "point_loss_short": "做空止损点",
        "point_win_short": "做空止盈点",
        "num_float_loss_short": "做空止损浮动价格",
        "multiple_win_short": "做空止盈倍数",
        "percent_short": "做空止盈向上浮动百分比"
    }

    # endregion

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MimicPanelStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.bars = []  # 记录开仓日之前的bar数据
        # 记录当前之前的bar数据
        self.bars_history_current = []
        self.order_id_map = {}  # {order_ref:order_id}
        # 记录order_ref的映射
        self.order_ref_map = {}
        self.loss_price_long = 0.0  # 做多止损价
        self.win_price_long = 0.0   # 做多止盈价
        self.loss_price_short = 0.0  # 做空止损价
        self.win_price_short = 0.0  # 做空止盈价
        self.middle_before_yesterday = 0.0
        self.is_open_long = False  # 是否允许做多(通过历史价格决定的)
        self.is_open_short = False  # 是否允许空(通过历史价格决定的)
        self.is_open_today = False  # 判断今天是否已经开过仓
        self.trade_date_obj = None
        # 记录原止盈止损价格
        self.original_win_loss_record = defaultdict(list)

        self.open_long = False   # 是否允许做多(人为输入参数控制的)
        self.open_short = False  # 是否允许做空

        self.symbol, self.exchange = extract_vt_symbol(self.vt_symbol)
        self.exchange = Convert().convert_jqdata_exchange(exchange=self.exchange.value)
        # 判断是否已查过数据库中开仓信息
        self.already_search = False
        # 存储已开仓的未平仓数据
        self.order_data_list = []
        # 是否在开仓委托中
        self.commission = False
        # 是否在平仓委托中(存储正在委托的数据)
        self.commission_map = {}
        self.enter_price_long = 0   # 做多入场价
        self.enter_price_short = 0  # 做空入场价

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10, interval=Interval.DAILY, use_database=True)
        self.write_local_log(self.strategy_name, "策略初始化")

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.write_local_log(self.strategy_name, "策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")
        self.write_local_log(self.strategy_name, "策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)   # 更新tick为合成bar数据
        hour = tick.datetime.time().hour
        minute = tick.datetime.time().minute
        # 交易日停盘时间不交易
        temporary_bool = self.stop_trade_time(hour, minute, tick)
        if not temporary_bool:
            return

        if self.trading:
            if hasattr(self.account, 'accountid') and self.account.accountid:
                if not self.already_search:
                    self.query_position_data()  # 重新查询持仓数据
                    self.already_search = True
                    self.query_is_open_today()  # 重新查询下今天是否已经开过仓
                    self.write_local_log(self.strategy_name, f'查询出来的持仓数据长度：{len(self.order_data_list)}')

                    if self.short_or_long == 3:  # 多空都做(注意:如果曾经做过多(但不包括今天,除非策略重启),现在就不允许做多,空的情况也是一样。)
                        self.confirm_short_or_long()
            else:
                return
            self.position_building(tick)  # 建仓
            self.close_position(tick)  # 平仓

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.commission = False
        for com in list(self.commission_map):
            self.commission_map[com] = False

        # 初始化但未交易时
        if not self.trading_preparation():
            return

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        if order.offset.name == 'OPEN':
            if order.direction.name == "LONG":
                order.price = self.enter_price_long
            else:
                order.price = self.enter_price_short
        else:
            if self.original_win_loss_record.get(str(order.order_ref)):
                order.price = self.original_win_loss_record[str(order.order_ref)][2]

        save_strategy_order(order, self.strategy_name, self.__class__.__name__, self.account)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.offset.name != 'OPEN':
            trade.win_price = self.original_win_loss_record[str(trade.order_ref)][0]
            trade.loss_price = self.original_win_loss_record[str(trade.order_ref)][1]
        strategy_update_trade(trade, self.order_id_map, self.order_ref_map, self.strategy_name, self.__class__.__name__, self.account)

        self.query_position_data()  # 重新查询持仓数据
        self.pos = self.updata_pos(self.order_data_list)
        self.query_is_open_today()  # 重新查询下今天是否已经开过仓
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def query_position_data(self):
        """查询持仓数据"""
        self.order_data_list = TradeDataModel().select_order_data(self.strategy_name, self.__class__.__name__, self.symbol, self.account.accountid)

    def query_is_open_today(self):
        """查询今天是否已经开过仓"""
        self.is_open_today = whether_open_today(self.strategy_name, self.__class__.__name__, self.symbol, self.account.accountid)

    def trading_preparation(self):
        """
        交易准备工作:
            策略初始化完,未交易前处理的事情。
        """

        if not self.inited:  # 未交易前
            end_date = datetime.now()
            start_date = (end_date - timedelta(days=20))
            # 加载前10日的历史数据
            data_history_bars = self.load_history_bars(end_date=end_date, start_date=start_date)
            self.bars_history_current = []
            for data_bar in data_history_bars:
                self.bars_history_current.append(data_bar)
                if len(self.bars_history_current) <= 2:
                    continue
                else:
                    self.bars_history_current.pop(0)
            # 昨天k线图的中上部位置的价格
            self.middle_before_yesterday = (self.bars_history_current[-2].low_price + self.bars_history_current[-2].high_price) / 2

            if self.bars_history_current[-1].close_price >= self.middle_before_yesterday:
                self.is_open_long = True
                self.write_local_log(self.strategy_name, "今日达到做多开仓条件")
            elif self.bars_history_current[-1].close_price < self.middle_before_yesterday:
                self.is_open_short = True
                self.write_local_log(self.strategy_name, "今日达到做空开仓条件")

            self.entry_price()  # 做多做空入场价确定
            self.judge_short_or_long()  # 判断做多还是做空
            return False
        else:
            return True

    def judge_short_or_long(self):
        """判断允许做多还是做空还是多空多做"""
        if self.short_or_long == 1:
            self.open_long = True
        elif self.short_or_long == 2:
            self.open_short = True
        else:
            self.open_long = True
            self.open_short = True

    def entry_price(self):
        """做多做空入仓价确定"""
        if self.point_enter == 1:
            self.enter_price_long = self.bars_history_current[-1].high_price
            self.enter_price_short = self.bars_history_current[-1].low_price
        else:
            self.enter_price_long = max(self.bars_history_current[-1].high_price, self.bars_history_current[-2].high_price)
            self.enter_price_short = min(self.bars_history_current[-1].low_price, self.bars_history_current[-2].low_price)

    def load_history_bars(self, start_date, end_date):
        data_history_bars = database_manager.load_bar_data(
            symbol=self.symbol,
            exchange=self.exchange,
            interval=Interval.DAILY,
            start=start_date,
            end=end_date)
        return data_history_bars

    def confirm_short_or_long(self):
        """
        如果曾经做过多/空,则现在不允许做多/空。
        """
        open_data = TradeDataModel().select().where(
            (TradeDataModel.symbol == self.symbol)
            & (TradeDataModel.account_id == self.account.accountid)
            & (TradeDataModel.offset == 'OPEN')
            & (TradeDataModel.strategy_name == self.strategy_name)
            & (TradeDataModel.strategy_class_name == self.__class__.__name__)
            & (TradeDataModel.gateway_name == 'CTP')
        )
        for data in open_data:
            if data.direction == 'SHORT':
                self.write_local_log(self.strategy_name, f'只能做多')
                self.open_long = True
                self.open_short = False
                break
            else:
                self.write_local_log(self.strategy_name, f'只能做空')
                self.open_short = True
                self.open_long = False
                break

    def position_building(self, tick):
        """
        建仓:建多/空仓
        """
        # self.is_open_today = False
        # self.open_long = True
        if not self.is_open_today and not self.commission and not self.pause and not self.strategy_value["risk_ctrl_cond"]:
            # print("tick.last_price：", tick.last_price, "self.enter_price_long:", self.enter_price_long, "self.open_long:", self.open_long, "self.is_open_long:", self.is_open_long)
            if tick.last_price >= self.enter_price_long and self.open_long and self.is_open_long:  # 做多
                if self.point_loss_long == 1:  # 做多止损点为1时才加入风险控制,其他不加风险控制。
                    self.loss_price_long = self.bars_history_current[-1].low_price + self.num_float_loss_long  # 做多止损价计算
                    if self.loss_price_long > tick.last_price - tick.last_price * 0.01:
                        self.loss_price_long = tick.last_price - tick.last_price * 0.01
                    engine = self.cta_engine.main_engine
                    fixed_size = self.risk_control(self.vt_symbol, engine, tick.last_price, self.loss_price_long)  # 开仓手数
                else:
                    fixed_size = self.fixed_size
                if not fixed_size:
                    self.strategy_value["risk_ctrl_cond"] = 1
                    RamValue().update_data(self.strategy_name, self.strategy_value)
                    self.write_log('因风险控制无法开仓')
                else:
                    self.buy(tick.limit_up, fixed_size)  # 开多仓
                    self.commission = True
                    self.write_local_log(self.strategy_name, "以前两日的最高价%s委托开多仓" % self.enter_price_long)

            elif tick.last_price <= self.enter_price_short and self.open_short and self.is_open_short:  # 做空
                if self.point_loss_short == 1:  # 做空止损点为1时才加入风险控制,其他不加风险控制。
                    self.loss_price_short = self.bars_history_current[-1].high_price + self.num_float_loss_short
                    if self.loss_price_short < tick.last_price + tick.last_price * 0.01:
                        self.loss_price_short = tick.last_price + tick.last_price * 0.01
                    engine = self.cta_engine.main_engine
                    fixed_size = self.risk_control(self.vt_symbol, engine, tick.last_price, self.loss_price_short)
                else:
                    fixed_size = self.fixed_size
                if not fixed_size:
                    self.strategy_value["risk_ctrl_cond"] = 1
                    RamValue().update_data(self.strategy_name, self.strategy_value)
                    self.write_log('因风险控制无法开仓')
                else:
                    self.short(tick.limit_down, fixed_size)  # 开空仓
                    self.commission = True
                    self.write_local_log(self.strategy_name, "以前两日的最低价%s委托开空仓" % self.enter_price_short)

    def close_position(self, tick):
        """
        平仓：
            平多/空仓
        """
        for order_data in self.order_data_list:
            if self.commission_map.get(str(order_data.order_ref)):  # 查询是否在平仓委托中
                continue
            self.init_win_loss_price(tick, order_data)  # 初始化设置止盈止损价
            self.run_close_position(tick, order_data)  # 执行平仓

    def run_close_position(self, tick, order_data):
        """
        平仓的真正处理函数
        """
        if order_data.direction == 'LONG':
            if self.point_win_long == 2:
                """
                浮动止盈和平半仓(条件: 最新价 > 止盈价)
                    1.先平一半仓位
                    2.止损点设为昨日低点
                    3.止盈点为此时最高价
                """
                if tick.last_price >= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.sell(tick.limit_down, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")

                    self.loss_price_long = self.bars_history_current[-1].low_price
                    self.win_price_long = tick.high_price
                    self.way_station(order_data, self.win_price_long, self.loss_price_long)

                elif tick.last_price <= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.sell(tick.limit_down, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            elif self.point_win_long == 3:
                """
                浮动止盈和平半仓(条件: 最新价 > 止盈价）
                    1.平半仓
                    2.止损点为昨日中点
                    3.止盈点为此时最高价
                """
                if tick.last_price >= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.sell(tick.limit_down, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                    self.loss_price_long = (self.bars_history_current[-1].open_price + self.bars_history_current[-1].close_price) / 2
                    self.win_price_long = tick.high_price
                    self.way_station(order_data, self.win_price_long, self.loss_price_long)

                elif tick.last_price <= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.sell(tick.limit_down, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            elif self.point_win_long == 4:
                """
                浮动止盈和平半仓(条件: 最新价 > 止盈价）
                    1.平半仓
                    2.止损点为(最高价 - 成交价）* 百分比 + 最新价
                    3.止盈点为此时最高价
                """
                if tick.last_price >= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.sell(tick.limit_down, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                    self.loss_price_long = (tick.high_price - order_data.price) * self.percent_long + tick.last_price
                    self.win_price_long = tick.high_price
                    self.way_station(order_data, self.win_price_long, self.loss_price_long)

                elif tick.last_price <= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.sell(tick.limit_down, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            else:
                if tick.last_price >= order_data.win_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                    self.sell(tick.limit_down, abs(int(order_data.volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")

                elif tick.last_price <= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.sell(tick.limit_down, abs(int(order_data.volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

        elif order_data.direction == 'SHORT':
            if self.point_win_short == 2:
                """
                浮动止盈和平半仓(条件: 最新价 < 止盈价）
                    1.平半仓
                    2.止损点为昨日高点
                    3.止盈点为此时最低价         
                """
                if tick.last_price <= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.cover(tick.limit_up, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                    self.loss_price_short = self.bars_history_current[-1].high_price
                    self.win_price_short = tick.low_price
                    self.way_station(order_data, self.win_price_short, self.loss_price_short)

                elif tick.last_price >= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.cover(tick.limit_up, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            elif self.point_win_short == 3:
                """
                浮动止盈和平半仓(条件: 最新价 < 止盈价）
                    1.平半仓
                    2.止损点为昨日中点
                    3.止盈点为此时最低价             
                """
                if tick.last_price <= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.cover(tick.limit_up, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                    self.loss_price_short = (self.bars_history_current[-1].open_price + self.bars_history_current[-1].close_price) / 2
                    self.win_price_short = tick.low_price
                    self.way_station(order_data, self.win_price_short, self.loss_price_short)

                elif tick.last_price >= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.cover(tick.limit_up, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            elif self.point_win_short == 4:
                """
                浮动止盈和平半仓(条件: 最新价 < 止盈价）
                    1.平半仓
                    2.止损点为(成交价 - 最低价）* 百分比 + 最新价
                    3.止盈点为此时最低价             
                """
                if tick.last_price <= order_data.win_price:
                    if order_data.volume == order_data.un_volume:
                        order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                        self.cover(tick.limit_up, int(order_data.volume / 2), order_ref=order_ref)
                        self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                    self.loss_price_short = (order_data.price - tick.low_price) * self.percent_short + tick.last_price
                    self.win_price_short = tick.low_price
                    self.way_station(order_data, self.win_price_short, self.loss_price_short)

                elif tick.last_price >= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.cover(tick.limit_up, abs(int(order_data.un_volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

            else:
                if tick.last_price <= order_data.win_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=True)  # 设置止盈止损价到字典中
                    self.cover(tick.limit_up, abs(int(order_data.volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止盈价{order_data.win_price}委托平仓，orderid:{order_data.orderid}")
                elif tick.last_price >= order_data.loss_price:
                    order_ref = self.set_win_loss_price(order_data, win_flag=False)  # 设置止盈止损价到字典中
                    self.cover(tick.limit_up, abs(int(order_data.volume)), order_ref=order_ref)
                    self.write_local_log(self.strategy_name, f"以止损价{order_data.loss_price}委托平仓，orderid:{order_data.orderid}")

    def init_win_loss_price(self, tick, order_data):
        """初始化设置做多(空)止盈止损价"""
        if not order_data.win_price:  # 没有止盈价时(刚开的仓是没有止盈止损价的)
            end = order_data.trade_date + timedelta(hours=5) - timedelta(days=1)
            start = end - timedelta(days=20)
            # 开仓日的前3日的历史数据
            data_bars = self.load_history_bars(end_date=end, start_date=start)
            self.bars = []
            for data_bar in data_bars:
                self.bars.append(data_bar)
                if len(self.bars) <= 2:
                    continue
                else:
                    self.bars.pop(0)

            middle = (self.bars[-2].open_price + self.bars[-2].close_price) / 2

            if order_data.direction == 'LONG':
                if self.point_loss_long == 2:
                    self.loss_price_long = self.bars[-2].low_price + self.num_float_loss_long
                elif self.point_loss_long == 3:
                    self.loss_price_long = middle + self.num_float_loss_long
                elif self.point_loss_long == 4:
                    self.loss_price_long = self.bars[-2].open_price + self.num_float_loss_long
                elif self.point_loss_long == 5:
                    self.loss_price_long = order_data.price + self.num_float_loss_long
                elif self.point_loss_long == 6:
                    self.loss_price_long = max(self.bars[-1].low_price, middle)
                else:
                    self.loss_price_long = self.bars[-1].low_price + self.num_float_loss_long

                if self.loss_price_long > order_data.price - tick.last_price * 0.01:
                    self.loss_price_long = order_data.price - tick.last_price * 0.01

                # 止盈价：（成交价 - 止损价）* 倍数 + 成交价
                self.win_price_long = (order_data.price - self.loss_price_long) * self.multiple_win_long + order_data.price

                TradeDataModel().update_loss_win_price(order_data, self.loss_price_long, self.win_price_long)  # 在数据库中更新止盈止损价
                self.query_position_data()  # 重新查询持仓数据

                order_data.win_price = self.win_price_long
                order_data.loss_price = self.loss_price_long
                self.write_local_log(self.strategy_name, f"做多-止盈止损价初始设置，止盈为：{self.win_price_long}, 止损为：{self.loss_price_long}")

            elif order_data.direction == 'SHORT':
                if self.point_loss_short == 2:
                    self.loss_price_short = self.bars[-2].high_price + self.num_float_loss_short  # 前日蜡烛最高点 + 浮动点
                elif self.point_loss_short == 3:
                    self.loss_price_short = middle + self.num_float_loss_short    # 前日蜡烛中点 + 浮动点
                elif self.point_loss_short == 4:
                    self.loss_price_short = self.bars[-2].open_price + self.num_float_loss_short  # 前日蜡烛的开盘价 + 浮动点
                elif self.point_loss_short == 5:
                    self.loss_price_short = order_data.price + self.num_float_loss_short  # 成交价 + 浮动点
                elif self.point_loss_short == 6:
                    self.loss_price_short = min(self.bars[-1].high_price, middle)  # 昨日蜡烛的最高价与前日蜡烛的中点之中的最低点
                else:
                    self.loss_price_short = self.bars[-1].high_price + self.num_float_loss_short  # 昨日蜡烛最高点 + 浮动点

                if self.loss_price_short < order_data.price + tick.last_price * 0.01:
                    self.loss_price_short = order_data.price + tick.last_price * 0.01

                # 止盈价：成交价 -（止损价 - 成交价）*倍数
                self.win_price_short = order_data.price - (self.loss_price_short - order_data.price) * self.multiple_win_short

                TradeDataModel().update_loss_win_price(order_data, self.loss_price_short, self.win_price_short)
                self.query_position_data()  # 重新查询持仓数据

                order_data.win_price = self.win_price_short
                order_data.loss_price = self.loss_price_short
                self.write_local_log(self.strategy_name, f"做空-止盈止损价初始设置，止盈为：{self.win_price_short}, 止损为：{self.loss_price_short}")

    def set_win_loss_price(self, order_data, win_flag=True):
        """设置止盈止损价到字典对象中"""
        order_ref = get_order_ref_value()
        self.order_id_map[str(order_ref)] = order_data.orderid
        self.order_ref_map[str(order_ref)] = order_data.order_ref
        self.original_win_loss_record[str(order_ref)].append(order_data.win_price)
        self.original_win_loss_record[str(order_ref)].append(order_data.loss_price)
        if win_flag:
            self.original_win_loss_record[str(order_ref)].append(order_data.win_price)
        else:
            self.original_win_loss_record[str(order_ref)].append(order_data.loss_price)
        self.commission_map[str(order_data.order_ref)] = True
        return order_ref

    def way_station(self, order_data, win_price, loss_price):
        """
        中间站:写日志、更新止盈止损价、重新查询持仓数据
        """
        self.write_local_log(self.strategy_name, "更新止盈止损价格，原止盈价：%s, 新止盈价：%s, 原止损价：%s, 新止损价：%s,orderid:%s"
                             % (order_data.win_price, win_price, order_data.loss_price, loss_price, order_data.orderid))

        TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
        self.query_position_data()  # 重新查询持仓数据


