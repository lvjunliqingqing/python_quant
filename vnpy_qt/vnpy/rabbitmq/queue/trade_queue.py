import datetime

from vnpy.rabbitmq.config.rabbitmq import RabbitmqCnf
from vnpy.rabbitmq.queue.rabbitmq import RabbitMQ
from vnpy.trader.object import TradeData

import json


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)


class TradeQueue:
    mq = None
    exchange = "trade"
    insert_route_key = "insert.trade"
    update_route_key = "update.trade"

    def __init__(self):
        self.mq = RabbitMQ(RabbitmqCnf)
        self.mq.connect()

    def get_connect(self):
        if self.mq:
            return self.mq

    def push(self, trade_data: TradeData):
        if not hasattr(trade_data, 'extend'):
            trade_data.extend = ''

        if hasattr(trade_data, 'time') and trade_data.time == '':
            trade_data.time = datetime.datetime.now()

        if not hasattr(trade_data, 'datetime'):
            trade_data.datetime = datetime.datetime.now()

        data = {
            "account_id": trade_data.account_id,
            "frozen": trade_data.frozen,
            "balance": trade_data.balance,
            "symbol": trade_data.symbol,
            "strategy_name": trade_data.strategy_name,
            "strategy_class_name": trade_data.strategy_class_name,
            "exchange": trade_data.exchange.name,
            "orderid": trade_data.orderid,
            "tradeid": trade_data.tradeid,
            "direction": trade_data.direction.name,
            "strategy_author": trade_data.strategy_author,
            "offset": trade_data.offset.name,
            "price": trade_data.price,
            "volume": trade_data.volume,
            "datetime": trade_data.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "time": trade_data.time,
            "gateway_name": trade_data.gateway_name,
            "extend": trade_data.extend
        }

        self.mq.put(json.dumps(data, cls=DateEncoder), route_key=self.insert_route_key, exchange=self.exchange)

    def pop(self, queue_name, exchange, route_key, callback, durable=True):
        self.mq.get(
            queue_name=queue_name,
            exchange=exchange,
            route_key=route_key,
            on_message_callback=callback,
            durable=durable
        )
