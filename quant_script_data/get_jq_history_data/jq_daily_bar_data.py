"""
@author：lv jun
获取所有期货的日bar数据
"""
from datetime import datetime
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
    "host": "192.168.20.112",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}
db = MySQLDatabase("vnpy", **setting)
auth('18578664901', 'Apple12320')

# 查看当日剩余可调用条数
print(get_query_count())


class SecuritiesInfoModel(Model):
    """所有标的信息模型类"""
    id = AutoField(primary_key=True, verbose_name="主键id")
    symbol = CharField(null=False)
    display_name = CharField(null=False, verbose_name="中文名称")
    name_code = CharField(null=False, verbose_name="缩写简称")
    start_date = DateField(null=False, verbose_name="上市日期")
    end_date = DateField(null=False, verbose_name="退市日期")
    sec_type = CharField(null=False, verbose_name="类型(futures:期货，stock:股票等等)")

    class Meta:
        database = db
        table_name = 'securities_info'


class BarModel(Model):
    id = AutoField(primary_key=True, verbose_name="主键id")
    symbol = CharField(verbose_name="标的物代码")
    exchange = CharField(verbose_name="交易所代码")
    datetime = DateTimeField(verbose_name="日期时间")
    interval = CharField(verbose_name="周期")
    volume = IntegerField(verbose_name="成交量")
    open_interest = FloatField(verbose_name="期货持仓量")
    open_price = FloatField(verbose_name="开盘价")
    close_price = FloatField(verbose_name="收盘价")
    high_price = FloatField(verbose_name="最高价")
    low_price = FloatField(verbose_name="最低价")

    class Meta:
        database = db
        table_name = 'dbbardata'

    def batch_save_data(self, df):
        data = []
        for idx, row in df.iterrows():
            data.append({
                "symbol": row["symbol"],
                "exchange": row["exchange"],
                "datetime": datetime.strptime(f'{row["time"].strftime("%Y-%m-%d")} 00:00:00', '%Y-%m-%d %H:%M:%S'),
                "interval": row["interval"],
                "volume": row["volume"],
                "open_interest": row["open_interest"],
                "open_price": row["open"],
                "close_price": row["close"],
                "high_price": row["high"],
                "low_price": row["low"]
            })
        with db.atomic():
            sql = BarModel.insert_many(data).on_conflict(
                preserve=[
                    BarModel.symbol,
                    BarModel.exchange,
                    BarModel.datetime,
                    BarModel.interval,
                    BarModel.volume,
                    BarModel.open_interest,
                    BarModel.open_price,
                    BarModel.close_price,
                    BarModel.high_price,
                    BarModel.low_price
                ]
            )
            try:
                ret = sql.execute()
                if ret:
                    print("BarModel.insert : 插入成功或修改成功")
                else:
                    print("BarModel.insert : 数据库已存在无需插入或更新")
            except Exception as e:
                print(f"BarModel.insert :error,错误信息为:{e}")


if __name__ == '__main__':
    symbol_list = [i.symbol for i in SecuritiesInfoModel.select()]
    # end_date要指定到时间,frequency指定周期,fields指定返回哪些字段
    # skip_paused: 是否跳过不交易日期(包括停牌, 未上市或者退市后的日期). 如果不跳过,停牌时会使用停牌前的数据填充,但上市前或者退市后数据都为nan,但注意设置true时且获取多个标的时需要将panel参数设置为False
    # fq：'pre': 前复权，None: 不复权, 返回实际价格，'post': 后复权
    # panel：指定返回结果是否使用panel格式，默认为True；指定panel=False时返回dataframe格式。
    df = get_price(symbol_list, start_date='2021-02-02', end_date='2021-03-02 23:00:00', frequency='daily',
                   fields=['open', 'close', 'high', 'low', 'volume', 'open_interest'], skip_paused=True, fq="pre",
                   panel=False)
    df["symbol"], df["exchange"] = df["code"].str.split('.', 1).str
    df["interval"] = "d"
    # print(df)
    BarModel().batch_save_data(df)
