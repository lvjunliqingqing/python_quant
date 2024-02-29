from stock.logic.skill.previous_year_date import The_last_day_of_last_year
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.balance_sheet import BalanceSheet
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_statement import FinancialStatement
from stock.models.moth_data import MothData
from utils.return_on_assets_overlapping_code import return_on_assets_overlapping_code


class ReturnOnAssets:
    def stock_return_on_assets(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票净资产收益率"""
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
                'return_on_assets_value': params['return_on_assets_value']
            }
            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = FinancialStatement().query_np_parent_company_owners(cond=cond)
            if obj:
                obj_code = obj.code
                symbol = obj_code.split('.')[0]
                # 净利润
                np_parent_company_owners = obj.net_profit
                # 净资产总额
                total_assets = BalanceSheet().query_balance_sheet(cond=cond)
                if total_assets and np_parent_company_owners:
                    total_owner_equities = float(np_parent_company_owners) / float(total_assets) * 100
                    return_on_assets_value_max = float(cond["return_on_assets_value"][1])
                    return_on_assets_value_min = float(cond["return_on_assets_value"][0])
                    if return_on_assets_value_max >= total_owner_equities >= return_on_assets_value_min:
                        out_stock_list = return_on_assets_overlapping_code(symbol, row, stock_list, out_stock_list, cond, model_d, total_owner_equities, vt_symbol_map)

        stock_column_desc.append({'name': '资产收益率(%)', 'key': 'total_owner_equities'})
        return out_stock_list, stock_column_desc