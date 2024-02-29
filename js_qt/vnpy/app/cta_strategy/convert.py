
from vnpy.trader.constant import Exchange


class Convert:
    def convert_jqdata_exchange(self, exchange):
        """
        vnpy交易代码转换成jq上的交易所代码
        """
        exchange_dist = {
            "CFFEX": Exchange.CCFX,
            "INE": Exchange.XINE,
            "SHFE": Exchange.XSGE,
            "CZCE": Exchange.XZCE,
            "DCE": Exchange.XDCE,
        }

        if exchange in exchange_dist:
            return exchange_dist[exchange]
        return Exchange(exchange)

    def convert_vnpy_exchange(self, exchange):
        """
        jq交易代码转换成vnpy上的交易所代码
        """
        exchange_dist = {
            "CCFX": Exchange.CFFEX,
            "XINE": Exchange.INE,
            "XSGE": Exchange.SHFE,
            "XZCE": Exchange.CZCE,
            "XDCE": Exchange.DCE,
        }

        if exchange in exchange_dist:
            return exchange_dist[exchange]
        return Exchange(exchange)