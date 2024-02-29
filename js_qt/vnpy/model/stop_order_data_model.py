import datetime

from peewee import *

from vnpy.app.cta_strategy import (
    OrderData,
)
from vnpy.model.base_model import BaseModel


class StopOrderDataModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    account_id = FloatField()
    frozen = FloatField()
    balance = FloatField()
    vt_symbol = CharField()
    strategy_name = CharField()
    strategy_class_name = CharField(100)
    exchange = CharField()
    vt_orderids = CharField()  # vt_orderids=[order.vt_orderid]
    stop_orderid = CharField()  # stop_orderid=order.vt_orderid
    direction = CharField()
    strategy_author = CharField()
    offset = CharField()
    price = FloatField()
    volume = FloatField()
    traded = FloatField()
    status = CharField()
    datetime = DateTimeField()
    time = DateTimeField()
    gateway_name = CharField()
    extend = TextField()

    def save_order_data(self, stop_order_data: OrderData):
        """"""

        if hasattr(stop_order_data, 'gateway_name') and stop_order_data.gateway_name == 'BACKTESTIN':
            return

        if not hasattr(stop_order_data, 'extend'):
            stop_order_data.extend = ''
        if hasattr(stop_order_data, 'time') and stop_order_data.time is "":
            stop_order_data.time = datetime.datetime.strftime("%Y-%m-%d %H:%M:%S")

        data_source = [
            {
                "symbol": stop_order_data.symbol,
                "strategy_name": stop_order_data.strategy_name,
                "strategy_class_name": stop_order_data.strategy_class_name,
                "exchange": stop_order_data.exchange.name,
                "orderid": stop_order_data.orderid,
                "stop_order_type": stop_order_data.type.name,
                "direction": stop_order_data.direction.name,
                "strategy_author": stop_order_data.strategy_author,
                "offset": stop_order_data.offset.name,
                "price": stop_order_data.price,
                "volume": stop_order_data.volume,
                "traded": stop_order_data.traded,
                "status": stop_order_data.status.name,
                "datetime": stop_order_data.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "time": stop_order_data.time,
                "gateway_name": stop_order_data.gateway_name,
                "extend": stop_order_data.extend
            }
        ]

        sql = self.insert_many(data_source)

        return sql.execute()

    def save_order_data_from_json(self, stop_order_data: dict):
        """"""

        if stop_order_data['time'] is "":
            stop_order_data['time'] = datetime.datetime.strftime("%Y-%m-%d %H:%M:%S")

        data_source = [
            {
                "account_id":stop_order_data['account_id'],
                "frozen":stop_order_data['frozen'],
                "balance":stop_order_data['balance'],
                "vt_symbol": stop_order_data['vt_symbol'],
                "strategy_name": stop_order_data['strategy_name'],
                "strategy_class_name": stop_order_data['strategy_class_name'],
                "exchange": stop_order_data['exchange'],
                "vt_orderids": stop_order_data['vt_orderids'],
                "stop_orderid": stop_order_data['stop_orderid'],
                "direction": stop_order_data['direction'],
                "strategy_author": stop_order_data['strategy_author'],
                "offset": stop_order_data['offset'],
                "price": stop_order_data['price'],
                "volume": stop_order_data['volume'],
                "status": stop_order_data['status'],
                "datetime": stop_order_data['datetime'],
                "time": stop_order_data['time'],
                "gateway_name": stop_order_data['gateway_name'],
                "extend": stop_order_data['extend']
            }
        ]

        sql = self.insert_many(data_source)
        return sql.execute()

    class Meta:
        table_name = 'stop_order_data'
