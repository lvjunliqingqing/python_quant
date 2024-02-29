from pathlib import Path
from vnpy.trader.app import BaseApp
from .engine import PlayBackChartEngine, APP_NAME


class PlayBackChartApp(BaseApp):
    """"""
    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "K线复盘训练"
    engine_class = PlayBackChartEngine
    widget_name = "PlayBackChartWidget"
    icon_name = "playback.ico"
