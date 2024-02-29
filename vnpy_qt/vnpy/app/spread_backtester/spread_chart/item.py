
from typing import Tuple
from vnpy.chart.item import CandleItem


class SpreadCandleItem(CandleItem):
    """"""

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        在给定x轴的范围内得到y轴的范围。
        如果min_ix和max_ix没有指定，则返回包含整个数据集的范围。
        """
        min_price, max_price = self._manager.get_price_range(min_ix, max_ix)
        return min_price * 1.04, max_price * 1.04

    def get_info_text(self, ix: int) -> str:
        """
        获取要通过光标显示的信息文本。
        """
        bar = self._manager.get_bar(ix)
        ratio = "-"
        if ix >= 1:
            pre_bar = self._manager.get_bar(ix - 1)
            if hasattr(pre_bar, "close_price") and hasattr(bar, "close_price"):
                try:
                    ratio = str(round((bar.close_price - pre_bar.close_price) / pre_bar.close_price * 100, 2)) + "%"
                except Exception:  # noqa
                    ratio = "0%"

        if bar:
            words = [
                "日期时间",
                bar.datetime.strftime("%Y-%m-%d %H:%M"),
                "",
                "开盘价",
                str(bar.open_price),
                "",
                "最高价",
                str(bar.high_price),
                "",
                "最低价",
                str(bar.low_price),
                "",
                "收盘价",
                str(bar.close_price),
                "涨幅",
                ratio

            ]
            text = "\n".join(words)
        else:
            text = ""

        return text
