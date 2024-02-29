import datetime

from vnpy.rabbitmq.config.rabbitmq import RabbitmqCnf
from vnpy.rabbitmq.queue.rabbitmq import RabbitMQ
from vnpy.trader.object import OrderData
import json


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)


class StopOrderQueue:
    mq = None
    exchange = "stop_order"
    insert_route_key = "insert.stop_order"
    update_route_key = "update.stop_order"

    def __init__(self):
        self.mq = RabbitMQ(RabbitmqCnf)
        self.mq.connect()

    def get_connect(self):
        if self.mq:
            return self.mq

    def push(self, stop_order_data: OrderData):

        if not hasattr(stop_order_data, 'extend'):
            stop_order_data.extend = ''

        if not hasattr(stop_order_data, 'time'):
            stop_order_data.time = datetime.datetime.now()

        if not hasattr(stop_order_data, 'datetime'):
            stop_order_data.datetime = datetime.datetime.now()

        if stop_order_data.vt_symbol:
            tmp = stop_order_data.vt_symbol.split('.')
            stop_order_data.exchange = tmp[1]
            stop_order_data.symbol = tmp[0]

        if type(stop_order_data.vt_orderids).__name__ == 'list':
            stop_order_data.vt_orderids = ','.join(stop_order_data.vt_orderids)

        if not hasattr(stop_order_data, 'gateway_name'):
            stop_order_data.gateway_name = ''

        data = {
            "account_id": stop_order_data.account_id,
            "frozen": stop_order_data.frozen,
            "balance": stop_order_data.balance,
            "vt_symbol": stop_order_data.symbol,
            "strategy_name": stop_order_data.strategy_name,
            "strategy_class_name": stop_order_data.strategy_class_name,
            "exchange": stop_order_data.exchange,
            "vt_orderids": stop_order_data.vt_orderids,
            "stop_orderid": stop_order_data.stop_orderid,
            "lock": stop_order_data.lock,
            "direction": stop_order_data.direction.name,
            "strategy_author": stop_order_data.strategy_author,
            "offset": stop_order_data.offset.name,
            "price": stop_order_data.price,
            "volume": stop_order_data.volume,
            "status": stop_order_data.status.name,
            "datetime": stop_order_data.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "time": stop_order_data.time,
            "gateway_name": stop_order_data.gateway_name,
            "extend": stop_order_data.extend
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
