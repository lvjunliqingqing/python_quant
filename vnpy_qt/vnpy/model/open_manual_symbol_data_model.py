
from vnpy.model.base_model import BaseModel
from peewee import *


class OpenManualSymbolModel(BaseModel):
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

    def query_open_data(self, account_id, strategy_class_name):
        open_data = OpenManualSymbolModel.select().where(
            (OpenManualSymbolModel.status == 1)
            & (OpenManualSymbolModel.audit_status == 1)
            & (OpenManualSymbolModel.account_id == account_id)
            & (OpenManualSymbolModel.strategy_name == strategy_class_name)
        )
        return open_data

    class Meta:
        table_name = 'js_open_manual_symbol_data'
