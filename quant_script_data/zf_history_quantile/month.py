# coding:utf-8
import datetime
import math
import pandas as pd
from peewee import (
    AutoField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
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

    def getData(self):
        data = self.select().where(
            (SecuritiesInfoModel.sec_type == 'stock')
            & (SecuritiesInfoModel.end_date >= datetime.datetime.now().strftime('%Y-%m-%d'))
        ).dicts()

        symbol_list = []
        for info in data.iterator():
            tmp = info['symbol'].split('.')
            symbol_list.append({'symbol': tmp[0], 'exchange': tmp[1]})
        return symbol_list


class StockBarModel(Model):
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

    class Meta:
        database = db
        table_name = 'dhtz_stock_dbbardata'


class MonthStockBarModel(Model):
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

    class Meta:
        database = db
        table_name = 'dhtz_stock_month_dbbardata'

    def generate_month_logic(self, df):

        """"""
        df['trade_date'] = df['datetime']
        # 转换为日期格式，否则无法转换季线
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        # W 周 M 月 Y 年 Q 季度，这里用Q
        period_type = 'M'
        # 必须将日期格式作为索引，才能做resample
        df.set_index('trade_date', inplace=True)
        # 原来的做法是 resample(...how='last')，但新版本中不那么用了
        # 日期用最后那天的日期
        df_quote = df.resample(period_type).last()
        df_quote.drop('interval', axis=1, inplace=True)
        df_quote.drop('close_price', axis=1, inplace=True)
        df_quote.drop('high_price', axis=1, inplace=True)
        df_quote.drop('low_price', axis=1, inplace=True)
        df_quote.drop('open_price', axis=1, inplace=True)
        df_quote.drop('id', axis=1, inplace=True)
        df_quote.drop('open_interest', axis=1, inplace=True)
        df_quote.drop('datetime', axis=1, inplace=True)
        # 涨跌用自定义函数计算，这里用apply
        # 开盘取第一天，收盘去最后一天，最高和最低分别取最大最小值，成交量和成交金额取求和值
        # 这里也不用how的方法
        # df_quote['change'] = df['change'].resample(period_type).apply(lambda x:(x+1.0).prod()-1.0)
        df_quote['open'] = df['open_price'].resample(period_type).first()
        df_quote['close'] = df['close_price'].resample(period_type).last()
        df_quote['high'] = df['high_price'].resample(period_type).max()
        df_quote['low'] = df['low_price'].resample(period_type).min()
        df_quote['volume'] = df['volume'].resample(period_type).sum()
        # df_quote['exchange'] = df['exchange']
        # df_quote['trade_date'] = df['datetime']
        # df_quote['symbol'] = df['symbol']
        # 过滤整季度无交易的数据
        df_quote = df_quote[df_quote['symbol'].notnull()]
        # 从新索引
        df_quote.reset_index(inplace=True)
        df.reset_index(inplace=True)
        return df_quote

    def savaManyData(self, df, start_date=None, end_date=None):
        data = []
        for idx, row in df.iterrows():
            row.open = (0.0 if (math.isnan(row.open)) else row.open)
            row.close = (0.0 if (math.isnan(row.close)) else row.close)
            row.high = (0.0 if (math.isnan(row.high)) else row.high)
            row.low = (0.0 if (math.isnan(row.low)) else row.low)
            row.volume = (0.0 if (math.isnan(row.volume)) else row.volume)
            data.append(
                {
                    'symbol': row.symbol,
                    'exchange': row.exchange,
                    'datetime': datetime.datetime.strftime(row.trade_date, '%Y-%m-%d'),
                    'interval': '1mth',
                    'volume': int(row.volume),
                    'open_interest': 0,
                    'open_price': row.open,
                    'close_price': row.close,
                    'high_price': row.high,
                    'low_price': row.low,
                }

            )

        if start_date and end_date:
            sql = MonthStockBarModel().replace_many(data)
        else:
            sql = MonthStockBarModel().insert_many(data).on_conflict_ignore()
        # print(sql)
        if sql.execute():
            print(f"ok {df['symbol'][0]}")
        else:
            print(f"error {sql}")

    def generate_month(self, start_date=None, end_date=None):
        stock_list = SecuritiesInfoModel().getData()
        for stock in stock_list:
            if start_date and end_date:
                bar_list = StockBarModel().select().where(
                    (StockBarModel.symbol == stock['symbol'])
                    & (StockBarModel.exchange == stock['exchange'])
                    & (StockBarModel.datetime >= start_date)
                    & (StockBarModel.datetime <= end_date)
                ).order_by(StockBarModel.datetime.desc()).dicts()

            else:
                bar_list = StockBarModel().select().where(
                    (StockBarModel.symbol == stock['symbol'])
                    & (StockBarModel.exchange == stock['exchange'])
                ).order_by(StockBarModel.datetime.desc()).dicts()

            data_list = []
            for bar in bar_list.iterator():
                data_list.append(bar)
            df = pd.DataFrame(data_list)
            insert_data = self.generate_month_logic(df)
            MonthStockBarModel().savaManyData(insert_data, start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    now = datetime.datetime.now()
    this_month_start = datetime.datetime(now.year, now.month, 1).strftime('%Y-%m-%d')
    curr_day = datetime.datetime.now().strftime('%Y-%m-%d')
    MonthStockBarModel().generate_month(start_date=this_month_start, end_date=curr_day)
