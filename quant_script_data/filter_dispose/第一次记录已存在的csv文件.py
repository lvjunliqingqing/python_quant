import os
from copy import copy

from filter_dispose.load_wirte_json import save_json


def existing_file_record():
    """用json文件记录已经导入过存在的文件"""
    data = {}
    current_folder_path = os.path.split(os.path.realpath(__file__))[0]  # 获取当前文件夹路径
    file_name = f"{current_folder_path}/filter_xls_data_to_csv.json"

    export_folder_list = os.listdir("E:/jobs/通达信数据/主连/所有品种主连")  # 所有主连文件夹名
    for folder_name in export_folder_list:
        dir_name = f"E:/jobs/通达信数据/主连/所有品种主连/{folder_name}/"  # 单个主连文件路径
        source_file_list = os.listdir(dir_name)  # 单个主连文件夹下所有文件名,是list。

        data[copy(folder_name)] = copy(source_file_list)
    save_json(file_name, data)  # 第一次初始化json文件用的


if __name__ == '__main__':
    pass
    # existing_file_record()
