from datetime import datetime
import numpy as np
import talib
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts.commons.utils import JsCode


class MainPositionPriceRelationship(object):

    def __init__(self, futures_Index):
        super(MainPositionPriceRelationship, self).__init__()
        self.main_all_security = []
        self.get_main_all_security(futures_Index)

    def create_k_line(self, title):
        # 创建一个蜡烛图对象
        kline = (
            Kline()
                .add_xaxis(xaxis_data=self.data["times"])  # 添加x轴
                .add_yaxis(
                series_name="kLine",
                y_axis=self.data["datas"],
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
                axispointer_opts=opts.AxisPointerOpts(  # 多个区域的提示信息一起显示
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
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
                    opts.DataZoomOpts(is_show=False, xaxis_index=[0, 2], range_end=100),
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

    def create_curve_line(self, xaxis_data, series_name, y_axis, grid_index):
        """创建曲线图对象"""
        line = (
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
                    grid_index=grid_index,  # 轴所在的 grid 的索引
                    axislabel_opts=opts.LabelOpts(is_show=False),  # 坐标轴标签配置项
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=grid_index,
                    split_number=3,  # 对于连续型数据，自动平均切分成几段。默认为5段。连续数据的范围需要 max 和 min 来指定
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),  # 坐标轴刻度配置项
                    splitline_opts=opts.SplitLineOpts(is_show=False),  # 分割线配置项
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
            )
        )
        return line

    def create_volume(self):
        """创建volume图形元素对象"""
        bar = (
            Bar()
                .add_xaxis(xaxis_data=self.data["times"])
                .add_yaxis(
                series_name="Volum",
                y_axis=self.data["vols"],
                xaxis_index=1,  # 如果设置为 [0, 3] 则控制 axisIndex 为 0 和 3 的 x 轴。
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        """
                    function(params) {
                        var colorList;
                        if (barData[params.dataIndex][1] > barData[params.dataIndex][0]) {
                            colorList = '#ef232a';
                        } else {
                            colorList = '#14b143';
                        }
                        return colorList;
                    }
                    """
                    )
                ),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=1,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(is_show=False),  # 图例的类型
            )
        )

        open_Interest_line = self.create_curve_line(self.data["times"], "Open_Interest", self.data["open_interest"], 1)  # 持仓量曲线
        open_Interest_line.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1)  # 透明度 0-1  1为不透明
        )
        bar.overlap(open_Interest_line)

        return bar

    def create_macd(self, series_name):
        """macd图形元素对象"""
        main_position_bar = (
            Bar()
                .add_xaxis(xaxis_data=self.data["main_position"]["times"])
                .add_yaxis(
                series_name=series_name,
                y_axis=self.data["main_position"]["buy_main_open_interest"],
                xaxis_index=2,
                yaxis_index=2,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        """
                            function(params) {
                                var colorList;
                                if (params.data >= 0) {
                                  colorList = '#ef232a';
                                } else {
                                  colorList = '#14b143';
                                }
                                return colorList;
                            }
                            """
                    )
                ),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=2,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=2,
                    split_number=4,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        return main_position_bar

    def draw_chart(self, data, series_name, filename, title):
        self.data = data
        kline = self.create_k_line(title)
        ma5_line = self.create_k_line_line(self.data["times"], "MA5", self.data["MA5"])
        ma10_line = self.create_k_line_line(self.data["times"], "MA10", self.data["MA10"])
        ma20_line = self.create_k_line_line(self.data["times"], "MA20", self.data["MA20"])
        # k线图区元素对象(Kline + Line)
        overlap_kline_line = kline.overlap(ma5_line)
        overlap_kline_line = kline.overlap(ma10_line)
        overlap_kline_line = kline.overlap(ma20_line)

        # MACD图形数据元素对象
        overlap_bar_line = self.create_macd(series_name)

        # volume图形元素
        bar_1 = self.create_volume()

        self.grid_chart(overlap_kline_line, bar_1, overlap_bar_line, filename)

    def grid_chart(self, overlap_kline_line, bar_1, overlap_bar_line, filename):
    # def grid_chart(self, overlap_kline_line, bar_1):
        # 创建网格图形对象
        grid_chart = Grid(init_opts=opts.InitOpts(width="1400px", height="800px"))  # InitOpts:初始化配置项

        #  把data["datas"]这个数据渲染到js代码中(增加一个js对象),不支持pandas和numpy数据类型
        # 注意一定要用Grid对象来传递js对象,不然在js代码function中没法获取。
        grid_chart.add_js_funcs("var barData = {}".format(self.data["datas"]))
        # K线图和 MA5 的折线图
        grid_chart.add(
            overlap_kline_line,
            grid_opts=opts.GridOpts(pos_left="8%", pos_right="1%", height="60%"),
        )
        # Volum 柱状图
        grid_chart.add(
            bar_1,
            grid_opts=opts.GridOpts(
                pos_left="8%", pos_right="1%", pos_top="71%", height="10%"
            ),
        )
        # MACD
        grid_chart.add(
            overlap_bar_line,
            grid_opts=opts.GridOpts(
                pos_left="8%", pos_right="1%", pos_top="82%", height="14%"
            ),
        )
        grid_chart.render(filename)

    def get_main_all_security(self, futures_Index):
        today = datetime.now()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        main_force_continuous_df = futures_Index.read_futures_main_force_continuous(today)
        if not main_force_continuous_df.empty:
            self.main_all_security = main_force_continuous_df["security"].to_list()

    def add_ma_data(self, df, ma_cycle=[5, 10, 20], drop_flg=True):
        """df添加数据MA数据"""
        ma_last = f'MA{ma_cycle[-1]}'
        for cycle in ma_cycle:  # 注意均线数据计算出来的跟通达信上对应不上,是因为聚宽上的停盘时,使用了数据填充。
            df[f'MA{cycle}'] = talib.MA(df["close"], cycle).round(2)

        if drop_flg:  # ma为nan的行就删除所在行
            df.drop(df[np.isnan(df[ma_last])].index, inplace=True)
        return df