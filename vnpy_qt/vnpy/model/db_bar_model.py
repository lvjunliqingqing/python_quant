
import re
from peewee import *
from vnpy.app.cta_strategy.convert import Convert
from vnpy.model.base_model import BaseModel


class DbBarModel(BaseModel):

    id = AutoField(primary_key=True)
    symbol = CharField()
    exchange = CharField()
    datetime = DateTimeField()
    interval = CharField()
    volume = IntegerField()
    open_interest = FloatField()
    open_price = FloatField()
    close_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()

    class Meta:
        table_name = 'dbbardata'

    def get_month_avg_volume(self, start_date=None, symbol=None, exchange=None):
        """获取月平均成交量"""
        symbol = re.match(r'^[a-zA-Z]+', symbol).group().upper()
        exchange = Convert().convert_jqdata_exchange(exchange=exchange).value
        sql = f"SELECT AVG(volume) AS vol, AVG(volume)/60 as min_vol FROM dbbardata WHERE  `datetime` >= '{start_date}' AND symbol='{symbol}9999' AND `interval`='1m' AND exchange='{exchange}' limit 1"
        ret = self.raw(sql)
        vol = None
        min_vol = None

        for row in ret:
            vol = row.vol
            min_vol = row.min_vol

        return vol, min_vol

