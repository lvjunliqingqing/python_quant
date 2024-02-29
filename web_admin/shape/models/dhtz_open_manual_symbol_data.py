from django.db import models
from django.db.models import Q

from utils.models import BaseModel


class DhtzOpenManualSymbolDataModel(BaseModel):
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
        db_table = 'js_open_manual_symbol_data'
        verbose_name = '手动加入交易的数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s:%s' % (self.exchange, self.symbol, self.trade_date)

    def query_by_audit_status_account_id_status(self, account_id, audit_status, status):
        if audit_status == "all" and status == "all":
            query_set = DhtzOpenManualSymbolDataModel.objects.filter(account_id=account_id)
        elif audit_status == "all":
            query_set = DhtzOpenManualSymbolDataModel.objects.filter(account_id=account_id, status=status)
        elif status == "all":
            query_set = DhtzOpenManualSymbolDataModel.objects.filter(account_id=account_id, audit_status=audit_status)
        else:
            query_set = DhtzOpenManualSymbolDataModel.objects.filter(
                Q(status=status)
                & Q(audit_status=audit_status)
                & Q(account_id=account_id))
        return query_set