
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.utils import jwt_decode_handler
from shape.models.dhtz_stock_open_manual_symbol_data import DhtzStockOpenManualSymbolDataModel
from shape.models.dhtz_stock_strategy_desc import DhtzStockStrategyDesc
from user.models import User


@csrf_exempt
def stock_audit_manual_info(request):
    """股票--查询手动交易清单表中数据，返回给前端"""
    if request.method == "POST":
        received_json_data = json.loads(request.body.decode())
        try:
            token = request.META.get("HTTP_AUTHORIZATION")[4:]
            token_user = jwt_decode_handler(token)
            ser_id = token_user['user_id']  # 获取用户id
            account_id = User.objects.get(id=ser_id).account_id
        except:
            return JsonResponse({"code": 50008, "msg": "账号未登录，请登录后再操作"})
        try:
            audit_status = received_json_data["audit_status"]
        except:
            audit_status = 0
        try:
            status = received_json_data["status"]
        except:
            status = 1

        dhtz_open_symbol_data_list = []
        query_set = DhtzStockOpenManualSymbolDataModel().query_by_audit_status_account_id_status(account_id, audit_status, status)
        desc_map = DhtzStockStrategyDesc().desc_map()
        if query_set:
            for i in query_set:
                key = f"{i.strategy_name}.{i.symbol}.{i.exchange}"
                dhtz_open_symbol_data_list.append(
                    {
                        "id": i.id,
                        "account_id": i.account_id,
                        "symbol": i.symbol,
                        "exchange": i.exchange,
                        "direction": i.direction,
                        "offset": i.offset,
                        "trade_date": i.trade_date,
                        "status": i.status,
                        "audit_status": i.audit_status,
                        "strategy_name": i.strategy_name,
                        "strategy_desc": desc_map[key] if desc_map[key] else desc_map[f"{i.strategy_name}.."],
                        "audit_time": i.audit_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(i.audit_time, "strftime") else " "
                    }
                )

        column_desc = [
                    {'name': 'id', 'key': 'id'},
                    {'name': '交易账户id', 'key': 'account_id'},
                    {'name': '标的物代码', 'key': 'symbol'},
                    {'name': '交易所', 'key': 'exchange', 'sort': True},
                    {'name': '方向', 'key': 'direction', 'sort': True},
                    {'name': '开平', 'key': 'offset'},
                    {'name': '交易日期', 'key': 'trade_date'},
                    {'name': '是否今天交易', 'key': 'status'},
                    {'name': '审核状态', 'key': 'audit_status'},
                    {'name': '策略名字', 'key': 'strategy_name'},
                    {'name': '策略描述', 'key': 'strategy_desc'},
                    {'name': '审核时间', 'key': 'audit_time'}
                ]

        out = {
            'code': 0,
            'msg': 'ok',
            'data': {
                "list": dhtz_open_symbol_data_list,
                'col': column_desc,
            }
        }
        return JsonResponse(out)
