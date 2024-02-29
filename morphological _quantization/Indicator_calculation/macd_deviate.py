def calculate_macd(df, short=12, long=26, dea=9, close='收盘价_复权'):
    """
    计算macd值
    :param df: DataFrame对象
    """
    # 计算MACD
    df['EMA_short'] = df[close].ewm(span=short, adjust=False).mean()
    df['EMA_long'] = df[close].ewm(span=long, adjust=False).mean()
    df['DIF'] = df['EMA_short'] - df['EMA_long']
    df['DEA'] = df['DIF'].ewm(span=dea, adjust=False).mean()
    df['MACD'] = (df['DIF'] - df['DEA']) * 2  # DIF大于DEA则出现金叉
    del df['EMA_short'], df['EMA_long']
    return df


def marking_deviate_signal(df, days):
    """
    标记出macd顶底背离信号
    """
    df = lower_deviation(df, days)  # 底背离
    # df = top_deviate(df, days)  # 顶背离

    return df


def lower_deviation(df, days):
    """低背离"""
    # 计算开盘和收盘的最低价
    df['min'] = df[['open', 'close']].min(axis=1)
    df["start_date"] = df['trade_date'].shift(days-1)
    df["loss_price"] = df['low'].rolling(days).min()  # 止损价

    # 先标记出所有波谷点,谷值条件：min小于前后两天，且小于最近30天所有的min
    df.loc[(df['min'].shift(1) < df['min']) & (df['min'].shift(1) < df['min'].shift(2)) & (
            df['min'].shift(1) == df['min'].rolling(days).min()), 'price_new_low'] = 1
    # 记录所有波谷点对应的收盘价和DIF值
    df.loc[df['price_new_low'] == 1, 'last_valley_price'] = df['close'].shift(1)
    df.loc[df['price_new_low'] == 1, 'last_valley_dif'] = df['DIF'].shift(1)
    # df.loc[df['price_new_low'] == 1, 'last_valley_macd'] = df['MACD'].shift(1)
    df.loc[df['price_new_low'] == 1, 'last_valley_trade_date'] = df['trade_date'].shift(1)

    # 填充空值(取前值)
    df['last_valley_price'].fillna(method='ffill', inplace=True)
    df['last_valley_dif'].fillna(method='ffill', inplace=True)
    # df['last_valley_macd'].fillna(method='ffill', inplace=True)
    df['last_valley_trade_date'].fillna(method='ffill', inplace=True)
    # 上一个波谷对应的股价和dif和交易日期
    df['last_valley_price'] = df['last_valley_price'].shift(1)
    df['last_valley_dif'] = df['last_valley_dif'].shift(1)
    # df['last_valley_macd'] = df['last_valley_macd'].shift(1)
    df['last_valley_trade_date'] = df['last_valley_trade_date'].shift(1)

    cond1 = df['price_new_low'] == 1  # 条件1：在拐点处判断
    cond2 = df['min'].shift(1) < df['last_valley_price']  # 条件2：当前谷底k线实体最低价比上一次拐点低（股价创新低）
    cond3 = df['DIF'].shift(1) > df['last_valley_dif']  # 条件3：当前谷底DEA比上一次拐点高（DEA创新高）
    # cond3 = df['MACD'].shift(1) > df['last_valley_macd']  # 条件3：当前谷底DEA比上一次拐点高（DEA创新高）
    cond4 = df['volume'] > 10000  # 条件四:成交量要大于10000

    df.loc[cond1 & cond2 & cond3 & cond4, 'state'] = '底背离'

    df.loc[cond1 & cond2 & cond3 & cond4, 'macd_deviate_signal'] = 1  # 买入信号（底背离）
    return df


def top_deviate(df, days):
    # 计算开盘和收盘的最高价
    df['max'] = df[['open', 'close']].max(axis=1)  # 当axis=1时表示取每一行的最大值
    df["start_date"] = df['trade_date'].shift(days - 1)
    df["loss_price"] = df['high'].rolling(days).max()  # 止损价
    # 标记波峰点,峰值条件：max大于后前两天，且max大于最近30天的所有max
    df.loc[(df['max'].shift(1) > df['max']) & (df['max'].shift(1) > df['max'].shift(2)) & (
            df['max'].shift(1) == df['max'].rolling(days).max()), 'price_new_high'] = 1

    # 记录波峰处对应的收盘价和DIF值
    df.loc[df['price_new_high'] == 1, 'last_peak_price'] = df['close'].shift(1)
    df.loc[df['price_new_high'] == 1, 'last_peak_dif'] = df['DIF'].shift(1)
    df.loc[df['price_new_high'] == 1, 'last_peak_trade_date'] = df['trade_date'].shift(1)

    # 填充空值(取前值)
    df['last_peak_price'].fillna(method='ffill', inplace=True)
    df['last_peak_dif'].fillna(method='ffill', inplace=True)
    df['last_peak_trade_date'].fillna(method='ffill', inplace=True)
    # 上一个波峰对应的股价和dif和交易日期
    df['last_peak_price'] = df['last_peak_price'].shift(1)
    df['last_peak_dif'] = df['last_peak_dif'].shift(1)
    df['last_peak_trade_date'] = df['last_peak_trade_date'].shift(1)

    # 计算顶底背离
    cond1 = df['price_new_high'] == 1  # 条件1：在拐点处判断
    cond2 = df['max'].shift(1) > df['last_peak_price']  # 条件2：当前谷峰对应的k线实体最高价比上一次拐点高（股价创新高）
    cond3 = df['DIF'].shift(1) < df['last_peak_dif']  # 条件3：当前谷峰对应的DEA比上一次拐点低（DEA创新低）
    cond4 = df['volume'] > 10000  # 条件四:成交量要大于10000

    df.loc[cond1 & cond2 & cond3 & cond4, 'state'] = '顶背离'

    df.loc[cond1 & cond2 & cond3 & cond4, 'macd_deviate_signal'] = 0  # 卖出信号（顶背离）
    return df


def marking_signal(df):
    """
    标记macd金叉死叉
    """
    # macd转正，产生买入信号
    condition1 = df['MACD'] > 0
    condition2 = df['MACD'].shift(1) <= 0
    df.loc[condition1 & condition2, 'macd_signal'] = 1  # 用1或0来标记是金叉还是死叉

    # macd转负，产生卖出信号
    condition1 = df['MACD'] < 0
    condition2 = df['MACD'].shift(1) >= 0
    df.loc[condition1 & condition2, 'macd_signal'] = 0
    return df