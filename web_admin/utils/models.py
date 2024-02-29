from django.db import models


class BaseModel(models.Model):
    """为模型类补充字段"""
    # atime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    # utime = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        # 指明仅仅当做一个类使用,而不是模型类，用于继承使用，数据库迁移时不会创建BaseModel的表。
        abstract = True
