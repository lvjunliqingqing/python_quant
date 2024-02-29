
from datetime import datetime, timedelta

from stock.logic.skill.big_yin_lower_middle_part import BigYinLowerMiddlePart
from stock.logic.skill.break_history_high import BreakHistoryHigh
from stock.logic.skill.break_history_ma import BreakHistoryMa
from stock.logic.skill.cross import Cross
from stock.logic.skill.long import Long
from stock.logic.skill.short import Short
from stock.logic.skill.quantile_history import QuantileHistory
from stock.logic.skill.sun_middle_upper_part import SunMiddleUpperPart


def futures_interface(condition, cycle, params, end_date):
    """期货接口"""
    # 用来存储选条件

    cond = []
    for idx, con in enumerate(condition):
        app_dist = {

            'cycle': cycle,
            'condition': con
        }
        days_diff = 0
        if con == 'break_high':
            days_diff = params[con]['break_high_value']['value']
            # app_dist['otherParams'] = params[con]

        elif con == 'break_ma':
            days_diff = params[con]['break_ma_value']['value']

        elif con == 'zf_long':
            app_dist['zf_long_one_value'] = params[con]['zf_long_one_value']['value']
            app_dist['zf_long_two_value'] = params[con]['zf_long_two_value']['value']

        elif con == 'df_long':
            app_dist['df_long_one_value'] = params[con]['df_long_one_value']['value']
            app_dist['df_long_two_value'] = params[con]['df_long_two_value']['value']

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

        elif con == 'sun_middle_upper_part':
            app_dist['sun_middle_upper_part_yesterday_value'] = params[con]['sun_middle_upper_part_yesterday_value']['value']

        elif con == 'big_yin_lower_middle_part':
            app_dist['big_yin_lower_middle_part_yesterday_value'] = params[con]['big_yin_lower_middle_part_yesterday_value']['value']

        app_dist['days_diff'] = days_diff

        if cycle == 'day' and app_dist['days_diff']:
            app_dist['start_date'] = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=int(days_diff))).strftime(
                "%Y-%m-%d")

        app_dist['end_date'] = end_date
        cond.append(app_dist)

    out_stock_list = []
    column_desc = []
    futures_column_desc = [
        {'name': '期货id', 'key': 'id'},
        {'name': '收盘日期', 'key': 'trade_date'},
        {'name': '期货合约代码', 'key': 'symbol'},
        {'name': '交易所', 'key': 'exchange'},
        {'name': '期货名称', 'key': 'display_name'},
        {'name': '收盘价', 'key': 'close'}
    ]
    empty_out = {
        'code': 0,
        'msg': '没有符合条件的期货',
        'data': {
            'list': [],
            'col': [
                    {'name': '期货id', 'key': 'id'},
                    {'name': '收盘日期', 'key': 'trade_date'},
                    {'name': '期货合约代码', 'key': 'symbol'},
                    {'name': '交易所', 'key': 'exchange'},
                    {'name': '期货名称', 'key': 'display_name'},
                    {'name': '收盘价', 'key': 'close'}
                ]
        }
    }
    for con in cond:
        if con['condition'] == 'break_high':
            out_stock_list, column_desc = BreakHistoryHigh().futures_break_high(params=con, stock_list=out_stock_list, futures_column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out
        elif con['condition'] == 'break_ma':
            out_stock_list, column_desc = BreakHistoryMa().futures_break_high_ma(params=con, stock_list=out_stock_list, futures_column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out
        elif con['condition'] == 'zf_long':
            out_stock_list, column_desc = Long().futures_long(params=con, stock_list=out_stock_list, futures_column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out
        elif con['condition'] == 'df_long':
            out_stock_list, column_desc = Short().futures_short(params=con, stock_list=out_stock_list, futures_column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out
        elif con['condition'] == 'df_history_long':
            out_stock_list, column_desc = QuantileHistory().quantile_long(params=con, stock_list=out_stock_list, column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'df_history_short':
            out_stock_list, column_desc = QuantileHistory().quantile_short(params=con, stock_list=out_stock_list, column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'history_cross':
            out_stock_list, column_desc = Cross().futures_cross(params=con, stock_list=out_stock_list, column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'sun_middle_upper_part':
            out_stock_list, column_desc = SunMiddleUpperPart().futures_sun_middle_upper_part(params=con, stock_list=out_stock_list, column_desc=futures_column_desc)
            if not out_stock_list:
                return empty_out

        elif con['condition'] == 'big_yin_lower_middle_part':
            out_stock_list, column_desc = BigYinLowerMiddlePart().futures_big_yin_lower_middle_part(params=con,stock_list=out_stock_list,column_desc=futures_column_desc)
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