
def marking_baldheaded_yang_line(df):
    cond1 = (df["change_pct"] * 100) > (5 * df["up_limit"] / 20)
    cond2 = (df["close"] == df["high"])
    # cond3 = df["volume"] > df["MAVOL5"]
    # cond4 = (df["close"] > df["MA5"]) & (df["MA5"] > df["MA10"]) & (df["MA10"] > df["MA20"])
    cond5 = (df["close"] != df["high_limit"])  # 不涨停
    cond6 = (df["volume"] > 10000)
    cond = cond1 & cond2 & cond5 & cond6
    df.loc[cond, "baldheaded_yang_line_signal"] = 1
    return df
