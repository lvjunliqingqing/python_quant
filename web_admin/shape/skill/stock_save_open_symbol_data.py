
import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.utils import jwt_decode_handler
from shape.constant import Exchange
from shape.models.dhtz_stock_open_manual_symbol_data import DhtzStockOpenManualSymbolDataModel
from shape.models.stock_open_symbol_data import StockOpenSymbolDataModel
from shape.models.trade_days import TradeDays
from user.models import User


@csrf_exempt
def stock_save_open_symbol(request):
    """前端点击交易按钮,后端保存数据到dhtz_open_symbol_data表中"""
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body.decode())
            symbol = received_json_data['symbol']
            exchange = received_json_data['exchange']
            direction = received_json_data['direction']
            offset = received_json_data['offset']
            trade_date = received_json_data['trade_date']
            strategy_name = received_json_data['strategy_name']

            token = request.META.get('HTTP_AUTHORIZATION')[4:]
            token_user = jwt_decode_handler(token)
            ser_id = token_user['user_id']  # 获取用户id
            account_id = User.objects.get(id=ser_id).account_id
        except:
            return JsonResponse({
                "code": -1,
                "msg": "失败,请重新登录后再操作"
            })

        if trade_date >= "2020-06-09":
            query_trade = TradeDays().get_the_next_trading_day(trade_date)
        else:
            query_trade = None

        try:
            strategy_args = json.dumps(received_json_data["strategy_args"], ensure_ascii=False)
        except:
            strategy_args = None

        if received_json_data["link_table"] == "dhtz_stock_open_symbol_data":
            try:
                StockOpenSymbolDataModel.objects.create(
                    account_id=account_id,
                    symbol=symbol,
                    exchange=Exchange[exchange].value,
                    direction=direction,
                    offset=offset,
                    trade_date=query_trade.trade_date if hasattr(query_trade, "trade_date") else trade_date,
                    strategy_name=strategy_name,
                    strategy_args=strategy_args,
                    audit_status=1,
                    audit_time=datetime.datetime.now()
                )
            except Exception as e:
                if e:
                    if "for key 'uni'" in str(e):
                        e = "数据在数据库中已存在，无需再插入。"
                    return JsonResponse({
                        "code": -1,
                        "msg": str(e)
                    })
        else:
            try:
                DhtzStockOpenManualSymbolDataModel.objects.create(
                        account_id=account_id,
                        symbol=symbol,
                        exchange=Exchange[exchange].value,
                        direction=direction,
                        offset=offset,
                        trade_date=query_trade.trade_date if hasattr(query_trade, "trade_date") else trade_date,
                        strategy_name=strategy_name,
                        strategy_args=strategy_args,
                        audit_status=1,
                        audit_time=datetime.datetime.now()
                )
            except Exception as e:
                if e:
                    if "for key 'uni'" in str(e):
                        e = "数据在数据库中已存在，无需再插入。"
                    return JsonResponse({
                        "code": -1,
                        "msg": str(e)
                    })

        out = {
            'code': 0,
            'msg': 'ok'
        }
        return JsonResponse(out)
