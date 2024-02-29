from stock.logic.skill.sec_info import get_stock_sec_info, get_futures_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData


class BreakHistoryVolume:
    def stock_break_volume(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票突破历史成交量"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'symbol': row['symbol'],
                'exchange': row['exchange'],
                'end_date': params['end_date'],
                'order': ['datetime', 'desc'],
                'cycle': params['cycle'],
                'days_diff': params['days_diff']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            df = model_d.GetStockByCond(cond=cond)
            if len(df) == int(cond["days_diff"]):
                last_close = df['close'].values[0]
                last_volume = df['volume'].values[0]
                trade_date = df['trade_date'].values[0]
                df.drop(df.index[0], inplace=True)
                history_volume_max = df['volume'].max()
                if last_volume > history_volume_max:
                    break_bill = round((last_volume - history_volume_max) / history_volume_max * 100, 2)
                    if stock_list:
                        row['history_volume_max'] = history_volume_max
                        row['break_bill_volume'] = break_bill
                        out_stock_list.append(row)
                    else:
                        out_stock_list.append(
                            {
                                'id': row['id'],
                                "symbol": row['symbol'],
                                "exchange": row['exchange'],
                                "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                'close': last_close,
                                'trade_date': trade_date,
                                'history_volume_max': history_volume_max,
                                'break_bill_volume': break_bill
                            }
                        )
        stock_column_desc.append({'name': '历史成交量高点', 'key': 'history_volume_max'})
        stock_column_desc.append({'name': '突破历史成交量高点比例(%)', 'key': 'break_bill_volume', 'sort': True})
        return out_stock_list, stock_column_desc
