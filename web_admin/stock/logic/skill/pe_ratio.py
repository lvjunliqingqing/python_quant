from django.db.models import Q

from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.Valuation_table_data import StockCompanyValuationData
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData


class PeRatio:
    def stock_pe_ratio(self, params=None, stock_list=[], stock_column_desc=[]):
        """市盈率"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'pe_ratio': params['pe_ratio']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = StockCompanyValuationData().query_company_valuation(cond=cond)
            if obj:
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                pe_ratio_max = float(cond["pe_ratio"][1])
                pe_ratio_min = float(cond["pe_ratio"][0])
                if pe_ratio_min <= obj.pe_ratio <= pe_ratio_max:
                    if symbol == row['symbol']:
                        if stock_list:
                            row['pe_ratio'] = obj.pe_ratio
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
                                        'pe_ratio': obj.pe_ratio
                                    }
                                )
        stock_column_desc.append({'name': '市盈率', 'key': 'pe_ratio'})
        return out_stock_list, stock_column_desc
