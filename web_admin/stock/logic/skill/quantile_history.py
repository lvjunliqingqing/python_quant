
from stock.logic.skill.sec_info import get_futures_sec_info, get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.dbbardata import FuturesData
from stock.models.moth_data import MothData


class QuantileHistory:

    def quantile_long(self, params=None, stock_list=[], column_desc=[]):
        """期货涨幅历史分位数"""
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
                "df_history_long_yesterday_value": params['df_history_long_yesterday_value'],
                "df_history_long_today_value": params['df_history_long_today_value']
            }

            if cond['cycle'] == 'day':
                model_d = FuturesData

            elif cond['cycle'] == 'month':
                model_d = FuturesData

            df = model_d.get_futures_by_cond(cond=cond)
            if len(df) > 1:
                trade_date = df['trade_date'].values[0]

                # df['diff_rise'] = df['close'].diff(periods=-1) / df['close'].shift(-1) * 100
                df['diff_rise'] = (df['close'] - df['open']) / df['open'] * 100

                last_close_rise = df['diff_rise'].values[0]
                pre_close_rise = df['diff_rise'].values[1]

                # 根据前端传过来的参数计算昨天分位数的最小值和最大值
                zf_min_yesterday_quantile_val = params['df_history_long_yesterday_value'][0] / 100
                zf_max_yesterday_quantile_val = params['df_history_long_yesterday_value'][1] / 100

                if zf_min_yesterday_quantile_val == 0.0 and zf_max_yesterday_quantile_val == 1.0:
                    zf_min_yesterday_quantile = 0
                    zf_max_yesterday_quantile = 100
                else:
                    zf_min_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_yesterday_quantile_val)
                    zf_max_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_yesterday_quantile_val)

                # 根据前端传过来的参数计算今天分位数的最小值和最大值
                zf_min_today_quantile_val = params['df_history_long_today_value'][0] / 100
                zf_max_today_quantile_val = params['df_history_long_today_value'][1] / 100

                if zf_min_today_quantile_val == 0.0 and zf_max_today_quantile_val == 1.0:
                    zf_min_today_quantile = 0
                    zf_max_today_quantile = 100.0
                else:
                    zf_min_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_today_quantile_val)
                    zf_max_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_today_quantile_val)

                if zf_max_yesterday_quantile >= pre_close_rise >= zf_min_yesterday_quantile and zf_max_today_quantile >= last_close_rise >= zf_min_today_quantile:
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

        column_desc.append({'name': '昨天的涨幅', 'key': 'pre_close_rise'})
        column_desc.append({'name': '今天的涨幅', 'key': 'last_close_rise'})
        return out_stock_list, column_desc

    def quantile_short(self, params=None, stock_list=[], column_desc=[]):
        """期货跌幅历史分位数"""
        # count = 0
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
                "df_history_long_yesterday_value": params['df_history_short_yesterday_value'],
                "df_history_long_today_value": params['df_history_short_today_value']
            }

            if cond['cycle'] == 'day':
                model_d = FuturesData

            elif cond['cycle'] == 'month':
                model_d = FuturesData

            df = model_d.get_futures_by_cond(cond=cond)

            if len(df) > 1:

                trade_date = df['trade_date'].values[0]
                # df['diff_rise'] = df['close'].diff(periods=-1) / df['close'].shift(-1) * 100
                df['diff_rise'] = (df['close'] - df['open']) / df['open'] * 100

                last_close_rise = df['diff_rise'].values[0]
                pre_close_rise = df['diff_rise'].values[1]

                # 根据前端传过来的参数计算昨天分位数的最小值和最大值
                zf_min_yesterday_quantile_val = params['df_history_short_yesterday_value'][0] / 100
                zf_max_yesterday_quantile_val = params['df_history_short_yesterday_value'][1] / 100

                if zf_min_yesterday_quantile_val == 0.0 and zf_max_yesterday_quantile_val == 1.0:
                    zf_min_yesterday_quantile = -100.0
                    zf_max_yesterday_quantile = 0
                else:
                    zf_min_yesterday_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(zf_min_yesterday_quantile_val)
                    zf_max_yesterday_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_max_yesterday_quantile_val)

                # 根据前端传过来的参数计算今天分位数的最小值和最大值
                zf_min_today_quantile_val = params['df_history_short_today_value'][0] / 100
                zf_max_today_quantile_val = params['df_history_short_today_value'][1] / 100

                if zf_min_today_quantile_val == 0.0 and zf_max_today_quantile_val == 1.0:
                    zf_min_today_quantile = -100.0
                    zf_max_today_quantile = 0
                else:
                    zf_min_today_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_min_today_quantile_val)
                    zf_max_today_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_max_today_quantile_val)

                if zf_max_yesterday_quantile >= pre_close_rise >= zf_min_yesterday_quantile and zf_max_today_quantile >= last_close_rise >= zf_min_today_quantile:
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
        #         else:
        #             count +=1
        #             print("历史涨幅最小：", zf_min_today_quantile, "历史涨幅最大：", zf_max_today_quantile, "今天实际涨幅：",
        #                   last_close_rise,
        #                   zf_min_today_quantile_val,
        #                   zf_max_today_quantile_val)
        #             print("历史涨幅最小：", zf_min_yesterday_quantile, "历史涨幅最大：", zf_max_yesterday_quantile, "昨天实际涨幅：",
        #                   pre_close_rise,
        #                   zf_min_yesterday_quantile_val, zf_max_yesterday_quantile_val)
        #             print(df[0:1].symbol)
        #             print("                                              ")
        # print(count)
        column_desc.append({'name': '昨天的跌幅', 'key': 'pre_close_rise'})
        column_desc.append({'name': '今天的跌幅', 'key': 'last_close_rise'})
        return out_stock_list, column_desc


    def stock_quantile_long(self, params=None, stock_list=[], column_desc=[]):
        """
        股票涨幅历史分位数
        """
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
                "df_history_long_yesterday_value": params['df_history_long_yesterday_value'],
                "df_history_long_today_value": params['df_history_long_today_value']
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

                # 根据前端传过来的参数计算昨天分位数的最小值和最大值
                zf_min_yesterday_quantile_val = params['df_history_long_yesterday_value'][0] / 100
                zf_max_yesterday_quantile_val = params['df_history_long_yesterday_value'][1] / 100

                if zf_min_yesterday_quantile_val == 0.0 and zf_max_yesterday_quantile_val == 1.0:
                    zf_min_yesterday_quantile = 0
                    zf_max_yesterday_quantile = 100
                else:
                    zf_min_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_yesterday_quantile_val)
                    zf_max_yesterday_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_yesterday_quantile_val)

                # 根据前端传过来的参数计算今天分位数的最小值和最大值
                zf_min_today_quantile_val = params['df_history_long_today_value'][0] / 100
                zf_max_today_quantile_val = params['df_history_long_today_value'][1] / 100

                if zf_min_today_quantile_val == 0.0 and zf_max_today_quantile_val == 1.0:
                    zf_min_today_quantile = 0
                    zf_max_today_quantile = 100.0
                else:
                    zf_min_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_min_today_quantile_val)
                    zf_max_today_quantile = df[df['diff_rise'] > 0]['diff_rise'].quantile(zf_max_today_quantile_val)

                if zf_max_yesterday_quantile >= pre_close_rise >= zf_min_yesterday_quantile and zf_max_today_quantile >= last_close_rise >= zf_min_today_quantile:
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

        column_desc.append({'name': '昨天的涨幅', 'key': 'pre_close_rise'})
        column_desc.append({'name': '今天的涨幅', 'key': 'last_close_rise'})
        return out_stock_list, column_desc


    def stock_quantile_short(self, params=None, stock_list=[], column_desc=[]):
        """
        股票跌幅历史分位数
        """
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
                "df_history_long_yesterday_value": params['df_history_short_yesterday_value'],
                "df_history_long_today_value": params['df_history_short_today_value']
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

                # 根据前端传过来的参数计算昨天分位数的最小值和最大值
                zf_min_yesterday_quantile_val = params['df_history_short_yesterday_value'][0] / 100
                zf_max_yesterday_quantile_val = params['df_history_short_yesterday_value'][1] / 100

                if zf_min_yesterday_quantile_val == 0.0 and zf_max_yesterday_quantile_val == 1.0:
                    zf_min_yesterday_quantile = -100.0
                    zf_max_yesterday_quantile = 0
                else:
                    zf_min_yesterday_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(zf_min_yesterday_quantile_val)
                    zf_max_yesterday_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_max_yesterday_quantile_val)

                # 根据前端传过来的参数计算今天分位数的最小值和最大值
                zf_min_today_quantile_val = params['df_history_short_today_value'][0] / 100
                zf_max_today_quantile_val = params['df_history_short_today_value'][1] / 100

                if zf_min_today_quantile_val == 0.0 and zf_max_today_quantile_val == 1.0:
                    zf_min_today_quantile = -100.0
                    zf_max_today_quantile = 0
                else:
                    zf_min_today_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_min_today_quantile_val)
                    zf_max_today_quantile = df[df['diff_rise'] < 0]['diff_rise'].quantile(
                        zf_max_today_quantile_val)

                if zf_max_yesterday_quantile >= pre_close_rise >= zf_min_yesterday_quantile and zf_max_today_quantile >= last_close_rise >= zf_min_today_quantile:
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
        column_desc.append({'name': '昨天的跌幅', 'key': 'pre_close_rise'})
        column_desc.append({'name': '今天的跌幅', 'key': 'last_close_rise'})
        return out_stock_list, column_desc