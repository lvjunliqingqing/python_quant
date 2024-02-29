from sqlalchemy import create_engine
import pandas as pd
import datetime

pd.set_option('display.float_format', lambda x: '%.4f' % x)  # 禁止科学计算显示,保留四位有效小数点
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


class StockIndex:

    def __init__(self):
        self.connect = create_engine('mysql+pymysql://manager:jskjfwq@192.168.11.253:3306/stock?charset=utf8')
        self.start_date = "2005-01-03 00:00:00"
        self.end_date = datetime.datetime.now().date().strftime("%Y-%m-%d")

    def read_mysql(self, sql):
        df = pd.read_sql(sql, con=self.connect)  # 读取SQL数据库，并转化成pandas。
        return df

    def read_futures_price_daily(self):
        """期货日K线数据表"""
        security = ('BB9999.XDCE', 'CY9999.XZCE', 'ER9999.XZCE', 'FB9999.XDCE', 'GN9999.XZCE',
                    'JR9999.XZCE', 'LR9999.XZCE', 'PM9999.XZCE', 'RI9999.XZCE', 'RR9999.XDCE',
                    'SS9999.XSGE', 'WH9999.XZCE', 'WR9999.XSGE', 'WS9999.XZCE', 'WT9999.XZCE',
                    'LU9999.XINE', 'NR9999.XINE', 'RS9999.XZCE', 'B9999.XDCE', 'IF9999.CCFX',
                    'IC9999.CCFX', 'IH9999.CCFX', 'TF9999.CCFX', 'T9999.CCFX', 'TS9999.CCFX',
                    'BC9999.XINE', 'PK9999.XZCE', 'TC9999.XZCE', 'ME9999.XZCE', 'RO9999.XZCE')
        sql = f'SELECT security,trade_date,open,close,low,high,volume FROM dwd_futures_price_daily WHERE security REGEXP ".*(9999).*" ' \
              f'and security not in {security} and (trade_date between "{self.start_date}" and "{self.end_date}") and adjust="none"'  # 正则匹配

        df = self.read_mysql(sql)
        if not df.empty:
            df = df[~((df["low"] == df["high"]) & (df["volume"] == 0))]  # 过滤掉停盘数据
            df.drop(["adjust", "factor"], axis=1, inplace=True)
            df["trade_date"] = df["trade_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df

    def stock_index_north_correlation(self, index_code="000001.XSHG", price_code="688686.XSHG", link_id_tuple=(310001, 310002)):
        """指数、陆股通、个股三表关联查询,得到拥有指数板块、个股、陆股通的df数据对象"""
        sql = """
            SELECT
                *
            FROM
                (dwd_index_price_daily as i,
                (SELECT trade_date,group_concat(currency_name),sum(sell_amount) as sell_money,sum(buy_amount) as buy_money, (sum(buy_amount) - sum(sell_amount)) as net_buy from dwd_stk_ml_quota WHERE link_id in %s GROUP BY trade_date) as q
                ),
                dwd_stock_price_daily as p
            WHERE
                q.trade_date = i.trade_date
                and i.`security` = "%s"
                and p.adjust = "post"
                and i.trade_date = p.trade_date
                and p.`security` = "%s"
            order by i.trade_date
        """ % (link_id_tuple, index_code, price_code)

        df = self.read_mysql(sql)
        return df

    def index_north_correlation(self, index_code="000001.XSHG", link_id_tuple=(310001, 310002)):
        """北向资金和上证指数的关系研究数据"""
        sql = """
            SELECT
                i.trade_date,i.close, i.pre_close, change_pct,q.trade_date as north_bund_trade_date,q.sell_money,q.buy_money,q.net_buy
            FROM
                (dwd_index_price_daily as i,
                (SELECT trade_date,sum(sell_amount) as sell_money,sum(buy_amount) as buy_money, (sum(buy_amount) - sum(sell_amount)) as net_buy from dwd_stk_ml_quota WHERE link_id in %s GROUP BY trade_date) as q
                )
            WHERE
                q.trade_date = i.trade_date
                and i.`security` = "%s"
            order by i.trade_date
        """ % (link_id_tuple, index_code)

        df = self.read_mysql(sql)
        return df

    def stock_index_correlation(self, index_code="000001.XSHG", price_code="688686.XSHG"):
        """指数和个股研究关系的数据"""
        sql = """
            SELECT
                i.security,i.trade_date,i.pre_close,i.change_pct,p.security as ge_security,p.trade_date as ge_trade_date,p.pre_close as ge_pre_close,p.change_pct as ge_change_pct
            FROM
                dwd_index_price_daily as i, dwd_stock_price_daily as p
            WHERE
                i.`security` = "%s"
                and p.adjust = "post"
                and i.trade_date = p.trade_date
                and p.`security` = "%s"
            order by i.trade_date
        """ % (index_code, price_code)
        df = self.read_mysql(sql)
        return df


if __name__ == '__main__':
    stock_Index = StockIndex()
    # stock_price_df = stock_Index.read_futures_price_daily("2022-01-04 00:00:00")
    # stock_price_df = stock_Index.stock_index_north_correlation()
    stock_price_df = stock_Index.index_north_correlation()
    # stock_price_df = stock_Index.stock_index_correlation()
    import numpy as np
    import scipy.stats as ss

    x = stock_price_df["change_pct"].shift(-1)[0:-1]
    y = stock_price_df["net_buy"][0:-1]
    result1 = np.corrcoef(x, y)

    # result3 = ss.pearsonr(x, y)
    print(result1)
