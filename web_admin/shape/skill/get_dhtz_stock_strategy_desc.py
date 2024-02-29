from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shape.models.dhtz_stock_strategy_desc import DhtzStockStrategyDesc



@csrf_exempt
def get_dhtz_stock_strategy_desc(request):
    """股票-获取策略参数"""
    if request.method == "POST":
        strategy_desc_info_list = []
        query_set = DhtzStockStrategyDesc().query_all()
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
            'data': strategy_desc_info_list,
        }
        return JsonResponse(out)
