
from django.urls import path
from shape.controller import common
from shape.skill import save_open_symbol_data, get_position_info, get_dhtz_strategy_desc, get_dhtz_open_symbol_data, \
    audit, new_shape_to_dhtz_open_symbol_data, get_dhtz_strategy_desc_by_symbol, audit_manual_info, \
    update_dhtz_open_manual_symbol_data, stock_audit, stock_save_open_symbol_data, \
    stock_new_shape_to_dhtz_open_symbol_data, get_dhtz_stock_strategy_desc_by_symbol, get_dhtz_stock_strategy_desc, \
    get_stock_position_info, get_dhtz_stock_open_symbol_data, stock_audit_manual_info, \
    stock_update_dhtz_open_manual_symbol_data

urlpatterns = [
    path(r'info', common.shape_symbo_info),

    path(r'saveopen', save_open_symbol_data.save_open_symbol),
    path(r'stock_saveopen', stock_save_open_symbol_data.stock_save_open_symbol),  # ok

    path(r'new_shape', new_shape_to_dhtz_open_symbol_data.new_shape_to_dhtz_open_symbol_data),
    path(r'stock_new_shape', stock_new_shape_to_dhtz_open_symbol_data.stock_new_shape_to_dhtz_open_symbol_data),  # ok

    path(r'get_position', get_position_info.get_position_info),
    path(r'get_stock_position', get_stock_position_info.get_stock_position_info),  # ok

    path(r'get_dhtz_strategy_desc', get_dhtz_strategy_desc.get_dhtz_strategy_desc),
    path(r'get_dhtz_stock_strategy_desc', get_dhtz_stock_strategy_desc.get_dhtz_stock_strategy_desc),  # ok

    path(r'get_dhtz_strategy_desc_by_symbol', get_dhtz_strategy_desc_by_symbol.get_dhtz_strategy_desc_by_symbol),
    path(r'get_dhtz_stock_strategy_desc_by_symbol', get_dhtz_stock_strategy_desc_by_symbol.get_dhtz_stock_strategy_desc_by_symbol),  # 0k

    path(r'get_dhtz_open_symbol_data', get_dhtz_open_symbol_data.get_dhtz_open_symbol_data),
    path(r'get_dhtz_stock_open_symbol_data', get_dhtz_stock_open_symbol_data.get_dhtz_stock_open_symbol_data),  # ok

    path(r'audit_manual/get_dhtz_open_symbol_data', audit_manual_info.audit_manual_info),
    path(r'audit_manual/get_dhtz_stock_open_symbol_data', stock_audit_manual_info.stock_audit_manual_info),  # ok

    path(r'audit', audit.audit),
    path(r'stock_audit', stock_audit.stock_audit),  # ok

    path(r'audit_manual', update_dhtz_open_manual_symbol_data.update_dhtz_open_manual_symbol_data),
    path(r'stock_audit_manual', stock_update_dhtz_open_manual_symbol_data.stock_update_dhtz_open_manual_symbol_data),
]


