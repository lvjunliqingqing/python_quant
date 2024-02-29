from datetime import datetime

import pandas as pd
from peewee import (
    MySQLDatabase,
)

settings = {
    'host': '192.168.0.250',
    'user': 'stock',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8'
}

db = MySQLDatabase("stock", **settings)

from peewee import (
    AutoField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
)


class BarModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField()
    exchange = CharField()
    datetime = DateTimeField()
    interval = CharField()
    volume = IntegerField()
    open_interest = FloatField()
    open_price = FloatField()
    close_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()

    class Meta:
        database = db  #
        table_name = 'dbbardata'  # 这里可以自定义表名


class SecuritiesInfoModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField(null=False)
    display_name = CharField(null=False)
    name_code = CharField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    sec_type = CharField(null=False)

    class Meta:
        database = db  # 这里是数据库链接，为了方便建立多个表，可以把这个部分提炼出来形成一个新的类
        table_name = 'securities_info'  # 这里可以自定义表名

    def get_futures_info(self):

        curr_date = datetime.now().strftime('%Y-%m-%d')

        sql = f"select * from securities_info where symbol  REGEXP '.*(9999).*' and end_date >= '{curr_date}' and sec_type='futures'"

        sec_list = SecuritiesInfoModel().raw(sql)

        return sec_list

    def main_futures_map(self):
        map_info = {}
        for info in self.get_futures_info():
            tmp = info.symbol.split('.')
            sql = f"SELECT  * FROM dbbardata AS t2 WHERE  symbol!='{tmp[0]}' and t2.`volume` = (SELECT volume FROM dbbardata WHERE symbol = '{tmp[0]}' and exchange='{tmp[1]}' AND `interval` = 'd' ORDER BY `datetime` DESC LIMIT 1) limit 1"
            _data = BarModel().raw(sql)
            for row in _data:
                map_info[f"{tmp[0]}.{tmp[1]}"] = row.symbol

        return map_info

    def get_bar(self, info):

        tmp = info.symbol.split('.')

        if len(tmp) >= 2:

            sql = f"select * from dbbardata where `interval`='d' and symbol='{tmp[0]}' and exchange='{tmp[1]}' order by `datetime` desc"

            bar_data = BarModel().raw(sql)

            data = []

            for row in bar_data:
                data.append(
                    {
                        'symbol': tmp[0],
                        'exchange': tmp[1],
                        'datetime': row.datetime,
                        'open': row.open_price,
                        'close': row.close_price,
                        'high': row.high_price,
                        'low': row.low_price

                    }
                )
            return pd.DataFrame(data)

    def logic(self):

        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%Y%m")
        day = datetime.now().strftime("%Y%m%d")

        long_70_100_35_65 = []
        long_70_100_midd_up = []

        shi_35_65_35_65 = []

        short_70_100_35_65 = []
        short_70_100_midd_up = []

        main_futures_map = self.main_futures_map()
        for info in self.get_futures_info():

            df = self.get_bar(info)

            if len(df):

                df['zf_rise'] = (df['close'] - df['open']) / df['open']

                zf_rise = df[df['zf_rise'] >= 0]['zf_rise']
                df_rise = df[df['zf_rise'] < 0]['zf_rise']

                yesterday_min_long = zf_rise.quantile(0.7)
                yesterday_max_long = zf_rise.quantile(1)

                yesterday_min_short = df_rise.quantile(0.7)
                yesterday_max_short = df_rise.quantile(1)

                today_min_long = quan_35_long = zf_rise.quantile(0.35)
                today_max_long = quan_65_long = zf_rise.quantile(0.65)

                today_min_short = quan_35_short = df_rise.quantile(0.35)
                today_max_short = quan_65_short = df_rise.quantile(0.65)

                yesterday_high = df['high'].values[1]
                yesterday_low = df['low'].values[1]

                today_close = df['close'].values[0]

                yestrday_midd_up = (yesterday_high + yesterday_low) / 2

                yestrday_rise = df['zf_rise'].values[1]
                today_rise = df['zf_rise'].values[0]

                long_direction = today_rise > 0 and yestrday_rise > 0
                short_direction = today_rise < 0 and yestrday_rise < 0

                if long_direction and yesterday_min_long < yestrday_rise < yesterday_max_long and today_min_long < today_rise < today_max_long:

                    long_70_100_35_65.append({
                        'day': df['datetime'].values[0],
                        'symbol': main_futures_map.get(f"{df['symbol'].values[0]}.{df['exchange'].values[0]}"),
                        'vt_symbol': df['symbol'].values[0],
                        'exchange': df['exchange'].values[0],
                        'high': df['high'].values[0],
                        'low': df['low'].values[0],
                        'open': df['open'].values[0],
                        'close': df['close'].values[0],
                        'zf_rise': df['zf_rise'].values[0],
                    })

                elif long_direction and yestrday_midd_up < today_close and yesterday_min_long < yestrday_rise < yesterday_max_long:

                    long_70_100_midd_up.append({
                        'day': df['datetime'].values[0],
                        'symbol': main_futures_map.get(f"{df['symbol'].values[0]}.{df['exchange'].values[0]}"),
                        'vt_symbol': df['symbol'].values[0],
                        'exchange': df['exchange'].values[0],
                        'high': df['high'].values[0],
                        'low': df['low'].values[0],
                        'open': df['open'].values[0],
                        'close': df['close'].values[0],
                        'zf_rise': df['zf_rise'].values[0],
                    })

                elif short_direction and yesterday_min_short < yestrday_rise < yesterday_max_short and today_min_short < today_rise < today_max_short:

                    short_70_100_35_65.append({
                        'day': df['datetime'].values[0],
                        'symbol': main_futures_map.get(f"{df['symbol'].values[0]}.{df['exchange'].values[0]}"),
                        'vt_symbol': df['symbol'].values[0],
                        'exchange': df['exchange'].values[0],
                        'high': df['high'].values[0],
                        'low': df['low'].values[0],
                        'open': df['open'].values[0],
                        'close': df['close'].values[0],
                        'zf_rise': df['zf_rise'].values[0],
                    })
                elif short_direction and yestrday_midd_up < today_close and yesterday_min_short < yestrday_rise < yesterday_max_short:
                    short_70_100_midd_up.append({
                        'day': df['datetime'].values[0],
                        'symbol': main_futures_map.get(f"{df['symbol'].values[0]}.{df['exchange'].values[0]}"),
                        'vt_symbol': df['symbol'].values[0],
                        'exchange': df['exchange'].values[0],
                        'high': df['high'].values[0],
                        'low': df['low'].values[0],
                        'open': df['open'].values[0],
                        'close': df['close'].values[0],
                        'zf_rise': df['zf_rise'].values[0],
                    })

                elif (
                        quan_65_long > yestrday_rise > quan_35_long or quan_65_short > yestrday_rise > quan_35_short) and (
                        quan_65_long > today_rise > quan_35_long or quan_65_short > today_rise > quan_35_short):
                    shi_35_65_35_65.append({
                        'day': df['datetime'].values[0],
                        'symbol': main_futures_map.get(f"{df['symbol'].values[0]}.{df['exchange'].values[0]}"),
                        'vt_symbol': df['symbol'].values[0],
                        'exchange': df['exchange'].values[0],
                        'high': df['high'].values[0],
                        'low': df['low'].values[0],
                        'open': df['open'].values[0],
                        'close': df['close'].values[0],
                        'zf_rise': df['zf_rise'].values[0],
                    })

        columns = ['day', 'symbol', 'vt_symbol', 'exchange', 'open', 'high', 'low', 'close', 'zf_rise']

        if long_70_100_35_65:
            pd.DataFrame(long_70_100_35_65).to_csv(f"C:/{year}/{month}/{day}_long_70_100_35_65.csv",
                                                   index=False, columns=columns)

        if long_70_100_midd_up:
            pd.DataFrame(long_70_100_midd_up).to_csv(
                f"C:/{year}/{month}/{day}_long_70_100_midd_up.csv", index=False, columns=columns)

        if short_70_100_35_65:
            pd.DataFrame(short_70_100_35_65).to_csv(
                f"C:/{year}/{month}/{day}_short_70_100_35_65.csv", index=False, columns=columns)

        if short_70_100_midd_up:
            pd.DataFrame(short_70_100_midd_up).to_csv(
                f"C:/{year}/{month}/{day}_short_70_100_midd_up.csv", index=False, columns=columns)

        if shi_35_65_35_65:
            pd.DataFrame(shi_35_65_35_65).to_csv(f"C:/{year}/{month}/{day}_shi_35_65_35_65.csv",
                                                 index=False, columns=columns)


# if __name__ == "__main__":
SecuritiesInfoModel().logic()
