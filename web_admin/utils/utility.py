

import talib

def rsi(close_list, n, array=False):
    """
    RSI指标
    """
    result = talib.RSI(close_list, n)
    if array:
        return result
    return result[-1]
