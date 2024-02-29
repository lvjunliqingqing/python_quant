
from chart_analysis.create_bar_line_object import draw_profit_loss_details
from chart_analysis.create_bar_revers_object import create_bar_revers
from chart_analysis.create_histogram_object import create_histogram
from chart_analysis.create_line_object import create_line
from pyecharts.charts import Tab
from matplotlib import pyplot as plt
from utility import interval_statistics


def draw_profit_loss_chart(df, day_list, prefix="出水芙蓉_所有品种", prefix_1="盈亏详情图", prefix_2="不同周期"):
    """绘制不同持仓周期盈亏详情和净值图"""
    tab = Tab(page_title=f"{prefix}_{prefix_1}")

    for i in day_list:
        bar = draw_profit_loss_details(df["trade_date"].tolist(), df[f"{i}日后涨跌幅"].tolist(), df[f'{i}日后净值(不复利)'].tolist(), title=f"{prefix}_持仓{i}日{prefix_1}", series_name="盈亏详情")
        tab.add(bar, f"{prefix}_持仓{i}日{prefix_1}")
    tab.render(f"{prefix}_{prefix_2}{prefix_1}.html")


def draw_net_worth_chart(x_data, y_data, df, day_list, str_flag, chart_title="图的名字", file_name="图的文件名"):
    """
    绘制不同持仓周期的净值曲线图
    :param df: 数据源
    :param day_list: 周期列表
    :param file_name: 生成绘图的文件名
    """
    line = create_line(x_data, y_data, series_name=f"持仓{day_list[0]}{str_flag}", title=chart_title)
    for i in day_list[1:]:
        line.overlap(create_line(x_data, df[f"{i}{str_flag}"], series_name=f"持仓{i}{str_flag}", title=chart_title))
    line.render(f"{file_name}.html")


def draw_symbol_distribution_diagram(x_data, y_data, series_name="盈亏对比", title="不同品种盈亏对比图", file_name="不同品种盈亏对比图", yaxis_name="品种名称", xaxis_name="净值"):
    """绘制不同品种的盈亏对比柱状图"""
    bar = create_bar_revers(x_data, y_data,  series_name=series_name, title=title, yaxis_name=yaxis_name, xaxis_name=xaxis_name)
    bar.render(f'{file_name}.html')


def draw_profit_loss_distribution_histogram(df, day_list, file_name="芙蓉出水_盈亏分布直方图", series_name="芙蓉出水_盈亏_区间分布图", title="芙蓉出水_盈亏_区间分布图"):
    """
    绘制盈亏分布的直方图
    """
    tab = Tab(page_title=f"{file_name}")
    for i in day_list:
        x_data_right, x_data_left, y_data, d_tp = interval_statistics(df[f"{i}日后涨跌幅"])
        bar = create_histogram(x_data_right, x_data_left, y_data, d_tp, file_name=file_name, series_name=series_name, title=title)
        tab.add(bar, f"{series_name}_持仓{i}日")
    tab.render(f"{file_name}.html")


# 绘制策略曲线
def draw_equity_curve(df, data_dict, time='交易日期', pic_size=[16, 9], dpi=72, font_size=25):
    plt.figure(figsize=(pic_size[0], pic_size[1]), dpi=dpi)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    for key in data_dict:
        plt.plot(df[time], df[data_dict[key]], label=key)
    plt.legend(fontsize=font_size)
    plt.show()
