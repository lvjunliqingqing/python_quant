from peewee import *

from vnpy.model.base_model import BaseModel


class PositionDataModel(BaseModel):
    """"""
    id = AutoField(primary_key=True)
    symbol = CharField()
    exchange = CharField()
    direction = CharField()
    position_date = CharField()
    account_id = CharField()
    broker_id = CharField()
    frozen = FloatField()
    balance = FloatField()
    strategy_name = CharField()
    strategy_class_name = CharField(100)
    strategy_author = CharField()
    hedge_flag = CharField()
    yd_position = FloatField()
    position = FloatField()
    price = FloatField()
    long_frozen = FloatField()
    short_frozen = FloatField()
    long_frozen_amount = FloatField()
    short_frozen_amount = FloatField()
    open_volume = FloatField()
    close_volume = FloatField()
    open_amount = FloatField()
    close_amount = FloatField()
    position_cost = FloatField()
    pre_margin = FloatField()
    use_margin = FloatField()
    frozen_margin = FloatField()
    frozen_cash = FloatField()
    frozen_commission = FloatField()
    cash_in = FloatField()
    commission = FloatField()
    close_profit = FloatField()
    position_profit = FloatField()
    presettlement_price = FloatField()
    settlement_price = FloatField()
    trading_day = DateField()
    settlement_id = CharField()
    open_cost = FloatField()
    exchange_margin = FloatField()
    comb_position = FloatField()
    comb_long_frozen = FloatField()
    comb_short_frozen = FloatField()
    close_profit_by_date = FloatField()
    close_profit_by_trade = FloatField()
    today_position = FloatField()
    margin_rate_by_volume = FloatField()
    margin_rate_by_money = FloatField()
    strike_frozen = FloatField()
    strike_frozen_amount = FloatField()
    abandon_frozen = FloatField()
    yd_strike_frozen = FloatField()
    invest_unit_id = CharField()
    position_cost_offset = FloatField()
    gateway_name = CharField()
    extend = TextField()

    def save_position_data_from_json(self, position_data: dict):
        """
        保存仓位日志
        :param self:
        :param position_data:
        :return:
        """

        data_source = [
            {
                "symbol": position_data['symbol'],
                "exchange": position_data['exchange'],
                "frozen": position_data['frozen'],
                "balance": position_data['balance'],
                "direction": position_data['direction'],
                "price": position_data['price'],
                "strategy_name": position_data['strategy_name'],
                "strategy_class_name": position_data['strategy_class_name'],
                "strategy_author": position_data['strategy_author'],
                "gateway_name": position_data['gateway_name'],
                "position_date": position_data['position_date'],
                "account_id": position_data['account_id'],
                "broker_id": position_data['broker_id'],
                "hedge_flag": position_data['hedge_flag'],
                "yd_position": position_data['yd_position'],
                "position": position_data['position'],
                "long_frozen": position_data['long_frozen'],
                "short_frozen": position_data['short_frozen'],
                "long_frozen_amount": position_data['long_frozen_amount'],
                "short_frozen_amount": position_data['short_frozen_amount'],
                "open_volume": position_data['open_volume'],
                "close_volume": position_data['close_volume'],
                "open_amount": position_data['open_amount'],
                "close_amount": position_data['close_amount'],
                "position_cost": position_data['position_cost'],
                "pre_margin": position_data['pre_margin'],
                "use_margin": position_data['use_margin'],
                "frozen_margin": position_data['frozen_margin'],
                "frozen_cash": position_data['frozen_cash'],
                "frozen_commission": position_data['frozen_commission'],
                "cash_in": position_data['cash_in'],
                "commission": position_data['commission'],
                "close_profit": position_data['close_profit'],
                "position_profit": position_data['position_profit'],
                "presettlement_price": position_data['presettlement_price'],
                "settlement_price": position_data['settlement_price'],
                "trading_day": position_data['trading_day'],
                "settlement_id": position_data['settlement_id'],
                "open_cost": position_data['open_cost'],
                "exchange_margin": position_data['exchange_margin'],
                "comb_position": position_data['comb_position'],
                "comb_long_frozen": position_data['comb_long_frozen'],
                "comb_short_frozen": position_data['comb_short_frozen'],
                "close_profit_by_date": position_data['close_profit_by_date'],
                "close_profit_by_trade": position_data['close_profit_by_trade'],
                "today_position": position_data['today_position'],
                "margin_rate_by_volume": position_data['margin_rate_by_volume'],
                "margin_rate_by_money": position_data['margin_rate_by_money'],
                "strike_frozen": position_data['strike_frozen'],
                "strike_frozen_amount": position_data['strike_frozen_amount'],
                "abandon_frozen": position_data['abandon_frozen'],
                "yd_strike_frozen": position_data['yd_strike_frozen'],
                "invest_unit_id": position_data['invest_unit_id'],
                "position_cost_offset": position_data['position_cost_offset'],
            }
        ]

        sql = self.insert(data_source).on_conflict(
            preserve=[
                PositionDataModel.symbol,
                PositionDataModel.exchange,
                PositionDataModel.direction,
                PositionDataModel.position_date,
                PositionDataModel.account_id,
                PositionDataModel.broker_id,
                PositionDataModel.frozen,
                PositionDataModel.balance,
                PositionDataModel.strategy_name,
                PositionDataModel.strategy_class_name,
                PositionDataModel.strategy_author,
                PositionDataModel.hedge_flag,
                PositionDataModel.yd_position,
                PositionDataModel.position,
                PositionDataModel.price,
                PositionDataModel.long_frozen,
                PositionDataModel.short_frozen,
                PositionDataModel.long_frozen_amount,
                PositionDataModel.short_frozen_amount,
                PositionDataModel.open_volume,
                PositionDataModel.close_volume,
                PositionDataModel.open_amount,
                PositionDataModel.close_amount,
                PositionDataModel.position_cost,
                PositionDataModel.pre_margin,
                PositionDataModel.use_margin,
                PositionDataModel.frozen_margin,
                PositionDataModel.frozen_cash,
                PositionDataModel.frozen_commission,
                PositionDataModel.cash_in,
                PositionDataModel.commission,
                PositionDataModel.close_profit,
                PositionDataModel.position_profit,
                PositionDataModel.presettlement_price,
                PositionDataModel.settlement_price,
                PositionDataModel.trading_day,
                PositionDataModel.settlement_id,
                PositionDataModel.open_cost,
                PositionDataModel.exchange_margin,
                PositionDataModel.comb_position,
                PositionDataModel.comb_long_frozen,
                PositionDataModel.comb_short_frozen,
                PositionDataModel.close_profit_by_date,
                PositionDataModel.close_profit_by_trade,
                PositionDataModel.today_position,
                PositionDataModel.margin_rate_by_volume,
                PositionDataModel.margin_rate_by_money,
                PositionDataModel.strike_frozen,
                PositionDataModel.strike_frozen_amount,
                PositionDataModel.abandon_frozen,
                PositionDataModel.yd_strike_frozen,
                PositionDataModel.invest_unit_id,
                PositionDataModel.position_cost_offset,
                PositionDataModel.gateway_name,
                PositionDataModel.extend
            ]
        )

        return sql.execute()

    class Meta:
        table_name = 'position_data'
