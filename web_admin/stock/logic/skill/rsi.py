from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from utils.utility import rsi


class CustomRsi:
    def custom_rsi(self, params=None, stock_list=[], stock_column_desc=[]):
        """计算rsi指标"""
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'symbol': row['symbol'],
                'exchange': row['exchange'],
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['datetime', '-desc'],
                'cycle': params['cycle'],
                'RSI_indicator_scope_value': params['RSI_indicator_scope_value'],
                'RSI_indicator_params_value': params['RSI_indicator_params_value']
            }

            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData

            df = model_d.GetStockByCond(cond=cond)
            rsi_params_value = int(cond['RSI_indicator_params_value'])
            if df is not None:
                if len(df) > rsi_params_value:
                    rsi_val = float(rsi(close_list=df["close"].values, array=False, n=rsi_params_value))
                    rsi_indicator_scope_max_value = float(cond["RSI_indicator_scope_value"][1])
                    rsi_indicator_scope_min_value = float(cond["RSI_indicator_scope_value"][0])
                    if rsi_indicator_scope_max_value >= rsi_val >= rsi_indicator_scope_min_value:
                        last_close = df['close'].values[-1]
                        trade_date = df['trade_date'].values[-1]
                        if stock_list:
                            row['rsi'] = round(rsi_val, 2)
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
                                    'rsi': round(rsi_val, 2)
                                }
                            )
        stock_column_desc.append({'name': 'RSI指标', 'key': 'rsi'})
        return out_stock_list, stock_column_desc
