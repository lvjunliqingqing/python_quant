from peewee import *
from vnpy.model.base_model import BaseModel


class OpenSymbolModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    account_id = CharField()
    symbol = CharField()
    exchange = CharField()
    direction = CharField()
    offset = CharField()
    status = BooleanField()
    audit_status = BooleanField()
    strategy_name = CharField()
    strategy_args = CharField()

    class Meta:
        table_name = 'js_open_symbol_data'

    def query_open_data(self, account_id, strategy_class_name):
        """查询用来开仓的合约数据"""
        open_data = OpenSymbolModel.select().where(
            (OpenSymbolModel.status != 0)
            & (OpenSymbolModel.audit_status != 0)
            & (OpenSymbolModel.account_id == account_id)
            & (OpenSymbolModel.strategy_name == strategy_class_name)
        )
        return open_data


