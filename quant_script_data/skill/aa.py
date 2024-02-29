import platform
import string
import time
from collections import defaultdict
from enum import Enum

from jqdatasdk import *
import datetime

# class Exchange(Enum):
#     CFFEX = "CFFEX"
#     SHFE = "SHFE"
#     CZCE = "CZCE"
#     DCE = "DCE"

# cl = Exchange("CFFEX")
#
# print(cl.value)  # CFFEX

# a = 1
# b = 2
# assert a == b
# class Person:
#     def PrintName(self):
#         print('Is a Person')
#     def PrintHello(self):
#         print('Hello, world')
#
#
# per = Person()
# per.PrintName()
# print(True) if hasattr(per, 'PrintName') else print(False)


# import datetime
# def The_last_day_of_last_year(end_date, n=1):
#     """获取n年前的最后一天"""
#     time_rel = datetime.datetime.strptime(end_date, '%Y-%m-%d')
#     next_month = 12
#     next_day = 31
#     next_time = datetime.datetime(time_rel.year - n, next_month, next_day).date()
#     print(next_time, type(next_time))
#     return next_time
#
# The_last_day_of_last_year("2020-2-29", n=5)


# def add_parameters(params={}, **kwargs):
#     params.update(kwargs)
#     print(params)
#
#
#
# add_parameters(f1=1, f2=3, f3=9)
# def equity_screener_duplicated_code(symbol, params={}, **kwargs):
#     params = {}
#     params.update(**kwargs)
#     # row = {"money": 12323, "age": 42342}
#     row = {}
#     for k, v in params.items():
#         row['k'] = v
#     print(row)
#
#
# equity_screener_duplicated_code(22, money=1223.232)


# auth("18601364608","Lvjun123")

# q = query(
#     indicator
# ).filter(
#     indicator.code == '000538.XSHE'
# )
# df = get_fundamentals(q, statDate='2019')
# df.to_csv("./roe_test.csv", encoding="utf-8", index=False)
# # # 打印出总市值
# # # print(df['roe'], df['day'])
# # print("----------------------------")
# print(df)
# # print(q)
# stock_list = ['000001.XSHE', '000002.XSHE', "000750.XSHE"]
# d = get_industry(stock_list, date="2020-08-17")
# print(d, type(d), len(d))
# for i in d:
#     print(i)
#     print(d[i]["zjw"]["industry_name"])
# d1 = get_industry("000002.XSHE", date="2020-08-17")
# print(d1)
# d2 = get_industry("000750.XSHE", date="2020-08-17")
# if d2["000750.XSHE"]["sw_l1"]["industry_name"]=="非银金融I":
#     print(80)
# a = "1207"
# print(a.rjust(10, '0'))

#
# class Exchange(Enum):
#     """
#     Exchange.
#     """
#     # Chinese
#     XSHE = "SZSE"         # China Financial Futures Exchange
#     SHFE = "SHFE"           # Shanghai Futures Exchange
#     CZCE = "CZCE"           # Zhengzhou Commodity Exchange
#     DCE = "DCE"             # Dalian Commodity Exchange
#     INE = "INE"             # Shanghai International Energy Exchange
#     SSE = "SSE"             # Shanghai Stock Exchange
#     SGE = "SGE"             # Shanghai Gold Exchange
#     WXE = "WXE"             # Wuxi Steel Exchange
#
# vt_symbols = "600036.SSE"
# symbol, exchange = vt_symbols.split(".")
# print(exchange)
#
# print(datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
#
# if datetime.datetime.strptime("2020-09-15 17:10:37", "%Y-%m-%d %H:%M:%S") < datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S").replace(hour=0, minute=0, second=0):
#     print(type(datetime.datetime.strptime("2020-09-15 17:10:37", "%Y-%m-%d %H:%M:%S")))
#
# from copy import copy
# # import copy
# list1 = [1, [1, 2, 3], 3, 4]
# list2 = copy(list1)
# list3 = list1
# list1[1][1] = 999
# list1[0] = 99
# print("list3：", list3, id(list3))
# print("list2：", list2, id(list2))
# print("list1：", list1, id(list1))


# # 批量插入数据库数据,有则更新,无则追加
# import pymysql
# import numpy as np
# import pandas as pd
#
# conn = pymysql.connect(
#     host='192.168.0.250',
#     port=3306,
#     user='stock',
#     passwd='123456',
#     db='stock',
#     charset='utf8'
# )
# # 游标
# cur = conn.cursor()
# trade_date = datetime.datetime.now().date()
# df = pd.DataFrame([['合肥', 12, 110, trade_date], ['北京5', 1224, 112, trade_date], ['北金', 113, 113, trade_date], ['上海', 100, 116, trade_date]], columns=['name', 'age', 'tel', 'trade_date'])
# train_data = np.array(df)  # np.ndarray()
# train_x_list = train_data.tolist()  # list
# trade_date1 = trade_date - datetime.timedelta(days=1)
# table = "stock_student"
# sql = "insert into {}(name,age,tel,trade_date) values(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE age=values(age),trade_date='{}'".format(table, trade_date1)
# print(sql)
# ret = cur.executemany(sql, train_x_list)  # ret=0:数据库已存在,无需插入。ret=1：插入成功,ret=2:更新成功,ret=3：部分插入成功部分更新成功。
# print(ret)
# conn.commit()
# conn.close()

if str(datetime.datetime.now().time()) > "15:00" and 3 > 2 or 4 > 5:
    print(datetime.datetime.now().time())



# import pandas as pd
# df1 = pd.DataFrame([{'col1': 'a', 'col2': 1}, {'col1': 'b', 'col2': 2}])
# df2 = pd.DataFrame([{'col1': 'a', 'col3': 11}, {'col1': 'c', 'col3': None}])
#
# data = pd.merge(left=df1, right=df2, how='left', left_on='col1', right_on='col1')
#
# # 将NaN替换为0
# print(df2)
# print(df2.fillna(-0.0, inplace=True))
# print(df2)
# print(data)