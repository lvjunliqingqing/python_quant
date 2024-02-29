# Create your views here.
import json
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.authentication import jwt_decode_handler
from user.models import User, DhtzTradeAccountInfo


def index(request):
    return HttpResponse(u"ok")

def info(request):
    try:
        # token = request.META.get("HTTP_X_TOKEN")
        token = request.META.get("HTTP_AUTHORIZATION")[4:]
        token_user = jwt_decode_handler(token)
        user_id = token_user['user_id']  # 获取用户id
        user_data = User.objects.get(id=user_id)
        query_account_info = DhtzTradeAccountInfo.objects.filter(username=user_data.username)
        account_id_list = []
        data = {}
        if query_account_info:
            data['list'] = list(query_account_info.values())
            for i in query_account_info:
                account_id_list.append(int(i.account_id))

        out = {
            "code": 0,
            "data": {
                "name":  user_data.username,
                "avatar": user_data.avatar,
                "account_id": account_id_list,
                "username_account_info": data
            }
        }
    except:
        out = {
            "code": 0,
            "data": {
                "name": 'dhtz',
                "avatar": 'http://img.52z.com/upload/news/image/20200211/20200211033419_30197.jpg',
                "account_id": None,
                "username_account_info": {}
            }
        }
    return JsonResponse(out)


@csrf_exempt
def logout(request):
    """
    退出登录
    """
    auth.logout(request)
    data = {
        "code": 0,
        "msg": "退出成功"
    }
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def change_password(request):
    """
    修改密码
    """
    if request.method == "POST":
        request_data = json.loads(request.body.decode())
        token = request.META.get("HTTP_AUTHORIZATION")[4:]
        token_user = jwt_decode_handler(token)
        ser_id = token_user['user_id']  # 获取用户id
        user = User.objects.get(id=ser_id)
        if not user.check_password(request_data["oldpasswd"]):
            return JsonResponse({
                "code": -1,
                "msg": f"{user.username}的原密码输入错误"
            })
        if request_data["newpasswd"] != request_data["newpasswd1"]:
            return JsonResponse({
                "code": -1,
                "msg": "两次密码输入不一致,请重新输入"
            })
        user.set_password(request_data["newpasswd1"])
        user.save()
        return JsonResponse({
            "code": 0,
            "msg": f"{user.username}的密码修改成功"
        })





