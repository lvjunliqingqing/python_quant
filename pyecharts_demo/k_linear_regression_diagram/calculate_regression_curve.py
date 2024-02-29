import matplotlib
import numpy as np
from sklearn import linear_model

from pyecharts_demo.k_linear_regression_diagram.point_regression_line import point_regression_line

matplotlib.rcParams['font.family'] = 'SimHei'


def cal_reg_l_d(df, days=5):
    """构建出回归趋势线,计算收盘价点到收盘价的回归线的距离"""
    for i in range(len(df)-days+1):
        l_data = df.iloc[i:i+days]
        l_data.index = list(l_data.index)  # RangeIndex 转 Int64Index
        y = l_data.close
        x = np.array(l_data.index).reshape(-1, 1)
        regr = linear_model.LinearRegression()
        regr.fit(x, y)
        l_index = l_data.index
        l_y = [y * regr.coef_ + regr.intercept_ for y in l_index]

        x1 = l_index[0]
        x2 = l_index[-1]
        y1 = round(l_y[0][0], 2)
        y2 = round(l_y[-1][0], 2)
        current_close = l_data.iloc[-1]["close"]
        current_date = l_data.iloc[-1]["trade_date"]

        distance = point_regression_line([x2, current_close], [x1, y1], [x2, y2])  # 计算得到距离值
        df.loc[df["trade_date"] == current_date, "distance"] = distance
    print(df)
    return df


