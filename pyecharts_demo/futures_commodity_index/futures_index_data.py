from sqlalchemy import create_engine
import pandas as pd
import datetime

pd.set_option('display.float_format', lambda x: '%.4f' % x)  # 禁止科学计算显示,保留四位有效小数点


class FuturesIndex:

    def __init__(self):
        self.connect = create_engine('mysql+pymysql://root:jskjfwq@192.168.11.250:3308/futures?charset=utf8')
        self.start_date = "1900-01-01"
        self.end_date = datetime.datetime.now().date().strftime("%Y-%m-%d")

    def read_mysql(self, sql):
        df = pd.read_sql(sql, con=self.connect)  # 读取SQL数据库，并转化成pandas。
        return df

    def read_futures_index(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        return df

    def read_futures_index_bias(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index_bias WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index_bias WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_index_rsi(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index_rsi WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index_rsi WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_index_boll(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index_boll WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index_boll WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_index_macd(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index_macd WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index_macd WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_index_ma(self, index_name=""):
        if index_name:
            sql = f'SELECT * FROM dwb_futures_customize_index_ma WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}" and index_name="{index_name}"'
        else:
            sql = f'SELECT * FROM dwb_futures_customize_index_ma WHERE trade_date >= "{self.start_date}" and trade_date <= "{self.end_date}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor"], axis=1, inplace=True)
        return df

    def read_futures_price_daily(self, trade_date):
        # sql = f'SELECT * FROM dwd_futures_price_daily WHERE trade_date="{trade_date}" and security NOT  REGEXP ".*(9999|8888).*"'  # 正则匹配
        sql = f'SELECT * FROM dwd_futures_price_daily WHERE trade_date="{trade_date}" and security REGEXP ".*(9999).*" and adjust="none"'  # 正则匹配
        df = self.read_mysql(sql)
        if df.empty:  # 如果指定日期取不到,则取这个表格中最新日期的数据
            sql = f'SELECT * FROM dwd_futures_price_daily WHERE trade_date=(SELECT trade_date FROM dwd_futures_price_daily where adjust="none" ORDER BY trade_date DESC LIMIT 1) and security REGEXP ".*(9999).*" and adjust="none"'
            df = self.read_mysql(sql)
        df.drop(["adjust", "factor", "paused"], axis=1, inplace=True)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_futures_main_price_daily(self, security, adjust="post"):
        sql = f'SELECT * FROM dwd_futures_price_daily WHERE security="{security}" and adjust="{adjust}"'
        df = self.read_mysql(sql)
        df.drop(["adjust", "factor", "paused"], axis=1, inplace=True)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_futures_contract_info(self, security_tuple, futures_type="Commodity"):
        # sql = f'-- SELECT * FROM dwd_futures_contract_info WHERE security in {security_tuple} and futures_type="{futures_type}"'  # 正则匹配
        sql = f'SELECT * FROM dwd_futures_contract_info WHERE security in {security_tuple}'  # 正则匹配
        df = self.read_mysql(sql)
        return df

    def read_futures_base_info(self, security_tuple):
        sql = f'SELECT * FROM dwd_futures_base_info WHERE security in {security_tuple}'  # 正则匹配
        df = self.read_mysql(sql)
        return df

    def read_futures_customize_index_weight(self, index_name, today_date):
        sql = f'SELECT * FROM dwb_futures_customize_index_weight WHERE index_name="{index_name}" and security REGEXP ".*9999.*" and end_date>="{today_date}" and start_date<="{today_date}" and weight>0'
        df = self.read_mysql(sql)
        return df

    def read_futures_main_force_continuous(self, today_date):
        sql = f"SELECT * FROM dwd_futures_base_info WHERE  end_date>='{today_date}' and security  REGEXP '.*(9999).*'"
        df = self.read_mysql(sql)
        return df

    def read_dwd_dominant_futures_winners_list(self, security):
        sql = f'SELECT * FROM dwd_dominant_futures_winners_list WHERE security="{security}" and rank_type_ID !=501001'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def second_read_dwd_dominant_futures_winners_list(self, security, member_name):
        sql = f'SELECT * FROM dwd_dominant_futures_winners_list WHERE security="{security}" and member_name="{member_name}" and rank_type_ID !=501001'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_cond_winners_list(self, security, member_name):
        sql = f'SELECT * FROM ods_futures_winners_list WHERE security="{security}" and member_name="{member_name}" and rank_type_ID !=501001'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_ods_futures_winners_list(self):
        last_trading_date = self.read_dwd_trade_days()

        sql = f'SELECT * FROM ods_futures_winners_list WHERE trade_date="{last_trading_date}"'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_all_futures_winners_list(self, security_code):
        sql = f'SELECT * FROM ods_futures_winners_list where security_code="{security_code}"'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def read_dwd_trade_days(self):
        today = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        sql = f'SELECT * FROM trade_date WHERE trade_date <= "{today}"'
        df = self.read_mysql(sql)
        if not df.empty:
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df["trade_date"].to_list()[-1]

    def read_futures_all_security(self, today_date):
        sql = f"SELECT * FROM dwd_futures_base_info WHERE  end_date>='{today_date}' and security  NOT REGEXP '.*(9999|8888).*'"  # 正则匹配
        df = self.read_mysql(sql)
        return df

    def read_ods_futures_contract_info(self):
        sql = f"SELECT * FROM ods_futures_contract_info"
        df = self.read_mysql(sql)
        return df




if __name__ == '__main__':
    futures_Index = FuturesIndex()
    # df_Index = futures_Index.read_futures_index("Avg Weight Increase Index")
    # print(df_Index[['trade_date', 'close']])
    # df_Index_bias = futures_Index.read_futures_index_bias("Avg Weight Increase Index")
    # print(df_Index_bias)
    # df_Index_rsi = futures_Index.read_futures_index_rsi("Avg Weight Increase Index")
    # print(df_Index_rsi)
    # df_Index_boll = futures_Index.read_futures_index_boll("Avg Weight Increase Index")
    # print(df_Index_boll)
    # df_index_macd = futures_Index.read_futures_index_macd("Avg Weight Increase Index")
    # print(df_index_macd)
    # df_index_ma = futures_Index.read_futures_index_ma("Avg Weight Increase Index")
    # print(df_index_ma)
    # futures_price_df = futures_Index.read_futures_price_daily("2022-01-04 00:00:00")
    futures_price_df = futures_Index.read_futures_main_force_continuous("2022-07-25 00:00:00")

    print(futures_price_df)
    # futures_contract_info_df = futures_Index.read_futures_contract_info(tuple(futures_price_df['security'].tolist()))

    # futures_price_df.sort_values("security", inplace=True)
    # futures_contract_info_df.sort_values("security", inplace=True)
    # futures_contract_info_df["contract_value"] = futures_price_df["open_interest"] * futures_price_df["close"] * futures_contract_info_df["multiplier"]
    # print(futures_contract_info_df.sort_values("contract_value", ascending=False).head(10))
    # futures_customize_index_weight_df = futures_Index.read_futures_customize_index_weight("Contract Value Weight Index 3Month", "2022-01-01 00:00:00")
    # print(futures_customize_index_weight_df)
