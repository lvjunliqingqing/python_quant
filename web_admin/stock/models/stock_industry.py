from django.db import models
from utils.models import BaseModel


class StockIndustryMode(BaseModel):
    """
    股票所属行业
    """
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=100, null=False)
    industry = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'stock_industry'
        verbose_name = '股票所属行业表'
