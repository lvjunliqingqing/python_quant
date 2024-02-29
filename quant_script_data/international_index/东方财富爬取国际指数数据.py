import pandas as pd
import requests
import json
import matplotlib.pyplot as plt


def main():
    index1 = '100.NDX'  # Nasdaq
    index2 = '100.DJIA'  # 道琼斯
    index3 = '100.SPX'  # 标普500
    index4 = '100.HSI'  # 恒生
    index5 = '124.HSTECH'  # 恒生科技
    index6 = '101.GC00Y'  # 黄金
    index7 = '102.CL00Y'  # 美油
    index8 = '109.LCPT'  # 伦铜
    index9 = '100.UDI'  # 美元指数

    listindex = [index1, index2, index3, index4, index5]
    display_name_dict = {'100.NDX': "纳斯达克指数", '100.DJIA': "道琼斯", '100.SPX': "标普500", '100.HSI': "恒生", '124.HSTECH': "恒生科技"}

    # listindex = [index1, index2, index3, index4, index5, index6, index7, index8, index9]
    # stockpool = ['105.TSLA', '105.AMZN', '105.AAPL', '105.MSFT', '105.BIDU', '105.jd', '106.NIO', '116.00700', '116.09988']
    # listin = []
    # listin.extend(listindex)
    # listin.extend(stockpool)

    global name

    all_data = pd.DataFrame()

    for stock in listindex:
        try:
            daydata = getdf(stock, bdate='20050101')  # , end_date='2018-05-10')
            daydata["security"] = stock
            daydata["display_name"] = display_name_dict[stock]
        except:
            print('Get %s Data Error!' % (stock))
            continue

        all_data = all_data.append(daydata, ignore_index=True)  # 合并数据
    all_data.to_csv("东方财富爬取的_国际指数数据.csv", index=False)
    # print(all_data)

    # 绘制图形
    # plt.figure(figsize=(12, 10))
    # daydata['close'].plot(grid=True, figsize=(12, 8))  # debug,show
    # plt.title(stock + ' ' + name)
    # plt.show()


# 东方财富爬虫,获得数据
def getdf(stock, bdate):
    params = create_params(4, stock, bdate)
    response = get_response(params, 4)
    stockdata = get_data(response, 4)
    df = data_clean2(stockdata)
    return df


def create_params(page, code, bdate):
    if page == 4:  # 国外指数和商品
        params = {'cb': 'jQuery1124007067471145044357_1611539968748', 'fields1': 'f1,f2,f3,f4,f5', 'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58', 'klt': '101', 'fqt': '0'}
        params['secid'] = code
        params['beg'] = bdate
        params['end'] = '20220601'

    return params


def get_response(params, page=0):
    cookies = {
        'waptgshowtime': '2020109',
        'st_si': '62033869304648',
        'st_asi': 'delete',
        'cowCookie': 'true',
        'qgqp_b_id': 'b6a504ec0746ecec06a8c9db5dde3bec',
        'intellpositionL': '249px',
        'intellpositionT': '755px',
        'st_pvi': '93530241304569',
        'st_sp': '2020-09-19^%^2017^%^3A34^%^3A43',
        'st_inirUrl': 'https^%^3A^%^2F^%^2Fwww.eastmoney.com^%^2F',
        'st_sn': '28',
        'st_psi': '20201009171102245-113300300813-9103840696',
    }

    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'http://data.eastmoney.com/',
        'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
    }

    if page == 4:
        url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?'

    response = requests.get(url, headers=headers,
                            params=params, cookies=cookies, verify=False, timeout=(10, 30))
    # print(response.url)  # 查看url
    return response


def get_data(response, page=0):
    global name
    content = response.text
    jstext = content.split("(")[1][:-2]  # 去掉"(...);"
    if (page == 4):  # 国外商品和指数
        data = json.loads(jstext)['data']['klines']
        name = json.loads(jstext)['data']['name']
    else:
        data = {}

    return data


def data_clean2(data):  # histroy kline flow
    liststr = []
    for i in range(0, len(data)):
        liststr.append(data[i].split(","))
    df = pd.DataFrame(liststr, columns=
    ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amp'])
    dfout = df
    dfout['close'] = df['close'].astype(float)
    dfout.index = df.astype({'date': 'datetime64[ns]'})
    # dfout.set_index('date', inplace=True)
    return dfout


name = ''
main()
