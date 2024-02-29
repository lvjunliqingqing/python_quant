
from pyecharts import options as opts
from pyecharts.charts import Scatter
from pyecharts.commons.utils import JsCode

tool_js = """function (param) {return param.seriesName + '<br/>'
            +'时间：'+param.data[0]+'<br/>'
            +'事件：'+param.data[2];}"""


def draw_scatter(x_data, y_data, series_name):
    scatter = (
        Scatter()
            .add_xaxis(x_data)
            .add_yaxis(series_name, y_data, label_opts=opts.LabelOpts(is_show=False), symbol="pin", symbol_size=(20, 30))
            .set_series_opts(
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(tool_js))
        )
    )

    return scatter

