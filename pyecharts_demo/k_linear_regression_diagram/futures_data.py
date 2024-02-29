from sqlalchemy import create_engine
import pandas as pd
import datetime

pd.set_option('display.float_format', lambda x: '%.4f' % x)  # 禁止科学计算显示,保留四位有效小数点
pd.set_option('expand_frame_repr', False)  # 最多显示多少列, 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


class FuturesData:

    def __init__(self):
        self.connect = create_engine('mysql+pymysql://manager:jskjfwq@192.168.11.253:3306/futures?charset=utf8')
        self.start_date = "2000-01-01 00:00:00"
        self.end_date = datetime.datetime.now().date().strftime("%Y-%m-%d")

    def read_mysql(self, sql):
        df = pd.read_sql(sql, con=self.connect)  # 读取SQL数据库，并转化成pandas。
        return df

    def read_futures_bias_daily(self):
        """期货每日BIAS表"""
        sql = f'SELECT * FROM dwb_futures_bias_daily WHERE security REGEXP  ".*(8888).*" and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'
        df = self.read_mysql(sql)
        if not df.empty:
            df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_rsi(self):
        """期货每日RSI表"""
        sql = f'SELECT * FROM dwb_futures_rsi_daily WHERE security REGEXP ".*(8888).*" and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'
        df = self.read_mysql(sql)
        if not df.empty:
            df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_boll(self):
        """期货每日BOLL表"""
        sql = f'SELECT * FROM dwb_futures_boll_daily WHERE security REGEXP ".*(8888).*" and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'
        df = self.read_mysql(sql)
        if not df.empty:
            df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_macd(self):
        """期货每日MACD表"""
        sql = f'SELECT * FROM dwb_futures_macd_daily WHERE security REGEXP ".*(8888).*" and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'
        df = self.read_mysql(sql)
        if not df.empty:
            df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_ma(self):
        """期货每日MA表"""
        sql = f'SELECT * FROM dwb_futures_ma_daily WHERE security REGEXP ".*(8888).*" and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'  # adjust字段只有none(不复权)数据
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_price_daily(self):
        """期货日K线数据表"""
        sql = f'SELECT security,trade_date,open,close,low,high,volume,open_interest,pre_close,high_limit,change_pct FROM dwd_futures_price_daily WHERE security REGEXP ".*(9999).*" ' \
              f'and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none" ORDER BY trade_date'  # 正则匹配

        df = self.read_mysql(sql)
        if not df.empty:
            df = df[~((df["low"] == df["high"]) & (df["volume"] == 0))]  # 过滤掉停盘数据
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_futures_contract_info(self, security_tuple=()):
        """期货合约乘数信息表"""
        if security_tuple:
            sql = f'SELECT * FROM dwd_futures_contract_info WHERE security in {security_tuple}'
        else:
            sql = f'SELECT * FROM dwd_futures_contract_info WHERE security REGEXP ".*(8888).*"'
        df = self.read_mysql(sql)
        return df

    def read_futures_base_info(self, security_tuple=()):
        """期货基本信息表(上市退市时间)"""
        if security_tuple:
            sql = f'SELECT * FROM dwd_futures_base_info WHERE security in {security_tuple}'
        else:
            sql = f'SELECT * FROM dwd_futures_base_info WHERE security REGEXP ".*(8888).*"'
        df = self.read_mysql(sql)
        return df


if __name__ == '__main__':
    futures_data = FuturesData()
    # futures_price_df = futures_data.read_futures_bias_daily()
    # futures_price_df = futures_data.read_futures_rsi()
    # futures_price_df = futures_data.read_futures_boll()
    # futures_price_df = futures_data.read_futures_macd()
    # futures_price_df = futures_data.read_futures_ma()
    # futures_price_df = futures_data.read_futures_contract_info()
    # futures_price_df = futures_data.read_futures_base_info()
    futures_price_df = futures_data.read_futures_price_daily()
    print(futures_price_df)

