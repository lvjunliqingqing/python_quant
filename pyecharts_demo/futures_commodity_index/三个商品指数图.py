# import sys
# sys.path.append("E:/jobs/designer_demo")
from copy import copy
from datetime import datetime

from pyecharts import options as opts
from pyecharts.charts import Line, Grid, Page
import pandas as pd
from pyecharts.components import Table

from pyecharts_demo.futures_commodity_index.Logger import Logger
from pyecharts_demo.futures_commodity_index.futures_index_data import FuturesIndex
from pyecharts_demo.futures_commodity_index.send_email import send_email


def split_data(origin_data) -> dict:
    datas = []
    times = []

    for i in range(len(origin_data)):
        datas.append(origin_data[i][1])
        times.append(origin_data[i][0])

    return {
        "datas": datas,
        "times": times,
    }


class CommodityIndex(object):

    def __init__(self):
        super(CommodityIndex, self).__init__()

    def create_one_line(self):
        """创建第一根曲线对象,配置此图的基本配置"""
        one_line = (
            Line()
                .add_xaxis(xaxis_data=self.data["times"])  # 添加x轴
                .add_yaxis(
                series_name="等权商品指数",
                is_smooth=True,  # 线条样式  , 是否设置成圆滑曲线
                y_axis=self.data["datas"],
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#9900ff",  # 图形的颜色。
                ),
                linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.5),
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title="期货商品指数图(自构建的)", pos_left="0"),
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

        return one_line

    def create_k_line_line(self, xaxis_data, series_name, y_axis):
        """创建曲线图对象"""
        line = (
            Line()
                .add_xaxis(xaxis_data=xaxis_data)  # 添加x轴
                .add_yaxis(  # 添加y轴
                series_name=series_name,  # 指定y轴名字
                y_axis=y_axis,  # y轴的数据
                is_smooth=True,  # 是否平滑曲线
                linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.5),  # 线条设置项,opacity：透明度, width控制曲线的宽度
                label_opts=opts.LabelOpts(is_show=False),  # 坐标轴标签配置项
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(  # 坐标轴配置项
                    type_="category",  # 坐标轴类型,'value': 数值轴，适用于连续数据。'category': 类目轴，适用于离散的类目数据 'log' 对数轴。适用于对数数据。 'time': 时间轴，适用于连续的时序数据
                    grid_index=1,  # 轴所在的 grid 的索引
                    axislabel_opts=opts.LabelOpts(is_show=False),  # 坐标轴标签配置项
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    split_number=3,  # 对于连续型数据，自动平均切分成几段。默认为5段。连续数据的范围需要 max 和 min 来指定
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),  # 坐标轴刻度配置项
                    splitline_opts=opts.SplitLineOpts(is_show=False),  # 分割线配置项
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
            )
        )
        return line

    def draw_chart(self):
        e_w_c_i_line = self.create_one_line()
        c_v_w_i_line = self.create_k_line_line(self.data["times"], "持仓金额商品指数", self.c_v_w_i["close"])
        c_v_w_i_line_3 = self.create_k_line_line(self.data["times"], "持仓金额商品指数(3个月)", self.c_v_w_i_3["close"])
        c_v_w_i_line_6 = self.create_k_line_line(self.data["times"], "持仓金额商品指数(6个月)", self.c_v_w_i_6["close"])
        m_w_i_line = self.create_k_line_line(self.data["times"], "成交金额商品指数", self.m_w_i["close"])
        m_w_i_line_3 = self.create_k_line_line(self.data["times"], "成交金额商品指数(3个月)", self.m_w_i_3["close"])
        # 三个图形(line + line+line)
        e_w_c_i_line.overlap(c_v_w_i_line)
        e_w_c_i_line.overlap(c_v_w_i_line_3)
        e_w_c_i_line.overlap(c_v_w_i_line_6)
        e_w_c_i_line.overlap(m_w_i_line_3)
        overlap_kline_line = e_w_c_i_line.overlap(m_w_i_line)

        return self.grid_chart(overlap_kline_line)

    def grid_chart(self, overlap_kline_line):
        # 创建网格图形对象
        grid_chart = Grid(init_opts=opts.InitOpts(width="1800px", height="800px", page_title="三个商品指数图", bg_color='rgba(255, 255, 255, 0.4)'))  # InitOpts:初始化配置项

        # K线图和 MA5 的折线图
        grid_chart.add(
            overlap_kline_line,
            grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", height="60%"),
        )
        return grid_chart
        # grid_chart.render("三个商品指数图.html")

    def process_data(self):
        self.futures_Index = FuturesIndex()

        self.df_Index = self.futures_Index.read_futures_index()
        self.e_w_c_i = self.df_Index[self.df_Index["index_name"] == "Avg Weight Increase Index"]  # 等权商品指数
        self.c_v_w_i = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index"]  # 持仓金额商品指数
        self.m_w_i = self.df_Index[self.df_Index["index_name"] == "Money Weight Index"]  # 成交金额商品指数
        self.m_w_i_3 = self.df_Index[self.df_Index["index_name"] == "Money Weight Index 3Month"]  # 成交金额商品指数(3个月)
        self.c_v_w_i_3 = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index 3Month"]  # 持仓金额商品指数(3个月)
        self.c_v_w_i_6 = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index 6Month"]  # 持仓金额商品指数(6个月)

        self.df = pd.DataFrame()
        self.df["times"] = self.e_w_c_i['trade_date'].apply(lambda x: x.strftime("%Y-%m-%d"))  # df中datetime64转字符串
        self.df["e_w_c_i"] = self.e_w_c_i["close"]
        echarts_data = self.df.values.tolist()
        self.data = split_data(origin_data=echarts_data)

        self.process_table_data()

    def process_table_data(self):
        """处理table表所需要的数据"""
        self.futures_price_df = self.futures_Index.read_futures_price_daily(self.df_Index['trade_date'].max())  # 期货日行情数据
        futures_tuple = tuple(self.futures_price_df['security'].tolist())
        self.futures_contract_info_df = self.futures_Index.read_futures_contract_info(futures_tuple)  # 查询合约数据为了拿到合约乘数

        self.futures_price_df.sort_values("security", inplace=True)  # 按security排序是为了计算持仓市值
        self.futures_contract_info_df.sort_values("security", inplace=True)

        self.futures_price_df["contract_value"] = self.futures_price_df["open_interest"] * self.futures_price_df["close"] * self.futures_contract_info_df["multiplier"]  # 计算持仓市值

        self.futures_price_df["change_pct"] = self.futures_price_df["change_pct"] * 100  # 换算成百分点,需要乘以100

        self.futures_base_info = self.futures_Index.read_futures_base_info(futures_tuple)
        self.futures_base_info.sort_values("security", inplace=True)

        self.futures_price_df["display_name"] = self.futures_base_info["display_name"]  # 获取合约的名称

        self.futures_price_df = self.futures_price_df[["security", "trade_date", "money", "change_pct", "contract_value", "display_name"]]  # 处理掉不需要的列

    def get_table_data(self, sort_fields="change_pct", ascending=False, num=10, columns=["display_name", "trade_date", "change_pct", "contribution"], decimal_point=4):
        """获取表格需要的数据,返回值是二维数组 [[]]"""

        today_date = datetime.now()
        if sort_fields == "contract_value":
            futures_customize_index_weight_df = self.futures_Index.read_futures_customize_index_weight("Contract Value Weight Index 3Month", today_date)
        elif sort_fields == "money":
            futures_customize_index_weight_df = self.futures_Index.read_futures_customize_index_weight("Money Weight Index 3Month", today_date)

        if sort_fields in ["contract_value", "money"]:  # 获取权重值
            # 如果发现列和列计算时,发现有nan值产生,去检查两个df对象的索引值是否一样对应,不对应就会产生nan值,如果其中一个df进行filter操作,最好用reset_index进行重新生成索引。
            futures_price_df = copy(self.futures_price_df[self.futures_price_df["security"].isin(futures_customize_index_weight_df["security"].tolist())]).reset_index(drop=True)
            futures_price_df.sort_values("security", inplace=True)
            futures_customize_index_weight_df.sort_values("security", inplace=True)

            weighted_value = futures_customize_index_weight_df["weight"]  # 权重值(持仓金额或成交金额)

        else:
            futures_price_df = copy(self.futures_price_df)
            weighted_value = 1 / len(self.futures_price_df)  # 权重值(等权)

        futures_price_df["contribution"] = futures_price_df["change_pct"] * weighted_value  # 计算贡献度

        data_df = futures_price_df.sort_values(by=sort_fields, ascending=ascending).head(num).reset_index(drop=True)[columns].round(decimal_point)
        data_df.insert(0, "serial_number", data_df.index + 1)  # 插入序号列
        return data_df.values.tolist()

    def table_chart(self, table_name, rows_data) -> Table:
        table = Table()
        headers = ["序号", "名称", "日期", "涨跌幅", "贡献度"]
        table.add(headers, rows_data).set_global_opts(
            title_opts=opts.ComponentTitleOpts(title=table_name)
        )
        return table

    def create_page_chart(self):
        self.process_data()

        index_grid = self.draw_chart()

        rows_data = self.get_table_data()
        table = self.table_chart("等权指数涨幅前10", rows_data)
        rows_data1 = self.get_table_data(ascending=True)
        table1 = self.table_chart("等权指数跌幅前10", rows_data1)
        rows_data2 = self.get_table_data("contract_value")
        table2 = self.table_chart("持仓金额指数前10", rows_data2)
        rows_data3 = self.get_table_data("money")
        table3 = self.table_chart("成交金额指数前10", rows_data3)

        page = Page(layout=Page.DraggablePageLayout, page_title="三个商品指数图")
        page.add(
            index_grid,
            table,
            table1,
            table2,
            table3
        )
        page.render("三种商品指数图.html")


if __name__ == "__main__":
    logger = Logger("三个商品指数定时任务")
    try:
        CommodityIndex().create_page_chart()
        logger.info("三个商品指数定时任务执行成功")
    except Exception as e:
        send_email(f"三个商品指数定时任务执行失败,原因:{e}")
        logger.info(f"三个商品指数定时任务执行失败,原因:{e}")
