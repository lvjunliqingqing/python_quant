from typing import List, Sequence, Union

from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.charts import Kline, Line, Bar, Grid

from pyecharts_demo.k线图案例.draw_scatter import draw_scatter
from pyecharts_demo.k线图案例.k_data import echarts_data


def split_data(origin_data) -> dict:
    datas = []
    times = []
    vols = []
    macds = []
    difs = []
    deas = []
    highs=[]

    for i in range(len(origin_data)):
        highs.append(origin_data[i][4])  # 最高价
        datas.append(origin_data[i][1:])
        times.append(origin_data[i][0:1][0])
        vols.append(origin_data[i][5])
        macds.append(origin_data[i][7])
        difs.append(origin_data[i][8])
        deas.append(origin_data[i][9])
    vols = [int(v) for v in vols]

    return {
        "highs": highs,
        "datas": datas,
        "times": times,
        "vols": vols,
        "macds": macds,
        "difs": difs,
        "deas": deas,
    }


def split_data_part() -> Sequence:
    mark_line_data = []
    tag = 0
    vols = 0
    for i in range(len(data["times"])):
        if data["datas"][i][5] != 0 and tag == 0:
            vols = data["datas"][i][4]
            tag = 1
        if tag == 1:
            vols += data["datas"][i][4]
        if data["datas"][i][5] != 0 or tag == 1:
                try:
                    mark_line_data.append(
                        [
                            {
                                "xAxis": i,
                                "yAxis": float("%.2f" % data["datas"][i][3]),
                                "value": vols,
                            },
                            {
                                "xAxis": i + 10,
                                "yAxis": float("%.2f" % data["datas"][i + 10][3])
                            },
                        ]
                    )
                    vols = data["datas"][i][4]
                    tag = 2
                except:
                    pass
    return mark_line_data


def calculate_ma(day_count: int):
    result: List[Union[float, str]] = []

    for i in range(len(data["times"])):
        if i < day_count:
            result.append("-")
            continue
        sum_total = 0.0
        for j in range(day_count):
            sum_total += float(data["datas"][i - j][1])
        result.append(abs(float("%.2f" % (sum_total / day_count))))
    return result


def draw_chart():
    kline = (
        Kline()
            .add_xaxis(xaxis_data=data["times"])
            .add_yaxis(
            series_name="",
            y_axis=data["datas"],
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ef232a",
                color0="#14b143",
                border_color="#ef232a",
                border_color0="#14b143",
            ),
            markpoint_opts=opts.MarkPointOpts(  # 设置标记点
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值"),
                ]
            ),
            markline_opts=opts.MarkLineOpts(  # 设置线标记点
                label_opts=opts.LabelOpts(
                    position="middle", color="blue", font_size=15
                ),
                data=split_data_part(),
                # symbol具体可选那些需要由echarts中定义决定的,有'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow','none'
                symbol=["circle", "none"],
            ),
        )
            .set_series_opts(  # set_series_opts是系列配置项
            markarea_opts=opts.MarkAreaOpts(is_silent=True, data=split_data_part())  # 标志区域配置项(也就是被红色框选的区域)
        )
            .set_global_opts(  # set_global_opt是全局配置项,具体使用参考pyecharts官网
            title_opts=opts.TitleOpts(title="K线周期图表", pos_left="0"),
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
                    is_show=False, type_="inside", xaxis_index=[0, 0], range_end=100
                ),
                opts.DataZoomOpts(
                    is_show=True, xaxis_index=[0, 1], pos_top="97%", range_end=100
                ),
                opts.DataZoomOpts(is_show=False, xaxis_index=[0, 2], range_end=100),
            ],
            # 三个图(Kline,volume,macd)的坐标信息矩形框设置连在一块
            # axispointer_opts=opts.AxisPointerOpts(
            #     is_show=True,
            #     link=[{"xAxisIndex": "all"}],
            #     label=opts.LabelOpts(background_color="#777"),
            # ),
        )
    )

    kline_line = (
        Line()
            .add_xaxis(xaxis_data=data["times"])
            .add_yaxis(
            series_name="MA5",
            y_axis=calculate_ma(day_count=5),
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(opacity=0.5),
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
    # Overlap Kline + Line
    overlap_kline_line = kline.overlap(kline_line)  # overlap把图叠加
    # 添加散点图
    x_data1 = [data["times"][i] for i in range(len(data["times"])) if i % 9 == 0]
    y_data1 = [data["highs"][i] for i in range(len(data["highs"])) if i % 9 == 0]

    x_data2 = [data["times"][i] for i in range(len(data["times"])) if i % 4 == 0]
    y_data2 = [data["highs"][i] for i in range(len(data["highs"])) if i % 4 == 0]

    scatter = draw_scatter(x_data1, y_data1, "政治类")
    scatter2 = draw_scatter(x_data2, y_data2, "经济类")

    overlap_kline_line.overlap(scatter)
    overlap_kline_line.overlap(scatter2)

    # Bar-1
    bar_1 = (
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

    # MACD图形区域对象
    bar_2 = (
        Bar()
            .add_xaxis(xaxis_data=data["times"])
            .add_yaxis(
            series_name="MACD",
            y_axis=data["macds"],
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

    line_2 = (
        Line()
            .add_xaxis(xaxis_data=data["times"])
            .add_yaxis(
            series_name="DIF",
            y_axis=data["difs"],
            xaxis_index=2,
            yaxis_index=2,
            label_opts=opts.LabelOpts(is_show=False),
        )
            .add_yaxis(
            series_name="DIF",
            y_axis=data["deas"],
            xaxis_index=2,
            yaxis_index=2,
            label_opts=opts.LabelOpts(is_show=False),
        )
            .set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
    )
    # 最下面的柱状图和折线图
    overlap_bar_line = bar_2.overlap(line_2)

    # 最后的 Grid
    grid_chart = Grid(init_opts=opts.InitOpts(width="1400px", height="800px"))

    #  把data["datas"]这个数据渲染到js代码中(增加一个js对象),不支持pandas和numpy数据类型
    # 注意一定要用Grid对象来传递js对象,不然在js代码function中没法获取。
    grid_chart.add_js_funcs("var barData = {}".format(data["datas"]))

    # K线图和 MA5 的折线图
    grid_chart.add(
        overlap_kline_line,
        grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", height="60%"),
    )
    # Volumn 柱状图
    grid_chart.add(
        bar_1,
        grid_opts=opts.GridOpts(
            pos_left="3%", pos_right="1%", pos_top="71%", height="10%"
        ),
    )
    # MACD(DIFS DEAS)
    grid_chart.add(
        overlap_bar_line,
        grid_opts=opts.GridOpts(
            pos_left="3%", pos_right="1%", pos_top="82%", height="14%"
        ),
    )
    grid_chart.render("k_line.html")


if __name__ == "__main__":
    data = split_data(origin_data=echarts_data)
    print(split_data_part())
    draw_chart()
