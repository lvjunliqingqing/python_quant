from django.db import models
from django.db.models import Q

from utils.models import BaseModel


class TradeDays(BaseModel):
    trade_date = models.DateField(null=True)

    class Meta:
        db_table = "trade_days"
        verbose_name = "交易日信息表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s" % self.trade_date

    def get_the_next_trading_day(self, yesterday_trade_date):
            try:
                query_set = TradeDays.objects.filter(Q(trade_date__gt=yesterday_trade_date)).order_by("trade_date")[0]
                return query_set
            except:
                return None

