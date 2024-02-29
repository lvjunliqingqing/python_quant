import base64
import time
import datetime
from jqdatasdk import *
from peewee import (
    AutoField,
    CharField,
    DateField,
    Model,
    MySQLDatabase,
)

settings = {
    'host': '192.168.0.250',
    'user': 'stock',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8'
}
db = MySQLDatabase("stock", **settings)
auth('18520128569', (base64.b64decode(b'Y2hhbzM0MzM1NDE3').decode()))


class SecuritiesInfoModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField(null=False)
    display_name = CharField(null=False)
    name_code = CharField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    sec_type = CharField(null=False)

    class Meta:
        database = db
        table_name = 'securities_info'


class StockIndustryModel(Model):
    code = CharField(max_length=20, null=False, verbose_name="股票代码")
    industry = CharField(max_length=255, verbose_name="股票所属行业(证监会行业)")

    class Meta:
        database = db
        table_name = 'stock_industry'

    def batch_sava_stock_industry(self, industry):
        data = []
        for row in industry:
            data.append(
                {
                    "code": row,
                    "industry": industry[row]["zjw"]["industry_name"]
                }
            )
        with db.atomic():
            sql = StockIndustryModel.insert_many(data)\
                .on_conflict(
                    preserve=[
                        StockIndustryModel.code,
                        StockIndustryModel.industry
                    ]
            )
            if sql.execute():
                print(f"ok")
            else:
                print(f"error")

    def get_stock_industry_data(self):
        sql = f"select * from securities_info where symbol REGEXP '^[0-9].*' and end_date >= '{datetime.datetime.now().strftime('%Y-%m-%d')}'"
        print(sql)
        sec_list = SecuritiesInfoModel.raw(sql)
        symbol_list = []
        for row in sec_list:
            symbol_list.append(row.symbol)
        d = get_industry(security=symbol_list, date="2020-08-17")
        with db.atomic():
            self.batch_sava_stock_industry(d)
        time.sleep(1)


if __name__ == "__main__":
    StockIndustryModel().get_stock_industry_data()
