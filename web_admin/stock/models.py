from django.db import models

# Create your models here.
from utils.models import BaseModel


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


class MothData(BaseModel):
    """
    股票月k线模型类
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
        db_table = 'js_stock_month_dbbardata'
        verbose_name = '股票月k线数据'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.id, self.symbol)