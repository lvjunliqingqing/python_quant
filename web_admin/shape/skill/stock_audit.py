import datetime
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shape.models.stock_open_symbol_data import StockOpenSymbolDataModel
from shape.skill.audit import decorator


@csrf_exempt
@decorator
def stock_audit(request):
    """股票--交易清单审核API"""
    if request.method == "POST":
        received_json_data = json.loads(request.body.decode())
        id = received_json_data["id"]
        audit_status = int(received_json_data["audit_status"])
        try:
            result = StockOpenSymbolDataModel.objects.filter(id=id).update(audit_status=audit_status, audit_time=datetime.datetime.now())
        except Exception as e:
            return JsonResponse({"code": -1, "msg": e})

        if result:
            if audit_status:
                out = {
                    'code': 0,
                    'msg': '审核通过！'
                }
            else:
                out = {
                    'code': 0,
                    'msg': '审核不通过！'
                }
        else:
            out = {
                'code': -1,
                'msg': '审核失败！'
            }
        return JsonResponse(out)


