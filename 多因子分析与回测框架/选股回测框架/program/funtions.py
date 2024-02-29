import pandas as pd
import datetime
from decimal import Decimal, ROUND_HALF_UP
from numpy import abs
import numpy as np
import seaborn as sns
from numpy import log
from numpy import sign
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pyecharts import options as opts
from pyecharts.charts import Line
from ast import literal_eval
import itertools

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行

# 显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def resample_pct_chg(x):
    result = []
    for i in x:
        if pd.isna(i) == True:
            i = 1
        else:
            i = i + 1
        result.append(i)
    result = round(np.prod(result) - 1, 4)
    return result


# 调仓周期固定的天数确定
def remove_date(trade_date_data, begin_date, gaps=2):
    df = trade_date_data[trade_date_data['Date'] >= begin_date]
    df.reset_index(drop=True, inplace=True)
    df = df[df.index % gaps == 0]
    df.reset_index(drop=True, inplace=True)
    return df


# 转换资金曲线
def pct_chg_to_equity(x):
    array = np.array(x)
    array1 = (array + 1).cumprod()
    return array1.tolist()


def handle_equity(x, period_type):
    result = []
    if type(x) is list:
        return x
    else:
        for i in range(0, period_type):
            result.append(1)
    return result


def handle_pct_chg(x, period_type):
    result = []
    if type(x) is list:
        return x
    else:
        for i in range(0, period_type):
            result.append(0)
    return result


def adjust_periods(x, period_type):
    if type(x) is list:
        return x[:period_type]
    else:
        return []


def handle_read_csv(x):
    result = []
    if type(x) is str:
        x = x[1:-1].split(',')
        result = list(map(float, x))
        return result
    else:
        return x


# 将日线数据转换为其他周期的数据
def transfer_to_period_data(df, period_type="w", is_IC=False, extra_agg_dict={}):
    """
    将日线数据转换为相应的周期数据
    :param df:
    :param period_type:
    :return:
    """
    # 将交易日期设置为index
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['period_last_trade_day'] = df['Date']
    df.set_index('Date', inplace=True)

    agg_dict = {
        # 必须列
        'period_last_trade_day': 'last',
        'Ticker': 'last',
        'is_trade': 'last',
        'display_name': 'last',
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Value': 'sum',
        'Volume': 'sum',
    }
    if is_IC:
        pass
    else:
        agg_dict['tom_istrade'] = 'last'
        agg_dict['next_day_open_lim_up'] = 'last'
        agg_dict['tom_open_chg'] = 'last'

    agg_dict = dict(agg_dict, **extra_agg_dict)
    period_df = df.resample(rule=period_type).agg(agg_dict)

    # 计算必须额外数据
    period_df['trade_days'] = df['is_trade'].resample(period_type).sum()
    period_df['market_trade_days'] = df['Ticker'].resample(period_type).size()
    period_df = period_df[period_df['market_trade_days'] > 0]  # 有的时候整个周期不交易（例如春节、国庆假期），需要将这一周期删除

    # 计算其他因子
    # 计算周期资金曲线
    period_df['pct_chg'] = df['pct_chg'].resample(period_type).apply(lambda x: (x + 1).prod() - 1)
    if is_IC:
        period_df['pct_chg_5'] = round(100 * period_df['pct_chg'].shift(-1), 2)
        del period_df['pct_chg']
    else:
        # 计算周期资金曲线
        period_df['every_days_chg'] = df['pct_chg'].resample(period_type).apply(lambda x: list(x))
    # 重新设定index
    period_df.reset_index(inplace=True)
    period_df['Date'] = period_df['period_last_trade_day']
    del period_df['period_last_trade_day']
    period_df['Date'] = period_df['Date'].astype("str")
    return period_df


