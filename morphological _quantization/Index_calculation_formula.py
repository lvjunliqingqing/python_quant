# 源码网址: https://github.com/mpquant/MyTT/blob/main/MyTT.py
# 将通达信,同花顺,文华麦语言等指标公式移植成Python单个文件

# 0级：核心工具函数
# 1级：应用层函数(通过0级核心函数实现）
# 2级：技术指标函数(全部通过0级，1级函数实现）
# 3级：选股指标公式
# 4级：专家买卖指标公式
# 5级：K线蜡烛形态
# 6级：绘图指标公式
# 7级：量化回测结果评估表

import numpy as np
import pandas as pd


# ------------------ 0级：核心工具函数 --------------------------------------------
def RD(N, D=3):
    """浮点数保留几位小数，四舍五入取3位小数"""
    return np.round(N, D)


def RET(S, N=1):
    """返回序列倒数第N个值,默认返回最后一个"""
    return np.array(S)[-N]


def ABS(S):
    """返回s的绝对值"""
    return np.abs(S)


def MAX(S1, S2):
    """序列max"""
    return np.maximum(S1, S2)


def MIN(S1, S2):
    """序列min"""
    return np.minimum(S1, S2)


def MA(S, N):
    """求序列的N日平均值，返回序列"""
    return pd.Series(S).rolling(N).mean().values


# 引用X在N个周期前的值
# 例如：REF(CLOSE,5)  #表示引用当前周期的前第5个周期的收盘价，如果是日线周期，即为第5个交易日前的收盘价
def REF(S, N=1):  # 对序列整体下移动N,返回序列(shift后会产生NAN)
    return pd.Series(S).shift(N).values


def DIFF(S, N=1):  # 前一个值减后一个值,前面会产生nan
    return pd.Series(S).diff(N)  # np.diff(S)直接删除nan，会少一行


def STD(S, N):  # 求序列的N日标准差，返回序列
    return pd.Series(S).rolling(N).std(ddof=0).values


def IF(S_BOOL, S_TRUE, S_FALSE):  # 序列布尔判断 return=S_TRUE if S_BOOL==True  else  S_FALSE
    return np.where(S_BOOL, S_TRUE, S_FALSE)


def SUM(S, N):  # 对序列求N天累计和，返回序列    N=0对序列所有依次求和
    return pd.Series(S).rolling(N).sum().values if N > 0 else pd.Series(S).cumsum()


def HHV(S, N):  # HHV(C, 5)  # 最近5天收盘最高价
    return pd.Series(S).rolling(N).max().values


def LLV(S, N):  # LLV(C, 5)  # 最近5天收盘最低价
    return pd.Series(S).rolling(N).min().values


def EMA(S, N):  # 指数移动平均,为了精度 S>4*N  EMA至少需要120周期     alpha=2/(span+1)
    return pd.Series(S).ewm(span=N, adjust=False).mean().values


def SMA(S, N, M=1):  # 中国式的SMA,至少需要120周期才精确 (雪球180周期)    alpha=1/(1+com)
    return pd.Series(S).ewm(com=N - M, adjust=True).mean().values


def DMA(CLOSE, A):
    return pd.Series(CLOSE).ewm(alpha=A, adjust=False).mean().values


def AVEDEV(S, N):  # 平均绝对偏差  (序列与其平均值的绝对差的平均值)
    return pd.Series(S).rolling(N).apply(lambda x: (np.abs(x - x.mean())).mean()).values


def SLOPE(S, N, RS=False):  # 返S序列N周期回线性回归斜率 (默认只返回斜率,不返回整个直线序列)
    M = pd.Series(S[-N:])
    poly = np.polyfit(M.index, M.values, deg=1)
    Y = np.polyval(poly, M.index)
    if RS: return Y[1] - Y[0], Y
    return Y[1] - Y[0]


# ------------------   1级：应用层函数(通过0级核心函数实现） ----------------------------------
def COUNT(S_BOOL, N):  # COUNT(CLOSE>O, N):  最近N天满足S_BOO的天数  True的天数
    return SUM(S_BOOL, N)


