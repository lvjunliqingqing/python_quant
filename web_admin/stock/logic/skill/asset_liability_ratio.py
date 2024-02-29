from stock.logic.skill.previous_year_date import n_years_ago_today
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.balance_sheet import BalanceSheet
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from stock.models.stock_industry import StockIndustryMode
from utils.return_on_assets_overlapping_code import equity_screener_duplicated_code

class AssetLiabilityRatio:
    def asset_liability_ratio(self, params=None, stock_list=[], stock_column_desc=[]):
        """资产负债率"""
        day_last_year = n_years_ago_today(params['end_date'], 1)
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__("start_date") else "",
                'order': ['pub_date', 'desc'],
                'pub_date_start': day_last_year,
                'cycle': params['cycle'],
                'asset_liability_ratio_value': params['asset_liability_ratio_value']
            }
            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData
            obj = BalanceSheet().query_asset_liability_ratio(cond=cond)
            if obj:
                try:
                    asset_liability_ratio = obj.total_liability / obj.total_assets * 100
                except:
                    asset_liability_ratio = -1
                asset_liability_ratio_value_max = float(cond["asset_liability_ratio_value"][1])
                asset_liability_ratio_value_min = float(cond["asset_liability_ratio_value"][0])
                industry_obj = StockIndustryMode.objects.get(code=cond["code"])
                if industry_obj:
                    try:
                        if industry_obj.industry == "资本市场服务":
                            asset_liability_ratio_value_max += 10
                        if industry_obj.industry == "货币金融服务":
                            asset_liability_ratio_value_max += 25
                    except:
                        pass
                if asset_liability_ratio_value_max >= asset_liability_ratio >= asset_liability_ratio_value_min:
                    conditions_key = "asset_liability_ratio"
                    conditions_value = asset_liability_ratio
                    obj_code = obj.code
                    symbol = obj_code.split('.')[0]
                    out_stock_list = equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value)

        stock_column_desc.append({'name': '资产负债率(%)', 'key': "asset_liability_ratio", "sort": True})
        return out_stock_list, stock_column_desc