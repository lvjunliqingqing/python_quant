"""
记录品种的基本属性， 合约乘数， 保证金占用比率， 品种最小价格跳动
"""

ContractMultiplier = {'A': 10,
                      'AG': 15,
                      'AL': 5,
                      'AP': 10,
                      'AU': 1000,
                      'B': 10,
                      'BB': 500,
                      'BU': 10,
                      'C': 10,
                      'CF': 5,
                      'CJ': 5,
                      'CS': 10,
                      'CU': 5,
                      'CY': 5,
                      'EB': 5,
                      'EG': 10,
                      'ER': 10,
                      'FB': 500,
                      'FG': 20,
                      'FU': 10,
                      'HC': 10,
                      'I': 100,
                      'IC': 200,
                      'IF': 300,
                      'IH': 300,
                      'J': 100,
                      'JD': 10,
                      'JM': 60,
                      'JR': 20,
                      'L': 5,
                      'LR': 20,
                      'M': 10,
                      'MA': 10,
                      'ME': 50,
                      'NI': 1,
                      'NR': 10,
                      'OI': 10,
                      'P': 10,
                      'PB': 5,
                      'PM': 50,
                      'PP': 5,
                      'RB': 10,
                      'RI': 20,
                      'RM': 10,
                      'RO': 5,
                      'RR': 10,
                      'RS': 10,
                      'RU': 10,
                      'SA': 20,
                      'SC': 1000,
                      'SF': 5,
                      'SM': 5,
                      'SN': 1,
                      'SP': 10,
                      'SR': 10,
                      'SS': 5,
                      'T': 10000,
                      'TA': 5,
                      'TC': 200,
                      'TF': 10000,
                      'TS': 20000,
                      'UR': 20,
                      'V': 5,
                      'WH': 20,
                      'WR': 10,
                      'WS': 10,
                      'WT': 10,
                      'Y': 10,
                      'ZC': 100,
                      'ZN': 5,
                      'PG': 20,
                      'IO': 100,
                      'LU': 10,
                      }

ContractMarginRatio = {'A': 0.05,
                       'AG': 0.08,
                       'AL': 0.1,
                       'AP': 0.07,
                       'AU': 0.08,
                       'B': 0.05,
                       'BB': 0.2,
                       'BU': 0.1,
                       'C': 0.05,
                       'CF': 0.05,
                       'CJ': 0.07,
                       'CS': 0.05,
                       'CU': 0.09,
                       'CY': 0.05,
                       'EB': 0.12,
                       'EG': 0.05,
                       'FB': 0.2,
                       'FG': 0.05,
                       'FU': 0.2,
                       'HC': 0.1,
                       'I': 0.05,
                       'IC': 0.1,
                       'IF': 0.1,
                       'IH': 0.1,
                       'J': 0.05,
                       'JD': 0.08,
                       'JM': 0.05,
                       'JR': 0.05,
                       'L': 0.05,
                       'LR': 0.05,
                       'M': 0.05,
                       'MA': 0.07,
                       'NI': 0.1,
                       'NR': 0.11,
                       'OI': 0.05,
                       'P': 0.05,
                       'PB': 0.1,
                       'PM': 0.05,
                       'PP': 0.05,
                       'RB': 0.1,
                       'RI': 0.05,
                       'RM': 0.05,
                       'RR': 0.06,
                       'RS': 0.05,
                       'RU': 0.1,
                       'SA': 0.05,
                       'SC': 0.05,
                       'SF': 0.05,
                       'SM': 0.05,
                       'SN': 0.09,
                       'SP': 0.07,
                       'SR': 0.05,
                       'SS': 0.09,
                       'T': 0.02,
                       'TA': 0.05,
                       'TF': 0.01,
                       'TS': 0.01,
                       'UR': 0.05,
                       'V': 0.05,
                       'WH': 0.05,
                       'WR': 0.2,
                       'Y': 0.05,
                       'ZC': 0.05,
                       'ZN': 0.1,
                       'ER': 0.1,
                       'IO': 0.1,
                       'LU': 0.12,
                       'ME': 0.1,
                       'RO': 0.1,
                       'TC': 0.1,
                       'WS': 0.1,
                       'WT': 0.1,
                       'PG': 0.05,
                       }

