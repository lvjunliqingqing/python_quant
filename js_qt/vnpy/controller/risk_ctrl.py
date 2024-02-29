
import pandas as pd
from vnpy.controller.global_variable import set_value, get_value
from vnpy.controller.trade_operation import write_local_log, trade_today_start_time
from vnpy.model.trade_data_model import TradeDataModel
from vnpy.trader.symbol_attr import ContractMarginRatio, ContractMultiplier, FuturesCompanySpread
from vnpy.trader.utility import get_letter_from_symbol, extract_vt_symbol


def risk_ctrl_info(engine, account_id):
    """查询数据库计算总止损,品种持仓数,品种保证金,同时把总最大亏损、各品种持仓手数、各品种保证金,设置到项目全局变量管理器中"""
    trade_data = TradeDataModel().query_all_position_data(account_id)  # 查询所有持仓数据
    df_trade = trade_data_df(trade_data, engine)  # 持仓数据查询集封装成df对象
    loss_total = int(df_trade[df_trade['max_loss'] < 0]['max_loss'].sum())  # 总最大亏损

    symbol_list = df_trade['symbol'].drop_duplicates().values.tolist()  # 持仓品种的所有symbol
    hold_pos_dict = {}  # 各品种持仓的手数
    margin_dict = {}  # 各品种保证金
    for symbol in symbol_list:
        hold_pos = single_symbol_today_hold_pos(df_trade, symbol)
        hold_pos_dict[symbol] = hold_pos
        symbol_used_margin = single_symbol_margin(df_trade, symbol)
        margin_dict[symbol] = symbol_used_margin

    set_value("loss_total", loss_total)
    set_value("symbol_hold_pos", hold_pos_dict)
    set_value("symbol_used_margin", margin_dict)


def trade_data_df(trade_data, engine):
    """持仓数据查询集封装成df对象"""
    trade_list = []
    for data in trade_data:
        s = []
        symbol = data.symbol
        vt_symbol = str(data.symbol + '.' + data.exchange)
        # 计算保证金、合约乘数
        margin_ratio, the_contract_multiplier = get_margin_rate_and_contract_multiplier(symbol, vt_symbol, engine)

        if data.direction == 'SHORT':
            data.un_volume = data.un_volume * -1

        max_loss = (data.loss_price - data.price) * data.un_volume * the_contract_multiplier
        margin = data.price * abs(data.un_volume) * the_contract_multiplier * margin_ratio

        s.append(data.symbol)
        s.append(data.direction)
        s.append(data.price)
        s.append(data.un_volume)
        s.append(data.win_price)
        s.append(data.loss_price)
        s.append(data.trade_date)
        s.append(max_loss)
        s.append(margin)
        trade_list.append(s)
    # 全部持仓的dataframe数据
    df_trade = pd.DataFrame(data=trade_list, columns=['symbol', 'direction', 'price', 'un_volume', 'win_price', 'loss_price', 'trade_date', 'max_loss', 'margin'])
    df_trade['trade_date'] = pd.to_datetime(df_trade['trade_date'])
    return df_trade


def get_margin_rate_and_contract_multiplier(symbol, vt_symbol, engine):
    """获取symbol对应的保证金和合约乘数"""
    symbol_letter = get_letter_from_symbol(symbol)
    the_contract = engine.get_contract(vt_symbol)
    if the_contract:  # 从交易所获取合约
        margin_ratio = the_contract.LongMarginRatio
        the_contract_multiplier = the_contract.size
    else:
        margin_ratio = ContractMarginRatio.get(symbol_letter)  # 保证金比率
        the_contract_multiplier = ContractMultiplier.get(symbol_letter)  # 合约乘数
    margin_ratio += FuturesCompanySpread.get(symbol_letter, 0)  # 增加期货公司增收保证金
    return margin_ratio, the_contract_multiplier


def single_symbol_margin(df_trade, symbol):
    """单品种单日持仓占用的保证金"""
    symbol_df_trade = single_symbol_today_data(df_trade, symbol)
    symbol_used_margin = int(symbol_df_trade['margin'].sum())
    return symbol_used_margin


