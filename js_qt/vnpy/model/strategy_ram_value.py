from vnpy.model.base_model import BaseModel
from peewee import *
import json


class RamValue(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    strategy_class_name = CharField()
    symbol = CharField()
    strategy_name = CharField()
    strategy_value = CharField()
    account_id = CharField()

    class Meta:
        table_name = 'js_strategy_ram_value'

    def insert_value(self, class_name, symbol, strategy_name, strategy_value, account_id):
        strategy_value = json.dumps(strategy_value)
        sql = RamValue().insert(
            strategy_class_name=class_name,
            symbol=symbol,
            strategy_name=strategy_name,
            strategy_value=strategy_value,
            account_id=account_id
        ).on_conflict(
            preserve=[
                RamValue.strategy_class_name,
                RamValue.symbol,
                RamValue.strategy_name,
                RamValue.strategy_value,
                RamValue.account_id
            ]
        )
        return sql.execute()

    def search_value(self, strategy_name, account_id):
        try:
            data = RamValue.get(strategy_name=strategy_name, account_id=account_id)
            value = json.loads(data.strategy_value)
            return value
        except:
            return None

    def cancel_data(self, strategy_name, account_id):
        sql = RamValue.delete().where(
            RamValue.strategy_name == strategy_name,
            RamValue.account_id == account_id
        ).execute()
        return sql

    def update_data(self, strategy_name, strategy_value):
        strategy_value = json.dumps(strategy_value)
        sql = RamValue.update(
            strategy_value=strategy_value
        ).where(
            RamValue.strategy_name == strategy_name
        ).execute()
        return sql

