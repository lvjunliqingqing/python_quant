from pathlib import Path

from vnpy.trader.app import BaseApp
from .engine import APP_NAME, ManualPositionAdjustmentEngine


class ManualPositionAdjustmentApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "手动输入开仓单"
    engine_class = ManualPositionAdjustmentEngine
    widget_name = "ManualPositionAdjustmentWidget"
    icon_name = "manual.ico"
