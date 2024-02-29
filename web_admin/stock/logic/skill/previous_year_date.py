import datetime
from dateutil.relativedelta import relativedelta


def previous_year_date(end_date, n):
    """获取距离end_date的n年前的今天日期时间"""
    # 考虑闰年
    d = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    date_str = (d - relativedelta(years=n)).strftime('%Y-%m-%d')
    date_time = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return date_time

def previous_month_date(end_date, n):
    """获取距离end_date的n个月前日期时间"""
    # 考虑闰年
    d = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    date_str = (d - relativedelta(months=n)).strftime('%Y-%m-%d')
    date_time = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return date_time


def The_last_day_of_last_year(end_date, n=1):
    """获取n年前的最后一天"""
    time_rel = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    next_month = 12
    next_day = 31
    next_time = datetime.datetime(time_rel.year - n, next_month, next_day).date()
    return next_time


def n_years_ago_today(end_date, n):
    """获取距离end_date n年的日期"""
    # 考虑闰年
    d = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    date_str = (d - relativedelta(years=n)).strftime('%Y-%m-%d')
    date_time = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    return date_time
