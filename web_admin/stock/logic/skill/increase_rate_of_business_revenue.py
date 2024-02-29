from django.db.models import Q

from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_statement import FinancialStatement
from stock.models.moth_data import MothData


class IncreaseRateOfBusinessRevenue:
    def increase_rate_of_business_revenue(self, params=None, stock_list=[], stock_column_desc=[]):
        """营业收入增长率"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'increase_rate_of_business_revenue_value': params['increase_rate_of_business_revenue_value'],
                'n_increase_rate_of_business_revenue_value': params['n_increase_rate_of_business_revenue_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            df, obj = FinancialStatement().query_increase_rate_of_business_revenue(cond=cond)
            if obj and len(df):
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                increase_rate_of_business_revenue_max = float(cond["increase_rate_of_business_revenue_value"][1])
                increase_rate_of_business_revenue_min = float(cond["increase_rate_of_business_revenue_value"][0])
                try:
                    df['total_operating_revenue_rise'] = df['total_operating_revenue'].diff(periods=-1) / df['total_operating_revenue'].shift(-1) * 100
                except:
                    df["total_operating_revenue_rise"] = None
                df = df.dropna(axis=0, how='any')
                if len(df["total_operating_revenue_rise"]):
                    if ((df["total_operating_revenue_rise"] >= increase_rate_of_business_revenue_min) & (df["total_operating_revenue_rise"] <= increase_rate_of_business_revenue_max)).all():
                        if symbol == row['symbol']:
                            if stock_list:
                                row['total_operating_revenue_rise'] = round(df["total_operating_revenue_rise"][0], 2)
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
                                            'total_operating_revenue_rise': round(df["total_operating_revenue_rise"][0], 2)
                                        }
                                    )
        stock_column_desc.append({'name': '营业收入增长率', 'key': 'total_operating_revenue_rise'})
        return out_stock_list, stock_column_desc
