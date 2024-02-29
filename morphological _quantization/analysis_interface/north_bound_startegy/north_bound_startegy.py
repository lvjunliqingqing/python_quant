"""
正确和错误的示范的区别:只是数据表的数据有所不同而已
核心逻辑:大于20.41亿看涨，小于2.95亿看跌
"""
import pandas as pd
from basic_statistics_indicator.evaluate_investment import evaluate_investment
from chart_analysis.draw_chart import draw_equity_curve


# 读取错误的
error_df = pd.read_csv('north_bound_err.csv', encoding='utf-8-sig', parse_dates=['交易日期'])
# 根据每日涨跌幅计算策略资金曲线
error_df['错误策略资金曲线'] = (error_df['equity_change'] + 1).cumprod()

# 读取正确
correct_df = pd.read_csv('north_bound_correct.csv', encoding='utf-8-sig', parse_dates=['交易日期'])
# 根据每日涨跌幅计算策略资金曲线
correct_df['正确策略资金曲线'] = (correct_df['equity_change'] + 1).cumprod()


# 评估错误策略表现
res = evaluate_investment(error_df, tittle='错误策略资金曲线', time_label='交易日期')
# 显示回测结果
print('\n===============错误结果展示===============')
print(res)

# 评估正确策略表现
res = evaluate_investment(correct_df, tittle='正确策略资金曲线', time_label='交易日期')
# 显示回测结果
print('\n===============正确结果展示===============')
print(res)

# 合并正确数据和错误数据，并在同一张图上绘制资金曲线
df = pd.merge(left=correct_df, right=error_df[['交易日期', '错误策略资金曲线']], on=['交易日期'], how='left')
# draw_equity_curve(df, data_dict={'资金择时_错误': '错误策略资金曲线', '资金择时_正确': '正确策略资金曲线', '沪深300': 'benchmark'})


