from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid, Tab
from pyecharts.commons.utils import JsCode
from calculate_ma import add_ma_data
from create_table import create_table
from draw_scatter import draw_scatter
from pyecharts_demo.futures_commodity_index.send_email import send_email
from pyecharts_demo.futures_commodity_index.Logger import Logger
from stock_data import StockData


class SZEVENTBACK(object):

    def __init__(self):
        self.international_index_dict = {}

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
            #     .set_series_opts(
            #         markarea_opts=opts.MarkAreaOpts(  # 设置标记区域
            #             label_opts=opts.LabelOpts(position="inside Top", color="black", font_size=13, font_weight="bold"),
            #             itemstyle_opts=opts.ItemStyleOpts(color="gray", opacity=0.5),
            #             data=[
            #                 opts.MarkAreaItem(name="第一次工业革命", x=(data["times"][-100], data["times"][-1])),
            #             ]
            #         )
            # )
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

    def create_scatter(self, overlap_kline_line):  # 添加散点图

        politics_df = event_data_df[event_data_df["incident_type"] == "政治事件"].groupby(by='trade_date').first()
        x_data1 = politics_df.index.to_list()
        politics_incident = politics_df["incident"].to_list()
        y_data1 = [[coordinate_point[v], politics_incident[i]] for i, v in enumerate(x_data1)]
        # x_data1 = [data["times"][i] for i in range(len(data["times"])) if i % 53 == 0]
        # y_data1 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 53 == 0]


        economic_df = event_data_df[event_data_df["incident_type"] == "经济事件"].groupby(by='trade_date').first()
        x_data2 = economic_df.index.to_list()
        economic_incident = economic_df["incident"].to_list()
        y_data2 = [[coordinate_point[v], economic_incident[i]] for i, v in enumerate(x_data2)]
        # x_data2 = [data["times"][i] for i in range(len(data["times"])) if i % 54 == 0]
        # y_data2 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 54 == 0]


        industry_change_df = event_data_df[event_data_df["incident_type"] == "行业变革事件"].groupby(by='trade_date').first()
        x_data3 = industry_change_df.index.to_list()
        industry_change_incident = industry_change_df["incident"].to_list()
        y_data3 = [[coordinate_point[v], industry_change_incident[i]] for i, v in enumerate(x_data3)]
        # x_data3 = [data["times"][i] for i in range(len(data["times"])) if i % 55 == 0]
        # y_data3 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 55 == 0]


        international_df = event_data_df[event_data_df["incident_type"] == "国际事件"].groupby(by='trade_date').first()
        x_data4 = international_df.index.to_list()
        international_incident = international_df["incident"].to_list()
        y_data4 = [[coordinate_point[v], international_incident[i]] for i, v in enumerate(x_data4)]
        # x_data4 = [data["times"][i] for i in range(len(data["times"])) if i % 56 == 0]
        # y_data4 = [[data["highs"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(data["highs"])) if i % 56 == 0]


        black_df = event_data_df[event_data_df["incident_type"] == "黑天鹅事件"].groupby(by='trade_date').first()
        x_data5 = black_df.index.to_list()
        black_incident = black_df["incident"].to_list()
        y_data5 = [[coordinate_point[v], black_incident[i]] for i, v in enumerate(x_data5)]


        shi_df = event_data_df[event_data_df["incident_type"] == "每日时事"].groupby(by='trade_date').first()
        x_data6 = shi_df.index.to_list()
        shi_incident = shi_df["incident"].to_list()
        y_data6 = [[coordinate_point[v], shi_incident[i]] for i, v in enumerate(x_data6)]

        scatter = draw_scatter(x_data1, y_data1, "政治类")
        scatter2 = draw_scatter(x_data2, y_data2, "经济类")
        scatter3 = draw_scatter(x_data3, y_data3, "行业变革类")
        scatter4 = draw_scatter(x_data4, y_data4, "国际类")
        scatter5 = draw_scatter(x_data5, y_data5, "黑天鹅类")
        scatter6 = draw_scatter(x_data6, y_data6, "每日时事类")

        overlap_kline_line.overlap(scatter)
        overlap_kline_line.overlap(scatter2)
        overlap_kline_line.overlap(scatter3)
        overlap_kline_line.overlap(scatter4)
        overlap_kline_line.overlap(scatter5)
        overlap_kline_line.overlap(scatter6)

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

    def dispose_international_data(self):
        stock_it_price = stock_data.stock_international_index_price_daily(("HSI", "IXIC", "DJI"))
        stock_it_price = stock_it_price[stock_it_price["trade_date"].isin(df["trade_date"].to_list())]
        # stock_it_price.sort_values("trade_date", inplace=True)
        HSI_index = stock_it_price[stock_it_price["security"] == "HSI"]
        IXIC_index = stock_it_price[stock_it_price["security"] == "IXIC"]
        DJI_index = stock_it_price[stock_it_price["security"] == "DJI"]

        HSI_date = HSI_index["trade_date"].to_list()
        HSI_close = HSI_index["close"].to_list()
        IXIC_date = IXIC_index["trade_date"].to_list()
        IXIC_close = IXIC_index["close"].to_list()
        DJI_date = DJI_index["trade_date"].to_list()
        DJI_close = DJI_index["close"].to_list()

        self.international_index_dict = {
            "HSI": {"date": HSI_date, "close": HSI_close},
            "IXIC": {"date": IXIC_date, "close": IXIC_close},
            "DJI": {"date": DJI_date, "close": DJI_close},
        }

    def create_index_line(self, series, x_data, y_data, color="#675bba"):
        line = (
            Line()
                .add_xaxis(x_data)
                .add_yaxis(
                series,
                y_data,
                is_smooth=True,
                color=color,
                label_opts=opts.LabelOpts(is_show=False),
            )
        )
        return line

    def create_sz_line(self):
        sz_line = (
            Line(init_opts=opts.InitOpts(theme='light', width='1600px', height='800px'))
                .add_xaxis(data["times"])
                .add_yaxis('上证指数', data["close"], is_smooth=True, label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                legend_opts=opts.LegendOpts(orient='vertical', pos_top="10%", pos_right='1%'),  # 设置图例的位置
                title_opts=opts.TitleOpts(title="上证叠加国际指数", pos_left="0"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    splitline_opts=opts.SplitLineOpts(is_show=False),  # 分割线配置项,不显示x轴分割线
                    split_number=20,
                    min_="dataMin",
                    max_="dataMax",
                ),
                toolbox_opts=opts.ToolboxOpts(pos_left='right'),  # 工具箱配置项, pos_left设置标题位置
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    type_="log",
                ),
                tooltip_opts=opts.TooltipOpts(  # 提示框配置项
                    trigger="axis",  # 触发类型  'axis': 坐标轴触发  'item': 数据项图形触发
                    axis_pointer_type="cross"  # 指示器类型。'cross'：十字准星指示器
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(  # 区域缩放配置项
                        xaxis_index=[0],  # 联动,是这个控制的。
                        type_="inside",
                        range_start=0,
                        range_end=100
                    )
                ],
            )
        )

        return sz_line

    def create_sz_international_index_chart(self):
        self.dispose_international_data()  # 获取国际指数数据
        line = self.create_index_line("恒生指数", self.international_index_dict["HSI"]["date"], self.international_index_dict["HSI"]["close"])
        line2 = self.create_index_line("纳斯达克指数", self.international_index_dict["IXIC"]["date"], self.international_index_dict["IXIC"]["close"])
        line3 = self.create_index_line("道琼斯工业指数", self.international_index_dict["DJI"]["date"], self.international_index_dict["DJI"]["close"])

        sz_line_chart = self.create_sz_line()
        sz_line_chart = sz_line_chart.overlap(line)
        sz_line_chart = sz_line_chart.overlap(line2)
        sz_line_chart = sz_line_chart.overlap(line3)
        sz_line_chart = self.create_scatter(sz_line_chart)
        return sz_line_chart

    def tab_add_table(self, tab):
        politics_df = event_data_df[event_data_df["incident_type"] == "政治事件"][["create_time", "incident"]]
        table1 = create_table("政治事件", rows_list=politics_df.values.tolist())

        economic_df = event_data_df[event_data_df["incident_type"] == "经济事件"][["create_time", "incident"]]
        table2 = create_table("经济事件", rows_list=economic_df.values.tolist())

        industry_change_df = event_data_df[event_data_df["incident_type"] == "行业变革事件"][["create_time", "incident"]]
        table3 = create_table("行业变革事件", rows_list=industry_change_df.values.tolist())

        international_df = event_data_df[event_data_df["incident_type"] == "国际事件"][["create_time", "incident"]]
        table4 = create_table("国际事件", rows_list=international_df.values.tolist())

        black_df = event_data_df[event_data_df["incident_type"] == "黑天鹅事件"][["create_time", "incident"]]
        table5 = create_table("黑天鹅事件", rows_list=black_df.values.tolist())

        shi_df = event_data_df[event_data_df["incident_type"] == "每日时事"][["create_time", "incident"]]
        table6 = create_table("每日时事事件", rows_list=shi_df.values.tolist())

        tab.add(table1, '政治事件')
        tab.add(table2, '经济事件')
        tab.add(table3, '行业变革事件')
        tab.add(table4, '国际事件')
        tab.add(table5, '黑天鹅事件')
        tab.add(table6, '每日时事事件')
        return tab


