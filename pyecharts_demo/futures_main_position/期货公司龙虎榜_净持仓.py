from pyecharts_demo.futures_commodity_index.futures_index_data import FuturesIndex
from pyecharts_demo.futures_main_position.MainPositionPriceRelationship import MainPositionPriceRelationship


if __name__ == "__main__":
    """
    期货公司龙虎榜每日净持仓
    """
    futures_Index = FuturesIndex()
    main_price_relationship = MainPositionPriceRelationship(futures_Index)

    for security in main_price_relationship.main_all_security:

        main_position_df = futures_Index.read_dwd_dominant_futures_winners_list(security)
        sell_main_position_df = main_position_df[main_position_df["rank_type_ID"] == 501003]
        buy_main_position_df = main_position_df[main_position_df["rank_type_ID"] == 501002]
        # 排名前20大期货公司持多单量
        buy_volume_series = buy_main_position_df.groupby(["trade_date"])["indicator"].sum()
        # 排名前20大期货公司持空单量
        sell_volume_series = sell_main_position_df.groupby(["trade_date"])["indicator"].sum()
        net_position_list = (buy_volume_series - sell_volume_series).to_list()
        main_times = buy_main_position_df.groupby(["trade_date"])["trade_date"].first().to_list()
        print(main_times)

        m_p_d_df = futures_Index.read_futures_main_price_daily(security)
        m_p_d_df = main_price_relationship.add_ma_data(m_p_d_df, drop_flg=False)
        m_p_d_df = m_p_d_df[m_p_d_df["trade_date"].isin(main_times)]

        if not m_p_d_df.empty:
            data = {
                    "datas": m_p_d_df[["open", "close", "low", "high"]].values.tolist(),
                    "times": m_p_d_df["trade_date"].to_list(),
                    "vols": m_p_d_df["volume"].to_list(),
                    "MA5": m_p_d_df["MA5"],
                    "MA10": m_p_d_df["MA10"],
                    "MA20": m_p_d_df["MA20"],
                    "security": m_p_d_df["security"].to_list()[0],
                    "open_interest": m_p_d_df["open_interest"].to_list(),
                    "main_position": {
                        "times": main_times,
                        "buy_main_open_interest": net_position_list
                    },
                    # , "volume",
                    # "macds": macds,
                    # "difs": difs,
                    # "deas": deas,
                    }

            series_name = "主力净持仓"
            filename = f"html_chart/龙虎榜净持仓/{data['security']}期货主力净持仓与股价的关系.html"
            title = f"{data['security']}期货主力净持仓与股价的关系"
            main_price_relationship.draw_chart(data, series_name, filename, title)
            # print(m_p_d_df)
            # print(data["datas"])
            # break


