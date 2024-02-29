import os
import re
path = r"E:\install\tongdaxin2\T0002\export"

# 获取该目录下所有文件，存入列表中
fileList = os.listdir(path)


for filename in fileList:
    # 设置旧文件名（就是路径+文件名）
    oldname = path + os.sep + filename  # os.sep添加系统分隔符
    file_temp = re.split(r'[_.]', filename)[1] + "分笔" + "." + "xls"
    # 设置新文件名
    newname = path + os.sep +file_temp
    # 修改文件名
    os.rename(oldname, newname)
    # print(oldname, '======>', newname)
