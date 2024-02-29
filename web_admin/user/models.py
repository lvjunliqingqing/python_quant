from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.models import BaseModel


class User(AbstractUser):
    """
    自定义用户模型类
        继承Django提供的django.contrib.auth.models.AbstractUser模型类
        添加django默认用户模型类中没有的字段。
    """
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    account_id = models.CharField(max_length=20, verbose_name="交易账户id")
    avatar = models.CharField(max_length=1000, verbose_name="头像")
    class Meta:
        db_table = 'js_tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class DhtzTradeAccountInfo(BaseModel):
    account_id = models.CharField(max_length=50, verbose_name="交易账户id")
    username = models.CharField(max_length=30, verbose_name="关联username")
    account_type = models.CharField(max_length=255, verbose_name="账户类型: 股票 期货 外汇等")
    status = models.BigIntegerField(verbose_name="状态")
    commpany = models.CharField(max_length=255, verbose_name="开户公司名称")

    class Meta:
        db_table = 'js_trade_account_info'
        verbose_name = '用户名关联交易账号表'
        verbose_name_plural = verbose_name