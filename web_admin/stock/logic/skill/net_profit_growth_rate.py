from django.db.models import Q
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_statement import FinancialStatement
from stock.models.moth_data import MothData


class NetProfitGrowthRate:
    def stock_np_parent_company_owners_growth_rate(self, params=None, stock_list=[], stock_column_desc=[]):
        """净利润增长率"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'np_parent_company_owners_growth_rate_value': params['np_parent_company_owners_growth_rate_value'],
                'n_np_parent_company_owners_growth_rate_value': params['n_np_parent_company_owners_growth_rate_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            df, obj = FinancialStatement().query_np_parent_company_owners_growth_rate(cond=cond)
            if obj and len(df):
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                np_parent_company_owners_growth_rate_max = float(cond["np_parent_company_owners_growth_rate_value"][1])
                np_parent_company_owners_growth_rate_min = float(cond["np_parent_company_owners_growth_rate_value"][0])
                try:
                    df['np_parent_company_owners_growth_rate_rise'] = df['np_parent_company_owners'].diff(periods=-1) / df['np_parent_company_owners'].shift(-1) * 100
                except:
                    df["np_parent_company_owners_growth_rate_rise"] = None
                df = df.dropna(axis=0, how='any')
                if len(df["np_parent_company_owners_growth_rate_rise"]):
                    if ((df["np_parent_company_owners_growth_rate_rise"] >= np_parent_company_owners_growth_rate_min) & (
                            df["np_parent_company_owners_growth_rate_rise"] <= np_parent_company_owners_growth_rate_max)).all():
                        if symbol == row['symbol']:
                            if stock_list:
                                row['np_parent_company_owners_growth_rate_rise'] = round(df["np_parent_company_owners_growth_rate_rise"][0], 2)
                                out_stock_list.append(row)
                            else:
                                if cond['start_date']:
                                    query_set = model_d.objects.filter(
                                        Q(datetime__lte=cond['end_date'])
                                        & Q(datetime__gte=cond['start_date'])
                                        & Q(symbol=row['symbol'])
                                        & Q(exchange=row['exchange'])
                                    ).order_by("-datetime")
                                else:
                                    query_set = model_d.objects.filter(
                                        Q(datetime__lte=cond['end_date'])
                                        # & Q(datetime__gte=cond['start_date'])
                                        & Q(symbol=row['symbol'])
                                        & Q(exchange=row['exchange'])
                                    ).order_by("-datetime")
                                if query_set:
                                    query_set = query_set[0]
                                    out_stock_list.append(
                                        {
                                            'id': row['id'],
                                            "symbol": row['symbol'],
                                            "exchange": row['exchange'],
                                            "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                            'close': query_set.close_price,
                                            'trade_date': query_set.datetime.strftime("%Y-%m-%d"),
                                            'np_parent_company_owners_growth_rate_rise': round(df["np_parent_company_owners_growth_rate_rise"][0],
                                                                                  2)
                                        }
                                    )
        stock_column_desc.append({'name': '净利润增长率', 'key': 'np_parent_company_owners_growth_rate_rise'})
        return out_stock_list, stock_column_desc
