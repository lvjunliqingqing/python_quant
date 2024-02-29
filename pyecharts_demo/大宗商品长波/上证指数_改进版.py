from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid, Tab
from pyecharts.commons.utils import JsCode
from calculate_ma import add_ma_data
from create_table import create_table
from draw_scatter import draw_scatter
from stock_data import StockData


class SZEVENTBACK(object):

    def create_Kline(self):
        kline = (
            Kline()
                .add_xaxis(xaxis_data=data["times"])
                .add_yaxis(
                series_name="KLine",
                y_axis=data["datas"],
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#14b143",
                    border_color="#ef232a",
                    border_color0="#14b143",
                ),
            )
                .set_series_opts(
                    markarea_opts=opts.MarkAreaOpts(  # 设置标记区域
                        label_opts=opts.LabelOpts(position="inside Top", color="black", font_size=13, font_weight="bold"),
                        itemstyle_opts=opts.ItemStyleOpts(color="gray", opacity=0.5),
                        data=[
                            opts.MarkAreaItem(name="第一次工业革命", x=(data["times"][-100], data["times"][-1])),
                        ]
                    )
            )
                .set_global_opts(  # set_global_opt是全局配置项,具体使用参考pyecharts官网
                title_opts=opts.TitleOpts(title="上证指数回溯事件", pos_left="0"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    split_number=20,
                    min_="dataMin",
                    max_="dataMax",
                ),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True)
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="line"),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False, type_="inside", xaxis_index=[0, 0], range_start=85, range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True, xaxis_index=[0, 1], pos_top="97%", range_start=85, range_end=100
                    ),
                ],
                # # 二个图(Kline,volume)的坐标信息矩形框设置连在一块
                # axispointer_opts=opts.AxisPointerOpts(
                #     is_show=True,
                #     link=[{"xAxisIndex": "all"}],
                #     label=opts.LabelOpts(background_color="#777"),
                # ),
            )
        )
        return kline

    def create_Ma_Line(self):
        kline_line = (
            Line()
                .add_xaxis(xaxis_data=data["times"])
                .add_yaxis(
                series_name="MA5",
                y_axis=df["MA5"].to_list(),
                is_smooth=True,
                linestyle_opts=opts.LineStyleOpts(opacity=0.9),
                label_opts=opts.LabelOpts(is_show=False),
            )
                .add_yaxis(
                series_name="MA10",
                y_axis=df["MA10"].to_list(),
                is_smooth=True,
                linestyle_opts=opts.LineStyleOpts(opacity=0.9),
                label_opts=opts.LabelOpts(is_show=False),
            )
                .add_yaxis(
                series_name="MA20",
                y_axis=df["MA20"].to_list(),
                is_smooth=True,
                linestyle_opts=opts.LineStyleOpts(opacity=0.9),
                label_opts=opts.LabelOpts(is_show=False),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=1,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    split_number=3,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
            )
        )

        return kline_line

    def create_volume_bar(self):
        volume_bar = (
            Bar()
                .add_xaxis(xaxis_data=data["times"])
                .add_yaxis(
                series_name="Volumn",
                y_axis=data["vols"],
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
                # 改进后在 grid 中 add_js_funcs 后变成如下
                itemstyle_opts=opts.ItemStyleOpts(  # 设置元素样式
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
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        return volume_bar

    def create_scatter(self, overlap_kline_line): # 添加散点图
        x_data1 = [data["times"][i] for i in range(len(data["times"])) if i % 53 == 0]
        y_data1 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 53 == 0]

        x_data2 = [data["times"][i] for i in range(len(data["times"])) if i % 54 == 0]
        y_data2 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 54 == 0]

        x_data3 = [data["times"][i] for i in range(len(data["times"])) if i % 55 == 0]
        y_data3 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 55 == 0]

        x_data4 = [data["times"][i] for i in range(len(data["times"])) if i % 56 == 0]
        y_data4 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 56 == 0]

        x_data5 = [data["times"][i] for i in range(len(data["times"])) if i % 57 == 0]
        y_data5 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 57 == 0]

        scatter = draw_scatter(x_data1, y_data1, "政治类")
        scatter2 = draw_scatter(x_data2, y_data2, "经济类")
        scatter3 = draw_scatter(x_data3, y_data3, "行业变革类")
        scatter4 = draw_scatter(x_data4, y_data4, "国际类")
        scatter5 = draw_scatter(x_data5, y_data5, "黑天鹅类")

        overlap_kline_line.overlap(scatter)
        overlap_kline_line.overlap(scatter2)
        overlap_kline_line.overlap(scatter3)
        overlap_kline_line.overlap(scatter4)
        overlap_kline_line.overlap(scatter5)

        return overlap_kline_line

    def draw_chart(self):

        kline = self.create_Kline()
        kline_line = self.create_Ma_Line()

        # Overlap Kline + Line
        overlap_kline_line = kline.overlap(kline_line)  # overlap把图叠加
        overlap_kline_line = self.create_scatter(overlap_kline_line)

        volume_bar = self.create_volume_bar()

        grid_chart = Grid(init_opts=opts.InitOpts(width="1400px", height="800px"))

        #  把data["datas"]这个数据渲染到js代码中,不支持pandas和numpy数据类型
        # 注意一定要用Grid对象来传递js对象,不然在js代码function中没法获取。
        grid_chart.add_js_funcs("var barData = {}".format(data["datas"]))

        # K线图和 MA5 的折线图
        grid_chart.add(
            overlap_kline_line,
            grid_opts=opts.GridOpts(pos_left="12%", pos_right="1%", height="60%"),
        )
        # Volumn 柱状图
        grid_chart.add(
            volume_bar,
            grid_opts=opts.GridOpts(
                pos_left="12%", pos_right="1%", pos_top="73%", height="21%"
            ),
        )

        # grid_chart.render("改进版_上证指数回溯事件.html")
        return grid_chart

    def tab_add_table(self, tab):
        table1 = create_table("政治事件")
        table2 = create_table("经济事件")
        table3 = create_table("行业变革事件")
        table4 = create_table("国际事件")
        table5 = create_table("黑天鹅事件")
        tab.add(table1, '政治事件')
        tab.add(table2, '经济事件')
        tab.add(table3, '行业变革事件')
        tab.add(table4, '国际事件')
        tab.add(table5, '黑天鹅事件')
        return tab


if __name__ == "__main__":
    stock_data = StockData()
    df = stock_data.stock_index_price_daily("000001.XSHG")
    df = add_ma_data(df)  # 添加均线数据
    times = df["trade_date"].to_list()
    datas = df[["open", "close", "low", "high", "volume"]].values.tolist()
    data = {"datas": datas, "times": times, "vols": df["volume"].to_list(), "highs": df["high"].to_list()}
    security = df["security"].to_list()[0]
    sz_event_back = SZEVENTBACK()
    grid_chart = sz_event_back.draw_chart()
    tab = Tab(page_title="上证指数回溯事件系统")
    tab.add(grid_chart, '上证指数回溯事件K线图')
    tab = sz_event_back.tab_add_table(tab)
    tab.render("上证指数回溯事件系统.html")
