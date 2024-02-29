
import json
import time
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List, Dict
from vnpy.app.cta_strategy.convert import Convert
from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.common.order import get_order_ref_no, write_local_log, is_open_today_judge, trade_updata, order_updata, \
    trade_current_date
from vnpy.model.open_symbol_data_model import OpenSymbolModel
from vnpy.model.strategy_portfolio_ram_value import PortfolioRamValue
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.constant import Interval
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData, BarData, TradeData, OrderData
from vnpy.trader.utility import extract_vt_symbol

"""
达到止盈前时,止损价就变换。
"""

class StockPorfolioTradeStrategy(StrategyTemplate):
    """"""
    author = "jun"

    multiple_win_long = 1.5
    point_enter = 2
    lowest_loss_price_percent = 0.01
    multiple_change_loss_price = 0.78
    rate = 0.04

    parameters = [
        "rate",
        "multiple_change_loss_price",
        "multiple_win_long",
        "point_enter",
        "lowest_loss_price_percent"
    ]
    parameters_chinese = {
        "rate": "最大亏损的1.5倍与开仓价的比率",
        "multiple_change_loss_price": "计算改变止损价的参数因子",
        "multiple_win_long": "止盈倍数",
        "point_enter": "入场点，突破昨日高点填1，突破前两日高点填2",
        "lowest_loss_price_percent": "计算止损价的参数因子"
    }

    is_change_loss_price_map = {}
    multiple_change_loss_price_map = {}

    variables = [
        "is_change_loss_price_map",
        "multiple_change_loss_price_map"
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
        # 上一个tick的时间
        self.last_tick_time = None
        self.fixed_size = 1
        # 此次交易的方向字典:以symbol为键,direction为值。
        self.direction_symbol = {}
        # 存储用来开仓的vt_symbol的列表
        self.vt_symbols_open = []
        # 今天是否开过仓字典:以symbol为键,bool值为值。
        self.is_open_today = {}
        # 当前股票历史数据字典:以symbol为键,symbol对应的历史数据对象为值。
        self.bars_history_current_all = {}
        # 做多确认价字典：以symbol为键,price为值。
        self.enter_price_long_all = {}
        # 是否允许做多的字典:以symbol为键，bool为值。
        self.is_open_long_all = {}
        # 开仓委托映射字典:为vt_symbol为键,以bool值为值。为True时证明此股票已经委托开仓了。一分钟只做一次,所以不需要在on_trade中把它设为False。
        self.commission_open_map = {}
        # 平仓委托映射字典:为vt_symbol为键,以bool值为值。为True时证明此股票已经委托平仓了。一分钟只做一次。
        self.commission_close_map = {}
        # 委托数据字典:以symbol为键,委托数据对象为值(委托数据其实就是在成交表中还未平仓完毕的数据)
        self.order_data_dict = defaultdict(list)
        # order_ref和orderid的映射字典:以order_ref为键,orderid为值
        self.order_id_map = defaultdict()
        # order_ref的映射:键为get_order_ref_no()生成的order_ref,值为传进去的数据对象的order_ref。
        self.order_ref_map = defaultdict()
        # 记录委托数据的原止盈止损收盘的字典:键为get_order_ref_no()生成的order_ref,值为[win_price,loss_price,close_price]。
        self.original_win_loss_close_map = defaultdict(list)
        # 风险控制模型类的对象
        self.portfolioramvalue = PortfolioRamValue()
        # 此次交易的参数映射字典：以symbol为键,strategy_args为值。
        self.parameters_map = {}
        # 开仓代码的历史数据映射字典:为orderid为键,symbol对应的历史数据为值。

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        # 获取交易账号
        account_id = self.strategy_engine.main_engine.get_gateway('XTP').td_api.userid
        self.vt_symbols = []
        if not account_id:
            self.write_log('策略未成功初始化，请重启连接账户之后再初始化')
            return

        # 从成交表中获取策略开仓但还未平仓完的数据
        self.order_data_list_all = TradeDataModel().select_order_data_all(self.strategy_name, self.__class__.__name__, account_id)
        for order_data in self.order_data_list_all:
            self.vt_symbols.append(str(order_data.symbol + '.' + order_data.exchange))
            self.order_data_dict[order_data.symbol].append(order_data)

        # 从web筛选出来用于交易的表中查询出数据
        self.open_symbol_data = OpenSymbolModel().select_open_data(account_id, self.__class__.__name__)

        # 如果此股票在交易表中显示还持仓,证明已经交易过,则今天不开仓,则从股票开仓数据列表中删除(self.open_symbol_data)
        for open_data in self.open_symbol_data:
            vt_symbol = str(open_data.symbol + '.' + open_data.exchange)
            if vt_symbol in self.vt_symbols_open:
                self.open_symbol_data.remove(open_data)
                self.write_log(f'已存在该品种:{vt_symbol, open_data.direction},不对此条记录进行操作。')
                continue
            # 如果没有开仓过,则把相关数据加入到相关对象中,为开仓做准备。
            self.vt_symbols_open.append(vt_symbol)
            self.direction_symbol[open_data.symbol] = open_data.direction
            self.parameters_map[open_data.symbol] = json.loads(open_data.strategy_args)
            # 查询今天是否开仓过,以symbol为键,bool值为值存到self.is_open_today。
            self.is_open_today[open_data.symbol] = is_open_today_judge(self.strategy_name, self.__class__.__name__, open_data.symbol, account_id)
            for key, value in self.parameters_map[open_data.symbol].items():
                if value["value"]:
                    self.parameters_map[open_data.symbol][key]["value"] = float(value["value"])  # 此步多余
                else:
                    self.parameters_map[open_data.symbol][key]["value"] = self.parameters[key]
        self.vt_symbols.extend(self.vt_symbols_open)
        self.vt_symbols = list(set(self.vt_symbols))
        self.init_data()
        self.write_log(f'开仓品种:{set(self.vt_symbols_open)}')

        # self.risk_ctrl_cond为空,则更新risk_ctrl_cond字段的值。
        if len(self.risk_ctrl_cond) == 0:
            for open_data in self.open_symbol_data:
                self.risk_ctrl_cond[open_data.symbol] = 0
                print(self.risk_ctrl_cond)
            self.portfolioramvalue.update_value(self.strategy_name, account_id, self.risk_ctrl_cond)
        self.load_bars(15, interval=Interval.DAILY, use_database=True)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        is_change = {}   # 是否变化的字典：以orderid为键,bool为值。
        change_loss = {}  # 改变止损的字典:以orderid为键,price为值。
        for order_data in self.order_data_list_all:
            if self.is_change_loss_price_map.get(order_data.orderid):
                is_change[order_data.orderid] = True
            if self.multiple_change_loss_price_map.get(order_data.orderid):
                change_loss[order_data.orderid] = self.multiple_change_loss_price_map[order_data.orderid]
        # 止损价是否变化映射字典:以orderid为键,bool为值。
        self.is_change_loss_price_map = deepcopy(is_change)
        # 止损价变动映射字典:以orderid为键,price为值。
        self.multiple_change_loss_price_map = deepcopy(change_loss)
        del is_change, change_loss
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
        start_time = time.time()
        tick_time = tick.datetime
        if not self.account:
            return

        # 新的一分钟到来
        if (self.last_tick_time and self.last_tick_time.minute != tick.datetime.minute):
            self.renew()
        self.last_tick_time = tick.datetime

        if self.trading:
            if self.direction_symbol.get(tick.symbol) and not self.is_open_today.get(tick.symbol) and not \
                    self.commission_open_map.get(tick.vt_symbol) and not self.risk_ctrl_cond.get(tick.symbol):
                # 开仓逻辑
                if self.direction_symbol[tick.symbol] == 'LONG':
                    if tick.last_price >= self.enter_price_long_all[tick.symbol] and self.is_open_long_all.get(tick.symbol):
                        fixed_size = self.get_fixed_size(tick, "LONG")
                    else:
                        fixed_size = self.fixed_size
                        if fixed_size:
                            self.buy(tick.vt_symbol, tick.limit_up, fixed_size)
                            self.commission_open_map[tick.vt_symbol] = True
                            write_local_log(self.strategy_name, f"{tick.symbol}以前两日的最高价{self.enter_price_long_all[tick.symbol]}委托开多仓{fixed_size}手,"f"{tick}")

            order_data_list = self.order_data_dict[tick.symbol]
            for order_data in order_data_list:
                if self.commission_close_map.get(str(order_data.order_ref)):
                    continue

                if order_data.direction == 'SHORT':
                    if not self.is_change_loss_price_map.get(order_data.orderid):
                        change_price = self.multiple_change_loss_price_map.get(order_data.orderid, 0)
                        if tick.last_price <= change_price and change_price:
                            open_date_bar = self.open_date_bar_map.get(order_data.orderid)
                            if open_date_bar:
                                loss_price = open_date_bar.high_price

                            else:
                                loss_price = tick.high_price
                                self.write_log(f'{tick.symbol}获取不到日数据，使用此时最高价')
                            win_price = order_data.win_price
                            write_local_log(self.strategy_name,
                                            f'{tick.symbol}更新止损价格,原止损价{order_data.loss_price},'
                                            f'新止损价{loss_price}，change_price为{change_price}')
                            TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
                            self.updata_price(order_data, tick, win_price, loss_price)
                            self.is_change_loss_price_map[order_data.orderid] = True
                            self.put_event()

                    if tick.last_price <= order_data.win_price:
                        if order_data.volume == order_data.un_volume:
                            order_ref = self.get_order_ref(order_data, order_data.win_price)
                            vt_orderid = self.cover(tick.vt_symbol, tick.limit_up, int(order_data.volume / 2), order_ref=order_ref)
                            if vt_orderid:
                                self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                        loss_price = self.bars_history_current_all[tick.symbol][-1].high_price
                        win_price = tick.last_price
                        write_local_log(self.strategy_name, f'{tick.symbol}更新止盈止损价格,原止盈止损价{order_data.win_price, order_data.loss_price},'
                                                            f'新止盈止损价{win_price, loss_price}')
                        TradeDataModel().update_loss_win_price(order_data, loss_price, win_price)
                        self.updata_price(order_data, tick, win_price, loss_price)
                    elif tick.last_price >= order_data.loss_price:
                        order_ref = self.get_order_ref(order_data, order_data.loss_price)
                        vt_orderid = self.cover(tick.vt_symbol, tick.limit_up, int(order_data.un_volume), order_ref=order_ref)
                        if vt_orderid:
                            self.vt_orderid_map[order_data.order_ref] = vt_orderid[0]
                        write_local_log(self.strategy_name, f'{tick.symbol}以止损价{order_data.loss_price}委托平仓,'
                                                            f'{tick}')
        end_time = time.time()
        write_local_log('interval', f'{tick.symbol}，tick时间：{tick_time}，时差：{end_time-start_time}，开始时间：{start_time}，结束时间：{end_time}')

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
            if order.direction.name == "LONG":
                order.price = self.enter_price_long_all[order.symbol]
        else:
            if self.original_win_loss_close_map.get(str(order.order_ref)):
                order.price = self.original_win_loss_close_map[str(order.order_ref)][2]
            else:
                self.write_log(f'{order.symbol}记录原止盈止损收盘委托价字典出现错误{self.original_win_loss_close_map}')
        order_updata(order, self.order_id_map, self.strategy_name, self.__class__.__name__, self.account)

    def on_trade(self, trade: TradeData):
        if trade.offset.name == 'OPEN':
            if trade.direction.name == 'LONG':
                trade.win_price, trade.loss_price, change_price = self.get_win_loss_price_long(trade.symbol, trade.price)

            self.is_open_today[trade.symbol] = True
            self.multiple_change_loss_price_map[trade.orderid] = change_price
            self.commission_open_map[trade.symbol] = False
        else:
            if self.original_win_loss_close_map.get(str(trade.order_ref)):
                trade.win_price = self.original_win_loss_close_map[str(trade.order_ref)][0]
                trade.loss_price = self.original_win_loss_close_map[str(trade.order_ref)][1]
            else:
                self.write_log(f'{trade.symbol}记录原止盈止损收盘委托价字典出现错误{self.original_win_loss_close_map}')
            self.commission_close_map[trade.symbol] = False
        trade_updata(trade, self.order_id_map, self.order_ref_map, self.strategy_name, self.__class__.__name__,
                     self.account)
        order_data_list_all = TradeDataModel().select_order_data_all(self.strategy_name,
                                                                     self.__class__.__name__, self.account.accountid)
        self.order_data_dict.clear()
        for order_data in order_data_list_all:
            self.order_data_dict[order_data.symbol].append(order_data)
        self.put_event()

    def init_data(self):
        for order_data in self.order_data_list_all:
            open_date = trade_current_date(order_data.trade_date)
            if not open_date:
                self.write_log('数据库中的交易日期不足')
                continue
            exchange = Convert().convert_jqdata_exchange(exchange=order_data.exchange)
            open_date_bar = database_manager.load_bar_data(
                symbol=order_data.symbol,
                exchange=exchange,
                interval=Interval.DAILY,
                start=open_date,
                end=open_date
            )
            if len(open_date_bar) == 0:
                self.write_log(f'{order_data.symbol}历史数据不足,无法获取开仓单天的bar数据')
                continue

            for data_bar in open_date_bar:
                self.open_date_bar_map[order_data.orderid] = data_bar

        end_date = datetime.now()
        start_date = end_date - timedelta(days=20)
        # 当前前20日的历史数据
        for vt_symbol in self.vt_symbols:
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

            bars_history_current = []
            for data_bar in data_history_bars:
                bars_history_current.append(data_bar)
                if len(bars_history_current) <= 2:
                    continue
                else:
                    bars_history_current.pop(0)
            self.bars_history_current_all[symbol] = bars_history_current
            middle_before_yesterday = (bars_history_current[-2].low_price + bars_history_current[-2].high_price) / 2
            if bars_history_current[-1].close_price >= middle_before_yesterday:
                self.is_open_long_all[symbol] = True

            if not self.parameters_map.get(symbol, None):
                continue
            if self.parameters_map[symbol]["point_enter"] == 1:
                enter_price_long = bars_history_current[-1].high_price
            else:
                enter_price_long = max(bars_history_current[-1].high_price, bars_history_current[-2].high_price)

            self.enter_price_long_all[symbol] = enter_price_long

    def get_win_loss_price_long(self, symbol, open_price):
        """获取做多止盈止损价"""
        loss_price = self.bars_history_current_all[symbol][-1].low_price
        change_loss_price = abs(open_price - loss_price) * self.parameters_map[symbol]["multiple_change_loss_price"]["value"] + open_price
        win_price = abs(open_price - loss_price) * self.parameters_map[symbol]["multiple_win_long"]["value"] + open_price
        loss_price = min(loss_price, open_price - open_price * self.parameters_map[symbol]["lowest_loss_price_percent"]["value"])
        return win_price, loss_price, change_loss_price

    def updata_price(self, order_data, tick, win_price, loss_price):
        """
        更新內存中有变换的止盈止损价
        """
        self.order_data_dict[tick.symbol].remove(order_data)
        order_data.win_price = win_price
        order_data.loss_price = loss_price
        self.order_data_dict[tick.symbol].append(order_data)

    def get_order_ref(self, order_data, close_price):
        """获取order_ref"""
        order_ref = get_order_ref_no()
        self.order_id_map[order_ref] = order_data.orderid
        self.order_ref_map[order_ref] = order_data.order_ref
        self.original_win_loss_close_map[order_ref].append(order_data.win_price)
        self.original_win_loss_close_map[order_ref].append(order_data.loss_price)
        self.original_win_loss_close_map[order_ref].append(close_price)
        self.commission_close_map[str(order_data.order_ref)] = True
        return order_ref

    def get_fixed_size(self, tick, direction):
        """
        获取交易手数
        """
        start_time = time.time()
        engine = self.strategy_engine.main_engine
        rate = self.parameters_map[tick.symbol]["rate"]["value"]
        if direction == 'LONG':
            win_price, loss_price, change_price = self.get_win_loss_price_long(tick.symbol, tick.last_price)
            fixed_size = self.risk_control(tick.vt_symbol, engine, tick.last_price, loss_price, rate)
        else:
            fixed_size = self.fixed_size
        if not fixed_size:
            self.risk_ctrl_cond[tick.symbol] = 1
            self.portfolioramvalue.update_value(self.strategy_name, self.account.accountid, self.risk_ctrl_cond)
            self.write_log(f'{tick.symbol}因风险控制无法开仓')
        end_time = time.time()
        write_local_log(self.strategy_name, f'{end_time-start_time, start_time, end_time}')
        return fixed_size

    def renew(self):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.commission_open_map.clear()
        self.commission_close_map.clear()