# 将股票数据和指数数据合并
def merge_with_index_data(df, index_data, extra_fill_0_list=[]):
    """
    原始股票数据在不交易的时候没有数据。
    将原始股票数据和指数数据合并，可以补全原始股票数据没有交易的日期。
    :param df: 股票数据
    :param index_data: 指数数据
    :return:
    """
    # ===将股票数据和上证指数合并，结果已经排序
    df = pd.merge(left=df, right=index_data, on='Date', how='right', sort=True, indicator=True)

    # ===对开、高、收、低、前收盘价价格进行补全处理
    # 用前一天的收盘价，补全收盘价的空值
    df['Close'].fillna(method='ffill', inplace=True)
    # 用收盘价补全开盘价、最高价、最低价的空值
    df['Open'].fillna(value=df['Close'], inplace=True)
    df['High'].fillna(value=df['Close'], inplace=True)
    df['Low'].fillna(value=df['Close'], inplace=True)

    # ===将停盘时间的某些列，数据填补为0
    fill_0_list = ['Volume', 'Value', 'pct_chg', 'open_chg'] + extra_fill_0_list
    df.loc[:, fill_0_list] = df[fill_0_list].fillna(value=0)

    # ===用前一天的数据，补全其余空值
    df.fillna(method='ffill', inplace=True)

    # ===去除上市之前的数据
    df = df[df['Ticker'].notnull()]

    # ===判断计算当天是否交易
    df['is_trade'] = 1
    df.loc[df['_merge'] == 'right_only', 'is_trade'] = 0
    del df['_merge']

    df.reset_index(drop=True, inplace=True)

    return df


