from peewee import *

from vnpy.model.base_model import BaseModel


class StrategyNameModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    strategy_class_name = CharField()
    strategy_name = CharField()
    strategy_args = CharField()
    strategy_no = CharField()
    strategy_desc = CharField()
    link_table = CharField()
    open_is = BooleanField()
    exchange = CharField()
    symbol = CharField()
    direction = CharField()

    def select_strategy_data(self):
        strategy_data = StrategyNameModel().select()
        return strategy_data

    class Meta:
        table_name = 'js_strategy_desc'



