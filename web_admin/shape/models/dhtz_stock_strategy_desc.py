
from collections import defaultdict
from django.db import models
from django.db.models import Q, QuerySet

from utils.models import BaseModel


class DhtzStockStrategyDesc(BaseModel):
    """"""
    strategy_class_name = models.CharField(max_length=50, verbose_name="策略类名")
    symbol = models.CharField(max_length=20, verbose_name="标的物")
    exchange = models.CharField(max_length=20, verbose_name="交易所")
    direction = models.CharField(max_length=20, verbose_name="方向")
    strategy_no = models.CharField(max_length=10, null=True, verbose_name="策略编号")
    open_is = models.IntegerField(null=True, verbose_name="是否开了再开")
    strategy_name = models.CharField(max_length=20, verbose_name="策略名字")
    strategy_desc = models.CharField(max_length=255, verbose_name="策略描述")
    strategy_remark = models.CharField(max_length=20, verbose_name="策略备注")
    strategy_args = models.CharField(max_length=10000, verbose_name="策略默认参数")
    link_table = models.CharField(max_length=30, verbose_name="关联的table")

    class Meta:
        db_table = 'js_stock_strategy_desc'
        verbose_name = '策略参数信息表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.strategy_class_name, self.strategy_name)

    def query_all(self):
        query = DhtzStockStrategyDesc.objects.all().query
        query.group_by = ["strategy_class_name"]
        return QuerySet(query=query, model=DhtzStockStrategyDesc)

    def get_by_symbol_exchange(self, symbol, exchange, strategy_name, direction):
        if strategy_name and direction:
            return DhtzStockStrategyDesc.objects.filter(
                Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(strategy_class_name=strategy_name)
                & Q(direction=direction)
            )
        elif strategy_name and not direction:
            return DhtzStockStrategyDesc.objects.filter(
                Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(strategy_class_name=strategy_name)
            )
        elif not strategy_name and direction:
            return DhtzStockStrategyDesc.objects.filter(
                Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(strategy_class_name=strategy_name)
            )
        else:
            return DhtzStockStrategyDesc.objects.filter(
                Q(symbol=symbol)
                & Q(exchange=exchange)
            )

    def desc_map(self):
        query_map = DhtzStockStrategyDesc.objects.all()
        data_map = defaultdict(int)
        for val in query_map:
            data_map[f"{val.strategy_class_name}.{val.symbol}.{val.exchange}"] = val.strategy_desc
        return data_map


