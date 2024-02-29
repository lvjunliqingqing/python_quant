import pandas as pd
import tushare as ts

from alphalens.utils import get_clean_factor_and_forward_returns
pd.set_option('display.float_format', lambda x: '%.4f' % x)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

pro = ts.pro_api(token="3d0ce5b02911a61a411deb19be29de9b24c50caf7807f34a5dff38d9")
# 此接口获取的数据为未复权数据，回测建议使用复权数据，这里为批量获取股票数据做了简化
df = pro.daily(ts_code='000001.SZ,600982.SH', start_date='20200101', end_date='20211122')
df.index = pd.to_datetime(df['trade_date'])
df.index.name = None
df.sort_index(inplace=True)
# 多索引的因子列，第一个索引为日期，第二个索引为股票代码
assets = df.set_index([df.index, df['ts_code']], drop=True)
# column为股票代码，index为日期，值为收盘价
close = df.pivot_table(index='trade_date', columns='ts_code', values='close')
close.index = pd.to_datetime(close.index)

print(assets[['pct_chg']].shift(2).head(10))
print(close.head(5))

# # 我们是使用pct_chg因子数据预测收盘价，因此需要偏移1天，但是这里有2只股票，所以是shift(2)
# # 接受的第一个参数就是因子的列，我们只需要从前面预处理好的 assets 中任取一列作为因子进行回测即可，第二列是收盘价。
# ret = get_clean_factor_and_forward_returns(assets[['pct_chg']].shift(2), close)
# create_full_tear_sheet(ret, long_short=False)
