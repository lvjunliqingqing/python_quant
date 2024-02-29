from stock.logic.skill.sec_info import get_stock_sec_info, get_futures_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.dbbardata import FuturesData
from stock.models.moth_data import MothData


class BreakHistoryMa:
    def stock_break_ma(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票突破历史均线"""
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
                trade_date = df['trade_date'].values[0]
                history_ma = round(df['close'].mean(), 2)
                if last_close >= history_ma:
                    break_bill = (round((last_close - history_ma) / history_ma * 100, 2))
                    if stock_list:
                        row['ma'] = history_ma
                        row['break_bill_ma'] = break_bill
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
                                'ma': history_ma,
                                'break_bill_ma': break_bill
                            }
                        )
        stock_column_desc.append({'name': '均线', 'key': 'ma'})
        stock_column_desc.append({'name': '突破均线比例(%)', 'key': 'break_bill_ma', 'sort': True})
        return out_stock_list, stock_column_desc

    def futures_break_high_ma(self, params=None, stock_list=[], futures_column_desc=[]):
        """期货突破历史均线"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_futures_sec_info(stock_list)
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
                model_d = FuturesData
            df = model_d.get_futures_by_cond(cond=cond)
            if len(df) == int(cond["days_diff"]):
                last_close = df['close'].values[0]
                trade_date = df['trade_date'].values[0]
                history_ma = round(df['close'].mean(), 2)
                if last_close >= history_ma:
                    break_bill = (round((last_close - history_ma) / history_ma * 100, 2))
                    if stock_list:
                        row['ma'] = history_ma
                        row['break_bill_ma'] = break_bill
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
                                'ma': history_ma,
                                'break_bill_ma': break_bill
                            }
                        )
        futures_column_desc.append({'name': '均线', 'key': 'ma'})
        futures_column_desc.append({'name': '突破均线比例(%)', 'key': 'break_bill_ma', 'sort': True})

        return out_stock_list, futures_column_desc
