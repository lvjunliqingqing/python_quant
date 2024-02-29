
import pandas as pd
pd.set_option('display.float_format', lambda x: '%.4f' % x)  # 禁止科学计算显示,保留四位有效小数点
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


def marking_water_hibiscus_signal(df, s=20, m=40, n=60):
    """标记出水芙蓉"""
    cond1 = df["close"] > df["open"]  # 收阳线
    # cond1并且收盘价>收盘价的S日简单移动平均并且收盘价>收盘价的M日简单移动平均并且收盘价>收盘价的N日简单移动
    cond2 = cond1 & (df["close"] > df[f'MA{s}']) & (df["close"] > df[f'MA{m}']) & (df["close"] > df[f'MA{n}'])
    # cond2并且开盘价<收盘价的M日简单移动平均并且开盘价<收盘价的N日简单移动平均
    cond3 = cond2 & (df["open"] < df[f'MA{m}']) & (df["open"] < df[f'MA{n}'])
    # cond3并且(收盘价-开盘价)>0.0618*收盘价
    cond4 = cond3 & ((df["close"] - df["open"]) > (0.0618 * df["close"] * df["up_limit"] / 20))
    cond5 = df["volume"] > 10000
    cond = cond4 & cond5
    # print(df["high_limit"] - df["close"].)
    df.loc[cond, "water_hibiscus_signal"] = 1
    # if not df[df["water_hibiscus_signal"] == 1].empty:  # 输出水芙蓉当天的数据
    #     print(df[df["water_hibiscus_signal"] == 1])

    return df





