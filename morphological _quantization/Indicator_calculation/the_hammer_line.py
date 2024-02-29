
def the_hammer_line(df, p=2, a=0.6, n=30):
    """锤子线"""
    df["min_open_close"] = df[["close", "open"]].min(axis=1)  # 开盘价和收盘价中取最小值
    df["max_open_close"] = df[["close", "open"]].max(axis=1)  # 开盘价和收盘价中取最大值

    lower_shadow = abs(df["low"] - df["min_open_close"]) / df["min_open_close"] * 100  # 计算下影线的长度(用涨幅点数来衡量)
    upper_shadow_entity = abs(df["high"] - df["min_open_close"]) / df["min_open_close"] * 100  # 计算"实体+上影线"的长度
    l_lower_shadow = lower_shadow / upper_shadow_entity  # 下影线在整日k线长度的占比
    upper_shadow = abs(df["high"] - df["max_open_close"]) / df["max_open_close"] * 100  # 计算上影线的长度
    u_upper_shadow = (upper_shadow_entity - upper_shadow) / upper_shadow_entity  # 上影线在上影线和实体组成的部分的占比

    # yang_xian = df["close"] > df["pre_close"]  # 收阳线
    # fang_liang = (df["volume"] > df["MAVOL5"])  # 放量

    # 1.下跌趋势中
    cond1 = (df["MA5"] < df["MA10"]) & (df["MA10"] < df["MA20"])
    # 2.长下影线且实体较小且上影线极短或者无
    cond2 = (l_lower_shadow > p) & (u_upper_shadow > a)
    # 3.成交量大于10000
    cond3 = df["volume"] > 10000
    # 4.股价创新低
    cond4 = (df["low"] <= df["low"].rolling(window=n).min())

    cond = cond1 & cond2 & cond3 & cond4
    df.loc[cond, "the_hammer_line_signal"] = 1
    return df
