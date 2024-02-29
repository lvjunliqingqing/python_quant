from datetime import datetime
from django.db import models
from django.db.models import Q
from shape.models.trade_days import TradeDays
from utils.models import BaseModel


class OpenSymbolDataModel(BaseModel):
    """"""
    id = models.AutoField(primary_key=True)
    account_id = models.CharField(max_length=30, null=True, default=0, verbose_name="交易账户id")
    symbol = models.CharField(max_length=20, verbose_name="标的代码")
    exchange = models.CharField(max_length=255, verbose_name="交易所简称")
    direction = models.CharField(max_length=255, verbose_name="方向")
    offset = models.CharField(max_length=255, verbose_name="开平")
    trade_date = models.DateField(null=True, verbose_name="交易日期")
    extend = models.TextField(null=True, verbose_name="扩展属性json")
    status = models.SmallIntegerField(default=1, verbose_name="是否今天交易")
    audit_status = models.SmallIntegerField(default=0, verbose_name="审核状态")
    strategy_name = models.CharField(max_length=50, null=True, verbose_name="策略名字")
    audit_time = models.DateTimeField(verbose_name="审核时间")
    strategy_args = models.CharField(max_length=10000, verbose_name="策略参数")
    # strategy_args = JSONField(verbose_name="策略参数")

    class Meta:
        db_table = 'js_open_symbol_data'
        verbose_name = '加入交易的数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s:%s' % (self.exchange, self.symbol, self.trade_date)

    def get_shape_not_open(self, trade_day):
        date = datetime.now().strftime("%Y-%m-%d")
        if not trade_day:
            trade_day = date
        if trade_day >= "2020-06-09":
            query_trade = TradeDays().get_the_next_trading_day(trade_day)
            trade_day = query_trade.trade_date.strftime("%Y-%m-%d") if hasattr(query_trade, "trade_date") else trade_day,
        else:
            trade_day = (trade_day,)
        data_list = []
        try:
            if trade_day[0]:
                obj = OpenSymbolDataModel.objects.filter(trade_date=trade_day[0])
            else:
                obj = OpenSymbolDataModel.objects.filter(trade_date=date)
            if obj:
                for i in obj:
                    if i.exchange != "CZCE":
                        i.symbol = i.symbol.upper()
                    i_key = f"{i.symbol}.{i.exchange}.{i.direction}.{i.offset}"
                    data_list.append(i_key)
        except:
            pass
        return data_list

    def get_all(self, trade_day, audit_status, account_id):
        date = datetime.now().strftime("%Y-%m-%d")
        if trade_day:
            query_set = OpenSymbolDataModel.objects.filter(Q(trade_date=trade_day) & Q(audit_status=audit_status) & Q(account_id=account_id))
        else:
            query_set = OpenSymbolDataModel.objects.filter(Q(trade_date=date) & Q(audit_status=audit_status) & Q(account_id=account_id))
        return query_set
