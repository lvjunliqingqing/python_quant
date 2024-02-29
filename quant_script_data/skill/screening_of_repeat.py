import pandas as pd


def screening_of_repeat():
    df = pd.read_csv("./2020-8-27基本面筛选后再突破120日高价.csv", encoding="gbk")
    df2 = pd.read_csv("./2020-8-28基本面筛选后再突破120日高价.csv", encoding="gbk")
    count = 0
    for i in df2["symbol"]:
        if i in df["symbol"].values.tolist():
            print(i)
            print(df2["symbol"][count])
        count += 1


if __name__ == '__main__':
    screening_of_repeat()
