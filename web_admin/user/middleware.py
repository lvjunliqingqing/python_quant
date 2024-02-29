from collections import Iterable


class ExceptionChangeMiddleware(object):
    """登录异常情况返回数据处理"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'data'):
            if hasattr(response.data, "keys"):
                if "non_field_errors" in response.data.keys():
                    if response.data["non_field_errors"] == ["无法使用提供的认证信息登录。"]:
                        del response.data["non_field_errors"]
                        response.data["code"] = "-1"
                        response.data["msg"] = "账号或密码错误,请重新输入密码和账号登录"
        return response
