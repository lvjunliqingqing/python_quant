import datetime
import math

from jqdatasdk import *
from peewee import (
    MySQLDatabase,
)

# import sys
# sys.setrecursionlimit(100000)
# coding:utf-8
# import tushare as ts

settings = {
    'host': '192.168.0.250',
    'user': 'stock',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8'
}

# TS = ts.pro_api(TOKEN)

FUT_TYPE = [
    1,  # 普通合约
    2  # 主力合约
]
EXCHANGES = [
    'SHFE',
    'CFFEX',
    'DCE',
    'CZCE',
    'INE'
]

db = MySQLDatabase("stock", **settings)

auth('13420134545', '13420134545HAn')

print(get_query_count())
# pd = get_price('A9999.XDCE', start_date='2010-09-07', end_date='2010-09-07', frequency='daily', fields=None, skip_paused=False, fq='pre')
# print(f"{pd} pd")

from peewee import (
    AutoField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
)


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


class StockBarModel(Model):
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

    def savaData(self, df):

        data = []
        for idx, row in df.iterrows():
            trade_date = idx.to_pydatetime()
            row.open = (0.0 if (math.isnan(row.open)) else row.open)
            row.close = (0.0 if (math.isnan(row.close)) else row.close)
            row.high = (0.0 if (math.isnan(row.high)) else row.high)
            row.low = (0.0 if (math.isnan(row.low)) else row.low)
            row.volume = (0.0 if (math.isnan(row.volume)) else row.volume)
            # print(f"row data {row} {row.volume}")
            data.append(
                {
                    'symbol': row.symbol,
                    'exchange': row.exchange,
                    'datetime': trade_date,
                    'interval': 'd',
                    'volume': int(row.volume),
                    'open_interest': 0,
                    'open_price': row.open,
                    'close_price': row.close,
                    'high_price': row.high,
                    'low_price': row.low,
                }
            )

        sql = StockBarModel().insert_many(data)

        if sql.execute():
            print(f"ok {df['symbol'][0]}")
            return True
        else:
            print(f"error {sql}")
            return False

    def SaveDataByDay(self, df):
        for idx, row in df.iterrows():

            row.open = (0.0 if (math.isnan(row.open)) else row.open)
            row.close = (0.0 if (math.isnan(row.close)) else row.close)
            row.high = (0.0 if (math.isnan(row.high)) else row.high)
            row.low = (0.0 if (math.isnan(row.low)) else row.low)
            row.volume = (0.0 if (math.isnan(row.volume)) else row.volume)

            sql = StockBarModel().insert(
                symbol=row.symbol,
                exchange=row.exchange,
                datetime=row.datetime,
                interval='d',
                volume=int(row.volume),
                open_interest=0,
                open_price=row.open,
                close_price=row.close,
                high_price=row.high,
                low_price=row.low
            ).on_conflict(
                preserve=[StockBarModel.open_price, StockBarModel.close_price, StockBarModel.high_price,
                          StockBarModel.low_price, StockBarModel.volume]
            )
            if sql.execute():
                print(f"ok {idx} sql {sql}")
            else:
                print(f"error {idx} sql {sql}")

    class Meta:
        database = db  #
        table_name = 'dhtz_stock_dbbardata'  # 这里可以自定义表名

    def get_jk_current_day_data(self, start_date=None, end_date=None, is_history=True):

        stock_info = SecuritiesInfoModel().select().where(
            (SecuritiesInfoModel.sec_type == 'stock')
            # & (SecuritiesInfoModel.id > 8129)
        ).dicts()

        symbol_list = []

        for info in stock_info.iterator():
            symbol_list.append(str(info['symbol']))

        if len(symbol_list) and is_history == False:

            if start_date == None:
                start_date = datetime.datetime.now().strftime('%Y-%m-%d')

            if end_date == None:
                end_date = datetime.datetime.now().strftime('%Y-%m-%d')

            print(f"symbol_list {len(symbol_list)} {start_date} {end_date}")

            pd = get_price(
                symbol_list, start_date=start_date, end_date=end_date, frequency='daily',
                fields=['open', 'close', 'high', 'low', 'volume', 'money', 'avg', 'high_limit', 'low_limit',
                        'pre_close', 'paused', 'factor', 'price', 'open_interest'],
                skip_paused=False, fq='pre'
            )

            if not len(pd.major_axis):
                print(f"{start_date} stock df len = 0 ")
            else:
                df = pd.major_xs(pd.major_axis[0])
                df['datetime'] = str(pd.major_axis[0])
                df['vt_symbol'] = (df.index)
                tmp = df['vt_symbol'].str.split('.', expand=True)
                df['symbol'] = tmp[0]
                df['exchange'] = tmp[1]
                print(f"pd {type(tmp)}  {df} ")
                if is_history:
                    self.savaData(df)
                else:
                    """"""
                    self.SaveDataByDay(df)


if __name__ == "__main__":
    # df = get_price('000001.XSHE', start_date=start_date, end_date=end_date, frequency='daily', 
    #   fields=['open', 'close', 'high', 'low', 'volume', 'money', 'avg', 'high_limit', 'low_limit', 'pre_close', 'paused', 'factor', 'price', 'open_interest'],
    #   skip_paused=False, fq='pre')

    StockBarModel().get_jk_current_day_data(start_date=None, end_date=None, is_history=False)
