from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.Valuation_table_data import StockCompanyValuationData
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from utils.return_on_assets_overlapping_code import equity_screener_duplicated_code


class PcfRatio:
    def stock_pcf_ratio(self, params=None, stock_list=[], stock_column_desc=[]):
        """市现率"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'pcf_ratio_value': params['pcf_ratio_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = StockCompanyValuationData().query_company_valuation(cond=cond)
            if obj:
                pcf_ratio_max = float(cond["pcf_ratio_value"][1])
                pcf_ratio_min = float(cond["pcf_ratio_value"][0])
                if pcf_ratio_min <= obj.pcf_ratio <= pcf_ratio_max:
                    obj_code = obj.code
                    symbol = obj_code.split('.')[0]
                    conditions_key = "pcf_ratio"
                    conditions_value = obj.pcf_ratio
                    out_stock_list = equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value)
        stock_column_desc.append({'name': '市现率', 'key': 'pcf_ratio'})
        return out_stock_list, stock_column_desc
