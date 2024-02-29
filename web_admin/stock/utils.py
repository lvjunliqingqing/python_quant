import json
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from stock.models.securities_info import SecuritiesInfo

def last_day_of_month(any_day):
    """
    获取获得一个月中的最后一天
    :param any_day: 任意日期
    :return: string
    """

    now = datetime.strptime(str(any_day), "%Y-%m-%d %H:%M:%S")
    this_month_end = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

    return this_month_end.strftime("%Y-%m-%d")

    # next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
    # return next_month - timedelta(days=next_month.day)


def Choose_condition(request):
    """
    获取前端发送过来的条件选股的数据
    """
    if request.method == 'POST':
        # 由于request.body获取到二进制的数据，最好用decode()解码下。
        received_json_data = json.loads(request.body.decode())
        condition = received_json_data['condition']
        dynamicParams = received_json_data['dynamicParams']
        end_date = received_json_data['end_date']
        cycle = received_json_data['cycle']
        # 存储选股条件
        cond = defaultdict(list)
        days_list = []
        for idx, con in enumerate(condition):
            days = int(dynamicParams[idx]['value'])
            days_list.append(days)
            cond[con] = days
        days = max(days_list)

        if cycle == 'day':
            DataTable = DailyStockData
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

        elif cycle == 'month':
            DataTable = MothData
            end_date = last_day_of_month(datetime.strptime(end_date, "%Y-%m-%d"))
            start_date = end_date - relativedelta(months=days)

        # 查询出所有非ST股票SecuritiesInfo数据
        sec_info = SecuritiesInfo.objects.filter(Q(sec_type='stock')
                                                 & Q(end_date__gte=datetime.now().today())
                                                 ).exclude(Q(display_name__icontains='ST'))
        # 存储所有股票的{symbol、exchange、display_name}
        sec_info_list = []
        # 存储所有股票的{display_name}
        vt_symbol_map = {}
        for sec in sec_info:
            vt_symbol = sec.symbol.split('.')
            symbol = vt_symbol[0]
            exchange = vt_symbol[1]
            sec_info_list.append(
                {
                    'symbol': symbol,
                    'exchange': exchange,
                    'display_name': sec.display_name
                }
            )
            vt_symbol_map[sec.symbol] = sec.display_name
    return sec_info_list, DataTable, start_date, end_date, vt_symbol_map, cond