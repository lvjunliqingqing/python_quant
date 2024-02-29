import datetime


def get_yesterday_or_today():
    """
    返回昨天或今天的日期
    """
    time = datetime.datetime.now().strftime("%H:%M")
    today = datetime.datetime.now()
    n_day = datetime.timedelta(days=-1)
    today_date = str(today.strftime("%Y-%m-%d"))
    yesterday_date = str((today + n_day).strftime("%Y-%m-%d"))
    if time > "15:22":
        return today_date
    else:
        return yesterday_date
