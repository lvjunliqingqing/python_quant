"""
@author：lv jun
获取所有标的物信息存储到数据库中
"""
from datetime import datetime
from jqdatasdk import *
from peewee import (
    MySQLDatabase,
    Model,
    AutoField,
    CharField,
    DateField,
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

    def batch_save_data(self, df):
        data = []
        for idx, row in df.iterrows():
            data.append({
                "symbol": idx,
                "display_name": row["display_name"],
                "name_code": row["name"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "sec_type": row["type"]
            })
        with db.atomic():
            sql = SecuritiesInfoModel.insert_many(data).on_conflict(
                preserve=[
                    SecuritiesInfoModel.symbol,
                    SecuritiesInfoModel.display_name,
                    SecuritiesInfoModel.name_code,
                    SecuritiesInfoModel.start_date,
                    SecuritiesInfoModel.end_date,
                    SecuritiesInfoModel.sec_type
                ]
            )
            try:
                ret = sql.execute()
                if ret:
                    print("SecuritiesInfoModel.insert : 插入成功或修改成功")
                else:
                    print("SecuritiesInfoModel.insert : 数据库已存在无需插入或更新")
            except Exception as e:
                print(f"SecuritiesInfoModel.insert :error,错误信息为:{e}")

    def get_all_securities(self):
        # date指定日期时间,表示此时还在上市交易的
        df = get_all_securities(['futures'], date=datetime.now())
        # 缺失值处理
        df.dropna(axis=0, how='all', inplace=True)
        self.batch_save_data(df)


if __name__ == '__main__':
    SecuritiesInfoModel().get_all_securities()
