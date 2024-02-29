from pyecharts import options as opts
from pyecharts.charts import Bar, Line
from pyecharts.commons.utils import JsCode


def draw_profit_loss_details(x_data, y_data, y_data2, title="图的标题", series_name="图例名字"):
    """创建bar+line(曲线和柱状图-双y轴)"""
    bar = (
        Bar(init_opts=opts.InitOpts(width='1600px', height='700px', theme='dark'))
            .add_xaxis(x_data)
            .add_yaxis(series_name, y_data, yaxis_index=0)
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
            # 设置缩放功能
            datazoom_opts=opts.DataZoomOpts(type_='inside',
                                            range_start=0,  # 设置起止位置，50%-100%
                                            range_end=100)
        )
            .set_series_opts(
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
                    ),
                    opacity=0.3
                ),
            label_opts=opts.LabelOpts(is_show=False),  # 隐藏文字(数字)
        )
    )

    # 添加一个Y轴
    bar.extend_axis(yaxis=opts.AxisOpts())
    line = Line()
    line.add_xaxis(x_data)
    # 将line数据通过yaxis_index指向后添加的Y轴
    line.add_yaxis('净值', y_data2, yaxis_index=1, is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=2, color='red'))  # is_smooth是否平滑曲线, 设置线宽。
    line.set_series_opts(label_opts=opts.LabelOpts(is_show=False))  # 隐藏文字(数字)
    bar.overlap(line)

    return bar
