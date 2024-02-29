
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


class OrderQueue:
    mq = None
    exchange = "order"
    insert_route_key = "insert.order"
    update_route_key = "update.order"

    def __init__(self):
        self.mq = RabbitMQ(RabbitmqCnf)
        self.mq.connect()

    def get_connect(self):
        if self.mq:
            return self.mq

    def push(self, order_data: OrderData):

        # if hasattr(order_data, 'gateway_name') and order_data.gateway_name == 'BACKTESTIN':
        #     return

        if not hasattr(order_data, 'extend'):
            order_data.extend = ''

        if hasattr(order_data, 'time') and order_data.time == '':
            order_data.time = datetime.datetime.now()

        if not hasattr(order_data, 'datetime'):
            order_data.datetime = datetime.datetime.now()

        data = {
            "account_id": order_data.account_id,
            "frozen": order_data.frozen,
            "balance": order_data.balance,
            "symbol": order_data.symbol,
            "strategy_name": order_data.strategy_name,
            "strategy_class_name": order_data.strategy_class_name,
            "exchange": order_data.exchange.name,
            "orderid": order_data.orderid,
            "order_type": order_data.type.name,
            "direction": order_data.direction.name,
            "strategy_author": order_data.strategy_author,
            "offset": order_data.offset.name,
            "price": order_data.price,
            "volume": order_data.volume,
            "traded": order_data.traded,
            "status": order_data.status.name,
            "datetime": order_data.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "time": order_data.time,
            "gateway_name": order_data.gateway_name,
            "extend": order_data.extend
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
