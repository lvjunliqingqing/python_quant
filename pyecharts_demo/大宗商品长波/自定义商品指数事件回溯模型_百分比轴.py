from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid, Tab
from pyecharts.commons.utils import JsCode
from calculate_ma import add_ma_data
from create_table import create_table
from draw_scatter import draw_scatter
from stock_data import StockData


js_code = JsCode("""
                    function(params) {
                        var colorList;
                        if (barData[params.dataIndex][1] > barData[params.dataIndex][0]) {
                            colorList = 2;
                        } else {
                            colorList = 1;
                        }
                        console.log(barData[params.dataIndex][1]);
                        return colorList;
                    }
                """)

js_code3 = JsCode("""
                    function(params) {
                        console.log(params);
                        console.log(barData);
                        return params
                    }
                """)

js_code1 = JsCode(
                """
                function (params) {
                console.log(params.value);
                console.log(params.seriesName);
                console.log(params.name);
                return 1;
                }
                """
            )


js_code2 = JsCode("""
                function(params){
                    console.log(params.seriesName);
                    console.log([1,2,4,5]);
                    return 1;
                }
            """)



class SZEVENTBACK(object):

    def __init__(self):
        self.international_index_dict = {}

    def create_scatter(self, overlap_kline_line):  # 添加散点图
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

    def create_index_line(self, series, x_data, y_data, yaxis_index, color="#675bba"):
        line = (
            Line()
                .add_xaxis(x_data)
                .add_yaxis(
                series,
                y_data,
                yaxis_index=yaxis_index,
                is_smooth=True,
                color=color,
                label_opts=opts.LabelOpts(is_show=False),
            )
        )
        return line

    def create_sz_line_with_multiple_axis(self):
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
                    type_="category",
                    axislabel_opts=opts.LabelOpts(
                        formatter=js_code3,
                        # formatter="{value}%"
                    ),
                    interval=5
                ),
                tooltip_opts=opts.TooltipOpts(  # 提示框配置项
                    trigger="axis",  # 触发类型  'axis': 坐标轴触发  'item': 数据项图形触发
                    axis_pointer_type="cross"  # 指示器类型。'cross'：十字准星指示器
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(  # 区域缩放配置项
                        xaxis_index=[0],  # 联动,是这个控制的。
                        # yaxis_index=[0, 1, 2, 3],  # 这里有个坑,当有多y轴时,这里需要把所有y轴传进去。
                        type_="inside",
                        range_start=0,
                        range_end=100
                    )
                ],
            )
        )

        # 添加一个Y轴(默认为轴一个编号,从0开始,一直累加。)
        # sz_line.extend_axis(yaxis=opts.AxisOpts(is_show=False, position="right", offset=70))  # 坐标轴隐藏
        # sz_line.extend_axis(yaxis=opts.AxisOpts(is_show=False, position="right", offset=-60))
        # sz_line.extend_axis(yaxis=opts.AxisOpts(is_show=False))

        return sz_line

    def create_sz_international_index_chart(self):
        self.dispose_international_data()  # 获取国际指数数据
        line = self.create_index_line("恒生指数", self.international_index_dict["HSI"]["date"], self.international_index_dict["HSI"]["close"], 1)
        line2 = self.create_index_line("纳斯达克指数", self.international_index_dict["IXIC"]["date"], self.international_index_dict["IXIC"]["close"], 2)
        line3 = self.create_index_line("道琼斯工业指数", self.international_index_dict["DJI"]["date"], self.international_index_dict["DJI"]["close"], 3)

        sz_line_chart = self.create_sz_line_with_multiple_axis()
        # sz_line_chart = sz_line_chart.overlap(line)
        # sz_line_chart = sz_line_chart.overlap(line2)
        # sz_line_chart = sz_line_chart.overlap(line3)
        # sz_line_chart = self.create_scatter(sz_line_chart)
        return sz_line_chart

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
    data = {"datas": datas, "times": times, "vols": df["volume"].to_list(), "highs": df["high"].to_list(), "close": df["close"].to_list()}
    security = df["security"].to_list()[0]
    sz_event_back = SZEVENTBACK()
    tab = Tab(page_title="自定义商品指数回溯事件系统")
    sz_line_chart = sz_event_back.create_sz_international_index_chart()

    grid_chart = Grid(init_opts=opts.InitOpts(width="1400px", height="800px"))
    grid_chart.add_js_funcs("var barData = {}".format(data["datas"]))
    # K线图和 MA5 的折线图
    grid_chart.add(
        sz_line_chart,
        # grid_opts=opts.GridOpts(pos_left="6%", pos_right="1%", height="80%"),
        grid_opts=opts.GridOpts(pos_left="6%"),
    )

    tab.add(grid_chart, "自定义商品指数回溯事件")
    tab = sz_event_back.tab_add_table(tab)
    tab.render("自定义商品指数回溯事件_百分比轴.html")
