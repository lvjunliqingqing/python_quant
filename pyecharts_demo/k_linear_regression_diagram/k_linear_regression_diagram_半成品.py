
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Grid
import pandas as pd


class RegressionDistanceValue(object):

    def __init__(self):
        super(RegressionDistanceValue, self).__init__()

    def create_k_line(self, x_data, y_data, title):
        # 创建一个蜡烛图对象
        kline = (
            Kline()
                .add_xaxis(xaxis_data=x_data)  # 添加x轴
                .add_yaxis(
                series_name="kLine",
                y_axis=y_data,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",  # 图形的颜色。
                    color0="#14b143",  # 阴线 图形的颜色。
                    border_color="#ef232a",  # 图形的描边颜色。
                    border_color0="#14b143",  # 阴线 图形的描边颜色。
                ),
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title=title, pos_left="0"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,  # 是否是脱离 0 值比例。设置成 true 后坐标刻度不会强制包含零刻度。只在数值轴中（type: 'value'）有效。在设置 min 和 max 之后该配置项无效。
                    boundary_gap=False,  # 坐标轴两边留白策略
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),  # 坐标轴刻度线配置项  is_on_zero:X 轴或者 Y 轴的轴线是否在另一个轴的 0 刻度上，只有在另一个轴为数值轴且包含 0 刻度时有效。
                    splitline_opts=opts.SplitLineOpts(is_show=False),  # 分割线配置项,不显示x轴分割线
                    split_number=20,  # 对于连续型数据，自动平均切分成几段。默认为5段。连续数据的范围需要 max 和 min 来指定
                    min_="dataMin",  # 坐标轴刻度最小值。'dataMin'表示取数据最小值在该轴上的最小值作为最小刻度。
                    max_="dataMax",  # 坐标轴刻度最大值。
                ),
                toolbox_opts=opts.ToolboxOpts(pos_left='right'),  # 工具箱配置项,is_show= True是否显示工具栏组件,默认显示
                yaxis_opts=opts.AxisOpts(
                    is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True),

                ),
                tooltip_opts=opts.TooltipOpts(  # 提示框配置项
                    trigger="axis",  # 触发类型  'axis': 坐标轴触发  'item': 数据项图形触发，主要在散点图，饼图等无类目轴的图表中使用
                    axis_pointer_type="cross"  # 指示器类型。'line'：直线指示器  'cross'：十字准星指示器
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(  # 区域缩放配置项
                        is_show=False,  # 是否显示 组件。如果设置为 false，不会显示，但是数据过滤的功能还存在。
                        type_="inside",  # 组件类型，可选 "slider", "inside"
                        xaxis_index=[0, 0],
                        range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0, 1],  # 如果是 number 表示控制一个轴，如果是 Array 表示控制多个轴。 ，默认控制和 dataZoom 平行的第一个 xAxis
                        pos_top="97%",  # 工具栏组件离容器上侧的距离。 top 的值可以是像 20 这样的具体像素值，可以是像 '20%' 这样相对于容器高宽的百分比， top 的值也可以为为'top', 'middle', 'bottom'，组件会根据相应的位置自动对齐。
                        range_end=100  # 数据窗口范围的结束百分比。范围是：0 ~ 100
                    ),
                ],
            )
        )

        return kline

    def create_k_line_line(self, xaxis_data, series_name, y_axis):
        """创建K线图中叠加线:比如MA5,MA10等等"""
        kline_line = (
            Line()
                .add_xaxis(xaxis_data=xaxis_data)  # 添加x轴
                .add_yaxis(  # 添加y轴
                series_name=series_name,  # 指定y轴名字
                y_axis=y_axis,  # y轴的数据
                is_smooth=True,  # 是否平滑曲线
                linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.5),  # 线条设置项,opacity：透明度, width控制曲线的宽度
                label_opts=opts.LabelOpts(is_show=False),  # 坐标轴标签配置项
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(  # 坐标轴配置项
                    type_="category",  # 坐标轴类型,'value': 数值轴，适用于连续数据。'category': 类目轴，适用于离散的类目数据 'log' 对数轴。适用于对数数据。 'time': 时间轴，适用于连续的时序数据
                    grid_index=1,  # 轴所在的 grid 的索引
                    axislabel_opts=opts.LabelOpts(is_show=False),  # 坐标轴标签配置项
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    split_number=3,  # 对于连续型数据，自动平均切分成几段。默认为5段。连续数据的范围需要 max 和 min 来指定
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),  # 坐标轴刻度配置项
                    splitline_opts=opts.SplitLineOpts(is_show=False),  # 分割线配置项
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
            )
        )
        return kline_line

    def create_regression_distance_curve(self, x_data, y_data, series_name, x_index=2, y_index=2, curve_color="#000033", width=3):
        "收盘价到回归曲线的垂直距离"
        regression_distance_curve = (
            Line()
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                series_name=series_name,
                y_axis=y_data,
                xaxis_index=x_index,
                yaxis_index=y_index,
                itemstyle_opts=opts.ItemStyleOpts(
                    color=curve_color,  # 图形的颜色。
                ),
                linestyle_opts=opts.LineStyleOpts(width=width),
                label_opts=opts.LabelOpts(is_show=False),
            )
                .set_global_opts(
                legend_opts=opts.LegendOpts(is_show=False),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(is_show=False),
                )
                )
        )
        return regression_distance_curve

    def draw_chart(self, df, security):
        kline = self.create_k_line(trade_date_list, Kline_data_list, f"{security}价格回归距离曲线")
        ma5_line = self.create_k_line_line(trade_date_list, "MA5", df["MA5"].to_list())
        ma10_line = self.create_k_line_line(trade_date_list, "MA10", df["MA10"].to_list())
        ma20_line = self.create_k_line_line(trade_date_list, "MA20", df["MA20"].to_list())
        # k线图区元素对象(Kline + Line)
        overlap_kline_line = kline.overlap(ma5_line)
        overlap_kline_line.overlap(ma10_line)
        overlap_kline_line.overlap(ma20_line)

        # 价格回归曲线图形数据元素对象
        regression_distance_curve = self.create_regression_distance_curve(trade_date_list, df["distance"].to_list(), "收盘价到回归曲线的垂直距离")

        self.grid_chart(overlap_kline_line, regression_distance_curve)

    def grid_chart(self, overlap_kline_line, regression_distance_curve):
        # 创建网格图形对象
        grid_chart = Grid(init_opts=opts.InitOpts(width="1400px", height="800px"))  # InitOpts:初始化配置项

        # K线图和 MA系列的折线图
        grid_chart.add(
            overlap_kline_line,
            grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", height="60%"),
        )

        grid_chart.add(
            regression_distance_curve,
            grid_opts=opts.GridOpts(
                pos_left="3%", pos_right="1%", pos_top="72%", height="20%"
            ),
        )
        grid_chart.render(f"k线线性回归图_{security}.html")


if __name__ == "__main__":
    df = pd.read_csv("ZN9999.XSGE.csv")
    trade_date_list = df["trade_date"].to_list()
    Kline_data_list = df[["open", "close", "low", "high", "volume"]].values.tolist()
    security = df["security"].to_list()[0]
    RegressionDistanceValue().draw_chart(df, security)
    # print(Kline_data_list)