if __name__ == "__main__":
    logger = Logger("上证指数回溯事件模型")
    try:
        stock_data = StockData()
        df = stock_data.stock_toshure_index_price_daily("000001.SH")
        df = add_ma_data(df)  # 添加均线数据
        times = df["trade_date"].to_list()
        datas = df[["open", "close", "low", "high", "volume"]].values.tolist()
        data = {"datas": datas, "times": times, "vols": df["volume"].to_list(), "highs": df["high"].to_list(), "close": df["close"].to_list()}
        coordinate_point = dict(zip(data["times"], df["high"].to_list()))

        security = df["security"].to_list()[0]

        # 查询事件数据
        event_data_df = stock_data.read_ods_the_shanghai_event()
        event_data_df = event_data_df[event_data_df["trade_date"].isin(df["trade_date"].to_list())]

        sz_event_back = SZEVENTBACK()
        grid_chart = sz_event_back.draw_chart()
        tab = Tab(page_title="上证指数回溯事件系统")
        tab.add(grid_chart, '上证指数回溯事件K线图')
        tab = sz_event_back.tab_add_table(tab)
        sz_line_chart = sz_event_back.create_sz_international_index_chart()
        tab.add(sz_line_chart, "上证国际指数事件对比")
        tab.render("上证指数_叠加国际指数_对数轴.html")

        logger.info("上证指数回溯事件模型定时任务执行成功")
    except Exception as e:
        send_email(f"上证指数回溯事件模型定时任务执行失败,原因:{e}")
        logger.info(f"上证指数回溯事件模型定时任务执行失败,原因:{e}")
