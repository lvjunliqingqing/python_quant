import datetime
import pandas as pd
from model.bar_model import BarModel
from model.securities_Info_model import SecuritiesInfoModel


def get_target_futures(zf_min_yesterday_quantile_val, zf_max_yesterday_quantile_val, zf_min_today_quantile_val, zf_max_today_quantile_val):
    count = False
    main_futures_map = SecuritiesInfoModel().main_futures_map()
    securities_info = SecuritiesInfoModel().get_futures_securities_info()
    for i in securities_info.iterator():
        bar_data = BarModel().get_futures_bar_data(i)
        futures_list = []
        for row in bar_data.iterator():
            futures_list.append({
                'trade_date': row.datetime.strftime("%Y-%m-%d"),
                'symbol': main_futures_map.get(f"{row.symbol}.{row.exchange}"),
                'vt_symbol': row.symbol,
                'exchange': row.exchange,
                'open': row.open_price,
                'close': row.close_price,
                'high': row.high_price,
                'low': row.low_price,
                'volume': row.volume,
                "display_name": i.display_name
            })
        df = pd.DataFrame(futures_list)
        if len(df) >= 2:
            df['diff_rise'] = df['close'].diff(periods=-1) / df['close'].shift(-1) * 100

            last_close_rise = df['diff_rise'].values[0]
            pre_close_rise = df['diff_rise'].values[1]

            # 计算昨天的分位数
            zf_min_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_yesterday_quantile_val)
            zf_max_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_yesterday_quantile_val)

            # 计算出今天分位数
            zf_min_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_today_quantile_val)
            zf_max_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_today_quantile_val)
            date_time = datetime.datetime.now().strftime("%Y%m%d")
            if zf_max_yesterday_quantile >= pre_close_rise >= zf_min_yesterday_quantile and zf_max_today_quantile >= last_close_rise >= zf_min_today_quantile:
                filename = f"{zf_min_yesterday_quantile_val}_{zf_max_yesterday_quantile_val}_{zf_min_today_quantile_val}_{zf_max_today_quantile_val}_{date_time}.csv"
                dr = "E:/data/"
                # dr = "../zf_history_quantile/"
                path = dr + filename
                if not count:
                    df = df[0:1].to_csv(path, encoding='utf8', index=False)
                    count = True
                else:
                    df = df[0:1].to_csv(path, encoding='utf8', mode='a', header=False, index=False)


if __name__ == "__main__":
    get_target_futures(0.7, 1, 0.35, 0.65)
