import copy
import random
import pandas as pd
import talib
import numpy as np

from data.commission import commission_map
from data.contract_multiplier import ContractMultiplier
from data.price_pick import ContractPricePick


def GBK2312():
    """随机生成4个中文字符串"""
    str_temp = ""
    for i in range(4):
        head = random.randint(0xb0, 0xf7)
        body = random.randint(0xa1, 0xf9)  # 在head区号为55的那一块最后5个汉字是乱码,为了方便缩减下范围
        val = f'{head:x}{body:x}'
        str_temp += copy.deepcopy(bytes.fromhex(val).decode('gb2312'))
    return str_temp


def num_map_index_position(a_list, b_num):
    """
    给定一个数和排序好的list,找出刚好大于这个数的list元素的索引位置
    a_list:list
    b_num:数
    """
    target_num = min(a_list, key=lambda x: abs(x - b_num))
    if target_num < b_num:
        return a_list.index(target_num) + 0.5
    elif target_num > b_num:
        return a_list.index(target_num) - 0.5
    else:
        return a_list.index(target_num)


def interval_statistics(series, n=100):
    """
    区间自动划分以及统计每个区间的个数
    series:Series类型
    """
    series = series.dropna()  # 缺失值处理
    df = pd.DataFrame()
    # 等分价格为n个区间
    quartiles, bins = pd.cut(series, n, retbins=True)
    # 获取分区间刻度,为了添加0,再按这个列表再重新划分。
    bins_list = list(bins)
    bins_list.append(0)
    bins_list.sort()
    age_groups, bins2 = pd.cut(series, bins_list, retbins=True)
    cut_series = age_groups.value_counts()  # 分区间统计数量,是个series对象
    df["x_data_right"] = [i.right for i in cut_series.index]  # 获取右区间值
    df["x_data_left"] = [i.left for i in cut_series.index]  # 获取左区间值
    df["y_data"] = cut_series.to_list()  # 获取数量值
    df.sort_values(by=["x_data_right"], inplace=True)  # 排序

    x_data_right = df["x_data_right"].to_list()
    x_data_left = df["x_data_left"].to_list()
    y_data = df["y_data"].to_list()

    mean = round(series.mean(), 4)
    std = round(series.std(), 4)
    median = round(series.median(), 4)
    min_value = round(series.min(), 4)
    x_index = num_map_index_position(x_data_right, mean)  # 收益率为0的位置
    d_tp = {"mean": mean, "std": std, "median": median, "x_index": x_index, "min_value": min_value}
    return (x_data_right, x_data_left, y_data, d_tp)


def add_ma_data(df, ma_cycle=[20, 40, 60], drop_flg=True):
    """df添加数据MA数据"""
    ma_last = f'MA{ma_cycle[-1]}'
    for cycle in ma_cycle:  # 注意均线数据计算出来的跟通达信上对应不上,是因为聚宽上的停盘时,使用了数据填充。
        df[f'MA{cycle}'] = talib.MA(df["close"], cycle)

    if drop_flg:  # ma为nan的行就删除所在行
        df.drop(df[np.isnan(df[ma_last])].index, inplace=True)
    return df


def add_MaVol_data(df, vol_cycle=[5, 10, 20], drop_flg=True):
    """df添加n日平均成交量数据"""
    ma_vol_last = f'MAVOL{vol_cycle[-1]}'
    for cycle in vol_cycle:  # 注意均线数据计算出来的跟通达信上对应不上,是因为聚宽上的停盘时,使用了数据填充。
        df[f'MAVOL{cycle}'] = talib.MA(df["volume"], cycle)

    if drop_flg:  # MAVOL为nan的行就删除所在行
        df.drop(df[np.isnan(df[ma_vol_last])].index, inplace=True)
    return df


def extract_vt_symbol(vt_symbol: str):
    """
    分割vt_symbol成symbol和exchange
    """
    symbol, exchange_str = vt_symbol.split(".")
    return symbol, exchange_str


def get_letter_from_symbol(symbol: str):
    """
    返回vt_symbol或者symbol的字符串的字母部分
    """
    if "." in symbol:
        symbol = extract_vt_symbol(symbol)[0]
    symbol_letter = "".join(list(filter(str.isalpha, symbol)))
    return symbol_letter


def get_symbol_price_pick(symbol):
    """
    获取品种价格跳动数据
        symbol:合约代码,带不带交易所后缀都可以
    """
    symbol_letter = get_letter_from_symbol(symbol)
    price_tick = ContractPricePick.get(symbol_letter)  # 获取价格跳动
    return price_tick


def get_symbol_contract_multiplier(symbol):
    """
    获取品种合约乘数数据
        symbol:合约代码,带不带交易所后缀都可以
    """
    symbol_letter = get_letter_from_symbol(symbol)
    contract_multiplier = ContractMultiplier.get(symbol_letter)  # 获取价格跳动
    return contract_multiplier


def get_symbol_commission(symbol, price_series, close_flag="close_y"):
    """
    获取品种手续费数据
        symbol:合约代码,带不带交易所后缀都可以
        price_series:开仓价的series
    """
    symbol_letter = get_letter_from_symbol(symbol)
    commission = commission_map.get(symbol_letter)  # 获取手续费
    commission_c_p = commission["open"] + commission[close_flag]

    if commission_c_p > 0.5:  # 如果按一手收多少钱
        commission_c_p_0 = commission_c_p / get_symbol_contract_multiplier(symbol)  # (计算的是市价对应的手续费而不是一手对应是手续费)
    else:
        # 手续费 = 价格 * 手续费率
        commission_c_p_0 = price_series * commission_c_p
    return commission_c_p_0


def optimize_long_change_percent(symbol, open_price, close_price):
    """
    优化后计算涨跌幅(多头)
    """
    slippage = get_symbol_price_pick(symbol) * 2  # 滑点
    commission = get_symbol_commission(symbol, open_price)  # 手续费
    zf = (close_price / (open_price + slippage + commission)) - 1  # 涨跌幅(已减去手续费和滑点)
    return zf
