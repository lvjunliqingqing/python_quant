from stock.logic.skill.sec_info import get_futures_sec_info, get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.dbbardata import FuturesData
from stock.models.moth_data import MothData


class Long:
    def stock_long(self, params=None, stock_list=[], stock_column_desc=[]):
        """股票涨幅做多"""
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
                "zf_long_one_value": params['zf_long_one_value'],
                "zf_long_two_value": params['zf_long_two_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            df = model_d.GetStockByCond(cond=cond)
            if len(df):
                last_close = df['close'].values[0]
                zf_long_one_value = round((df['close'].values[1] - df['close'].values[2]) / df['close'].values[2] * 100,
                                          2)
                zf_long_two_value = round((last_close - df['close'].values[1]) / df['close'].values[1] * 100, 2)
                trade_date = df['trade_date'].values[0]
                if cond['zf_long_one_value'][0] <= zf_long_one_value <= cond['zf_long_one_value'][1] and \
                        cond['zf_long_two_value'][0] <= zf_long_two_value <= cond['zf_long_two_value'][1]:
                    if stock_list:
                        row['zf_long_one_value'] = zf_long_one_value
                        row['zf_long_two_value'] = zf_long_two_value
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
                                'zf_long_one_value': zf_long_one_value,
                                'zf_long_two_value': zf_long_two_value
                            }
                        )
        stock_column_desc.append({'name': '前天涨幅', 'key': 'zf_long_one_value'})
        stock_column_desc.append({'name': '昨天涨幅', 'key': 'zf_long_two_value'})

        return out_stock_list, stock_column_desc

    def futures_long(self, params=None, stock_list=[], futures_column_desc=[]):
        """期货涨幅做多"""
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
                "zf_long_one_value": params['zf_long_one_value'],
                "zf_long_two_value": params['zf_long_two_value']
            }

            if cond['cycle'] == 'day':
                model_d = FuturesData

            df = model_d.get_futures_by_cond(cond=cond)
            if len(df):
                last_close = df['close'].values[0]
                zf_long_one_value = round((df['close'].values[1] - df['close'].values[2]) / df['close'].values[2] * 100,
                                          2)
                zf_long_two_value = round((last_close - df['close'].values[1]) / df['close'].values[1] * 100, 2)
                trade_date = df['trade_date'].values[0]
                if cond['zf_long_one_value'][0] <= zf_long_one_value <= cond['zf_long_one_value'][1] and \
                        cond['zf_long_two_value'][0] <= zf_long_two_value <= cond['zf_long_two_value'][1]:
                    if stock_list:
                        row['zf_long_one_value'] = zf_long_one_value
                        row['zf_long_two_value'] = zf_long_two_value
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
                                'zf_long_one_value': zf_long_one_value,
                                'zf_long_two_value': zf_long_two_value
                            }
                        )
        futures_column_desc.append({'name': '前天涨幅', 'key': 'zf_long_one_value'})
        futures_column_desc.append({'name': '昨天涨幅', 'key': 'zf_long_two_value'})

        return out_stock_list, futures_column_desc
