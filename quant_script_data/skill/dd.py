# 查询贵州茅台2015年之后公告的母公司利润表数据，取出母公司利润表中本期的营业总收入，归属于母公司所有者的净利润
import base64
import pandas as pd
# from jqdatasdk import *
#
# auth("18601364608", "Lvjun123")
# q = query(finance.STK_INCOME_STATEMENT_PARENT.company_name,
#           finance.STK_INCOME_STATEMENT_PARENT.code,
#           finance.STK_INCOME_STATEMENT_PARENT.pub_date,
#           finance.STK_INCOME_STATEMENT_PARENT.report_date,
#           finance.STK_INCOME_STATEMENT_PARENT.total_operating_revenue,
#           finance.STK_INCOME_STATEMENT_PARENT.np_parent_company_owners).filter(
#     finance.STK_INCOME_STATEMENT_PARENT.code == '000651.XSHE',
#     finance.STK_INCOME_STATEMENT_PARENT.report_date >= '2020-03-30',
#     finance.STK_INCOME_STATEMENT_PARENT.report_type == 0).limit(20)
# df = finance.run_query(q)
# df.to_csv("./finance.STK.csv", encoding="utf-8", index=False)
# print(df)

# 获取沪深300指数
# stocks_300 = get_index_stocks('000300.XSHG')
# df = pd.read_csv("the_stock_selected.csv")
# count = 0
# for i in df["code"]:
#     if i in stocks_300:
#         count += 1
# print(count)
# print(stocks_300)

# # 获取中正100所有股票的代码
# panel = get_index_stocks('000903.XSHG')
# print(panel, len(panel))


# # 获取上证50所有股票的代码
# panel = get_index_stocks('000016.XSHG')
# print(panel, len(panel))


# q = query(valuation.turnover_ratio,
#               valuation.market_cap,
#               indicator.eps
#             ).filter(valuation.code.in_(['000001.XSHE', '600000.XSHG']))
#
# panel = get_fundamentals_continuously(q, end_date='2020-08-25', count=5)
# print(panel.minor_xs('600000.XSHG'))

# ret = get_fundamentals(query(valuation), date="2020-08-26")
# print(ret)

class A(object):
    name = ""
    age = 102

    def __init__(self):
        self.get_age()

    def get_age(self):
        self.age += 1
        print(self.age)


# class B(A):
#     name = "lvjun"
#     age = 100

    # def __init__(self):
    #     print("hehe")
    #     super(B, self).__init__()
    # def get_age(self):
    #     print("niubi")
    #     super(B, self).get_age()


# print(B.age)
#
#
# b = B()
# print(b.__init__())
# a = A()
# print()
# b.get_name()


# class Color:
#     red = 'red'
#
#     def __getattr__(self, item):
#         # 在实例没有item属性的时候，调用该方法
#         print("getattr is being called")
#         return 'whatever'
#
#     def __getattribute__(self, item):
#         # 实例有没有item属性，都会调用该方法
#         print("getattribute is being called")
#         return super().__getattribute__(item)
#
#
# color = Color()
# print(color.red)
# print(color.blue)
