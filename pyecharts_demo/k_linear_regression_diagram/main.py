
import multiprocessing
import matplotlib
from pyecharts_demo.k_linear_regression_diagram.calculate_ma import add_ma_data
from pyecharts_demo.k_linear_regression_diagram.calculate_regression_curve import cal_reg_l_d
from pyecharts_demo.k_linear_regression_diagram.futures_data import FuturesData
from pyecharts_demo.k_linear_regression_diagram.regression_distance_value_draw_chart import RegressionDistanceValueDrawChart

matplotlib.rcParams['font.family'] = 'SimHei'


def draw_chart(df):
    # if "ZN9999" in code:
    df = df.reset_index(drop=True)  # 重置索引值
    df = cal_reg_l_d(df, days=30)  # 计算距离
    df = add_ma_data(df)  # 添加均线数据
    # df.to_csv(f"{code}.csv")
    security = df["security"].to_list()[0]
    RegressionDistanceValueDrawChart().draw_chart(df, security)  # 绘图
    # return


def main():
    cpu_nums = multiprocessing.cpu_count() - 4
    ctx = multiprocessing.get_context("spawn")
    pool = ctx.Pool(cpu_nums)

    futures_data = FuturesData()
    futures_price_df = futures_data.read_futures_price_daily()  # 查询行情数据

    results = []
    for code, df in futures_price_df.groupby("security"):
        result = (pool.apply_async(draw_chart, (df,)))
        results.append(result)
    pool.close()
    pool.join()


if __name__ == '__main__':
    main()


