from stock.logic.skill.sec_info import get_futures_sec_info
from stock.models.dbbardata import FuturesData

class BigYinLowerMiddlePart:
    def futures_big_yin_lower_middle_part(self, params=None, stock_list=[], column_desc=[]):
        """期货大阴中下部"""
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
                "big_yin_lower_middle_part_yesterday_value": params['big_yin_lower_middle_part_yesterday_value']
            }

            if cond['cycle'] == 'day':
                model_d = FuturesData

            elif cond['cycle'] == 'month':
                model_d = FuturesData

            df = model_d.get_futures_by_cond(cond=cond)
            if len(df):
                trade_date = df['trade_date'].values[0]
                df['diff_rise'] = (df['close'] - df['open']) / df['open'] * 100
                pre_close_rise = df['diff_rise'].values[1]

                zf_min_yesterday_float_val = params['big_yin_lower_middle_part_yesterday_value'][0]
                zf_max_yesterday_float_val = params['big_yin_lower_middle_part_yesterday_value'][1]

                central_val = (df["close"].values[1] + df['open'].values[1])/2
                last_close = df["close"].values[0]
                if zf_max_yesterday_float_val >= pre_close_rise >= zf_min_yesterday_float_val and last_close < central_val:
                    if stock_list:
                        row['pre_close_rise'] = round(pre_close_rise, 2)
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
                                'central_val': round(central_val, 2)
                            }
                        )

        column_desc.append({'name': '阴线的长度值', 'key': 'pre_close_rise'})
        column_desc.append({'name': '大阴中部位置值', 'key': 'central_val'})
        return out_stock_list, column_desc
