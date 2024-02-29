from rest_framework import serializers

from stock.models.daily_stock_data import DailyStockData


class ConditionSerializers(serializers.ModelSerializer):
    """
    选股序列化器
    """
    class Meta(object):
        # 关联的模型类
        model = DailyStockData
        fields = '__all__'
        read_only_fields = ('id',)
