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
from scipy import stats

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
    if begin_date is None:
        df = trade_date_data
    else:
        df = trade_date_data[trade_date_data['Date'] >= begin_date]
    df.reset_index(drop=True, inplace=True)
    df = df[df.index % gaps == 0]
    df.reset_index(drop=True, inplace=True)
    return df


# 将日线数据转换为其他周期的数据，这里只能固定的转换为 1d, 1w,1m，其他都不行
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
        # 'name': 'last',
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


# 可转换任意的周期函数，但因子合并只能是last
def wudi_transfer_every_period_data(all_trade_df, all_factor_data, is_trade_date, period_type, begin_date=None):
    # 固定间隔周期的因子IC分析
    final_data = pd.DataFrame()
    future_list = all_trade_df['Ticker'].unique().tolist()
    for code in future_list:
        # 行情数据
        trade_df = all_trade_df[all_trade_df['Ticker'] == code]
        # 因子数据
        factor_df = all_factor_data[all_factor_data['Ticker'] == code]
        factor_df.sort_values('Date', inplace=True)

        trade_df['pct_chg'] = trade_df['Close'] / trade_df['Close'].shift() - 1
        trade_df['open_chg'] = trade_df['Close'] / trade_df['Open'] - 1  # 为之后开盘买入做好准备

        # 数据融合
        df = pd.merge(trade_df, factor_df, on=['Date', 'Ticker'])
        # 将数据与指数合并，补全数据
        df = merge_with_index_data(df, is_trade_date)

        # 构建能转换周期的期货数据
        # 计算每天未来N日的涨跌幅（包含当天）
        df['pre_pct_chg'] = df['pct_chg']
        df.reset_index(drop=True, inplace=True)
        roll = df['pre_pct_chg'].rolling(window=period_type, min_periods=1)
        df[f'before_{period_type}days_chg'] = [window.to_list() for window in roll]
        df.dropna(inplace=True)
        df[f'{period_type}days_chg_fators'] = df[f'before_{period_type}days_chg'].apply(resample_pct_chg)

        remove_df = remove_date(is_trade_date, begin_date=begin_date, gaps=period_type)
        df = pd.merge(left=remove_df, right=df, on='Date', how='left')
        df['pct_chg_5'] = df[f'{period_type}days_chg_fators'].shift(-1)
        df['pct_chg_5'] = round(100 * df['pct_chg_5'], 2)
        df.dropna(inplace=True)
        # 那因子都是last
        factor_list = df.columns.values[10:-6]

        final_data = final_data.append(df)
    return factor_list, final_data


# 比较因子的相关性
def get_features_corr_data(ic_, corr_value=0.70):
    # 获得所有因子相关性表
    corr_df = ic_.corr(method='spearman')
    m = (corr_df.mask(np.eye(len(corr_df), dtype=bool)).abs() > corr_value).any()

    raw = corr_df.loc[m, m]  # 能看具体相关系数的值
    corr_dict = {}
    for col in raw.columns:
        corr_dict[col] = list(raw[abs(raw[col]) > corr_value].index)
    corr_df = pd.DataFrame.from_dict(corr_dict, orient='index')  # 关系表，没有值
    return raw, corr_df


# apply处理函数
def handlex(x):
    if type(x) == list and len(x) > 0:
        return x[1:]
    elif type(x) == str and len(x) > 0:
        x = literal_eval(x)
        return x[1:]
    else:
        return [0]


# 去极值，处理离群值，将超出变量特定百分位范围的数值替换为其特定百分位数值。
def winsor(x):
    if x.dropna().shape[0] != 0:
        x.loc[x < np.percentile(x.dropna(), 5)] = np.percentile(x.dropna(), 5)
        x.loc[x > np.percentile(x.dropna(), 95)] = np.percentile(x.dropna(), 95)
    else:
        x = x.fillna(0)
    return x


# MAD去极值
# 截尾,nan用行业平均代替
def mad_cut(x):
    diff = (x - x.median()).apply(abs)
    mad = diff.median()
    upper_limit = x.median() + 1.4826 * mad
    lower_limit = x.median() - 1.4826 * mad
    x.loc[x < lower_limit] = lower_limit * 3.0
    x.loc[x > upper_limit] = upper_limit * 3.0
    x.clip(lower_limit, upper_limit, inplace=True)
    return x


# 标准化
def standardize(x):
    return (x - x.mean()) / x.std()


