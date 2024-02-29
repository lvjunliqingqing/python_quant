from django.db import models
from utils.models import BaseModel
from django.db.models import Q
from datetime import datetime
from pandas import DataFrame


class SecuritiesInfo(BaseModel):
    """
    股票日k线模型类
    """
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=255, null=False)
    display_name = models.CharField(max_length=255, null=False)
    name_code = models.CharField(max_length=255, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    sec_type = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'securities_info'
        verbose_name = '证券信息'

    def GetStockData(self, stock_list):
        """
        查询所有股票的代码、交易所的信息:
            第一个选股条件到就根据条件查询所有,第二个选股条件在第一次查询继承上中再查询。以此类推
        """
        stock_list = DataFrame(stock_list)
        if len(stock_list):
            # list_str = ','.join(stock_list['id'].values.tolist())
            list_str = stock_list['id'].values.tolist()
            # print(type(list_str))
            sec_info = SecuritiesInfo.objects.filter(Q(sec_type='stock')
                                                     & Q(id__in=list_str)
                                                     & Q(end_date__gte=datetime.now().today())
                                                     ).exclude(Q(display_name__icontains='ST'))
        else:
            sec_info = SecuritiesInfo.objects.filter(Q(sec_type='stock')
                                                     & Q(end_date__gte=datetime.now().today())
                                                     ).exclude(Q(display_name__icontains='ST'))
        return sec_info



    def GetFuturesData(self, stock_list):
        """
        查询所有期货的代码、交易所的信息:
            第一个选股条件到就根据条件查询所有,第二个选股条件在第一次查询继承上中再查询。以此类推
        """
        stock_list = DataFrame(stock_list)
        if len(stock_list):
            # list_str = ','.join(stock_list['id'].values.tolist())
            list_str = stock_list['id'].values.tolist()
            # print(type(list_str))
            sec_info = SecuritiesInfo.objects.filter(Q(sec_type='futures')
                                                     & Q(id__in=list_str)
                                                     & Q(end_date__gte=datetime.now().today())
                                                     & Q(symbol__iregex=".*(9999).*")
                                                     ).exclude(Q(display_name__icontains='ST'))
        else:
            sec_info = SecuritiesInfo.objects.filter(Q(sec_type='futures')
                                                     & Q(end_date__gte=datetime.now().today())
                                                     & Q(symbol__iregex=".*(9999).*")
                                                     ).exclude(Q(display_name__icontains='ST'))
        return sec_info


    def VtSymbolMapByStock(self, stock_list):
        """获取所有股票的交易所、代码、股票名称的信息"""
        vt_map = {}
        # 查询数据库获取所有股票的代码和交易所的信息
        obj = self.GetStockData(stock_list)
        sec_list = []
        for row in obj:
            vt_symbol = row.symbol.split('.')
            symbol = vt_symbol[0]
            exchange = vt_symbol[1]
            vt_map[f"{symbol}.{exchange}"] = row.display_name
            sec_list.append({
                'id': str(row.id),
                'symbol': symbol,
                'exchange': exchange
            })
        return vt_map, sec_list


    def get_stock_display_name(self, stock_list):
        vt_map = {}
        stock_list = DataFrame(stock_list)
        list_str = stock_list['id'].values.tolist()
        obj = SecuritiesInfo.objects.filter(Q(sec_type='stock')
                                            & Q(id__in=list_str)
                                            & Q(end_date__gte=datetime.now().today())
                                            ).exclude(Q(display_name__icontains='ST'))
        for row in obj:
            vt_symbol = row.symbol.split('.')
            symbol = vt_symbol[0]
            exchange = vt_symbol[1]
            vt_map[f"{symbol}.{exchange}"] = row.display_name
        return vt_map


    def VtSymbolMapByFutures(self, stock_list):
        """获取所有股票的交易所、代码、股票名称的信息"""
        vt_map = {}
        # 查询数据库获取所有股票的代码和交易所的信息
        obj = self.GetFuturesData(stock_list)
        sec_list = []
        for row in obj:
            vt_symbol = row.symbol.split('.')
            symbol = vt_symbol[0]
            exchange = vt_symbol[1]
            vt_map[f"{symbol}.{exchange}"] = row.display_name
            sec_list.append({
                'id': str(row.id),
                'symbol': symbol,
                'exchange': exchange
            })
        return vt_map, sec_list


    def get_futures_display_name(self, stock_list):
        vt_map = {}
        stock_list = DataFrame(stock_list)
        list_str = stock_list['id'].values.tolist()
        obj = SecuritiesInfo.objects.filter(Q(sec_type='futures')
                                            & Q(id__in=list_str)
                                            & Q(end_date__gte=datetime.now().today())
                                            & Q(symbol__iregex=".*(9999).*")
                                            ).exclude(Q(display_name__icontains='ST'))
        for row in obj:
            vt_symbol = row.symbol.split('.')
            symbol = vt_symbol[0]
            exchange = vt_symbol[1]
            vt_map[f"{symbol}.{exchange}"] = row.display_name
        return vt_map