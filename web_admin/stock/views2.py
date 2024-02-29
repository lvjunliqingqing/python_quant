import pandas as pd
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from stock.utils import Choose_condition


@csrf_exempt
def condition(request):
    """条件选股"""
    sec_info_list, DataTable, start_date, end_date, vt_symbol_map, cond = Choose_condition(request)
    out_stock_list = []
    key_list = []
    for s in sec_info_list:
        tmp_data = DataTable.objects.filter(
            Q(datetime__gte=start_date)
            & Q(datetime__lte=end_date)
            & Q(symbol=s['symbol'])
            & Q(exchange=s['exchange'])
        ).order_by('-datetime')
        tmp_stock_data_list = []
        for st in tmp_data:
            tmp_stock_data_list.append({
                'close': st.close_price,
                'open': st.open_price,
                'trade_date': st.datetime.strftime("%Y-%m-%d"),
                'high': st.high_price,
                'low': st.low_price,
                'volume': st.volume,
                'symbol': st.symbol,
                'exchange': st.exchange,
                'display_name': vt_symbol_map[f"{st.symbol}.{st.exchange}"]
            })
        df = pd.DataFrame(tmp_stock_data_list)
        last_close = df['close'].values[0]
        trade_date = df['trade_date'].values[0]
        df.drop(df.index[0], inplace=True)
        # 存储突破历史高点的股票数据
        high_stock_dict = {}
        # 存储突破均线的股票数据
        ma_stock_dict = {}
        for key, value in cond.items():
            key_list.append(key)
            value = int(value)
            if key == "break_high":
                max_high = df['high'][-value:].max()
                if last_close >= max_high:
                    high_stock_dict = {
                                        "symbol": s['symbol'],
                                        "exchange": s['exchange'],
                                        "display_name": vt_symbol_map[f"{s['symbol']}.{s['exchange']}"],
                                        'close': last_close,
                                        'trade_date': trade_date
                                        # 'high': max_high,
                                        # 'break_bill': break_bill
                                      }

            if key == "break_ma":
                mean_value = df['close'][-value:].mean()
                if last_close >= mean_value:
                    ma_stock_dict = {
                        "symbol": s['symbol'],
                        "exchange": s['exchange'],
                        "display_name": vt_symbol_map[f"{s['symbol']}.{s['exchange']}"],
                        'close': last_close,
                        'trade_date': trade_date
                    }
        if "break_ma" not in key_list and "break_high" in key_list:
            high_stock_dict['high'] = max_high
            break_high_bill = (round((last_close - max_high) / max_high * 100, 2))
            high_stock_dict['break_high_bill'] = break_high_bill
            out_stock_list.append(high_stock_dict)

        elif "break_high" not in key_list and "break_ma" in key_list:
            ma_stock_dict["mean_value"] = mean_value
            break_mean_bill = (round((last_close - mean_value) / mean_value * 100, 2))
            ma_stock_dict['break_mean_bill'] = break_mean_bill
            out_stock_list.append(ma_stock_dict)

        elif "break_high" in key_list and "break_ma" in key_list:
            list1 = [high_stock_dict]
            list2 = [ma_stock_dict]
            list3 = [i for i in list1 if i in list2]
            if list3 and list3 != [{}]:
                print(list3)
                for i in list3:
                    i["mean_value"] = mean_value
                    break_mean_bill = (round((last_close - mean_value) / mean_value * 100, 2))
                    i['break_mean_bill'] = break_mean_bill
                    i['high'] = max_high
                    break_high_bill = (round((last_close - max_high) / max_high * 100, 2))
                    i['break_high_bill'] = break_high_bill
                    out_stock_list.append(i)

    out = {
        'code': 0,
        'msg': 'ok',
        'data': out_stock_list
    }
    return JsonResponse(out)