def EVERY(S_BOOL, N):  # EVERY(CLOSE>O, 5)   最近N天是否都是True
    R = SUM(S_BOOL, N)
    return IF(R == N, True, False)


def LAST(S_BOOL, A, B):  # 从前A日到前B日一直满足S_BOOL条件
    if A < B: A = B  # 要求A>B    例：LAST(CLOSE>OPEN,5,3)  5天前到3天前是否都收阳线
    return S_BOOL[-A:-B].sum() == (A - B)  # 返回单个布尔值


def EXIST(S_BOOL, N=5):  # EXIST(CLOSE>3010, N=5)  n日内是否存在一天大于3000点
    R = SUM(S_BOOL, N)
    return IF(R > 0, True, False)


def BARSLAST(S_BOOL):  # 上一次条件成立到当前的周期
    M = np.argwhere(S_BOOL);  # BARSLAST(CLOSE/REF(CLOSE)>=1.1) 上一次涨停到今天的天数
    return len(S_BOOL) - int(M[-1]) - 1 if M.size > 0 else -1


def FORCAST(S, N):  # 返S序列N周期回线性回归后的预测值
    K, Y = SLOPE(S, N, RS=True)
    return Y[-1] + K


def CROSS(S1, S2):  # 判断穿越 CROSS(MA(C,5),MA(C,10))
    CROSS_BOOL = IF(S1 > S2, True, False)
    return COUNT(CROSS_BOOL > 0, 2) == 1  # 上穿：昨天0 今天1   下穿：昨天1 今天0


def RELATE(x, y, N=10):  # RELATE(X,Y,N) 返回X和Y的N周期的相关系数,N支持变量
    x = pd.Series(x)
    y = pd.Series(y)
    result = x.rolling(N).corr(y).values
    return result


def PANEL_MAX(data):  # 多个数据同时比较大小，避免掉写多个MAX的情况
    pandas_list = []
    for i in data:
        pandas_list.append(pd.Series(i))
    df = pd.concat(pandas_list, axis=1)
    result = df.max(axis=1).to_numpy()
    return result


# ------------------   2级：技术指标函数(全部通过0级，1级函数实现） ------------------------------
def MACD(CLOSE, SHORT=12, LONG=26, M=9):  # EMA的关系，S取120日，和雪球小数点2位相同
    DIF = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG);
    DEA = EMA(DIF, M)
    MACD = (DIF - DEA) * 2
    return RD(DIF), RD(DEA), RD(MACD)


def KDJ(CLOSE, HIGH, LOW, N=9, M1=3, M2=3):  # KDJ指标
    RSV = (CLOSE - LLV(LOW, N)) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    K = EMA(RSV, (M1 * 2 - 1))
    D = EMA(K, (M2 * 2 - 1))
    J = K * 3 - D * 2
    return K, D, J


def RSI(CLOSE, N=24):  # RSI指标,和通达信小数点2位相同
    DIF = CLOSE - REF(CLOSE, 1)
    return RD(SMA(MAX(DIF, 0), N) / SMA(ABS(DIF), N) * 100)


def WR(CLOSE, HIGH, LOW, N=10):  # W&R 威廉指标
    WR = (HHV(HIGH, N) - CLOSE) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    return RD(WR)


def BIAS(CLOSE, L1=20):  # BIAS乖离率
    BIAS1 = (CLOSE - MA(CLOSE, L1)) / MA(CLOSE, L1) * 100
    return RD(BIAS1)


def BOLL(CLOSE, N=20, P=2):  # BOLL指标，布林带
    MID = MA(CLOSE, N)
    UPPER = MID + STD(CLOSE, N) * P
    LOWER = MID - STD(CLOSE, N) * P
    return RD(UPPER), RD(MID), RD(LOWER)


def PSY(CLOSE, N=12, M=6):
    PSY = COUNT(CLOSE > REF(CLOSE, 1), N) / N * 100
    PSYMA = MA(PSY, M)
    return RD(PSY), RD(PSYMA)


