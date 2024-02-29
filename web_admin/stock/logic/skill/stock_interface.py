
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from stock.logic.skill.adjusted_profit import AdjustedProfit
from stock.logic.skill.asset_liability_ratio import AssetLiabilityRatio
from stock.logic.skill.break_history_high import BreakHistoryHigh
from stock.logic.skill.break_history_ma import BreakHistoryMa
from stock.logic.skill.break_history_volume import BreakHistoryVolume
from stock.logic.skill.capital_reserves_per_share import CapitalReservesPerShare
from stock.logic.skill.circulating_market_cap import CirculatingMarketCap
from stock.logic.skill.cross import Cross
from stock.logic.skill.increase_rate_of_business_revenue import IncreaseRateOfBusinessRevenue
from stock.logic.skill.long import Long
from stock.logic.skill.earnings_per_share import EarningsPerShare
from stock.logic.skill.net_profit import NetProfit
from stock.logic.skill.net_profit_growth_rate import NetProfitGrowthRate
from stock.logic.skill.pb_ratio import PbRatio
from stock.logic.skill.pcf_ratio import PcfRatio
from stock.logic.skill.pe_ratio import PeRatio
from stock.logic.skill.quantile_history import QuantileHistory
from stock.logic.skill.return_on_assets import ReturnOnAssets
from stock.logic.skill.rsi import CustomRsi
from stock.logic.skill.short import Short
from stock.logic.skill.turnover_rate import TurnoverRate
from stock.utils import last_day_of_month

