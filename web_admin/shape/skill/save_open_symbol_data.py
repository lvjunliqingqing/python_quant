
import copy
import json
import numpy as np
import pandas as pd
import pymysql
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.utils import jwt_decode_handler
from shape.models.trade_days import TradeDays


@csrf_exempt
def save_open_symbol(request):
    """前端点击交易按钮,后端保存数据到dhtz_open_symbol_data表中"""
    if request.method == 'POST':
        # 由于request.body获取到二进制的数据，最好用decode()解码下。
        received_json_data = json.loads(request.body.decode())
        try:
            token = request.META.get('HTTP_AUTHORIZATION')[4:]
            jwt_decode_handler(token)  # 验证token,有效token,则会抛出异常错误。
        except:
            return JsonResponse({
                "code": -1,
                "msg": "用户未登录或登录时间已过期,请重新登录！"
            })

        try:
            strategy_name = received_json_data['strategy_name']
        except:
            strategy_name = None

        try:
            strategy_args = json.dumps(received_json_data["strategy_args"], ensure_ascii=False)
        except:
            strategy_args = None

        try:
            direction = received_json_data['direction']
        except:
            direction = "LONG"

        try:
            trade_date = received_json_data['trade_date']
        except:
            trade_date = None

        if trade_date and trade_date >= "2020-06-09":
            query_trade = TradeDays().get_the_next_trading_day(trade_date)
        else:
            query_trade = None

        try:
            account_list = received_json_data['account_list']
        except:
            account_list = []

        offset = "OPEN"

        data = received_json_data['data']

        insert_data_list = list()

        if received_json_data["link_table"] == "dhtz_open_symbol_data":
            Model_class = "dhtz_open_symbol_data"
        else:
            Model_class = "dhtz_open_manual_symbol_data"

        # 连接数据库
        conn = pymysql.connect(
            host='192.168.0.250',
            port=3306,
            user='stock',
            passwd='123456',
            db='stock',
            charset='utf8'
        )
        # 获取游标
        cursor = conn.cursor()

        if account_list and data:
            for i in data:
                for account_id in account_list:
                    data_list = []
                    symbol = i["symbol"]
                    exchange = i["exchange"]
                    trade_date = i["trade_date"]
                    if exchange != "CZCE":
                        symbol = symbol.lower()
                    data_list.append(account_id)
                    data_list.append(symbol)
                    data_list.append(exchange)
                    data_list.append(direction)
                    data_list.append(offset)
                    data_list.append(query_trade.trade_date if hasattr(query_trade, "trade_date") else trade_date)
                    data_list.append(strategy_name)
                    data_list.append(strategy_args)
                    insert_data_list.append(copy.deepcopy(data_list))

            columns = ['account_id', 'symbol', 'exchange', 'direction', 'offset', 'trade_date', 'strategy_name','strategy_args']
            df = pd.DataFrame(insert_data_list, columns=columns)
            train_data = np.array(df)
            train_x_list = train_data.tolist()  # list
        else:
            return JsonResponse({
                "code": -1,
                "msg": "前端未传入account_list或data"
            })

        sql = "insert into {}(account_id,symbol,exchange,direction,offset,trade_date,strategy_name,strategy_args) values(%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE account_id=values(account_id)".format(Model_class)

        try:
            ret = cursor.executemany(sql, train_x_list)    # ret=0:数据库已存在,无需插入。ret=1：插入成功,ret=2:更新成功,ret=3：部分插入成功部分更新成功。
        except Exception as e:
            return JsonResponse({
                        "code": -1,
                        "msg": str(e)
                    })

        conn.commit()
        conn.close()

        if not ret:
            return JsonResponse({
                        "code": -1,
                        "msg": "数据在数据库中已存在，无需再插入。"
                    })

        out = {
            'code': 0,
            'msg': 'ok'
        }
        return JsonResponse(out)
