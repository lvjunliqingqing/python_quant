
import multiprocessing
import platform
import random
import traceback
from collections import defaultdict
from copy import copy
from datetime import date, datetime, timedelta
from functools import lru_cache
from itertools import product
from time import time
from typing import Dict, List, Set, Tuple

import numpy as np
import plotly.graph_objects as go
from deap import algorithms, base, tools, creator
from pandas import DataFrame
from plotly.subplots import make_subplots

from vnpy.trader.constant import Direction, Offset, Interval, Status
from vnpy.trader.database import database_manager
from vnpy.trader.object import OrderData, TradeData, BarData
from vnpy.trader.symbol_attr import ContractMultiplier
from vnpy.trader.utility import round_to, extract_vt_symbol, get_letter_from_symbol
from .base import BacktestingMode
from .template import StrategyTemplate

INTERVAL_DELTA_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta(days=1),
}

class OptimizationSetting:
    """
    Setting for runnning optimization.
    """

    def __init__(self):
        """"""
        self.params = {}
        self.target_name = ""

    def add_parameter(
        self, name: str, start: float, end: float = None, step: float = None
    ):
        """"""
        if not end and not step:
            self.params[name] = [start]
            return

        if start >= end:
            print("参数优化起始点必须小于终止点")
            return

        if step <= 0:
            print("参数优化步进必须大于0")
            return

        value = start
        value_list = []

        while value <= end:
            value_list.append(value)
            value += step

        self.params[name] = value_list

    def set_target(self, target_name: str):
        """"""
        self.target_name = target_name

    def generate_setting(self):
        """"""
        keys = self.params.keys()
        values = self.params.values()
        products = list(product(*values))

        settings = []
        for p in products:
            setting = dict(zip(keys, p))
            settings.append(setting)

        return settings

    def generate_setting_ga(self):
        """"""
        settings_ga = []
        settings = self.generate_setting()
        for d in settings:
            param = [tuple(i) for i in d.items()]
            settings_ga.append(param)
        return settings_ga


