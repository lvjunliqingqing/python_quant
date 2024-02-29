# -*- coding : utf-8 -*-
# coding: utf-8

"""
@author：lv jun
把读取原始csv中的主连筹数据,把数据入库。
"""
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import re
import os
import pandas as pd
import datetime
import json
from copy import copy
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

from get_jq_history_data.symbolLetter_exchange_map import symbolLetter_exchange_map, symbol_exchange_map

setting = {
    "host": "192.168.20.119",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}

db = MySQLDatabase("vnpy", **setting)  # 连接数据库


def load_json(filepath: str) -> dict:
    """
    json文件读操作
    filepath:文件路径: "E:\jobs\designer_demo\python_验证\main_breed_record.json"
    """
    if os.path.isfile(filepath):
        with open(filepath, mode="r", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    else:
        save_json(filepath, {})
        return {}


def save_json(filepath: str, data: dict) -> None:
    """
    json写操作
    filepath:文件路径: "E:\jobs\designer_demo\python_验证\main_breed_record.json"
    """
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )



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
        data = df.to_dict('records')
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
    try:
        df['vt_symbol'] = symbolLetter_exchange_map[symbol_letter]
    except:
        symbol_letter = re.sub('[^a-zA-Z]', '', folder_name)
        df['vt_symbol'] = folder_name + "." + symbol_exchange_map[symbol_letter]

    return df


def many_multiprocess(source_file_list):
    cpu_nums = multiprocessing.cpu_count() - 4
    # 强制使用spawn方法创建新进程(而不是Linux上的fork)
    ctx = multiprocessing.get_context("spawn")
    pool = ctx.Pool(cpu_nums)
    threadPool = ThreadPoolExecutor(max_workers=4)

    # results = []
    for source_file in source_file_list:
        result = (pool.apply_async(dispose_csv_data, (source_file, dir_name, folder_name)))
        if not result.get().empty:
            threadPool.submit(SecondTransactionDayDetailModel().batch_save_data, result.get())   # 往数据库插入数据

    setting[folder_name] = list(set(setting.get(folder_name, [])).union(difference_set))  # 并上这些今天写入数据库的新文件名
    setting[folder_name].sort()  # 排序

    threadPool.shutdown(wait=True)

    pool.close()
    pool.join()

"""多进程+进程池进行逻辑运算,多线程+线程池进行数据库写操作,边逻辑运算边进行数据库读写操作"""
if __name__ == '__main__':
    current_folder_path = os.path.split(os.path.realpath(__file__))[0]  # 获取当前文件夹路径
    source_folder_list = os.listdir("E:/jobs/通达信数据/主连/所有品种主连")  # 所有主连文件夹名
    # data = {}
    setting = load_json(f"{current_folder_path}\original_main_breed_record.json")  # 获取已经写过入数据库的文件清单
    for folder_name in source_folder_list:
        dir_name = f"E:/jobs/通达信数据/主连/所有品种主连/{folder_name}/"
        source_file_list = os.listdir(dir_name)  # 单品主连文件夹所有文件名
        difference_set = set(source_file_list).difference(set(setting.get(folder_name, [])))  # 获取没有写入过数据库的文件(用的是两个列表求差集)
        if difference_set:
            many_multiprocess(difference_set)  # 多进程多线程处理数据
            setting[folder_name] = list(set(setting.get(folder_name, [])).union(difference_set))  # 并上这些今天写入数据库的新文件名
            setting[folder_name].sort()  # 排序

        # data[copy(folder_name)] = copy(source_file_list)
        # print(setting[folder_name][0], setting[folder_name][-1])

    save_json(f"{current_folder_path}\original_main_breed_record.json", setting)