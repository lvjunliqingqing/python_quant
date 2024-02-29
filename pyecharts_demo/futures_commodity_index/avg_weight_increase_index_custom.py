from pyecharts import options as opts
from pyecharts.charts import Line, Grid, Bar, Tab
import pandas as pd
from pyecharts.commons.utils import JsCode

from pyecharts_demo.futures_commodity_index.Logger import Logger
from pyecharts_demo.futures_commodity_index.futures_index_data import FuturesIndex
from pyecharts_demo.futures_commodity_index.send_email import send_email


def split_data(origin_data) -> dict:
    datas = []
    times = []

    for i in range(len(origin_data)):
        datas.append(origin_data[i][1:])
        times.append(origin_data[i][0])

    return {
        "datas": datas,
        "times": times,
    }


class CommodityIndex(object):

    def __init__(self):
        self.df_Index = ""
        self.ma_df = ""
        self.macd_df = ""
        self.boll_df = ""
        self.rsi_df = ""
        self.bias_df = ""
        self.df = ""
        self.data = ""

    def create_one_line(self, chart_name):
        """创建第一根曲线对象,配置此图的基本配置"""
        one_line = (
            Line()
                .add_xaxis(xaxis_data=self.data["times"])  # 添加x轴
                .add_yaxis(
                series_name=chart_name,
                y_axis=self.df_Index["close"],
                is_smooth=True,  # 线条样式  , 是否设置成圆滑曲线
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#9900ff",  # 图形的颜色。
                ),
                linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.5),
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title=chart_name, pos_left="0"),
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
                toolbox_opts=opts.ToolboxOpts(pos_left='right'),  # 工具箱配置项,is_show= True是否显示工具栏组件,默认显示, pos_left设置标题位置
                yaxis_opts=opts.AxisOpts(
                    is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=False),

                ),
                tooltip_opts=opts.TooltipOpts(  # 提示框配置项
                    trigger="axis",  # 触发类型  'axis': 坐标轴触发  'item': 数据项图形触发，主要在散点图，饼图等无类目轴的图表中使用
                    axis_pointer_type="cross"  # 指示器类型。'line'：直线指示器  'cross'：十字准星指示器
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(  # 区域缩放配置项
                        is_show=False,  # 是否显示 组件。如果设置为 false，不会显示，但是数据过滤的功能还存在。
                        type_="inside",  # 组件类型，可选 "slider", "inside"
                        xaxis_index=[0, 0],  # 联动,是这个控制的。
                        range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0, 1],  # 如果是 number 表示控制一个轴，如果是 Array 表示控制多个轴。 ，默认控制和 dataZoom 平行的第一个 xAxis
                        pos_top="97%",  # 工具栏组件离容器上侧的距离。 top 的值可以是像 20 这样的具体像素值，可以是像 '20%' 这样相对于容器高宽的百分比， top 的值也可以为为'top', 'middle', 'bottom'，组件会根据相应的位置自动对齐。
                        range_end=100  # 数据窗口范围的结束百分比。范围是：0 ~ 100
                    ),
                    opts.DataZoomOpts(is_show=False, xaxis_index=[0, 2], range_end=100),
                    opts.DataZoomOpts(is_show=False, xaxis_index=[0, 3], range_end=100),
                    opts.DataZoomOpts(is_show=False, xaxis_index=[0, 4], range_end=100),
                ],
            ).set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        )

        return one_line

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

    def create_bar(self, xaxis_data, series_name, y_axis, xaxis_index, yaxis_index, grid_index, split_number=4):
        """bar图形元素对象"""
        bar = (
            Bar()
                .add_xaxis(xaxis_data=xaxis_data)
                .add_yaxis(
                series_name=series_name,
                y_axis=y_axis,
                xaxis_index=xaxis_index,
                yaxis_index=yaxis_index,
                label_opts=opts.LabelOpts(is_show=False),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=grid_index,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=grid_index,
                    split_number=split_number,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )

        return bar

    def create_volume_bar(self):
        volume_bar = self.create_bar(self.data["times"], "Volume", self.df_Index["volume"].tolist(), 1, 1, 1)  # 不支持numpy类型
        volume_bar.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(
                # params.dataIndex 是 代表 数据的index值    params具体有哪些属性,请去pyecharts官网搜索formatter则明白所用法。
                color=JsCode(
                    """
                        function(params) {
                            var colorList;
                            if (barData[params.dataIndex][1] >= 0) {
                                colorList = '#ef232a';
                            } else {
                                colorList = '#14b143';
                            }
                            return colorList;
                        }
                """
                ),
                opacity=0.5  # bar透明度设置
            )
        )

        open_Interest_line = self.create_curve_line(self.data["times"], "Open_Interest", self.df_Index["open_interest"].tolist(), 1)  # 持仓量曲线
        open_Interest_line.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1)  # 透明度 0-1  1为不透明
        )
        volume_bar.overlap(open_Interest_line)

        # # 添加一个Y轴(双y轴在Grid中显示不出来,无效)
        # volume_bar.extend_axis(yaxis=opts.AxisOpts())
        # line = Line()
        # line.add_xaxis(data["times"])
        # # 将line数据通过yaxis_index指向后添加的Y轴
        # line.add_yaxis('右边Y轴', df_Index["open_interest"], yaxis_index=1)
        #
        # volume_bar.overlap(line)

        return volume_bar

    def create_macd_bar_line(self):
        macd_bar = self.create_bar(self.data["times"], "MACD", self.macd_df["macd"].tolist(), 2, 2, 2)
        macd_bar.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(
                # params.dataIndex 是 代表 数据的index值    params具体有哪些属性,请去pyecharts官网搜索formatter则明白所用法。
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
            ), )
        DIFF_line = self.create_curve_line(self.data["times"], "DIFF", self.macd_df["dif"], 2)
        DEA_line = self.create_curve_line(self.data["times"], "DEA", self.macd_df["dea"], 2)

        DIFF_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#330099"))
        DEA_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#0D0D0D"))

        macd_bar.overlap(DIFF_line)
        macd_bar_line = macd_bar.overlap(DEA_line)

        return macd_bar_line

    def create_rsi_line(self):
        rsi_line = self.create_curve_line(self.data["times"], "rsi", self.rsi_df["rsi"], 4).set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
        rsi_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"))
        return rsi_line

    def create_bias_line(self):
        bias_ma5_line = self.create_curve_line(self.data["times"], "BIAS", self.bias_df["bias_ma5"], 5).set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
        bias_ma10_line = self.create_curve_line(self.data["times"], "BIAS1", self.bias_df["bias_ma10"], 5)
        bias_ma20_line = self.create_curve_line(self.data["times"], "BIAS2", self.bias_df["bias_ma20"], 5)

        bias_ma5_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"))
        bias_ma10_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#00ffff"))
        bias_ma20_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#33ff33"))

        bias_ma5_line.overlap(bias_ma10_line)
        boll_bar_line = bias_ma5_line.overlap(bias_ma20_line)
        return boll_bar_line

    def draw_chart(self, chart_name):
        e_w_c_i_line = self.create_one_line(chart_name)
        e_w_c_i_line.set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#030303"), linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5))

        ma5_line = self.create_curve_line(self.data["times"], "MA5", self.ma_df["ma5"], 1)
        ma10_line = self.create_curve_line(self.data["times"], "MA10", self.ma_df["ma10"], 1)
        ma20_line = self.create_curve_line(self.data["times"], "MA20", self.ma_df["ma20"], 1)
        ma30_line = self.create_curve_line(self.data["times"], "MA30", self.ma_df["ma30"], 1)

        upper_line = self.create_curve_line(self.data["times"], "BOLL", self.boll_df["upper"], 1).set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color="#FF00FF"),
            # tooltip_opts=opts.TooltipOpts(
            #     formatter=JsCode(
            #         """
            #         function (params) {
            #         return params.seriesName + '_UP:' + params.value[1]
            #         }
            #         """
            #     )
            #
            # )
        )
        mid_line = self.create_curve_line(self.data["times"], "BOLL", self.boll_df["middle"], 1)
        lower_line = self.create_curve_line(self.data["times"], "BOLL", self.boll_df["lower"], 1).set_series_opts(itemstyle_opts=opts.ItemStyleOpts(color="#33ff99"))

        # k线图区元素对象(kline + line)
        e_w_c_i_line.overlap(ma5_line)
        e_w_c_i_line.overlap(ma10_line)
        e_w_c_i_line.overlap(ma20_line)
        e_w_c_i_line.overlap(ma30_line)
        e_w_c_i_line.overlap(upper_line)
        e_w_c_i_line.overlap(mid_line)
        overlap_kline_line = e_w_c_i_line.overlap(lower_line)

        # Volume柱状图
        volume_bar = self.create_volume_bar()

        # MACD图
        macd_bar_line = self.create_macd_bar_line()

        # rsi图
        rsi_line = self.create_rsi_line()

        # bias图
        bias_line = self.create_bias_line()

        grid_chart = self.grid_chart(overlap_kline_line, volume_bar, macd_bar_line, rsi_line, bias_line)
        return grid_chart

    def grid_chart(self, overlap_kline_line, volume_bar, macd_bar_line, rsi_line, bias_line):
        # 创建网格图形对象
        grid_chart = Grid(init_opts=opts.InitOpts(width="1500px", height="800px", page_title="等权商品指数", bg_color='rgba(255, 255, 255, 0.4)'))  # InitOpts:初始化配置项
        grid_chart.add_js_funcs("var barData = {}".format(self.data["datas"]))
        # K线图和 MA5 的折线图
        grid_chart.add(
            overlap_kline_line,
            grid_opts=opts.GridOpts(pos_left="6%", pos_right="1%", height="35%"),
        )

        # Volum 柱状图
        grid_chart.add(
            volume_bar,
            grid_opts=opts.GridOpts(
                pos_left="6%", pos_right="1%", pos_top="48%", height="10%"
            ),
        )

        # MACD图
        grid_chart.add(
            macd_bar_line,
            grid_opts=opts.GridOpts(
                pos_left="6%", pos_right="1%", pos_top="60%", height="10%"
            ),
        )

        # rsi图
        grid_chart.add(
            rsi_line,
            grid_opts=opts.GridOpts(
                pos_left="6%", pos_right="1%", pos_top="72%", height="10%"
            ),
        )

        # bias图
        grid_chart.add(
            bias_line,
            grid_opts=opts.GridOpts(
                pos_left="6%", pos_right="1%", pos_top="84%", height="10%"
            ),
        )

        # grid_chart.render("等权商品指数(自定义).html")
        return grid_chart

    def process_data(self, index_name, chart_name):
        futures_Index = FuturesIndex()
        self.df_Index = futures_Index.read_futures_index(index_name)  # 等权商品指数
        self.ma_df = futures_Index.read_futures_index_ma(index_name)
        self.macd_df = futures_Index.read_futures_index_macd(index_name)
        self.boll_df = futures_Index.read_futures_index_boll(index_name)
        self.rsi_df = futures_Index.read_futures_index_rsi(index_name)
        self.bias_df = futures_Index.read_futures_index_bias(index_name)

        self.df = pd.DataFrame()
        self.df["times"] = self.df_Index['trade_date'].apply(lambda x: x.strftime("%Y-%m-%d"))  # df中datetime64转字符串
        self.df["e_w_c_i"] = self.df_Index["close"]
        self.df["change_pct"] = self.df_Index["change_pct"]

        echarts_data = self.df.values.tolist()
        self.data = split_data(origin_data=echarts_data)

        return self.draw_chart(chart_name)


if __name__ == "__main__":
    logger = Logger("商品指数定时任务")
    try:
        commodity_index = CommodityIndex()

        avg_grid_chart = commodity_index.process_data("Avg Weight Increase Index", "等权商品指数")
        contract_grid_chart = commodity_index.process_data("Contract Value Weight Index 3Month", "持仓合约价值加权商品指数")
        money_grid_chart = commodity_index.process_data("Money Weight Index 3Month", "成交金额加权商品指数")

        tab = Tab(page_title="商品指数K线图系统")
        tab.add(avg_grid_chart, '等权商品指数')
        tab.add(contract_grid_chart, '持仓合约价值加权商品指数')
        tab.add(money_grid_chart, '成交金额加权商品指数')
        tab.render("自构建的商品指数k线.html")

        logger.info("自构建的商品指数k线执行成功")
    except Exception as e:
        send_email("自构建的商品指数k线定时任务执行失败,原因:{e}")
        logger.error(f"自构建的商品指数k线执行失败,原因:{e}")