# 中性化
def norm(data):
    data = data.copy()
    """
    数据预处理，标准化
    """
    # 判断有无缺失值，若有缺失值，drop，若都缺失，返回原值

    datax = data.copy()
    if data.shape[0] != 0:
        ## 去极值
        data = data.apply(lambda x: winsor(x), axis=0)

        ## zscore
        data1 = (data - data.mean()) / data.std()

        # 缺失部分补进去
        data1 = data1.reindex(datax.index)
    else:
        data1 = data
    return data1


"""
调用norm中性化所有因子
"""


def NormFactors(datas):
    # datas = factorall.copy()
    fnormall = []

    dates = datas.Date.unique()
    for dateuse in dates:  # dateuse = dates[0]
        datause = datas.loc[datas.Date == dateuse]

        stockname = datause[['Date', 'Ticker']]
        fnorm = norm(datause.drop(['Date', 'Ticker'], axis=1))
        fnormall.append(pd.concat([stockname, fnorm], axis=1))
    fnormall = pd.concat(fnormall, axis=0)
    fnormall = fnormall.sort_values(by=['Date', 'Ticker'])
    return fnormall.reset_index(drop=True)


# 中性化
def OlsResid(y, x):
    df = pd.concat([y, x], axis=1)

    if df.dropna().shape[0] > 0:
        resid = sm.OLS(y, x, missing='drop').fit().resid
        return resid.reindex(df.index)
    else:
        return y


# 因子分布
def plot_factor(df, fname, ifyear=False, ifcut=True):
    data = df.copy()
    data['year'] = data['Date'].apply(lambda x: x.split('-')[0])

    # 因子值的去头去尾
    if ifcut:
        data[fname] = winsor(data[fname])

    if ifyear:
        year_l = data.year.unique()
        n_year = len(year_l)
        ncol = int(n_year / 3) + 1

        fig, axes = plt.subplots(3, ncol, figsize=(24, 10), sharex=False, sharey=False)

        for i in range(n_year):
            sns.kdeplot(data.loc[data.year == year_l[i], fname], shade=True, ax=axes[int(i / ncol), i % ncol],
                        label=year_l[i])
    else:
        fig, axes = plt.subplots(1, 1, figsize=(24, 10), sharex=False, sharey=False)
        sns.kdeplot(data[fname], shade=True)

    plt.suptitle('Factor distribution:' + fname)


def plot_norm_of_qq(df, fname):
    # QQ图
    fig, axes = plt.subplots(1, 1, figsize=(24, 10), sharex=False, sharey=False)
    stats.probplot(df[fname], dist="norm", plot=plt)
    plt.suptitle('Factor norm of QQ:' + fname)
    plt.show()


# 计算因子自相关性 #一阶自回归的时间序列
def get_factor_atuo_corr(factors):
    # factors = fnormall;ret = retdata
    """
    计算因子自相关性
    """
    factors = factors.copy()
    factors = factors.set_index(['Date', 'Ticker'])
    fac = []
    for i in factors.columns:
        s = factors.loc[:, i].unstack().T.corr()
        fac.append(pd.DataFrame(np.diag(s, 1), columns=[i], index=s.index[1:]))

    fac = pd.concat(fac, axis=1)
    return fac


# 计算IC
def getIC(factors, ret, method='spearman'):
    # method = 'spearman';factors = fnorm;
    icall = pd.DataFrame()
    fall = pd.merge(factors, ret, left_on=['Date', 'Ticker'], right_on=['Date', 'Ticker'])
    icall = fall.groupby('Date').apply(lambda x: x.corr(method=method)['pct_chg_5']).reset_index()
    icall = icall.dropna().drop(['pct_chg_5'], axis=1).set_index('Date')
    return icall


# 画出因子自相关性图
def plot_atuo_corr(fac):
    # outputpath = output_picture
    """
    因子AC作图
    """
    for f in fac.columns:  # f = fac.columns[0]
        fig = plt.figure(figsize=(10, 5))
        fac[f].plot(legend=False, color='darkred')
        plt.title('因子auto_corr: ' + f)


# IC作图
def plotIC(ic_f):
    """
    IC作图
    """

    # fname = ic_f.columns[0]
    for fname in ic_f.columns:
        fig = plt.figure(figsize=(18, 8))
        ax = plt.axes()
        xtick = np.arange(0, ic_f.shape[0], 18)
        xticklabel = pd.Series(ic_f.index[xtick])
        plt.bar(np.arange(ic_f.shape[0]), ic_f[fname], color='red')
        ax.plot(np.arange(ic_f.shape[0]), ic_f[fname].rolling(10).mean(), color='green')
        ax1 = plt.twinx()
        ax1.plot(np.arange(ic_f.shape[0]), ic_f[fname].cumsum(), color='orange')
        ax.set_xticks(xtick)
        ax.set_xticklabels(xticklabel)
        plt.title(fname + '  IC = {},ICIR = {}'.format(round(ic_f[fname].mean(), 4),
                                                       round(ic_f[fname].mean() / ic_f[fname].std() * np.sqrt(52), 4)))


