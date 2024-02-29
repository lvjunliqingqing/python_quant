import os
import csv

from filter_dispose.load_wirte_json import load_json, save_json


def existing_file_record(file_path):
    """用json文件记录已经导入过存在的文件"""
    current_folder_path = os.path.split(os.path.realpath(__file__))[0]  # 获取当前文件夹路径
    file_name = f"{current_folder_path}/filter_xls_data_to_csv.json"
    setting = load_json(file_name)  # 获取已导入过的文件清单

    export_folder_list = os.listdir(file_path)  # 所有主连文件夹名

    for folder_name in export_folder_list:
        dir_name = f"{file_path}/{folder_name}/"  # 单个主连文件路径
        source_file_list = os.listdir(dir_name)  # 单个主连文件夹下所有文件名,是list。
        difference_set = set(source_file_list).difference(set(setting.get(folder_name, [])))  # 获取没有写入过数据库的文件(用的是两个列表求差集:筛选出list1中存在list2中不存的)

        if difference_set:
            print(difference_set)
            setting[folder_name] = list(set(setting.get(folder_name, [])).union(difference_set))  # 拼接上这次新导出的文件记录
            setting[folder_name].sort()  # 排序

    save_json(file_name, setting)


def xls_data_to_csv(source_dir, target_dir, source_file):
    save_filename = source_file[0:-4]

    # target_flie_dir = target_dir + os.sep + save_filename + '.csv'
    # if not os.path.isfile(target_flie_dir):  # 如果文件不存在(基于文件夹目录判断,所有文件不能删除,会造成硬盘容量不够的问题),因为在man()中已经过滤了,所以注释。

    reader = open(source_dir + os.sep + source_file, 'r')  # 读取原始数据   print(os.sep) 输出 "\"
    list_data = reader.readlines()
    reader.close()
    columns = list_data[2].split()
    columns.extend(['开平', '性质'])
    list_temp = []
    for i in list_data[4:-1]:
        list_temp.append(i.split())

    with open(target_dir + os.sep + save_filename + '.csv', "w", newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(columns)  # 先写入columns_name
        writer.writerows(list_temp)  # 写入多行用writerows

    print(f"往{target_dir + os.sep}中，写入新文件{save_filename}")


def main():
    tdx_export_dir = r"E:\install\tongdaxin2\T0002\export"  # 通达信导出目录
    source_folder_list = os.listdir(tdx_export_dir)  # 读取此文件夹下所有文件夹名
    for folder_name in source_folder_list:
        source_dir = f'{tdx_export_dir}\{folder_name}'  # 源文件夹路径(通达信分时成交明细目录)
        target_dir = f'E:\jobs\通达信数据\主连\所有品种主连\{folder_name}'  # 通达信数据转换后存储目录

        if not os.path.exists(target_dir):  # 没有文件夹就创建
            os.makedirs(target_dir)

        current_folder_path = os.path.split(os.path.realpath(__file__))[0]  # 获取当前文件夹路径
        file_name = f"{current_folder_path}/filter_xls_data_to_csv.json"
        setting = load_json(file_name)  # 获取已导入过的文件清单

        source_file_list = os.listdir(source_dir)  # 将源文件夹下的所有文件列表出来
        if source_file_list:
            source_file_list = [i for i in source_file_list if (i.split(".")[0] + "." + "csv") not in setting[folder_name]]  # 过滤掉已经处理过的文件(改成基于json文件记录来判断,可以删除已入库的csv文件,没有硬盘容量不够的问题)

        for stockfile in source_file_list:
            xls_data_to_csv(source_dir, target_dir, stockfile)

    existing_file_record(r"E:\jobs\通达信数据\主连\所有品种主连")  # 把处理过的文件写入json文件中


if __name__ == '__main__':
    main()
