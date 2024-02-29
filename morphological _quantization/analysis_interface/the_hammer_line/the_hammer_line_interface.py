
from Indicator_calculation.the_hammer_line import the_hammer_line
from utility import add_MaVol_data, add_ma_data
from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd


def the_hammer_line_interface():
    """锤子线分析接口函数"""
    all_futures_data = pd.DataFrame()
    futures_index = FuturesIndex()
    basic_statistic = BasicStatistic()
    # 计算N日后涨跌幅所需参数
    day_list = [1, 3, 5, 10, 20, 30]
    basic_statistic.set_day_list(day_list=day_list)  # 设置N日参数列表
    futures_price_df = futures_index.read_futures_price_daily()
    for code, df in futures_price_df.groupby("security"):
        df = add_ma_data(df, ma_cycle=[5, 10, 20])
        df = the_hammer_line(df)  # 标记出锤子线信号

        # df = add_MaVol_data(df)  # 添加平均成交量数据
        df = basic_statistic.futures_change_percent_long(df, close="close")  # 计算N日后涨跌幅
        all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据
    # print(all_futures_data)
    all_futures_data.sort_values(by="trade_date", inplace=True)  # 排序
    basic_statistic.statistical_prob(all_futures_data, "锤子线", signal="the_hammer_line_signal", str_flag="锤子线", str2_flag="锤子线")  # 计算涨跌的概率


if __name__ == '__main__':
    the_hammer_line_interface()