def single_symbol_today_hold_pos(df_trade, symbol):
    """单品种单日持仓手数"""
    symbol_df_trade = single_symbol_today_data(df_trade, symbol)
    hold_pos_long = abs(symbol_df_trade[symbol_df_trade['un_volume'] > 0]['un_volume'].sum())  # 做多持仓手数
    hold_pos_short = abs(symbol_df_trade[symbol_df_trade['un_volume'] < 0]['un_volume'].sum())  # 多空持仓手数
    hold_pos = hold_pos_long + hold_pos_short  # 总手数
    return int(hold_pos)


def single_symbol_today_data(df_trade, symbol):
    """返回单品种当天交易的dataframe数据"""
    symbol_df_trade = df_trade[df_trade['symbol'] == symbol]
    start_time = trade_today_start_time()
    symbol_df_trade = symbol_df_trade[symbol_df_trade['trade_date'] > start_time]
    return symbol_df_trade


def risk_control_pos(strategy, vt_symbol, engine, open_price, loss_price, max_open_loss_rate, order_ref, balance):
    """风险控制允许开仓的手数"""
    max_hold_limit = 50  # 单品种持仓数据限制
    symbol_margin_rate_limit = 0.1  # 单品占用总资金率限制
    total_loss_rate = 0.2   # 总最大亏损率限制
    symbol_one_loss_rate = 0.01   # 单品种单次开仓亏损率限制
    multiple_max_loss = 1.5  # 单次开仓该品种的最大亏损的1.5倍比开仓价的值不能超过4%
    max_open_loss_rate = max_open_loss_rate  # 单品种1.5倍的开仓最大损失率限制
    symbol, exchange = extract_vt_symbol(vt_symbol)

    if not strategy.account:
        strategy.write_log('还未获取到账户信息，请重新登录再操作')
        return None

    if not get_value('loss_total'):  # 总最大亏损
        risk_ctrl_info(engine, strategy.account.accountid)  # 查询数据库,把总最大亏损、各品种持仓手数、各品种保证金,设置到项目全局变量管理器中

    margin_ratio, the_contract_multiplier = get_margin_rate_and_contract_multiplier(symbol, vt_symbol, engine)  # 获取symbol对应的保证金和合约乘数
    if not margin_ratio or not the_contract_multiplier:
        strategy.write_log(f'未获取到{symbol}的保证金比率和合约乘数，不允许开仓')
        return None

    if not max_open_loss_rate_limit(strategy, symbol, open_price, loss_price, multiple_max_loss, max_open_loss_rate):  # 单品种1.5倍开仓最大损失率的限制
        return None

    open_pos_symbol = single_symbol_open_pos_limit(strategy, symbol, max_hold_limit)  # 单品种开仓手数限制

    open_pos_margin = single_symbol_margin_limit(strategy, symbol, symbol_margin_rate_limit, open_price, the_contract_multiplier, margin_ratio)  # 单品种保证金占用总资金率限制
                                                 
    open_pos_max_loss = total_loss_rate_limit(strategy, symbol, total_loss_rate, open_price, loss_price, the_contract_multiplier)  # 总资金亏损率限制

    open_pos_symbol_single = single_loss_available_limit(strategy, symbol, symbol_one_loss_rate, open_price, loss_price, the_contract_multiplier, balance)  # 单品种单次开仓亏损率限制

    real_open_pos = min(open_pos_symbol, open_pos_margin, open_pos_max_loss, open_pos_symbol_single)  # 各种限制允许开仓的手数中取最小值

    if not real_open_pos:
        return None

    if real_open_pos % 2:  # 判断是否为双数,为了取双数。平半仓时算数方便整除
        real_open_pos -= 1

    if real_open_pos:
        # 累计每一次开仓的总止损、品种持仓、品种占用保证金，更新项目全局变量管理器中的总止损、品种持仓、品种占用的保证金
        update_global_value(symbol, loss_price, open_price, the_contract_multiplier, margin_ratio, real_open_pos)
        if order_ref:  # 全局变量中保存这次委托保证金、止损等,防止委托被拒绝或撤销,好重新计算风控控制相关参数。
            set_value(str(order_ref), (symbol, loss_price, open_price, vt_symbol, engine, the_contract_multiplier, margin_ratio))
        return real_open_pos
    else:
        strategy.write_log(f'{symbol}, 可开仓0手')
        return None


