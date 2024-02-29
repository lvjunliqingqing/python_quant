from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.utils import jwt_decode_handler

from shape.models.position_data import PositionDataModel
from user.models import User


@csrf_exempt
def get_position_info(request):
    """查询持仓信息"""
    if request.method == 'POST':
        try:
            # 由于request.body获取到二进制的数据，最好用decode()解码下。
            token = request.META.get('HTTP_AUTHORIZATION')[4:]
            token_user = jwt_decode_handler(token)
            ser_id = token_user['user_id']  # 获取用户id
            account_id = User.objects.get(id=ser_id).account_id
        except:
            return JsonResponse({
                "code": -1,
                "msg": "失败,没有token值,请登录后再操作。"
            })
        shape_symbo_info_list = []
        query_set = PositionDataModel().get_position_info(account_id=account_id)
        if query_set:
            for i in query_set:
                shape_symbo_info_list.append(
                    {
                        "account_id": i.account_id,
                        # "balance": i.balance,
                        "symbol": i.symbol,
                        "exchange": i.exchange,
                        "direction": i.direction,
                        "position": int(i.position),
                        "yd_position": int(i.yd_position),
                        "frozen": i.frozen,
                        "price": i.price,
                        "position_profit": i.position_profit,
                        "gateway_name": i.gateway_name,
                        "trading_day": i.trading_day
                    }
                    )
        column_desc = [
            {'name': '交易账户id', 'key': 'account_id'},
            # {'name': '账号余额', 'key': 'balance'},
            {'name': '代码', 'key': 'symbol'},
            {'name': '交易所', 'key': 'exchange'},
            {'name': '方向', 'key': 'direction'},
            {'name': '持仓数量', 'key': 'position'},
            {'name': '昨仓', 'key': 'yd_position'},
            {'name': '冻结', 'key': 'frozen'},
            {'name': '持仓均价', 'key': 'price'},
            {'name': '持仓盈亏', 'key': 'position_profit'},
            {'name': '接口', 'key': 'gateway_name'},
            {'name': '成交的日期', 'key': 'trading_day'}
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



