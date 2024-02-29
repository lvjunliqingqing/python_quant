
from pyecharts import options as opts
from pyecharts.components import Table


def create_table(tile, rows_list=[]):
    table = Table()
    headers = ["时间", "事件"]
    # rows = [
    #     ["2022-03-11", "台湾团结联盟参拜靖国神社"],
    #     ["2022-03-12", "台湾与诺鲁建交"],
    #     ["2022-03-13", "中华民国任务型国代选举举行"],
    #     ["2022-03-14", "国民大会复决通过修宪案"],
    #     ["2022-03-15", "中国国民党党主席选举"],
    #     ["2022-03-16", "云南证劵关闭"],
    #     ["2022-03-17", "央行调高个人房贷利率"],
    #     ["2022-03-18", "南方证劵关闭"],
    #     ["2022-03-19", "伊核危机波澜不断"]
    # ]
    # if rows_list:
    rows = rows_list
    table.add(headers, rows).set_global_opts(
        title_opts=opts.ComponentTitleOpts(title=tile)
    )
    return table