# IC分层
def getGroupIC(fdata, rt, method, groups):
    # groups = 5
    """
    因子分组IC，groups为分组数
    """
    rt = pd.concat([fdata, rt], axis=1).dropna()
    indexs = ["startdate"] + list(range(groups))
    if rt.shape[0] != 0:
        groupdata = pd.qcut(rt.iloc[:, 0], q=groups, labels=False, duplicates='drop')

        if groupdata.unique().shape[0] == groups:
            rt['group'] = groupdata
            IC = rt.groupby('group').apply(lambda x: x.corr(method=method).fillna(0).iloc[0, 1])

            result = pd.DataFrame([rt.columns[1]] + IC.tolist(), index=indexs).T

        else:
            result = pd.DataFrame([rt.columns[1]] + [0] * groups, index=indexs).T
    else:
        result = pd.DataFrame([rt.columns[1]] + [0] * groups, index=indexs).T

    return result.set_index('startdate')


# IC分层
def getGroupICSeries(factors, ret, method, groups):
    # method = 'spearman';factors = fnorm.copy();ret = ret
    icall = pd.DataFrame()

    dates = factors.Date.unique()
    ret = ret.pivot(index='Date', columns='Ticker', values='pct_chg_5')
    for dateuse in dates:  # dateuse = dates[0]

        fic = pd.DataFrame()
        fdata = factors.loc[factors.Date == dateuse, factors.columns[1:]].set_index('Ticker')

        rt = ret.loc[dateuse]
        for f in fdata.columns:  # f = fdata.columns[0]
            IC = getGroupIC(fdata[f], rt, method, groups)
            IC.insert(0, 'factor', f)
            fic = pd.concat([fic, IC], axis=0)

        icall = pd.concat([icall, fic], axis=0)

    return icall


# 分组IC作图
def plotGroupIC(groupIC):
    """
    分组IC作图
    """
    for f in groupIC.factor.unique():
        fig = plt.figure(figsize=(10, 5))
        groupIC.loc[groupIC.factor == f, groupIC.columns[1:]].mean(axis=0).plot(kind='bar')

        plt.title('Meverage of factor grouping IC: ' + f, fontsize=15)


# 一次性测试多个因子
def GroupTestAllFactors(factors, ret, groups):
    # factors = fnorm.copy();groups = 10
    """
    一次性测试多个因子
    """
    fnames = factors.columns
    fall = pd.merge(factors, ret, left_on=['Date', 'Ticker'], right_on=['Date', 'Ticker'])
    Groupret = []
    Groupturnover = []
    for f in fnames:  # f= fnames[2]
        if ((f != 'Ticker') & (f != 'Date')):
            fuse = fall[['Ticker', 'Date', 'pct_chg_5', f]]
            #            fuse['groups'] = pd.qcut(fuse[f],q = groups,labels = False)
            # 分组
            fuse['groups'] = fuse[f].groupby(fuse.Date).apply(
                lambda x: np.ceil(x.rank(method='first') / (len(x) / groups)))
            # 分组下期收益平均值
            result = fuse.groupby(['Date', 'groups']).apply(lambda x: x.pct_chg_5.mean())
            result = result.unstack().reset_index()
            if result.iloc[:, -1].mean() > result.iloc[:, -groups].mean():
                result['L-S'] = result.iloc[:, -1] - result.iloc[:, -groups]
                stock_l = fuse.loc[fuse.groups == 1]
            else:
                result['L-S'] = result.iloc[:, -groups] - result.iloc[:, -1]
                stock_l = fuse.loc[fuse.groups == groups]
            result.insert(0, 'factor', f)
            Groupret.append(result)

    Groupret = pd.concat(Groupret, axis=0).reset_index(drop=True)
    Groupret.dropna(inplace=True)

    Groupnav = Groupret.iloc[:, 2:].groupby(Groupret.factor).apply(lambda x: (1 + x / 100).cumprod())

    Groupnav = pd.concat([Groupret[['Date', 'factor']], Groupnav], axis=1)
    Groupnav.dropna(inplace=True)

    return Groupnav


