import datetime

from peewee import (
    CharField,
    DateField,
    Model,
)

from model.bar_model import BarModel
from model.db import db


class SecuritiesInfoModel(Model):
    symbol = CharField(null=False)
    display_name = CharField(null=False)
    name_code = CharField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    sec_type = CharField(null=False)

    class Meta:
        database = db  # 这里是数据库链接，为了方便建立多个表，可以把这个部分提炼出来形成一个新的类
        table_name = 'securities_info'  # 这里可以自定义表名

    def get_futures_securities_info(self):
        curr_date = datetime.datetime.now().strftime('%Y-%m-%d')
        securities_info = SecuritiesInfoModel.select().where((SecuritiesInfoModel.sec_type == "futures") & (SecuritiesInfoModel.symbol.regexp(".*9999.*")) & (SecuritiesInfoModel.end_date >= curr_date))
        # securities_info = SecuritiesInfoModel.select().where((SecuritiesInfoModel.sec_type == "futures") & (SecuritiesInfoModel.symbol.regexp(".*9999.*"))).dicts()
        return securities_info

    def main_futures_map(self):
        map_info = {}
        for info in self.get_futures_securities_info():
            tmp = info.symbol.split('.')
            sql = f"SELECT  * FROM dbbardata AS t2 WHERE  symbol!='{tmp[0]}' and t2.volume = (SELECT volume FROM dbbardata WHERE symbol = '{tmp[0]}' and exchange='{tmp[1]}' AND `interval` = 'd' ORDER BY datetime DESC LIMIT 1) limit 1"
            map_data = BarModel().raw(sql)
            for row in map_data:
                map_info[f"{tmp[0]}.{tmp[1]}"] = row.symbol
        return map_info
