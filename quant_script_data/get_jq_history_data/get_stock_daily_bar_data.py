"""
@author：lv jun
获取单个的股票bar数据
"""
import pandas as pd
from jqdatasdk import *
from peewee import (
    MySQLDatabase,
    Model,
    AutoField,
    CharField,
    DateField,
    IntegerField,
    DateTimeField,
    FloatField
)

setting = {
    "host": "192.168.20.108",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}
db = MySQLDatabase("vnpy", **setting)
auth('18578664901', 'Apple12320')

# 查看当日剩余可调用条数
print(get_query_count())


class StockBarModel(Model):
    id = AutoField(primary_key=True, verbose_name="主键id")
    symbol = CharField(verbose_name="标的物代码")
    exchange = CharField(verbose_name="交易所代码")
    datetime = DateTimeField(verbose_name="日期时间")
    interval = CharField(verbose_name="周期")
    volume = IntegerField(verbose_name="成交量")
    open_interest = FloatField(verbose_name="股票未平仓量")
    open_price = FloatField(verbose_name="开盘价")
    close_price = FloatField(verbose_name="收盘价")
    high_price = FloatField(verbose_name="最高价")
    low_price = FloatField(verbose_name="最低价")

    class Meta:
        database = db
        table_name = 'js_stock_dbbardata'

    def batch_save_data(self, df):
        import datetime
        data = []
        for idx, row in df.iterrows():
            time_str = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                "symbol": row["symbol"],
                "exchange": row["exchange"],
                "datetime": datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'),
                "interval": row["interval"],
                "volume": row["volume"],
                "open_interest": row["open_interest"] if not pd.isnull(row["open_interest"]) else 0,
                "open_price": row["open"],
                "close_price": row["close"],
                "high_price": row["high"],
                "low_price": row["low"]
            })
        with db.atomic():
            sql = StockBarModel.insert_many(data).on_conflict(
                preserve=[
                    StockBarModel.symbol,
                    StockBarModel.exchange,
                    StockBarModel.datetime,
                    StockBarModel.interval,
                    StockBarModel.volume,
                    StockBarModel.open_interest,
                    StockBarModel.open_price,
                    StockBarModel.close_price,
                    StockBarModel.high_price,
                    StockBarModel.low_price
                ]
            )
            try:
                ret = sql.execute()
                if ret:
                    print("StockBarModel.insert : 插入成功或修改成功")
                else:
                    print("StockBarModel.insert : 数据库已存在无需插入或更新")
            except Exception as e:
                print(f"StockBarModel.insert :error,错误信息为:{e}")


if __name__ == '__main__':
    df = get_price("000001.XSHE", start_date="2015-01-01", end_date="2021-05-16", frequency='daily',
                   fields=['open', 'close', 'low', 'high', 'volume', 'open_interest'],
                   skip_paused=True, fill_paused=True, fq='pre')
    df["datetime"] = df.index.tolist()
    df["symbol"] = "000001"
    df["exchange"] = "XSHE"
    df["interval"] = "d"
    StockBarModel().batch_save_data(df)
