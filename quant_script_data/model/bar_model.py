from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
)

from model.db import db

class BarModel(Model):
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
        database = db  #
        table_name = 'dbbardata'  # 这里可以自定义表名

    def get_futures_bar_data(self, i):
        symbol = i.symbol.split(".")[0]
        bar_data = BarModel.select().where((BarModel.symbol == symbol) & (BarModel.interval == "d"))
        bar_data = bar_data.order_by(BarModel.datetime.desc())
        return bar_data