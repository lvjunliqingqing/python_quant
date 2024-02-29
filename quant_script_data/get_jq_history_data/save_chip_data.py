"""
@author：lv jun
把读取原始csv中的筹数据,把数据入库。
"""
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

setting = {
    "host": "192.168.20.111",
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
                "price": row["price"]
            })
        with db.atomic():
            sql = TransactionDayDetailModel.insert_many(data).on_conflict(
                preserve=[
                    TransactionDayDetailModel.vt_symbol,
                    TransactionDayDetailModel.datetime,
                    TransactionDayDetailModel.interval,
                    TransactionDayDetailModel.volume,
                    TransactionDayDetailModel.price
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


def dispose_csv_data():
    filename = f"ru2109-{datetime.datetime.now().date()}.csv"
    # filename = "ru2109-2021-06-18.csv"
    dir_name = f"E:/jobs/designer_demo/data_table_process/"
    df = pd.read_csv(dir_name+filename, encoding='gbk')
    # 从"现手"这一列删选出数字部分数据
    # expanded = df.现手.str.extractall(r"(\d+(?:\.\d+)?)")
    # print(expanded)

    # df["volume"] = expanded.unstack()
    # df["volume"] = pd.to_numeric(df["volume"], errors='coerce')  # 字符串转数字
    df["volume"] = df["现量"]

    # print(df["volume"].sum())  # 成交量求和
    # df.to_csv(f"{dir_name}new_{filename}", index=False)

    # chip_df = df.groupby(['成交'], as_index=False)["volume"].sum()
    # chip_df.rename(columns={'成交': 'price'}, inplace=True)  # 修改 列名"成交" 为 "成交价"

    chip_df = df.groupby(['价格'], as_index=False)["volume"].sum()
    chip_df.rename(columns={'价格': 'price'}, inplace=True)  # 修改 列名"成交" 为 "成交价"

    chip_df["datetime"] = datetime.datetime.now().date()  # 添加交易日期
    # chip_df["datetime"] = (datetime.datetime.now()+datetime.timedelta(days=-3)).date()  # 添加交易日期(日期减一)
    chip_df['interval'] = "d"
    chip_df['vt_symbol'] = "RU2109.XSGE"

    # 删选出日期大于等于指定日期的数据
    # print(chip_df[chip_df["交易日期"] >= datetime.now().date()])

    # print(df["volume"].sum())  # 成交量求和
    # df.to_csv(f"{dir_name}chip_{filename}", index=False)

    # df列转list
    # print(chip_df["成交价"].to_list())
    # print(chip_df["成交量"].to_list())
    return chip_df


if __name__ == '__main__':
    df = dispose_csv_data()
    # print(df)
    TransactionDayDetailModel().batch_save_data(df)
