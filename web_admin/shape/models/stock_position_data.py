import datetime

from django.db import models
from django.db.models import Q

from utils.models import BaseModel


class StockPositionDataModel(BaseModel):
    """"""
    account_id = models.CharField(max_length=30, verbose_name="交易账户id")
    symbol = models.CharField(max_length=20, verbose_name="合约代码")
    ticker_name = models.CharField(max_length=255, verbose_name="证券名称")
    exchange = models.CharField(max_length=30, null=True, verbose_name="交易所代码")
    direction = models.CharField(max_length=255, verbose_name="方向")
    balance = models.FloatField(max_length=30, verbose_name="账号余额")
    frozen = models.FloatField(max_length=30, null=True, verbose_name="总的冻结余额")
    trading_day = models.DateField(null=True, verbose_name="交易日")
    strategy_class_name = models.CharField(max_length=100, verbose_name="策略类名")
    strategy_name = models.CharField(max_length=50, verbose_name="策略名字")
    total_qty = models.IntegerField(verbose_name="总持仓")
    position = models.IntegerField(verbose_name="今日持仓")
    sellable_qty = models.IntegerField(verbose_name="可卖持仓")
    price = models.FloatField(verbose_name="持仓成本均价")
    unrealized_pnl = models.FloatField(verbose_name="浮动盈亏")
    yd_position = models.FloatField(verbose_name="上日持仓")
    purchase_redeemable_qty = models.IntegerField(verbose_name="今日申购赎回数量（申购和赎回数量不可能同时存在，因此可以共用一个字段）")
    executable_option = models.IntegerField(verbose_name="可行权合约")
    lockable_position = models.IntegerField(verbose_name="可锁定标的")
    executable_underlying = models.IntegerField(verbose_name="可行权标的")
    locked_position = models.IntegerField(verbose_name="已锁定标的")
    usable_locked_position = models.IntegerField(verbose_name="可用已锁定标的")
    strategy_author = models.CharField(max_length=50, verbose_name="策略作者")
    open_volume = models.FloatField(default=0, verbose_name="开仓量")
    close_volume = models.FloatField(default=0, verbose_name="平仓量")
    open_amount = models.FloatField(default=0, verbose_name="开仓金额")
    close_amount = models.FloatField(default=0, verbose_name="平仓金额")
    frozen_cash = models.FloatField(default=0, verbose_name="冻结的资金")
    commission = models.FloatField(default=0, verbose_name="手续费")
    close_profit = models.FloatField(default=0, verbose_name="平仓盈亏")
    position_profit = models.FloatField(verbose_name="持仓盈亏")
    extend = models.TextField(null=True, verbose_name="扩展信息")
    gateway_name = models.CharField(max_length=30, null=True, verbose_name="网关名字")

    class Meta:
        db_table = 'stock_position_data'
        verbose_name = '仓位数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.exchange, self.symbol)

    def get_position_info(self, account_id, ):
        try:
            obj = StockPositionDataModel.objects.filter(
                Q(account_id=account_id)
                & Q(trading_day=str(datetime.datetime.now().date()))
            ).order_by("-total_qty")
        except:
            return None
        return obj
