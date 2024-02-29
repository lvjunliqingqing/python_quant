from pyecharts_demo.futures_commodity_index.futures_index_data import FuturesIndex
import time


def data_migration():
    futures_Index = FuturesIndex()
    contract_df = futures_Index.read_ods_futures_contract_info()
    security_code_list = contract_df["futures_code"].to_list()
    print(security_code_list)
    for security_code in security_code_list:
        read_futures_winners_list(security_code)


def read_futures_winners_list(security_code):
    start_time = time.time()
    futures_Index = FuturesIndex()
    connect = futures_Index.connect
    winners_df = futures_Index.read_all_futures_winners_list(security_code)
    winners_df = winners_df.drop_duplicates()
    print(winners_df)
    winners_df.to_sql(name='ods_futures_winners_list1', con=connect, if_exists='append', index=False, index_label=False)
    end_time = time.time()
    run_time = end_time - start_time
    print(run_time)


if __name__ == '__main__':
    data_migration()


