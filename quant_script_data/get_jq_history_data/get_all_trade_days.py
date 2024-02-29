"""
@author：lv jun
获取所有交易日期
"""
from jqdatasdk import *
from peewee import (
    MySQLDatabase,
    Model,
    AutoField,
    DateField
)

setting = {
    "host": "192.168.20.119",
    "user": "root",
    "password": "Js@1234560",
    "port": 3306,
    "charset": "utf8"
}
auth('18578664901', 'Apple12320')


print(get_query_count())

db = MySQLDatabase("vnpy", **setting)


class TradeDayModel(Model):
    id = AutoField(primary_key=True)
    trade_date = DateField(null=False)

    class Meta:
        database = db
        table_name = 'trade_days'

    def save_all_trade_days(self):
        trade_datas = get_all_trade_days()  # 从聚宽中获取所有交易日期,返回一个包含所有交易日的 [numpy.ndarray], 每个元素为一个 [datetime.date] 类型.。
        data = []
        for i in trade_datas:
            data.append({
                "trade_date": i
            })
        with db.atomic():
            sql = TradeDayModel.insert_many(data).on_conflict(
                preserve=[TradeDayModel.trade_date]
            )
            try:
                ret = sql.execute()
                if ret:
                    print("TradeDayModel.insert : 插入成功或修改成功")
                else:
                    print("TradeDayModel.insert : 数据库已存在无需插入或更新")
            except Exception as e:
                print(f"TradeDayModel.insert :error,错误信息为:{e}")


if __name__ == "__main__":
    TradeDayModel().save_all_trade_days()







