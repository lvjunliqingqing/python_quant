
import os
import platform
import string
import time
from datetime import datetime, time as tm, timedelta
from vnpy.model.order_data_model import OrderDataModel
from vnpy.model.trade_data_model import TradeDataModel, TradeDayModel

num = 0


def get_order_ref_value():
    """
    生成order_ref
    """
    global num
    num += 1
    order_ref_value = str(int(round(time.time() * 100, 0)) + num)
    return order_ref_value


def write_local_log(strategy_name, context):
    filename = f"{strategy_name}_{datetime.now().date()}.txt"
    sys = platform.system()
    if sys == "Windows":
        disk_list = []
        for c in string.ascii_uppercase:
            disk = c + ':'
            if os.path.isdir(disk):
                disk_list.append(disk)
        path = os.path.join(disk_list[1], f"/futures_log/{strategy_name}")
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + "/" + filename, "a") as f:
            f.write("\n%s:%s\n" % (datetime.now(), context))

    elif sys == "Linux":
        path = f"/data/futures_log/{strategy_name}"
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + "/" + filename, "a") as f:
            f.write("\n%s:%s\n" % (datetime.now(), context))


def whether_open_today(strategy_name, strategy_class_name, symbol, account_id):
    """判断今天是否已经开过仓"""
    trade_start_time = trade_today_start_time()
    open_position_data = TradeDataModel().select().where(
        (TradeDataModel.symbol == symbol)
        & (TradeDataModel.trade_date > trade_start_time)
        & (TradeDataModel.account_id == account_id)
        & (TradeDataModel.offset == 'OPEN')
        & (TradeDataModel.strategy_name == strategy_name)
        & (TradeDataModel.strategy_class_name == strategy_class_name)
        & (TradeDataModel.gateway_name == 'CTP')
    )
    if open_position_data:
        del open_position_data
        return True
    else:
        del open_position_data
        return False


def trade_today_start_time():
    """
    返回今日或者上一交易日开始时间
        当前小时 > 20时,返回当前日期的20时。
        当前小时 <= 20时,返回上一个交易日的20时。
    """
    time_now = datetime.now()
    if time_now.time() > tm(hour=20):
        trade_start_time = time_now.replace(hour=20)
    else:
        start_date_trade = (datetime.now() - timedelta(days=30)).date()
        end_date_trade = datetime.now().date()
        trade_date_obj = TradeDayModel().select().where(
            (TradeDayModel.trade_date > start_date_trade)
            & (TradeDayModel.trade_date <= end_date_trade)
        )
        if len(trade_date_obj) < 2:
            return None
        trade_date_list = []
        for tra_obj in trade_date_obj:
            trade_date_list.append(tra_obj.trade_date)
        time_yesterday = sorted(trade_date_list)[-2]
        trade_start_time = datetime(year=time_yesterday.year, month=time_yesterday.month, day=time_yesterday.day, hour=20)

    return trade_start_time


def current_trade_date(trade_datetime):
    """根据传进来datetime,如果是夜盘返回datetime后一天的日期，否则返回当天的日期"""
    start_date = (trade_datetime + timedelta(hours=5)).date()
    end_date = start_date + timedelta(days=30)
    trade_date_obj = TradeDayModel().select().where(
        (TradeDayModel.trade_date >= start_date)
        & (TradeDayModel.trade_date <= end_date)
    )

    trade_date_list = []
    if trade_date_obj:
        for tra_obj in trade_date_obj:
            trade_date_list.append(tra_obj.trade_date)
        trade_date_list = sorted(trade_date_list)[0]
    return trade_date_list


def save_strategy_order(order, strategy_name, strategy_class_name, account):
    """委托单保存到数据库"""
    order.account_id = account.accountid
    order.balance = account.balance
    order.strategy_name = strategy_name
    order.strategy_class_name = strategy_class_name
    order.order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order.strategy_author = 'auto'

    if order.offset.name == "NONE":
        write_local_log(strategy_name, f"{order.symbol}，order.offset.name=None")
        return

    sql = OrderDataModel().save_order_data(order)  # 保存订单
    if order.offset.name == 'OPEN':
        if sql:
            write_local_log(strategy_name, f"{order.symbol},开仓-委托单-保存成功，订单数据：{order}")
        else:
            write_local_log(strategy_name, f"{order.symbol}开仓-委托单保-存失败，订单数据：{order}")
    else:
        if sql:
            write_local_log(strategy_name, f"{order.symbol},平仓-委托单-保存成功，订单数据：{order}")
        else:
            write_local_log(strategy_name, f"{order.symbol},平仓-委托单-保存失败，订单数据：{order}")


