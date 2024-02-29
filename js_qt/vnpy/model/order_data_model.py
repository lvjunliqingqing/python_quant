import datetime
from vnpy.model.base_model import BaseModel, db
from peewee import *


class OrderDataModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    account_id = CharField()
    frozen = FloatField()
    balance = FloatField()
    symbol = CharField()
    exchange = CharField()
    order_ref = CharField()
    strategy_name = CharField()
    strategy_class_name = CharField(100)
    orderid = CharField(64)
    order_type = CharField()
    direction = CharField()
    strategy_author = CharField()
    offset = CharField()
    price = FloatField()
    volume = FloatField()
    traded = FloatField()
    status = CharField()
    time = TimeField()
    order_time = DateTimeField()
    gateway_name = CharField()
    extend = TextField()
    order_sys_id = CharField()
    order_local_id = CharField()
    run_type = CharField()

    def get_one(self,
                order_ref=None,
                account_id=None,
                symbol=None,
                exchange=None,
                gateway_name=None,
                run_type=None
                ):

        try:

            return self.get(
                OrderDataModel.order_ref == order_ref,
                OrderDataModel.account_id == account_id,
                OrderDataModel.symbol == symbol,
                OrderDataModel.exchange == exchange,
                OrderDataModel.gateway_name == gateway_name,
                OrderDataModel.run_type == run_type,
            )
        except DoesNotExist:

            return None

    def save_order_data(self, order_data):
        """
        保存委托单
        """

        if hasattr(order_data, 'gateway_name') and order_data.gateway_name == 'BACKTESTIN':
            return

        if not hasattr(order_data, 'extend'):
            order_data.extend = ''
        if hasattr(order_data, 'time') and order_data.time is "":
            order_data.time = datetime.datetime.now().strftime("%H:%M:%S")

        sql = self.insert(
            account_id=order_data.account_id,
            frozen=order_data.frozen,
            balance=order_data.balance,
            symbol=order_data.symbol,
            strategy_name=order_data.strategy_name,
            strategy_class_name=order_data.strategy_class_name,
            exchange=order_data.exchange.name,
            orderid=order_data.orderid,
            order_ref=order_data.order_ref,
            order_type=order_data.type.name,
            direction=order_data.direction.name,
            strategy_author=order_data.strategy_author,
            offset=order_data.offset.name,
            price=order_data.price,
            volume=order_data.volume,
            traded=order_data.traded,
            status=order_data.status.name,
            time=order_data.time,
            order_time=order_data.order_time,
            gateway_name=order_data.gateway_name,
            extend=order_data.extend,
            order_sys_id=order_data.order_sys_id,
            order_local_id=order_data.order_local_id,
            run_type=order_data.run_type,
        ).on_conflict(
            preserve=[
                OrderDataModel.price, OrderDataModel.traded, OrderDataModel.order_type,
                OrderDataModel.volume, OrderDataModel.offset, OrderDataModel.extend,
                OrderDataModel.status, OrderDataModel.direction, OrderDataModel.order_ref,
                OrderDataModel.order_sys_id, OrderDataModel.order_local_id,
            ]
        )
        return sql.execute()

    def save_order_data_from_json(self, order_data: dict):
        """"""

        if order_data['time'] is "":
            order_data['time'] = datetime.datetime.strftime("%Y-%m-%d %H:%M:%S")

        data_source = [
            {
                "account_id": order_data['account_id'],
                "frozen": order_data['frozen'],
                "balance": order_data['balance'],
                "symbol": order_data['symbol'],
                "strategy_name": order_data['strategy_name'],
                "strategy_class_name": order_data['strategy_class_name'],
                "exchange": order_data['exchange'],
                "orderid": order_data['orderid'],
                "order_type": order_data['order_type'],
                "direction": order_data['direction'],
                "strategy_author": order_data['strategy_author'],
                "offset": order_data['offset'],
                "price": order_data['price'],
                "volume": order_data['volume'],
                "traded": order_data['traded'],
                "status": order_data['status'],
                "datetime": order_data['datetime'],
                "time": order_data['time'],
                "order_time": order_data['order_time'] if hasattr(order_data, 'order_time') else order_data['datetime'],
                "gateway_name": order_data['gateway_name'],
                "extend": order_data['extend']
            }
        ]

        sql = self.insert_many(data_source)
        return sql.execute()

    class Meta:
        table_name = 'order_data'

    def update_order_status(self, order_data):

        if not order_data.order_ref:
            return False

        sql = self.update(
            status=order_data.status.name,
            order_sys_id=order_data.order_sys_id,
            order_local_id=order_data.order_local_id,
            traded=order_data.traded,
        ).where(
            (OrderDataModel.order_ref == order_data.order_ref)
            & (OrderDataModel.orderid == order_data.orderid)
        ).limit(1)

        return sql.execute()

    def volume_divided_into_one(self, order_data):
        list_data = []
        for data in order_data:
            if hasattr(data, 'gateway_name') and data.gateway_name == 'BACKTESTIN':

                return

            if not hasattr(data, 'extend'):
                data.extend = ''
            if hasattr(data, 'time') and data.time is "":
                data.time = datetime.datetime.now().strftime("%H:%M:%S")

            data_list = {
                "account_id": data.account_id,
                "frozen": data.frozen,
                "balance": data.balance,
                "symbol": data.symbol,
                "strategy_name": data.strategy_name,
                "strategy_class_name": data.strategy_class_name,
                "exchange": data.exchange.name,
                "orderid": data.orderid,
                "order_ref": data.order_ref,
                "order_type": data.type.name,
                "direction": data.direction.name,
                "strategy_author": data.strategy_author,
                "offset": data.offset.name,
                "price": data.price,
                "volume": data.volume,
                "traded": data.traded,
                "status": data.status.name,
                "time": data.time,
                "order_time": data.order_time,
                "gateway_name": data.gateway_name,
                "extend": data.extend,
                "order_sys_id": data.order_sys_id,
                "order_local_id": data.order_local_id,
                "run_type": data.run_type
            }
            list_data.append(data_list)
        with db.atomic():
            sql = self.insert_many(list_data).execute()
            return sql
