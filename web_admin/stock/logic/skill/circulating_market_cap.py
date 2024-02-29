from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.Valuation_table_data import StockCompanyValuationData
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from utils.return_on_assets_overlapping_code import equity_screener_duplicated_code


class CirculatingMarketCap:
    def stock_circulating_market_cap(self, params=None, stock_list=[], stock_column_desc=[]):
        """流通市值"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'circulating_market_cap_value': params['circulating_market_cap_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = StockCompanyValuationData().query_company_valuation(cond=cond)
            if obj:
                circulating_market_cap_max = float(cond["circulating_market_cap_value"][1])
                circulating_market_cap_min = float(cond["circulating_market_cap_value"][0])
                if circulating_market_cap_min <= obj.circulating_market_cap <= circulating_market_cap_max:
                    obj_code = obj.code
                    symbol = obj_code.split('.')[0]
                    conditions_key = "circulating_market_cap"
                    conditions_value = obj.circulating_market_cap
                    out_stock_list = equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value)
        stock_column_desc.append({'name': '流通市值', 'key': 'circulating_market_cap'})
        return out_stock_list, stock_column_desc
