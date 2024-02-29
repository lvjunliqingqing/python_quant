import base64
import math
import time

from jqdatasdk import *
from peewee import (
    MySQLDatabase,
)

settings = {
        'host': '192.168.0.250',
        'user': 'stock',
        'password': '123456',
        'port': 3306,
        'charset': 'utf8'
        }

db = MySQLDatabase("stock", **settings)

auth('18520128569', (base64.b64decode(b'Y2hhbzM0MzM1NDE3').decode()))

from peewee import (
    AutoField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
)


class SecuritiesInfoModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField(null=False)
    display_name = CharField(null=False)
    name_code = CharField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    sec_type = CharField(null=False)

    class Meta:
        database = db  # 这里是数据库链接，为了方便建立多个表，可以把这个部分提炼出来形成一个新的类
        table_name = 'securities_info'  # 这里可以自定义表名

    def savaData(self, df):
        for idx, row in df.iterrows():

            sql = SecuritiesInfoModel.insert(
                symbol=idx,
                display_name=row.display_name,
                name_code=row['name'],
                start_date=row.start_date,
                end_date=row.end_date,
                sec_type=row.type,
            ).on_conflict(
                preserve=[
                    SecuritiesInfoModel.display_name,
                    SecuritiesInfoModel.start_date,
                    SecuritiesInfoModel.end_date,
                    SecuritiesInfoModel.sec_type,
                    SecuritiesInfoModel.name_code,
                    SecuritiesInfoModel.sec_type,
                ]
            )
            if sql.execute():
                print(f"ok {idx} sql {sql}")
            else:
                print(f"error sql {sql}")


class BarModel(Model):
    id = AutoField(primary_key=True)
    symbol = CharField()
    exchange = CharField()
    datetime = DateTimeField()
    interval = CharField()
    volume = IntegerField()
    open_interest = FloatField()
    open_price = FloatField()
    close_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()

    def savaData(self, df):
        for idx, row in df.iterrows():
            trade_date = idx.to_pydatetime()
            print(f"trade_date {trade_date} {type(trade_date)}")
            Bar = BarModel(
                symbol=row.symbol,
                exchange=row.exchange,
                datetime=trade_date,
                interval='d',
                volume=float(row.volume),
                open_interest=0,
                open_price=row.open,
                close_price=row.close,
                high_price=row.high,
                low_price=row.low
            )

            row.open = (0.0 if (math.isnan(row.open)) else row.open)
            row.close = (0.0 if (math.isnan(row.close)) else row.close)
            row.high = (0.0 if (math.isnan(row.high)) else row.high)
            row.low = (0.0 if (math.isnan(row.low)) else row.low)
            row.volume = (0.0 if (math.isnan(row.volume)) else row.volume)

            sql = Bar.insert(
                symbol=row.symbol,
                exchange=row.exchange,
                datetime=trade_date,
                interval='d',
                volume=int(row.volume),
                open_interest=0,
                open_price=row.open,
                close_price=row.close,
                high_price=row.high,
                low_price=row.low
            ).on_conflict(
                preserve=[BarModel.open_price, BarModel.close_price, BarModel.high_price, BarModel.low_price,
                          BarModel.volume]
            )
            if sql.execute():
                print(f"ok {trade_date} sql {sql}")
            else:
                print(f"error sql {sql}")

    class Meta:
        database = db  #
        table_name = 'dbbardata'  # 这里可以自定义表名

    def get_jk_current_day_data(self, is_history=False):

        curr_date = datetime.datetime.now().strftime('%Y-%m-%d')

        sql = f"select * from securities_info where symbol NOT  REGEXP '.*(9999|8888).*' and end_date >= '{curr_date}' and name_code REGEXP '^(RB).*'"

        # print(sql)
        # return
        sec_list = SecuritiesInfoModel().raw(sql)

        curr_db_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')

        for row in sec_list:

            tmp = row.symbol.split('.')

            # print(tmp[0])
            # bar_data = BarModel.select().where(
            #   (BarModel.datetime == curr_db_date)
            #   & (BarModel.symbol == tmp[0])
            #   & (BarModel.exchange == tmp[1])
            # ).dicts()

            # curr_hour = datetime.datetime.now().strftime("%H:%M")

            # limit_hour = '15:00'

            # if len(bar_data) > 0 and is_history == False and curr_hour > limit_hour:
            #   print(f"{datetime.datetime.now()} len(bar_data) {curr_date} {len(bar_data)} {row.symbol}")
            #   continue

            start_date = datetime.datetime.now().strftime('%Y-%m-%d')
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            if is_history == True:
                start_date = row.start_date

            df = get_price(row.symbol, start_date=start_date, end_date=end_date, frequency='daily', fields=None,
                           skip_paused=False, fq='pre')
            print(f"df {df}")
            df.dropna(axis=0, how='all', inplace=True)
            print(f"df.dropna {df}")
            if not len(df):
                print(f"ts_code df len = 0 {row.symbol}")
            else:
                df['exchange'] = tmp[1]
                df['symbol'] = tmp[0]
                self.savaData(df)

            time.sleep(0.5)


if __name__ == "__main__":
    # BarModel().get_jk_current_day_data(True)

    q = query(
        valuation
    ).filter(
        valuation.code == '000001.XSHE'
    )
    df = get_fundamentals(q, '2015-10-15')
    # 打印出总市值
    print(df)