def stock_interface(condition, cycle, params, end_date):
    """股票接口"""
    # 用来存储选条件
    cond = []
    days_diff = 0
    for idx, con in enumerate(condition):
        app_dist = {

            'cycle': cycle,
            'condition': con
        }

        if con == 'break_high':
            days_diff = params[con]['break_high_value']['value']
            app_dist['from_the_current_number_of_days'] = int(params[con]['from_the_current_number_of_days']['value'])
            # app_dist['otherParams'] = params[con]

        elif con == 'break_ma':
            days_diff = params[con]['break_ma_value']['value']

        elif con == 'break_volume':
            days_diff = params[con]['break_volume_value']['value']

        elif con == "np_parent_company_owners":
            app_dist['np_parent_company_owners_condition'] = params[con]['np_parent_company_owners_logic']['value']
            app_dist['np_parent_company_owners_money'] = params[con]['np_parent_company_owners_value']['value']
            
        elif con == "adjusted_profit":
            app_dist['adjusted_profit_condition'] = params[con]['adjusted_profit_logic']['value']
            app_dist['adjusted_profit_money'] = params[con]['adjusted_profit_value']['value']

        elif con == 'pe_ratio':
            app_dist['pe_ratio'] = params[con]['pe_ratio_value']['value']

        elif con == 'pb_ratio':
            app_dist['pb_ratio'] = params[con]['pb_ratio_value']['value']

        elif con == 'pcf_ratio':
            app_dist['pcf_ratio_value'] = params[con]['pcf_ratio_value']['value']

        elif con == 'zf_long':
            app_dist['zf_long_one_value'] = params[con]['zf_long_one_value']['value']
            app_dist['zf_long_two_value'] = params[con]['zf_long_two_value']['value']

        elif con == 'df_long':
            app_dist['df_long_one_value'] = params[con]['df_long_one_value']['value']
            app_dist['df_long_two_value'] = params[con]['df_long_two_value']['value']

        elif con == "return_on_assets":
            app_dist['return_on_assets_value'] = params[con]['return_on_assets_value']['value']

        elif con == "earnings_per_share":
            app_dist['earnings_per_share_value'] = params[con]['earnings_per_share_value']['value']

        elif con == "increase_rate_of_business_revenue":
            app_dist['increase_rate_of_business_revenue_value'] = params[con]['increase_rate_of_business_revenue_value']['value']
            app_dist['n_increase_rate_of_business_revenue_value'] = params[con]['n_increase_rate_of_business_revenue_value']['value']

        elif con == "RSI_indicator":
            app_dist['RSI_indicator_scope_value'] = params[con]['RSI_indicator_scope_value']['value']
            app_dist['RSI_indicator_params_value'] = params[con]['RSI_indicator_params_value']['value']

        elif con == "np_parent_company_owners_growth_rate":
            app_dist['np_parent_company_owners_growth_rate_value'] = params[con]['np_parent_company_owners_growth_rate_value']['value']
            app_dist['n_np_parent_company_owners_growth_rate_value'] = params[con]['n_np_parent_company_owners_growth_rate_value']['value']

        elif con == "asset_liability_ratio":
            app_dist['asset_liability_ratio_value'] = params[con]['asset_liability_ratio_value']['value']

        elif con == "turnover_rate":
            app_dist['turnover_rate_value'] = params[con]['turnover_rate_value']['value']

        elif con == "circulating_market_cap":
            app_dist['circulating_market_cap_value'] = params[con]['circulating_market_cap_value']['value']

        elif con == "capital_reserves_per_share":
            app_dist['capital_reserves_per_share_value'] = params[con]['capital_reserves_per_share_value']['value']

        elif con == 'df_history_long':
            app_dist['df_history_long_yesterday_value'] = params[con]['df_history_long_yesterday_value']['value']
            app_dist['df_history_long_today_value'] = params[con]['df_history_long_today_value']['value']

        elif con == 'df_history_short':
            app_dist['df_history_short_yesterday_value'] = params[con]['df_history_short_yesterday_value']['value']
            app_dist['df_history_short_today_value'] = params[con]['df_history_short_today_value']['value']

        elif con == 'history_cross':
            app_dist['history_cross_yesterday_value'] = params[con]['history_cross_yesterday_value']['value']
            app_dist['history_cross_today_value'] = params[con]['history_cross_today_value']['value']
            app_dist['history_cross_yesterday_width_value'] = params[con]['history_cross_yesterday_width_value']['value']
            app_dist['history_cross_today_width_value'] = params[con]['history_cross_today_width_value']['value']

        app_dist['days_diff'] = days_diff

        if cycle == 'day' and app_dist['days_diff']:
            app_dist['start_date'] = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=int(days_diff))).strftime(
                "%Y-%m-%d")
        elif cycle == 'month':
            end_date = last_day_of_month(datetime.strptime(end_date, "%Y-%m-%d"))
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=days_diff)
            app_dist['start_date'] = start_date
        else:
            params['start_date'] = ''

        app_dist['end_date'] = end_date

        cond.append(app_dist)
    out_stock_list = []
    column_desc = []
    stock_column_desc = [
        {'name': '股票id', 'key': 'id'},
        {'name': '收盘日期', 'key': 'trade_date'},
        {'name': '股票代码', 'key': 'symbol'},
        {'name': '交易所', 'key': 'exchange'},
        {'name': '股票名称', 'key': 'display_name'},
        {'name': '收盘价', 'key': 'close'}
    ]
    empty_out = {
        'code': 0,
        'msg': '没有符合条件的股票',
        'data': {
            'list': [],
            'col': [
                {'name': '股票id', 'key': 'id'},
                {'name': '收盘日期', 'key': 'trade_date'},
                {'name': '股票代码', 'key': 'symbol'},
                {'name': '交易所', 'key': 'exchange'},
                {'name': '股票名称', 'key': 'display_name'},
                {'name': '收盘价', 'key': 'close'}
            ]
        }
    }

    for con in cond:
        if con['condition'] == 'break_high':
            out_stock_list, column_desc = BreakHistoryHigh().stock_break_high(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'break_ma':
            out_stock_list, column_desc = BreakHistoryMa().stock_break_ma(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'break_volume':
            out_stock_list, column_desc = BreakHistoryVolume().stock_break_volume(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'np_parent_company_owners':
            out_stock_list, column_desc = NetProfit().stock_np_parent_company_owners(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'adjusted_profit':
            out_stock_list, column_desc = AdjustedProfit().stock_adjusted_profit(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'pe_ratio':
            out_stock_list, column_desc = PeRatio().stock_pe_ratio(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'pb_ratio':
            out_stock_list, column_desc = PbRatio().stock_pb_ratio(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'pcf_ratio':
            out_stock_list, column_desc = PcfRatio().stock_pcf_ratio(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'zf_long':
            out_stock_list, column_desc = Long().stock_long(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'df_long':
            out_stock_list, column_desc = Short().stock_short(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'return_on_assets':
            out_stock_list, column_desc = ReturnOnAssets().stock_return_on_assets(params=con, stock_list=out_stock_list,stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'earnings_per_share':
            out_stock_list, column_desc = EarningsPerShare().earnings_per_share(params=con, stock_list=out_stock_list,stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'increase_rate_of_business_revenue':
            out_stock_list, column_desc = IncreaseRateOfBusinessRevenue().increase_rate_of_business_revenue(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'RSI_indicator':
            out_stock_list, column_desc = CustomRsi().custom_rsi(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'np_parent_company_owners_growth_rate':
            out_stock_list, column_desc = NetProfitGrowthRate().stock_np_parent_company_owners_growth_rate(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'asset_liability_ratio':
            out_stock_list, column_desc = AssetLiabilityRatio().asset_liability_ratio(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'circulating_market_cap':
            out_stock_list, column_desc = CirculatingMarketCap().stock_circulating_market_cap(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'turnover_rate':
            out_stock_list, column_desc = TurnoverRate().stock_turnover_rate(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'capital_reserves_per_share':
            out_stock_list, column_desc = CapitalReservesPerShare().stock_capital_reserves_per_share(params=con, stock_list=out_stock_list, stock_column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'df_history_long':
            out_stock_list, column_desc = QuantileHistory().stock_quantile_long(params=con, stock_list=out_stock_list, column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'df_history_short':
            out_stock_list, column_desc = QuantileHistory().stock_quantile_short(params=con, stock_list=out_stock_list, column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'history_cross':
            out_stock_list, column_desc = Cross().stock_cross(params=con, stock_list=out_stock_list, column_desc=stock_column_desc)
            if not out_stock_list:
                return empty_out

    out = {
        'code': 0,
        'msg': 'ok',
        'data': {
            'list': out_stock_list,
            'col': column_desc
        }
    }
    return out