from Indicator_calculation.water_hibiscus import marking_water_hibiscus_signal
from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd

from utility import add_ma_data


def water_hibiscus_interface():
    """出水芙蓉量化接口函数"""
    all_futures_data = pd.DataFrame()
    futures_index = FuturesIndex()
    basic_statistic = BasicStatistic()
    # futures_price_df = futures_Index.read_futures_ma()
    futures_price_df = futures_index.read_futures_price_daily()
    for code, df in futures_price_df.groupby("security"):
        df = add_ma_data(df)
        df = marking_water_hibiscus_signal(df)  # 出水芙蓉信号标记
        df = basic_statistic.futures_change_percent_long(df)  # 计算N日后涨跌幅
        all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据

    all_futures_data.sort_values(by="trade_date", inplace=True)  # 按日期排序
    basic_statistic.statistical_prob(all_futures_data, "出水芙蓉", signal="water_hibiscus_signal", str_flag="出水芙蓉")  # 计算涨跌的概率


if __name__ == '__main__':
    water_hibiscus_interface()
