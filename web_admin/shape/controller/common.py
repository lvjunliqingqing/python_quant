import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from shape.models.open_symbol_data import OpenSymbolDataModel
from shape.models.shape_symbol_info import ShapeSymbolInfoModel


@csrf_exempt
def shape_symbo_info(request):
    if request.method == "POST":
        received_json_data = json.loads(request.body.decode())
        try:
            trade_day = received_json_data["trade_day"]
        except:
            trade_day = None

        shape_symbo_info_list = []
        query_set = ShapeSymbolInfoModel().get_all(trade_day)
        # data_list = OpenSymbolDataModel().get_shape_not_open(trade_day)
        if query_set:
            for i in query_set:
                # i_key = f"{i.symbol}.{i.exchange}.{i.direction}.{i.offset}"
                # if i_key not in data_list:
                shape_symbo_info_list.append(
                    {
                        "symbol": i.symbol,
                        "exchange": i.exchange,
                        "direction": i.direction,
                        "offset": i.offset,
                        "trade_date": i.trade_date,
                        # "extend": i.extend,
                        "open": i.open,
                        "close": i.close,
                        "high": i.high,
                        "low": i.low,
                        "vt_symbol": i.vt_symbol,
                        "zf_rise": f"{round(i.zf_rise * 100, 3)}",
                        "shape": i.shape
                    }
                )
        column_desc = [
                    {'name': '标的物代码', 'key': 'symbol'},
                    {'name': '交易所', 'key': 'exchange'},
                    {'name': '方向', 'key': 'direction'},
                    {'name': '开平', 'key': 'offset'},
                    {'name': '交易日期', 'key': 'trade_date'},
                    # {'name': '扩展属性json', 'key': 'extend'},
                    {'name': '开盘价', 'key': 'open'},
                    {'name': '收盘价', 'key': 'close'},
                    {'name': '最高价', 'key': 'high'},
                    {'name': '最低价', 'key': 'low'},
                    {'name': '本地代码', 'key': 'vt_symbol'},
                    {'name': '涨跌幅(%)', 'key': 'zf_rise'},
                    {'name': '形态', 'key': 'shape'},

                ]

        out = {
            'code': 0,
            'msg': 'ok',
            'data': {
                "list": shape_symbo_info_list,
                'col': column_desc,
            }
        }
        return JsonResponse(out)
