import datetime
from vnpy.model.base_model import BaseModel, db
from peewee import *

from vnpy.model.order_data_model import OrderDataModel


class TradeDataModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    account_id = CharField()
    frozen = FloatField()
    balance = FloatField()
    symbol = CharField()
    strategy_name = CharField()
    strategy_class_name = CharField(100)
    exchange = CharField()
    orderid = CharField()
    order_time = CharField()
    tradeid = CharField()
    direction = CharField()
    strategy_author = CharField()
    offset = CharField()
    price = FloatField()
    close_price = FloatField()
    close_date = DateTimeField()
    un_volume = FloatField()
    volume = FloatField()
    time = TimeField()
    utime = DateTimeField()
    atime = DateTimeField()
    trade_date = DateTimeField()
    gateway_name = CharField()
    extend = TextField()
    run_type = TextField()
    order_sys_id = CharField()
    order_local_id = CharField()
    order_ref = CharField()
    win_price = FloatField()
    loss_price = FloatField()
    trade_src = CharField()
    p_orderid = CharField()
    trade_option = CharField()
    error_order = BooleanField()

    class Meta:
        table_name = 'trade_data'

    def save_trade_data(self, trade_data):
        """一次向数据库中保存一条成交数据"""
        if hasattr(trade_data, 'gateway_name') and trade_data.gateway_name == 'BACKTESTIN':
            return

        if not hasattr(trade_data, 'extend'):
            trade_data.extend = ''
        if hasattr(trade_data, 'time') and trade_data.time is "":
            trade_data.time = trade_data.datetime.strftime("%H:%M:%S")

        if not hasattr(trade_data, 'win_price'):
            trade_data.win_price = 0

        if not hasattr(trade_data, 'loss_price'):
            trade_data.loss_price = 0

        sql = TradeDataModel().insert(
            account_id=trade_data.account_id,
            frozen=trade_data.frozen,
            balance=trade_data.balance,
            symbol=trade_data.symbol,
            strategy_name=trade_data.strategy_name,
            strategy_class_name=trade_data.strategy_class_name,
            strategy_author=trade_data.strategy_author,
            exchange=trade_data.exchange.name,
            orderid=trade_data.orderid,
            order_ref=trade_data.order_ref,
            tradeid=trade_data.tradeid,
            direction=trade_data.direction.name,
            offset=trade_data.offset.name,
            price=trade_data.price,
            win_price=trade_data.win_price,
            loss_price=trade_data.loss_price,
            un_volume=trade_data.volume,
            volume=trade_data.volume,
            trade_date=trade_data.trade_date,
            order_time=trade_data.order_time,
            time=trade_data.time,
            gateway_name=trade_data.gateway_name,
            extend=trade_data.extend,
            order_sys_id=trade_data.order_sys_id,
            order_local_id=trade_data.order_local_id,
            run_type=trade_data.run_type,
            trade_src=trade_data.trade_src if hasattr(trade_data, 'trade_src') else 'vnpy',
            p_orderid=trade_data.p_orderid,
            trade_option=trade_data.trade_option,
        ).on_conflict(
            preserve=[
                TradeDataModel.price,
                TradeDataModel.volume,
                TradeDataModel.offset,
                TradeDataModel.extend,
                TradeDataModel.direction,
                TradeDataModel.order_sys_id,
                TradeDataModel.order_local_id
            ]
        )
        return sql.execute()

    def save_trade_data_from_json(self, trade_data: object) -> object:
        """用一次性插入多条的方式向数据库中插入一条成交单"""

        if trade_data['time'] is "":
            trade_data['time'] = datetime.datetime.strftime("%Y-%m-%d %H:%M:%S")

        data_source = [
            {
                "account_id": (trade_data['userid'] if trade_data['userid'] else trade_data['account_id']),
                "frozen": trade_data['frozen'],
                "balance": trade_data['balance'],
                "symbol": trade_data['symbol'],
                "strategy_name": trade_data['strategy_name'],
                "strategy_class_name": trade_data['strategy_class_name'],
                "exchange": trade_data['exchange'],
                "orderid": trade_data['orderid'],
                "tradeid": trade_data['tradeid'],
                "direction": trade_data['direction'],
                "strategy_author": trade_data['strategy_author'],
                "offset": trade_data['offset'],
                "price": trade_data['price'],
                "volume": trade_data['volume'],
                "trade_date": trade_data['trade_date'],
                "order_time": trade_data['datetime'],
                "time": trade_data['time'],
                "gateway_name": trade_data['gateway_name'],
                "extend": trade_data['extend']
            }
        ]

        sql = self.insert_many(data_source)
        return sql.execute()

    def save_widget_event_trade_data(self, trade_data):
        """委托单在数据库中存在时,才保存成交单数据到数据库"""
        OrderInfo = OrderDataModel().get_one(
            order_ref=trade_data.order_ref,
            account_id=trade_data.account_id,
            symbol=trade_data.symbol,
            exchange=trade_data.exchange.name,
            gateway_name=trade_data.gateway_name,
            run_type='undersell'
        )

        if OrderInfo:
            trade_data.strategy_name = OrderInfo.strategy_name
            trade_data.strategy_class_name = OrderInfo.strategy_class_name
            trade_data.strategy_author = OrderInfo.strategy_author
            trade_data.order_time = OrderInfo.order_time
            trade_data.run_type = OrderInfo.run_type

            if self.save_trade_data(trade_data):
                print(trade_data)
            else:
                print('error', trade_data)

    def select_order_data(self, strategy_name, strategy_class_name, symbol, account_id):
        """根据合约代码、策略名、账号id、策略类名查询在成交表中查询未平仓的数据,查询不到返回空的查询集"""
        trade_data = TradeDataModel().select().where(
            (TradeDataModel.symbol == symbol)
            & (TradeDataModel.account_id == account_id)
            & (TradeDataModel.un_volume != 0)
            & (TradeDataModel.offset == 'OPEN')
            & (TradeDataModel.strategy_name == strategy_name)
            & (TradeDataModel.strategy_class_name == strategy_class_name)
            & (TradeDataModel.gateway_name == 'CTP')
        )
        return trade_data

    def query_open_positions_data(self, strategy_name, strategy_class_name, account_id):
        """根据策略名、账号id、策略类名查询在成交表中查询未平仓的数据,查询不到返回空的查询集"""
        trade_data = TradeDataModel().select().where(
            (TradeDataModel.account_id == account_id)
            & (TradeDataModel.offset == 'OPEN')
            & (TradeDataModel.un_volume != 0)
            & (TradeDataModel.strategy_name == strategy_name)
            & (TradeDataModel.strategy_class_name == strategy_class_name)
            & (TradeDataModel.gateway_name == 'CTP')
        )
        return trade_data

    def query_all_position_data(self, account_id):
        """查询单账号CTP所有持仓数据"""
        trade_data = TradeDataModel().select().where(
            (TradeDataModel.account_id == account_id)
            & (TradeDataModel.offset == 'OPEN')
            & (TradeDataModel.un_volume != 0)
            & (TradeDataModel.gateway_name == 'CTP')
        )
        return trade_data

    def update_loss_win_price(self, order_data, loss_price, win_price):
        """更新止盈止损价"""
        sql = TradeDataModel().update(
            loss_price=loss_price,
            win_price=win_price
        ).where(
            TradeDataModel.orderid == order_data.orderid
        )
        if sql.execute():
            print(order_data.orderid, "止盈止损价格修改成功")

    def volume_divided_into_one(self, data):
        list_data = []
        for trade_data in data:

            if hasattr(trade_data, 'gateway_name') and trade_data.gateway_name == 'BACKTESTIN':
                return

            if not hasattr(trade_data, 'extend'):
                trade_data.extend = ''
            if hasattr(trade_data, 'time') and trade_data.time is "":
                trade_data.time = trade_data.datetime.strftime("%H:%M:%S")

            data_list = {
                "account_id": trade_data.account_id,
                "frozen": trade_data.frozen,
                "balance": trade_data.balance,
                "symbol": trade_data.symbol,
                "strategy_name": trade_data.strategy_name,
                "strategy_class_name": trade_data.strategy_class_name,
                "strategy_author": trade_data.strategy_author,
                "exchange": trade_data.exchange.name,
                "orderid": trade_data.orderid,
                "order_ref": trade_data.order_ref,
                "tradeid": trade_data.tradeid,
                "direction": trade_data.direction.name,
                "offset": trade_data.offset.name,
                "price": trade_data.price,
                "volume": trade_data.volume,
                "trade_date": trade_data.trade_date,
                "order_time": trade_data.order_time,
                "time": trade_data.time,
                "gateway_name": trade_data.gateway_name,
                "extend": trade_data.extend,
                "order_sys_id": trade_data.order_sys_id,
                "order_local_id": trade_data.order_local_id,
                "run_type": trade_data.run_type,
                "trade_src": trade_data.trade_src if hasattr(trade_data, 'trade_src') else 'vnpy',
            }
            list_data.append(data_list)

        with db.atomic():
            sql = self.insert_many(list_data).execute()
            return sql


class TradeDayModel(BaseModel):
    id = AutoField(primary_key=True)
    trade_date = DateField(null=False)

    class Meta:
        table_name = 'trade_days'
