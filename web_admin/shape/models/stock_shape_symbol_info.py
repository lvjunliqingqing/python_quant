from datetime import datetime
from django.db import models
from utils.models import BaseModel


class StockShapeSymbolInfoModel(BaseModel):
    """"""
    symbol = models.CharField(max_length=20, verbose_name="标的代码")
    exchange = models.CharField(max_length=255, verbose_name="交易所简称")
    direction = models.CharField(max_length=255, verbose_name="开仓方向(多或空)")
    offset = models.CharField(max_length=255, verbose_name="开或平")
    trade_date = models.DateField(verbose_name="交易日期")
    extend = models.TextField(verbose_name="扩展属性json")
    open = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='开盘价')
    close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='收盘价')
    high = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最高价')
    low = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最低价')
    zf_rise = models.FloatField(verbose_name="涨跌幅")
    shape = models.CharField(max_length=20, verbose_name="形态")

    class Meta:
        db_table = 'js_stock_shape_symbol_info'
        verbose_name = '形态表信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.exchange, self.symbol)

    def get_all(self, trade_day):

        date = datetime.now().strftime("%Y-%m-%d")
        if trade_day:
            query_set = StockShapeSymbolInfoModel.objects.filter(trade_date=trade_day)
        else:
            query_set = StockShapeSymbolInfoModel.objects.filter(trade_date=date)
        return query_set