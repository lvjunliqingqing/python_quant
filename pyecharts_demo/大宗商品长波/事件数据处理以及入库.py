from pyecharts_demo.futures_commodity_index.Logger import Logger
from datetime import datetime
import pandas as pd
from xlrd import open_workbook, xldate_as_tuple
from pyecharts_demo.futures_commodity_index.send_email import send_email
import numpy as np

from stock_data import StockData


def read_excel(FileName):
    stock_data = StockData()
    trade_date_df = stock_data.read_ods_trade_days()
    xl = open_workbook(FileName)  # 获取excel对象
    data = []
    for sheet_name in xl.sheet_names():
        sheet = xl.sheet_by_name(sheet_name)  # 根据名字获取具体的sheet对象
        n_rows = sheet.nrows  # 获取总行数
        idx = sheet.row_values(0)  # 获取表格头(获取第n行的内容)
        for i in range(1, n_rows):
            row_data = sheet.row_values(i)
            row_data_dict = {}
            for j in range(len(row_data)):
                item = row_data[j]
                if j == 0:
                    item = datetime(*(xldate_as_tuple(item, 0)))  # 把float时间转成datetime
                    if item >= trade_date_df.iloc[0, 0]:
                        trade_date = trade_date_df.loc[trade_date_df["trade_date"] >= item].iloc[0, 0]
                    else:
                        trade_date = item

                    # 下面这两行代码,解决'Timestamp' object has no attribute 'translate'的问题
                    item = item.strftime('%Y-%m-%d')
                    trade_date = trade_date.strftime('%Y-%m-%d')

                    row_data_dict["trade_date"] = trade_date
                row_data_dict[idx[j]] = item

            data.append(row_data_dict)  # 将行数据字典加入到data列表中

    df = pd.DataFrame.from_dict(data)
    df['network_address'] = ""

    if not df.empty:
        columns = {'日期': 'create_time', '事件': 'incident', '事件类型': 'incident_type'}
        df.rename(columns=columns, inplace=True)

        data_ndarray = np.array(df).tolist()  # 先变np.ndarray(),再变多维列表

        connect = stock_data.connect

        sql = """
                insert into
                    ods_the_shanghai_event_copy1(`trade_date`,`create_time`,`incident`,`incident_type`,`network_address`)
                    values(%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    incident_type=values(incident_type), network_address=values(network_address);
        """
        connect.execute(sql, data_ndarray)


if __name__ == "__main__":
    logger = Logger("手动收集的事件数据处理以及入库")
    try:
        read_excel(r'E:\jobs\designer_demo\pyecharts_demo\大宗商品长波\重大事件.xls')
        send_email(f"手动收集的事件数据处理以及入库成功")
    except Exception as e:
        send_email(f"手动收集的事件数据处理以及入库,原因:{e}")
        logger.info(f"手动收集的事件数据处理以及入库,原因:{e}")
