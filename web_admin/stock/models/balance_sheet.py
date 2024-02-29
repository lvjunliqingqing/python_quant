from django.db.models import Q

from utils.models import BaseModel
from django.db import models


class BalanceSheet(BaseModel):
    """
    资产负债报表模型类
    """
    company_id = models.CharField(max_length=30, verbose_name='公司ID')
    company_name = models.CharField(max_length=100, verbose_name='公司名称')
    code = models.CharField(max_length=12, verbose_name='股票代码')
    a_code = models.CharField(max_length=12, verbose_name='A股代码')
    b_code = models.CharField(max_length=12, verbose_name='B股代码')
    h_code = models.CharField(max_length=12, verbose_name='H股代码')
    pub_date = models.DateField(verbose_name='公告日期')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='截止日期')
    report_date = models.DateField(verbose_name='报告期')
    report_type = models.IntegerField(verbose_name='报告期类型int 0：本期，1：上期')
    source_id = models.IntegerField(verbose_name='报表来源编码 321002  上市公告书,321003  定期报告,321004 预披露公告,321005 换股报告书,321099 其他')
    source = models.CharField(max_length=60, verbose_name='报表来源 varchar(60) 选择时程序自动填入')
    cash_equivalents = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='货币资金')
    trading_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='交易性金融资产')
    bill_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收票据')
    account_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收账款')
    advance_payment = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='预付款项')
    other_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='其他应收款')
    affiliated_company_receivable = models.DecimalField(max_digits=20, decimal_places=4, verbose_name='应收关联公司款')
    interest_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收利息')
    dividend_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收股利')
    inventories = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='存货')
    expendable_biological_asset = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='消耗性生物资产是指为出售而持有的、等')
    non_current_asset_in_one_year = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='一年内到期的非流动资产')
    total_current_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='流动资产合计')
    hold_for_sale_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='可供出售金融资产')
    hold_to_maturity_investments = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='持有至到期投资')
    longterm_receivable_account = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期应收款')
    longterm_equity_invest = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期股权投资')
    investment_property = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='投资性房地产')
    fixed_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='固定资产')
    constru_in_process = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='在建工程')
    construction_materials = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='工程物资')
    fixed_assets_liquidation = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='固定资产清理')
    biological_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='生产性生物资产')
    oil_gas_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='油气资产')
    intangible_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='无形资产')
    development_expenditure = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='开发支出')
    good_will = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='商誉')
    long_deferred_expense = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期待摊费用')
    deferred_tax_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='递延所得税资产')
    total_non_current_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='非流动资产合计')
    total_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='资产总计')
    shortterm_loan = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='短期借款')
    trading_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='交易性金融负债')
    notes_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付票据')
    accounts_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付账款')
    advance_peceipts = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='预收款项')
    salaries_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付职工薪酬')
    taxs_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应交税费')
    interest_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付利息')
    dividend_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付股利')
    other_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='其他应付款')
    affiliated_company_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付关联公司款')
    non_current_liability_in_one_year = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='一年内到期的非流动负债')
    total_current_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='流动负债合计')
    longterm_loan = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期借款')
    bonds_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付债券')
    longterm_account_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期应付款')
    specific_account_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='专项应付款')
    estimate_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='预计负债')
    deferred_tax_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='递延所得税负债')
    total_non_current_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='非流动负债合计')
    total_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='负债合计')
    paidin_capital = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='实收资本（或股本)')
    capital_reserve_fund = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='资本公积')
    specific_reserves = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='专项储备')
    surplus_reserve_fund = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='盈余公积')
    treasury_stock = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='库存股')
    retained_profit = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='未分配利润')
    equities_parent_company_owners = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='归属于母公司所有者权益')
    minority_interests = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='少数股东权益')
    foreign_currency_report_conv_diff = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='外币报表折算价差')
    irregular_item_adjustment = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='非正常经营项目收益调整')
    total_owner_equities = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='所有者权益（或股东权益）合计')
    total_sheet_owner_equities = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='负债和所有者权益（或股东权益）合计')
    other_comprehensive_income = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='其他综合收益')
    deferred_earning = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='递延收益-非流动负债')
    settlement_provi = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='结算备付金')
    lend_capital = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='拆出资金')
    loan_and_advance_current_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='发放贷款及垫款-流动资产')
    derivative_financial_asset = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='衍生金融资产')
    insurance_receivables = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收保费')
    reinsurance_receivables = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收分保账款')
    reinsurance_contract_reserves_receivable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应收分保合同准备金')
    bought_sellback_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='买入返售金融资产')
    hold_sale_asset = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='划分为持有待售的资产')
    loan_and_advance_noncurrent_assets = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='发放贷款及垫款-非流动资产')
    borrowing_from_centralbank = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='向中央银行借款')
    deposit_in_interbank = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='吸收存款及同业存放')
    borrowing_capital = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='拆入资金')
    derivative_financial_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='衍生金融负债')
    sold_buyback_secu_proceeds = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='卖出回购金融资产款')
    commission_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付手续费及佣金')
    reinsurance_payables = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='应付分保账款')
    insurance_contract_reserves = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='保险合同准备金')
    proxy_secu_proceeds = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='代理买卖证券款')
    receivings_from_vicariously_sold_securities = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='代理承销证券款')
    hold_sale_liability = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='划分为持有待售的负债')
    estimate_liability_current = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='预计负债-流动负债')
    deferred_earning_current = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='递延收益-流动负债')
    preferred_shares_noncurrent = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='优先股-非流动负债')
    pepertual_liability_noncurrent = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='永续债-非流动负债')
    longterm_salaries_payable = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='长期应付职工薪酬')
    other_equity_tools = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='其他权益工具')
    preferred_shares_equity = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='其中：优先股-所有者权益')
    pepertual_liability_equity = models.DecimalField(max_digits=20, null=True, decimal_places=4, verbose_name='永续债-所有者权益')


    class Meta:
        db_table = 'js_stk_balance_sheet'
        verbose_name = '资产负债报表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.company_id, self.company_name)

    def query_balance_sheet(self, cond={}):
        """
        查询balance sheet
        """
        obj = BalanceSheet.objects.filter(
            Q(report_date=cond["report_date"])
            & Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__lte=cond['end_date'])
            & Q(source_id="321003")
        )
        total_owner_equities = 0
        if obj:
            obj = obj.order_by("-report_date")[0]
            total_owner_equities = obj.equities_parent_company_owners
        return total_owner_equities

    def query_asset_liability_ratio(self, cond={}):
        """查询资产负债率"""
        obj = BalanceSheet.objects.filter(
            Q(code=cond['code'])
            & Q(report_type=0)
            & Q(pub_date__gte=cond['pub_date_start'])
            & Q(pub_date__lte=cond['end_date'])
            & Q(source_id="321003")
        )
        if obj:
            obj = obj.order_by("-report_date")[0]
        return obj
