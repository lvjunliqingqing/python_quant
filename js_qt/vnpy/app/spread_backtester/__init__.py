from pathlib import Path

from vnpy.trader.app import BaseApp

from .engine import SpreadBacktesterEngine, APP_NAME


class SpreadBacktesterApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "套利回测"
    engine_class = SpreadBacktesterEngine
    widget_name = "SpreadBacktesterManager"
    icon_name = "SpreadBacktester.ico"
