from django.db import models
from django.db.models import Q
from utils.models import BaseModel


class StockCompanyValuationData(BaseModel):
    """
    股票公司估值数据模型类
    """
    code = models.CharField(max_length=255, verbose_name="股票代码(带后缀.XSHE/.XSHG)")
    day = models.DateField(verbose_name='日期时间')
    capitalization = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总股本(万股)')
    circulating_cap = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='流通股本(万股)')
    market_cap = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='总市值(亿元)')
    circulating_market_cap = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='流通市值(亿元)')
    turnover_ratio = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='换手率(%)')
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='市盈率(PE, TTM)')
    pe_ratio_lyr = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='市盈率(PE)')
    pb_ratio = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='市净率(PB)')
    ps_ratio = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='市销率(PS, TTM)')
    pcf_ratio = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='市现率(PCF, 现金净流量TTM)')

    class Meta:
        db_table = 'js_valuation'
        verbose_name = '股票公司估值数据表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.day, self.code)


    def query_company_valuation(self, cond={}):
        """查询股票公司估值的指标"""
        obj = StockCompanyValuationData.objects.filter(
            Q(code=cond['code'])
            & Q(day__lte=cond["end_date"])
        )
        # 根据条件选择排序方式,再切片。
        if cond['order'][1] == 'desc':
            if obj:
                obj = obj.order_by('-' + cond['order'][0])[0]
        else:
            if obj:
                obj = obj.order_by(cond['order'][0])[0]
        return obj

