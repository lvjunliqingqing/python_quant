from django.db import models

# Create your models here.
from utils.models import BaseModel
from django.db.models import Q
from pandas import DataFrame


class DailyStockData(BaseModel):
    """
    股票日k线模型类
    """
    symbol = models.CharField(max_length=255, verbose_name="股票代码")
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
        db_table = 'js_stock_dbbardata'
        verbose_name = '股票日K线数据'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.id, self.symbol)

    def GetStockByCond(cond):

        obj = DailyStockData.objects.filter(
            Q(datetime__lte=cond['end_date'])
            # & Q(datetime__gte=cond['start_date'])
            & Q(symbol=cond['symbol'])
            & Q(exchange=cond['exchange'])
        )

        try:
            limit = int(cond['days_diff'])
        except:
            limit = False

        if limit:
            # 根据条件选择排序方式,再切片。
            if cond['order'][1] == 'desc':
                obj_list = obj.order_by('-' + cond['order'][0])[0:limit]
            else:
                obj_list = obj.order_by(cond['order'][0])[0:limit]
        else:
            if cond['order'][1] == 'desc':
                obj_list = obj.order_by('-' + cond['order'][0])
            else:
                if len(obj) >= 100:
                    obj_list = obj.order_by(cond['order'][0])[(len(obj) - 100):]
                else:
                    return DataFrame()

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