def update_global_value(symbol, loss_price, open_price, the_contract_multiplier, margin_ratio, real_open_pos):
    """每次允许开仓后,要累加计算总止损,品种持仓数,品种占用的保证金,同时更新项目全局变量管理器中的总止损、品种持仓、品种占用的保证金"""
    loss_symbol = abs(loss_price - open_price) * the_contract_multiplier * real_open_pos  # 计算品种本次止损
    loss_total = get_value('loss_total') - loss_symbol  # 总止损累加
    hold_pos_dict = get_value('symbol_hold_pos')
    hold_pos_dict[symbol] = hold_pos_dict.get(symbol, 0) + real_open_pos  # 持仓手数累加
    margin_dict = get_value('symbol_used_margin')
    margin_dict[symbol] = margin_dict.get(symbol, 0) + (open_price * the_contract_multiplier * margin_ratio * real_open_pos)  # 品种占用保证金累加
    set_value("loss_total", loss_total)  # 全局变量中更新总止损
    set_value("symbol_hold_pos", hold_pos_dict)   # 全局变量中更新品种持仓
    set_value("symbol_used_margin", margin_dict)  # 全局变量中更新品种占用的保证金


def single_symbol_open_pos_limit(strategy, symbol, max_hold_limit):
    """单品种的开仓手数限制,返回可开仓手数"""
    hold_pos = get_value('symbol_hold_pos').get(symbol, 0)
    if hold_pos < max_hold_limit:
        symbol_open_pos = max_hold_limit - hold_pos
        write_local_log(strategy.strategy_name, f'{symbol}开仓手数限制为：{max_hold_limit} ，已持仓：{hold_pos} ，可开仓：{symbol_open_pos}')
        return symbol_open_pos
    else:
        write_local_log(strategy.strategy_name, f'{symbol}开仓手数限制为：{max_hold_limit} ， 已持仓：{hold_pos} ，不可开仓')
        strategy.write_log(f'{symbol}开仓手数限制为：{max_hold_limit} ， 已持仓：{hold_pos} ，不可开仓')
        return 0


def single_symbol_margin_limit(strategy, symbol, symbol_margin_rate_limit, open_price, the_contract_multiplier, margin_ratio):
    """单品种保证金占用总资金限制,返回可开仓手数"""
    # 单品种已使用的保证金
    used_margin = get_value('symbol_used_margin').get(symbol, 0)
    # 单品种剩余可用保证金
    available_margin = min(strategy.account.balance * symbol_margin_rate_limit - used_margin, strategy.account.available)
    # 计算可开仓的手数
    open_pos = int(available_margin / (open_price * the_contract_multiplier * margin_ratio))
    if open_pos > 0:
        write_local_log(strategy.strategy_name, f'{symbol}, 单品种已使用保证金：{used_margin}，可用保证金：{available_margin}，可开仓：{open_pos}，单品种保证金占用总资金不超{symbol_margin_rate_limit * 100}%')
        return open_pos
    else:
        write_local_log(strategy.strategy_name, f'{symbol}, 单品种已使用保证金：{used_margin}，可用保证金：{available_margin}，不可开仓，单品种保证金占用总资金不超{symbol_margin_rate_limit * 100}%')
        strategy.write_log(f'{symbol}, 单品种已使用保证金：{used_margin}，可用保证金：{available_margin}，不可开仓，单品种保证金占用总资金不超10%')
        return 0


def total_loss_rate_limit(strategy, symbol, total_loss_rate, open_price, loss_price, the_contract_multiplier):
    """总资金亏损率限制,返回可开仓手数"""
    loss_total = get_value('loss_total')  # 总最大亏损
    loss_available = strategy.account.balance * total_loss_rate - abs(loss_total)  # 剩余可用最大亏损
    # 计算可开仓的手数
    open_pos_max_loss = int(loss_available / (abs(loss_price - open_price) * the_contract_multiplier))
    if open_pos_max_loss > 0:
        write_local_log(strategy.strategy_name, f'{symbol}, 总最大亏损为：{loss_total}，剩余可用最大亏损：{loss_available}，可开仓：{open_pos_max_loss}, 总资金亏损比率不超过{total_loss_rate * 100}%')
        return open_pos_max_loss
    else:
        write_local_log(strategy.strategy_name, f'{symbol}, 总最大亏损为：{loss_total}，剩余可用最大亏损：{loss_available}，不可开仓：{open_pos_max_loss}, 总资金亏损比率不超过{total_loss_rate * 100}%')
        strategy.write_log(f'{symbol}, 总最大亏损为：{loss_total}，剩余可用最大亏损：{loss_available}，不可开仓：{open_pos_max_loss}, 总资金亏损比率不超过{total_loss_rate * 100}%')
        return 0


