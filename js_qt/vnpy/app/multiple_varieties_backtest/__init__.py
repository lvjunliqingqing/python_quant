from pathlib import Path
from vnpy.trader.app import BaseApp
from .engine import APP_NAME, MultipleVarietiesBackTestEngine


class MultipleVarietiesBackTestApp(BaseApp):
    """多品种合约app"""
    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "多品种回测"
    engine_class = MultipleVarietiesBackTestEngine
    widget_name = "MultipleVarietiesBackTestManager"
    icon_name = "multiple_varieties_backtest.ico"
