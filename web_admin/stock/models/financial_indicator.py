from django.db.models import Q

from utils.models import BaseModel
from django.db import models


class FinancialIndicatorDayModel(BaseModel):
    """ 财务主要指标统计数据表"""
    id = models.IntegerField(primary_key=True, verbose_name="主键")
    code = models.CharField(max_length=20, null=False, verbose_name="股票代码(带后缀: .XSHE/.XSHG)")
    pubDate = models.DateField(null=False, verbose_name="公司发布财报日期")
    statDate = models.DateField(null=False, verbose_name="财报统计的季度的最后一天(比如2015-03-31, 2015-06-30)")
    eps = models.FloatField(verbose_name="每股收益EPS(元)")
    adjusted_profit = models.FloatField(verbose_name="扣除非经常损益后的净利润(元)")
    operating_profit = models.FloatField(verbose_name="经营活动净收益(元)")
    value_change_profit = models.FloatField(verbose_name="价值变动净收益(元)")
    roe = models.FloatField(verbose_name="净资产收益率ROE(%)")
    inc_return = models.FloatField(verbose_name="净资产收益率(扣除非经常损益)(%)")
    roa = models.FloatField(verbose_name="总资产净利率ROA(%)")
    net_profit_margin = models.FloatField(verbose_name="销售净利率(%)")
    gross_profit_margin = models.FloatField(verbose_name="销售毛利率(%)")
    expense_to_total_revenue = models.FloatField(verbose_name="营业总成本/营业总收入(%)")
    operation_profit_to_total_revenue = models.FloatField(verbose_name="营业利润/营业总收入(%)")
    net_profit_to_total_revenue = models.FloatField(verbose_name="净利润/营业总收入(%)")
    operating_expense_to_total_revenue = models.FloatField(verbose_name="营业费用/营业总收入(%)")
    ga_expense_to_total_revenue = models.FloatField(verbose_name="管理费用/营业总收入(%)")
    financing_expense_to_total_revenue = models.FloatField(verbose_name="财务费用/营业总收入(%)")
    operating_profit_to_profit = models.FloatField(verbose_name="经营活动净收益/利润总额(%)")
    invesment_profit_to_profit = models.FloatField(verbose_name="价值变动净收益/利润总额(%)")
    adjusted_profit_to_profit = models.FloatField(verbose_name="扣除非经常损益后的净利润/净利润(%)")
    goods_sale_and_service_to_revenue = models.FloatField(verbose_name="销售商品提供劳务收到的现金/营业收入(%)")
    ocf_to_revenue = models.FloatField(verbose_name="经营活动产生的现金流量净额/营业收入(%)")
    ocf_to_operating_profit = models.FloatField(verbose_name="经营活动产生的现金流量净额/经营活动净收益(%)")
    inc_total_revenue_year_on_year = models.FloatField(verbose_name="营业总收入同比增长率(%)")
    inc_total_revenue_annual = models.FloatField(verbose_name="营业总收入环比增长率(%)")
    inc_revenue_year_on_year = models.FloatField(verbose_name="营业收入同比增长率(%)")
    inc_revenue_annual = models.FloatField(verbose_name="营业收入环比增长率(%)")
    inc_operation_profit_year_on_year = models.FloatField(verbose_name="营业利润同比增长率(%)")
    inc_operation_profit_annual = models.FloatField(verbose_name="营业利润环比增长率(%)")
    inc_net_profit_year_on_year = models.FloatField(verbose_name="净利润同比增长率(%)")
    inc_net_profit_annual = models.FloatField(verbose_name="净利润环比增长率(%)")
    inc_net_profit_to_shareholders_year_on_year = models.FloatField(verbose_name="归属母公司股东的净利润同比增长率(%)")
    inc_net_profit_to_shareholders_annual = models.FloatField(verbose_name="归属母公司股东的净利润环比增长率(%)")

    class Meta:
        db_table = 'js_stk_quarterly_financial_indicator_day'
        verbose_name = '财务主要指标统计数据表'
        verbose_name_plural = verbose_name

    def get_financial_target(self, cond={}):
        """根据扣非净利润条件查询财务主要指标对象"""
        obj = None
        adjusted_profit_condition = cond['adjusted_profit_condition']
        if adjusted_profit_condition == "gte":
            obj = FinancialIndicatorDayModel.objects.filter(
                Q(statDate__gte=cond['statDate'])
                & Q(code=cond['code'])
                & Q(pubDate__lte=cond['end_date'])
                & Q(adjusted_profit__gte=cond['adjusted_profit_money'])
            )
        elif adjusted_profit_condition == "lte":
            obj = FinancialIndicatorDayModel.objects.filter(
                Q(statDate__gte=cond['statDate'])
                & Q(code=cond['code'])
                & Q(pubDate__lte=cond['end_date'])
                & Q(adjusted_profit__lte=cond['adjusted_profit_money'])
            )
        # 根据条件选择排序方式,再切片。
        if cond['order'][1] == 'desc':
            if obj:
                obj = obj.order_by('-' + cond['order'][0])[0]
        else:
            if obj:
                obj = obj.order_by(cond['order'][0])[0]
        return obj
