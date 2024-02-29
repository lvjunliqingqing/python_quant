from stock.logic.skill.previous_year_date import n_years_ago_today
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.Valuation_table_data import StockCompanyValuationData
from stock.models.balance_sheet import BalanceSheet
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from utils.return_on_assets_overlapping_code import equity_screener_duplicated_code


class CapitalReservesPerShare:
    def stock_capital_reserves_per_share(self, params=None, stock_list=[], stock_column_desc=[]):
        """
        每股资本公积：
            每股资本公积金=资本公积/总股本
            每股资本公积金越高，上市公司转增股本的能力也就越高，股本扩张能力越强。
            每股资本公积达到1元,就具有转增股的能力。
        """
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        day_last_year = n_years_ago_today(params['end_date'], 1)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'pub_date_start': day_last_year,
                'cycle': params['cycle'],
                'capital_reserves_per_share_value': params['capital_reserves_per_share_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = BalanceSheet().query_asset_liability_ratio(cond=cond)
            obj2 = StockCompanyValuationData().query_company_valuation(cond=cond)
            if obj and obj2:
                capital_reserves_per_share_max = float(cond["capital_reserves_per_share_value"][1])
                capital_reserves_per_share_min = float(cond["capital_reserves_per_share_value"][0])
                if obj2.capitalization:
                    capital_reserves_per_share = float(obj.capital_reserve_fund) / float(obj2.capitalization) / 10000
                else:
                    capital_reserves_per_share = -1
                if capital_reserves_per_share_min <= capital_reserves_per_share <= capital_reserves_per_share_max:
                    obj_code = obj.code
                    symbol = obj_code.split('.')[0]
                    conditions_key = "capital_reserves_per_share"
                    conditions_value = capital_reserves_per_share
                    out_stock_list = equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value)
        stock_column_desc.append({'name': '每股资本公积', 'key': 'capital_reserves_per_share'})
        return out_stock_list, stock_column_desc
