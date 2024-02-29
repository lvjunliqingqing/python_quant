from Indicator_calculation.baldheaded_yang_line import marking_baldheaded_yang_line
from Indicator_calculation.macd_deviate import calculate_macd, marking_deviate_signal
from utility import add_MaVol_data, add_ma_data
from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd


def macd_deviate_interface():
    """macd底背离分析接口函数"""
    all_futures_data = pd.DataFrame()
    futures_index = FuturesIndex()
    basic_statistic = BasicStatistic()
    # 将高点时间段定为30日，可自己修改
    days = 30  # macd背离的时间窗口
    # 计算N日后涨跌幅所需参数
    day_list = [1, 3, 5, 10, 20, 30]
    futures_price_df = futures_index.read_futures_price_daily()
    for code, df in futures_price_df.groupby("security"):
        df = calculate_macd(df, close='close')  # 计算MACD指标
        df = marking_deviate_signal(df, days)  # 标记出macd顶底背离信号

        # df = add_ma_data(df, ma_cycle=[5, 10, 20], drop_flg=False)
        # df = add_MaVol_data(df)  # 添加平均成交量数据
        basic_statistic.set_day_list(day_list=day_list)  # 设置N日参数列表
        df = basic_statistic.futures_change_percent_long(df, close="close")  # 计算N日后涨跌幅

        all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据

    all_futures_data.sort_values(by="trade_date", inplace=True)  # 排序
    basic_statistic.statistical_prob(all_futures_data, "macd底背离", signal="macd_deviate_signal", str_flag="macd底背离", str2_flag="macd底背离")  # 计算涨跌的概率


if __name__ == '__main__':
    macd_deviate_interface()


