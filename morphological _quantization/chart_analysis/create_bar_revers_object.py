from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode


def create_bar_revers(x_data, y_data,  series_name="图例名称", title="图的标题", yaxis_name="y轴名称", xaxis_name="x轴名称"):
    """创建xy反转的柱状图对象"""
    bar = (
        Bar(init_opts=opts.InitOpts(width='1000px', height='2000px', theme='dark', page_title=title))
            .add_xaxis(x_data)
            .add_yaxis(series_name, y_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                # 设置缩放功能
                datazoom_opts=opts.DataZoomOpts(type_='inside',
                                                range_start=0,  # 设置起止位置，50%-100%
                                                range_end=100),
                yaxis_opts=opts.AxisOpts(name=yaxis_name),
                xaxis_opts=opts.AxisOpts(name=xaxis_name)
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
                    )
                ),
                label_opts=opts.LabelOpts(is_show=False)
        )
    )
    bar.reversal_axis()  # 让xy反转
    return bar

