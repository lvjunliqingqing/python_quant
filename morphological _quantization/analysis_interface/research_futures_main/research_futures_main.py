from datetime import datetime

from Indicator_calculation.the_hammer_line import the_hammer_line
from analysis_interface.research_futures_main.futures_rank import futures_company_top20, futrues_varieties_filter_list
from utility import add_MaVol_data, add_ma_data
from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd


def research_futures_main():
    """期货主力龙虎榜数据研究接口"""

    all_futures_data = pd.DataFrame()
    basic_statistic = BasicStatistic()
    today = datetime.now()
    today = today.strftime("%Y-%m-%d %H:%M:%S")
    futures_index = FuturesIndex()
    for security in futures_index.read_futures_main_force_continuous(today):
        if security in futrues_varieties_filter_list:
            continue

        for index, member_name in enumerate(futures_company_top20):

            main_position_df = futures_index.second_read_dwd_dominant_futures_winners_list(security, member_name)
            sell_main_position_df = main_position_df[main_position_df["rank_type_ID"] == 501003]
            buy_main_position_df = main_position_df[main_position_df["rank_type_ID"] == 501002]

            # 排名前20大期货公司持多单量
            buy_volume_series = buy_main_position_df.groupby(["trade_date"])["indicator"].sum()
            # 排名前20大期货公司持空单量
            sell_volume_series = sell_main_position_df.groupby(["trade_date"])["indicator"].sum()
            print(type(sell_volume_series))
            net_position_list = (buy_volume_series - sell_volume_series).fillna(method='ffill').to_list()
            main_times = buy_main_position_df.groupby(["trade_date"])["trade_date"].first().to_list()
            print(main_times)

            m_p_d_df = futures_index.read_futures_main_price_daily(security)
            m_p_d_df = m_p_d_df[m_p_d_df["trade_date"].isin(main_times)]

            print(security, member_name)

    # # 计算N日后涨跌幅所需参数
    # day_list = [1, 3, 5, 10, 20, 30]
    # basic_statistic.set_day_list(day_list=day_list)  # 设置N日参数列表
    # futures_price_df = futures_index.read_futures_price_daily()
    # for code, df in futures_price_df.groupby("security"):
    #     df = add_ma_data(df, ma_cycle=[5, 10, 20])
    #     df = the_hammer_line(df)  # 标记出锤子线信号
    #
    #     # df = add_MaVol_data(df)  # 添加平均成交量数据
    #     df = basic_statistic.futures_change_percent_long(df, close="close")  # 计算N日后涨跌幅
    #     all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据
    # # print(all_futures_data)
    # all_futures_data.sort_values(by="trade_date", inplace=True)  # 排序
    # basic_statistic.statistical_prob(all_futures_data, "锤子线", signal="the_hammer_line_signal", str_flag="锤子线", str2_flag="锤子线")  # 计算涨跌的概率


if __name__ == '__main__':
    research_futures_main()

