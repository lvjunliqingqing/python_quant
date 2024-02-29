import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pandas import Series

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def evaluate_investment(source_data, tittle="累积净值", time_label='交易日期', equity_change="equity_change", risk_free: float = 2, annual_days=250):  # 评价策略
    """
    :param source_data: 策略交易数据
    :param tittle: 净值列名
    :param time_label: 交易日期列名
    :param equity_change: 策略盈亏幅度
    :param risk_free: 无风险年利率
    :param annual_days: 一年有多少个交易日
    """

    temp = source_data.copy()
    results = pd.DataFrame()  # 用于保存回测统计指标的df

    # 计算年化收益
    annual_return = (temp[tittle].iloc[-1]) ** ('1 days 00:00:00' / (temp[time_label].iloc[-1] - temp[time_label].iloc[0]) * 365) - 1
    # print(temp[time_label].iloc[-1] - temp[time_label].iloc[0])
    # 计算当日之前的资金曲线的最高点
    temp['highlevel'] = temp[tittle].expanding().max()
    # 计算到历史最高值到当日的跌幅(当日回撤率)
    temp['drowdwon'] = temp[tittle] / temp['highlevel'] - 1
    # 计算最大回撤，以及最大回撤结束时间
    end_date, max_draw_down = tuple(temp.sort_values(by=['drowdwon']).iloc[0][[time_label, 'drowdwon']])
    # 计算最大回撤开始时间
    start_date = temp[temp[time_label] <= end_date].sort_values(by=tittle, ascending=False).iloc[0][time_label]
    # 计算盈亏比
    profit_loss_ratio = abs(temp[temp[equity_change] > 0][equity_change].sum() / temp[temp[equity_change] < 0][equity_change].sum())

    # 将无关的变量删除
    temp.drop(['highlevel', 'drowdwon'], axis=1, inplace=True)

    # 计算累积净值
    results.loc[0, '累积净值'] = round(temp[tittle].iloc[-1], 2)
    results.loc[0, '最大回撤'] = format(max_draw_down, '.2%')
    results.loc[0, '最大回撤开始时间'] = str(start_date)
    results.loc[0, '最大回撤结束时间'] = str(end_date)
    results.loc[0, '年化收益'] = str(round(annual_return * 100, 2)) + '%'
    results.loc[0, '年化收益/回撤比'] = round(annual_return / abs(max_draw_down), 2)
    results.loc[0, '胜率'] = round(temp[temp[equity_change] > 0].shape[0] / temp.shape[0], 2)
    results.loc[0, '夏普比率'] = cal_sharpe_ratio(temp[equity_change], risk_free=risk_free, annual_days=annual_days)
    results.loc[0, '盈亏比'] = round(profit_loss_ratio, 2)

    return results.T


def cal_sharpe_ratio(series: Series, risk_free: float = 2, annual_days=250):
    """
    计算夏普比率
    :param series:收益率那一列
    :param risk_free: 无风险年利率
    :param annual_days: 年交易天数(一年有250个交易日)
    """
    daily_return = series.mean() * 100  # 日均收益率
    return_std = series.std() * 100  # 收益标准差
    if return_std:
        daily_risk_free = risk_free / annual_days
        # daily_risk_free = risk_free / np.sqrt(annual_days)  # 同时把risk_free 设为0.02  vnpy中是这种计算公式, 这种计算公式是错误的。
        # 夏普比率 = (日均收益率 - 日无风险率) / 收益标准差 * 年利率换算系数(年交易天数开根号)
        sharpe_ratio = (daily_return - daily_risk_free) / return_std * np.sqrt(annual_days)  # 标准差是方差的算数平方根,所以 年收益标准差 转换 日收益标准差 时,只需除以250的平方根。
        sharpe_ratio = round(sharpe_ratio, 2)
    else:
        sharpe_ratio = 0
    return sharpe_ratio
