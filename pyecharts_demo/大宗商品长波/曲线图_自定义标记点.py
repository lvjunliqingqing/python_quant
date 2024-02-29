from pyecharts.charts import *
from pyecharts import options as opts
import random

x_data = ["2010/10/{}".format(i + 1) for i in range(100)]

# 随机生成点数据
y_data = [i + random.randint(10, 20) for i in range(len(x_data))]


def line_with_custom_mark_point():
    line = (
        Line(init_opts=opts.InitOpts(theme='light', width='1400px', height='900px'))
        .add_xaxis(x_data)
        .add_yaxis('', y_data, is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=2, color='black'))  # 设置线条样式以及颜色以及是否平滑
        .set_global_opts(
            title_opts=opts.TitleOpts(title="大宗商品长波"),
            # 设置缩放功能
            datazoom_opts=opts.DataZoomOpts(type_='inside',
                                            range_start=0,  # 设置起止位置，50%-100%
                                            range_end=50))
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),  # 隐藏文字(数字)
            markpoint_opts=opts.MarkPointOpts(
                label_opts=opts.LabelOpts(position="inside Top", color="black", font_size=13, rotate=80, font_weight="bold"),
                symbol_size=(3, 100),
                data=[
                    # opts.MarkPointItem(name="重要事件标记点", coord=[x_data[2], y_data[2]], value="抗日战争", symbol_size=(80, 100)),
                    # opts.MarkPointItem(name="重要事件标记点", coord=[x_data[4], y_data[4]], value="内战", symbol_size=(40, 100)),
                    opts.MarkPointItem(name="重要事件标记点", coord=[x_data[2], y_data[2]], value="我是吕军,湖南邵阳人,今年31岁,从事量化交易工作",
                                       itemstyle_opts=opts.ItemStyleOpts(color="red")),
                    opts.MarkPointItem(name="重要事件标记点", coord=[x_data[4], y_data[4]], value="内战"),  # 自定义标记点
                ]),
            markarea_opts=opts.MarkAreaOpts(  # 设置标记区域
                label_opts=opts.LabelOpts(position="inside Top", color="black", font_size=13, font_weight="bold"),
                itemstyle_opts=opts.ItemStyleOpts(color="gray", opacity=0.5),
                data=[
                    opts.MarkAreaItem(name="第一次工业革命", x=(x_data[2], x_data[5])),
                    opts.MarkAreaItem(name="第二次工业革命", x=(x_data[20], x_data[40])),
                ]
            )
        )
    )

    return line


chart = line_with_custom_mark_point()
chart.render("曲线图_自定义标记点.html")

