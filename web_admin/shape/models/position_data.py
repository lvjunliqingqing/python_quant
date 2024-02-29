import datetime

from django.db import models
from django.db.models import Q

from utils.models import BaseModel


class PositionDataModel(BaseModel):
    """"""
    symbol = models.CharField(max_length=20, verbose_name="合约代码")
    account_id = models.CharField(max_length=30, verbose_name="交易账户id")
    balance = models.FloatField(max_length=30, verbose_name="账号余额")
    frozen = models.FloatField(max_length=30, null=True, verbose_name="冻结资金")
    broker_id = models.CharField(max_length=50, verbose_name="经纪公司代码")
    hedge_flag = models.SmallIntegerField(default=1,
                                          verbose_name="投机套保标志类型1.投机 2.套利 3.套保 5.做市商 6.第一腿投机第二腿套保 大商所专用 7.第一腿套保第二腿投机  大商所专用")
    direction = models.CharField(max_length=255, verbose_name="方向")
    trading_day = models.DateField(null=True, verbose_name="交易日")
    strategy_class_name = models.CharField(max_length=100, verbose_name="策略类名")
    strategy_name = models.CharField(max_length=50, verbose_name="策略名字")
    strategy_author = models.CharField(max_length=50, verbose_name="策略作者")
    position_date = models.CharField(max_length=10, verbose_name="持仓日期 1.今日持仓 2.历史持仓")
    yd_position = models.FloatField(verbose_name="上日持仓")
    position = models.FloatField(verbose_name="今日持仓")
    long_frozen = models.FloatField(default=0, verbose_name="多头冻结")
    short_frozen = models.FloatField(default=0, verbose_name="空头冻结")
    long_frozen_amount = models.FloatField(default=0, verbose_name="开仓多头冻结金额")
    short_frozen_amount = models.FloatField(default=0, verbose_name="开仓空头冻结金额")
    open_volume = models.FloatField(default=0, verbose_name="开仓量")
    close_volume = models.FloatField(default=0, verbose_name="平仓量")
    open_amount = models.FloatField(default=0, verbose_name="开仓金额")
    close_amount = models.FloatField(default=0, verbose_name="平仓金额")
    price = models.FloatField(default=0, verbose_name="持仓成本均价 兼容vnpy")
    position_cost = models.FloatField(verbose_name="持仓成本")
    pre_margin = models.FloatField(default=0, verbose_name="上次占用的保证金")
    use_margin = models.FloatField(verbose_name="占用的保证金")
    frozen_margin = models.FloatField(default=0, verbose_name="冻结的保证金")
    frozen_cash = models.FloatField(default=0, verbose_name="冻结的资金")
    frozen_commission = models.FloatField(default=0, verbose_name="冻结的手续费")
    cash_in = models.FloatField(default=0, verbose_name="资金差额")
    commission = models.FloatField(default=0, verbose_name="手续费")
    close_profit = models.FloatField(default=0, verbose_name="平仓盈亏")
    position_profit = models.FloatField(verbose_name="持仓盈亏")
    presettlement_price = models.FloatField(verbose_name="上次结算价")
    settlement_price = models.FloatField(verbose_name="本次结算价")
    settlement_id = models.CharField(max_length=20, verbose_name="结算编号")
    open_cost = models.FloatField(null=True, verbose_name="开仓成本")
    exchange_margin = models.FloatField(null=True, verbose_name="交易所保证金")
    comb_position = models.FloatField(null=True, verbose_name="组合成交形成的持仓")
    comb_long_frozen = models.FloatField(default=0, null=True, verbose_name="组合多头冻结")
    comb_short_frozen = models.FloatField(default=0, verbose_name="组合空头冻结")
    close_profit_by_date = models.FloatField(default=0, null=True, verbose_name="逐日盯市平仓盈亏")
    close_profit_by_trade = models.FloatField(default=0, null=True, verbose_name="逐笔对冲平仓盈亏")
    today_position = models.FloatField(null=True, verbose_name="今日持仓")
    margin_rate_by_volume = models.FloatField(default=0, null=True, verbose_name="保证金率(按手数)")
    margin_rate_by_money = models.FloatField(default=0, null=True, verbose_name="保证金率")
    strike_frozen = models.FloatField(default=0, null=True, verbose_name="执行冻结")
    strike_frozen_amount = models.FloatField(default=0, null=True, verbose_name="执行冻结金额")
    abandon_frozen = models.FloatField(default=0, null=True, verbose_name="放弃执行冻结")
    exchange = models.CharField(max_length=30, null=True, verbose_name="交易所代码")
    yd_strike_frozen = models.FloatField(default=0, null=True, verbose_name="执行冻结的昨仓")
    invest_unit_id = models.CharField(max_length=300, null=True, verbose_name="投资单元代码")
    position_cost_offset = models.CharField(max_length=30, null=True, verbose_name="大商所持仓成本差值，只有大商所使用")
    extend = models.TextField(null=True, verbose_name="扩展信息")
    gateway_name = models.CharField(max_length=30, null=True, verbose_name="网关名字")

    class Meta:
        db_table = 'position_data'
        verbose_name = '仓位数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.exchange, self.symbol)

    def get_position_info(self, account_id, ):
        try:
            obj = PositionDataModel.objects.filter(
                Q(account_id=account_id)
                & Q(trading_day=str(datetime.datetime.now().date()))
            ).order_by("-position")
        except:
            return None
        return obj
