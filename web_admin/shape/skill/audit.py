import datetime
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.authentication import jwt_decode_handler

from shape.models.open_symbol_data import OpenSymbolDataModel
from user.models import User
import time


def decorator(func):
    def wrapper(request):
        try:
            # token = request.META.get("HTTP_X_TOKEN")
            token = request.META.get("HTTP_AUTHORIZATION")[4:]
            token_user = jwt_decode_handler(token)
            ser_id = token_user['user_id']  # 获取用户id
            account_id = User.objects.get(id=ser_id).account_id
            if not account_id:
                return JsonResponse({"code": 50008, "msg": "非认证用户，请从新登录再操作"})
        except:
            return JsonResponse({"code": 50008, "msg": "账号未登录，请登录后再操作"})
        try:
            current_time = int(time.time())
            exp = int(token_user["exp"])
            if current_time - exp >= 86400:
                return JsonResponse({"code": 50008, "msg": "jwt已过期,请重新登录"})
        except:
            return JsonResponse({"code": 50008, "msg": "账号未登录，请登录后再操作"})

        data = func(request)
        return data
    return wrapper


@csrf_exempt
# @login_required(login_url='/login_permission')
@decorator
def audit(request):
    if request.method == "POST":
        received_json_data = json.loads(request.body.decode())
        id = received_json_data["id"]
        audit_status = int(received_json_data["audit_status"])
        try:
            result = OpenSymbolDataModel.objects.filter(id=id).update(audit_status=audit_status, audit_time=datetime.datetime.now())
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


def login(request):
    out = {
        "code": 50008,
        "msg": "暂时未有权限，请重新登录后，再操作"
    }
    return JsonResponse(out)


