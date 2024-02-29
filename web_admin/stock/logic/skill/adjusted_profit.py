from django.db.models import Q
from stock.logic.skill.previous_year_date import previous_month_date
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_indicator import FinancialIndicatorDayModel
from stock.models.moth_data import MothData


class AdjustedProfit:
    def stock_adjusted_profit(self, params=None, stock_list=[], stock_column_desc=[]):
        """扣非净利润"""
        next_year_datetime = previous_month_date(params['end_date'], 3)
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['statDate', 'desc'],
                'statDate': next_year_datetime,
                'cycle': params['cycle'],
                'adjusted_profit_money': params['adjusted_profit_money'] * 10000,
                'adjusted_profit_condition': params['adjusted_profit_condition']
            }
            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = FinancialIndicatorDayModel().get_financial_target(cond=cond)

            if obj:
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                if symbol == row['symbol']:
                    if stock_list:
                        row['adjusted_profit'] = round(obj.adjusted_profit / 10000, 2)
                        out_stock_list.append(row)
                    else:
                        if cond["start_date"]:
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
                                    'adjusted_profit': round(obj.adjusted_profit / 10000, 2),
                                    "pub_date": obj.pubDate,
                                    "stat_date": obj.statDate
                                }
                            )
        stock_column_desc.append({'name': '扣非净利润(单位:万元)', 'key': 'adjusted_profit'})
        stock_column_desc.append({'name': '报告期', 'key': 'stat_date', "sort": True})
        stock_column_desc.append({'name': '公告日期', 'key': 'pub_date', "sort": True})
        return out_stock_list, stock_column_desc
