
from pyecharts import options as opts
from pyecharts.charts import Line


def create_line(x_data, y_data, series_name="图例名字", title="曲线图的名字", color="red"):
    """创建第一根曲线对象,配置此图的基本配置"""
    line = (
        Line(init_opts=opts.InitOpts(width='1800px', height='700px', theme='dark', page_title=title))
            .add_xaxis(xaxis_data=x_data)  # 添加x轴
            .add_yaxis(
            series_name=series_name,
            is_smooth=True,  # 线条样式  , 是否设置成圆滑曲线
            y_axis=y_data,
            # itemstyle_opts=opts.ItemStyleOpts(
            #     color=color,  # 图形的颜色。
            # ),
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.5),
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
                )
            ],
        ).set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    )

    return line