ContractPricePick = {'A': 1.0,
                     'AG': 1.0,
                     'AL': 5.0,
                     'AP': 1.0,
                     'AU': 0.02,
                     'B': 1.0,
                     'BB': 0.05,
                     'BU': 2.0,
                     'C': 1.0,
                     'CF': 5.0,
                     'CJ': 5.0,
                     'CS': 1.0,
                     'CU': 10.0,
                     'CY': 5.0,
                     'EB': 1.0,
                     'EG': 1.0,
                     'FB': 0.05,
                     'FG': 1.0,
                     'FU': 1.0,
                     'HC': 1.0,
                     'I': 0.5,
                     'IC': 0.2,
                     'IF': 0.2,
                     'IH': 0.2,
                     'J': 0.5,
                     'JD': 1.0,
                     'JM': 0.5,
                     'JR': 1.0,
                     'L': 5.0,
                     'LR': 1.0,
                     'M': 1.0,
                     'MA': 1.0,
                     'NI': 10.0,
                     'NR': 5.0,
                     'OI': 1.0,
                     'P': 2.0,
                     'PB': 5.0,
                     'PM': 1.0,
                     'PP': 1.0,
                     'RB': 1.0,
                     'RI': 1.0,
                     'RM': 1.0,
                     'RR': 1.0,
                     'RS': 1.0,
                     'RU': 5.0,
                     'SA': 1.0,
                     'SC': 0.1,
                     'SF': 2.0,
                     'SM': 2.0,
                     'SN': 10.0,
                     'SP': 2.0,
                     'SR': 1.0,
                     'SS': 5.0,
                     'T': 0.005,
                     'TA': 2.0,
                     'TF': 0.005,
                     'TS': 0.005,
                     'UR': 1.0,
                     'V': 5.0,
                     'WH': 1.0,
                     'WR': 1.0,
                     'Y': 2.0,
                     'ZC': 0.2,
                     'ZN': 5.0,
                     'PG': 1,
                     'ER': 1,
                     'IO': 1,
                     'LU': 1,
                     'ME': 1,
                     'RO': 1,
                     'TC': 1,
                     'WS': 1,
                     'WT': 1,
                     }

# 期货品种的手续费，如果数值少于 0.1 的话，即为 手续费率， 如果数据大于 0.1 的话，即为 手续费。
SymbolCommission = {'SC': 0.0001,
                    'AG': 5e-05,
                    'AL': 3.0,
                    'AU': 10.0,
                    'BU': 0.0001,
                    'CU': 5e-05,
                    'HC': 0.0001,
                    'NI': 6.0,
                    'PB': 4e-05,
                    'RB': 0.0001,
                    'RU': 4.5e-05,
                    'SN': 3.0,
                    'SP': 5e-05,
                    'WR': 4e-05,
                    'ZN': 3.0,
                    'PM': 5.0,
                    'RI': 2.5,
                    'RM': 1.5,
                    'SF': 3.0,
                    'SM': 3.0,
                    'WH': 2.5,
                    'A': 2.0,
                    'B': 2.0,
                    'BB': 0.0001,
                    'C': 1.2,
                    'CS': 1.5,
                    'FB': 0.0001,
                    'I': 6e-05,
                    'J': 6e-05,
                    'JM': 6e-05,
                    'L': 2.0,
                    'M': 1.5,
                    'P': 2.5,
                    'PP': 5e-05,
                    'V': 2.0,
                    'Y': 2.5,
                    'CF': 4.3,
                    'SR': 3.0,
                    'TA': 3.0,
                    'CY': 4.0,
                    'FG': 3.0,
                    'MA': 1.4,
                    'RS': 2.0,
                    'IC': 2.3e-05,
                    'IF': 2.3e-05,
                    'IH': 2.3e-05,
                    'ZC': 4.0,
                    'EG': 6.0,
                    'JD': 0.00015,
                    'FU': 2e-05,
                    'AP': 0.5,
                    'JR': 3.0,
                    'LR': 3.0,
                    'OI': 2.5,
                    'T': 3.0,
                    'TF': 3.0,
                    'TS': 3.0,
                    'UR': 5.0,
                    'CJ': 0.0001,
                    'LU': 0.0001,
                    'NR': 0.0001,
                    'RR': 0.0001,
                    'SA': 0.0001,
                    'SS': 0.0001,
                    'PG': 0.0001,
                    }

