import talib


def add_ma_data(df, ma_cycle=[5, 10, 20]):
    """df添加数据MA数据"""
    for cycle in ma_cycle:
        df[f'MA{cycle}'] = talib.MA(df["close"], cycle).round(2)
    return df
