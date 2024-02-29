# 项目全局变量管理器(这样全局变量就能跨文件使用)
import collections

_global_variable_dict = None


def init_global_variable():
    global _global_variable_dict
    _global_variable_dict = collections.defaultdict(list)


def set_value(key, value):
    _global_variable_dict[key] = value


def get_value(key, default=None):
    try:
        return _global_variable_dict[key]
    except KeyError:
        return default


def get_all_value():
    return _global_variable_dict