SymbolExchange = {
    'A': 'XDCE',
    'AG': 'XSGE',
    'AL': 'XSGE',
    'AP': 'XZCE',
    'AU': 'XSGE',
    'B': 'XDCE',
    'BB': 'XDCE',
    'BU': 'XSGE',
    'C': 'XDCE',
    'CF': 'XZCE',
    'CJ': 'XZCE',
    'CS': 'XDCE',
    'CU': 'XSGE',
    'CY': 'XZCE',
    'EB': 'XDCE',
    'EG': 'XDCE',
    'FB': 'XDCE',
    'FG': 'XZCE',
    'FU': 'XSGE',
    'HC': 'XSGE',
    'I': 'XDCE',
    'IC': 'CCFX',
    'IF': 'CCFX',
    'IH': 'CCFX',
    'J': 'XDCE',
    'JD': 'XDCE',
    'JM': 'XDCE',
    'JR': 'XZCE',
    'L': 'XDCE',
    'LR': 'XZCE',
    'M': 'XDCE',
    'MA': 'XZCE',
    'NI': 'XSGE',
    'NR': 'XINE',
    'OI': 'XZCE',
    'P': 'XDCE',
    'PB': 'XSGE',
    'PM': 'XZCE',
    'PP': 'XDCE',
    'RB': 'XSGE',
    'RI': 'XZCE',
    'RM': 'XZCE',
    'RS': 'XZCE',
    'RU': 'XSGE',
    'SC': 'XINE',
    'SF': 'XZCE',
    'SM': 'XZCE',
    'SN': 'XSGE',
    'SP': 'XSGE',
    'SR': 'XZCE',
    'SS': 'XSGE',
    'T': 'CCFX',
    'TA': 'XZCE',
    'TF': 'CCFX',
    'TS': 'CCFX',
    'UR': 'XZCE',
    'V': 'XDCE',
    'WH': 'XZCE',
    'WR': 'XSGE',
    'Y': 'XDCE',
    'ZC': 'XZCE',
    'ZN': 'XSGE',
    'PG': 'XDCE',
    'LU': 'XSGE',
    'RR': 'XDCE',
    'SA': 'XZCE',
}

FuturesCompanySpread = {
    'CU': 0.0600,
    'AL': 0.0600,
    'ZN': 0.0600,
    'PB': 0.0600,
    'NI': 0.0600,
    'SN': 0.0600,
    'AU': 0.0600,
    'AG': 0.0600,
    'RB': 0.0600,
    'SS': 0.0600,
    'WR': 0.0600,
    'HC': 0.0600,
    'FU': 0.0600,
    'BU': 0.0600,
    'RU': 0.0600,
    'SP': 0.0600,
    'A': 0.0500,
    'B': 0.0600,
    'M': 0.0600,
    'Y': 0.0600,
    'P': 0.0600,
    'C': 0.0500,
    'CS': 0.0500,
    'RR': 0.0500,
    'JD': 0.0600,
    'EG': 0.0600,
    'L': 0.0600,
    'V': 0.0600,
    'EB': 0.0600,
    'PP': 0.0600,
    'J': 0.0600,
    'JM': 0.0600,
    'I': 0.0600,
    'PG': 0.0700,
    'FB': 0.2000,
    'BB': 0.0500,
    'AP': 0.0600,
    'WH': 0.0533,
    'PM': 0.0467,
    'CF': 0.0600,
    'CY': 0.0433,
    'CJ': 0.0600,
    'SR': 0.0600,
    'OI': 0.0500,
    'RS': 0.0300,
    'RM': 0.0500,
    'RI': 0.0467,
    'LR': 0.0467,
    'JR': 0.0467,
    'MA': 0.0600,
    'TA': 0.0600,
    'UR': 0.0600,
    'SA': 0.0500,
    'FG': 0.0500,
    'SF': 0.0700,
    'SM': 0.0700,
    'ZC': 0.0600,
    'IF': 0.0300,
    'IO': 0.0300,
    'IH': 0.0300,
    'IC': 0.0300,
    'TS': 0.0050,
    'TF': 0.0100,
    'T': 0.0100,
    'LU': 0.0600,
    'NR': 0.0600,
    'SC': 0.0600,
}