
import json
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.utils import jwt_decode_handler

from shape.constant import Exchange
from shape.models.stock_shape_symbol_info import StockShapeSymbolInfoModel
from stock.models.daily_stock_data import DailyStockData
from user.models import User


@csrf_exempt
def stock_new_shape_to_dhtz_open_symbol_data(request):
    """前端点击添加新形态时，后端保存数据到dhtz_stock_shape_symbol_info表中"""
    if request.method == 'POST':
        try:
            token = request.META.get('HTTP_AUTHORIZATION')[4:]
            token_user = jwt_decode_handler(token)
            ser_id = token_user['user_id']  # 获取用户id
            account_id = User.objects.get(id=ser_id).account_id
            if not account_id:
                return JsonResponse({
                    "code": -1,
                    "msg": "失败,请重新登录后再操作"
                })
        except:
            return JsonResponse({
                "code": -1,
                "msg": "失败,请重新登录后再操作"
            })

        received_json_data = json.loads(request.body.decode())
        symbol = received_json_data['symbol']
        direction = received_json_data['direction']
        trade_date = received_json_data['trade_day']
        obj = DailyStockData.objects.filter(
            Q(symbol=symbol)
            & Q(datetime__lte=trade_date)
        ).order_by("-datetime")[0]
        if obj:
            exchange = obj.exchange
            symbol = symbol.upper()
            offset = "OPEN"
            try:
                StockShapeSymbolInfoModel.objects.create(
                    symbol=symbol,
                    exchange=Exchange[exchange].value,
                    direction=direction,
                    offset=offset,
                    trade_date=trade_date,
                    extend=None,
                    open=obj.open_price,
                    close=obj.close_price,
                    high=obj.high_price,
                    low=obj.low_price,
                    zf_rise=round((obj.close_price - obj.open_price) / obj.open_price, 2),
                    shape="new_shape"
                    )
            except Exception as e:
                if "for key 'uni'" in str(e):
                    e = "数据在数据库中已存在，无需再插入。"
                return JsonResponse({
                    "code": -1,
                    "msg": str(e)
                })

            out = {
                'code': 0,
                'msg': 'ok',
                "data": {
                    "symbol": symbol,
                    "exchange": Exchange[exchange].value,
                    "direction": direction,
                    "offset": offset,
                    "trade_date": trade_date,
                    "extend": None,
                    "open": obj.open_price,
                    "close": obj.close_price,
                    "high": obj.high_price,
                    "low": obj.low_price,
                    "zf_rise": round((obj.close_price - obj.open_price) / obj.open_price, 2),
                    "shape": "new_shape"
                }
            }
            return JsonResponse(out)

        else:
            return JsonResponse(
                {
                    'code': -1,
                    'msg': '标的物代码填写错误！'
                }
            )
