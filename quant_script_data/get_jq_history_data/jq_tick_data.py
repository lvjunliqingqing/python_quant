"""
@author：lv jun
获取所有期货的tick数据
"""
from datetime import datetime
from jqdatasdk import *
from peewee import (
    MySQLDatabase,
    Model,
    AutoField,
    CharField,
    DateField,
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
# print(get_query_count())


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


class DbTickData(Model):
    id = AutoField(primary_key=True, verbose_name="主键id")
    symbol = CharField(verbose_name="合约代码+交易所")
    exchange = CharField(verbose_name="交易所代码")
    datetime = DateTimeField(verbose_name="日期时间")
    name = CharField()
    volume = FloatField(verbose_name="成交量")
    open_interest = FloatField(verbose_name="未平仓量")
    last_price = FloatField(verbose_name="最新价")
    last_volume = FloatField("最新成家量")
    limit_up = FloatField(verbose_name="涨停价")
    limit_down = FloatField(verbose_name="跌停价")
    open_price = FloatField(verbose_name="开盘价")
    high_price = FloatField(verbose_name="最高价")
    low_price = FloatField(verbose_name="最低价")
    pre_close = FloatField(verbose_name="前一天的收盘价")
    bid_price_1 = FloatField(verbose_name="买一价")
    bid_price_2 = FloatField(null=True, verbose_name="买二价")
    bid_price_3 = FloatField(null=True, verbose_name="买三价")
    bid_price_4 = FloatField(null=True, verbose_name="买四价")
    bid_price_5 = FloatField(null=True, verbose_name="买五价")
    ask_price_1 = FloatField(verbose_name="卖一价")
    ask_price_2 = FloatField(null=True, verbose_name="卖二价")
    ask_price_3 = FloatField(null=True, verbose_name="卖三价")
    ask_price_4 = FloatField(null=True, verbose_name="卖四价")
    ask_price_5 = FloatField(null=True, verbose_name="卖五价")
    bid_volume_1 = FloatField(verbose_name="买一量")
    bid_volume_2 = FloatField(null=True, verbose_name="买二量")
    bid_volume_3 = FloatField(null=True, verbose_name="买三量")
    bid_volume_4 = FloatField(null=True, verbose_name="买四量")
    bid_volume_5 = FloatField(null=True, verbose_name="买五量")
    ask_volume_1 = FloatField(verbose_name="卖一量")
    ask_volume_2 = FloatField(null=True, verbose_name="卖二量")
    ask_volume_3 = FloatField(null=True, verbose_name="卖三量")
    ask_volume_4 = FloatField(null=True, verbose_name="卖四量")
    ask_volume_5 = FloatField(null=True, verbose_name="卖五量")

    class Meta:
        database = db
        table_name = 'dbtickdata'

    def batch_save_data(self, df):
        data = []
        for idx, row in df.iterrows():
            data.append({
                "symbol": row["symbol"],
                "exchange": row["exchange"],
                "datetime": datetime.strptime(row["time"].strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S'),
                "name": row["name"],
                "volume": row["volume"],
                "open_interest": row["open_interest"],
                "last_price": row["last_price"],
                "last_volume": row["last_volume"],
                "limit_up": row["limit_up"],
                "limit_down": row["limit_down"],
                "open_price": row["open"],
                "high_price": row["high"],
                "low_price": row["low"],
                "pre_close": row["pre_close"],
                "bid_price_1": row["bid_price_1"],
                "bid_price_2": row["bid_price_2"],
                "bid_price_3": row["bid_price_3"],
                "bid_price_4": row["bid_price_4"],
                "bid_price_5": row["bid_price_5"],
                "ask_price_1": row["ask_price_1"],
                "ask_price_2": row["ask_price_2"],
                "ask_price_3": row["ask_price_3"],
                "ask_price_4": row["ask_price_4"],
                "ask_price_5": row["ask_price_5"],
                "bid_volume_1": row["bid_volume_1"],
                "bid_volume_2": row["bid_volume_2"],
                "bid_volume_3": row["bid_volume_3"],
                "bid_volume_4": row["bid_volume_4"],
                "bid_volume_5": row["bid_volume_5"],
                "ask_volume_1": row["ask_volume_1"],
                "ask_volume_2": row["ask_volume_2"],
                "ask_volume_3": row["ask_volume_3"],
                "ask_volume_4": row["ask_volume_4"],
                "ask_volume_5": row["ask_volume_5"],
            })
        with db.atomic():
            sql = DbTickData.insert_many(data).on_conflict(
                preserve=[
                    DbTickData.symbol,
                    DbTickData.exchange,
                    DbTickData.datetime,
                    DbTickData.name,
                    DbTickData.volume,
                    DbTickData.open_interest,
                    DbTickData.last_price,
                    DbTickData.last_volume,
                    DbTickData.limit_up,
                    DbTickData.limit_down,
                    DbTickData.open_price,
                    DbTickData.high_price,
                    DbTickData.low_price,
                    DbTickData.pre_close,
                    DbTickData.bid_price_1,
                    DbTickData.bid_price_2,
                    DbTickData.bid_price_3,
                    DbTickData.bid_price_4,
                    DbTickData.bid_price_5,
                    DbTickData.ask_price_1,
                    DbTickData.ask_price_2,
                    DbTickData.ask_price_3,
                    DbTickData.ask_price_4,
                    DbTickData.ask_price_5,
                    DbTickData.bid_volume_1,
                    DbTickData.bid_volume_2,
                    DbTickData.bid_volume_3,
                    DbTickData.bid_volume_4,
                    DbTickData.bid_volume_5,
                    DbTickData.ask_volume_1,
                    DbTickData.ask_volume_2,
                    DbTickData.ask_volume_3,
                    DbTickData.ask_volume_4,
                    DbTickData.ask_volume_5
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
    symbol_list = [i.symbol for i in SecuritiesInfoModel.select().where(
        (SecuritiesInfoModel.name_code ** "%8888%") | (SecuritiesInfoModel.name_code ** "%9999%"))]
    df = get_ticks("AU1812.XSGE", start_dt='2018-07-02', end_dt='2018-07-03', count=None)
    # DbTickData().batch_save_data(df)
