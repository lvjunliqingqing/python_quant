

if __name__ == '__main__':
    import pandas as pd
    import numpy as np
    from chart_analysis.create_histogram_object import create_histogram
    from utility import interval_statistics

    data = pd.DataFrame({'price': np.random.randn(20),
                         'amount': 100 * np.random.randn(20)})
    x_data_right, x_data_left, y_data, d_tp = interval_statistics(data['price'])
    bar = create_histogram(x_data_right, x_data_left, y_data, d_tp, file_name="芙蓉出水_盈亏分布直方图", series_name="芙蓉出水_盈亏_区间分布图", title="芙蓉出水_盈亏_区间分布图")
    bar.render("芙蓉出水_盈亏分布直方图.html")
