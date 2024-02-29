
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shape.models.dhtz_stock_open_manual_symbol_data import DhtzStockOpenManualSymbolDataModel
from shape.skill.audit import decorator


@csrf_exempt
@decorator
def stock_update_dhtz_open_manual_symbol_data(request):
    """股票--手动交易清单审核API"""
    if request.method == "POST":
        received_json_data = json.loads(request.body.decode())
        id = received_json_data["id"]

        if "audit_status" in received_json_data.keys() and "status" in received_json_data.keys():
            audit_status = int(received_json_data["audit_status"])
            status = int(received_json_data["status"])
            try:
                result = DhtzStockOpenManualSymbolDataModel.objects.filter(id=id).update(audit_status=audit_status, status=status)
            except Exception as e:
                return JsonResponse({"code": -1, "msg": e})

        elif "audit_status" in received_json_data.keys():
            audit_status = int(received_json_data["audit_status"])
            try:
                result = DhtzStockOpenManualSymbolDataModel.objects.filter(id=id).update(audit_status=audit_status)
            except Exception as e:
                return JsonResponse({"code": -1, "msg": e})

        elif "status" in received_json_data.keys():
            status = int(received_json_data["status"])
            try:
                result = DhtzStockOpenManualSymbolDataModel.objects.filter(id=id).update(status=status)
            except Exception as e:
                return JsonResponse({"code": -1, "msg": e})

        if result:
            out = {
                'code': 0,
                'msg': 'ok'
            }

        else:
            out = {
                'code': -1,
                'msg': 'failed'
            }
        return JsonResponse(out)