def CCI(CLOSE, HIGH, LOW, N=14):
    TP = (HIGH + LOW + CLOSE) / 3
    return (TP - MA(TP, N)) / (0.015 * AVEDEV(TP, N))


def ATR(CLOSE, HIGH, LOW, N=20):  # 真实波动N日平均值
    TR = MAX(MAX((HIGH - LOW), ABS(REF(CLOSE, 1) - HIGH)), ABS(REF(CLOSE, 1) - LOW))
    return MA(TR, N)


def BBI(CLOSE, M1=3, M2=6, M3=12, M4=20):  # BBI多空指标
    return (MA(CLOSE, M1) + MA(CLOSE, M2) + MA(CLOSE, M3) + MA(CLOSE, M4)) / 4


def DMI(CLOSE, HIGH, LOW, M1=14, M2=6):  # 动向指标：结果和同花顺，通达信完全一致
    TR = SUM(MAX(MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1))), ABS(LOW - REF(CLOSE, 1))), M1)
    HD = HIGH - REF(HIGH, 1)
    LD = REF(LOW, 1) - LOW
    DMP = SUM(IF((HD > 0) & (HD > LD), HD, 0), M1)
    DMM = SUM(IF((LD > 0) & (LD > HD), LD, 0), M1)
    PDI = DMP * 100 / TR
    MDI = DMM * 100 / TR
    ADX = MA(ABS(MDI - PDI) / (PDI + MDI) * 100, M2)
    ADXR = (ADX + REF(ADX, M2)) / 2
    return PDI, MDI, ADX, ADXR


def TAQ(HIGH, LOW, N):  # 唐安奇通道(海龟)交易指标，大道至简，能穿越牛熊
    UP = HHV(HIGH, N)
    DOWN = LLV(LOW, N)
    MID = (UP + DOWN) / 2
    return UP, MID, DOWN


def KTN(CLOSE, HIGH, LOW, N=20, M=10):  # 肯特纳交易通道, N选20日，ATR选10日
    MID = EMA((HIGH + LOW + CLOSE) / 3, N)
    ATRN = ATR(CLOSE, HIGH, LOW, M)
    UPPER = MID + 2 * ATRN
    LOWER = MID - 2 * ATRN
    return UPPER, MID, LOWER


def TRIX(CLOSE, M1=12, M2=20):  # 三重指数平滑平均线
    TR = EMA(EMA(EMA(CLOSE, M1), M1), M1)
    TRIX = (TR - REF(TR, 1)) / REF(TR, 1) * 100
    TRMA = MA(TRIX, M2)
    return TRIX, TRMA


def VR(CLOSE, VOL, M1=26):  # VR容量比率
    LC = REF(CLOSE, 1)
    return SUM(IF(CLOSE > LC, VOL, 0), M1) / SUM(IF(CLOSE <= LC, VOL, 0), M1) * 100


def EMV(HIGH, LOW, VOL, N=14, M=9):  # 简易波动指标
    VOLUME = MA(VOL, N) / VOL
    MID = 100 * (HIGH + LOW - REF(HIGH + LOW, 1)) / (HIGH + LOW)
    EMV = MA(MID * VOLUME * (HIGH - LOW) / MA(HIGH - LOW, N), N)
    MAEMV = MA(EMV, M)
    return EMV, MAEMV


def DPO(CLOSE, M1=20, M2=10, M3=6):  # 区间震荡线
    DPO = CLOSE - REF(MA(CLOSE, M1), M2)
    MADPO = MA(DPO, M3)
    return DPO, MADPO


def BRAR(OPEN, CLOSE, HIGH, LOW, M1=26):  # BRAR-ARBR 情绪指标
    AR = SUM(HIGH - OPEN, M1) / SUM(OPEN - LOW, M1) * 100
    BR = SUM(MAX(0, HIGH - REF(CLOSE, 1)), M1) / SUM(MAX(0, REF(CLOSE, 1) - LOW), M1) * 100
    return AR, BR


def DMA(CLOSE, N1=10, N2=50, M=10):  # 平行线差指标
    DIF = MA(CLOSE, N1) - MA(CLOSE, N2)
    DIFMA = MA(DIF, M)
    return DIF, DIFMA


