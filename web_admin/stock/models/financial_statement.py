from django.db.models import Q
from pandas import DataFrame

from stock.logic.skill.previous_year_date import previous_year_date
from utils.models import BaseModel
from django.db import models


class FinancialStatement(BaseModel):
    """
    财务报表模型类
    """
    company_id = models.IntegerField(null=True, verbose_name='公司ID')
    company_name = models.CharField(max_length=100, verbose_name='公司名称')
    code = models.CharField(max_length=20, verbose_name='股票代码')
    a_code = models.CharField(max_length=20, null=True, verbose_name='A股代码')
    b_code = models.CharField(max_length=20, null=True, verbose_name='B股代码')
    h_code = models.CharField(max_length=20, null=True, verbose_name='H股代码')
    pub_date = models.DateField(null=True, verbose_name='公告日期')
    start_date = models.DateField(null=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, verbose_name='截止日期')
    report_date = models.DateField(null=True, verbose_name='报告期')
    report_type = models.IntegerField(verbose_name='报告期类型int 0：本期，1：上期')
    source_id = models.IntegerField(null=True, verbose_name='报表来源编码 321002  上市公告书,321003  定期报告,321004 预披露公告,321005 换股报告书,321099 其他')
    source = models.CharField(max_length=100, null=True, verbose_name='报表来源 varchar(60) 选择时程序自动填入')
    total_operating_revenue = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='营业总收入')
    operating_revenue = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='营业收入')
    total_operating_cost = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='营业总成本')
    operating_cost = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='营业成本')
    operating_tax_surcharges = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='营业税金及附加')
    sale_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='销售费用')
    administration_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='管理费用')
    exploration_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='堪探费用 decimal(20,4) 勘探费用用于核算企业（石油天然气开采）核算的油气勘探过程中发生的地质调查、物理化学勘探各项支出和非成功探井等支出。')
    financial_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='财务费用')
    asset_impairment_loss = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='资产减值损失')
    fair_value_variable_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='公允价值变动净收益')
    investment_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='投资收益')
    invest_income_associates = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='对联营企业和合营企业的投资收益')
    exchange_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='汇兑收益')
    other_items_influenced_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='影响营业利润的其他科目')
    operating_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='营业利润')
    subsidy_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='补贴收入')
    non_operating_revenue = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='营业外收入')
    non_operating_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='营业外支出')
    disposal_loss_non_current_liability = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='非流动资产处置净损失')
    other_items_influenced_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='影响利润总额的其他科目')
    total_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='利润总额')
    income_tax = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='所得税')
    other_items_influenced_net_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='影响净利润的其他科目')
    net_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='净利润')
    np_parent_company_owners = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='归属于母公司所有者的净利润')
    minority_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='少数股东损益')
    eps = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='每股收益')
    basic_eps = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='基本每股收益')
    diluted_eps = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='稀释每股收益')
    other_composite_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='其他综合收益')
    total_composite_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='综合收益总额')
    ci_parent_company_owners = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='归属于母公司所有者的综合收益总额')
    ci_minority_owners = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='归属于少数股东的综合收益总额')
    interest_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='利息收入')
    premiums_earned = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='已赚保费')
    commission_income = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='手续费及佣金收入')
    interest_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='利息支出')
    commission_expense = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='手续费及佣金支出')
    refunded_premiums = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='退保金')
    net_pay_insurance_claims = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='赔付支出净额')
    withdraw_insurance_contract_reserve = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='提取保险合同准备金净额')
    policy_dividend_payout = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='保单红利支出')
    reinsurance_cost = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='分保费用')
    non_current_asset_disposed = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='非流动资产处置利得')
    other_earnings = models.DecimalField(max_digits=20, decimal_places=4, null=True, verbose_name='其他收益')

    class Meta:
        db_table = 'js_stk_income_statement'
        verbose_name = '财务报表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.company_id, self.company_name)

    def query_financial(self, cond={}):
        """根据净利润条件查询财务报表数据对象"""
        obj = None
        np_parent_company_owners_condition = cond['np_parent_company_owners_condition']
        if np_parent_company_owners_condition == "gte":
            obj = FinancialStatement.objects.filter(
                Q(report_date__gte=cond['report_date'])
                & Q(code=cond['code'])
                & Q(report_type=0)
                & Q(pub_date__lte=cond['end_date'])
                & Q(source_id="321003")
                & Q(np_parent_company_owners__gte=cond['np_parent_company_owners_money'])
            )
        elif np_parent_company_owners_condition == "lte":
            obj = FinancialStatement.objects.filter(
                Q(report_date__gte=cond['report_date'])
                & Q(code=cond['code'])
                & Q(report_type=0)
                & Q(pub_date__lte=cond['end_date'])
                & Q(source_id="321003")
                & Q(np_parent_company_owners__lte=cond['np_parent_company_owners_money'])
            )
        # 根据条件选择排序方式,再切片。
        if cond['order'][1] == 'desc':
            if obj:
                obj = obj.order_by('-' + cond['order'][0])[0]
        else:
            if obj:
                obj = obj.order_by(cond['order'][0])[0]

        return obj

    def get_net_prfit(self, cond):
        datetime_net_profit = []
        obj = FinancialStatement.objects.filter(
            Q(report_date__gte=cond['report_date'])
            & Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__lte=cond['end_date'])
            & Q(report_date__contains="12-31")
            & Q(source_id="321003")
        )
        # 根据条件选择排序方式,再切片。
        if cond['order'][1] == 'desc':
            if len(obj) >= 3:
                obj = obj.order_by('-' + cond['order'][0])[0:3]
                for i in obj:
                    datetime_net_profit.append({
                       "report_date": i.report_date,
                       "np_parent_company_owners": i.np_parent_company_owners
                    })
        else:
            if len(obj) >= 3:
                obj = obj.order_by(cond['order'][0])[0:3]
                for i in obj:
                    datetime_net_profit.append({
                       "report_date": i.report_date,
                       "np_parent_company_owners": i.np_parent_company_owners
                    })
        return DataFrame(datetime_net_profit)


    def query_np_parent_company_owners(self, cond={}):
        """查询净利润"""
        obj = FinancialStatement.objects.filter(
            Q(report_date=cond['report_date'])
            & Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__lte=cond['end_date'])
            & Q(source_id="321003")
        )
        if obj:
            obj = obj.order_by("-pub_date")[0]
        return obj

    def query_increase_rate_of_business_revenue(self, cond={}):
        """查询营业收入增长率"""
        limit = int(cond["n_increase_rate_of_business_revenue_value"])
        next_time = previous_year_date(end_date=cond["end_date"], n=limit+1)
        obj = FinancialStatement.objects.filter(
            Q(report_date__icontains="12-31")
            & Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__gte=next_time)
            & Q(source_id="321003")
        )

        if obj and len(obj) > limit:
            obj = obj.order_by("-report_date")[0:limit+1]
            close_list = []
            for i in obj:
                close_list.append({
                    'total_operating_revenue': i.total_operating_revenue,
                    "report_date": i.report_date,
                    "company_name": i.company_name
                })
            return DataFrame(close_list), obj[0]

        else:
            return None, None

    def query_np_parent_company_owners_growth_rate(self, cond={}):
        """查询净利润增长率"""
        limit = int(cond["n_np_parent_company_owners_growth_rate_value"])
        next_time = previous_year_date(end_date=cond["end_date"], n=limit+1)
        obj = FinancialStatement.objects.filter(
            Q(report_date__icontains="12-31")
            & Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__gte=next_time)
            & Q(source_id="321003")
        )
        if obj and len(obj) > limit:
            obj = obj.order_by("-report_date")[0:limit+1]
            close_list = []
            for i in obj:
                close_list.append({
                    'np_parent_company_owners': i.np_parent_company_owners,
                    "report_date": i.report_date,
                    "company_name": i.company_name
                })
            return DataFrame(close_list), obj[0]

        else:
            return None, None
