from pyecharts import options as opts
from pyecharts.charts import Bar


def create_histogram(x_data, x_data2, y_data, d_tp, file_name="文件名", series_name="图例名字", title="图的标题"):
    """绘制直方图"""
    y = []
    for idx, item in enumerate(x_data):
        if item <= 0:
            y.append(
                opts.BarItem(
                    name=item,
                    value=y_data[idx],
                    itemstyle_opts=opts.ItemStyleOpts(color="#00ff33"),
                )
            )
        else:
            y.append(
                opts.BarItem(
                    name=item,
                    value=y_data[idx],
                    itemstyle_opts=opts.ItemStyleOpts(color="#ffff33"),
                )
            )
    x_data = [str(x_data2[index])+"至"+str(value) for index, value in enumerate(x_data)]
    if d_tp['mean']:
        v_f = (d_tp['std'] / d_tp['mean'], 2)
    else:
        v_f = "均值为0,无法计算"

    bar = (
            Bar(init_opts=opts.InitOpts(width='1400px', height='800px', theme='dark', page_title=file_name))
            .add_xaxis(x_data)
            .add_yaxis(series_name, y, category_gap=0)
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
            )
            .set_series_opts(
                # label_opts=opts.LabelOpts(is_show=False),  # 隐藏文字(数字)
                markline_opts=opts.MarkLineOpts(
                    data=[opts.MarkLineItem(x=d_tp['x_index'], name=f"均值={d_tp['mean']},标准差={d_tp['std']},中位数={d_tp['median']},变异系数={v_f}，索引位置为")],
                ),
            )
            # .render(f"{file_name}.html")
        )
    return bar

