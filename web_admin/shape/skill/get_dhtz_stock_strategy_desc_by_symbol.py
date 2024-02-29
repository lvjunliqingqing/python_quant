import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shape.models.dhtz_stock_strategy_desc import DhtzStockStrategyDesc


@csrf_exempt
def get_dhtz_stock_strategy_desc_by_symbol(request):
    """根据前端传过的参数，查询--策略参数信息表"""
    if request.method == "POST":
        try:
            received_json_data = json.loads(request.body.decode())
            symbol = received_json_data['symbol']
            exchange = received_json_data['exchange']
        except:
            return {
                    'code': -1,
                    'msg': '参数未传'
                }
        try:
            strategy_name = received_json_data['strategy_name']
        except:
            strategy_name = ""
        try:
            direction = received_json_data['direction']
        except:
            direction = ""
        strategy_desc_info_list = []
        query_set = DhtzStockStrategyDesc().get_by_symbol_exchange(symbol, exchange, strategy_name, direction)
        if query_set:
            for i in query_set:
                strategy_desc_info_list.append(
                    {
                        "strategy_class_name": i.strategy_class_name,
                        "symbol": i.symbol,
                        "exchange": i.exchange,
                        "strategy_no": i.strategy_no,
                        "open_is": i.open_is,
                        "strategy_name": i.strategy_name,
                        "strategy_desc": i.strategy_desc,
                        "strategy_remark": i.strategy_remark,
                        "strategy_args": i.strategy_args,
                        "link_table": i.link_table
                    }
                )
        out = {
            'code': 0,
            'msg': 'ok',
            'data': strategy_desc_info_list[0] if len(strategy_desc_info_list) == 1 else strategy_desc_info_list,
        }
        return JsonResponse(out)
