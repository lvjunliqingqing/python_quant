import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import datetime
import time
import numpy as np
from funtions import *
import os
import warnings
from scipy.stats import rankdata
import scipy as sp
from jqdatasdk import *
from numpy import abs
from numpy import log
from numpy import sign
import pymysql
import tushare as ts

warnings.filterwarnings("ignore")
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 500)  # 最多显示数据的行数

localhost = "192.168.11.166"
username = 'root'
password = "jskjfwq"
dbname = 'futures'

now = datetime.datetime.now()
end_date = now.strftime("%Y-%m-%d")  # 获取到"2021-01-11"这个字符串
end_date = '2022-10-10'

factor_path = r'F:/jswork2/构建聚宽数据库/期货会员持仓/data/汇总/'
index_path = r"F:/jswork2/量化框架/多因子分析框架/data/input_data/"
daily_path = r'F:/jswork2/构建聚宽数据库/期货行情数据/data/日线行情/'
# output_path = r'F:/jswork2/期货策略/期货多因子/非量价因子/会员持仓/分析程序/data/会员因子构建数据/'
# muilt_factor_path = r'F:/jswork2/期货策略/期货多因子/非量价因子/会员持仓/分析程序/data/优秀席位多因子数据/'
muilt_factor_path = r'F:/jswork2/期货策略/期货多因子/非量价因子/会员持仓/分析程序/data/会员持仓多因子数据/'
output_path = r'F:/jswork2/量化框架/选股回测框架/data/output_data/'

# 获取期货交易日历
is_trade_date = pd.read_pickle(index_path + "is_trade_date" + ".pkl")
index_alldata = is_trade_date.copy()
index_alldata["index_pct_chg"] = 0

final_data = pd.read_pickle(output_path + 'zhuli_all_post_zhulian_final_data.pkl')

# ===新建一个dataframe保存回测指标
results = pd.DataFrame()

factor_list = [
    # 'long_position',
    # 'long_position_increase',
    'short_position',
    'short_position_increase',
    'net_position',
    'jiaquan_every_long_positon_zhanbi',
    'jiaquan_every_short_positon_zhanbi',
    'every_long_zhanbi_sub_short_zhanbi',
    'jiaquan_every_long_zhanbi_sub_short_zhanbi',
    'long_net_add_short_net_div_all_position',
    'long_net_div_all_long_sub_short_net_div_all_short',
    # 'net_xiwei',
    # 'all_position',
    'net_position_increase',
    'net_position_zhanbi',
    'net_position_pct_chg_1',
    'net_position_all_position_pct_chg_1',
    'long_position_pct_chg_1',
    'short_position_pct_chg_1',
    'long_position_all_position_pct_chg_1',
    'short_position_all_position_pct_chg_1',
    # 'sign_long_and_short_1',
    # 'sign_long_1',
    # 'sign_short_1',
    'net_position_pct_chg_3',
    'net_position_all_position_pct_chg_3',
    'long_position_pct_chg_3',
    'short_position_pct_chg_3',
    'long_position_all_position_pct_chg_3',
    'short_position_all_position_pct_chg_3',
    # 'sign_long_and_short_3',
    # 'sign_long_3',
    # 'sign_short_3',
    'net_position_pct_chg_5',
    'net_position_all_position_pct_chg_5',
    'long_position_pct_chg_5',
    'short_position_pct_chg_5',
    'long_position_all_position_pct_chg_5',
    'short_position_all_position_pct_chg_5',
    # 'sign_long_and_short_5',
    # 'sign_long_5',
    # 'sign_short_5',
    'net_position_pct_chg_10',
    'net_position_all_position_pct_chg_10',
    'long_position_pct_chg_10',
    'short_position_pct_chg_10',
    'long_position_all_position_pct_chg_10',
    'short_position_all_position_pct_chg_10',
    # 'sign_long_and_short_10',
    # 'sign_long_10',
    # 'sign_short_10',
]


fangxiang_list = ['long', 'short']

for factor in factor_list:
    print(factor)
    for begin_date in ['2015-01-05', '2015-01-06', '2015-01-07', '2015-01-08', '2015-01-09', '2015-01-10', '2015-01-13',
                       '2015-01-14']:
        for period_type in [1, 2, 3, 4, 5, 6, 8, 9]:
            for fangxiang in fangxiang_list:
                final_data['my_factor'] = final_data[factor]
                params_dict = {
                    'begin_date': begin_date,
                    'period_type': period_type,
                    'num': 5,
                    'rank': 0,
                    'fangxiang': fangxiang,
                    'c_rate': 1.5 / 10000,  # 手续费
                    't_rate': 0 / 1000,  # 印花税
                }
                select_stock, equity = get_backtest_equity_and_select_stock_data(final_data, is_trade_date,
                                                                                 index_alldata,
                                                                                 params_dict)
                if fangxiang == 'long':
                    good_equity = equity
                else:
                    bad_equity = equity
            if len(fangxiang_list) == 1:
                rtn, year_return, month_return = strategy_evaluate(equity, select_stock)
                par_str = str(factor) + '_' + str(params_dict['period_type']) + '_' + str(
                    params_dict['rank']) + '_' + \
                          params_dict['begin_date'] + '_' + params_dict['fangxiang']
            elif len(fangxiang_list) == 2:
                hedge_equity = pd.merge(good_equity, bad_equity, on=['Date'])
                hedge_equity['pct_chg'] = (hedge_equity['pct_chg_x'] - hedge_equity['pct_chg_y'])
                hedge_equity['equity_curve'] = (hedge_equity['pct_chg'] + 1).cumprod()
                hedge_equity['benchmark'] = (hedge_equity['index_pct_chg_x'] + 1).cumprod()
                rtn, year_return, month_return = strategy_evaluate(hedge_equity, select_stock)

                par_str = str(factor) + '_' + str(params_dict['period_type']) + '_' + str(
                    params_dict['rank']) + '_' + \
                          params_dict['begin_date'] + '_' + 'all'

            # ===计算累积净值
            results.loc[par_str, '累积净值'] = rtn[rtn.index == '累积净值'][0].values[0]
            results.loc[par_str, '年化收益'] = rtn[rtn.index == '年化收益'][0].values[0]
            results.loc[par_str, '最大回撤'] = rtn[rtn.index == '最大回撤'][0].values[0]

results.sort_values('累积净值', ascending=False, inplace=True)
print(results)
results.to_csv("./results.csv")
exit()
