import json
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from stock.models.daily_stock_data import DailyStockData
from stock.models.moth_data import MothData
from stock.models.dbbardata import FuturesData


# Create your views here.
@csrf_exempt
def condition(request):
    """条件选股"""
    pass


@csrf_exempt
def kline_chart(request):
    """
    获取k线图数据
    """
    if request.method == 'POST':
        kline_chart_data = json.loads(request.body.decode())
        symbol = kline_chart_data['symbol']
        exchange = kline_chart_data['exchange']
        sec_type = kline_chart_data['sec_type']

        interval = 'd'
        try:
            cycle = kline_chart_data['cycle']
        except:
            cycle = "day"
        if not cycle:
            cycle = "day"

        if cycle == "day":
            ModeData = FuturesData if sec_type == 'futures' else DailyStockData
        elif cycle == "month":
            ModeData = MothData


        try:
            start_date = kline_chart_data['start_date']
        except:
            start_date = 0
        if not start_date:
            start_date = 0
        try:
            end_date = kline_chart_data['end_date']
        except:
            end_date = 0
        if not end_date:
            end_date = 0

        if end_date == 0 and start_date == 0:
            query_set = ModeData.objects.filter(
                Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(interval=interval)
            ).order_by('datetime')

        elif end_date == 0 and start_date != 0:
            query_set = ModeData.objects.filter(
                Q(datetime__gte=start_date)
                & Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(interval=interval)
            ).order_by('datetime')

        elif end_date != 0 and start_date == 0:
            query_set = ModeData.objects.filter(
                Q(datetime__lte=end_date)
                & Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(interval=interval)
            ).order_by('datetime')

        elif end_date != 0 and start_date != 0:
            query_set = ModeData.objects.filter(
                Q(datetime__gte=start_date)
                & Q(datetime__lte=end_date)
                & Q(symbol=symbol)
                & Q(exchange=exchange)
                & Q(interval=interval)
            ).order_by('datetime')
        data_list = []
        for queryset in query_set:
            data_list.append([queryset.datetime.strftime("%Y-%m-%d"), queryset.open_price, queryset.close_price, queryset.low_price, queryset.high_price, queryset.volume // 100])
        data = {
            "code": 0,
            "msg": "ok",
            "data": data_list

        }

        return JsonResponse(data)



