import json
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from stock.logic.skill.futures_interface import futures_interface
from stock.logic.skill.stock_interface import stock_interface

# Create your views here.
@csrf_exempt
def condition(request):
    """条件选股"""
    if request.method == 'POST':
        # 由于request.body获取到二进制的数据，最好用decode()解码下。
        received_json_data = json.loads(request.body.decode())
        condition = received_json_data['condition']
        dynamicParams = received_json_data['dynamicParams']
        end_date = received_json_data['end_date']
        cycle = received_json_data['cycle']
        sec_type = received_json_data['sec_type']
        params = defaultdict(lambda: defaultdict(list))
        # 设置个默认值(前端不传参数时，默认days_diff = 5)
        for par in dynamicParams:
            params[par['group']][par['key']] = par

        if sec_type == "stock":
            out = stock_interface(condition, cycle, params, end_date)
        elif sec_type == "futures":
            out = futures_interface(condition, cycle, params, end_date)
        return JsonResponse(out)



