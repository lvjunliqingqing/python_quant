import datetime
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

"""
把需要导入出的期货合约相关信息写入export_futures_list表中
"""


class ExportManageData:

    def __init__(self):
        self.connect = create_engine('mysql+pymysql://js_sql:js_sql123456@192.168.20.119:3306/vnpy?charset=utf8')
        self.today_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
        self.start_time_str = f"{datetime.datetime.now().year}-01-01"

    def single_contract_information(self):
        """单品种合约信息写入export_futures_list表,用来限制脚本从通达信上导哪些数据"""
        sql = f'SELECT symbol,start_date,end_date FROM vnpy.securities_info WHERE start_date >= "{self.start_time_str}" and end_date >= "{self.today_date}" and  symbol NOT  REGEXP ".*(9999|8888).*" and sec_type="futures"'
        df_futures = pd.read_sql(sql, con=self.connect)
        if not df_futures.empty:
            df_futures.drop_duplicates(subset=['symbol', 'start_date', "end_date"], keep='first', inplace=True)
            df_futures[["security_code", "exchange"]] = df_futures['symbol'].str.split('.', n=1, expand=True)
            new_df_futures = df_futures[["security_code", "start_date", "end_date"]]
            self.write_to_table(new_df_futures)

    def mian_contract_information(self):
        """主连合约信息写入export_futures_list表,用来限制脚本从通达信上导哪些数据"""
        sql = f'SELECT symbol,start_date,end_date FROM vnpy.securities_info WHERE start_date <= "{self.start_time_str}" and symbol REGEXP ".*9999.*" and sec_type="futures"'
        df_main_futures = pd.read_sql(sql, con=self.connect)
        if not df_main_futures.empty:
            df_main_futures[["security_code", "exchange"]] = df_main_futures['symbol'].str.split('[9.]', n=1, expand=True)
            df_main_futures['security_code'] = df_main_futures["security_code"] + "L8"
            df_main_futures["start_date"] = np.where(df_main_futures["start_date"].apply(lambda x: x.strftime("%Y-%m-%d")) < "2019-01-02", "2019-01-02", df_main_futures["start_date"])
            df_main_futures = df_main_futures[["security_code", "start_date", "end_date"]]
            self.write_to_table(df_main_futures)

    def write_to_table(self, df):
        train_x_list = np.array(df).tolist()
        sql = "insert into export_futures_list(security_code,start_date,end_date) values(%s,%s,%s) ON DUPLICATE KEY UPDATE security_code=values(security_code),start_date=values(start_date),end_date=values(end_date)"
        self.connect.execute(sql, train_x_list)  # 批量插入或者更新   sql语句中的数据从train_x_list中取


if __name__ == '__main__':
    ExportManageData().single_contract_information()  # 单一合约写入
    ExportManageData().mian_contract_information()  # 主连合约写入
