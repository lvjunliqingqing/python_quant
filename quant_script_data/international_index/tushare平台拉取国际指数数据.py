import datetime
import tushare as ts
import pymysql
# from sqlalchemy import create_engine
import pandas as pd
import numpy as np


pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# connect = create_engine('mysql+pymysql://manager:jskjfwq@192.168.11.253:3306/stock?charset=utf8')
connect = pymysql.connect(
    host='192.168.11.250',
    port=3308,
    user='root',
    passwd='jskjfwq',
    db='stock',
    charset='utf8'
)

pro = ts.pro_api(token="572c7e13b431da6b7481ca0693db0b56fc83b14bd41055e52e74b459")

inter_index_df = pd.read_csv("国际指数合约代码.csv")
display_names = inter_index_df["指数名称"].to_list()


def insert_international_index_daily_price():
    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
    end_date = datetime.datetime.now().date().strftime("%Y%m%d")
    # 单次最大提取4000行情数据，可循环获取，总量不限制
    # all_data = pd.DataFrame()
    for index, code in enumerate(inter_index_df["TS指数代码"].to_list()):
        # df = pro.index_global(ts_code=code, start_date='20150805', end_date='20220602')
        df = pro.index_global(ts_code=code, start_date=start_date, end_date=end_date)
        display_name = display_names[index]
        df["display_name"] = display_name
        df.rename(columns={'ts_code': 'security', 'vol': "volume", "pct_chg": "change_pct"}, inplace=True)
        df = df[['security', 'trade_date', 'display_name', 'open', 'close', 'high', 'low', 'pre_close', 'change_pct', 'volume']]
        if not df.empty:
            # df["trade_date"] = df["trade_date"].apply(lambda x: datetime.strptime(x[0:4] + '-' + x[4:6] + '-' + x[6:8], '%Y-%m-%d'))
            df["trade_date"] = pd.to_datetime(df["trade_date"]).apply(lambda x: x.date())  # str转Timestamp再转datetime.date
            df["volume"].fillna(0.0, inplace=True)
            df.fillna(method='ffill', inplace=True, axis=0)  # nan值全部使用上一行填充
            # all_data = all_data.append(df, ignore_index=True)  # 合并数据
            """
            坑点:
                raise ProgrammingError("%s can not be used with MySQL" % s)
                pymysql.err.ProgrammingError: nan can not be used with MySQL
            原因:数据中有nan值
            """
            # 批量插入或修改,存在即更新,不存在即插入数据。
            data_array = np.array(df).tolist()

            # print(np.any(pd.isnull(df)))
            # print(data_array)
            # DUPLICATE KEY UPDATE:多进程多线程时且批量插入时,可能会造成死锁或数据丢失的情况(解决方案:使用单线程单进程)
            sql = """
                insert into 
                    dwd_international_index_price_daily(security,trade_date,display_name,open,close,high,low,pre_close,change_pct,volume) 
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                ON DUPLICATE KEY UPDATE 
                    open=values(open), 
                    close=values(close),
                    high=values(high),
                    low=values(low),
                    pre_close=values(pre_close),
                    change_pct=values(change_pct),
                    volume=values(volume)
                """

            with connect.cursor() as cursor:
                connect.begin()
                ret = cursor.executemany(sql, data_array)  # 批量插入或者更行   sql语句中的数据从data_array中取
                connect.commit()
                if ret == 0:
                    print(f"{display_name},数据库已存在,无需插入")
                elif ret == len(data_array):
                    print(f"{display_name},插入{ret}条数据")
                else:
                    print(f"{display_name},插入{ret}条数据,更新{len(data_array) - ret}条数据")
            #     ret = connect.execute(sql, data_array)
    # all_data.to_csv("tushare平台拉取_国际指数数据.csv", index=False)
        # if code == "HKTECH":
        #     break
    connect.close()


if __name__ == '__main__':
    insert_international_index_daily_price()
