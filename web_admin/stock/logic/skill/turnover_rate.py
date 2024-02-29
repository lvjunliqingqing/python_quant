
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.Valuation_table_data import StockCompanyValuationData
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from utils.return_on_assets_overlapping_code import equity_screener_duplicated_code


class TurnoverRate:
    def stock_turnover_rate(self, params=None, stock_list=[], stock_column_desc=[]):
        """
        换手率：
            高位低换手率，说明庄家还不急着出货，说明该股后市还会继续上涨。
            低位高换手率，说明有机构逢低买入，看好此股，股价随后就会上涨。
        换手率范围:
            1%以下,很不活跃,属于冷门股。
            1-3%,成交量温和,活跃度一般,表明没有大资金在其中动作。
            3——7%,成交量大,对活跃状态。
            7-10%则为强势股的出现，股价处于高度活跃当中。
            10%——15%，大庄密切操作。
            超过15%换手率，持续多日的,股价低位持续上涨，此股也许成为最大黑马。
        """
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['day', 'desc'],
                'cycle': params['cycle'],
                'turnover_rate_value': params['turnover_rate_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData
            elif cond['cycle'] == 'month':
                model_d = MothData

            obj = StockCompanyValuationData().query_company_valuation(cond=cond)
            if obj:
                turnover_rate_max = float(cond["turnover_rate_value"][1])
                turnover_rate_min = float(cond["turnover_rate_value"][0])
                if turnover_rate_min <= obj.turnover_ratio <= turnover_rate_max:
                    obj_code = obj.code
                    symbol = obj_code.split('.')[0]
                    conditions_key = "turnover_rate"
                    conditions_value = obj.turnover_ratio
                    out_stock_list = equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value)
        stock_column_desc.append({'name': '换手率', 'key': 'turnover_rate'})
        return out_stock_list, stock_column_desc
