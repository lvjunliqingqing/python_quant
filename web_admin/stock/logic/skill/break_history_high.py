from stock.logic.skill.sec_info import get_futures_sec_info, get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.dbbardata import FuturesData
from stock.models.moth_data import MothData


class BreakHistoryHigh:
    def stock_break_high(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票突破历史高点"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        number_of_days = params['from_the_current_number_of_days']
        for row in sec_info_list:
            # 构建突破历史高点的查询条件
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
            if len(df) == int(cond['days_diff']):
                last_high = df['high'].values[0]
                trade_date = df['trade_date'].values[0]
                last_close = df['close'].values[0]
                df.drop(df.index[0], inplace=True)

                max_high = df['high'].max()
                max_location = int(df["high"].idxmax()) + 1
                pre_high = df["high"].values[0]
                df.drop(df.index[0], inplace=True)

                pre_max_high = df['high'].max()
                if last_high > max_high and pre_high < pre_max_high and max_location >= number_of_days:
                    # print(max_location, df["trade_date"][max_location - 1], row['symbol'])
                    break_bill = (round((last_high - max_high) / max_high * 100, 2))
                    if stock_list:
                        row['high'] = max_high
                        row['break_bill_high'] = break_bill
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
                                'high': max_high,
                                'break_bill_high': break_bill
                            }
                        )
        stock_column_desc.append({'name': '历史高价', 'key': 'high'})
        stock_column_desc.append({'name': '突破历史高点比例(%)', 'key': 'break_bill_high', 'sort': True})

        return out_stock_list, stock_column_desc

    def futures_break_high(self, params=None, stock_list=[], futures_column_desc=[]):
        """期货突破历史高点"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_futures_sec_info(stock_list)
        number_of_days = params['from_the_current_number_of_days']
        for row in sec_info_list:
            # 构建突破历史高点的查询条件
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
            if len(df) == int(cond['days_diff']):
                last_high = df['high'].values[0]
                trade_date = df['trade_date'].values[0]
                last_close = df['close'].values[0]
                df.drop(df.index[0], inplace=True)
                max_high = df['high'].max()
                max_location = int(df["high"].idxmax()) + 1

                pre_high = df["high"].values[0]
                df.drop(df.index[0], inplace=True)
                pre_max_high = df['high'].max()
                if last_high > max_high and pre_high < pre_max_high and max_location >= number_of_days:
                    break_bill = (round((last_high - max_high) / max_high * 100, 2))
                    if stock_list:
                        row['high'] = max_high
                        row['break_bill_high'] = break_bill
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
                                'high': max_high,
                                'break_bill_high': break_bill
                            }
                        )
        futures_column_desc.append({'name': '历史高价', 'key': 'high'})
        futures_column_desc.append({'name': '突破历史高点比例(%)', 'key': 'break_bill_high', 'sort': True})

        return out_stock_list, futures_column_desc