class BacktestingEngine:
    """"""

    gateway_name = "BACKTESTING"

    def __init__(self):
        """"""
        self.vt_symbols: List[str] = []
        self.start: datetime = None
        self.end: datetime = None

        self.rates: Dict[str, float] = 0
        self.slippages: Dict[str, float] = 0
        self.sizes: Dict[str, float] = 1
        self.priceticks: Dict[str, float] = 0

        self.capital: float = 1_000_000

        self.strategy: StrategyTemplate = None
        self.bars: Dict[str, BarData] = {}
        self.datetime: datetime = None
        self.vt_symbol = None
        self.interval: Interval = None
        self.strategy_class = None
        self.days: int = 0
        self.history_data: Dict[Tuple, BarData] = {}
        self.dts: Set[datetime] = set()

        self.limit_order_count = 0
        self.limit_orders = {}
        self.active_limit_orders = {}

        self.trade_count = 0
        self.trades = {}

        self.logs = []
        self.trades_record = []
        self.daily_results = {}
        self.daily_df = None
        self.inverse = False
        self.mode = BacktestingMode.BAR


    def clear_data(self) -> None:
        """
        Clear all data of last backtesting.
        """
        self.strategy = None
        self.bars = {}
        self.datetime = None

        self.limit_order_count = 0
        self.limit_orders.clear()
        self.active_limit_orders.clear()

        self.trade_count = 0
        self.trades.clear()

        self.logs.clear()
        self.daily_results.clear()
        self.daily_df = None

    def set_parameters(
        self,
        vt_symbols: List[str],
        interval: Interval,
        start: datetime,
        rates: Dict[str, float],
        slippages: Dict[str, float],
        sizes: Dict[str, float],
        priceticks: Dict[str, float],
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
        inverse: bool = False
    ) -> None:
        """"""
        self.vt_symbols = vt_symbols
        self.interval = interval
        self.inverse = inverse
        self.rates = rates
        self.slippages = slippages
        self.sizes = sizes
        self.priceticks = priceticks
        self.mode = mode
        self.start = start
        self.end = end
        self.capital = capital

    def add_strategy(self, strategy_class: type, setting: dict) -> None:
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, copy(self.vt_symbols), setting
        )

    def load_data(self) -> None:
        """"""
        self.output("开始加载历史数据")

        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            self.output("起始日期必须小于结束日期")
            return

        # Clear previously loaded history data
        self.history_data.clear()
        self.dts.clear()

        # Load 30 days of data each time and allow for progress update
        progress_delta = timedelta(days=30)
        total_delta = self.end - self.start
        interval_delta = INTERVAL_DELTA_MAP[self.interval]

        for vt_symbol in self.vt_symbols:
            start = self.start
            end = self.start + progress_delta
            progress = 0

            data_count = 0
            while start < self.end:
                end = min(end, self.end)  # Make sure end time stays within set range

                data = load_bar_data(
                    vt_symbol,
                    self.interval,
                    start,
                    end
                )

                for bar in data:
                    self.dts.add(bar.datetime)
                    self.history_data[(bar.datetime, vt_symbol)] = bar
                    data_count += 1

                progress += progress_delta / total_delta
                progress = min(progress, 1)
                progress_bar = "#" * int(progress * 10)
                self.output(f"{vt_symbol}加载进度：{progress_bar} [{progress:.0%}]")

                start = end + interval_delta
                end += (progress_delta + interval_delta)

            self.output(f"{vt_symbol}历史数据加载完成，数据量：{data_count}")

        self.output("所有历史数据加载完成")

    def run_backtesting(self) -> None:
        """"""
        self.strategy.on_init()

        # Generate sorted datetime list
        dts = list(self.dts)
        dts.sort()

        # Use the first [days] of history data for initializing strategy
        day_count = 0
        ix = 0

        for ix, dt in enumerate(dts):
            if self.datetime and dt.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break

            try:
                self.new_bars(dt)
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return

        self.strategy.inited = True
        self.output("策略初始化完成")

        self.strategy.on_start()
        self.strategy.trading = True
        self.output("开始回放历史数据")

        # Use the rest of history data for running backtesting
        for dt in dts[ix:]:
            try:
                self.new_bars(dt)
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return

        self.output("历史数据回放结束")

    def calculate_result(self) -> None:
        """"""
        self.output("开始计算逐日盯市盈亏")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            return

        # Add trade data into daily reuslt.
        for trade in self.trades.values():
            d = trade.datetime.date()
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)

        # Calculate daily result by iteration.
        pre_closes = {}
        start_poses = {}

        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_closes,
                start_poses,
                self.sizes,
                self.rates,
                self.slippages,
            )

            pre_closes = daily_result.close_prices
            start_poses = daily_result.end_poses

        # Generate dataframe
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            fields = [
                "date", "trade_count", "turnover",
                "commission", "slippage", "trading_pnl",
                "holding_pnl", "total_pnl", "net_pnl"
            ]
            for key in fields:
                value = getattr(daily_result, key)
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_statistics(self, df: DataFrame = None, output=True) -> None:
        """"""
        self.output("开始计算策略统计指标")

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
            winlist = []  # 存储止盈
            losslist = []  # 存储止损
            total_cost = 0  # 总成本
            for index, row in df.iterrows():
                for trade in row.get("trades", []):
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
                        total_cost += trade.price * trade.volume * ContractMultiplier[symbol_code]
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
            if total_cost:
                real_yields = f"{round(df['net_pnl'].sum() / total_cost, 3)}"
            else:  # 总成本无法计算时
                real_yields = f"无法统计总成本,则收益率无法计算"
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

        # Filter potential error infinite value
        for key, value in statistics.items():
            if value in (np.inf, -np.inf):
                value = 0
            statistics[key] = np.nan_to_num(value)

        self.output("策略统计指标计算完成")
        return statistics

    def show_chart(self, df: DataFrame = None) -> None:
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


    def run_optimization(self, optimization_setting: OptimizationSetting, output=True):
        """多进程优化"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        cpu_nums = multiprocessing.cpu_count()
        if platform.system() == 'Windows':
            cpu_nums = cpu_nums
        elif platform.system() == 'Linux':
            cpu_nums = cpu_nums - 2

        # Force to use spawn method to create new process (instead of fork on Linux)
        ctx = multiprocessing.get_context("spawn")
        pool = ctx.Pool(cpu_nums)

        results = []
        for setting in settings:
            result = (pool.apply_async(optimize, (
                target_name,
                self.strategy_class,
                setting,
                self.vt_symbols,
                self.interval,
                self.start,
                self.rates,
                self.slippages,
                self.sizes,
                self.priceticks,
                self.capital,
                self.end,
                self.mode,
                self.inverse
            )))
            results.append(result)

        pool.close()
        pool.join()

        # Sort results and output
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[1])

        if output:
            for value in result_values:
                msg = f"参数：{value[0]}, 目标：{value[1]}"
                self.output(msg)

        return result_values

    def run_ga_optimization(self, optimization_setting: OptimizationSetting, population_size=100, ngen_size=30, output=True):
        """遗传算法优化"""
        # 获得优化设置和目标
        settings = optimization_setting.generate_setting_ga()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Define parameter generation function
        def generate_parameter():
            """"""
            return random.choice(settings)

        def mutate_individual(individual, indpb):
            """"""
            size = len(individual)
            paramlist = generate_parameter()
            for i in range(size):
                if random.random() < indpb:
                    individual[i] = paramlist[i]
            return individual,

        # 声明下全局变量
        global ga_target_name
        global ga_strategy_class
        global ga_setting
        global ga_vt_symbol
        global ga_interval
        global ga_start
        global ga_rate
        global ga_slippage
        global ga_size
        global ga_pricetick
        global ga_capital
        global ga_end
        global ga_mode
        global ga_inverse

        ga_target_name = target_name
        ga_strategy_class = self.strategy_class
        ga_setting = settings[0]
        ga_vt_symbol = self.vt_symbols
        ga_interval = self.interval
        ga_start = self.start
        ga_rate = self.rates
        ga_slippage = self.slippages
        ga_size = self.sizes
        ga_pricetick = self.priceticks
        ga_capital = self.capital
        ga_end = self.end
        ga_mode = self.mode
        ga_inverse = self.inverse

        # Set up genetic algorithem
        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate, creator.Individual, generate_parameter)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", mutate_individual, indpb=1)
        toolbox.register("evaluate", ga_optimize)
        toolbox.register("select", tools.selNSGA2)

        total_size = len(settings)
        pop_size = population_size                      # number of individuals in each generation
        lambda_ = pop_size                              # number of children to produce at each generation
        mu = int(pop_size * 0.8)                        # number of individuals to select for the next generation

        cxpb = 0.95         # probability that an offspring is produced by crossover
        mutpb = 1 - cxpb    # probability that an offspring is produced by mutation
        ngen = ngen_size    # number of generation

        pop = toolbox.population(pop_size)
        hof = tools.ParetoFront()               # end result of pareto front

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        np.set_printoptions(suppress=True)
        stats.register("mean", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Multiprocessing is not supported yet.
        # pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # toolbox.register("map", pool.map)

        # Run ga optimization
        self.output(f"参数优化空间：{total_size}")
        self.output(f"每代族群总数：{pop_size}")
        self.output(f"优良筛选个数：{mu}")
        self.output(f"迭代次数：{ngen}")
        self.output(f"交叉概率：{cxpb:.0%}")
        self.output(f"突变概率：{mutpb:.0%}")

        start = time()

        algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu,
            lambda_,
            cxpb,
            mutpb,
            ngen,
            stats,
            halloffame=hof
        )

        end = time()
        cost = int((end - start))

        self.output(f"遗传算法优化完成，耗时{cost}秒")

        # Return result list
        results = []

        for parameter_values in hof:
            setting = dict(parameter_values)
            target_value = ga_optimize(parameter_values)[0]
            results.append((setting, target_value, {}))

        return results

    def update_daily_close(self, bars: Dict[str, BarData], dt: datetime) -> None:
        """"""
        d = dt.date()

        close_prices = {}
        for bar in bars.values():
            close_prices[bar.vt_symbol] = bar.close_price

        daily_result = self.daily_results.get(d, None)

        if daily_result:
            daily_result.update_close_prices(close_prices)
        else:
            self.daily_results[d] = PortfolioDailyResult(d, close_prices)

    def new_bars(self, dt: datetime) -> None:
        """"""
        self.datetime = dt

        # self.bars.clear()
        for vt_symbol in self.vt_symbols:
            bar = self.history_data.get((dt, vt_symbol), None)

            # If bar data of vt_symbol at dt exists
            if bar:
                self.bars[vt_symbol] = bar
            # Otherwise, use previous data to backfill
            elif vt_symbol in self.bars:
                old_bar = self.bars[vt_symbol]

                bar = BarData(
                    symbol=old_bar.symbol,
                    exchange=old_bar.exchange,
                    datetime=dt,
                    open_price=old_bar.close_price,
                    high_price=old_bar.close_price,
                    low_price=old_bar.close_price,
                    close_price=old_bar.close_price,
                    gateway_name=old_bar.gateway_name
                )
                self.bars[vt_symbol] = bar

        self.cross_limit_order()
        self.strategy.on_bars(self.bars)

        self.update_daily_close(self.bars, dt)

    def cross_limit_order(self) -> None:
        """
        Cross limit order with last bar/tick data.
        """
        for order in list(self.active_limit_orders.values()):
            bar = self.bars[order.vt_symbol]

            long_cross_price = bar.low_price
            short_cross_price = bar.high_price
            long_best_price = bar.open_price
            short_best_price = bar.open_price

            # Push order update with status "not traded" (pending).
            if order.status == Status.SUBMITTING:
                order.status = Status.NOTTRADED
                self.strategy.update_order(order)

            # Check whether limit orders can be filled.
            long_cross = (
                order.direction == Direction.LONG
                and order.price >= long_cross_price
                and long_cross_price > 0
            )

            short_cross = (
                order.direction == Direction.SHORT
                and order.price <= short_cross_price
                and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            # Push order update with status "all traded" (filled).
            order.traded = order.volume
            order.status = Status.ALLTRADED
            self.strategy.update_order(order)

            self.active_limit_orders.pop(order.vt_orderid)

            # Push trade update
            self.trade_count += 1

            if long_cross:
                trade_price = min(order.price, long_best_price)
            else:
                trade_price = max(order.price, short_best_price)

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                datetime=self.datetime,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )

            self.strategy.update_trade(trade)
            self.trades[trade.vt_tradeid] = trade

    def load_bars(
        self,
        strategy: StrategyTemplate,
        days: int,
        interval: Interval,
        use_database: bool = False
    ) -> None:
        """"""
        self.days = days

    def send_order(
        self,
        strategy: StrategyTemplate,
        vt_symbol: str,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        lock: bool,
        order_ref: str
    ) -> List[str]:
        """"""
        price = round_to(price, self.priceticks[vt_symbol])
        symbol, exchange = extract_vt_symbol(vt_symbol)

        self.limit_order_count += 1

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            orderid=str(self.limit_order_count),
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            datetime=self.datetime,
            gateway_name=self.gateway_name,
        )

        self.active_limit_orders[order.vt_orderid] = order
        self.limit_orders[order.vt_orderid] = order

        return [order.vt_orderid]

    def cancel_order(self, strategy: StrategyTemplate, vt_orderid: str) -> None:
        """
        Cancel order by vt_orderid.
        """
        if vt_orderid not in self.active_limit_orders:
            return
        order = self.active_limit_orders.pop(vt_orderid)

        order.status = Status.CANCELLED
        self.strategy.update_order(order)

    def write_log(self, msg: str, strategy: StrategyTemplate = None) -> None:
        """
        Write log message.
        """
        msg = f"{self.datetime}\t{msg}"
        self.logs.append(msg)

    def send_email(self, msg: str, strategy: StrategyTemplate = None) -> None:
        """
        Send email to default receiver.
        """
        pass

    def sync_strategy_data(self, strategy: StrategyTemplate) -> None:
        """
        Sync strategy data into json file.
        """
        pass

    def put_strategy_event(self, strategy: StrategyTemplate) -> None:
        """
        Put an event to update strategy status.
        """
        pass

    def output(self, msg) -> None:
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

    def get_all_trades(self) -> List[TradeData]:
        """
        Return all trade data of current backtesting result.
        """
        return list(self.trades.values())

    def get_all_orders(self) -> List[OrderData]:
        """
        Return all limit order data of current backtesting result.
        """
        return list(self.limit_orders.values())

    def get_all_daily_results(self) -> List["PortfolioDailyResult"]:
        """
        Return all daily result data.
        """
        return list(self.daily_results.values())

    def get_trades_record(self):
        """"""
        return self.trades_record

class ContractDailyResult:
    """"""

    def __init__(self, result_date: date, close_price: float):
        """"""
        self.date: date = result_date
        self.close_price: float = close_price
        self.pre_close: float = 0

        self.trades: List[TradeData] = []
        self.trade_count: int = 0

        self.start_pos: float = 0
        self.end_pos: float = 0

        self.turnover: float = 0
        self.commission: float = 0
        self.slippage: float = 0

        self.trading_pnl: float = 0
        self.holding_pnl: float = 0
        self.total_pnl: float = 0
        self.net_pnl: float = 0

    def add_trade(self, trade: TradeData) -> None:
        """"""
        self.trades.append(trade)

    def calculate_pnl(
        self,
        pre_close: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float
    ) -> None:
        """"""
        # If no pre_close provided on the first day,
        # use value 1 to avoid zero division error
        if pre_close:
            self.pre_close = pre_close
        else:
            self.pre_close = 1

        # Holding pnl is the pnl from holding position at day start
        self.start_pos = start_pos
        self.end_pos = start_pos

        self.holding_pnl = self.start_pos * (self.close_price - self.pre_close) * size

        # Trading pnl is the pnl from new trade during the day
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
            else:
                pos_change = -trade.volume

            self.end_pos += pos_change

            turnover = trade.volume * size * trade.price

            self.trading_pnl += pos_change * (self.close_price - trade.price) * size
            self.slippage += trade.volume * size * slippage
            self.turnover += turnover
            self.commission += turnover * rate

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage

    def update_close_price(self, close_price: float) -> None:
        """"""
        self.close_price = close_price


class PortfolioDailyResult:
    """"""

    def __init__(self, result_date: date, close_prices: Dict[str, float]):
        """"""
        self.date: date = result_date
        self.close_prices: Dict[str, float] = close_prices
        self.pre_closes: Dict[str, float] = {}
        self.start_poses: Dict[str, float] = {}
        self.end_poses: Dict[str, float] = {}

        self.contract_results: Dict[str, ContractDailyResult] = {}

        for vt_symbol, close_price in close_prices.items():
            self.contract_results[vt_symbol] = ContractDailyResult(result_date, close_price)

        self.trade_count: int = 0
        self.turnover: float = 0
        self.commission: float = 0
        self.slippage: float = 0
        self.trading_pnl: float = 0
        self.holding_pnl: float = 0
        self.total_pnl: float = 0
        self.net_pnl: float = 0

    def add_trade(self, trade: TradeData) -> None:
        """"""
        contract_result = self.contract_results[trade.vt_symbol]
        contract_result.add_trade(trade)

    def calculate_pnl(
        self,
        pre_closes: Dict[str, float],
        start_poses: Dict[str, float],
        sizes: Dict[str, float],
        rates: Dict[str, float],
        slippages: Dict[str, float],
    ) -> None:
        """"""
        self.pre_closes = pre_closes

        for vt_symbol, contract_result in self.contract_results.items():
            contract_result.calculate_pnl(
                pre_closes.get(vt_symbol, 0),
                start_poses.get(vt_symbol, 0),
                sizes[vt_symbol],
                rates[vt_symbol],
                slippages[vt_symbol]
            )

            self.trade_count += contract_result.trade_count
            self.turnover += contract_result.turnover
            self.commission += contract_result.commission
            self.slippage += contract_result.slippage
            self.trading_pnl += contract_result.trading_pnl
            self.holding_pnl += contract_result.holding_pnl
            self.total_pnl += contract_result.total_pnl
            self.net_pnl += contract_result.net_pnl

            self.end_poses[vt_symbol] = contract_result.end_pos

    def update_close_prices(self, close_prices: Dict[str, float]) -> None:
        """"""
        self.close_prices = close_prices

        for vt_symbol, close_price in close_prices.items():
            contract_result = self.contract_results.get(vt_symbol, None)
            if contract_result:
                contract_result.update_close_price(close_price)


@lru_cache(maxsize=999)
def load_bar_data(
    vt_symbol: str,
    interval: Interval,
    start: datetime,
    end: datetime
):
    """"""
    symbol, exchange = extract_vt_symbol(vt_symbol)

    return database_manager.load_bar_data(
        symbol, exchange, interval, start, end
    )


def optimize(
    target_name: str,
    strategy_class: StrategyTemplate,
    setting: dict,
    vt_symbol: list,
    interval: Interval,
    start: datetime,
    rate: dict,
    slippage: dict,
    size: dict,
    pricetick: dict,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    inverse: bool
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        vt_symbols=vt_symbol,
        interval=interval,
        start=start,
        rates=rate,
        slippages=slippage,
        sizes=size,
        priceticks=pricetick,
        capital=capital,
        end=end,
        mode=mode,
        inverse=inverse
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]

    return ("+".join(vt_symbol) + ' ' + str(setting), target_value, statistics)


@lru_cache(maxsize=1000000)
def _ga_optimize(parameter_values: tuple):
    """"""
    setting = dict(parameter_values)

    result = optimize(
        ga_target_name,
        ga_strategy_class,
        setting,
        ga_vt_symbol,
        ga_interval,
        ga_start,
        ga_rate,
        ga_slippage,
        ga_size,
        ga_pricetick,
        ga_capital,
        ga_end,
        ga_mode,
        ga_inverse
    )
    return (result[1],)


def ga_optimize(parameter_values: list):
    """"""
    return _ga_optimize(tuple(parameter_values))


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