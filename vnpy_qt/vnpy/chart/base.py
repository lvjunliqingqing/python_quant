from vnpy.trader.ui import QtGui


WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
GREY_COLOR = (100, 100, 100)

UP_COLOR = (255, 75, 75)
DOWN_COLOR = (0, 255, 255)
CURSOR_COLOR = (255, 245, 162)

DARKVIOLET_COLOR = (148, 0, 211)
PALEGREEN_COLOR = (84, 139, 84)
YELLOW_COLOR_2 = (255, 255, 0)
GREEN_COLOR = (0, 128, 0)
YELLOW_COLOR = (225, 225, 0)
RED_COLOR = (255, 0, 0)
PEN_WIDTH = 1
BAR_WIDTH = 0.3

AXIS_WIDTH = 0.8
NORMAL_FONT = QtGui.QFont("Arial", 10)


def to_int(value: float) -> int:
    """"""
    return int(round(value, 0))
