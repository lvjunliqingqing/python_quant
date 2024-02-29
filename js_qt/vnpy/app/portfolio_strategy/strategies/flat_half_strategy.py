
import json
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List, Dict
from vnpy.app.cta_strategy.convert import Convert
from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.controller.constant import INIT_DAY
from vnpy.controller.risk_ctrl import global_value_minus_the
from vnpy.controller.trade_operation import get_order_ref_value, write_local_log, whether_open_today, strategy_update_trade, save_strategy_order, \
    current_trade_date, trade_time_judge
from vnpy.model.open_symbol_data_model import OpenSymbolModel
from vnpy.model.strategy_portfolio_ram_value import PortfolioRamValue
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Interval, Status
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData, BarData, TradeData, OrderData
from vnpy.trader.utility import extract_vt_symbol


class FlatHalfStrategy(StrategyTemplate):
    """"""
    author = "lv jun"

    multiple_win_long = 1.5
    multiple_win_short = 1.5
    point_enter = 2
    lowest_loss_price_percent = 0.01  # 做多做空止损价的因子数
    multiple_change_loss_price = 0.78
    max_open_loss_rate = 0.04  # 单品种1.5倍的开仓最大损失率

    parameters = [
        "max_open_loss_rate",
        "multiple_change_loss_price",
        "multiple_win_long",
        "multiple_win_short",
        "point_enter",
        "lowest_loss_price_percent"
    ]
    parameters_chinese = {
        "max_open_loss_rate": "1.5倍的开仓最大损失率",
        "multiple_change_loss_price": "更改止损价的止损区间倍数",
        "multiple_win_long": "做多止盈倍数",
        "multiple_win_short": "做空止盈倍数",
        "point_enter": "入场点，突破昨日高(低)点填1，突破前两日高(低)点填2",
        "lowest_loss_price_percent": "做多做空止损价的因子数"
    }

    is_change_loss_price_map = {}  # 记录止损价是否变化过的字典 {orderid:bool值}
    repeatedly_change_loss_price_map = {}  # 会变化的止损价记录字典  {orderid:change_loss_price}

    variables = [
        "is_change_loss_price_map",
        "repeatedly_change_loss_price_map"
    ]

    def __init__(
            self,
            strategy_engine: StrategyEngine,
            strategy_name: str,
            vt_symbols: List[str],
            setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)

        self.last_tick_time: datetime = None  # 记录上个tick的datetime
        self.fixed_size = 1   # 委托手数
        self.direction_symbol = {}  # 允许开仓的方向 {symbol:direction} 键和值均来自允许开仓的数据集
        self.open_vt_symbols = []  # 存储允许开仓的vt_symbol
        self.is_open_today = {}  # 今天是否已经开过仓{symbol:bool值}
        self.bars_history_current_all = {}  # {symbol:[bar,bar]}  保存最近2天的bar数据
        self.enter_price_long_all = {}  # {symbol:做多入场价}
        self.enter_price_short_all = {}  # {symbol:做空入场价}
        self.is_open_long_all = {}  # {symbol:bool值,symbol:bool值} 是否做多
        self.is_open_short_all = {}  # {symbol:bool值,symbol:bool值} 是否做空
        self.open_interest_data_dict = defaultdict(list)  # 持仓数据字典 {未平仓的symbol:未平仓的data}
        self.order_id_map = defaultdict()  # {order_ref:orderid}
        self.order_ref_map = defaultdict()  # {order_ref:order_data.order_ref}
        self.original_win_loss_close_map = defaultdict(list)  # 原止盈止损价记录字典 {order_ref:[win_price,loss_price,close_price]}
        self.portfolioramvalue = PortfolioRamValue()
        self.parameters_map = {}    # 策略参数字典 {symbol:strategy_args} 键和值均来自允许开仓的数据集,如果数据库中没有、就获取用户输入的策略参数。
        self.open_date_bar_map = {}  # {orderid:持仓的开仓时的当日的日bar数据对象}
        self.active_order_open_map = {}  # 开仓委托的字典 {symbol:True}
        self.active_order_close_map = {}  # 平仓委托的字典 {order_ref:True}
        self.close_order_successful_map = {}  # 平仓委托单全部成交字典 {order_ref:True}
        self.query_open_interest_data = None  # 未平仓成交单数据

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        account_id = self.strategy_engine.main_engine.get_gateway('CTP').td_api.userid
        
        if not account_id:
            self.write_log('策略未成功初始化，请重启连接账户之后再初始化')
            return

        # 查询未平仓数据
        self.query_open_interest_data = TradeDataModel().query_open_positions_data(self.strategy_name, self.__class__.__name__, account_id)
        self.vt_symbols = []  # 存储允许交易的品种(开仓+平仓)
        for interest_data in self.query_open_interest_data:
            self.vt_symbols.append(f"{interest_data.symbol}.{interest_data.exchange}")
            self.open_interest_data_dict[interest_data.symbol].append(interest_data)

        # 查询允许开仓的合约数据
        query_open_data = OpenSymbolModel().query_open_data(account_id, self.__class__.__name__)
        for open_data in query_open_data:
            vt_symbol = f"{open_data.symbol}.{open_data.exchange}"
            if vt_symbol in self.open_vt_symbols:
                self.write_log(f'存在重复开仓品种:{vt_symbol}')
            self.open_vt_symbols.append(vt_symbol)
            self.direction_symbol[open_data.symbol] = open_data.direction
            self.parameters_map[open_data.symbol] = json.loads(open_data.strategy_args)  # json数据解析成字典才好遍历
            self.is_open_today[open_data.symbol] = whether_open_today(self.strategy_name, self.__class__.__name__, open_data.symbol, account_id)

            # 获取策略参数
            strategy_parameters = self.get_parameters()  # 获取策略参数
            for key, value in self.parameters_map[open_data.symbol].items():
                if len(str(value["value"])):
                    self.parameters_map[open_data.symbol][key]["value"] = float(value["value"])
                else:
                    self.parameters_map[open_data.symbol][key]["value"] = strategy_parameters[key]
                    self.write_log(f'参数为空：{key, strategy_parameters[key]}')

        # 获得允许交易的品种
        self.vt_symbols.extend(self.open_vt_symbols)
        self.vt_symbols = list(set(self.vt_symbols))

        self.trade_before()  # 交易前的准备工作
        self.write_log(f'允许开仓的品种:{list(set(self.open_vt_symbols))}')
        # load_bars不仅仅只加载数据,没加载一个bar数据就会调用一次策略中的on_bars(),这行代码起到策略初始化的作用
        self.load_bars(15, interval=Interval.DAILY, use_database=True)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        print(self.risk_ctrl_cond)
        # 防止策略变量没有及时更新(策略变量发生改变时,需要隔一段时间才会把变化的数据写入json文件中),通过查询数据库来进行同步更新策略变量。
        is_change_map = {}
        change_loss_map = {}
        for order_data in self.query_open_interest_data:
            if self.is_change_loss_price_map.get(order_data.orderid):
                is_change_map[order_data.orderid] = True

            if self.repeatedly_change_loss_price_map.get(order_data.orderid):
                change_loss_map[order_data.orderid] = self.repeatedly_change_loss_price_map[order_data.orderid]

        self.is_change_loss_price_map = deepcopy(is_change_map)
        self.repeatedly_change_loss_price_map = deepcopy(change_loss_map)

        write_local_log(self.strategy_name, f"is_change_loss_price_map:{self.is_change_loss_price_map}")
        write_local_log(self.strategy_name, f"repeatedly_change_loss_price_map:{self.repeatedly_change_loss_price_map}")
        del is_change_map, change_loss_map
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        if not self.account:
            return
        is_trade = trade_time_judge(tick, self)  # 判断是否在交易时间段
        if not is_trade:
            return
        # 撤销所有订单(一分钟执行一次)
        if self.last_tick_time and self.last_tick_time.minute != tick.datetime.minute:
            self.cancel_all()
        self.last_tick_time = tick.datetime  # 记录上一tick的时间
        if self.trading:
            self.position_building(tick)  # 建仓
            self.close_position(tick)  # 平仓

    def on_bar(self, bar: BarData):
        """"""
        pass

    def on_bars(self, bars: Dict[str, BarData]):
        """"""
        if not self.inited:
            pass
        self.put_event()

    def on_order(self, order: OrderData):
        if order.offset.name == 'OPEN':
            # 订单取消,开仓委托字典中删除委托数据
            if order.status == Status.CANCELLED or order.status == Status.REJECTED:
                self.active_order_open_map.pop(order.symbol)
                if order.order_ref:
                    cancel_pos = abs(order.volume - order.traded)  # 撤销的手数或拒单手数
                    global_value_minus_the(str(order.order_ref), cancel_pos)  # 当开仓单被撤销后就需要减去这次的开仓保证金、开仓手数等等。

            if order.direction.name == "LONG":
                order.price = self.enter_price_long_all[order.symbol]
            else:
                order.price = self.enter_price_short_all[order.symbol]
        else:
            if order.status == Status.CANCELLED or order.status == Status.REJECTED:
                self.active_order_close_map.pop(self.order_ref_map[order.order_ref])
            elif order.status == Status.ALLTRADED:
                self.close_order_successful_map[order.order_ref] = True

            if self.original_win_loss_close_map.get(str(order.order_ref)):
                order.price = self.original_win_loss_close_map[str(order.order_ref)][2]
            else:
                self.write_log(f'{order.symbol}记录原止盈止损收盘委托价字典出现错误{self.original_win_loss_close_map}')

        save_strategy_order(order, self.strategy_name, self.__class__.__name__, self.account)  # 保存委托单

    def on_trade(self, trade: TradeData):
        if trade.offset.name == 'OPEN':
            if trade.direction.name == 'LONG':
                trade.win_price, trade.loss_price, change_loss_price = self.get_win_loss_price_long(trade.symbol, trade.price)
            else:
                trade.win_price, trade.loss_price, change_loss_price = self.get_win_loss_price_short(trade.symbol, trade.price)
            self.is_open_today[trade.symbol] = True
            self.repeatedly_change_loss_price_map[trade.orderid] = change_loss_price
        else:
            if self.close_order_successful_map.get(trade.order_ref):
                self.active_order_close_map.pop(self.order_ref_map[trade.order_ref])
            if self.original_win_loss_close_map.get(str(trade.order_ref)):
                trade.win_price = self.original_win_loss_close_map[str(trade.order_ref)][0]
                trade.loss_price = self.original_win_loss_close_map[str(trade.order_ref)][1]
            else:
                self.write_log(f'{trade.symbol}记录原止盈止损收盘委托价字典出现错误{self.original_win_loss_close_map}')

        # 保存或更新成交单信息
        strategy_update_trade(trade, self.order_id_map, self.order_ref_map, self.strategy_name, self.__class__.__name__, self.account)
        # 重新查询持仓数据
        order_data_list_all = TradeDataModel().query_open_positions_data(self.strategy_name, self.__class__.__name__, self.account.accountid)
        self.open_interest_data_dict.clear()
        for order_data in order_data_list_all:
            self.open_interest_data_dict[order_data.symbol].append(order_data)

        self.put_event()

    def get_win_loss_price_long(self, symbol, open_price):
        """获取做多止盈止损价、会变化的止损价"""
        yesterday_low_price = self.bars_history_current_all[symbol][-1].low_price
        change_loss_price = abs(open_price - yesterday_low_price) * self.parameters_map[symbol]["multiple_change_loss_price"]["value"] + open_price
        win_price = abs(open_price - yesterday_low_price) * self.parameters_map[symbol]["multiple_win_long"]["value"] + open_price
        loss_price = min(yesterday_low_price, open_price - open_price * self.parameters_map[symbol]["lowest_loss_price_percent"]["value"])
        return win_price, loss_price, change_loss_price

    def get_win_loss_price_short(self, symbol, open_price):
        """获取做空止盈止损价、会变化的止损价"""
        yesterday_high_price = self.bars_history_current_all[symbol][-1].high_price
        change_loss_price = open_price - abs(open_price - yesterday_high_price) * self.parameters_map[symbol]["multiple_change_loss_price"]["value"]
        win_price = open_price - abs(yesterday_high_price - open_price) * self.parameters_map[symbol]["multiple_win_short"]["value"]
        loss_price = max(yesterday_high_price, open_price + open_price * self.parameters_map[symbol]["lowest_loss_price_percent"]["value"])
        return win_price, loss_price, change_loss_price

    def trade_before(self):
        """
        交易前的准备工作：
            判断是做多/空,确定多/空的入场价
        """
        for transaction_data in self.query_open_interest_data:
            # 获取未平仓的开仓单的开仓当天的历史数据
            current_open_date = current_trade_date(transaction_data.trade_date)  # 获取开仓日当天日期
            if not current_open_date:
                self.write_log("从数据库中的无法获取当天交易的日期")
                continue
            exchange = Convert().convert_jqdata_exchange(exchange=transaction_data.exchange)
            open_date_bar = database_manager.load_bar_data(
                symbol=transaction_data.symbol,
                exchange=exchange,
                interval=Interval.DAILY,
                start=current_open_date,
                end=current_open_date
            )
            if len(open_date_bar) == 0:
                self.write_log(f'{transaction_data.symbol},dbbardata表中历史数据不足,无法获取开仓单当天的bar数据,此笔仓位数据不添加到持仓字典中')
                continue
            for data_bar in open_date_bar:
                self.open_date_bar_map[transaction_data.orderid] = data_bar

        # 获取20天历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=INIT_DAY)  # INIT_DAY=20
        vt_symbols = deepcopy(self.vt_symbols)
        for vt_symbol in vt_symbols:
            symbol, exchange = extract_vt_symbol(vt_symbol)
            exchange = Convert().convert_jqdata_exchange(exchange=exchange.value)
            data_history_bars = database_manager.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                interval=Interval.DAILY,
                start=start_date,
                end=end_date,
            )
            if len(data_history_bars) < 3:
                self.write_log(f'{vt_symbol}历史数据不足,无法进行交易')
                self.vt_symbols.remove(vt_symbol)
                continue

            # 保存最近2天的历史bar数据
            bars_history_current = []
            for data_bar in data_history_bars:
                bars_history_current.append(data_bar)
                if len(bars_history_current) <= 2:
                    continue
                else:
                    bars_history_current.pop(0)

            self.bars_history_current_all[symbol] = bars_history_current  # 保存最近2天的bar数据

            # 做多做空判断
            middle_before_yesterday = (bars_history_current[-2].low_price + bars_history_current[-2].high_price) / 2
            if bars_history_current[-1].close_price >= middle_before_yesterday:
                self.is_open_long_all[symbol] = True
            elif bars_history_current[-1].close_price < middle_before_yesterday:
                self.is_open_short_all[symbol] = True
            if not self.parameters_map.get(symbol, None):
                continue

            # 根据入场点确定做多做空的入场价
            if self.parameters_map[symbol]["point_enter"] == 1:
                enter_price_long = bars_history_current[-1].high_price
                enter_price_short = bars_history_current[-1].low_price
            else:
                enter_price_long = max(bars_history_current[-1].high_price, bars_history_current[-2].high_price)
                enter_price_short = min(bars_history_current[-1].low_price, bars_history_current[-2].low_price)
            self.enter_price_long_all[symbol] = enter_price_long
            self.enter_price_short_all[symbol] = enter_price_short

    def get_fixed_size(self, tick, direction, order_ref=""):
        """价格一旦触发开仓条件,先设置给止损止盈价(理论上的,此时还没有进行委托),再返回开仓手数用于开仓"""
        engine = self.strategy_engine.main_engine
        max_open_loss_rate = self.parameters_map[tick.symbol]["max_open_loss_rate"]["value"]
        if direction == 'LONG':
            win_price, loss_price, change_loss_price = self.get_win_loss_price_long(tick.symbol, tick.last_price)  # 设置止盈止损价以及会变化的止损价。
            fixed_size = self.risk_control(tick.vt_symbol, engine, tick.last_price, loss_price, max_open_loss_rate=max_open_loss_rate, order_ref=order_ref, balance=True)
        elif direction == 'SHORT':
            win_price, loss_price, change_loss_price = self.get_win_loss_price_short(tick.symbol, tick.last_price)  # 设置止盈止损价以及会变化的止损价。
            fixed_size = self.risk_control(tick.vt_symbol, engine, tick.last_price, loss_price, max_open_loss_rate=max_open_loss_rate, order_ref=order_ref, balance=True)
        else:
            fixed_size = self.fixed_size
        if not fixed_size:
            self.risk_ctrl_cond[tick.symbol] = 1
            self.portfolioramvalue.update_value(self.strategy_name, self.account.accountid, self.risk_ctrl_cond)
            self.write_log(f'{tick.symbol}因风险控制无法开仓')
        return fixed_size

    def update_memory_variable_price(self, order_data, tick, win_price, loss_price):
        """
        更新内存(self.open_interest_data_dict)中的止盈止损价
        """
        self.open_interest_data_dict[tick.symbol].remove(order_data)
        order_data.win_price = win_price
        order_data.loss_price = loss_price
        self.open_interest_data_dict[tick.symbol].append(order_data)

    def get_order_ref(self, order_data, close_price):
        """获取order_ref,记录原止盈止损平仓价"""
        order_ref = get_order_ref_value()
        self.order_id_map[order_ref] = order_data.orderid
        self.order_ref_map[order_ref] = order_data.order_ref
        self.original_win_loss_close_map[order_ref].append(order_data.win_price)
        self.original_win_loss_close_map[order_ref].append(order_data.loss_price)
        self.original_win_loss_close_map[order_ref].append(close_price)
        return order_ref

    def position_building(self, tick):
        """
        平仓:
            平多/空仓
        """
        # print(self.direction_symbol.get(tick.symbol), self.is_open_today.get(tick.symbol), self.risk_ctrl_cond.get(tick.symbol), self.active_order_open_map.get(tick.symbol))
        if self.direction_symbol.get(tick.symbol) and not self.is_open_today.get(tick.symbol) and not \
                self.risk_ctrl_cond.get(tick.symbol) and not self.active_order_open_map.get(tick.symbol):

            order_ref = get_order_ref_value()
            if self.direction_symbol[tick.symbol] == 'LONG':
                # print(tick.last_price, self.enter_price_long_all[tick.symbol], self.is_open_long_all.get(tick.symbol))
                if tick.last_price >= self.enter_price_long_all[tick.symbol] and self.is_open_long_all.get(tick.symbol):
                    self.buying(tick, order_ref, "LONG", self.buy, tick.limit_up, "以前两日的最高价", "委托开多仓")

            elif self.direction_symbol[tick.symbol] == 'SHORT':
                # self.is_open_short_all[tick.symbol] = True
                # print(tick.last_price, self.enter_price_short_all[tick.symbol], self.is_open_short_all.get(tick.symbol, None))
                if tick.last_price <= self.enter_price_short_all[tick.symbol] and self.is_open_short_all.get(tick.symbol, None):
                    self.buying(tick, order_ref, "SHORT", self.short, tick.limit_down, "以前两日的最低价", "委托开空仓")

            elif self.direction_symbol[tick.symbol] == 'NET':
                if tick.last_price >= self.enter_price_long_all[tick.symbol]:
                    self.buying(tick, order_ref, "LONG", self.buy, tick.limit_up, "以前两日的最高价", "委托开多仓")
                elif tick.last_price <= self.enter_price_short_all[tick.symbol]:
                    self.buying(tick, order_ref, "SHORT", self.short, tick.limit_down, "以前两日的最低价", "委托开空仓")

    def close_position(self, tick):
        """
        平仓：
            平多/空仓
        """
        order_data_list = self.open_interest_data_dict[tick.symbol]
        for order_data in order_data_list:
            if self.active_order_close_map.get(order_data.order_ref):  # 如果这笔持仓单正在委托平仓中
                continue
            if order_data.direction == 'LONG':
                self.close_long(tick, order_data)  # 平多仓

            elif order_data.direction == 'SHORT':  # 平空仓
                self.close_short(tick, order_data)


    def buying(self, tick, order_ref, direction, buying, price, content_1, content_2):
        fixed_size = self.get_fixed_size(tick, direction, order_ref=order_ref)
        if fixed_size:
            vt_orderid = buying(tick.vt_symbol, price, fixed_size, order_ref=order_ref)
            if vt_orderid:
                self.active_order_open_map[tick.symbol] = True
            write_local_log(self.strategy_name, f"{tick.symbol}{content_1}:{self.enter_price_short_all[tick.symbol]}{content_2}{fixed_size}手,{tick}")

    def close_long(self, tick, order_data):
        """
        平多仓：
            1.当会变化的止损价没变化之前且最新价 >= 会变化的止损价初始化值时,更新止盈止损价。
            2.达到止盈止盈一半,更新止盈止损价,另一半只能止损出场。
            3.如果达到止损,全部止损掉。
        """
        if not self.is_change_loss_price_map.get(order_data.orderid):
            change_loss_price = self.repeatedly_change_loss_price_map.get(order_data.orderid, 0)
            if tick.last_price >= change_loss_price and change_loss_price:
                open_date_bar = self.open_date_bar_map.get(order_data.orderid)
                if open_date_bar:
                    loss_price = open_date_bar.low_price
                else:
                    loss_price = tick.low_price
                    self.write_log(f'{tick.symbol}获取不到做多开仓单当日数据，使用此时最低价')
                win_price = order_data.win_price
                write_local_log(self.strategy_name, f'{tick.symbol}更新止损价格,原止损价{order_data.loss_price},新止损价{loss_price}，change_price为{change_loss_price}')
                TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
                self.update_memory_variable_price(order_data, tick, win_price, loss_price)
                self.is_change_loss_price_map[order_data.orderid] = True
                self.put_event()

        if tick.last_price >= order_data.win_price:  # 止盈
            if order_data.volume == order_data.un_volume:  # 达到止盈先止盈一半
                order_ref = self.get_order_ref(order_data, order_data.win_price)
                vt_orderid = self.sell(tick.vt_symbol, tick.limit_down, int(order_data.volume / 2), order_ref=order_ref)
                if vt_orderid:
                    self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                    self.active_order_close_map[order_data.order_ref] = True
            # 更新止盈止损价
            if self.bars_history_current_all.get(tick.symbol):
                loss_price = self.bars_history_current_all[tick.symbol][-1].low_price
            else:
                write_local_log(self.strategy_name, f'无历史数据，止损价不变')
                loss_price = order_data.loss_price
            win_price = tick.last_price
            write_local_log(self.strategy_name, f'{tick.symbol}更新止盈止损价格,原止盈止损价{order_data.win_price, order_data.loss_price},新止盈止损价{win_price, loss_price}')
            TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
            self.update_memory_variable_price(order_data, tick, win_price, loss_price)

        elif tick.last_price < order_data.loss_price:  # 止损
            order_ref = self.get_order_ref(order_data, order_data.loss_price)
            vt_orderid = self.sell(tick.vt_symbol, tick.limit_down, int(order_data.un_volume), order_ref=order_ref)
            if vt_orderid:
                self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                self.active_order_close_map[order_data.order_ref] = True
            write_local_log(self.strategy_name, f'{tick.symbol}以止损价{order_data.loss_price}委托平仓,{tick}')

    def close_short(self, tick, order_data):
        """
        平空仓:
            1.当会变化的止损价没变化之前且最新价 <= 会变化的止损价初始化值时,更新止盈止损价。
            2.达到止盈止盈一半,更新止盈止损价,另一半只能止损出场。
            3.如果达到止损,全部止损掉。
        """
        if not self.is_change_loss_price_map.get(order_data.orderid):
            change_loss_price = self.repeatedly_change_loss_price_map.get(order_data.orderid, 0)
            if tick.last_price <= change_loss_price and change_loss_price:
                open_date_bar = self.open_date_bar_map.get(order_data.orderid)
                if open_date_bar:
                    loss_price = open_date_bar.high_price
                else:
                    loss_price = tick.high_price
                    self.write_log(f'{tick.symbol}获取不到做空开仓单当日数据，使用此时最高价')
                win_price = order_data.win_price
                write_local_log(self.strategy_name, f'{tick.symbol}更新止损价格,原止损价{order_data.loss_price},新止损价{loss_price}，change_price为{change_loss_price}')
                TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
                self.update_memory_variable_price(order_data, tick, win_price, loss_price)
                self.is_change_loss_price_map[order_data.orderid] = True
                self.put_event()

        if tick.last_price <= order_data.win_price:   # 止赢
            if order_data.volume == order_data.un_volume:  # 达到止盈先止盈一半
                order_ref = self.get_order_ref(order_data, order_data.win_price)
                vt_orderid = self.cover(tick.vt_symbol, tick.limit_up, int(order_data.volume / 2), order_ref=order_ref)
                if vt_orderid:
                    self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                    self.active_order_close_map[order_data.order_ref] = True
            if self.bars_history_current_all.get(tick.symbol):
                loss_price = self.bars_history_current_all[tick.symbol][-1].high_price
            else:
                write_local_log(self.strategy_name, f'无历史数据，止损价不变')
                loss_price = order_data.loss_price
            win_price = tick.last_price
            write_local_log(self.strategy_name, f'{tick.symbol}更新止盈止损价格,原止盈止损价{order_data.win_price, order_data.loss_price},新止盈止损价{win_price, loss_price}')
            TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
            # 为什么此时不更新order_data的未平仓量(un_volume}呢？因为只要这笔开仓单在委托平仓时，直到这笔委托单终止交易了,才考虑下一次委托。
            # 而在on_trade()中更新了成交表中这笔开仓的单的un_volume,又重新查询了(self.open_interest_data_dict重新赋值了)
            # 所以此时没必要通过self.update_memory_variable_price()来更改self.open_interest_data_dict中的开仓数据中的un_volume(而且通过它更改也不合理,因为此时还不知道委托单能否交易成功)
            self.update_memory_variable_price(order_data, tick, win_price, loss_price)

        elif tick.last_price >= order_data.loss_price:    # 止损
            order_ref = self.get_order_ref(order_data, order_data.loss_price)
            vt_orderid = self.cover(tick.vt_symbol, tick.limit_up, int(order_data.un_volume), order_ref=order_ref)
            if vt_orderid:
                self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                self.active_order_close_map[order_data.order_ref] = True
            write_local_log(self.strategy_name, f'{tick.symbol}以止损价{order_data.loss_price}委托平仓,{tick}')

