from Indicator_calculation.baldheaded_yang_line import marking_baldheaded_yang_line
from utility import add_MaVol_data, add_ma_data
from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd


def baldheaded_yang_line_interface():
    """长下影线量化分析接口函数"""
    all_futures_data = pd.DataFrame()
    futures_index = FuturesIndex()
    basic_statistic = BasicStatistic()
    futures_price_df = futures_index.read_futures_price_daily()
    for code, df in futures_price_df.groupby("security"):
        df = add_ma_data(df, ma_cycle=[5, 10, 20], drop_flg=False)
        df = add_MaVol_data(df)  # 添加平均成交量数据
        df = marking_baldheaded_yang_line(df)  # 光头大阳线信号标记
        df = basic_statistic.futures_change_percent_long(df)  # 计算N日后涨跌幅
        all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据

    all_futures_data.sort_values(by="trade_date", inplace=True)  # 排序
    basic_statistic.statistical_prob(all_futures_data, "光头大阳线", signal="baldheaded_yang_line_signal", str_flag="光头大阳线")  # 计算涨跌的概率


if __name__ == '__main__':
    baldheaded_yang_line_interface()
