

from chart_analysis.draw_chart import draw_profit_loss_chart, draw_net_worth_chart, draw_profit_loss_distribution_histogram
from utility import get_symbol_price_pick, get_symbol_commission


class BasicStatistic:

    def __init__(self):
        # self.day_list = [1, 5, 10, 20, 30, 60]
        self.day_list = [1, 3, 5, 7, 10]

    def set_day_list(self, day_list):
        self.day_list = day_list

    def futures_change_percent_long(self, df, close='close', open="open", security="security"):
        """
        计算N日后涨跌幅(多头)
        """
        open_price_series = df[open].shift(-1)  # 开盘价的series
        symbol = df[security].to_list()[0]
        slippage = get_symbol_price_pick(symbol) * 2  # 滑点
        commission = get_symbol_commission(symbol, open_price_series)  # 手续费
        df["开仓价"] = open_price_series
        for i in self.day_list:
            # df['%s日后close' % i] = df[close].shift(-i)
            df['%s日后涨跌幅' % i] = (df[close].shift(-(i+1)) / (open_price_series + slippage + commission)) - 1  # 涨跌幅(已减去手续费和滑点)
            # df['%s日后涨跌幅' % i] = (df[close].shift(-i) / open_price_series - 1)
        return df

    def futures_change_percent_short(self, df, close='close', open="open", security="security"):
        """
        计算N日后涨跌幅(空头)
        """
        open_price_series = df[open].shift(-1)  # 开盘价的series
        symbol = df[security].to_list()[0]
        slippage = get_symbol_price_pick(symbol) * 2  # 滑点
        commission = get_symbol_commission(symbol, open_price_series)  # 手续费
        for i in self.day_list:
            df['%s日后close' % i] = df[close].shift(-(i+1))
            # df['%s日后涨跌幅' % i] = 1 - (df[close].shift(-(i+1)) / (open_price_series - slippage - commission))  # 涨跌幅(已减去手续费和滑点)
            df['%s日后涨跌幅' % i] = (df[close].shift(-i-1) / open_price_series - 1)
        return df

    def statistical_prob(self, df, xt_flag, signal='macd_signal',  str_flag="macd金叉_", str2_flag="macd死叉_"):
        """
        统计信号出现后n日的涨跌概率以及胜率等等
            xt_flag:表示那种形态
        """
        for signal, group in df.groupby(signal):
            print("signal:", signal)
            print(group[[str(i) + '日后涨跌幅' for i in self.day_list]].describe())  # 综合分析
            print("-------------------------------------------------------")
            for i in self.day_list:
                win_df = group[group[str(i) + '日后涨跌幅'] > 0]
                loss_df = group[group[str(i) + '日后涨跌幅'] < 0]
                column_name = str(i) + '日后涨跌幅'
                if signal == 1:
                    win_rate = round(win_df.shape[0] / group.shape[0], 3)
                    profit_loss_than = round(abs((win_df[column_name].sum() / len(win_df)) / (loss_df[column_name].sum() / len(loss_df))), 3)
                    # 凯利公式 = (盈亏比 * 胜率 - 赔率) / 盈亏比
                    f_k_l = round((profit_loss_than * win_rate - (1-win_rate)) / profit_loss_than, 3)
                    print(str_flag + str(i) + '天后涨跌幅大于0概率', '\t', win_rate)
                    print(str_flag + str(i) + '天后盈亏比', '\t', profit_loss_than)
                    print(str_flag + str(i) + '天后凯利值', '\t', f_k_l)
                    print("-------------------------------------------------------")
                elif signal == 0:
                    print(str2_flag + str(i) + '天后涨跌幅小于0概率', '\t', round(loss_df.shape[0] / group.shape[0], 3))
                    print(str2_flag + str(i) + '天后盈亏比', '\t', round(abs((loss_df[column_name].sum() / len(loss_df)) / (win_df[column_name].sum() / len(win_df))), 3))

            df = self.accumulative_return_rate(group)
            df.to_csv(f"{str_flag}{signal}.csv", index=False)

            self.draw_diagram(group, xt_flag)

    def draw_diagram(self, df, xt_flag="出水芙蓉"):
        """
        按交易日分组统计 & 绘制分析图
        """
        new_df = df.groupby("trade_date").agg(trade_date=('trade_date', 'first'))

        for i in self.day_list:  # 按交易日统计涨跌幅
            new_df[f"{i}日后涨跌幅"] = df.groupby("trade_date").agg(trade_date=(f"{i}日后涨跌幅", 'mean')).round(4)

        new_df = self.accumulative_return_rate(new_df)  # 计算净值

        draw_profit_loss_chart(new_df, self.day_list, prefix=f"{xt_flag}_所有品种", prefix_1="盈亏详情图", prefix_2="不同周期")  # 单周期的盈亏详情图和净值

        draw_net_worth_chart(new_df["trade_date"], new_df["1日后净值(不复利)"], new_df, self.day_list, str_flag="日后净值(不复利)", chart_title=f"{xt_flag}_不同持仓周期净值对比图", file_name=f"{xt_flag}_不同持仓周期净值对比图")  # 不同周期净值对比图
        draw_profit_loss_distribution_histogram(new_df, self.day_list, file_name=f"{xt_flag}_不同周期盈亏分布直方图", series_name=f"{xt_flag}_盈亏_区间分布图", title=f"{xt_flag}_盈亏_区间分布图")  # 单周期的盈亏分布图

    def accumulative_return_rate(self, df):
        """计算累计收益率"""
        for i in self.day_list:
            # df[f'{i}日后净值(复利)'] = (df[f'{i}日后涨跌幅'] + 1).cumprod().round(4)  # 求净值(复利)
            df[f'{i}日后净值(不复利)'] = df[f'{i}日后涨跌幅'].cumsum().round(4)  # 求净值(不复利)
            df[f'{i}日后净值(不复利)'] = df[f'{i}日后净值(不复利)'] + 1
        return df

