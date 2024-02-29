GATEWAY_INFO = [
    {
        "name": "CTP",
        "module": "vnpy.gateway.ctp",
        "class": "CtpGateway",
        "description": "期货、期货期权（实盘6.3.15）"
    },
    {
        "name": "CTP测试",
        "module": "vnpy.gateway.ctptest",
        "class": "CtptestGateway",
        "description": "期货、期货期权（测试6.3.16）"
    },
    {
        "name": "CTP Mini",
        "module": "vnpy.gateway.mini",
        "class": "MiniGateway",
        "description": "期货、期货期权（实盘1.4）"
    },
    {
        "name": "CTP Mini测试",
        "module": "vnpy.gateway.minitest",
        "class": "MinitestGateway",
        "description": "期货、期货期权（测试1.2）"
    },
    {
        "name": "飞马",
        "module": "vnpy.gateway.femas",
        "class": "FemasGateway",
        "description": "期货"
    },
    {
        "name": "CTP期权",
        "module": "vnpy.gateway.sopt",
        "class": "SoptGateway",
        "description": "ETF期权（实盘20190802）"
    },
    {
        "name": "CTP期权测试",
        "module": "vnpy.gateway.sopttest",
        "class": "SopttestGateway",
        "description": "ETF期权（实盘20190604）"
    },
    {
        "name": "飞创期权",
        "module": "vnpy.gateway.sec",
        "class": "SecGateway",
        "description": "ETF期权（实盘20200427）"
    },
    {
        "name": "恒生UFT",
        "module": "vnpy.gateway.uft",
        "class": "UftGateway",
        "description": "期货、ETF期权"
    },
    {
        "name": "恒生期权",
        "module": "vnpy.gateway.hsoption",
        "class": "HsoptionGateway",
        "description": "ETF期权"
    },
    {
        "name": "中泰XTP",
        "module": "vnpy.gateway.xtp",
        "class": "XtpGateway",
        "description": "A股、两融、ETF期权"
    },
    {
        "name": "华鑫奇点股票",
        "module": "vnpy.gateway.tora",
        "class": "ToraStockGateway",
        "description": "A股"
    },
    {
        "name": "华鑫奇点期权",
        "module": "vnpy.gateway.tora",
        "class": "ToraOptionGateway",
        "description": "ETF期权"
    },
    {
        "name": "宽睿",
        "module": "vnpy.gateway.oes",
        "class": "OesGateway",
        "description": "A股、ETF期权"
    },
    {
        "name": "中亿汇达Comstar",
        "module": "vnpy.gateway.comstar",
        "class": "ComstarGateway",
        "description": "银行间市场"
    },
    {
        "name": "富途证券",
        "module": "vnpy.gateway.futu",
        "class": "FutuGateway",
        "description": "港股、美股"
    },
    {
        "name": "盈透证券",
        "module": "vnpy.gateway.ib",
        "class": "IbGateway",
        "description": "海外全品种"
    },
    {
        "name": "老虎证券",
        "module": "vnpy.gateway.tiger",
        "class": "TigerGateway",
        "description": "海外全品种"
    },
    {
        "name": "易盛9.0外盘",
        "module": "vnpy.gateway.tap",
        "class": "TapGateway",
        "description": "外盘期货"
    },
    {
        "name": "直达期货",
        "module": "vnpy.gateway.da",
        "class": "DaGateway",
        "description": "外盘期货"
    },
    {
        "name": "MetaTrader 5",
        "module": "vnpy.gateway.mt5",
        "class": "Mt5Gateway",
        "description": "外汇、CFD、股票、期货"
    },
    {
        "name": "币安",
        "module": "vnpy.gateway.binance",
        "class": "BinanceGateway",
        "description": "数字货币"
    },
    {
        "name": "币安永续合约",
        "module": "vnpy.gateway.binances",
        "class": "BinancesGateway",
        "description": "数字货币永续和期货"
    },
    {
        "name": "火币",
        "module": "vnpy.gateway.huobi",
        "class": "HuobiGateway",
        "description": "数字货币"
    },
    {
        "name": "火币期货",
        "module": "vnpy.gateway.huobif",
        "class": "HuobifGateway",
        "description": "数字货币期货"
    },
    {
        "name": "火币永续",
        "module": "vnpy.gateway.huobis",
        "class": "HuobisGateway",
        "description": "数字货币永续"
    },
    {
        "name": "火币期权",
        "module": "vnpy.gateway.huobio",
        "class": "HuobioGateway",
        "description": "数字货币期权"
    },
    {
        "name": "OKEX",
        "module": "vnpy.gateway.okex",
        "class": "OkexGateway",
        "description": "数字货币"
    },
    {
        "name": "OKEX期货",
        "module": "vnpy.gateway.okexf",
        "class": "OkexfGateway",
        "description": "数字货币期货"
    },
    {
        "name": "OKEX永续",
        "module": "vnpy.gateway.okexs",
        "class": "OkexsGateway",
        "description": "数字货币永续"
    },
    {
        "name": "OKEX期权",
        "module": "vnpy.gateway.okexo",
        "class": "OkexoGateway",
        "description": "数字货币期权"
    },
    {
        "name": "BitMEX",
        "module": "vnpy.gateway.bitmex",
        "class": "BitmexGateway",
        "description": "数字货币期货、永续"
    },
    {
        "name": "Bybit",
        "module": "vnpy.gateway.bybit",
        "class": "BybitGateway",
        "description": "数字货币永续"
    },
    {
        "name": "Gate.io合约",
        "module": "vnpy.gateway.gateios",
        "class": "GateiosGateway",
        "description": "数字货币永续"
    },
    {
        "name": "Deribit",
        "module": "vnpy.gateway.deribit",
        "class": "DeribitGateway",
        "description": "数字货币永续、期权"
    },
    {
        "name": "Bitfinex",
        "module": "vnpy.gateway.bitfinex",
        "class": "BitfinexGateway",
        "description": "数字货币"
    },
    {
        "name": "Coinbase",
        "module": "vnpy.gateway.coinbase",
        "class": "CoinbaseGateway",
        "description": "数字货币"
    },
    {
        "name": "Bitstamp",
        "module": "vnpy.gateway.bitstamp",
        "class": "BitstampGateway",
        "description": "数字货币"
    },
    {
        "name": "1Token",
        "module": "vnpy.gateway.onetoken",
        "class": "OnetokenGateway",
        "description": "数字货币"
    },
    {
        "name": "融航",
        "module": "vnpy.gateway.rohon",
        "class": "RohonGateway",
        "description": "期货资管"
    },
    {
        "name": "鑫管家",
        "module": "vnpy.gateway.xgj",
        "class": "XgjGateway",
        "description": "期货资管"
    },
    {
        "name": "RPC服务",
        "module": "vnpy.gateway.rpc",
        "class": "RpcGateway",
        "description": "核心交易路由"
    }
]


