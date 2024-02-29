from rest_framework import serializers

from user.models import User


class UserSerializer(serializers.ModelSerializer):
    """用户类模型序列化器"""

    class Meta(object):
        # 关联的模型类
        model = User
        fields = '__all__'
