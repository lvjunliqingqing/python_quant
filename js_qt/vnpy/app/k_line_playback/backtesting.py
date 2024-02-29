import os
import platform
import string
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Callable
import numpy as np
import plotly.graph_objects as go
import seaborn as sns
from pandas import DataFrame
from plotly.subplots import make_subplots
from vnpy.app.cta_strategy import CtaTemplate
from vnpy.app.cta_strategy.base import (
    BacktestingMode,
    EngineType,
    STOPORDER_PREFIX,
    StopOrder,
    StopOrderStatus,
    INTERVAL_DELTA_MAP
)
from vnpy.controller.trade_operation import get_order_ref_value
from vnpy.trader.constant import (Direction, Offset, Exchange,
                                  Interval, Status)
from vnpy.trader.database import database_manager
from vnpy.trader.object import OrderData, TradeData, BarData, TickData
from vnpy.trader.symbol_attr import ContractMultiplier
from vnpy.trader.utility import round_to, get_letter_from_symbol
from ..cta_strategy.convert import Convert

# Set seaborn style
sns.set_style("whitegrid")


class PlaybackBacktestingEngine:
    """"""

    engine_type = EngineType.BACKTESTING
    gateway_name = "BACKTESTING"

    def __init__(self):
        """"""
        self.vt_symbol = ""
        self.symbol = ""
        self.exchange = None
        self.start = None
        self.end = None
        self.rate = 0
        self.slippage = 0
        self.size = 1
        self.pricetick = 0
        self.capital = 1_000_000
        self.mode = BacktestingMode.BAR
        self.inverse = False

        self.strategy_class = None
        self.strategy = None
        self.tick: TickData
        self.bar: BarData
        self.datetime = None

        self.interval = None
        self.days = 0
        self.callback = None
        self.history_data = []  # 存储加载的历史数据

        self.stop_order_count = 0
        self.stop_orders = {}  # 仅存储停止委托单
        self.active_stop_orders = {}

        self.limit_order_count = 0
        self.limit_orders = {}  # 存储所有委托单(同时存储限价委托单和停止委托单)
        self.active_limit_orders = {}  # 限价单活动字典

        self.trade_count = 0
        self.trades = {}  # 存储所有的成交单
        self.dt_trades_map = defaultdict(list)  # {trade.datetime:[trade]}

        self.logs = []  # 存储日志信息

        self.daily_results = {}  # {datetime:每日盈亏结果数据对象}
        self.daily_df = None

    def clear_data(self):
        """
        Clear all data of last back-testing.
        """
        self.strategy = None
        self.tick = None
        self.bar = None
        self.datetime = None

        self.stop_order_count = 0
        self.stop_orders.clear()
        self.active_stop_orders.clear()

        self.limit_order_count = 0
        self.limit_orders.clear()
        self.active_limit_orders.clear()

        self.trade_count = 0
        self.trades.clear()
        self.dt_trades_map.clear()

        self.logs.clear()
        self.daily_results.clear()

    def set_parameters(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        rate: float,
        slippage: float,
        size: float,
        pricetick: float,
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
        inverse: bool = False
    ):
        """"""
        self.mode = mode
        self.vt_symbol = vt_symbol
        self.interval = Interval(interval)
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        self.start = start

        self.symbol, exchange_str = self.vt_symbol.split(".")
        self.exchange = Exchange(exchange_str)

        self.capital = capital
        self.end = end
        self.mode = mode
        self.inverse = inverse

    def add_strategy(self, strategy_class: type, setting: dict):
        """实例化一个策略对象"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.vt_symbol, setting
        )

    def load_data(self):
        """"""
        self.output("开始加载历史数据")

        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            self.output("起始日期必须小于结束日期")
            return

        self.history_data.clear()       # Clear previously loaded history data

        # Load 30 days of data each time and allow for progress update
        progress_delta = timedelta(days=30)
        total_delta = self.end - self.start
        interval_delta = INTERVAL_DELTA_MAP[self.interval]
        if self.interval == Interval.MINUTE:
            start = datetime.strptime(str(self.start), '%Y-%m-%d')
            end = start + progress_delta
            self.end = datetime.strptime(str(self.end), '%Y-%m-%d')
        else:
            start = self.start
            end = self.start + progress_delta
        progress = 0

        exchange = self.exchange
        self.exchange = Convert().convert_jqdata_exchange(exchange=exchange)

        while start < self.end:
            end = min(end, self.end)  # Make sure end time stays within set range

            if self.mode == BacktestingMode.BAR:
                data = load_bar_data(
                    self.symbol,
                    self.exchange,
                    self.interval,
                    start,
                    end
                )
            else:
                data = load_tick_data(
                    self.symbol,
                    self.exchange,
                    start,
                    end
                )

            self.history_data.extend(data)  # 存储加载的历史数据

            progress += progress_delta / total_delta
            progress = min(progress, 1)
            progress_bar = "#" * int(progress * 10)
            self.output(f"加载进度：{progress_bar} [{progress:.0%}]")

            start = end + interval_delta
            end += (progress_delta + interval_delta)

        self.output(f"历史数据加载完成，数据量：{len(self.history_data)}")

        # 将所需要的历史bar数据,合约乘数,回测资金赋进策略中(lv jun 个人所加)
        self.strategy.history_data = self.history_data
        self.strategy.size = self.size
        self.strategy.capital = self.capital

    def run_backtesting(self):
        """"""
        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick

        self.strategy.on_init()  # 初始化策略
        self.history_data = self.strategy.history_data
        # 使用策略中指定的n(self.days）天历史数据来初始化策略
        day_count = 1
        ix = 0

        for ix, data in enumerate(self.history_data):
            if self.datetime and data.datetime.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break

            self.datetime = data.datetime

            try:
                self.callback(data)  # 真正执行策略初始化的逻辑函数(callback默认是策略中的on_bar())
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return

        self.strategy.inited = True
        self.output("复盘策略初始化完成")

        self.strategy.on_start()
        self.strategy.trading = True
        # self.output("复盘开始回放历史数据")

        # 使用剩余的历史数据来运行复盘策略回测
        for data in self.history_data[ix:]:
            try:
                func(data)
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return

        self.strategy.on_stop()
        # self.output("复盘历史数据回放结束")

    def calculate_result(self):
        """"""
        # self.output("复盘开始计算逐日盯市盈亏")
        if not self.trades:
            # self.output("成交记录为空，无法计算")
            return

        # 将交易数据添加到每日结果对象中。
        for trade in self.trades.values():
            d = trade.datetime.date()
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)

        # 通过迭代计算每日结果。
        pre_close = 0
        start_pos = 0
        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_close,
                start_pos,
                self.size,
                self.rate,
                self.slippage,
                self.inverse
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

        # 创建个默认字典(默认值为list)
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        # self.output("复盘逐日盯市盈亏计算完成")

        return self.daily_df

    def calculate_statistics(self, df: DataFrame = None, output=True):
        """"""
        # self.output("复盘开始计算策略统计指标")

        # Check DataFrame input exterior
        if df is None:
            df = self.daily_df

        # Check for init DataFrame
        if (df is None) or (not self.trades):
            # Set all statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            max_drawdown_duration = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0

            # lv jun个人所加
            win_ratio = 0
            win_loss_ratio = 0
            return_risk_ratio = 0
            real_yields = 0

        else:
            # Calculate balance related time series data
            df["balance"] = df["net_pnl"].cumsum() + self.capital

            np.seterr(divide='ignore', invalid='ignore')  # 这行代码解决(RuntimeWarning: invalid value encountered in log)的bug

            df["return"] = np.log(df["balance"] / df["balance"].shift(1)).fillna(0)  # 每天的收益率
            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # lv jun个人添加
            winlist = []
            losslist = []
            use_price = 0
            for index, row in df.iterrows():
                for trade in row["trades"]:
                    if trade.offset.name == "OPEN":
                        if trade.direction.name == "LONG":
                            open_price = trade.price
                            orther = self.slippage + trade.price * self.rate
                        else:
                            open_price = trade.price
                            orther = self.slippage + trade.price * self.rate
                    else:
                        if trade.direction.name == "SHORT":
                            money = trade.volume * self.size * (
                                    trade.price - open_price - orther - self.slippage - trade.price * self.rate)
                        else:
                            money = trade.volume * self.size * (
                                    open_price - trade.price - orther - self.slippage - trade.price * self.rate)
                        if money > 0:
                            winlist.append(money)
                        elif money < 0:
                            losslist.append(money)
                    if trade.offset.name == "OPEN":
                        symbol_code = get_letter_from_symbol(trade.symbol)
                        use_price += trade.price * trade.volume * ContractMultiplier[symbol_code]
            # 胜率
            if (len(winlist) + len(losslist)) == 0:
                win_ratio = "0(旧的)"
            else:
                win_ratio = f"{round(abs(len(winlist) / (len(winlist) + len(losslist))), 2)}(旧的)"
            # 盈亏比
            if sum(losslist) == 0:
                win_loss_ratio = f"{round(sum(winlist), 2)}(旧的)"
            else:
                win_loss_ratio = f"{round(abs(sum(winlist) / sum(losslist)), 2)}(旧的)"
            # 实际收益率 = 总利润 / 总成本
            real_yields = f"{round(df['net_pnl'].sum() / use_price, 4)}"
            # 此处结束

            # Calculate statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()
            max_drawdown_end = df["drawdown"].idxmin()

            if isinstance(max_drawdown_end, date):
                max_drawdown_start = df["balance"][:max_drawdown_end].idxmax()
                max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days
            else:
                max_drawdown_duration = 0

            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * 240
            daily_return = df["return"].mean() * 100
            return_std = df["return"].std() * 100

            # lv jun个人所加 收益风险比
            if max_ddpercent:
                # 收益风险比 = 年化收益 / 百分比最大回测
                return_risk_ratio = abs(annual_return / max_ddpercent)
                # 收益回撤比 = -总收益率 / 百分比最大回测
                return_drawdown_ratio = -total_return / max_ddpercent
            else:
                return_risk_ratio = 0.00
                return_drawdown_ratio = 0.00

            if return_std:
                # 夏普比率 = (年收益率 - 5) / 收益标准差
                sharpe_ratio = (annual_return - 5) / (return_std * np.sqrt(240))
            else:
                sharpe_ratio = 0

        # lv jun个人所加
        if hasattr(self.strategy, 'is_write_csv') and self.strategy.is_write_csv:
            parameter_values = {
                "最大回撤": f"{max_drawdown:,.2f}",
                "百分比最大回撤": f"{max_ddpercent:,.2f}%",
                "总盈亏": f"{total_net_pnl:,.2f}",
                "总收益率": f"{total_return:,.2f}%"
            }

            df_strategy = self.storage_data(self.strategy.data, parameter_values)
            try:
                return_risk_ratio = abs(df_strategy["price_profits"].max() / df_strategy["price_profits"].min())
                win_ratio = round(df_strategy["win_ratio"].values[0], 2)
                win_loss_ratio = round(df_strategy["win_loss_ratio"].values[0], 2)
            except:
                pass

        # Output
        if output:
            self.output("-" * 30)
            self.output(f"首个交易日：\t{start_date}")
            self.output(f"最后交易日：\t{end_date}")

            self.output(f"总交易日：\t{total_days}")
            self.output(f"盈利交易日：\t{profit_days}")
            self.output(f"亏损交易日：\t{loss_days}")

            self.output(f"起始资金：\t{self.capital:,.2f}")
            self.output(f"结束资金：\t{end_balance:,.2f}")

            self.output(f"总收益率：\t{total_return:,.2f}%")
            self.output(f"年化收益：\t{annual_return:,.2f}%")
            self.output(f"最大回撤: \t{max_drawdown:,.2f}")
            self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")
            self.output(f"最长回撤天数: \t{max_drawdown_duration}")

            self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
            self.output(f"总手续费：\t{total_commission:,.2f}")
            self.output(f"总滑点：\t{total_slippage:,.2f}")
            self.output(f"总成交金额：\t{total_turnover:,.2f}")
            self.output(f"总成交笔数：\t{total_trade_count}")

            self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            self.output(f"日均手续费：\t{daily_commission:,.2f}")
            self.output(f"日均滑点：\t{daily_slippage:,.2f}")
            self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
            self.output(f"日均成交笔数：\t{daily_trade_count}")

            self.output(f"日均收益率：\t{daily_return:,.2f}%")
            self.output(f"收益标准差：\t{return_std:,.2f}%")
            self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            self.output(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

            self.output(f"胜率：\t{win_ratio:,.2f}")
            self.output(f"盈亏比：\t{win_loss_ratio}")
            self.output(f"收益风险比：\t{return_risk_ratio:,.2f}")
            self.output(f"实际收益率：\t{real_yields}")

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
            # lv jun个人所加
            "win_ratio": win_ratio,
            "win_loss_ratio": win_loss_ratio,
            "return_risk_ratio": return_risk_ratio,
            "real_yields": real_yields,
        }

        # 过滤掉正负无穷大值
        for key, value in statistics.items():
            if value in (np.inf, -np.inf):
                value = 0
            statistics[key] = np.nan_to_num(value)

        # self.output("复盘策略统计指标计算完成")
        return statistics

        # lv jun个人所加，获取策略中特别处理过的成交数据记录数据。
    def get_trades_record(self):
        if hasattr(self.strategy, 'is_write_csv') and self.strategy.is_write_csv:
            return self.strategy.data
        else:
            return None

    def storage_data(self, storage_data, parameter_values):
        results = defaultdict(list)
        if len(storage_data) == 0:
            return
        for data in storage_data:
            for key, value in data.items():
                results[key].append(value)
        df = DataFrame.from_dict(results).set_index("date_open")
        if df[df["price_profits"] < 0]["price_profits"].sum():
            win_loss_ratio = round(abs(df[df["price_profits"] > 0]["price_profits"].sum() / df[df["price_profits"] < 0]["price_profits"].sum()), 2)
        else:
            win_loss_ratio = round(df[df["price_profits"] > 0]["price_profits"].sum(), 2)
        df["win_loss_ratio"] = win_loss_ratio
        df1 = df.groupby('date_open')["price_profits"].sum()
        df['赢的次数'] = df1[df1 > 0].shape[0]
        df['交易的总次数'] = len(df1)
        df['win_ratio'] = df1[df1 >= 0].shape[0] / len(df1)

        try:
            all_daily_results = self.get_all_daily_results()
            list_data = []
            all_daily_results.reverse()
            for obj in all_daily_results:
                list_data.append(int(obj.end_pos))
            if min(list_data):
                df["最大持仓"] = min(list_data)
            if max(list_data):
                df["最大持仓"] = max(list_data)
        except:
            pass
        df["最大盈利"] = df["price_profits"].max()
        df["最大亏损"] = df["price_profits"].min()

        for k, v in parameter_values.items():
            df[k] = v

        try:
            df2 = df.rename(columns={'date_open ': '开仓时间', 'direction': '方向', 'win_price': '止盈价', 'loss_price': '止损价',
                                     'price_open': '开仓价', 'pos': '手数', 'price_sell': '平仓价', 'date_sell': '平仓时间',
                                     'price_profits': '盈亏金额(元)', 'win_loss': '盈亏(盈为1，亏为0）', 'parameters': '参数'
                                     , 'win_loss_ratio': '盈亏比', 'win_ratio': '胜率', 'multiple_win_long': '止盈倍数'})

            df2 = df2.rename_axis("开仓时间", axis=0).rename_axis(None, axis=1)
        except:
            df2 = df
        sys = platform.system()
        if sys == "Windows":
            disk_list = []
            for c in string.ascii_uppercase:
                disk = c + ':'
                if os.path.isdir(disk):
                    disk_list.append(disk)
            path = os.path.join(disk_list[1], "/backtesting_data")
            if not os.path.exists(path):
                os.mkdir(path)
            df2.to_csv("%s/%s_%s.csv" % (path, self.strategy.strategy_name, df['parameters'].iloc[0]),
                       encoding='utf_8_sig')

        elif sys == "Linux":
            path = "/data/backtesting_data"
            if not os.path.exists(path):
                os.mkdir(path)
            df2.to_csv("%s/%s_%s.csv" % (path, self.strategy.strategy_name, df['parameters'].iloc[0]), encoding='utf_8_sig')

        return df

    def show_chart(self, df: DataFrame = None):
        """"""
        # Check DataFrame input exterior
        if df is None:
            df = self.daily_df

        # Check for init DataFrame
        if df is None:
            return

        fig = make_subplots(
            rows=4,
            cols=1,
            subplot_titles=["Balance", "Drawdown", "Daily Pnl", "Pnl Distribution"],
            vertical_spacing=0.06
        )

        balance_line = go.Scatter(
            x=df.index,
            y=df["balance"],
            mode="lines",
            name="Balance"
        )
        drawdown_scatter = go.Scatter(
            x=df.index,
            y=df["drawdown"],
            fillcolor="red",
            fill='tozeroy',
            mode="lines",
            name="Drawdown"
        )
        pnl_bar = go.Bar(y=df["net_pnl"], name="Daily Pnl")
        pnl_histogram = go.Histogram(x=df["net_pnl"], nbinsx=100, name="Days")

        fig.add_trace(balance_line, row=1, col=1)
        fig.add_trace(drawdown_scatter, row=2, col=1)
        fig.add_trace(pnl_bar, row=3, col=1)
        fig.add_trace(pnl_histogram, row=4, col=1)

        fig.update_layout(height=1000, width=1000)
        fig.show()

    def update_daily_close(self, price: float):
        """
        更新self.daily_results中的DailyResult中的收盘价
        """
        d = self.datetime.date()
        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)

    def new_bar(self, bar: BarData):
        """"""
        self.bar = bar
        self.datetime = bar.datetime
        # 如果发停止单就行停止单撮合,发限价单就进行限价单撮合。
        self.cross_limit_order()  # 限价单撮合
        self.cross_stop_order()  # 停止单撮合
        self.strategy.on_bar(bar)

        self.update_daily_close(bar.close_price)

    def new_tick(self, tick: TickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick)

        self.update_daily_close(tick.last_price)

    def cross_limit_order(self):
        """
        撮合限价单委托
            1.当最新的行情K线或者TICK到来时,和策略之前下达的所有委托进行检查，如果能够撮合成交，则返回并记录数据。
            2.此函数中会调用两次 self.strategy.on_order()和一次 self.strategy.on_trade()
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.low_price  # (做多坏情况的限价)最低价或卖一价
            short_cross_price = self.bar.high_price  # (做空坏情况的限价)最高价或买一价
            long_best_price = self.bar.open_price  # (做多好情况的限价)开盘价或卖一价
            short_best_price = self.bar.open_price  # (做空好情况的限价)开盘价或买一价
        else:
            long_cross_price = self.tick.ask_price_1
            short_cross_price = self.tick.bid_price_1
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        for order in list(self.active_limit_orders.values()):
            # 当委托单为全部提交中时(刚提交委托时),把委托单的状态设为未成交状态
            if order.status == Status.SUBMITTING:
                order.status = Status.NOTTRADED
                self.strategy.on_order(order)

            # 检查限价单是否能被触发
            # 1、构建做多的满足的条件
            long_cross = (
                order.direction == Direction.LONG
                and order.price >= long_cross_price
                and (long_cross_price > 0)  # 有错误的K线价格为0时
            )
            # 2、构建做空的满足的条件
            short_cross = (
                order.direction == Direction.SHORT
                and order.price <= short_cross_price
                and short_cross_price > 0  # 有错误的K线价格为0时
            )

            if not long_cross and not short_cross:  # 如果空多条件都不满足时
                continue

            # 推送更新委托单到策略中
            order.traded = order.volume
            order.status = Status.ALLTRADED
            self.strategy.on_order(order)

            self.active_limit_orders.pop(order.vt_orderid)

            # 推送更行成交单到策略中
            self.trade_count += 1

            if long_cross:
                trade_price = min(order.price, long_best_price)  # 做多就是在委托价和"开盘价或卖一价中"取最小值
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)  # 做多就是在委托价和"开盘价或买一价中"取最大值
                pos_change = -order.volume

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
                order_ref=order.order_ref,
            )

            trade.datetime = self.datetime

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)  # 调用策略的on_trade函数

            self.trades[trade.vt_tradeid] = trade
            self.dt_trades_map[trade.datetime].append(trade)

    def cross_stop_order(self):
        """
        撮合本地停止单(条件单)委托。
            当最新的行情K线或者TICK到来时,和策略之前下达的所有委托进行检查，如果能够撮合成交，则返回并记录数据
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.high_price
            short_cross_price = self.bar.low_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.last_price
            short_cross_price = self.tick.last_price
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        for stop_order in list(self.active_stop_orders.values()):
            # 检查停止单是否能被触发
            long_cross = (
                stop_order.direction == Direction.LONG
                and stop_order.price <= long_cross_price
            )

            short_cross = (
                stop_order.direction == Direction.SHORT
                and stop_order.price >= short_cross_price
            )

            if not long_cross and not short_cross:
                continue

            # 创建订单数据
            self.limit_order_count += 1

            order = OrderData(
                symbol=self.symbol,
                exchange=self.exchange,
                orderid=str(self.limit_order_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=stop_order.price,
                volume=stop_order.volume,
                traded=stop_order.volume,
                status=Status.ALLTRADED,
                gateway_name=self.gateway_name,
                order_ref=stop_order.order_ref,
            )
            order.datetime = self.datetime

            self.limit_orders[order.vt_orderid] = order

            # 创建成交单数据
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -order.volume

            self.trade_count += 1

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
                order_ref=order.order_ref,
            )
            trade.datetime = self.datetime

            self.trades[trade.vt_tradeid] = trade
            self.dt_trades_map[trade.datetime].append(trade)

            # 更新停止委托单
            stop_order.vt_orderids.append(order.vt_orderid)
            stop_order.status = StopOrderStatus.TRIGGERED

            if stop_order.stop_orderid in self.active_stop_orders:
                self.active_stop_orders.pop(stop_order.stop_orderid)

            # 推送更新到策略。
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(order)

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

    def load_bar(
        self,
        vt_symbol: str,
        days: int,
        interval: Interval,
        callback: Callable,
        use_database: bool
    ):
        """
        策略文件中会调用此方法
        """
        self.days = days  # 指定多少天
        self.callback = callback  # 指定回调函数(默认为on_bar())

    def load_tick(self, vt_symbol: str, days: int, callback: Callable):
        """"""
        self.days = days
        self.callback = callback

    def send_order(
        self,
        strategy: CtaTemplate,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool,
        lock: bool,
        order_ref
    ):
        """"""
        price = round_to(price, self.pricetick)
        if not order_ref:
            order_ref = get_order_ref_value()
        if stop:
            vt_orderid = self.send_stop_order(direction, offset, price, volume, order_ref)
        else:
            vt_orderid = self.send_limit_order(direction, offset, price, volume, order_ref)
        return [vt_orderid]

    def send_stop_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        order_ref: str
    ):
        """"""
        self.stop_order_count += 1

        stop_order = StopOrder(
            vt_symbol=self.vt_symbol,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            stop_orderid=f"{STOPORDER_PREFIX}.{self.stop_order_count}",
            strategy_name=self.strategy.strategy_name,
            order_ref=order_ref,
        )

        self.active_stop_orders[stop_order.stop_orderid] = stop_order
        self.stop_orders[stop_order.stop_orderid] = stop_order

        return stop_order.stop_orderid

    def send_limit_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        order_ref: str,
    ):
        """"""
        self.limit_order_count += 1

        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=str(self.limit_order_count),
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            gateway_name=self.gateway_name,
            order_ref=order_ref,
        )
        order.datetime = self.datetime

        self.active_limit_orders[order.vt_orderid] = order
        self.limit_orders[order.vt_orderid] = order

        return order.vt_orderid

    def cancel_order(self, strategy: CtaTemplate, vt_orderid: str):
        """
        Cancel order by vt_orderid.
        """
        if vt_orderid.startswith(STOPORDER_PREFIX):
            self.cancel_stop_order(strategy, vt_orderid)
        else:
            self.cancel_limit_order(strategy, vt_orderid)

    def cancel_stop_order(self, strategy: CtaTemplate, vt_orderid: str):
        """"""
        if vt_orderid not in self.active_stop_orders:
            return
        stop_order = self.active_stop_orders.pop(vt_orderid)

        stop_order.status = StopOrderStatus.CANCELLED
        self.strategy.on_stop_order(stop_order)

    def cancel_limit_order(self, strategy: CtaTemplate, vt_orderid: str):
        """"""
        if vt_orderid not in self.active_limit_orders:
            return
        order = self.active_limit_orders.pop(vt_orderid)

        order.status = Status.CANCELLED
        self.strategy.on_order(order)

    def cancel_all(self, strategy: CtaTemplate):
        """
        Cancel all orders, both limit and stop.
        """
        vt_orderids = list(self.active_limit_orders.keys())
        for vt_orderid in vt_orderids:
            self.cancel_limit_order(strategy, vt_orderid)

        stop_orderids = list(self.active_stop_orders.keys())
        for vt_orderid in stop_orderids:
            self.cancel_stop_order(strategy, vt_orderid)

    def write_log(self, msg: str, strategy: CtaTemplate = None):
        """
        Write log message.
        """
        msg = f"{self.datetime}\t{msg}"
        self.logs.append(msg)

    def send_email(self, msg: str, strategy: CtaTemplate = None):
        """
        发送邮件到默认收件人。(实盘用到,回测未用到,但策略文件中调用此方法,因此保留此方法但不做任何逻辑处理。)
        """
        pass

    def sync_strategy_data(self, strategy: CtaTemplate):
        """
        同步策略变量数据到json文件中(实盘用到,回测未用到,但策略文件中调用此方法,因此保留此方法但不做任何逻辑处理。)
        """
        pass

    def get_engine_type(self):
        """
        Return engine type.
        """
        return self.engine_type

    def get_pricetick(self, strategy: CtaTemplate):
        """
        Return contract pricetick data.
        """
        return self.pricetick

    def put_strategy_event(self, strategy: CtaTemplate):
        """
        通知界面更新策略相关参数的状态(实盘中需要,回测中未需要,但策略文件中调用此方法,因此保留此方法但不做任何逻辑处理。)
        """
        pass

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

    def get_all_trades(self):
        """
        Return all trade data of current backtesting result.
        """
        return list(self.trades.values())

    def get_all_dt_trades_map(self):
        return self.dt_trades_map

    def get_all_orders(self):
        """
        Return all limit order data of current backtesting result.
        """
        return list(self.limit_orders.values())

    def get_all_daily_results(self):
        """
        返回所有每日盈亏结果数据
        """
        return list(self.daily_results.values())


class DailyResult:
    """"""

    def __init__(self, date: date, close_price: float):
        """"""
        self.date = date
        self.close_price = close_price
        self.pre_close = 0

        self.trades = []
        self.trade_count = 0  # 成交笔数

        self.start_pos = 0  # 开盘持仓量
        self.end_pos = 0  # 收盘持仓量

        self.turnover = 0  # 成交额
        self.commission = 0  # 保证金
        self.slippage = 0  # 交易滑点

        self.trading_pnl = 0  # 交易盈亏
        self.holding_pnl = 0  # 持仓盈亏
        self.total_pnl = 0  # 总盈亏
        self.net_pnl = 0  # 净盈亏

    def add_trade(self, trade: TradeData):
        """"""
        self.trades.append(trade)

    def calculate_pnl(
        self,
        pre_close: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float,
        inverse: bool
    ):
        """"""
        # 如果第一天没有提供pre_close，使用1来避免零除法错误。
        if pre_close:
            self.pre_close = pre_close
        else:
            self.pre_close = 1

        # 计算持仓盈亏
        self.start_pos = start_pos
        self.end_pos = start_pos

        if not inverse:     # 正向合约(正向合约inverse=False)
            self.holding_pnl = self.start_pos * \
                (self.close_price - self.pre_close) * size
        else:
            self.holding_pnl = self.start_pos * \
                (1 / self.pre_close - 1 / self.close_price) * size

        self.trade_count = len(self.trades)  # 交易笔数

        # 计算交易盈亏
        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
            else:
                pos_change = -trade.volume

            self.end_pos += pos_change

            # 正向合约
            if not inverse:
                turnover = trade.volume * size * trade.price   # 成交额
                self.trading_pnl += pos_change * \
                    (self.close_price - trade.price) * size
                self.slippage += trade.volume * size * slippage
            else:
                turnover = trade.volume * size / trade.price
                self.trading_pnl += pos_change * \
                    (1 / trade.price - 1 / self.close_price) * size
                self.slippage += trade.volume * size * slippage / (trade.price ** 2)

            self.turnover += turnover
            self.commission += turnover * rate

        # 计算总盈亏和净盈亏
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage


@lru_cache(maxsize=999)
def load_bar_data(
    symbol: str,
    exchange: Exchange,
    interval: Interval,
    start: datetime,
    end: datetime
):
    """"""
    return database_manager.load_bar_data(
        symbol, exchange, interval, start, end
    )


@lru_cache(maxsize=999)
def load_tick_data(
    symbol: str,
    exchange: Exchange,
    start: datetime,
    end: datetime
):
    """"""
    return database_manager.load_tick_data(
        symbol, exchange, start, end
    )


# GA related global value
ga_end = None
ga_mode = None
ga_target_name = None
ga_strategy_class = None
ga_setting = None
ga_vt_symbol = None
ga_interval = None
ga_start = None
ga_rate = None
ga_slippage = None
ga_size = None
ga_pricetick = None
ga_capital = None
