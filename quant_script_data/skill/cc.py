import base64
import datetime
import time
from jqdatasdk import *
from peewee import (
    AutoField,
    CharField,
    DateField,
    FloatField,
    IntegerField,
    Model,
    MySQLDatabase,
)

settings = {
    'host': '192.168.0.250',
    'user': 'stock',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8'
}
db = MySQLDatabase("stock", **settings)
auth('18520128569', (base64.b64decode(b'Y2hhbzM0MzM1NDE3').decode()))


class SecuritiesInfoModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField(null=False)
    display_name = CharField(null=False)
    name_code = CharField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    sec_type = CharField(null=False)

    class Meta:
        database = db
        table_name = 'securities_info'


class FinancialIndicatorDayModel(Model):
    id = IntegerField(primary_key=True, verbose_name="主键")
    code = CharField(max_length=20, null=False, verbose_name="股票代码(带后缀: .XSHE/.XSHG)")
    pubDate = DateField(null=False, verbose_name="公司发布财报日期")
    statDate = DateField(null=False, verbose_name="财报统计的季度的最后一天(比如2015-03-31, 2015-06-30)")
    eps = FloatField(verbose_name="每股收益EPS(元)")
    adjusted_profit = FloatField(verbose_name="扣除非经常损益后的净利润(元)")
    operating_profit = FloatField(verbose_name="经营活动净收益(元)")
    value_change_profit = FloatField(verbose_name="价值变动净收益(元)")
    roe = FloatField(verbose_name="净资产收益率ROE(%)")
    inc_return = FloatField(verbose_name="净资产收益率(扣除非经常损益)(%)")
    roa = FloatField(verbose_name="总资产净利率ROA(%)")
    net_profit_margin = FloatField(verbose_name="销售净利率(%)")
    gross_profit_margin = FloatField(verbose_name="销售毛利率(%)")
    expense_to_total_revenue = FloatField(verbose_name="营业总成本/营业总收入(%)")
    operation_profit_to_total_revenue = FloatField(verbose_name="营业利润/营业总收入(%)")
    net_profit_to_total_revenue = FloatField(verbose_name="净利润/营业总收入(%)")
    operating_expense_to_total_revenue = FloatField(verbose_name="营业费用/营业总收入(%)")
    ga_expense_to_total_revenue = FloatField(verbose_name="管理费用/营业总收入(%)")
    financing_expense_to_total_revenue = FloatField(verbose_name="财务费用/营业总收入(%)")
    operating_profit_to_profit = FloatField(verbose_name="经营活动净收益/利润总额(%)")
    invesment_profit_to_profit = FloatField(verbose_name="价值变动净收益/利润总额(%)")
    adjusted_profit_to_profit = FloatField(verbose_name="扣除非经常损益后的净利润/净利润(%)")
    goods_sale_and_service_to_revenue = FloatField(verbose_name="销售商品提供劳务收到的现金/营业收入(%)")
    ocf_to_revenue = FloatField(verbose_name="经营活动产生的现金流量净额/营业收入(%)")
    ocf_to_operating_profit = FloatField(verbose_name="经营活动产生的现金流量净额/经营活动净收益(%)")
    inc_total_revenue_year_on_year = FloatField(verbose_name="营业总收入同比增长率(%)")
    inc_total_revenue_annual = FloatField(verbose_name="营业总收入环比增长率(%)")
    inc_revenue_year_on_year = FloatField(verbose_name="营业收入同比增长率(%)")
    inc_revenue_annual = FloatField(verbose_name="营业收入环比增长率(%)")
    inc_operation_profit_year_on_year = FloatField(verbose_name="营业利润同比增长率(%)")
    inc_operation_profit_annual = FloatField(verbose_name="营业利润环比增长率(%)")
    inc_net_profit_year_on_year = FloatField(verbose_name="净利润同比增长率(%)")
    inc_net_profit_annual = FloatField(verbose_name="净利润环比增长率(%)")
    inc_net_profit_to_shareholders_year_on_year = FloatField(verbose_name="归属母公司股东的净利润同比增长率(%)")
    inc_net_profit_to_shareholders_annual = FloatField(verbose_name="归属母公司股东的净利润环比增长率(%)")

    class Meta:
        database = db
        table_name = 'dhtz_stk_financial_indicator_day'

    def sava_financial_indicator_day_data(self, df):
        for idx, row in df.iterrows():
            sql = FinancialIndicatorDayModel.insert(
                code=row.code,
                pubDate=row.pubDate,
                statDate=row.statDate,
                eps=row.eps,
                adjusted_profit=row.adjusted_profit,
                operating_profit=row.operating_profit,
                value_change_profit=row.value_change_profit,
                roe=row.roe,
                inc_return=row.inc_return,
                roa=row.roa,
                net_profit_margin=row.net_profit_margin,
                gross_profit_margin=row.gross_profit_margin,
                expense_to_total_revenue=row.expense_to_total_revenue,
                operation_profit_to_total_revenue=row.operation_profit_to_total_revenue,
                net_profit_to_total_revenue=row.net_profit_to_total_revenue,
                operating_expense_to_total_revenue=row.operating_expense_to_total_revenue,
                ga_expense_to_total_revenue=row.ga_expense_to_total_revenue,
                financing_expense_to_total_revenue=row.financing_expense_to_total_revenue,
                operating_profit_to_profit=row.operating_profit_to_profit,
                invesment_profit_to_profit=row.invesment_profit_to_profit,
                adjusted_profit_to_profit=row.adjusted_profit_to_profit,
                goods_sale_and_service_to_revenue=row.goods_sale_and_service_to_revenue,
                ocf_to_revenue=row.ocf_to_revenue,
                ocf_to_operating_profit=row.ocf_to_operating_profit,
                inc_total_revenue_year_on_year=row.inc_total_revenue_year_on_year,
                inc_total_revenue_annual=row.inc_total_revenue_annual,
                inc_revenue_year_on_year=row.inc_revenue_year_on_year,
                inc_revenue_annual=row.inc_revenue_annual,
                inc_operation_profit_year_on_year=row.inc_operation_profit_year_on_year,
                inc_operation_profit_annual=row.inc_operation_profit_annual,
                inc_net_profit_year_on_year=row.inc_net_profit_year_on_year,
                inc_net_profit_annual=row.inc_net_profit_annual,
                inc_net_profit_to_shareholders_year_on_year=row.inc_net_profit_to_shareholders_year_on_year,
                inc_net_profit_to_shareholders_annual=row.inc_net_profit_to_shareholders_annual
            ).on_conflict(
                preserve=[
                    FinancialIndicatorDayModel.code,
                    FinancialIndicatorDayModel.pubDate,
                    FinancialIndicatorDayModel.statDate,
                    FinancialIndicatorDayModel.eps,
                    FinancialIndicatorDayModel.adjusted_profit,
                    FinancialIndicatorDayModel.operating_profit,
                    FinancialIndicatorDayModel.value_change_profit,
                    FinancialIndicatorDayModel.roe,
                    FinancialIndicatorDayModel.inc_return,
                    FinancialIndicatorDayModel.roa,
                    FinancialIndicatorDayModel.net_profit_margin,
                    FinancialIndicatorDayModel.gross_profit_margin,
                    FinancialIndicatorDayModel.expense_to_total_revenue,
                    FinancialIndicatorDayModel.operation_profit_to_total_revenue,
                    FinancialIndicatorDayModel.net_profit_to_total_revenue,
                    FinancialIndicatorDayModel.operating_expense_to_total_revenue,
                    FinancialIndicatorDayModel.ga_expense_to_total_revenue,
                    FinancialIndicatorDayModel.financing_expense_to_total_revenue,
                    FinancialIndicatorDayModel.operating_profit_to_profit,
                    FinancialIndicatorDayModel.invesment_profit_to_profit,
                    FinancialIndicatorDayModel.adjusted_profit_to_profit,
                    FinancialIndicatorDayModel.goods_sale_and_service_to_revenue,
                    FinancialIndicatorDayModel.ocf_to_revenue,
                    FinancialIndicatorDayModel.ocf_to_operating_profit,
                    FinancialIndicatorDayModel.inc_total_revenue_year_on_year,
                    FinancialIndicatorDayModel.inc_total_revenue_annual,
                    FinancialIndicatorDayModel.inc_revenue_year_on_year,
                    FinancialIndicatorDayModel.inc_revenue_annual,
                    FinancialIndicatorDayModel.inc_operation_profit_year_on_year,
                    FinancialIndicatorDayModel.inc_operation_profit_annual,
                    FinancialIndicatorDayModel.inc_net_profit_year_on_year,
                    FinancialIndicatorDayModel.inc_net_profit_annual,
                    FinancialIndicatorDayModel.inc_net_profit_to_shareholders_year_on_year,
                    FinancialIndicatorDayModel.inc_net_profit_to_shareholders_annual
                ]
            )
            if sql.execute():
                print(f"ok sql:{sql}")
            else:
                print(f"error sql:{sql}")

    def get_financial_indicators_table_data(self):
        sql = f"select * from securities_info where symbol REGEXP '^[0-9].*' and end_date >= '{datetime.datetime.now().strftime('%Y-%m-%d')}'"
        sec_list = SecuritiesInfoModel.raw(sql)
        for row in sec_list:
            q = query(finance.STK_FIN_FORCAST).filter(finance.STK_FIN_FORCAST.code == row.symbol,
                                                      finance.STK_FIN_FORCAST.pub_date >= '2021-01-01').limit(10)
            df = finance.run_query(q)
            df.dropna(axis=0, how='all', inplace=True)
            if not len(df):
                print(f"the data for:{len(df)}")
            else:
                df.fillna(-0.0, inplace=True)
                columns = ["id", "code", "day", "pubDate", "statDate", "eps", "adjusted_profit", "operating_profit",
                           "value_change_profit", "roe",
                           "inc_return", "roa", "net_profit_margin", "gross_profit_margin", "expense_to_total_revenue",
                           "operation_profit_to_total_revenue", "net_profit_to_total_revenue",
                           "operating_expense_to_total_revenue",
                           "ga_expense_to_total_revenue", "financing_expense_to_total_revenue",
                           "operating_profit_to_profit",
                           "invesment_profit_to_profit", "adjusted_profit_to_profit", "goods_sale_and_service_to_revenue",
                           "ocf_to_revenue",
                           "ocf_to_operating_profit", "inc_total_revenue_year_on_year", "inc_total_revenue_annual",
                           "inc_revenue_year_on_year",
                           "inc_revenue_annual", "inc_operation_profit_year_on_year", "inc_operation_profit_annual",
                           "inc_net_profit_year_on_year", "inc_net_profit_annual",
                           "inc_net_profit_to_shareholders_year_on_year",
                           "inc_net_profit_to_shareholders_annual"]
                df.to_csv("./advance_notice.csv", encoding="utf-8", index=False)
if __name__ == "__main__":
    FinancialIndicatorDayModel().get_financial_indicators_table_data()
