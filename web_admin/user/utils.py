import re
from django.contrib.auth.backends import ModelBackend
from rest_framework import serializers

from user.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    data = {
        'token': token,
        'username': user.username,
        'account_id': user.account_id
    }
    return {
        "code": 0,
        "data": data,
        "msg": "登录成功"
    }


def get_user_by_account(account):
    """
    根据帐号获取user对象
    """
    try:
        if re.match('^1[3-9]\d{9}$', account):
            # 帐号为手机号
            user = User.objects.get(mobile=account)
        else:
            # 帐号为用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义用户名或手机号认证
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = get_user_by_account(username)
            # 调用User对象的check_password方法检查密码是否正确
            if user is not None and user.check_password(password):
                return user
        except Exception as e:
            # # 异常信息UserProfile matching query does not exist
            raise serializers.ValidationError({'username or password': '账户或密码输入错误'})