APP_INFO = [
    {
        "name": "CtaStrategy",
        "module": "vnpy.app.cta_strategy",
        "class": "CtaStrategyApp",
        "description": "CTA自动交易模块"
    },
    {
        "name": "CtaBacktester",
        "module": "vnpy.app.cta_backtester",
        "class": "CtaBacktesterApp",
        "description": "CTA回测研究模块"
    },
    {
        "name": "SpreadTrading",
        "module": "vnpy.app.spread_trading",
        "class": "SpreadTradingApp",
        "description": "多合约价差套利模块"
    },
    {
        "name": "AlgoTrading",
        "module": "vnpy.app.algo_trading",
        "class": "AlgoTradingApp",
        "description": "算法委托执行交易模块"
    },
    {
        "name": "OptionMaster",
        "module": "vnpy.app.option_master",
        "class": "OptionMasterApp",
        "description": "期权波动率交易模块"
    },
    {
        "name": "PortfolioStrategy",
        "module": "vnpy.app.portfolio_strategy",
        "class": "PortfolioStrategyApp",
        "description": "多合约组合策略模块"
    },
    {
        "name": "ScriptTrader",
        "module": "vnpy.app.script_trader",
        "class": "ScriptTraderApp",
        "description": "脚本策略交易模块"
    },
    {
        "name": "MarketRadar",
        "module": "vnpy.app.market_radar",
        "class": "MarketRadarApp",
        "description": "市场扫描雷达模块"
    },
    {
        "name": "ChartWizard",
        "module": "vnpy.app.chart_wizard",
        "class": "ChartWizardApp",
        "description": "实时K线图表模块"
    },
    {
        "name": "RpcService",
        "module": "vnpy.app.rpc_service",
        "class": "RpcServiceApp",
        "description": "RPC服务器模块"
    },
    {
        "name": "ExcelRtd",
        "module": "vnpy.app.excel_rtd",
        "class": "ExcelRtdApp",
        "description": "EXCEL RTD模块"
    },
    {
        "name": "DataManager",
        "module": "vnpy.app.data_manager",
        "class": "DataManagerApp",
        "description": "历史数据管理模块"
    },
    {
        "name": "DataRecorder",
        "module": "vnpy.app.data_recorder",
        "class": "DataRecorderApp",
        "description": "实盘行情记录模块"
    },
    {
        "name": "RiskManager",
        "module": "vnpy.app.risk_manager",
        "class": "RiskManagerApp",
        "description": "事前风险管理模块"
    },
    {
        "name": "PortfolioManager",
        "module": "vnpy.app.portfolio_manager",
        "class": "PortfolioManagerApp",
        "description": "投资组合管理模块"
    },
    {
        "name": "PaperAccount",
        "module": "vnpy.app.paper_account",
        "class": "PaperAccountApp",
        "description": "模拟交易账户模块"
    },
    {
        "name": "CsvLoader",
        "module": "vnpy.app.csv_loader",
        "class": "CsvLoaderApp",
        "description": "CSV载入模块"
    },
    {
        "name": "MultipleVarietiesBackTest",
        "module": "vnpy.app.multiple_varieties_backtest",
        "class": "MultipleVarietiesBackTestApp",
        "description": "多品种回测模块"
    },
    {
        "name": "ManualPositionAdjustment",
        "module": "vnpy.app.manual_position_adjustment",
        "class": "ManualPositionAdjustmentApp",
        "description": "手动输入开仓单模块"
    },
    {
        "name": "PortfolioBacktester",
        "module": "vnpy.app.portfolio_backtester",
        "class": "PortfolioBacktesterApp",
        "description": "组合回测模块"
    },
]


TEXT_TRADER_CONFIG = """
1. 请勾选需要使用的底层接口和上层应用模块
2. 配置完毕后，点击“启动”按钮来打开VN Trader
3. VN Trader运行时请勿关闭VN Station（会造成退出）
4. CTP、CTP测试接口不能同时加载（会导致API版本错误）
5. CTP Mini和CTP Mini测试接口不能同时加载（会导致API版本错误）
"""
