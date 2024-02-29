
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Tab
from create_table import create_table
from draw_scatter import draw_scatter
from pyecharts_demo.futures_commodity_index.Logger import Logger
from pyecharts_demo.futures_commodity_index.futures_index_data import FuturesIndex
from pyecharts_demo.futures_commodity_index.send_email import send_email
from stock_data import StockData


class CommodityIndexBACK(object):

    def __init__(self):
        super(CommodityIndexBACK, self).__init__()

    def create_scatter(self, overlap_kline_line):  # 添加散点图

        politics_df = self.event_data_df[self.event_data_df["incident_type"] == "政治事件"].groupby(by='trade_date').first()
        x_data1 = politics_df.index.to_list()
        politics_incident = politics_df["incident"].to_list()
        y_data1 = [[self.coordinate_point[v], politics_incident[i]] for i, v in enumerate(x_data1)]
        # x_data1 = [self.times[i] for i in range(len(self.times)) if i % 53 == 0]
        # y_data1 = [[self.e_w_c_i["close"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(self.e_w_c_i)) if i % 53 == 0]


        economic_df = self.event_data_df[self.event_data_df["incident_type"] == "经济事件"].groupby(by='trade_date').first()
        x_data2 = economic_df.index.to_list()
        economic_incident = economic_df["incident"].to_list()
        y_data2 = [[self.coordinate_point[v], economic_incident[i]] for i, v in enumerate(x_data2)]
        # x_data2 = [self.times[i] for i in range(len(self.times)) if i % 54 == 0]
        # y_data2 = [[self.e_w_c_i["close"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(self.e_w_c_i)) if i % 54 == 0]

        industry_change_df = self.event_data_df[self.event_data_df["incident_type"] == "行业变革事件"].groupby(by='trade_date').first()
        x_data3 = industry_change_df.index.to_list()
        industry_change_incident = industry_change_df["incident"].to_list()
        y_data3 = [[self.coordinate_point[v], industry_change_incident[i]] for i, v in enumerate(x_data3)]
        # x_data3 = [self.times[i] for i in range(len(self.times)) if i % 55 == 0]
        # y_data3 = [[self.e_w_c_i["close"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(self.e_w_c_i)) if i % 55 == 0]


        international_df = self.event_data_df[self.event_data_df["incident_type"] == "国际事件"].groupby(by='trade_date').first()
        x_data4 = international_df.index.to_list()
        international_incident = international_df["incident"].to_list()
        y_data4 = [[self.coordinate_point[v], international_incident[i]] for i, v in enumerate(x_data4)]
        # x_data4 = [self.times[i] for i in range(len(self.times)) if i % 56 == 0]
        # y_data4 = [[self.e_w_c_i["close"][i], f"大事件大事件大事件大事件大事件大事件大事件大事件大事件{i}"] for i in range(len(self.e_w_c_i)) if i % 56 == 0]

        black_df = self.event_data_df[self.event_data_df["incident_type"] == "黑天鹅事件"].groupby(by='trade_date').first()
        x_data5 = black_df.index.to_list()
        black_incident = black_df["incident"].to_list()
        y_data5 = [[self.coordinate_point[v], black_incident[i]] for i, v in enumerate(x_data5)]


        shi_df = self.event_data_df[self.event_data_df["incident_type"] == "每日时事"].groupby(by='trade_date').first()
        x_data6 = shi_df.index.to_list()
        shi_incident = shi_df["incident"].to_list()
        y_data6 = [[self.coordinate_point[v], shi_incident[i]] for i, v in enumerate(x_data6)]


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

    def process_custom_commodity_index_data(self):
        self.futures_Index = FuturesIndex()

        self.df_Index = self.futures_Index.read_futures_index()

        self.e_w_c_i = self.df_Index[self.df_Index["index_name"] == "Avg Weight Increase Index"]  # 等权商品指数
        self.c_v_w_i = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index"]  # 持仓金额商品指数
        self.m_w_i = self.df_Index[self.df_Index["index_name"] == "Money Weight Index"]  # 成交金额商品指数
        self.m_w_i_3 = self.df_Index[self.df_Index["index_name"] == "Money Weight Index 3Month"]  # 成交金额商品指数(3个月)
        self.c_v_w_i_3 = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index 3Month"]  # 持仓金额商品指数(3个月)
        self.c_v_w_i_6 = self.df_Index[self.df_Index["index_name"] == "Contract Value Weight Index 6Month"]  # 持仓金额商品指数(6个月)
        self.times = self.e_w_c_i['trade_date'].apply(lambda x: x.strftime("%Y-%m-%d"))  # df中datetime64转字符串
        self.coordinate_point = dict(zip(self.times.to_list(), self.e_w_c_i["close"].to_list()))

        # 查询事件数据
        stock_data = StockData()
        event_data_df = stock_data.read_ods_the_shanghai_event()
        self.event_data_df = event_data_df[event_data_df["trade_date"].isin(self.times.to_list())]

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
            Line(init_opts=opts.InitOpts(theme='light', width='2000px', height='800px'))
                .add_xaxis(self.times)
                .add_yaxis('等权商品指数', self.e_w_c_i["close"], is_smooth=True, label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                legend_opts=opts.LegendOpts(orient='vertical', pos_top="10%", pos_right='1%'),  # 设置图例的位置
                title_opts=opts.TitleOpts(title="自定义商品指数", pos_left="0"),
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

    def create_custom_commodity_index_chart(self):

        self.process_custom_commodity_index_data()

        line = self.create_index_line("持仓金额商品指数", self.times, self.c_v_w_i["close"])
        line2 = self.create_index_line("持仓金额商品指数(3个月)", self.times, self.c_v_w_i_3["close"])
        line3 = self.create_index_line("持仓金额商品指数(6个月)", self.times, self.c_v_w_i_6["close"])
        line4 = self.create_index_line("成交金额商品指数", self.times, self.m_w_i["close"])
        line5 = self.create_index_line("成交金额商品指数(3个月)", self.times, self.m_w_i_3["close"])

        sz_line_chart = self.create_sz_line()
        sz_line_chart = sz_line_chart.overlap(line)
        sz_line_chart = sz_line_chart.overlap(line2)
        sz_line_chart = sz_line_chart.overlap(line3)
        sz_line_chart = sz_line_chart.overlap(line4)
        sz_line_chart = sz_line_chart.overlap(line5)
        sz_line_chart = self.create_scatter(sz_line_chart)
        return sz_line_chart

    def tab_add_table(self, tab):
        politics_df = self.event_data_df[self.event_data_df["incident_type"] == "政治事件"][["create_time", "incident"]]
        table1 = create_table("政治事件", rows_list=politics_df.values.tolist())

        economic_df = self.event_data_df[self.event_data_df["incident_type"] == "经济事件"][["create_time", "incident"]]
        table2 = create_table("经济事件", rows_list=economic_df.values.tolist())

        industry_change_df = self.event_data_df[self.event_data_df["incident_type"] == "行业变革事件"][["create_time", "incident"]]
        table3 = create_table("行业变革事件", rows_list=industry_change_df.values.tolist())

        international_df = self.event_data_df[self.event_data_df["incident_type"] == "国际事件"][["create_time", "incident"]]
        table4 = create_table("国际事件", rows_list=international_df.values.tolist())

        black_df = self.event_data_df[self.event_data_df["incident_type"] == "黑天鹅事件"][["create_time", "incident"]]
        table5 = create_table("黑天鹅事件", rows_list=black_df.values.tolist())

        shi_df = self.event_data_df[self.event_data_df["incident_type"] == "每日时事"][["create_time", "incident"]]
        table6 = create_table("每日时事事件", rows_list=shi_df.values.tolist())

        tab.add(table1, '政治事件')
        tab.add(table2, '经济事件')
        tab.add(table3, '行业变革事件')
        tab.add(table4, '国际事件')
        tab.add(table5, '黑天鹅事件')
        tab.add(table6, '每日时事事件')
        return tab


if __name__ == "__main__":
    logger = Logger("自定义商品指数事件回溯模型")
    try:
        commodity_index_back = CommodityIndexBACK()
        tab = Tab(page_title="自定义商品指数回溯事件系统")
        sz_line_chart = commodity_index_back.create_custom_commodity_index_chart()
        tab.add(sz_line_chart, "自定义商品指数回溯事件")
        tab = commodity_index_back.tab_add_table(tab)
        tab.render("自定义商品指数回溯事件_对数轴.html")

        logger.info("自定义商品指数事件回溯模型定时任务执行成功")

    except Exception as e:
        send_email(f"自定义商品指数事件回溯模型定时任务执行失败,原因:{e}")
        logger.info(f"自定义商品指数事件回溯模型定时任务执行失败,原因:{e}")
