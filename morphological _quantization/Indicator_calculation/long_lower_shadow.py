
def long_lower_shadow(df, p=1, a=3, n=60):
    """长下影线"""
    df["min_open_close"] = df[["close", "open"]].min(axis=1)  # 开盘价和收盘价中取最小值
    lower_shadow = abs(df["low"] - df["min_open_close"]) / df["min_open_close"] * 100  # 计算下影线的长度(用涨幅点数来衡量)
    upper_shadow_entity = abs(df["high"] - df["min_open_close"]) / df["min_open_close"] * 100  # 计算"实体+上影线"的长度
    amplitude = ((df["high"] - df["low"]) / df["min_open_close"]) * 100 > a * df["up_limit"] / 10
    l_lower_shadow = (lower_shadow / upper_shadow_entity) > p  # 下影线在整日k线长度的占比
    low_point = (df["low"] <= df["low"].rolling(window=n).min())  # n日股价创新低
    volume_cond = df["volume"] > 10000
    yang_xian = df["close"] > df["pre_close"]  # 收阳线
    fang_liang = (df["volume"] > df["MAVOL5"])  # 放量
    # cond = l_lower_shadow & low_point & amplitude & volume_cond  # 长下影线&股价n日创新低&振幅要大于a
    cond = l_lower_shadow & low_point & amplitude & yang_xian & fang_liang & volume_cond  # 长下影线&股价n日创新低&振幅要大于a&收阳放量
    # df["long_lower_shadow_signal"] = 0
    df.loc[cond, "long_lower_shadow_signal"] = 1
    # print(df[df["long_lower_shadow_signal"] == 1])
    return df

