from basic_statistics_indicator.basic_statistics import BasicStatistic
from data.futures_data import FuturesIndex
import pandas as pd
from utility import optimize_long_change_percent


def macd_deviate_optimize(days=3, loss_point=4):
    """
    macd底背离优化:
        固定止损+移动平均线止损
    """
    data_df = pd.read_csv("macd底背离1.0.csv")
    data_df["平仓价"] = 0
    data_df["平仓日期"] = ""

    futures_index = FuturesIndex()
    basic_statistic = BasicStatistic()
    futures_price_df = futures_index.read_futures_price_daily()
    all_futures_data = pd.DataFrame()
    for code, df in futures_price_df.groupby("security"):
        df["MA10"] = df["close"].ewm(span=10, adjust=False).mean().round(4)  # 计算10日均线
        all_futures_data = all_futures_data.append(df, ignore_index=True)  # 合并数据

    all_futures_data.sort_values(by="trade_date", inplace=True)  # 排序
    all_futures_data.index = pd.to_datetime(all_futures_data["trade_date"])

    for index, row in data_df.iterrows():  # 底背离信号数据
        security_df = all_futures_data[all_futures_data['security'] == row["security"]]  # 获取单个品种的df
        position = security_df.index.get_loc(row["trade_date"])
        security_df = security_df.iloc[position+1:position + days+1]  # 获取开仓日到持仓周期到期日的k线数据

        exit_price = security_df.tail(1)["close"].to_list()[0]  # 初始设置平仓价
        exit_date = security_df.tail(1)["trade_date"].to_list()[0]  # 初始设置平仓日
        loss_price = row["loss_price"]  # 设置初始止损价
        if abs((loss_price - row["开仓价"]) / row["开仓价"] * 100) > loss_point:  # 确定止损点在规定点数内
            loss_price = row["开仓价"] * (100 - loss_point) / 100

        for index_2, row2 in security_df.iterrows():  # 移动止损价

            if row2["close"] < loss_price:  # 如果止损出场
                exit_price = row2["close"]
                exit_date = row2["trade_date"]
                cond3 = data_df["security"] == row["security"]
                cond4 = data_df["trade_date"] == row["trade_date"]
                data_df.loc[cond3 & cond4, "是否止损出场"] = "是"
                break

            if row2["MA10"] > loss_price and row2["close"] > row2["MA10"] and row2["close"] > row["开仓价"]:  # 10日均价移动止损
                loss_price = row2["MA10"]

        cond1 = data_df["security"] == row["security"]
        cond2 = data_df["trade_date"] == row["trade_date"]
        data_df.loc[cond1 & cond2, "平仓价"] = exit_price
        data_df.loc[cond1 & cond2, "平仓日期"] = exit_date
        data_df.loc[cond1 & cond2, "移动止损价"] = loss_price
        data_df.loc[cond1 & cond2, f"{days}日后涨跌幅"] = optimize_long_change_percent(row["security"], row["开仓价"], exit_price)

    keep_columns = ["security", "trade_date", "loss_price", "state", "开仓价", "平仓价", "平仓日期", "是否止损出场", "移动止损价", f"{days}日后涨跌幅", "macd_deviate_signal", "1日后涨跌幅",  "1日后净值(不复利)"]

    draw_df = data_df[keep_columns]

    # draw_df.sort_values(by="trade_date", inplace=True)  # 表示排序的结果是直接在原数据上的就地修改还是生成新的DatFrame,会报错。
    new_draw_df = draw_df.sort_values(by="trade_date")  # 排序
    new_draw_df[f"{days}日后净值(不复利)"] = new_draw_df[f"{days}日后涨跌幅"].cumsum().round(4)
    new_draw_df[f"{days}日后净值(不复利)"] = new_draw_df[f"{days}日后净值(不复利)"] + 1

    new_draw_df.to_csv("macd底背离优化.csv", index=False)

    basic_statistic.set_day_list(day_list=[1, 3])
    basic_statistic.statistical_prob(new_draw_df, "macd底背离", signal="macd_deviate_signal", str_flag="macd底背离", str2_flag="macd顶背离")  # 计算涨跌的概率


if __name__ == '__main__':
    macd_deviate_optimize()