def strategy_update_trade(trade, order_id_map, order_ref_map, strategy_name, strategy_class_name, account):
    """更新或保存成交单"""
    trade.account_id = account.accountid
    trade.balance = account.balance
    trade.strategy_name = strategy_name
    trade.strategy_class_name = strategy_class_name
    if trade.offset.name == 'OPEN':
        trade_own = TradeDataModel().get_or_none(orderid=trade.orderid)
        if trade_own:  # 一次委托分多笔成交
            volume = trade_own.volume + trade.volume
            price = (trade_own.price * trade_own.volume + trade.price * trade.volume) / volume
            un_volume = trade_own.un_volume + trade.volume
            sql = TradeDataModel().update(volume=volume, price=price, un_volume=un_volume).where(TradeDataModel.orderid == trade.orderid).execute()
            if sql:
                write_local_log(strategy_name, f"开仓-成交单数据-更新成功，orderid:{trade.orderid}, 手数：{trade.volume}，未平：{un_volume} 成交价：{trade.price}")
            else:
                write_local_log(strategy_name, f"开仓-成交单数据-更新失败，orderid：{trade.orderid}")
        else:
            trade = strategy_update_trade_date(trade)
            sql = TradeDataModel().save_trade_data(trade)
            if sql:
                write_local_log(strategy_name, f"{trade.symbol},开仓-成交单数据-保存成功，orderid:{trade.orderid},已开仓成交, 手数：{trade.volume}， 成交价：{trade.price}")

            else:
                write_local_log(strategy_name, f"{trade.symbol},开仓-成交数据-保存失败，orderid：{trade.order_ref}")
    else:
        if order_id_map.get(str(trade.order_ref)):
            # 先减少持仓量
            orderid_tem = order_id_map[str(trade.order_ref)]
            TradeDataModel().update(un_volume=TradeDataModel.un_volume - trade.volume
                                    ).where(
                TradeDataModel.orderid == orderid_tem
            ).execute()

            trade.order_ref = order_ref_map[str(trade.order_ref)]
            trade.p_orderid = orderid_tem
            trade.orderid = trade.orderid
            trade = strategy_update_trade_date(trade)
            # 再保存平仓成交单
            sql = TradeDataModel().save_trade_data(trade)
            if sql:
                write_local_log(strategy_name, f"{trade.symbol},平仓-成交信息-保存成功，orderid:{trade.orderid}已平成交, 手数：{trade.volume}")
            else:
                write_local_log(strategy_name, f"{trade.symbol},平仓-成交信息-保存失败，orderid：{trade.orderid}")
        else:
            write_local_log(strategy_name, f"{trade.symbol},order_id_map出错，平仓时未能执行减仓操作")
            print("order_id_map出错，平仓时未能执行减仓操作")


def strategy_update_trade_date(trade):
    """给trade数据添加trade_date"""
    cul_date = datetime.now() + timedelta(hours=1)
    trade_date = datetime.strptime(trade.trade_date, '%Y-%m-%d %H:%M:%S')
    if trade_date > cul_date:
        cul_date_forward = datetime.now() - timedelta(hours=1)
        year = cul_date_forward.year
        month = cul_date_forward.month
        day = cul_date_forward.day
        trade_date = trade_date.replace(year=year, month=month, day=day)
    trade.trade_date = str(trade_date)
    return trade


def trade_time_judge(tick, strategy):
    """交易时间判断"""
    dt_time = tick.datetime.time()
    am_start_time_first = datetime.strptime('9:00:00', '%H:%M:%S').time()
    am_end_time_first = datetime.strptime('10:15:00', '%H:%M:%S').time()
    am_start_time_second = datetime.strptime('10:30:00', '%H:%M:%S').time()
    am_end_time_second = datetime.strptime('11:30:00', '%H:%M:%S').time()
    pm_start_time = datetime.strptime('13:30:00', '%H:%M:%S').time()
    pm_end_time = datetime.strptime('15:00:00', '%H:%M:%S').time()
    eve_start_time = datetime.strptime('21:00:00', '%H:%M:%S').time()
    eve_end_time = datetime.strptime('2:30:00', '%H:%M:%S').time()

    if am_start_time_first <= dt_time < am_end_time_first:
        return True
    elif am_start_time_second <= dt_time < am_end_time_second:
        return True
    elif pm_start_time <= dt_time < pm_end_time:
        return True
    elif dt_time < eve_end_time:
        return True
    elif dt_time >= eve_start_time:
        return True
    else:
        strategy.write_log(f'{tick.symbol, tick.datetime},不在交易时间内')
        return False