# GroupTest作图
def plotnav(Groupnav):
    """
    GroupTest作图
    """
    for f in Groupnav.factor.unique():  # f = Groupnav.factor.unique()[0]
        fnav = Groupnav.loc[Groupnav.factor == f, :].set_index('Date').iloc[:, 1:]
        groups = fnav.shape[1] - 1
        lwd = [2] * groups + [4]
        ls = ['-'] * groups + ['--']

        plt.figure(figsize=(10, 5))
        for i in range(groups + 1):
            plt.plot(fnav.iloc[:, i], linewidth=lwd[i], linestyle=ls[i])
        plt.legend(list(range(groups)) + ['L-S'])
        plt.title('Factor layered testing / multi - space combination： ' + f, fontsize=15)


# 评价指标
def strategy_evaluate(df):
    # ===新建一个dataframe保存回测指标
    results = pd.DataFrame()

    ret_df = df[1].copy()
    ret_df['Date'] = pd.to_datetime(ret_df['Date'], format='%Y-%m-%d')

    for i in range(0, 6):
        results.loc[i, 'factor'] = df[0] + '_' + str(ret_df.columns[i + 2])
        # ===计算累积净值
        results.loc[i, 'cum_returns_final'] = round(ret_df[ret_df.columns[i + 2]].iloc[-1], 3)

        # ===计算年化收益
        annual_return = (ret_df[ret_df.columns[i + 2]].iloc[-1]) ** (
                '1 days 00:00:00' / (ret_df['Date'].iloc[-1] - ret_df['Date'].iloc[0]) * 365) - 1
        results.loc[i, 'Annual_return'] = str(round(annual_return * 100, 2)) + '%'

        # 计算当日之前的资金曲线的最高点
        ret_df['max2here'] = ret_df[ret_df.columns[i + 2]].expanding().max()
        # 计算到历史最高值到当日的跌幅，drowdwon
        ret_df['dd2here'] = ret_df[ret_df.columns[i + 2]] / ret_df['max2here'] - 1
        # 计算最大回撤，以及最大回撤结束时间
        end_date, max_draw_down = tuple(ret_df.sort_values(by=['dd2here']).iloc[0][['Date', 'dd2here']])

        results.loc[i, 'Max_drawdown'] = format(max_draw_down, '.2%')
        ret_df['pct_chg_{}'.format(i + 1)] = 100 * (
                ret_df[ret_df.columns[i + 2]] / ret_df[ret_df.columns[i + 2]].shift(1) - 1)

        ret_df.fillna(0, inplace=True)
        sharpe = round((ret_df['pct_chg_{}'.format(i + 1)] - 0.04 / 52).mean() / ret_df[
            'pct_chg_{}'.format(i + 1)].std() * np.sqrt(52), 3)

        results.loc[i, 'sharpe_ratio'] = sharpe

    return results


# 计算IC
def getfactor_return(factors, ret):
    df = pd.merge(factors, ret, left_on=['Date', 'Ticker'], right_on=['Date', 'Ticker'])
    return_df = pd.DataFrame()
    avg_mean = pd.DataFrame()
    fac_list = list(df.columns[2:-1])
    retu = 'pct_chg_5'
    for fac in fac_list:
        for i, df1 in enumerate(df.groupby('Date')):
            X = df1[1][fac].values
            X = standardize(X)
            X[np.isnan(X)] = 0
            Y = df1[1][retu].values
            result = sm.OLS(Y.astype(float), X.astype(float)).fit()  # 股票收益率和因子数据回归
            result = result.params[0]
            return_df.loc[i, 'Date'] = df1[0]
            return_df.loc[i, 'factor_return'] = result
        # 因子的平均收益
        avg_mean.loc[0, fac] = return_df['factor_return'].mean()

    return avg_mean


# 计算多因子的IC 与 ICIR 与因子收益率
def get_factor_icir_return(ic_, ic_value=0.07):
    report_df = pd.DataFrame()
    for i, fname in enumerate(ic_.columns):
        # 因子名称
        report_df.loc[i, 'factors'] = fname
        # 因子平均IC
        report_df.loc[i, 'IC'] = round(ic_[fname].mean(), 4)
        # 因子IR
        report_df.loc[i, 'IR'] = round(abs(ic_[fname].mean()) / ic_[fname].std() * np.sqrt(52), 4)

        # 因子IC》0.07的比例
        report_df.loc[i, 'IC>0.07'] = len(ic_[abs(ic_[fname]) > ic_value]) / len(ic_)

    return report_df


if __name__ == '__main__':
    pass