# 计算是涨停
def cal_if_zhangting_with_st(df):
    """
    计算股票当天的涨跌停价格。在计算涨跌停价格的时候，按照严格的四舍五入。
    包含st股，但是不包含新股

    :param df: 必须得是日线数据。必须包含的字段：前收盘价，开盘价，最高价，最低价
    :return:
    """
    # 计算涨停价格
    df['lim_up'] = df['Close'].shift(1) * 1.1
    # 四舍五入
    df['lim_up'] = df['lim_up'].apply(
        lambda x: float(Decimal(x * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 100))
    # 判断是否一字涨停
    df['one_lim_up'] = False
    df.loc[((df['Low'] == df['High']) & (df['Low'] > df['Close'].shift(1))), 'one_lim_up'] = True
    # 判断是否开盘涨停
    df['open_lim_up'] = False
    df.loc[df['Open'] >= df['lim_up'], 'open_lim_up'] = True
    return df


# 获取回测所需数据，
def get_backtest_data(all_trade_df, all_factor_data, is_trade_date):
    final_data = pd.DataFrame()
    period_type = 35
    for code in all_trade_df['Ticker'].unique().tolist():
        print(code)
        trade_df = all_trade_df[all_trade_df['Ticker'] == code]
        trade_df.sort_values('Date', inplace=True)
        trade_df['Date'] = trade_df['Date'].astype('str')

        # 因子数据
        factor_df = all_factor_data[all_factor_data['Ticker'] == code]
        factor_df.sort_values('Date', inplace=True)

        trade_df['pct_chg'] = trade_df['Close'] / trade_df['Close'].shift() - 1
        trade_df['open_chg'] = trade_df['Close'] / trade_df['Open'] - 1  # 为之后开盘买入做好准备

        # 数据融合
        df = pd.merge(trade_df, factor_df, on=['Date', 'Ticker'], how='left')
        df.fillna(method='ffill', inplace=True)

        # 将数据与指数合并，补全数据
        df = merge_with_index_data(df, is_trade_date)

        df['open_lim_up'] = np.where(df['Open'] == df['high_limit'], True, False)

        # 计算每天未来N日的涨跌幅（包含当天）
        df['next_pct_chg'] = df['pct_chg'].shift(-period_type + 1)
        roll = df['next_pct_chg'].rolling(window=period_type, min_periods=1)
        df[f'future_Ndays_chg'] = [window.to_list() for window in roll]

        # 把第一天的涨跌幅改成开盘买入涨跌幅
        df['open_chg'] = df['open_chg'].apply(lambda x: [x])
        df[f'future_Ndays_chg'] = df[f'future_Ndays_chg'].apply(lambda x: x[1:])
        df[f'future_Ndays_chg'] = df['open_chg'] + df[f'future_Ndays_chg']

        # =计算下个交易的相关情况
        df['tom_istrade'] = df['is_trade'].shift(-1)
        df['next_day_open_lim_up'] = df['open_lim_up'].shift(-1)
        df['tom_open_chg'] = df['open_chg'].shift(-1)
        df[f'future_Ndays_chg'] = df[f'future_Ndays_chg'].shift(-1)

        # =对数据进行整理
        # 删除上市的第一个周期
        df.drop([0], axis=0, inplace=True)  # 删除第一行数据
        # 筛选时间
        # 删除月末不交易的周期数
        df = df[df['is_trade'] == 1]

        df.drop_duplicates(subset=['Date', 'Ticker'], keep='first', inplace=True)
        final_data = final_data.append(df)

    return final_data


# 获取回测的的资金曲线以及选股记录,过滤条件从外面做
def get_backtest_equity_and_select_stock_data(final_data, is_trade_date, index_alldata, params_dict):
    period_type = params_dict["period_type"]
    fangxiang = params_dict["fangxiang"]
    c_rate = params_dict["c_rate"]
    t_rate = params_dict["t_rate"]
    rank = params_dict["rank"]
    num = params_dict["num"]
    begin_date = params_dict["begin_date"]

    df = final_data.copy()

    # 如果是从CSV文件读取出来的总数据文件,要经过以下处理
    df['open_chg'] = df['open_chg'].apply(lambda x: handle_read_csv(x))
    df['future_Ndays_chg'] = df['future_Ndays_chg'].apply(lambda x: handle_read_csv(x))
    df['tom_open_chg'] = df['tom_open_chg'].apply(lambda x: handle_read_csv(x))

    df.sort_values(['Date', 'Ticker'], ascending=False, inplace=True)

    df[f'future_{period_type}days_chg'] = df['future_Ndays_chg'].apply(lambda x: adjust_periods(x, period_type))

    # 因子是越大越好进行绘制
    if fangxiang == "short":
        c_rate = -1 * c_rate  # 手续费
        t_rate = -1 * t_rate  # 印花税
        is_back = True
    elif fangxiang == "long":
        is_back = False
    else:
        return 0

    # ===删除下个交易日不交易、开盘涨停的股票，因为这些股票在下个交易日开盘时不能买入。
    df = df[df['tom_istrade'] == 1]
    df = df[df['next_day_open_lim_up'] == False]

    """添加过滤条件"""
    # df = df[df['my_factor']<=-0.020]

    n_ticker = rank
    n_ticker1 = rank + num

    df['rank'] = df.groupby('Date')['my_factor'].rank(ascending=is_back, method='first')
    df = df[(df['rank'] > n_ticker) & (df['rank'] <= n_ticker1)]

    df.sort_values('rank', inplace=True)

    # ===整理选中股票数据
    # 挑选出选中股票
    df['Ticker'] += ' '
    group = df.groupby('Date')
    select_stock = pd.DataFrame()
    select_stock['buy_Ticker'] = group['Ticker'].sum()
    # select_stock['buy_Ticker_name'] = group['display_name'].sum()
    select_stock['Ticker_number'] = group['Ticker'].size()

    remove_df = remove_date(is_trade_date, begin_date, gaps=period_type)

    # select_stock
    # 计算下周期每天的涨跌幅
    select_stock['ticker_next_everday_chg'] = group[f'future_{period_type}days_chg'].apply(
        lambda x: (np.array(x.tolist())).mean(axis=0))

    select_stock['ticker_next_everday_equity'] = select_stock['ticker_next_everday_chg'].apply(pct_chg_to_equity)
    # 扣除买入手续费
    select_stock['ticker_next_everday_equity'] = select_stock['ticker_next_everday_equity'].apply(
        lambda x: np.array(x) * (1 - c_rate))

    # 扣除卖出手续费
    select_stock['ticker_next_everday_equity'] = select_stock['ticker_next_everday_equity'].apply(
        lambda x: list(x[:-1]) + [x[-1] * (1 - c_rate - t_rate)])
    # 计算下周期每天的涨跌幅
    select_stock['ticker_next_everday_chg'] = select_stock['ticker_next_everday_equity'].apply(
        lambda x: list(pd.DataFrame([1] + x).pct_change()[0].iloc[1:]))

    select_stock = pd.merge(left=remove_df, right=select_stock, on='Date', how='left')

    select_stock['buy_Ticker'].fillna('000000', inplace=True)
    select_stock['Ticker_number'].fillna(0, inplace=True)
    select_stock['ticker_next_everday_equity'].fillna(0, inplace=True)
    select_stock['ticker_next_everday_chg'].fillna(0, inplace=True)

    # 计算下周期整体涨跌幅
    select_stock['ticker_next_everday_equity'] = select_stock['ticker_next_everday_equity'].apply(
        lambda x: handle_equity(x, period_type))

    select_stock['ticker_next_everday_chg'] = select_stock['ticker_next_everday_chg'].apply(
        lambda x: handle_pct_chg(x, period_type))

    select_stock['ticker_next_chg'] = select_stock['ticker_next_everday_equity'].apply(lambda x: x[-1] - 1)

    # 计算整体资金曲线
    select_stock.reset_index(inplace=True)
    select_stock['price'] = (select_stock['ticker_next_chg'] + 1).cumprod()

    del select_stock['ticker_next_everday_equity']

    # 指数全部数据
    index_alldata['Date'] = index_alldata['Date'].astype(str)

    equity = pd.merge(left=index_alldata, right=select_stock[['Date', 'buy_Ticker']], on=['Date'], how='left',
                      sort=True)  # 将选股结果和大盘指数合并
    equity['hold_Ticker'] = equity['buy_Ticker'].shift()
    equity['hold_Ticker'].fillna(method='ffill', inplace=True)
    equity.dropna(subset=['hold_Ticker'], inplace=True)
    equity.reset_index(drop=True, inplace=True)
    del equity['buy_Ticker']

    check_point_index = select_stock[select_stock['ticker_next_everday_chg'].notnull()].index
    first_eq_index = equity.index.tolist()[0]

    for index in check_point_index:
        li = select_stock.loc[index, 'ticker_next_everday_chg']
        if len(li) > period_type:
            li = li[:period_type]
        # 获取涨跌幅数组
        for i in range(0, len(li)):
            equity.loc[first_eq_index, 'pct_chg'] = li[i]
            first_eq_index = first_eq_index + 1

    equity['pct_chg'].fillna(value=0, inplace=True)
    # equity['pct_chg'] = equity['pct_chg']*-1
    equity['equity_curve'] = (equity['pct_chg'] + 1).cumprod()
    equity['benchmark'] = (equity['index_pct_chg'] + 1).cumprod()
    equity.dropna(inplace=True)

    return select_stock, equity


# 作图
def draw_captial_curve(equity):
    line1 = Line()
    # x铀
    line1.add_xaxis(equity.Date.to_list())
    # 每个y轴
    line1.add_yaxis('策略净值曲线', equity.equity_curve.round(3).to_list(), yaxis_index=0,
                    label_opts=opts.LabelOpts(is_show=False),
                    )
    line1.add_yaxis('对照指数', equity.benchmark.round(3).round(3).to_list(), yaxis_index=0,
                    label_opts=opts.LabelOpts(is_show=False),
                    )

    # 图表配置
    line1.set_global_opts(
        title_opts=opts.TitleOpts(title='equity_curve VS benchmark'),
        yaxis_opts=opts.AxisOpts(
            min_='dataMin'
        ),
        tooltip_opts=opts.TooltipOpts(trigger='axis', axis_pointer_type='cross'),
        datazoom_opts=[opts.DataZoomOpts(pos_bottom="-2%")],
    )
    return line1


# 计算策略评价指标
def strategy_evaluate(equity_data, select_stock_data):
    """
    :param equity:  每天的资金曲线
    :param select_stock: 每周期选出的股票
    :return:
    """
    equity = equity_data.copy()
    select_stock = select_stock_data.copy()

    # ===新建一个dataframe保存回测指标
    results = pd.DataFrame()

    # ===计算累积净值
    results.loc[0, '累积净值'] = round(equity['equity_curve'].iloc[-1], 2)

    equity['Date'] = pd.to_datetime(equity['Date'], format='%Y-%m-%d')

    # ===计算年化收益
    # ===计算年化收益
    annual_return = (equity['equity_curve'].iloc[-1]) ** (
            '1 days 00:00:00' / (equity['Date'].iloc[-1] - equity['Date'].iloc[0]) * 365) - 1
    results.loc[0, '年化收益'] = str(round(annual_return * 100, 2)) + '%'

    # 计算当日之前的资金曲线的最高点
    equity['max2here'] = equity['equity_curve'].expanding().max()
    # 计算到历史最高值到当日的跌幅，drowdwon
    equity['dd2here'] = equity['equity_curve'] / equity['max2here'] - 1
    # 计算最大回撤，以及最大回撤结束时间
    end_date, max_draw_down = tuple(equity.sort_values(by=['dd2here']).iloc[0][['Date', 'dd2here']])
    # 计算最大回撤开始时间
    start_date = equity[equity['Date'] <= end_date].sort_values(by='equity_curve', ascending=False).iloc[0]['Date']
    # 将无关的变量删除
    equity.drop(['max2here', 'dd2here'], axis=1, inplace=True)
    results.loc[0, '最大回撤'] = format(max_draw_down, '.2%')
    results.loc[0, '最大回撤开始时间'] = str(start_date)
    results.loc[0, '最大回撤结束时间'] = str(end_date)

    # ===年化收益/回撤比：我个人比较关注的一个指标
    results.loc[0, '年化收益/回撤比'] = round(annual_return / abs(max_draw_down), 2)

    # ===统计每个周期
    results.loc[0, '盈利周期数'] = len(select_stock.loc[select_stock['ticker_next_chg'] > 0])  # 盈利笔数
    results.loc[0, '亏损周期数'] = len(select_stock.loc[select_stock['ticker_next_chg'] <= 0])  # 亏损笔数
    results.loc[0, '胜率'] = format(results.loc[0, '盈利周期数'] / len(select_stock), '.2%')  # 胜率
    results.loc[0, '每周期平均收益'] = format(select_stock['ticker_next_chg'].mean(), '.2%')  # 每笔交易平均盈亏
    results.loc[0, '盈亏收益比'] = round(select_stock.loc[select_stock['ticker_next_chg'] > 0]['ticker_next_chg'].mean() / \
                                    select_stock.loc[select_stock['ticker_next_chg'] <= 0]['ticker_next_chg'].mean() * (
                                        -1), 2)  # 盈亏比
    results.loc[0, '单周期最大盈利'] = format(select_stock['ticker_next_chg'].max(), '.2%')  # 单笔最大盈利
    results.loc[0, '单周期大亏损'] = format(select_stock['ticker_next_chg'].min(), '.2%')  # 单笔最大亏损

    # ===连续盈利亏损
    results.loc[0, '最大连续盈利周期数'] = max([len(list(v)) for k, v in itertools.groupby(
        np.where(select_stock['ticker_next_chg'] > 0, 1, np.nan))])  # 最大连续盈利次数

    results.loc[0, '最大连续亏损周期数'] = max([len(list(v)) for k, v in itertools.groupby(
        np.where(select_stock['ticker_next_chg'] <= 0, 1, np.nan))])  # 最大连续亏损次数

    # ===每年、每月收益率
    equity.set_index('Date', inplace=True)
    year_return = equity[['pct_chg']].resample(rule='A').apply(lambda x: (1 + x).prod() - 1)
    monthly_return = equity[['pct_chg']].resample(rule='M').apply(lambda x: (1 + x).prod() - 1)

    return results.T, year_return, monthly_return


if __name__ == '__main__':
    pass
