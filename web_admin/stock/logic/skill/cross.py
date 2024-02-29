from stock.logic.skill.sec_info import get_futures_sec_info, get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.dbbardata import FuturesData
import pandas as pd

from stock.models.moth_data import MothData


class Cross:
    def futures_cross(self, params=None, stock_list=[], column_desc=[]):
        """期货十字星"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_futures_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'symbol': row['symbol'],
                'exchange': row['exchange'],
                'end_date': params['end_date'],
                'order': ['datetime', 'desc'],
                'cycle': params['cycle'],
                'days_diff': params['days_diff'],
                "history_cross_yesterday_value": params['history_cross_yesterday_value'],
                "history_cross_today_value": params['history_cross_today_value'],
                "history_cross_yesterday_width_value": params['history_cross_yesterday_width_value'],
                "history_cross_today_width_value": params['history_cross_today_width_value']
            }

            if cond['cycle'] == 'day':
                model_d = FuturesData

            elif cond['cycle'] == 'month':
                model_d = FuturesData

            df = model_d.get_futures_by_cond(cond=cond)
            if len(df) > 1:
                trade_date = df['trade_date'].values[0]

                df['diff_rise'] = (df['close'] - df['open']) / df['open'] * 100
                last_close_rise = df['diff_rise'].values[0]
                pre_close_rise = df['diff_rise'].values[1]

                # df["width"] = (df['high'] - df['low']) / df['high'] * 100
                # # print(df["width"].max(), df["width"].min())
                # last_width = df["width"].values[0]
                # pre_width = df["width"].values[1]

                last_open = df["open"].values[0]
                pre_open = df["open"].values[1]

                last_close = df["close"].values[0]
                pre_close = df["close"].values[1]

                last_open_close_max = max(last_close, last_open)
                last_open_close_min = min(last_close, last_open)

                pre_open_close_max = max(pre_close, pre_open)
                pre_open_close_min = min(pre_close, pre_open)

                last_high = df["high"].values[0]
                pre_high = df["high"].values[1]

                last_low = df["low"].values[0]
                pre_low = df["low"].values[1]

                last_width_up = (last_high - last_open_close_max) / last_high * 100
                last_width_down = (last_open_close_min - last_low) / last_low * 100

                pre_width_up = (pre_high - pre_open_close_max) / pre_high * 100
                pre_width_down = (pre_open_close_min - pre_low) / pre_low * 100
                zf_min_yesterday_float_val = params['history_cross_yesterday_value'][0]
                zf_max_yesterday_float_val = params['history_cross_yesterday_value'][1]

                zf_min_today_float_val = params['history_cross_today_value'][0]
                zf_max_today_float_val = params['history_cross_today_value'][1]

                zf_min_yesterday_width_float_val = params['history_cross_yesterday_width_value'][0]
                zf_max_yesterday_width_float_val = params['history_cross_yesterday_width_value'][1]

                zf_min_today_width_float_val = params['history_cross_today_width_value'][0]
                zf_max_today_width_float_val = params['history_cross_today_width_value'][1]

                if zf_max_yesterday_float_val >= pre_close_rise >= zf_min_yesterday_float_val and zf_max_today_float_val >= last_close_rise >= zf_min_today_float_val:
                    if zf_max_yesterday_width_float_val >= pre_width_down >= zf_min_yesterday_width_float_val and zf_max_today_width_float_val >= last_width_down >= zf_min_today_width_float_val:
                        if zf_max_yesterday_width_float_val >= pre_width_up >= zf_min_yesterday_width_float_val and zf_max_today_width_float_val >= last_width_up >= zf_min_today_width_float_val:
                            # if pre_high > pre_close > pre_low and pre_high > pre_open > pre_low and last_high > last_close > last_low and last_high > last_open > last_low:
                            if stock_list:
                                row['pre_close_rise'] = round(pre_close_rise, 2)
                                row['last_close_rise'] = round(last_close_rise, 2)
                                out_stock_list.append(row)
                            else:
                                out_stock_list.append(
                                    {
                                        'id': row['id'],
                                        "symbol": row['symbol'],
                                        "exchange": row['exchange'],
                                        "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                        'close': df['close'].values[0],
                                        'trade_date': trade_date,
                                        'pre_close_rise': round(pre_close_rise, 2),
                                        'last_close_rise': round(last_close_rise, 2)
                                    }
                                )

        column_desc.append({'name': '十字星昨天的浮动点', 'key': 'pre_close_rise'})
        column_desc.append({'name': '十字星今天的浮动点', 'key': 'last_close_rise'})
        return out_stock_list, column_desc

    def stock_cross(self, params=None, stock_list=[], column_desc=[]):
        """股票十字星"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'symbol': row['symbol'],
                'exchange': row['exchange'],
                'end_date': params['end_date'],
                'order': ['datetime', 'desc'],
                'cycle': params['cycle'],
                'days_diff': params['days_diff'],
                "history_cross_yesterday_value": params['history_cross_yesterday_value'],
                "history_cross_today_value": params['history_cross_today_value'],
                "history_cross_yesterday_width_value": params['history_cross_yesterday_width_value'],
                "history_cross_today_width_value": params['history_cross_today_width_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            df = model_d.GetStockByCond(cond=cond)
            if len(df) > 1:
                trade_date = df['trade_date'].values[0]

                df['diff_rise'] = (df['close'] - df['open']) / df['open'] * 100
                last_close_rise = df['diff_rise'].values[0]
                pre_close_rise = df['diff_rise'].values[1]

                last_open = df["open"].values[0]
                pre_open = df["open"].values[1]

                last_close = df["close"].values[0]
                pre_close = df["close"].values[1]

                last_open_close_max = max(last_close, last_open)
                last_open_close_min = min(last_close, last_open)

                pre_open_close_max = max(pre_close, pre_open)
                pre_open_close_min = min(pre_close, pre_open)

                last_high = df["high"].values[0]
                pre_high = df["high"].values[1]

                last_low = df["low"].values[0]
                pre_low = df["low"].values[1]

                last_width_up = (last_high - last_open_close_max) / last_high * 100
                last_width_down = (last_open_close_min - last_low) / last_low * 100

                pre_width_up = (pre_high - pre_open_close_max) / pre_high * 100
                pre_width_down = (pre_open_close_min - pre_low) / pre_low * 100
                zf_min_yesterday_float_val = params['history_cross_yesterday_value'][0]
                zf_max_yesterday_float_val = params['history_cross_yesterday_value'][1]

                zf_min_today_float_val = params['history_cross_today_value'][0]
                zf_max_today_float_val = params['history_cross_today_value'][1]

                zf_min_yesterday_width_float_val = params['history_cross_yesterday_width_value'][0]
                zf_max_yesterday_width_float_val = params['history_cross_yesterday_width_value'][1]

                zf_min_today_width_float_val = params['history_cross_today_width_value'][0]
                zf_max_today_width_float_val = params['history_cross_today_width_value'][1]

                if zf_max_yesterday_float_val >= pre_close_rise >= zf_min_yesterday_float_val and zf_max_today_float_val >= last_close_rise >= zf_min_today_float_val:
                    if zf_max_yesterday_width_float_val >= pre_width_down >= zf_min_yesterday_width_float_val and zf_max_today_width_float_val >= last_width_down >= zf_min_today_width_float_val:
                        if zf_max_yesterday_width_float_val >= pre_width_up >= zf_min_yesterday_width_float_val and zf_max_today_width_float_val >= last_width_up >= zf_min_today_width_float_val:
                            # if pre_high > pre_close > pre_low and pre_high > pre_open > pre_low and last_high > last_close > last_low and last_high > last_open > last_low:
                            if stock_list:
                                row['pre_close_rise'] = round(pre_close_rise, 2)
                                row['last_close_rise'] = round(last_close_rise, 2)
                                out_stock_list.append(row)
                            else:
                                out_stock_list.append(
                                    {
                                        'id': row['id'],
                                        "symbol": row['symbol'],
                                        "exchange": row['exchange'],
                                        "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                        'close': df['close'].values[0],
                                        'trade_date': trade_date,
                                        'pre_close_rise': round(pre_close_rise, 2),
                                        'last_close_rise': round(last_close_rise, 2)
                                    }
                                )

        column_desc.append({'name': '十字星昨天的浮动点', 'key': 'pre_close_rise'})
        column_desc.append({'name': '十字星今天的浮动点', 'key': 'last_close_rise'})
        return out_stock_list, column_desc
