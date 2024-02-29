from vnpy.model.base_model import BaseModel
from peewee import *
import json


class PortfolioRamValue(BaseModel):
    """
    组合策略添加策略模型类
        存储的是组合策略创建策略时的策略相关数据信息
    """
    id = AutoField(primary_key=True)
    strategy_class_name = CharField()
    symbol = CharField()
    strategy_name = CharField()
    account_id = CharField()
    risk_ctrl_cond = CharField()

    class Meta:
        table_name = 'js_strategy_portfolio_ram_value'

    def insert_value_plotfolio(self, class_name, symbol, strategy_name, risk_ctrl_cond, account_id):
        risk_ctrl_cond = json.dumps(risk_ctrl_cond)

        sql = PortfolioRamValue().insert(
            strategy_class_name=class_name,
            symbol=symbol,
            strategy_name=strategy_name,
            risk_ctrl_cond=risk_ctrl_cond,
            account_id=account_id
        ).on_conflict(
            preserve=[
                PortfolioRamValue.strategy_class_name,
                PortfolioRamValue.symbol,
                PortfolioRamValue.strategy_name,
                PortfolioRamValue.risk_ctrl_cond,
                PortfolioRamValue.account_id
            ]
        )
        return sql.execute()

    def search_value_plotfolio(self, strategy_name, account_id):
        try:
            data = PortfolioRamValue.get(strategy_name=strategy_name, account_id=account_id)
            return data
        except:
            return None

    def cancel_data(self, strategy_name, account_id):
        sql = PortfolioRamValue.delete().where(
            PortfolioRamValue.strategy_name == strategy_name,
            PortfolioRamValue.account_id == account_id,
        ).execute()
        return sql

    def update_value(self, strategy_name, account_id, risk_ctrl_cond):
        risk_ctrl_cond = json.dumps(risk_ctrl_cond)
        sql = PortfolioRamValue.update(
            risk_ctrl_cond=risk_ctrl_cond
        ).where(
            (PortfolioRamValue.strategy_name == strategy_name)
            & (PortfolioRamValue.account_id == account_id)
        ).execute()

        return sql