def KAMA(CLOSE, N=10, SHORT=2, LONG=30, MAAMA=10):
    DIRECTION = CLOSE - REF(CLOSE, N)
    VOLATILITY = SUM(ABS((CLOSE - REF(CLOSE, 1))), N)
    ER = ABS(DIRECTION / VOLATILITY)
    FASTSC = 2 / (SHORT + 1)
    SLOWSC = 2 / (LONG + 1)
    SSC = ER * (FASTSC - SLOWSC) + SLOWSC
    CONSTANT = SSC * SSC
    AMA = np.zeros(CONSTANT.size)
    first_value = True
    for i in range(len(CONSTANT)):
        if CONSTANT[i] != CONSTANT[i]:
            AMA[i] = np.nan
        else:
            if first_value:
                AMA[i] = CLOSE[i]
                first_value = False
            else:
                AMA[i] = AMA[i - 1] + CONSTANT[i] * (CLOSE[i] - AMA[i - 1])
    AMA = AMA[30:]
    AMA1 = AMA
    AMA2 = EMA(AMA, MAAMA)
    return AMA1, AMA2


def MTM(CLOSE, N=12, M=6):  # 动量指标
    MTM = CLOSE - REF(CLOSE, N)
    MTMMA = MA(MTM, M)
    return MTM, MTMMA


def MASS(HIGH, LOW, N1=9, N2=25, M=6):  # 梅斯线
    MASS = SUM(MA(HIGH - LOW, N1) / MA(MA(HIGH - LOW, N1), N1), N2)
    MA_MASS = MA(MASS, M)
    return MASS, MA_MASS


def ROC(CLOSE, N=12, M=6):  # 变动率指标
    ROC = 100 * (CLOSE - REF(CLOSE, N)) / REF(CLOSE, N)
    MAROC = MA(ROC, M)
    return ROC, MAROC


def EXPMA(CLOSE, N1=12, N2=50):  # EMA指数平均数指标
    return EMA(CLOSE, N1), EMA(CLOSE, N2)


def OBV(CLOSE, VOL):  # 能量潮指标
    return SUM(IF(CLOSE > REF(CLOSE, 1), VOL, IF(CLOSE < REF(CLOSE, 1), -VOL, 0)), 0) / 10000


def MFI(CLOSE, HIGH, LOW, VOL, N=14):  # MFI指标是成交量的RSI指标
    TYP = (HIGH + LOW + CLOSE) / 3
    V1 = SUM(IF(TYP > REF(TYP, 1), TYP * VOL, 0), N) / SUM(IF(TYP < REF(TYP, 1), TYP * VOL, 0), N)
    return 100 - (100 / (1 + V1))


def ASI(OPEN, CLOSE, HIGH, LOW, M1=26, M2=10):  # 振动升降指标
    LC = REF(CLOSE, 1)
    AA = ABS(HIGH - LC)
    BB = ABS(LOW - LC)
    CC = ABS(HIGH - REF(LOW, 1))
    DD = ABS(LC - REF(OPEN, 1))
    R = IF((AA > BB) & (AA > CC), AA + BB / 2 + DD / 4, IF((BB > CC) & (BB > AA), BB + AA / 2 + DD / 4, CC + DD / 4))
    X = (CLOSE - LC + (CLOSE - OPEN) / 2 + LC - REF(OPEN, 1))
    SI = 16 * X / R * MAX(AA, BB)
    ASI = SUM(SI, M1)
    ASIT = MA(ASI, M2)
    return ASI, ASIT


def williams(df, n, column='williams'):  # 威廉指标
    # 100*(10日内最高价的最高值-收盘价)/(10日内最高价的最高值-10日内最低价的最低值)
    for i in range(len(df)):
        if i < n - 1:
            continue
        df.ix[i, column] = 100 * (df.high.values[i - n + 1:i + 1].max() - df.close.values[i]) / (
                df.high.values[i - n + 1:i + 1].max() - df.low.values[i - n + 1:i + 1].min())
    return df

