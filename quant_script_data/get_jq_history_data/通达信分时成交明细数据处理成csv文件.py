import csv
import os


def xls_data_to_csv(source_dir, target_dir, source_file):
    reader = open(source_dir + os.sep + source_file, 'r')  # 读取原始数据   print(os.sep) 输出 "\"
    list_data = reader.readlines()
    reader.close()
    columns = list_data[2].split()
    columns.extend(['开平', '性质'])

    list_temp = []
    for i in list_data[4:-1]:
        list_temp.append(i.split())
    save_filename = source_file[0:-4]
    with open(target_dir + os.sep + save_filename + '.csv', "w", newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(columns)  # 先写入columns_name
        writer.writerows(list_temp)  # 写入多行用writerows


source_dir = 'E:/jobs/通达信数据/主连/sourcedata/'  # 源文件夹路径(通达信分时成交明细目录)
target_dir = 'E:/jobs/通达信数据/主连/2021-10-15'  # 通达信数据转换后存储目录

if not os.path.exists(target_dir):  # 没有文件夹就创建
    os.makedirs(target_dir)

source_file_list = os.listdir(source_dir)  # 将源文件夹下的所有文件列表出来
# print(source_file_list)
for stockfile in source_file_list:
    xls_data_to_csv(source_dir, target_dir, stockfile)
