"""
Event type string used in VN Trader.
"""

from vnpy.event import EVENT_TIMER  # noqa

EVENT_TICK = "eTick."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."
EVENT_LOG = "eLog"
EVENT_CTA_LOG = "eCtaLog"
EVENT_PORTFOLIO_LOG = "ePortfolioLog"
EVENT_DOMINANT_CONTRACT_TRADE = "DominantContractTrade"

EVENT_STRATEGY_HOLD_POSITION = "eStrategyHoldPosition"
EVENT_STRATEGY_CLOSE_POSITION = "eStrategyClosePosition"
# 策略是否继续开仓的事件变量
EVENT_STRATEGY_WHETHER_CONTINUE_OPEN = "eStrategyWhetherContinueOpen"
# 强制平仓事件变量
EVENT_FORCED_LIQUIDATION = "eForcedLiquidation"

EVENT_WINRATE = "eWinRate"
EVENT_DELETEID = "eNewDelete"
