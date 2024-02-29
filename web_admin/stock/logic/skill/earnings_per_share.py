from django.db.models import Q
from stock.logic.skill.previous_year_date import The_last_day_of_last_year
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_statement import FinancialStatement
from stock.models.moth_data import MothData


class EarningsPerShare:
    def earnings_per_share(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票每股收益"""
        yesterday_year_last_daily = The_last_day_of_last_year(params['end_date'])
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__("start_date") else "",
                'order': ['pub_date', 'desc'],
                'report_date': yesterday_year_last_daily,
                'cycle': params['cycle'],
                'earnings_per_share_value': params['earnings_per_share_value']
            }
            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = FinancialStatement().query_np_parent_company_owners(cond=cond)
            if obj:
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                # 每股收益
                basic_eps = float(obj.basic_eps)
                earnings_per_share_max = float(cond["earnings_per_share_value"][1])
                earnings_per_share_min = float(cond["earnings_per_share_value"][0])
                if earnings_per_share_max >= basic_eps >= earnings_per_share_min:
                    if symbol == row['symbol']:
                        if stock_list:
                            row['basic_eps'] = round(basic_eps, 2)
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
                                        'basic_eps': round(basic_eps, 2)
                                    }
                                )

        stock_column_desc.append({'name': '每股收益', 'key': 'basic_eps'})
        return out_stock_list, stock_column_desc