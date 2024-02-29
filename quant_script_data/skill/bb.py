# a = 100
# b = 101
# c = 102
# if 99 < (c & b) < 1000 and 99 < (a & b) < 1000:
#     print("True")


# 打印返回值
# print("name" not in d.keys())
import re
# regex = ".*"
# print(re.match(regex, 'E:\\gext\\ket.txt').group())
#
#
# print(re.match("((\d{3,4})-(\d{6,8}))", "020-12345678").group(2))
# # print(re.match("\\\\\\\\d", b).group())
# print(re.match("\.",'.').group())
# symbol = "rb2005.SHFE"
# print(re.split('\\.',symbol))


# import pandas as pd
#
# key = pd.DataFrame(data={
#     "user": [18, 18, 18, 19, -19, 18, 19, 19],
#     "name": ["江苏", "四川", "北京", "成都", "天津","北京", "成都", "天津"],
#     "age": ["1", "2", "3", "4", "5","6", "7", "8"]
# })
# print(key)
# key = key.groupby(["name"])["user"].sum()
# print(key)


import pandas as pd
#你的df有time索引，df.reset_index(False)去掉索引即可
# df = pd.DataFrame([['2018-03-11 20:00:12', 1, 5], ['2018-03-11 20:00:12', 1, 5], ['2018-03-12 20:00:12', 1, 5]], columns=['date', 'a', 'b',])

# def f(r):
#     r['date'] = r['date'].split(' ')[0]    # 如果是日期类型直接r['date'] = r['date'].date()
#     return r
# print(df)
# df1 = df.groupby('date')["a"].sum()
# print(df1)
# print("长度:", len(df1))
# print(df1[df1 > 1].shape[0])
# from typing import Any, Callable
# class Event:
#     """
#     事件类，有两个成员，type(字符串类型):事件的类型,data(任意类型):数据对象。
#     """
#
#     def __init__(self, type: str, data: Any = None):
#         """"""
#         self.type = type
#         self.data = data
#
#
# # 定义要在事件引擎中使用的处理程序函数。
# HandlerType = Callable[[Event], None]
# print(HandlerType)
import talib
import numpy as np

# close_price = np.zeros(100)
# length = len(close_price)
# print([np.nan] * length)



def RSI(close_list:list, periods=2):
    length = len(close_list)

    rsies = [np.nan]*length
    # 数据不够，直接return
    if length <= periods:
        return rsies
    # 用于快速计算；
    up_avg = 0
    down_avg = 0

    # 首先计算第一个RSI，用前periods+1个数据，构成periods个价差序列;
    first_close_list = close_list[:periods+1]
    for i in range(1, len(first_close_list)):
        # 价格上涨;
        if first_close_list[i] >= first_close_list[i-1]:
            up_avg += first_close_list[i] - first_close_list[i-1]
        # 价格下跌;
        else:
            down_avg += first_close_list[i-1] - first_close_list[i]
    up_avg = up_avg / periods
    down_avg = down_avg / periods

    try:
        rs = up_avg / down_avg
    except:
        rs = 0
    rsies[periods] = 100 - 100/(1+rs)

    # 后面的将使用快速计算；
    for j in range(periods+1, length):
        up = 0
        down = 0
        if close_list[j] >= close_list[j-1]:
            up = close_list[j] - close_list[j-1]
            down = 0
        else:
            up = 0
            down = close_list[j-1] - close_list[j]
        # 类似移动平均的计算公式;
        up_avg = (up_avg*(periods - 1) + up)/periods
        down_avg = (down_avg*(periods - 1) + down)/periods
        try:
            rs = up_avg/down_avg
        except:
            rs = 0
        rsies[j] = 100 - 100/(1+rs)
    print(rsies[-1])
    return rsies




def rsi(close_list, n, array=False):
    """
    RSI指标
    """
    result = talib.RSI(close_list, n)
    if array:
        return result
    print(result[-1])
    return result[-1]

t = [56.24, 56.82, 56.94, 57.97, 58.09, 58.02, 59.65, 60.17, 62.39, 60.17, 62.39, 62.39, 60.17, 62.39]

# result = RSI(t, 2)

result2 = rsi(np.array(t), 2)
# t1 = [338,339,340,401,401,334,335,336,337,338,339,340,401]
# result = RSI(t1, 2)
# def numberOfNonNans(data):
#     count = 0
#     for i in data:
#         if not np.isnan(i):
#             count += 1
#     return count
# count = numberOfNonNans(result)
# print(count)
# print(len(result))
# a = np.zeros(100)
# print(len(np.zeros(100)), type(np.zeros((100))))
# b = np.maximum(a, 2)
# print(b)

# data = np.zeros(100)
# print(data)
# 简单方法
# print(sum(data == 4))