def single_loss_available_limit(strategy, symbol, symbol_one_loss_rate, open_price, loss_price, the_contract_multiplier, balance):
    """单品种单次开仓亏损率限制"""

    # 单品种单次开仓可用亏损资金计算
    if balance:
        symbol_one_available = strategy.account.balance * symbol_one_loss_rate
    else:
        symbol_one_available = strategy.account.available * symbol_one_loss_rate

    open_pos_symbol_single = int(symbol_one_available / (abs(loss_price - open_price) * the_contract_multiplier))  # 计算允许开仓的手数(int取整时,小于1的浮点数统统为0)

    if open_pos_symbol_single > 0:
        write_local_log(strategy.strategy_name, f'{symbol}, 单次开仓可用亏损资金:{symbol_one_available}, 可开仓：{open_pos_symbol_single}, 单次开仓亏损比率不超过1%')
        return open_pos_symbol_single
    else:
        write_local_log(strategy.strategy_name,f'{symbol}, 单次开仓可用亏损资金:{symbol_one_available}, 不可开仓：{open_pos_symbol_single}, 单次开仓亏损比率不超过1%')
        strategy.write_log(f'{symbol}, 单次开仓可用亏损资金:{symbol_one_available}, 不可开仓：{open_pos_symbol_single}, 单次开仓亏损比率不超过1%')
        return 0


def max_open_loss_rate_limit(strategy, symbol, open_price, loss_price, multiple_max_loss, max_open_loss_rate):
    """
    单品种1.5倍开仓最大损失率的限制:
        open_price:并不是真实的开仓价,而是达到开仓条件时tick.last_price(理论上的开仓价)
    """
    # 1.5倍的开仓最大损失率要在指定范围内(max_open_loss_rate)才允许开仓(单次单品种)
    loss_open_rate = (abs(loss_price - open_price) * multiple_max_loss) / open_price
    if loss_open_rate < max_open_loss_rate:
        write_local_log(strategy.strategy_name, f'单次,品种{symbol}的1.5倍的开仓最大损失率:{loss_open_rate}, 可开仓，未超过{max_open_loss_rate * 100}%的规定')
        return True
    else:
        strategy.write_log(f'{symbol}, 单次的1.5倍开仓最大损失率:{loss_open_rate}, 已超过{max_open_loss_rate * 100}%的规定,不允许开仓')
        write_local_log(strategy.strategy_name, f'单次,品种{symbol}的1.5倍的开仓最大损失率:{loss_open_rate}, 不可开仓，已超过{max_open_loss_rate * 100}%的规定')
        return False


def global_value_minus_the(order_ref, real_open_pos):
    """当开仓委托单被拒单或已取消时,总止损,品种持仓数,品种占用的保证金应减去这次的"""
    if get_value(order_ref):
        symbol, loss_price, open_price, vt_symbol, engine, the_contract_multiplier, margin_ratio = get_value(order_ref)

        loss_symbol = abs(loss_price - open_price) * the_contract_multiplier * real_open_pos  # 计算品种本次止损
        loss_total = get_value('loss_total') + loss_symbol  # 总止损累减去本次撤销单的(总止损为负数,所以减去就为+号)
        hold_pos_dict = get_value('symbol_hold_pos')
        hold_pos_dict[symbol] = hold_pos_dict.get(symbol, 0) - real_open_pos  # 持仓手数减去本次撤销单的
        margin_dict = get_value('symbol_used_margin')
        margin_dict[symbol] = margin_dict.get(symbol, 0) - (open_price * the_contract_multiplier * margin_ratio * real_open_pos)  # 品种占用保证金减去本次撤销单的
        set_value("loss_total", loss_total)  # 全局变量中更新总止损
        set_value("symbol_hold_pos", hold_pos_dict)   # 全局变量中更新品种持仓
        set_value("symbol_used_margin", margin_dict)  # 全局变量中更新品种占用的保证金