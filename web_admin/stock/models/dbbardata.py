
from django.db import models

# Create your models here.
from utils.models import BaseModel
from django.db.models import Q
from pandas import DataFrame

class FuturesData(BaseModel):
    """
    期货模型类(此表里有分钟和日的期货数据)
    """
    symbol = models.CharField(max_length=255, verbose_name="期货代码")
    exchange = models.CharField(max_length=255, verbose_name="交易所")
    datetime = models.DateField(verbose_name='日期时间')
    interval = models.CharField(max_length=10, verbose_name="周期")
    volume = models.IntegerField(default=0, verbose_name='成交量')
    open_interest = models.IntegerField(default=0, verbose_name='未平仓量')
    open_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='开盘价')
    high_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最高价')
    low_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最低价')
    close_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='收盘价')

    class Meta:
        db_table = 'dbbardata'
        verbose_name = '期货数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.id, self.symbol)


    def get_futures_by_cond(cond={}):
        """查询期货数据"""
        if cond['cycle'] == "day":
            cond['cycle'] = "d"
        obj = FuturesData.objects.filter(
            Q(datetime__lte=cond['end_date'])
            # & Q(datetime__gte=cond['start_date'])
            & Q(symbol=cond['symbol'])
            & Q(interval=cond['cycle'])
            & Q(exchange=cond['exchange'])
        )

        limit = int(cond['days_diff'])

        # 根据条件选择排序方式,再切片。
        if cond['order'][1] == 'desc':
            obj_list = obj.order_by('-' + cond['order'][0])
        else:
            obj_list = obj.order_by(cond['order'][0])

        if limit > 0:
            obj_list = obj_list[0:limit]

        std_stock_list = []
        for row in obj_list:
            std_stock_list.append({
                'close': row.close_price,
                'open': row.open_price,
                'trade_date': row.datetime.strftime("%Y-%m-%d"),
                'high': row.high_price,
                'low': row.low_price,
                'volume': row.volume,
                'symbol': row.symbol,
                'exchange': row.exchange
            })

        return DataFrame(std_stock_list)