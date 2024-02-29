# -*- coding : utf-8 -*-
# coding: utf-8

"""
@author：lv jun
把读取原始csv中的主连筹数据,把数据入库。
"""

import re
import os
import pandas as pd
import datetime
from jqdatasdk import *
from peewee import (
    MySQLDatabase,
    Model,
    AutoField,
    CharField,
    IntegerField,
    DateTimeField,
    FloatField, Field
)

from get_jq_history_data.symbolLetter_exchange_map import symbolLetter_exchange_map

setting = {
    "host": "192.168.20.119",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}

db = MySQLDatabase("vnpy", **setting)  # 连接数据库


class TimestampField(Field):
    field_type = "timestamp"


class SecondTransactionDayDetailModel(Model):
    id = AutoField(primary_key=True, verbose_name="主键id")
    vt_symbol = CharField(verbose_name="本地代码")
    datetime = DateTimeField(verbose_name="日期时间")
    time = TimestampField(verbose_name="时间")
    interval = CharField(verbose_name="周期")
    volume = IntegerField(verbose_name="成交量")
    price = FloatField(verbose_name="成交价")
    direction = CharField(verbose_name="开平方向")
    attribute = CharField(verbose_name="性质")
    increase_decrease_position = IntegerField(verbose_name="增减仓")

    class Meta:
        database = db
        table_name = 'second_transaction_detail_day_data'

    def batch_save_data(self, df):
        data = []
        for idx, row in df.iterrows():
            # time_str = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                "vt_symbol": row["vt_symbol"],
                "datetime": row["datetime"],
                "time": row["time"],
                "interval": row["interval"],
                "volume": row["volume"],
                "price": row["price"],
                "direction": row["direction"],
                "attribute": row["attribute"],
                "increase_decrease_position": row["increase_decrease_position"]
            })
        with db.atomic():
            sql = SecondTransactionDayDetailModel.insert_many(data).on_conflict(
                preserve=[
                    SecondTransactionDayDetailModel.vt_symbol,
                    SecondTransactionDayDetailModel.datetime,
                    SecondTransactionDayDetailModel.time,
                    SecondTransactionDayDetailModel.interval,
                    SecondTransactionDayDetailModel.volume,
                    SecondTransactionDayDetailModel.price,
                    SecondTransactionDayDetailModel.direction,
                    SecondTransactionDayDetailModel.attribute,
                    SecondTransactionDayDetailModel.increase_decrease_position
                ]
            )
            try:
                ret = sql.execute()
                if ret:
                    print(f"SecondTransactionDayDetailModel.insert : {data[0]['vt_symbol']}-{data[0]['datetime']}插入成功或修改成功")
                else:
                    print(f"SecondTransactionDayDetailModel.insert : {data[0]['vt_symbol']}-{data[0]['datetime']}数据库已存在无需插入或更新")
            except Exception as e:
                print(f"SecondTransactionDayDetailModel.insert :{data[0]['vt_symbol']}-{data[0]['datetime']}error,错误信息为:{e}")


def dispose_csv_data(source_file, dir_name, folder_name):
    df = pd.read_csv(dir_name + source_file, encoding="gbk")

    if not df.empty:
        df.rename(columns={'时间': 'time'}, inplace=True)  # 修改 列名"时间" 为 "time"
        time_filter = ["08:59", "09:00", "09:01", "20:59", "21:00", "21:01"]
        # 使用and时,每个条件要用()括起再使用and连接
        df = df[~((df["增仓"].abs() >= df["现量"]) & (df.time.isin(time_filter) & (df["增仓"].abs() >= 10000)))]  # 过滤掉通达信换月移仓增仓数据错误问题

    df.rename(columns={'现量': 'volume'}, inplace=True)
    df.rename(columns={'开平': 'direction'}, inplace=True)
    df.rename(columns={'性质': 'attribute'}, inplace=True)
    df.rename(columns={'增仓': 'increase_decrease_position'}, inplace=True)

    if "time" not in df.columns:
        df['time'] = df["时间"]

    df.rename(columns={'价格': 'price'}, inplace=True)
    file_split_list = re.split("[_]", source_file)
    df["datetime"] = file_split_list[0][0:4] + "-" + file_split_list[0][4:6] + "-" + file_split_list[0][6:8]
    df['interval'] = "s"
    symbol_letter = folder_name[0:-1]
    df['vt_symbol'] = symbolLetter_exchange_map[symbol_letter]

    return df


if __name__ == '__main__':
    # source_folder_list = os.listdir("E:/jobs/通达信数据/主连/所有品种主连")
    source_folder_list = ['NIL8', 'NRL8', 'OIL8', 'PBL8', 'PFL8', 'PGL8', 'PKL8', 'PL8', 'PPL8', 'RBL8', 'RML8', 'RUL8', 'SAL8', 'SCL8', 'SFL8', 'SML8', 'SNL8', 'SPL8', 'SRL8', 'TAL8', 'TFL8', 'TL8', 'TSL8', 'URL8', 'VL8', 'YL8', 'ZCL8', 'ZNL8']
    for folder_name in source_folder_list:
        dir_name = f"E:/jobs/通达信数据/主连/所有品种主连/{folder_name}/"
        source_file_list = os.listdir(dir_name)
        for source_file in source_file_list:
            df = dispose_csv_data(source_file, dir_name, folder_name)
            if df.empty:
                continue
            # print(df)
            SecondTransactionDayDetailModel().batch_save_data(df)
