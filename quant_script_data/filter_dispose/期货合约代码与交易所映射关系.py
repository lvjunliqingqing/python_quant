from sqlalchemy import create_engine
import pandas as pd
import re
connect = create_engine('mysql+pymysql://js_sql:js_sql123456@192.168.20.119:3306/vnpy?charset=utf8')

sql2 = 'select * from securities_info where end_date >= curdate();'
csv_data = pd.read_sql(sql2, con=connect)
dict_temp = {}
for index, row in csv_data.iterrows():
    key = re.sub('[^a-zA-Z]', '', row['symbol'].split(".")[0])
    value = row['symbol'].split(".")[1]
    dict_temp[key] = value

print(dict_temp)