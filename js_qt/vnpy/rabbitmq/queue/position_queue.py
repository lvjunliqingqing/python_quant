import datetime

from vnpy.rabbitmq.config.rabbitmq import RabbitmqCnf
from vnpy.rabbitmq.queue.rabbitmq import RabbitMQ
from vnpy.trader.object import PositionData

import json


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)


class PositionQueue:
    mq = None
    exchange = "position"
    insert_route_key = "insert.position"
    update_route_key = "update.position"

    def __init__(self):
        self.mq = RabbitMQ(RabbitmqCnf)
        self.mq.connect()

    def get_connect(self):
        if self.mq:
            return self.mq

    def push(self, position_data: PositionData):

        # if hasattr(position_data, 'gateway_name') and position_data.gateway_name == 'BACKTESTIN':
        #     return

        if not hasattr(position_data, 'extend'):
            position_data.extend = ''

        if hasattr(position_data, 'time') and position_data.time == '':
            position_data.time = datetime.datetime.now()

        if not hasattr(position_data, 'datetime'):
            position_data.datetime = datetime.datetime.now()

        data = {
            "symbol": position_data.symbol,
            "exchange": position_data.exchange.name,
            "direction": position_data.direction.name,
            "price": position_data.price,
            "frozen": position_data.frozen,
            "balance": position_data.balance,
            "position_date": position_data.position_date,
            "account_id": position_data.account_id,
            "broker_id": position_data.broker_id,
            "hedge_flag": position_data.hedge_flag,
            "yd_position": position_data.yd_position,
            "position": position_data.position,
            "long_frozen": position_data.long_frozen,
            "short_frozen": position_data.short_frozen,
            "long_frozen_amount": position_data.long_frozen_amount,
            "short_frozen_amount": position_data.short_frozen_amount,
            "open_volume": position_data.open_volume,
            "close_volume": position_data.close_volume,
            "open_amount": position_data.open_amount,
            "close_amount": position_data.close_amount,
            "position_cost": position_data.position_cost,
            "pre_margin": position_data.pre_margin,
            "use_margin": position_data.use_margin,
            "frozen_margin": position_data.frozen_margin,
            "frozen_cash": position_data.frozen_cash,
            "frozen_commission": position_data.frozen_commission,
            "cash_in": position_data.cash_in,
            "commission": position_data.commission,
            "close_profit": position_data.close_profit,
            "position_profit": position_data.position_profit,
            "presettlement_price": position_data.presettlement_price,
            "settlement_price": position_data.settlement_price,
            "trading_day": position_data.trading_day,
            "settlement_id": position_data.settlement_id,
            "open_cost": position_data.open_cost,
            "exchange_margin": position_data.exchange_margin,
            "comb_position": position_data.comb_position,
            "comb_long_frozen": position_data.comb_long_frozen,
            "comb_short_frozen": position_data.comb_short_frozen,
            "close_profit_by_date": position_data.close_profit_by_date,
            "close_profit_by_trade": position_data.close_profit_by_trade,
            "today_position": position_data.today_position,
            "margin_rate_by_volume": position_data.margin_rate_by_volume,
            "margin_rate_by_money": position_data.margin_rate_by_money,
            "strike_frozen": position_data.strike_frozen,
            "strike_frozen_amount": position_data.strike_frozen_amount,
            "abandon_frozen": position_data.abandon_frozen,
            "yd_strike_frozen": position_data.yd_strike_frozen,
            "invest_unit_id": position_data.invest_unit_id,
            "position_cost_offset": position_data.position_cost_offset,
            "gateway_name": position_data.gateway_name,
            "strategy_name": position_data.strategy_name,
            "strategy_class_name": position_data.strategy_class_name,
            "strategy_author": position_data.strategy_author,
            "extend": position_data.extend
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
