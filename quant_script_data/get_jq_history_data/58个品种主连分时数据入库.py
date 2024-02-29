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
    FloatField
)

from get_jq_history_data.symbolLetter_exchange_map import symbolLetter_exchange_map

setting = {
    "host": "192.168.20.119",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}

db = MySQLDatabase("vnpy", **setting)


class TransactionDayDetailModel(Model):
    id = AutoField(primary_key=True, verbose_name="主键id")
    vt_symbol = CharField(verbose_name="本地代码")
    datetime = DateTimeField(verbose_name="日期时间")
    interval = CharField(verbose_name="周期")
    volume = IntegerField(verbose_name="成交量")
    price = FloatField(verbose_name="成交价")
    increase_decrease_position = IntegerField(verbose_name="增减仓")

    class Meta:
        database = db
        table_name = 'transaction_detail_day_data'

    def batch_save_data(self, df):
        data = []
        for idx, row in df.iterrows():
            # time_str = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                "vt_symbol": row["vt_symbol"],
                "datetime": row["datetime"],
                "interval": row["interval"],
                "volume": row["volume"],
                "price": row["price"],
                "increase_decrease_position": row["increase_decrease_position"]
            })
        with db.atomic():
            sql = TransactionDayDetailModel.insert_many(data).on_conflict(
                preserve=[
                    TransactionDayDetailModel.vt_symbol,
                    TransactionDayDetailModel.datetime,
                    TransactionDayDetailModel.interval,
                    TransactionDayDetailModel.volume,
                    TransactionDayDetailModel.price,
                    TransactionDayDetailModel.increase_decrease_position
                ]
            )
            try:
                ret = sql.execute()
                if ret:
                    print(f"StockBarModel.insert : {data[0]['vt_symbol']}-{data[0]['datetime']}插入成功或修改成功")
                else:
                    print(f"StockBarModel.insert : {data[0]['vt_symbol']}-{data[0]['datetime']}数据库已存在无需插入或更新")
            except Exception as e:
                print(f"StockBarModel.insert :{data[0]['vt_symbol']}-{data[0]['datetime']}error,错误信息为:{e}")


def dispose_csv_data(source_file, dir_name, folder_name):
    df = pd.read_csv(dir_name + source_file, encoding="gbk")

    if not df.empty:
        df.rename(columns={'时间': 'time'}, inplace=True)  # 修改 列名"时间" 为 "time"
        time_filter = ["08:59", "09:00", "09:01", "20:59", "21:00", "21:01"]
        # 使用and时,每个条件要用()括起再使用and连接
        df = df[~((df["增仓"].abs() >= df["现量"]) & (df.time.isin(time_filter) & (df["增仓"].abs() >= 10000)))]  # 过滤掉通达信换月移仓增仓数据错误问题

    df["volume"] = df["现量"]
    df["increase_decrease_position"] = df["增仓"]

    # print(df["volume"].sum())  # 成交量求和
    # chip_df = df.groupby(['成交'], as_index=False)["volume"].sum()

    chip_df = df.groupby(['价格'], as_index=False)["volume", "increase_decrease_position"].sum()  # 按照价格分组,成交量和增仓量进行求和操作。
    chip_df.rename(columns={'价格': 'price'}, inplace=True)  # 修改列名"成交" 为 "成交价"

    file_split_list = re.split("[_]", source_file)

    # chip_df["datetime"] = datetime.datetime.now().date()
    # chip_df["datetime"] = "2021-08-24"  # 添加交易日期
    chip_df["datetime"] = file_split_list[0][0:4] + "-" + file_split_list[0][4:6] + "-" + file_split_list[0][6:8]
    # chip_df["datetime"] = (datetime.datetime.now()+datetime.timedelta(days=-3)).date()  # 添加交易日期(日期减一)
    chip_df['interval'] = "d"

    # chip_df['vt_symbol'] = symbolLetter_exchange_map[re.match(r"[a-zA-z]+", source_file).group()]
    symbol_letter = folder_name[0:-1]
    chip_df['vt_symbol'] = symbolLetter_exchange_map[symbol_letter]

    # 删选出日期大于等于指定日期的数据
    # print(chip_df[chip_df["交易日期"] >= datetime.now().date()])

    # print(df["volume"].sum())  # 成交量求和
    # df.to_csv(f"{dir_name}chip_{filename}", index=False)

    # df列转list
    # print(chip_df["成交价"].to_list())
    # print(chip_df["成交量"].to_list())
    return chip_df


if __name__ == '__main__':
    source_folder_list = os.listdir("E:/jobs/通达信数据/主连/所有品种主连")
    # print(source_folder_list, len(source_folder_list))
    for folder_name in source_folder_list:
        dir_name = f"E:/jobs/通达信数据/主连/所有品种主连/{folder_name}/"
        # dir_name = f"E:/jobs/通达信数据/主连/{datetime.datetime.now().date()}/"
        source_file_list = os.listdir(dir_name)
        # print(source_file_list, len(source_file_list), folder_name)
        for source_file in source_file_list:
            df = dispose_csv_data(source_file, dir_name, folder_name)
            # print(df)
            if df.empty:
                continue
            TransactionDayDetailModel().batch_save_data(df)
