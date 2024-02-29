from pathlib import Path

from vnpy.trader.app import BaseApp

from .engine import PortfolioEngine, APP_NAME


class PortfolioManagerApp(BaseApp):
    """"""
    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "本地模拟环境-交易盈亏分析"
    engine_class = PortfolioEngine
    widget_name = "PortfolioManager"
    icon_name = "portfolio.ico"
