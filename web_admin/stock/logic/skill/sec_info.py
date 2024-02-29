from stock.models.securities_info import SecuritiesInfo


def get_stock_sec_info(stock_list):
    """ 获取所有股票的交易所、代码、股票名称的信息"""
    if stock_list:
        sec_info_list = stock_list
        vt_symbol_map = SecuritiesInfo().get_stock_display_name(stock_list)
    else:
        vt_symbol_map, sec_info_list = SecuritiesInfo().VtSymbolMapByStock(stock_list)
    return sec_info_list, vt_symbol_map


def get_futures_sec_info(stock_list):
    if stock_list:
        sec_info_list = stock_list
        vt_symbol_map = SecuritiesInfo().get_futures_display_name(stock_list)
    else:
        vt_symbol_map, sec_info_list = SecuritiesInfo().VtSymbolMapByFutures(stock_list)

    return sec_info_list, vt_symbol_map